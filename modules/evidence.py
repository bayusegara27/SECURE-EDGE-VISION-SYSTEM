"""
Evidence Manager Module
Handles encrypted evidence storage with AES-256-GCM
"""

import os
import time
import pickle
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List

import cv2
import numpy as np

from modules.security import SecureVault

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvidenceManager:
    """
    Manages encrypted evidence storage
    Buffers frames and saves to encrypted .enc files
    Names match public recordings: evidence_{prefix}_{timestamp}_{count}.enc
    """
    
    def __init__(
        self,
        output_dir: str,
        key_path: str = "keys/master.key",
        max_duration: int = 300,  # 5 minutes per file
        prefix: str = "cam0",
        detection_only: bool = True,
        jpeg_quality: int = 75
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.key_path = key_path
        self.max_duration = max_duration
        self.prefix = prefix
        self.detection_only = detection_only
        self.jpeg_quality = jpeg_quality
        
        # Ensure key directory exists
        Path(key_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.vault: Optional[SecureVault] = None
        self.buffer: List[dict] = []
        self.pre_roll: List[dict] = [] # Circular buffer for context before detection
        self.pre_roll_size = 30 # ~1 second at 30fps
        
        self.buffer_start: Optional[float] = None
        self.file_count = 0
        self.current_target: Optional[str] = None
        self.sync_timestamp: Optional[str] = None
    
    def _init_vault(self) -> None:
        """Initialize encryption vault"""
        if self.vault is None:
            self.vault = SecureVault(key_path=self.key_path)
            logger.info("Encryption vault initialized")
    
    def add_frame(
        self,
        frame: np.ndarray,
        detections: List[dict],
        timestamp: Optional[float] = None,
        sync_timestamp: Optional[str] = None
    ) -> None:
        """
        Add frame to buffer with optional selective recording and pre-roll
        """
        self._init_vault()
        
        if timestamp is None:
            timestamp = time.time()
        
        # 1. Encode frame early to store in buffers
        _, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        frame_data = {
            "frame_jpg": encoded.tobytes(),
            "detections": detections,
            "timestamp": timestamp
        }

        # 2. Handle Selective Recording (Avoid saving empty footage)
        if self.detection_only:
            if not detections:
                # Add to pre-roll circular buffer for potential future detection context
                self.pre_roll.append(frame_data)
                if len(self.pre_roll) > self.pre_roll_size:
                    self.pre_roll.pop(0)
                
                # If buffer is active, we might want to keep recording for a few frames after detection lost
                # But for simplicity, we stop here if no detections.
                if not self.buffer:
                    return
            else:
                # Detection found! 
                # If this is the start of a new event, prep the buffer with pre-roll
                if not self.buffer:
                    self.buffer.extend(self.pre_roll)
                    self.pre_roll = []
                    self.buffer_start = self.buffer[0]["timestamp"]
        
        # 3. Standard Buffer Handling
        if self.buffer_start is None:
            self.buffer_start = timestamp
            if sync_timestamp:
                self.sync_timestamp = sync_timestamp
            else:
                target_ts = datetime.fromtimestamp(timestamp)
                self.sync_timestamp = target_ts.strftime('%Y%m%d_%H%M%S')
            self.current_target = f"evidence_{self.prefix}_{self.sync_timestamp}_{self.file_count:04d}.enc"
        
        self.buffer.append(frame_data)
        
        # Auto-flush if duration exceeded (based on wall clock, not frame count)
        if (timestamp - self.buffer_start) >= self.max_duration:
            self.flush()
    
    def flush(self, blocking: bool = True) -> Optional[str]:
        """
        Save buffer to encrypted file
        
        Args:
            blocking: If False, run encryption in background thread
        """
        if not self.buffer:
            return None
        
        self._init_vault()
        
        # Copy buffer for encryption
        buffer_copy = self.buffer.copy()
        buffer_start = self.buffer_start
        file_count = self.file_count
        
        # Reset buffer immediately but save sync_timestamp for encryption
        sync_ts = self.sync_timestamp
        self.buffer = []
        self.buffer_start = None
        self.current_target = None
        self.sync_timestamp = None
        self.file_count += 1
        
        def encrypt_and_save():
            # Serialize buffer
            data = pickle.dumps(buffer_copy)
            
            # Generate filename using synced timestamp + prefix
            if sync_ts:
                filename = f"evidence_{self.prefix}_{sync_ts}_{file_count:04d}.enc"
            else:
                # Fallback to buffer_start timestamp if sync failed
                dt = datetime.fromtimestamp(buffer_start)
                filename = f"evidence_{self.prefix}_{dt.strftime('%Y%m%d_%H%M%S')}_{file_count:04d}.enc"
            filepath = self.output_dir / filename
            
            # Metadata
            metadata = {
                "frame_count": len(buffer_copy),
                "start_time": buffer_start,
                "end_time": buffer_copy[-1]["timestamp"],
                "total_detections": sum(len(f["detections"]) for f in buffer_copy)
            }
            
            # Save encrypted
            self.vault.save_encrypted_file(data, str(filepath), metadata)
            
            logger.info(f"Saved encrypted evidence: {filename} ({len(buffer_copy)} frames)")
            return str(filepath)
        
        if blocking:
            return encrypt_and_save()
        else:
            # Run in background thread
            import threading
            thread = threading.Thread(target=encrypt_and_save, daemon=True)
            thread.start()
            return None
    
    def close(self) -> None:
        """Flush remaining buffer (blocking) and close"""
        if self.buffer:
            # Use blocking mode for final flush to ensure data is saved
            self.flush(blocking=True)
    
    def stop(self) -> None:
        """Alias for close() - for compatibility with engine shutdown"""
        self.close()
    
    def get_evidence_list(self) -> list:
        """Get list of evidence files"""
        evidence = []
        for f in sorted(self.output_dir.glob("*.enc"), reverse=True):
            stat = f.stat()
            is_active = (f.name == self.current_target)
            evidence.append({
                "filename": f.name,
                "path": str(f),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "status": "encrypted",
                "is_active": is_active
            })
        return evidence
