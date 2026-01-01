"""
Frame Processor Module - YOLOv8-Face Detection
Uses specialized face detection model for accurate, real-time face blur
Optimized for RTX 3050 4GB GPU
"""

import os
import time
import logging
from typing import List, Tuple

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrameProcessor:
    """
    YOLOv8-Face based processor for real-time face anonymization
    
    Features:
    - Uses YOLOv8-Face model trained on WIDER Face dataset
    - GPU accelerated (CUDA)
    - Simple tracking for smoother blur
    - Optimized for RTX 3050 4GB (25-30 FPS)
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
