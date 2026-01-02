"""
Storage Module
Handles public MP4 recording and encrypted evidence storage
Supports automatic file rotation based on duration/size
"""

import cv2
import numpy as np
import time
import logging
import os
import pickle
from pathlib import Path
from multiprocessing import Process, Event, Queue
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass

from modules.security import SecureVault, HybridVault, create_vault_from_env, create_hybrid_vault_from_env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RecordingConfig:
    """Recording configuration"""
    output_dir: str
    max_duration_seconds: int = 300  # 5 minutes
    max_size_mb: int = 100
    fps: int = 30
    resolution: tuple = (1280, 720)


class PublicRecorder:
    """
    Records blurred video to MP4 files
    Automatic file rotation based on duration
    """
    
    def __init__(self, config: RecordingConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._writer: Optional[cv2.VideoWriter] = None
        self._current_file: Optional[str] = None
        self._frame_count = 0
        self._start_time: Optional[float] = None
        self._current_timestamp: Optional[str] = None  # Shared timestamp for matching
    
    @property
    def current_file(self) -> Optional[str]:
        return self._current_file
    
    @property
    def current_timestamp(self) -> Optional[str]:
        """Current recording timestamp for matching with evidence files"""
        return self._current_timestamp
    
    def _create_writer(self) -> cv2.VideoWriter:
        """Create new video writer"""
        self._current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"public_{self._current_timestamp}.mp4"
        filepath = self.output_dir / filename
        
        # Use H.264 codec for better compression
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        writer = cv2.VideoWriter(
            str(filepath),
            fourcc,
            self.config.fps,
            self.config.resolution
        )
        
        if not writer.isOpened():
            raise RuntimeError(f"Failed to create video writer: {filepath}")
        
        self._current_file = str(filepath)
        self._frame_count = 0
        self._start_time = time.time()
        
        logger.info(f"Started recording: {filename}")
        return writer
    
    def _should_rotate(self) -> bool:
        """Check if file should be rotated"""
        if self._start_time is None:
            return True
        
        elapsed = time.time() - self._start_time
        return elapsed >= self.config.max_duration_seconds
    
    def write_frame(self, frame: np.ndarray):
        """Write frame to current recording"""
        if self._writer is None or self._should_rotate():
            if self._writer is not None:
                self._writer.release()
                logger.info(f"Finished recording: {self._current_file} ({self._frame_count} frames)")
            
            self._writer = self._create_writer()
        
        # Ensure correct resolution
        if frame.shape[:2] != (self.config.resolution[1], self.config.resolution[0]):
            frame = cv2.resize(frame, self.config.resolution)
        
        self._writer.write(frame)
        self._frame_count += 1
    
    def close(self):
        """Close current recording"""
        if self._writer is not None:
            self._writer.release()
            logger.info(f"Closed recording: {self._current_file} ({self._frame_count} frames)")
            self._writer = None


class EvidenceRecorder:
    """
    Records encrypted evidence (raw frames with detections)
    Uses Hybrid RSA+AES encryption:
    - RSA encrypts per-file session key (Public Key only needed)
    - AES-GCM encrypts video data with session key
    - Private Key only needed for DECRYPTION (can be offline/USB)
    """
    
    def __init__(self, config: RecordingConfig, vault, sync_timestamp_getter=None):
        """
        Args:
            config: Recording configuration
            vault: HybridVault (preferred) or SecureVault (legacy)
            sync_timestamp_getter: Optional callable to get synced timestamp from PublicRecorder
        """
        self.config = config
        self.vault = vault
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._buffer: List[dict] = []
        self._buffer_start_time: Optional[float] = None
        self._file_count = 0
        self._sync_timestamp: Optional[str] = None  # For matching with public files
        self._sync_timestamp_getter = sync_timestamp_getter
    
    def add_frame(self, frame: np.ndarray, detections: list, timestamp: float, sync_timestamp: str = None):
        """Add frame to buffer
        
        Args:
            frame: Video frame
            detections: List of detection boxes
            timestamp: Frame timestamp
            sync_timestamp: Optional synced timestamp from PublicRecorder for matching filenames
        """
        if self._buffer_start_time is None:
            self._buffer_start_time = timestamp
            # Capture sync timestamp at start of buffer
            if sync_timestamp:
                self._sync_timestamp = sync_timestamp
            elif self._sync_timestamp_getter:
                self._sync_timestamp = self._sync_timestamp_getter()
        
        # Compress frame to JPEG for storage efficiency
        _, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        self._buffer.append({
            "frame_jpg": encoded.tobytes(),
            "detections": [
                {
                    "x1": d.x1, "y1": d.y1,
                    "x2": d.x2, "y2": d.y2,
                    "confidence": d.confidence
                } if hasattr(d, 'x1') else d
                for d in detections
            ],
            "timestamp": timestamp
        })
        
        # Auto-flush if buffer duration exceeded
        elapsed = timestamp - self._buffer_start_time
        if elapsed >= self.config.max_duration_seconds:
            self.flush()
    
    def flush(self) -> Optional[str]:
        """Flush buffer to encrypted file"""
        if not self._buffer:
            return None
        
        # Serialize buffer
        data = pickle.dumps(self._buffer)
        
        # Generate filename - use synced timestamp if available for matching
        if self._sync_timestamp:
            filename = f"evidence_{self._sync_timestamp}_{self._file_count:04d}.enc"
        else:
            dt = datetime.fromtimestamp(self._buffer_start_time)
            filename = f"evidence_{dt.strftime('%Y%m%d_%H%M%S')}_{self._file_count:04d}.enc"
        
        filepath = self.output_dir / filename
        
        # Metadata for the file
        metadata = {
            "frame_count": len(self._buffer),
            "start_time": self._buffer_start_time,
            "end_time": self._buffer[-1]["timestamp"],
            "resolution": list(self.config.resolution),
            "total_detections": sum(len(f["detections"]) for f in self._buffer)
        }
        
        # Save encrypted
        self.vault.save_encrypted_file(data, str(filepath), metadata)
        
        # Clear buffer
        saved_count = len(self._buffer)
        self._buffer = []
        self._buffer_start_time = None
        self._sync_timestamp = None  # Reset sync timestamp
        self._file_count += 1
        
        logger.info(f"Saved encrypted evidence: {filename} ({saved_count} frames)")
        return str(filepath)
    
    def close(self):
        """Flush remaining buffer and close"""
        if self._buffer:
            self.flush()


class StorageManager:
    """
    Manages both public and evidence storage
    Runs recording loops in background processes
    """
    
    def __init__(
        self,
        public_config: RecordingConfig,
        evidence_config: RecordingConfig,
        vault: SecureVault
    ):
        self.public_config = public_config
        self.evidence_config = evidence_config
        self.vault = vault
        
        self._public_process: Optional[Process] = None
        self._evidence_process: Optional[Process] = None
        self._stop_event = Event()
    
    def _public_recording_loop(
        self,
        queue: Queue,
        stop_event: Event
    ):
        """Public recording process loop"""
        recorder = PublicRecorder(self.public_config)
        
        logger.info("Public recorder started")
        
        try:
            while not stop_event.is_set():
                try:
                    data = queue.get(timeout=1.0)
                    frame = data["frame"]
                    recorder.write_frame(frame)
                except Exception:
                    continue
        finally:
            recorder.close()
            logger.info("Public recorder stopped")
    
    def _evidence_recording_loop(
        self,
        queue: Queue,
        stop_event: Event,
        public_key_path: str
    ):
        """Evidence recording process loop (uses Hybrid encryption)"""
        # Create HybridVault with PUBLIC KEY ONLY for encryption
        # Private key is NOT needed - can be stored offline for security
        vault = HybridVault(public_key_path=public_key_path)
        recorder = EvidenceRecorder(self.evidence_config, vault)
        
        logger.info("Evidence recorder started")
        
        try:
            while not stop_event.is_set():
                try:
                    data = queue.get(timeout=1.0)
                    recorder.add_frame(
                        data["frame"],
                        data["detections"],
                        data["timestamp"]
                    )
                except Exception:
                    continue
        finally:
            recorder.close()
            logger.info("Evidence recorder stopped")
    
    def start(self, public_queue: Queue, evidence_queue: Queue, public_key_path: str):
        """Start recording processes
        
        Args:
            public_queue: Queue for public (blurred) frames
            evidence_queue: Queue for evidence (raw) frames
            public_key_path: Path to RSA public key for hybrid encryption
        """
        self._stop_event.clear()
        
        # Start public recorder
        self._public_process = Process(
            target=self._public_recording_loop,
            args=(public_queue, self._stop_event),
            daemon=True
        )
        self._public_process.start()
        
        # Start evidence recorder with PUBLIC KEY ONLY
        # Private key not needed for encryption - keeps system secure
        self._evidence_process = Process(
            target=self._evidence_recording_loop,
            args=(evidence_queue, self._stop_event, public_key_path),
            daemon=True
        )
        self._evidence_process.start()
        
        logger.info("Storage manager started")
    
    def stop(self):
        """Stop recording processes"""
        self._stop_event.set()
        
        for proc in [self._public_process, self._evidence_process]:
            if proc is not None:
                proc.join(timeout=5)
                if proc.is_alive():
                    proc.terminate()
        
        self._public_process = None
        self._evidence_process = None
        
        logger.info("Storage manager stopped")


def get_recording_list(directory: str) -> List[dict]:
    """Get list of recordings in directory"""
    path = Path(directory)
    if not path.exists():
        return []
    
    recordings = []
    for f in sorted(path.glob("*.mp4"), reverse=True):
        stat = f.stat()
        recordings.append({
            "filename": f.name,
            "path": str(f),
            "size_mb": stat.st_size / (1024 * 1024),
            "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    return recordings


def cleanup_storage(public_path: str, evidence_path: str, max_gb: int):
    """
    Enforce storage retention policy (FIFO)
    Deletes oldest files if total usage exceeds max_gb
    """
    try:
        max_bytes = max_gb * 1024 * 1024 * 1024
        all_files = []
        total_size = 0
        
        # Scan Public
        p_path = Path(public_path)
        if p_path.exists():
            for f in p_path.rglob("*.*"):
                if f.is_file():
                    stat = f.stat()
                    all_files.append((stat.st_mtime, f, stat.st_size))
                    total_size += stat.st_size
                    
        # Scan Evidence
        e_path = Path(evidence_path)
        if e_path.exists():
            for f in e_path.rglob("*.*"):
                if f.is_file():
                    stat = f.stat()
                    all_files.append((stat.st_mtime, f, stat.st_size))
                    total_size += stat.st_size
        
        if total_size <= max_bytes:
            return total_size
            
        # Exceeded! Sort by time (oldest first)
        all_files.sort(key=lambda x: x[0])
        
        target_size = max_bytes * 0.9 # Aim for 90% occupancy
        deleted_count = 0
        deleted_bytes = 0
        
        for mtime, f, size in all_files:
            if total_size <= target_size:
                break
            try:
                os.remove(f)
                total_size -= size
                deleted_count += 1
                deleted_bytes += size
            except Exception as e:
                logger.error(f"Failed to delete {f}: {e}")
                
        if deleted_count > 0:
            logger.warning(f"RETENTION: Deleted {deleted_count} oldest files ({deleted_bytes / (1024*1024):.1f} MB) to free space.")
            
        return total_size
    except Exception as e:
        logger.error(f"Retention error: {e}")
        return 0
    """
    Create storage components from environment variables
    
    Returns:
        (public_config, evidence_config, public_key_path)
        Note: Only returns public_key_path - private key not needed for encryption
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    public_config = RecordingConfig(
        output_dir=os.getenv("PUBLIC_RECORDINGS_PATH", "recordings/public"),
        max_duration_seconds=int(os.getenv("RECORDING_DURATION_SECONDS", "300")),
        fps=int(os.getenv("TARGET_FPS", "30"))
    )
    
    evidence_config = RecordingConfig(
        output_dir=os.getenv("EVIDENCE_RECORDINGS_PATH", "recordings/evidence"),
        max_duration_seconds=int(os.getenv("RECORDING_DURATION_SECONDS", "300")),
        fps=int(os.getenv("TARGET_FPS", "30"))
    )
    
    # For hybrid encryption, we only need the public key for encryption
    # Private key is only needed for decryption (can be stored offline!)
    public_key_path = os.getenv("RSA_PUBLIC_KEY_PATH", "keys/rsa_public.pem")
    
    return public_config, evidence_config, public_key_path


# Test code
if __name__ == "__main__":
    import tempfile
    
    # Test public recorder
    with tempfile.TemporaryDirectory() as tmpdir:
        config = RecordingConfig(
            output_dir=tmpdir,
            max_duration_seconds=5,
            fps=30,
            resolution=(640, 480)
        )
        
        recorder = PublicRecorder(config)
        
        # Write some test frames
        for i in range(90):  # 3 seconds at 30fps
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f"Frame {i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            recorder.write_frame(frame)
            time.sleep(0.01)
        
        recorder.close()
        
        # List recordings
        recordings = get_recording_list(tmpdir)
        print(f"Created {len(recordings)} recording(s):")
        for r in recordings:
            print(f"  - {r['filename']} ({r['size_mb']:.2f} MB)")
