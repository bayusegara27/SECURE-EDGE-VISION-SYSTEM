"""
================================================================================
Frame Processor Module - YOLOv8 Face Detection
================================================================================
Real-time face detection and anonymization using YOLOv8.

This module provides the FrameProcessor class that handles:
1. AI-based face detection using YOLOv8-Face model
2. Gaussian blur application for privacy protection
3. GPU acceleration via CUDA for real-time processing

Architecture:
    +------------------+       +------------------+       +------------------+
    |   Input Frame    | ----> | YOLOv8 Detection | ----> |  Blur Applied    |
    |   (1280x720)     |       |   (640x640)      |       |   (Face Areas)   |
    +------------------+       +------------------+       +------------------+
                                      |
                                      v
                               [Detection List]
                               x1, y1, x2, y2, conf

Model Selection:
    - YOLOv8-Face (preferred): Trained on WIDER Face dataset, best accuracy
    - YOLOv8n (fallback): General model, estimates face from person detection

Performance (RTX 3050 4GB):
    - Detection: ~15ms per frame (640x640)
    - Blur: ~2ms per face region
    - Total: 25-30 FPS achievable

Thread Safety:
    - process() is thread-safe when used with separate FrameProcessor instances
    - Single shared instance works with proper synchronization
    - Tracking disabled in multi-camera mode for safety

Usage:
    processor = FrameProcessor(
        model_path="models/model.pt",
        device="cuda",
        confidence=0.5,
        blur_intensity=51
    )
    processor.load_model()
    
    # Process frame
    blurred, raw, detections = processor.process(frame)
    print(f"Found {len(detections)} faces")

Author: SECURE EDGE VISION SYSTEM
License: MIT
================================================================================
"""

import os
import time
import logging
from typing import List, Tuple, Dict, Any, Optional

import cv2
import numpy as np

