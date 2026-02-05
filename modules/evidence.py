"""
================================================================================
Evidence Manager Module
================================================================================
Handles encrypted evidence storage with AES-256-GCM encryption.

This module provides the EvidenceManager class that handles secure storage of
raw (unblurred) video frames as encrypted evidence files. Key features:

- ENCRYPTED STORAGE: All frames encrypted with AES-256-GCM
- NON-BLOCKING FLUSH: Encryption runs in background thread
- SELECTIVE RECORDING: Only saves frames with detections (80% storage saving)
- PRE-ROLL BUFFER: Captures context before detection starts
- INTEGRITY PROTECTION: SHA-256 hash embedded for tamper detection

Architecture:
    +------------------+       +-------------------+
    |   Camera Thread  | ----> |  EvidenceManager  |
    +------------------+       +-------------------+
                                      |
                        +-------------+-------------+
                        |                           |
                   [Frame Buffer]          [Background Thread]
                   Collects frames         Encrypts & saves .enc

Evidence File Format (.enc):
    - 12 bytes: AES-GCM Nonce
    - 8 bytes: Timestamp (double)
    - 4 bytes: Metadata length
    - N bytes: Metadata (JSON)
    - Rest: AES-GCM Ciphertext (contains SHA-256 hash + pickled frames)

Usage:
    manager = EvidenceManager(
        output_dir="recordings/evidence/cam0",
        key_path="keys/master.key",
        detection_only=True
    )
    
    while streaming:
        manager.add_frame(raw_frame, detections)
    
    manager.close()

Thread Safety:
    - add_frame() is called from camera thread (single producer)
    - Encryption/save runs in dedicated background worker thread
    - Queue-based communication for non-blocking operation

Author: SECURE EDGE VISION SYSTEM
License: MIT
================================================================================
"""

import os
import time
import pickle
import logging
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

import cv2
import numpy as np

from modules.security import SecureVault

