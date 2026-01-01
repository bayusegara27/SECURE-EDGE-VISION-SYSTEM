"""
Camera Ingestion Module
Handles RTSP/Webcam capture and shared memory distribution
"""

import cv2
import numpy as np
import time
import logging
from multiprocessing import shared_memory, Process, Event
from typing import Optional, Tuple
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SharedFrameBuffer:
    """Manages shared memory for zero-copy frame transfer between processes"""
    
    def __init__(self, name: str, shape: Tuple[int, int, int], create: bool = False):
        self.name = name
        self.shape = shape
        self.size = int(np.prod(shape))
        self.dtype = np.uint8
        
        if create:
            try:
                # Clean up existing shared memory if exists
                existing = shared_memory.SharedMemory(name=name)
                existing.close()
                existing.unlink()
            except FileNotFoundError:
                pass
            
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.size)
            logger.info(f"Created shared memory buffer: {name} ({self.size} bytes)")
        else:
            self.shm = shared_memory.SharedMemory(name=name)
            logger.info(f"Attached to shared memory buffer: {name}")
        
        self.buffer = np.ndarray(shape, dtype=self.dtype, buffer=self.shm.buf)
    
    def write(self, frame: np.ndarray):
        """Write frame to shared memory"""
        if frame.shape != self.shape:
            frame = cv2.resize(frame, (self.shape[1], self.shape[0]))
        np.copyto(self.buffer, frame)
    
    def read(self) -> np.ndarray:
        """Read frame from shared memory"""
        return self.buffer.copy()
    
    def close(self):
        """Close shared memory connection"""
        self.shm.close()
    
    def unlink(self):
        """Remove shared memory from system"""
        self.shm.unlink()


class CameraIngester:
    """
    Camera stream ingestion with shared memory output
    Supports webcam and RTSP streams
    """
    
    def __init__(
        self,
        source: str | int,
        output_width: int = 1280,
        output_height: int = 720,
        target_fps: int = 30,
        buffer_name: str = "frame_buffer"
    ):
        self.source = int(source) if str(source).isdigit() else source
        self.output_width = output_width
        self.output_height = output_height
        self.target_fps = target_fps
        self.buffer_name = buffer_name
        self.frame_interval = 1.0 / target_fps
        
        self._stop_event = Event()
        self._process: Optional[Process] = None
        self._shm_buffer: Optional[SharedFrameBuffer] = None
    
    def _capture_loop(self, stop_event: Event):
        """Main capture loop running in separate process"""
        logger.info(f"Starting capture from source: {self.source}")
        
        # Open video capture
        cap = cv2.VideoCapture(self.source)
        
        if not cap.isOpened():
            logger.error(f"Failed to open camera source: {self.source}")
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.output_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.output_height)
        cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
        
        # Create shared memory buffer
        shape = (self.output_height, self.output_width, 3)
        shm_buffer = SharedFrameBuffer(self.buffer_name, shape, create=True)
        
        frame_count = 0
        fps_start = time.time()
        last_frame_time = 0
        
        try:
            while not stop_event.is_set():
                current_time = time.time()
                
                # Frame rate limiting
                if current_time - last_frame_time < self.frame_interval:
                    time.sleep(0.001)
                    continue
                
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning("Failed to read frame, reconnecting...")
                    cap.release()
                    time.sleep(1)
                    cap = cv2.VideoCapture(self.source)
                    continue
                
                # Resize if needed
                if frame.shape[:2] != (self.output_height, self.output_width):
                    frame = cv2.resize(frame, (self.output_width, self.output_height))
                
                # Write to shared memory
                shm_buffer.write(frame)
                
                frame_count += 1
                last_frame_time = current_time
                
                # Log FPS every 5 seconds
                elapsed = current_time - fps_start
                if elapsed >= 5.0:
                    fps = frame_count / elapsed
                    logger.info(f"Camera FPS: {fps:.1f}")
                    frame_count = 0
                    fps_start = current_time
                    
        except Exception as e:
            logger.error(f"Capture error: {e}")
        finally:
            cap.release()
            shm_buffer.close()
            shm_buffer.unlink()
            logger.info("Camera capture stopped")
    
    def start(self):
        """Start camera capture in background process"""
        if self._process is not None:
            logger.warning("Camera already running")
            return
        
        self._stop_event.clear()
        self._process = Process(
            target=self._capture_loop,
            args=(self._stop_event,),
            daemon=True
        )
        self._process.start()
        logger.info("Camera process started")
    
    def stop(self):
        """Stop camera capture"""
        if self._process is None:
            return
        
        self._stop_event.set()
        self._process.join(timeout=5)
        
        if self._process.is_alive():
            self._process.terminate()
        
        self._process = None
        logger.info("Camera process stopped")
    
    def get_buffer_info(self) -> dict:
        """Get shared memory buffer information"""
        return {
            "name": self.buffer_name,
            "shape": (self.output_height, self.output_width, 3),
            "dtype": "uint8"
        }


def create_camera_from_env() -> CameraIngester:
    """Create camera instance from environment variables"""
    from dotenv import load_dotenv
    load_dotenv()
    
    source = os.getenv("CAMERA_SOURCES", "0").split(",")[0].strip()
    target_fps = int(os.getenv("TARGET_FPS", "30"))
    
    return CameraIngester(
        source=source,
        target_fps=target_fps
    )


# Test code
if __name__ == "__main__":
    camera = CameraIngester(source=0)
    camera.start()
    
    # Create reader in main process
    time.sleep(2)  # Wait for camera to initialize
    
    try:
        shape = (720, 1280, 3)
        reader = SharedFrameBuffer("frame_buffer", shape, create=False)
        
        while True:
            frame = reader.read()
            cv2.imshow("Camera Test", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        reader.close()
        camera.stop()
        cv2.destroyAllWindows()
