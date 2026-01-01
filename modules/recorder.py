"""
Video Recorder Module
Handles public MP4 recording with automatic file rotation
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import tempfile

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class VideoRecorder:
    """
    Records video to MP4 files with automatic rotation
    Used for public (blurred) recordings
    """
    
    def __init__(
        self,
        output_dir: str,
        prefix: str = "recording",
        fps: int = 30,
        max_duration: int = 300,  # 5 minutes
        resolution: tuple = (1280, 720)
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.prefix = prefix
        self.fps = fps
        self.max_duration = max_duration
        self.resolution = resolution
        
        self.writer: Optional[cv2.VideoWriter] = None
        self.current_file: Optional[str] = None
        self.frame_count = 0
        self.start_time: Optional[float] = None
        self._force_rotate = False
        self.detection_events = []  # List of frame indices with detections
    
    def _create_writer(self, frame_shape: tuple) -> None:
        """Create new video writer"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.prefix}_{timestamp}.mp4"
        filepath = self.output_dir / filename
        
        h, w = frame_shape[:2]
        
        # Try standard codecs. Priority: 
        # 1. avc1 (H.264, Best for Web/Dashboard Replay)
        # 2. X264 (H.264 fallback)
        # 3. mp4v (MPEG-4, common but often NOT playable in browsers)
        # 4. MJPG (universal fallback)
        codecs = ['avc1', 'X264', 'mp4v', 'MJPG']
        
        for codec in codecs:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            ext = ".mp4" if codec != 'MJPG' else ".avi"
            out_file = str(filepath.with_suffix(ext))
            
            # Use a slightly lower FPS if we hit MJPG as it's heavy on disk but very stable
            self.writer = cv2.VideoWriter(out_file, fourcc, self.fps, (w, h))
            
            # PRE-FLIGHT CHECK: On Windows, isOpened() can return True even if 
            # the codec fails later. We write a single blank frame to verify.
            if self.writer.isOpened():
                blank = np.zeros(frame_shape, dtype=np.uint8)
                self.writer.write(blank)
                # If write() didn't crash and isOpened is still true, we use it
                if self.writer.isOpened():
                    self.current_file = out_file
                    logger.info(f"OpenCV: Using codec {codec} for {Path(out_file).name}")
                    break
            
            self.writer.release()
            self.writer = None
        
        if self.writer is None or not self.writer.isOpened():
            # Nuclear fallback: XVID or raw
            self.current_file = str(filepath.with_suffix(".avi"))
            self.writer = cv2.VideoWriter(self.current_file, cv2.VideoWriter_fourcc(*'XVID'), self.fps, (w, h))
            if self.writer is None or not self.writer.isOpened():
                self.writer = cv2.VideoWriter(self.current_file, 0, self.fps, (w, h))
        
        # REMOVED: self.current_file = str(filepath) - This was overwriting the correct path!
        self.frame_count = 0
        self.start_time = time.time()
        self.detection_events = [] # Reset events for new file
        
        logger.info(f"Started recording: {filename}")
    
    def _save_metadata(self) -> None:
        """Save detection metadata to JSON file"""
        if not self.current_file or not self.detection_events:
            return
            
        import json
        meta_file = Path(self.current_file).with_suffix('.json')
        try:
            metadata = {
                "filename": Path(self.current_file).name,
                "fps": self.fps,
                "total_frames": self.frame_count,
                "detections": self.detection_events
            }
            with open(meta_file, 'w') as f:
                json.dump(metadata, f)
            logger.debug(f"Saved metadata: {meta_file.name}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def _should_rotate(self) -> bool:
        """Check if should rotate to new file"""
        if self._force_rotate:
            self._force_rotate = False
            return True
        if self.start_time is None:
            return True
        return (time.time() - self.start_time) >= self.max_duration
    
    def rotate(self) -> None:
        """Force rotation on next write"""
        self._force_rotate = True
    
    def write(self, frame: np.ndarray, detections: list = None) -> None:
        """Write frame to video"""
        if self.writer is None or self._should_rotate():
            if self.writer is not None:
                self._save_metadata() # Save for previous file
                self.writer.release()
                logger.info(f"Finished: {self.current_file} ({self.frame_count} frames)")
            self._create_writer(frame.shape)
        
        if frame.shape[:2] != (self.resolution[1], self.resolution[0]):
            frame = cv2.resize(frame, self.resolution)
        
        self.writer.write(frame)
        if detections:
            # Store frame index and unique classes found in this frame
            classes = list(set([d.get("class", "unknown") for d in detections]))
            self.detection_events.append({
                "f": self.frame_count,
                "c": classes
            })
        self.frame_count += 1
    
    def close(self) -> None:
        """Close video writer"""
        if self.writer is not None:
            self._save_metadata()
            self.writer.release()
            if self.current_file:
                logger.info(f"Closed: {self.current_file}")
            self.writer = None
    
    def stop(self) -> None:
        """Alias for close() - for consistency with other modules"""
        self.close()
    
    def get_recording_list(self) -> list:
        """Get list of recordings"""
        recordings = []
        recordings = []
        # Support both .mp4 and .avi (for fallback codecs)
        files = []
        for ext in ['*.mp4', '*.avi']:
            files.extend(list(self.output_dir.glob(f"{self.prefix}_{ext}")))
            
        for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
            stat = f.stat()
            is_active = (str(f) == self.current_file)
            
            # If active, force size update from writer interaction if possible, 
            # or just use file size on disk which might be lagging slightly.
            
            recordings.append({
                "filename": f.name,
                "path": str(f),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_active": is_active
            })
        return recordings
