"""
Simplified Runner for Secure Edge Vision System
This script provides a simpler way to run the system with real-time frame processing
"""

import os
import sys
import time
import signal
import logging
import threading
from pathlib import Path
from multiprocessing import Queue
from queue import Empty

import cv2
import numpy as np
from dotenv import load_dotenv

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleEdgeVision:
    """Simplified single-process version for testing and development"""
    
    def __init__(self):
        self.running = False
        self.frame_queue = Queue(maxsize=10)
        
        # Load settings
        self.camera_source = os.getenv("CAMERA_SOURCES", "0")
        self.camera_source = int(self.camera_source) if self.camera_source.isdigit() else self.camera_source
        self.blur_intensity = int(os.getenv("BLUR_INTENSITY", "51"))
        
        # Components
        self.cap = None
        self.model = None
        self.vault = None
        
    def start(self):
        """Start the system"""
        logger.info("Starting Simple Edge Vision System...")
        
        # Open camera
        self.cap = cv2.VideoCapture(self.camera_source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera: {self.camera_source}")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        logger.info(f"Camera opened: {self.camera_source}")
        
        # Load YOLO model
        try:
            from ultralytics import YOLO
            self.model = YOLO("yolov8n.pt")
            
            # Warm up
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model.predict(dummy, device=device, verbose=False)
            logger.info(f"YOLO model loaded on {device}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
        self.running = True
        logger.info("System ready!")
        
    def stop(self):
        """Stop the system"""
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        logger.info("System stopped")
    
    def apply_blur(self, frame, boxes):
        """Apply blur to detected faces"""
        blurred = frame.copy()
        
        for box in boxes:
            x1, y1, x2, y2 = map(int, box[:4])
            
            # For person detection, estimate face region
            height = y2 - y1
            y2 = y1 + int(height * 0.3)
            
            # Ensure bounds
            h, w = frame.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            if x2 > x1 and y2 > y1:
                roi = blurred[y1:y2, x1:x2]
                blurred_roi = cv2.GaussianBlur(roi, (self.blur_intensity, self.blur_intensity), 0)
                blurred[y1:y2, x1:x2] = blurred_roi
        
        return blurred
    
    def process_frame(self, frame):
        """Process a single frame"""
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Detect
        results = self.model.predict(frame, device=device, conf=0.5, classes=[0], verbose=False)
        
        boxes = []
        if results and results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
        
        # Blur
        blurred = self.apply_blur(frame, boxes)
        
        return blurred, len(boxes)
    
    def run_live(self):
        """Run live demo with display"""
        self.start()
        
        fps_counter = 0
        fps_start = time.time()
        current_fps = 0
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("Failed to read frame")
                    continue
                
                # Process
                start = time.time()
                blurred, detections = self.process_frame(frame)
                proc_time = (time.time() - start) * 1000
                
                # Calculate FPS
                fps_counter += 1
                if time.time() - fps_start >= 1.0:
                    current_fps = fps_counter
                    fps_counter = 0
                    fps_start = time.time()
                
                # Draw info
                cv2.putText(blurred, f"FPS: {current_fps}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(blurred, f"Detections: {detections}", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(blurred, f"Process: {proc_time:.1f}ms", (10, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(blurred, "Privacy Protected - Faces Blurred", (10, blurred.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
                
                # Display
                cv2.imshow("Secure Edge Vision - Live (Press Q to quit)", blurred)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.stop()


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("  SECURE EDGE VISION - SIMPLE RUNNER")
    print("=" * 60)
    print("\nThis runs a simplified version for testing.")
    print("For full system with web interface, run: python main.py")
    print("\nPress Q to quit the live view.\n")
    
    system = SimpleEdgeVision()
    
    try:
        system.run_live()
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
