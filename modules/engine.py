"""
Core Engine Module
Handles the main processing loop, system orchestration, and component management.
"""

import os
import time
import logging
import threading
import contextlib
from datetime import datetime
from typing import Optional
from pathlib import Path

import cv2
import numpy as np

from config import Config
from modules.processor import FrameProcessor
from modules.recorder import VideoRecorder
from modules.evidence import EvidenceManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EdgeVisionSystem:
    """Main system orchestrator - coordinates all components for multiple cameras"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.running = False
        
        # Components (one per camera)
        self.processor = None  # Shared for all cameras to save VRAM
        self.public_recorders = {}
        self.evidence_managers = {}
        self.caps = {}
        
        # Shared states
        self.latest_frames = {}  # {camera_idx: frame}
        self.latest_detections = {} # {camera_idx: count}
        self.camera_fps = {} # {camera_idx: fps}
        self.camera_status = {} # {camera_idx: "online" | "offline" | "connecting"}
        self.frame_locks = {} # {camera_idx: Lock}
        
        # FPS Stats handlers
        self.frame_counts = {}
        self.fps_starts = {}
    
    def start(self) -> None:
        """Initialize core components and metadata (cameras init in threads)"""
        logger.info("=" * 60)
        logger.info("Starting Secure Edge Vision System (Multi-Camera)")
        logger.info("=" * 60)
        
        # Initialize shared processor
        self.processor = FrameProcessor(
            model_path=self.config.model_path,
            device=self.config.device,
            confidence=self.config.confidence,
            blur_intensity=self.config.blur_intensity
        )
        if not self.processor.load_model():
            raise RuntimeError("Failed to load AI model")

        # Setup metadata and components for each camera
        for i, src in enumerate(self.config.camera_sources):
            logger.info(f"Initializing Channel {i}: {src}")
            
            self.caps[i] = None # Will be opened in thread
            self.frame_locks[i] = threading.Lock()
            self.latest_frames[i] = None
            self.latest_detections[i] = 0
            self.camera_fps[i] = 0
            self.camera_status[i] = "connecting"
            self.frame_counts[i] = 0
            self.fps_starts[i] = time.time()
            
            prefix = f"cam{i}"
            if str(src).startswith("rtsp"):
                prefix = "rtsp"
            
            self.public_recorders[i] = VideoRecorder(
                output_dir=self.config.public_path,
                prefix=f"public_{prefix}",
                fps=self.config.target_fps,
                max_duration=self.config.max_duration
            )
            
            self.evidence_managers[i] = EvidenceManager(
                output_dir=Path(self.config.evidence_path) / prefix,
                key_path=self.config.key_path,
                max_duration=self.config.max_duration,
                prefix=prefix,
                detection_only=self.config.evidence_detection_only,
                jpeg_quality=self.config.evidence_quality
            )
        
        self.running = True
        logger.info(f"System ready! All {len(self.config.camera_sources)} threads starting...")
        logger.info("=" * 60)
    
    def process_frame(self, camera_idx: int) -> bool:
        """Capture and process one frame for a specific camera. Returns False if read fails."""
        if not self.running or camera_idx not in self.caps:
            return False
        
        cap = self.caps[camera_idx]
        if cap is None:
            return False
            
        ret, frame = cap.read()
        if not ret:
            return False
        
        # 1. Smart Resize to 720p (Center-Crop to 16:9 to prevent stretching)
        target_w, target_h = 1280, 720
        h, w = frame.shape[:2]
        
        # Validate dimensions are positive
        if h <= 0 or w <= 0:
            return False
        
        target_aspect = target_w / target_h
        current_aspect = w / h
        
        if abs(current_aspect - target_aspect) > 0.01:
            # Aspect ratio mismatch - perform center crop to 16:9
            if current_aspect > target_aspect:
                # Source is wider than 16:9 - crop horizontally
                new_w = int(h * target_aspect)
                x_offset = (w - new_w) // 2
                frame = frame[:, x_offset:x_offset + new_w]
            else:
                # Source is taller than 16:9 (e.g. 4:3 or portrait) - crop vertically
                new_h = int(w / target_aspect)
                y_offset = (h - new_h) // 2
                frame = frame[y_offset:y_offset + new_h, :]
        
        # Now resize to exact 720p
        if frame.shape[1] != target_w or frame.shape[0] != target_h:
            frame = cv2.resize(frame, (target_w, target_h))
        
        # 2. Process frame (detect + blur) - uses shared model
        blurred, raw, detections = self.processor.process(frame)
        
        # 3. Record public video (blurred)
        self.public_recorders[camera_idx].write(blurred, detections=detections)
        
        # 4. Record evidence (raw) - ALWAYS, to sync with public recordings
        # Get timestamp from public recorder for matching filenames
        recorder = self.public_recorders.get(camera_idx)
        sync_timestamp = None
        if recorder and recorder.current_file:
            import re
            match = re.search(r'(\d{14})', recorder.current_file)
            if match:
                # Convert 14-digit format to 8_6 format for evidence filename
                timestamp_str = match.group(1)
                sync_timestamp = f"{timestamp_str[:8]}_{timestamp_str[8:]}"
        
        self.evidence_managers[camera_idx].add_frame(raw, detections, sync_timestamp=sync_timestamp)
        
        # Update stats
        self.frame_counts[camera_idx] += 1
        elapsed = time.time() - self.fps_starts[camera_idx]
        if elapsed >= 1.0:
            self.camera_fps[camera_idx] = self.frame_counts[camera_idx] / elapsed
            self.frame_counts[camera_idx] = 0
            self.fps_starts[camera_idx] = time.time()
        
        # 5. Apply video overlays (timestamp, debug info)
        blurred = self._apply_overlays(blurred, camera_idx, len(detections))
        
        # Update shared frame
        with self.frame_locks[camera_idx]:
            self.latest_frames[camera_idx] = blurred.copy()
            self.latest_detections[camera_idx] = len(detections)
        
        return True

    def _apply_overlays(self, frame: np.ndarray, camera_idx: int, det_count: int) -> np.ndarray:
        """Draw timestamp and debug info on frame"""
        show_ts = getattr(self.config, 'show_timestamp', True)
        show_debug = getattr(self.config, 'show_debug_overlay', False)
        
        if not show_ts and not show_debug:
            return frame
            
        h, w = frame.shape[:2]
        
        # 1. Draw Timestamp (Top Right)
        if show_ts:
            ts_text = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.7
            thickness = 2
            
            size = cv2.getTextSize(ts_text, font, scale, thickness)[0]
            tx = w - size[0] - 20
            ty = 30
            
            # Text background
            cv2.rectangle(frame, (tx - 5, ty - 25), (tx + size[0] + 5, ty + 10), (0, 0, 0), -1)
            cv2.putText(frame, ts_text, (tx, ty), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
            
        # 2. Draw Debug Overlay (Top Left)
        if show_debug:
            fps = self.camera_fps.get(camera_idx, 0)
            status = self.camera_status.get(camera_idx, "offline")
            
            debug_lines = [
                f"CAM {camera_idx}",
                f"FPS: {fps:.1f}",
                f"DET: {det_count}",
                f"STAT: {status.upper()}"
            ]
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.5
            thickness = 1
            
            cv2.rectangle(frame, (10, 10), (160, 15 + (len(debug_lines) * 20)), (0, 0, 0), -1)
            
            status_color = (0, 255, 0) if status == "online" else (0, 0, 255)
            for i, line in enumerate(debug_lines):
                color = (255, 255, 255)
                if "STAT" in line: color = status_color
                cv2.putText(frame, line, (20, 30 + (i * 20)), font, scale, color, thickness, cv2.LINE_AA)
                
        return frame
    
    def get_frame(self, camera_idx: int) -> tuple:
        """Get latest frame for streaming for specific camera"""
        if camera_idx not in self.frame_locks:
            return None, 0, 0
            
        with self.frame_locks[camera_idx]:
            if self.latest_frames[camera_idx] is not None:
                return self.latest_frames[camera_idx].copy(), self.latest_detections[camera_idx], self.camera_fps.get(camera_idx, 0)
            return None, 0, 0
    
    def stop(self) -> None:
        """Stop all components"""
        logger.info("Stopping system...")
        self.running = False
        
        for idx, cap in self.caps.items():
            if cap is not None:
                cap.release()
            
        for idx, rec in self.public_recorders.items():
            if rec is not None:
                rec.close()
            
        for idx, env in self.evidence_managers.items():
            if env is not None:
                env.stop()  # Gracefully stop background worker
        
        logger.info("System stopped")


# ============================================================
# Global Instance
# ============================================================

_system: Optional[EdgeVisionSystem] = None


def get_system() -> EdgeVisionSystem:
    """Get or create system instance"""
    global _system
    if _system is None:
        _system = EdgeVisionSystem()
    return _system


def processing_loop(camera_idx: int):
    """Background processing loop with auto-reconnect logic"""
    system = get_system()
    src = system.config.camera_sources[camera_idx]
    target_fps = system.config.target_fps
    frame_time = 1.0 / target_fps
    
    while system.running:
        try:
            # 1. Check/Open Connection
            if system.caps[camera_idx] is None:
                system.camera_status[camera_idx] = "connecting"
                logger.info(f"[Cam {camera_idx}] Attempting to connect to: {src}")
                
                # Use CAP_FFMPEG for RTSP, CAP_DSHOW for local webcams on Windows
                backend = cv2.CAP_ANY
                if isinstance(src, str) and src.startswith("rtsp"):
                    backend = cv2.CAP_FFMPEG
                    # Force TCP and set short timeout (5 seconds = 5,000,000 microseconds)
                    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"
                
                # Handle local webcams on Windows
                elif os.name == 'nt' and isinstance(src, int):
                    backend = cv2.CAP_DSHOW
                
                # Open video capture
                cap = cv2.VideoCapture(src, backend)

                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FPS, target_fps)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    system.caps[camera_idx] = cap
                    system.camera_status[camera_idx] = "online"
                    logger.info(f"[Cam {camera_idx}] Connected successfully")
                    logger.info(f"AUDIT: Camera {camera_idx} ({src}) reconnected")
                else:
                    logger.warning(f"[Cam {camera_idx}] Connection failed, retrying in 5s...")
                    system.camera_status[camera_idx] = "offline"
                    # Use short sleeps to allow graceful shutdown
                    for _ in range(50):  # 5 seconds total
                        if not system.running:
                            return
                        time.sleep(0.1)
                    continue

            # 2. Process Session
            start = time.time()
            success = system.process_frame(camera_idx)
            
            if not success:
                logger.error(f"[Cam {camera_idx}] Feed lost or read error")
                logger.info(f"AUDIT: Camera {camera_idx} ({src}) connection lost")
                
                system.camera_status[camera_idx] = "offline"
                
                # IMPORTANT: Finalize recordings immediately so they are viewable
                if camera_idx in system.public_recorders:
                    system.public_recorders[camera_idx].close()
                if camera_idx in system.evidence_managers:
                    system.evidence_managers[camera_idx].close()
                
                if system.caps[camera_idx]:
                    system.caps[camera_idx].release()
                system.caps[camera_idx] = None
                
                # Use short sleeps to allow graceful shutdown list
                for _ in range(20):  # 2 seconds total
                    if not system.running:
                        return
                    time.sleep(0.1)
                continue

            # 3. Rate Limit
            elapsed = time.time() - start
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            
        except Exception as e:
            logger.error(f"Critical error (Cam {camera_idx}): {e}")
            system.camera_status[camera_idx] = "offline"
            
            # Reset camera connection on critical error to prevent memory leak
            if system.caps.get(camera_idx):
                try:
                    system.caps[camera_idx].release()
                except:
                    pass
                system.caps[camera_idx] = None
            
            if not system.running:
                return
            
            # Longer sleep to prevent rapid error loops causing memory leak
            time.sleep(2.0)
