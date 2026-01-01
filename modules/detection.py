"""
Face Detection and Blurring Module
YOLO-based face detection with GPU acceleration and dual-path output
"""

import cv2
import numpy as np
import time
import logging
import os
from multiprocessing import Process, Event, Queue
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Face detection result"""
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    timestamp: float


class FaceDetector:
    """
    YOLO-based face detection with Gaussian blur anonymization
    Outputs to both public (blurred) and evidence (raw) queues
    """
    
    def __init__(
        self,
        model_path: str = "models/yolov8n-face.pt",
        confidence_threshold: float = 0.5,
        device: str = "cuda",
        blur_intensity: int = 51
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.blur_intensity = blur_intensity if blur_intensity % 2 == 1 else blur_intensity + 1
        
        self._model = None
        self._stop_event = Event()
        self._process: Optional[Process] = None
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            from ultralytics import YOLO
            
            # Check if custom face model exists, otherwise use default
            if os.path.exists(self.model_path):
                self._model = YOLO(self.model_path)
                logger.info(f"Loaded custom model: {self.model_path}")
            else:
                # Use pre-trained YOLOv8n and filter for 'person' class
                # For face detection, we'll use a face-specific approach
                self._model = YOLO("yolov8n.pt")
                logger.info("Loaded default YOLOv8n model (will detect persons)")
            
            # Warm up model on GPU
            if self.device == "cuda":
                import torch
                if torch.cuda.is_available():
                    dummy = np.zeros((640, 640, 3), dtype=np.uint8)
                    self._model.predict(dummy, device=self.device, verbose=False)
                    logger.info(f"Model warmed up on {self.device}")
                else:
                    self.device = "cpu"
                    logger.warning("CUDA not available, using CPU")
            
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def _apply_blur(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Apply Gaussian blur to detected face regions"""
        blurred = frame.copy()
        
        for det in detections:
            # Extract face region
            x1, y1, x2, y2 = det.x1, det.y1, det.x2, det.y2
            
            # Ensure coordinates are within frame bounds
            h, w = frame.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            if x2 > x1 and y2 > y1:
                # Apply Gaussian blur
                roi = blurred[y1:y2, x1:x2]
                blurred_roi = cv2.GaussianBlur(roi, (self.blur_intensity, self.blur_intensity), 0)
                blurred[y1:y2, x1:x2] = blurred_roi
        
        return blurred
    
    def detect_faces(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Detection]]:
        """
        Detect faces and return blurred frame with detection list
        Returns: (blurred_frame, detections)
        """
        if self._model is None:
            if not self._load_model():
                return frame, []
        
        timestamp = time.time()
        detections = []
        
        try:
            # Run inference
            results = self._model.predict(
                frame,
                device=self.device,
                conf=self.confidence_threshold,
                classes=[0],  # Person class for COCO, or face class if using face model
                verbose=False
            )
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        conf = float(box.conf[0].cpu().numpy())
                        
                        # For person detection, estimate face region (upper portion)
                        # If using face model, use full box
                        if "face" not in self.model_path.lower():
                            # Estimate face as upper 30% of person bounding box
                            height = y2 - y1
                            y2 = y1 + int(height * 0.3)
                        
                        detections.append(Detection(
                            x1=x1, y1=y1, x2=x2, y2=y2,
                            confidence=conf,
                            timestamp=timestamp
                        ))
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
        
        # Apply blur to detected regions
        blurred_frame = self._apply_blur(frame, detections)
        
        return blurred_frame, detections
    
    def _detection_loop(
        self,
        buffer_name: str,
        buffer_shape: Tuple[int, int, int],
        public_queue: Queue,
        evidence_queue: Queue,
        stop_event: Event
    ):
        """Main detection loop running in separate process"""
        from modules.camera import SharedFrameBuffer
        
        logger.info("Detection process starting...")
        
        # Load model in this process
        if not self._load_model():
            logger.error("Failed to load model in detection process")
            return
        
        # Connect to shared memory
        time.sleep(1)  # Wait for camera to create buffer
        
        try:
            frame_buffer = SharedFrameBuffer(buffer_name, buffer_shape, create=False)
        except FileNotFoundError:
            logger.error("Shared memory buffer not found")
            return
        
        frame_count = 0
        fps_start = time.time()
        last_frame = None
        
        try:
            while not stop_event.is_set():
                # Read frame from shared memory
                frame = frame_buffer.read()
                
                # Skip if frame hasn't changed (simple check)
                if last_frame is not None and np.array_equal(frame, last_frame):
                    time.sleep(0.001)
                    continue
                
                last_frame = frame.copy()
                
                # Detect and blur
                blurred_frame, detections = self.detect_faces(frame)
                
                # Send to public queue (blurred)
                if not public_queue.full():
                    public_queue.put({
                        "frame": blurred_frame,
                        "detections": len(detections),
                        "timestamp": time.time()
                    })
                
                # Send to evidence queue (raw) only if faces detected
                if len(detections) > 0 and not evidence_queue.full():
                    evidence_queue.put({
                        "frame": frame,
                        "detections": detections,
                        "timestamp": time.time()
                    })
                
                frame_count += 1
                
                # Log FPS
                elapsed = time.time() - fps_start
                if elapsed >= 5.0:
                    fps = frame_count / elapsed
                    logger.info(f"Detection FPS: {fps:.1f}")
                    frame_count = 0
                    fps_start = time.time()
                    
        except Exception as e:
            logger.error(f"Detection loop error: {e}")
        finally:
            frame_buffer.close()
            logger.info("Detection process stopped")
    
    def start(
        self,
        buffer_name: str,
        buffer_shape: Tuple[int, int, int],
        public_queue: Queue,
        evidence_queue: Queue
    ):
        """Start detection in background process"""
        if self._process is not None:
            logger.warning("Detector already running")
            return
        
        self._stop_event.clear()
        self._process = Process(
            target=self._detection_loop,
            args=(buffer_name, buffer_shape, public_queue, evidence_queue, self._stop_event),
            daemon=True
        )
        self._process.start()
        logger.info("Detection process started")
    
    def stop(self):
        """Stop detection process"""
        if self._process is None:
            return
        
        self._stop_event.set()
        self._process.join(timeout=5)
        
        if self._process.is_alive():
            self._process.terminate()
        
        self._process = None
        logger.info("Detection process stopped")


def create_detector_from_env() -> FaceDetector:
    """Create detector from environment variables"""
    from dotenv import load_dotenv
    load_dotenv()
    
    return FaceDetector(
        model_path=os.getenv("MODEL_PATH", "models/yolov8n-face.pt"),
        confidence_threshold=float(os.getenv("DETECTION_CONFIDENCE", "0.5")),
        device=os.getenv("DEVICE", "cuda"),
        blur_intensity=int(os.getenv("BLUR_INTENSITY", "51"))
    )


# Test code
if __name__ == "__main__":
    detector = FaceDetector(device="cuda")
    
    cap = cv2.VideoCapture(0)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            blurred, detections = detector.detect_faces(frame)
            
            # Draw info
            cv2.putText(
                blurred,
                f"Faces: {len(detections)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            
            cv2.imshow("Face Detector Test", blurred)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