# Configure module logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvidenceManager:
    """
    Manages encrypted evidence storage with non-blocking I/O.
    
    This class handles secure storage of raw video frames as encrypted
    evidence files. It implements several features:
    
    1. SELECTIVE RECORDING: Only records frames that contain detections,
       saving up to 80% storage compared to continuous recording.
       
    2. PRE-ROLL BUFFER: Maintains a circular buffer of recent frames
       so that when a detection starts, context frames are included.
       
    3. NON-BLOCKING ENCRYPTION: All encryption and file I/O happens
       in a dedicated background thread, not blocking the camera loop.
       
    4. INTEGRITY PROTECTION: Each file includes SHA-256 hash for
       tamper detection during decryption.
    
    Attributes:
        output_dir (Path): Directory where .enc files are saved
        key_path (str): Path to encryption key file
        max_duration (int): Max seconds of recording before auto-flush
        prefix (str): Camera identifier prefix for filenames
        detection_only (bool): If True, only record when detections present
        jpeg_quality (int): JPEG compression quality for frame storage
        
        vault (SecureVault): Encryption vault instance
        buffer (List[dict]): Current frame buffer
        pre_roll (List[dict]): Circular buffer for context frames
        
    Example:
        >>> manager = EvidenceManager("evidence/cam0", detection_only=True)
        >>> manager.add_frame(frame, [{"class": "face", "x1": 100}])
        >>> manager.close()
    """
    
    # ==========================================================================
    # INITIALIZATION
    # ==========================================================================
    
    def __init__(
        self,
        output_dir: str,
        key_path: str = "keys/master.key",
        max_duration: int = 300,  # 5 minutes per file
        prefix: str = "cam0",
        detection_only: bool = True,
        jpeg_quality: int = 75
    ):
        """
        Initialize the EvidenceManager.
        
        Args:
            output_dir: Directory where encrypted evidence files (.enc) will
                        be saved. Will be created if it doesn't exist.
            key_path: Path to the AES-256 encryption key file. If the file
                      doesn't exist, a new key will be generated (backup it!).
            max_duration: Maximum recording duration in seconds before the
                          buffer is automatically flushed to a file. Default
                          300 seconds (5 minutes).
            prefix: Camera identifier prefix used in filenames. Example:
                    "cam0" produces "evidence_cam0_20240115_120000_0001.enc"
            detection_only: If True, only record frames that contain detections.
                            Pre-roll buffer provides context before detections.
                            This can save up to 80% storage. Default True.
            jpeg_quality: JPEG compression quality (0-100) for frame storage.
                          Lower = smaller files but lower quality. Default 75.
        
        Example:
            >>> manager = EvidenceManager(
            ...     output_dir="recordings/evidence/cam0",
            ...     key_path="keys/master.key",
            ...     max_duration=300,
            ...     prefix="cam0",
            ...     detection_only=True,
            ...     jpeg_quality=75
            ... )
        """
        # --------------------------------------------------
        # Output Directory Setup
        # --------------------------------------------------
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # --------------------------------------------------
        # Encryption Configuration
        # --------------------------------------------------
        self.key_path = key_path
        # Ensure key directory exists
        Path(key_path).parent.mkdir(parents=True, exist_ok=True)
        
        # --------------------------------------------------
        # Recording Parameters
        # --------------------------------------------------
        self.max_duration = max_duration
        self.prefix = prefix
        self.detection_only = detection_only
        self.jpeg_quality = jpeg_quality
        
        # --------------------------------------------------
        # Encryption Vault (lazy initialization)
        # --------------------------------------------------
        self.vault: Optional[SecureVault] = None
        
        # --------------------------------------------------
        # Frame Buffer
        # --------------------------------------------------
        self.buffer: List[Dict[str, Any]] = []          # Main frame buffer
        self.pre_roll: List[Dict[str, Any]] = []        # Context buffer
        self.pre_roll_size = 30                          # ~1 second at 30fps
        
        # --------------------------------------------------
        # Buffer State
        # --------------------------------------------------
        self.buffer_start: Optional[float] = None        # Buffer start timestamp
        self.file_count = 0                              # Sequential file counter
        self.current_target: Optional[str] = None        # Current target filename
        self.sync_timestamp: Optional[str] = None        # Timestamp for sync
        
        # --------------------------------------------------
        # Background Worker Thread
        # --------------------------------------------------
        self._encrypt_queue: queue.Queue = queue.Queue()
        self._encrypt_thread: Optional[threading.Thread] = None
        self._stop_worker = False
        
        # Start background encryption worker
        self._start_encrypt_worker()
    
    # ==========================================================================
    # ENCRYPTION VAULT MANAGEMENT
    # ==========================================================================
    
    def _init_vault(self) -> None:
        """
        Initialize encryption vault (lazy initialization).
        
        The vault is initialized on first use to avoid loading the key
        file if no evidence is ever recorded. This also allows the key
        to be generated at runtime if it doesn't exist.
        
        Side Effects:
            - Sets self.vault to a SecureVault instance
            - May create new key file if key_path doesn't exist
        """
        if self.vault is None:
            self.vault = SecureVault(key_path=self.key_path)
            logger.info(f"[{self.prefix}] Encryption vault initialized")
    
    # ==========================================================================
    # BACKGROUND WORKER THREAD
    # ==========================================================================
    
    def _start_encrypt_worker(self) -> None:
        """
        Start background thread for non-blocking encryption.
        
        This thread handles:
        1. Pickle serialization of frame buffers (can be slow for large buffers)
        2. AES-256-GCM encryption
        3. File writing
        
        The thread runs continuously, waiting for items in the encrypt queue.
        When flush() is called, it pushes the buffer to this queue instead
        of blocking to encrypt inline.
        """
        self._stop_worker = False
        self._encrypt_thread = threading.Thread(
            target=self._encrypt_worker_loop,
            daemon=True,
            name=f"Encrypt-{self.prefix}"
        )
        self._encrypt_thread.start()
        logger.debug(f"[{self.prefix}] Encrypt worker thread started")
    
    def _encrypt_worker_loop(self) -> None:
        """
        Worker loop that processes encryption queue.
        
        This runs in a background thread and waits for encryption jobs.
        Each job is a tuple: (buffer_copy, metadata, filepath)
        
        Processing each job:
        1. Pickle serialize the buffer
        2. Encrypt with AES-256-GCM
        3. Write to file
        4. Log completion
        
        The loop exits when _stop_worker is True and queue is empty.
        """
        while not self._stop_worker or not self._encrypt_queue.empty():
            try:
                # Wait for encryption job with timeout
                job = self._encrypt_queue.get(timeout=0.5)
                
                # Unpack job data
                buffer_copy, metadata, filepath = job
                
                # --------------------------------------------------
                # Perform Encryption (potentially slow)
                # --------------------------------------------------
                try:
                    # 1. Serialize buffer with pickle
                    data = pickle.dumps(buffer_copy)
                    
                    # 2. Encrypt and save to file
                    self.vault.save_encrypted_file(data, str(filepath), metadata)
                    
                    logger.info(
                        f"[BG] Saved evidence: {filepath.name} "
                        f"({len(buffer_copy)} frames, {len(data)/1024:.1f} KB)"
                    )
                except Exception as e:
                    logger.error(f"[BG] Encryption error: {e}")
                
                # Mark job as done
                self._encrypt_queue.task_done()
                
            except queue.Empty:
                # No jobs to process, continue loop
                continue
            except Exception as e:
                logger.error(f"[BG] Encrypt worker error: {e}")
    
    # ==========================================================================
    # FRAME BUFFERING
    # ==========================================================================
    
    def add_frame(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        timestamp: Optional[float] = None,
        sync_timestamp: Optional[str] = None
    ) -> None:
        """
        Add frame to buffer with optional selective recording.
        
        This is the main method called for each frame. It handles:
        1. JPEG encoding of the frame
        2. Selective recording logic (skip frames without detections)
        3. Pre-roll buffer management
        4. Auto-flush when max_duration exceeded
        
        Selective Recording Logic:
        - If detection_only=True and no detections:
          - Frame is added to pre_roll circular buffer only
          - If main buffer is empty, frame is discarded (storage saving)
        - If detection found:
          - Pre-roll frames are moved to main buffer for context
          - Frame is added to main buffer
        
        Args:
            frame: Raw video frame as numpy array (BGR, HxWx3)
            detections: List of detection dicts. Empty list = no detections.
            timestamp: Optional Unix timestamp. If None, uses time.time().
            sync_timestamp: Optional timestamp string for filename sync
                            with public recordings (format: YYYYMMDD_HHMMSS)
        
        Example:
            >>> manager.add_frame(frame, [{"class": "face", "x1": 100}])
            >>> manager.add_frame(frame, [])  # No detections
        """
        # Initialize vault on first use
        self._init_vault()
        
        # Use current time if no timestamp provided
        if timestamp is None:
            timestamp = time.time()
        
        # --------------------------------------------------
        # 1. Encode Frame as JPEG
        # --------------------------------------------------
        # JPEG encoding is done early to minimize memory usage in buffers
        _, encoded = cv2.imencode(
            '.jpg', 
            frame, 
            [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
        )
        
        # Create frame data structure
        frame_data = {
            "frame_jpg": encoded.tobytes(),   # JPEG-encoded frame bytes
            "detections": detections,          # Detection list
            "timestamp": timestamp             # Unix timestamp
        }
        
        # --------------------------------------------------
        # 2. Handle Selective Recording
        # --------------------------------------------------
        if self.detection_only:
            if not detections:
                # NO DETECTION: Add to pre-roll only
                # Pre-roll is a circular buffer that keeps context frames
                self.pre_roll.append(frame_data)
                if len(self.pre_roll) > self.pre_roll_size:
                    self.pre_roll.pop(0)  # Remove oldest
                
                # If main buffer is empty, we're in "idle" mode
                # Don't save frames without detections (storage saving)
                if not self.buffer:
                    return
            else:
                # DETECTION FOUND!
                # If this is the start of a new recording event,
                # include pre-roll frames for context
                if not self.buffer:
                    # Move pre-roll to main buffer
                    self.buffer.extend(self.pre_roll)
                    self.pre_roll = []
                    
                    # Set buffer_start from first pre-roll frame if available
                    if self.buffer:
                        self.buffer_start = self.buffer[0]["timestamp"]
        
        # --------------------------------------------------
        # 3. Standard Buffer Handling
        # --------------------------------------------------
        # Initialize buffer start if needed
        if self.buffer_start is None:
            self.buffer_start = timestamp
            
            # Set timestamp for filename synchronization
            if sync_timestamp:
                self.sync_timestamp = sync_timestamp
            else:
                target_ts = datetime.fromtimestamp(timestamp)
                self.sync_timestamp = target_ts.strftime('%Y%m%d_%H%M%S')
            
            # Generate target filename
            self.current_target = (
                f"evidence_{self.prefix}_{self.sync_timestamp}_{self.file_count:04d}.enc"
            )
        
        # Add frame to buffer
        self.buffer.append(frame_data)
        
        # --------------------------------------------------
        # 4. Auto-Flush if Duration Exceeded
        # --------------------------------------------------
        if (timestamp - self.buffer_start) >= self.max_duration:
            self.flush(blocking=False)  # Non-blocking flush
    
    # ==========================================================================
    # BUFFER FLUSHING
    # ==========================================================================
    
    def flush(self, blocking: bool = False) -> Optional[str]:
        """
        Flush buffer to encrypted file (NON-BLOCKING by default).
        
        This method:
        1. Copies current buffer
        2. Resets buffer state immediately
        3. Queues encryption job (non-blocking) or encrypts inline (blocking)
        
        The non-blocking mode pushes the encryption work to a background
        thread, allowing the camera loop to continue immediately.
        
        Args:
            blocking: If True, encrypt and save synchronously (blocks).
                      If False (default), queue for background encryption.
        
        Returns:
            str: Filepath of saved evidence file (only for blocking=True)
            None: When non-blocking or if buffer was empty
        
        Example:
            >>> manager.flush()  # Non-blocking (recommended)
            >>> path = manager.flush(blocking=True)  # Blocking, returns path
        """
        # Nothing to flush
        if not self.buffer:
            return None
        
        # Ensure vault is initialized
        self._init_vault()
        
        # --------------------------------------------------
        # 1. Copy Buffer and State
        # --------------------------------------------------
        buffer_copy = self.buffer.copy()
        buffer_start = self.buffer_start
        file_count = self.file_count
        sync_ts = self.sync_timestamp
        
        # --------------------------------------------------
        # 2. Reset Buffer State Immediately
        # --------------------------------------------------
        # This allows new frames to be collected while encryption happens
        self.buffer = []
        self.buffer_start = None
        self.current_target = None
        self.sync_timestamp = None
        self.file_count += 1
        
        # --------------------------------------------------
        # 3. Generate Filepath
        # --------------------------------------------------
        if sync_ts:
            filename = f"evidence_{self.prefix}_{sync_ts}_{file_count:04d}.enc"
        else:
            dt = datetime.fromtimestamp(buffer_start)
            filename = f"evidence_{self.prefix}_{dt.strftime('%Y%m%d_%H%M%S')}_{file_count:04d}.enc"
        
        filepath = self.output_dir / filename
        
        # --------------------------------------------------
        # 4. Build Metadata
        # --------------------------------------------------
        metadata = {
            "frame_count": len(buffer_copy),
            "start_time": buffer_start,
            "end_time": buffer_copy[-1]["timestamp"],
            "total_detections": sum(len(f["detections"]) for f in buffer_copy),
            "camera": self.prefix,
            "jpeg_quality": self.jpeg_quality
        }
        
        # --------------------------------------------------
        # 5. Encrypt and Save
        # --------------------------------------------------
        if blocking:
            # BLOCKING: Encrypt inline
            try:
                data = pickle.dumps(buffer_copy)
                self.vault.save_encrypted_file(data, str(filepath), metadata)
                logger.info(
                    f"[{self.prefix}] Saved evidence: {filename} "
                    f"({len(buffer_copy)} frames)"
                )
                return str(filepath)
            except Exception as e:
                logger.error(f"[{self.prefix}] Encryption error: {e}")
                return None
        else:
            # NON-BLOCKING: Queue for background thread
            self._encrypt_queue.put((buffer_copy, metadata, filepath))
            return None
    
    # ==========================================================================
    # SHUTDOWN AND CLEANUP
    # ==========================================================================
    
    def close(self) -> None:
        """
        Flush remaining buffer and close manager.
        
        This method:
        1. Flushes any remaining frames (blocking to ensure save)
        2. Waits for background encryption to complete
        3. Stops the background worker thread
        
        Should be called when stopping recording to ensure all evidence is saved.
        
        Example:
            >>> manager.close()
        """
        # Flush remaining buffer (blocking to ensure it's saved)
        if self.buffer:
            self.flush(blocking=True)
        
        # Stop background worker
        self._stop_worker = True
        
        # Wait for all encryption to complete
        if self._encrypt_thread is not None and self._encrypt_thread.is_alive():
            self._encrypt_thread.join(timeout=30.0)  # Max 30 second wait
            if self._encrypt_thread.is_alive():
                logger.warning(f"[{self.prefix}] Encrypt thread still running after timeout")
        
        logger.info(f"[{self.prefix}] Evidence manager closed")
    
    def stop(self) -> None:
        """
        Alias for close() - for compatibility with engine shutdown.
        
        Example:
            >>> manager.stop()  # Same as manager.close()
        """
        self.close()
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def get_evidence_list(self) -> List[Dict[str, Any]]:
        """
        Get list of evidence files in output directory.
        
        Scans the output directory for .enc files and returns metadata
        about each file.
        
        Returns:
            List of dicts with keys:
            - filename: File name (e.g., "evidence_cam0_20240115_120000_0001.enc")
            - path: Full file path
            - size_mb: File size in megabytes
            - created: ISO timestamp of creation
            - status: Always "encrypted"
            - is_active: True if this is the current target file
        
        Example:
            >>> files = manager.get_evidence_list()
            >>> for f in files:
            ...     print(f"{f['filename']}: {f['size_mb']} MB")
        """
        evidence = []
        
        # Find all .enc files, sorted by modification time (newest first)
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
    
    def get_buffer_status(self) -> Dict[str, Any]:
        """
        Get current buffer status for monitoring.
        
        Returns:
            Dict with keys:
            - buffer_frames: Number of frames in main buffer
            - pre_roll_frames: Number of frames in pre-roll buffer
            - buffer_duration: Duration of buffered content in seconds
            - current_target: Current target filename (or None)
        
        Example:
            >>> status = manager.get_buffer_status()
            >>> print(f"Buffer: {status['buffer_frames']} frames")
        """
        buffer_duration = 0
        if self.buffer_start is not None and self.buffer:
            buffer_duration = self.buffer[-1]["timestamp"] - self.buffer_start
        
        return {
            "buffer_frames": len(self.buffer),
            "pre_roll_frames": len(self.pre_roll),
            "buffer_duration": round(buffer_duration, 2),
            "current_target": self.current_target
        }


# ==============================================================================
# MODULE TEST
# ==============================================================================

if __name__ == "__main__":
    """
    Simple test to verify EvidenceManager functionality.
    """
    import sys
    
    print("=" * 60)
    print("EvidenceManager Test")
    print("=" * 60)
    
    # Create test manager
    manager = EvidenceManager(
        output_dir="/tmp/test_evidence",
        key_path="/tmp/test_evidence/test.key",
        max_duration=3,  # Short duration for testing
        prefix="test",
        detection_only=True,
        jpeg_quality=75
    )
    
    print("\nSimulating camera feed with intermittent detections...")
    
    for i in range(200):
        # Create test frame
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(frame, f"Frame {i}", (500, 400),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Simulate detections on some frames
        detections = []
        if 50 <= i <= 100 or 150 <= i <= 180:
            detections = [{"class": "face", "x1": 100, "y1": 100, "x2": 200, "y2": 200}]
        
        # Add frame
        start = time.time()
        manager.add_frame(frame, detections)
        elapsed = (time.time() - start) * 1000
        
        # Print status at intervals
        if i % 50 == 0:
            status = manager.get_buffer_status()
            print(f"  Frame {i}: buffer={status['buffer_frames']}, "
                  f"preroll={status['pre_roll_frames']}, time={elapsed:.1f}ms")
        
        time.sleep(1/30)  # Simulate 30fps
    
    print("\nClosing manager...")
    manager.close()
    
    print("\nEvidence files:")
    for f in manager.get_evidence_list():
        print(f"  {f['filename']}: {f['size_mb']} MB")
    
    print("\n✓ Test complete!")