# Configure module logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrameProcessor:
    """
    YOLOv8-based face detection and anonymization processor.
    
    This class handles real-time face detection and Gaussian blur application
    for privacy protection in video streams. It uses YOLOv8 for detection
    and supports both GPU (CUDA) and CPU processing.
    
    Key Features:
    1. AUTOMATIC MODEL SELECTION: Uses face model if available, falls back
       to general model with face region estimation.
    2. GPU ACCELERATION: Automatically uses CUDA if available.
    3. ADAPTIVE BLUR: Gaussian blur with configurable intensity.
    4. PADDING: Adds 15% padding around faces for better coverage.
    
    Attributes:
        model_path (str): Path to YOLOv8 model file
        device (str): Compute device ("cuda" or "cpu")
        confidence (float): Detection confidence threshold
        blur_intensity (int): Gaussian blur kernel size
        is_face_model (bool): True if using dedicated face detection model
        
    Detection Output Format:
        [
            {
                "x1": int,           # Left edge
                "y1": int,           # Top edge
                "x2": int,           # Right edge
                "y2": int,           # Bottom edge
                "class": str,        # "face" or "person"
                "confidence": float, # Detection confidence
                "timestamp": float   # Detection timestamp
            }
        ]
    
    Example:
        >>> processor = FrameProcessor(device="cuda", confidence=0.5)
        >>> processor.load_model()
        >>> blurred, raw, detections = processor.process(frame)
        >>> print(f"Detected {len(detections)} faces")
    """
    
    def __init__(
        self,
        model_path: str = "models/model.pt",
        device: str = "cuda",
        confidence: float = 0.5,
        blur_intensity: int = 51,
        use_face_detection: bool = True  # Kept for compatibility
    ):
        # Get absolute path relative to this file's directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Try absolute path first
        abs_model_path = os.path.join(base_dir, model_path) if not os.path.isabs(model_path) else model_path
        abs_face_model = os.path.join(base_dir, "models", "model.pt")
        
        # Try face model first, fallback to person model
        if os.path.exists(abs_face_model):
            self.model_path = abs_face_model
            self.is_face_model = True
        elif os.path.exists(abs_model_path):
            self.model_path = abs_model_path
            self.is_face_model = "face" in model_path.lower()
        elif os.path.exists(model_path):
            self.model_path = model_path
            self.is_face_model = "face" in model_path.lower()
        else:
            self.model_path = "yolov8n.pt"
            self.is_face_model = False
        
        self.device = device
        self.confidence = confidence
        self.blur_intensity = blur_intensity if blur_intensity % 2 == 1 else blur_intensity + 1
        
        self.model = None
        self._is_loaded = False
        
        # Simple tracking
        self._last_faces = []
        self._last_time = 0
        self._timeout = 0.3  # Keep faces for 300ms after lost
    
    def load_model(self) -> bool:
        """Load YOLOv8 model"""
        if self._is_loaded:
            return True
        
        try:
            from ultralytics import YOLO
            import torch
            
            # Check CUDA
            if self.device == "cuda":
                if torch.cuda.is_available():
                    logger.info(f"CUDA: {torch.cuda.get_device_name(0)}")
                else:
                    self.device = "cpu"
                    logger.warning("CUDA not available")
            
            # Load model
            self.model = YOLO(self.model_path)
            logger.info(f"Loaded: {self.model_path} ({'Face' if self.is_face_model else 'Person'} model)")
            
            # Warm up
            dummy = np.zeros((480, 480, 3), dtype=np.uint8)
            self.model.predict(dummy, device=self.device, verbose=False)
            
            self._is_loaded = True
            logger.info(f"Processor ready on {self.device.upper()}")
            return True
            
        except Exception as e:
            logger.error(f"Load error: {e}")
            return False
    
    def _detect_faces(self, frame: np.ndarray) -> List[dict]:
        """Detect faces in frame"""
        h, w = frame.shape[:2]
        now = time.time()
        
        try:
            # Run detection
            results = self.model.predict(
                frame,
                device=self.device,
                conf=self.confidence,
                verbose=False,
                imgsz=640  # Good balance of speed/accuracy
            )
            
            faces = []
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        conf = float(box.conf[0].cpu().numpy())
                        
                        # If using person model, estimate face region
                        if not self.is_face_model:
                            # Face is upper 30% of person box
                            person_h = y2 - y1
                            y2 = y1 + int(person_h * 0.30)
                        
                        # Ensure valid bounds
                        x1 = max(0, x1)
                        y1 = max(0, y1)
                        x2 = min(w, x2)
                        y2 = min(h, y2)
                        
                        if x2 > x1 and y2 > y1:
                            faces.append({
                                "x1": x1, "y1": y1,
                                "x2": x2, "y2": y2,
                                "class": "face" if self.is_face_model else "person",
                                "confidence": conf,
                                "timestamp": now
                            })
            
            # Tracking removed for thread safety in multi-camera setup
            # Each thread calls this concurrently, so shared state causes "ghost" detections
            return faces
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def _apply_blur(self, frame: np.ndarray, faces: List[dict]) -> np.ndarray:
        """Apply Gaussian blur to face regions"""
        blurred = frame.copy()
        h, w = frame.shape[:2]
        
        for face in faces:
            x1, y1, x2, y2 = face["x1"], face["y1"], face["x2"], face["y2"]
            
            # Add 15% padding for better coverage
            fw, fh = x2 - x1, y2 - y1
            pad_x = int(fw * 0.15)
            pad_y = int(fh * 0.15)
            
            x1 = max(0, x1 - pad_x)
            y1 = max(0, y1 - pad_y)
            x2 = min(w, x2 + pad_x)
            y2 = min(h, y2 + pad_y)
            
            if x2 > x1 and y2 > y1:
                roi = blurred[y1:y2, x1:x2]
                blurred_roi = cv2.GaussianBlur(
                    roi,
                    (self.blur_intensity, self.blur_intensity),
                    0
                )
                blurred[y1:y2, x1:x2] = blurred_roi
                
                # Draw Visual Indicator (Green Box) - REMOVED per user request
                # This makes the "movement" visible while keeping identity protected
                # cv2.rectangle(blurred, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
        return blurred
    
    def process(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[dict]]:
        """
        Process frame: detect faces and apply blur
        
        Returns:
            (blurred_frame, raw_frame, detections_list)
        """
        if not self._is_loaded:
            if not self.load_model():
                return frame, frame, []
        
        faces = self._detect_faces(frame)
        blurred = self._apply_blur(frame, faces)
        
        return blurred, frame, faces
    
    def get_info(self) -> dict:
        """Get processor info"""
        return {
            "model": self.model_path,
            "is_face_model": self.is_face_model,
            "device": self.device,
            "blur_intensity": self.blur_intensity,
            "is_loaded": self._is_loaded
        }
