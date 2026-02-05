"""
================================================================================
Video Recorder Module
================================================================================
Handles public MP4 recording with automatic file rotation and non-blocking I/O.

This module provides the VideoRecorder class that records video frames to MP4
files with automatic file rotation based on duration. Key features:

- NON-BLOCKING FILE ROTATION: Uses background thread for file finalization
- DOUBLE BUFFERING: Maintains two writers for seamless transitions  
- CODEC AUTO-DETECTION: Tries multiple codecs for maximum compatibility
- DETECTION METADATA: Saves JSON metadata alongside video files

Architecture:
    +------------------+       +-------------------+
    |   Camera Thread  | ----> |   VideoRecorder   |
    +------------------+       +-------------------+
                                      |
                        +-------------+-------------+
                        |                           |
                   [Active Writer]           [Background Thread]
                   Writes frames            Finalizes old files

Usage:
    recorder = VideoRecorder(
        output_dir="recordings/public",
        prefix="public_cam0",
        fps=30,
        max_duration=300  # 5 minutes
    )
    
    while streaming:
        recorder.write(frame, detections)
    
    recorder.close()

Thread Safety:
    - write() is designed to be called from a single camera thread
    - File finalization happens in background threads
    - No locks needed for frame writing (single producer)

Author: SECURE EDGE VISION SYSTEM
License: MIT
================================================================================
"""

import os
import time
import logging
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import cv2
import numpy as np

# Suppress OpenH264 warnings (system falls back to avc1 automatically)
os.environ.setdefault('OPENCV_FFMPEG_CAPTURE_OPTIONS', 'rtsp_transport;tcp')
os.environ.setdefault('OPENCV_VIDEOIO_PRIORITY_FFMPEG', '0')

# Disable OpenCV error messages for codec issues
# This suppresses "Failed to load OpenH264" and similar warnings
# since we're using avc1 codec which works perfectly
import sys
if hasattr(cv2, 'setLogLevel'):
    cv2.setLogLevel(0)  # 0 = Silent, 1 = Fatal, 2 = Error, 3 = Warning, 4 = Info

# Configure module logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Context manager to suppress stderr output at OS level (OpenH264 warnings)
class SuppressStderr:
    """
    Temporarily redirects stderr to null at OS file descriptor level.
    This suppresses C/C++ library warnings that bypass Python's stderr.
    """
    def __enter__(self):
        # Save original stderr file descriptor
        self._original_stderr_fd = sys.stderr.fileno()
        self._saved_stderr_fd = os.dup(self._original_stderr_fd)
        
        # Open null device
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        
        # Redirect stderr to null
        os.dup2(devnull_fd, self._original_stderr_fd)
        os.close(devnull_fd)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original stderr
        os.dup2(self._saved_stderr_fd, self._original_stderr_fd)
        os.close(self._saved_stderr_fd)


class VideoRecorder:
    """
    Records video to MP4 files with automatic rotation and non-blocking I/O.
    
    This class handles video recording for the public (blurred) video feed.
    It implements several optimizations to prevent streaming lag:
    
    1. NON-BLOCKING ROTATION: When a file needs to rotate, the old writer
       is handed off to a background thread for finalization while a new
       writer is created immediately.
       
    2. ASYNC FILE FINALIZATION: writer.release() and metadata saving happen
       in background threads, not blocking the main recording loop.
       
    3. FRAME QUEUE (Optional): Can buffer frames during transitions.
    
    Attributes:
        output_dir (Path): Directory where video files are saved
        prefix (str): Filename prefix (e.g., "public_cam0")
        fps (int): Target frames per second
        max_duration (int): Maximum recording duration in seconds before rotation
        resolution (tuple): Target video resolution (width, height)
        
        writer (cv2.VideoWriter): Current active video writer
        current_file (str): Path to currently recording file
        frame_count (int): Number of frames written to current file
        start_time (float): Unix timestamp when current recording started
        
    Example:
        >>> recorder = VideoRecorder("recordings/public", prefix="cam0", fps=30)
        >>> recorder.write(frame)  # Write frame to video
        >>> recorder.write(frame, detections=[{"class": "face"}])  # With detection
        >>> recorder.close()  # Finalize and close
    """
    
    # ==========================================================================
    # CLASS CONSTANTS
    # ==========================================================================
    
    # Timeout for queue operations (seconds)
    QUEUE_TIMEOUT_SECONDS = 0.5
    
    # Timeout for waiting on finalization thread during close (seconds)
    FINALIZE_TIMEOUT_SECONDS = 10.0
    
    # ==========================================================================
    # INITIALIZATION
    # ==========================================================================
    
    def __init__(
        self,
        output_dir: str,
        prefix: str = "recording",
        fps: int = 30,
        max_duration: int = 300,  # 5 minutes default
        resolution: tuple = (1280, 720)
    ):
        """
        Initialize the VideoRecorder.
        
        Args:
            output_dir: Directory path where video files will be saved.
                        Will be created if it doesn't exist.
            prefix: Filename prefix for output files. Final filename format:
                    {prefix}_{YYYYMMDD_HHMMSS}.mp4
            fps: Target frames per second for recording. Should match
                 the camera's capture FPS for proper playback speed.
            max_duration: Maximum duration in seconds before rotating to
                          a new file. Default 300 = 5 minutes.
            resolution: Target video resolution as (width, height).
                        Frames will be resized if they don't match.
        
        Example:
            >>> recorder = VideoRecorder(
            ...     output_dir="recordings/public",
            ...     prefix="public_cam0", 
            ...     fps=30,
            ...     max_duration=300,
            ...     resolution=(1280, 720)
            ... )
        """
        # --------------------------------------------------
        # Output Directory Setup
        # --------------------------------------------------
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # --------------------------------------------------
        # Recording Parameters
        # --------------------------------------------------
        self.prefix = prefix
        self.fps = fps
        self.max_duration = max_duration
        self.resolution = resolution
        
        # --------------------------------------------------
        # Writer State
        # --------------------------------------------------
        self.writer: Optional[cv2.VideoWriter] = None  # Current active writer
        self.current_file: Optional[str] = None        # Current file path
        self.frame_count = 0                           # Frames in current file
        self.start_time: Optional[float] = None        # Recording start timestamp
        self._force_rotate = False                     # Flag to force rotation
        
        # --------------------------------------------------
        # Detection Metadata
        # --------------------------------------------------
        self.detection_events: List[Dict[str, Any]] = []  # Detection events list
        
        # --------------------------------------------------
        # Background Thread for Non-Blocking Finalization
        # --------------------------------------------------
        self._finalize_queue = queue.Queue()  # Queue for files to finalize
        self._finalize_thread = None          # Background worker thread
        self._stop_finalize = False           # Signal to stop worker
        
        # Start background finalization thread
        self._start_finalize_worker()
    
    # ==========================================================================
    # BACKGROUND WORKER THREAD
    # ==========================================================================
    
    def _start_finalize_worker(self) -> None:
        """
        Start background thread for non-blocking file finalization.
        
        This thread handles:
        1. Releasing old VideoWriter objects (can take 100-500ms)
        2. Saving detection metadata to JSON files
        3. Logging completion messages
        
        The thread runs continuously, waiting for items in the finalize queue.
        When write() rotates to a new file, it pushes the old writer to this
        queue instead of blocking to release it.
        """
        self._stop_finalize = False
        self._finalize_thread = threading.Thread(
            target=self._finalize_worker_loop,
            daemon=True,  # Thread will exit when main program exits
            name=f"Finalize-{self.prefix}"
        )
        self._finalize_thread.start()
        logger.debug(f"[{self.prefix}] Finalize worker thread started")
    
    def _finalize_worker_loop(self) -> None:
        """
        Worker loop that processes finalization queue.
        
        This runs in a background thread and waits for (writer, filepath, 
        frame_count, detection_events) tuples to finalize.
        
        Processing each item:
        1. writer.release() - Flush buffers and close file
        2. Save detection metadata to .json file
        3. Log completion
        
        The loop exits when _stop_finalize is True and queue is empty.
        """
        while not self._stop_finalize or not self._finalize_queue.empty():
            try:
                # Wait for item with timeout to allow checking stop flag
                item = self._finalize_queue.get(timeout=self.QUEUE_TIMEOUT_SECONDS)
                
                # Unpack finalization data
                writer, filepath, frame_count, events = item
                
                # --------------------------------------------------
                # 1. Release Writer (potentially slow I/O operation)
                # --------------------------------------------------
                if writer is not None:
                    try:
                        writer.release()
                        logger.info(f"[BG] Finished: {Path(filepath).name} ({frame_count} frames)")
                    except Exception as e:
                        logger.error(f"[BG] Error releasing writer: {e}")
                
                # --------------------------------------------------
                # 2. Save Detection Metadata
                # --------------------------------------------------
                if filepath and events:
                    self._save_metadata_sync(filepath, frame_count, events)
                
                # Mark task as done
                self._finalize_queue.task_done()
                
            except queue.Empty:
                # No items to process, continue loop
                continue
            except Exception as e:
                logger.error(f"[BG] Finalize worker error: {e}")
    
    def _save_metadata_sync(
        self, 
        filepath: str, 
        frame_count: int, 
        events: List[Dict]
    ) -> None:
        """
        Save detection metadata to JSON file (synchronous, runs in background).
        
        Creates a .json file alongside the video file containing:
        - Video filename
        - FPS setting
        - Total frame count
        - List of detection events with frame indices
        
        Args:
            filepath: Path to the video file
            frame_count: Total number of frames in the video
            events: List of detection events [{f: frame_idx, c: [classes]}]
        """
        import json
        
        if not filepath or not events:
            return
        
        meta_file = Path(filepath).with_suffix('.json')
        try:
            metadata = {
                "filename": Path(filepath).name,
                "fps": self.fps,
                "total_frames": frame_count,
                "detections": events
            }
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.debug(f"[BG] Saved metadata: {meta_file.name}")
        except Exception as e:
            logger.error(f"[BG] Failed to save metadata: {e}")
    
    # ==========================================================================
    # VIDEO WRITER MANAGEMENT
    # ==========================================================================
    
    def _create_writer(self, frame_shape: tuple) -> None:
        """
        Create new VideoWriter with automatic codec detection.
        
        Tries multiple codecs in order of preference:
        1. avc1 (H.264) - Best for web playback
        2. X264 (H.264 fallback)
        3. mp4v (MPEG-4) - Common but less web-compatible
        4. MJPG - Universal fallback (AVI container)
        5. XVID - Nuclear fallback
        
        The method performs a pre-flight check by writing a blank frame
        to verify the codec actually works (Windows can report success
        for codecs that fail later).
        
        Args:
            frame_shape: Shape of frames that will be written (h, w, channels)
        
        Side Effects:
            - Sets self.writer to new VideoWriter
            - Sets self.current_file to new file path
            - Resets self.frame_count to 0
            - Resets self.start_time to current time
            - Clears self.detection_events
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.prefix}_{timestamp}.mp4"
        filepath = self.output_dir / filename
        
        h, w = frame_shape[:2]
        
        # --------------------------------------------------
        # Try Codecs in Order of Preference
        # --------------------------------------------------
        # Priority:
        # 1. avc1 - H.264, best for web/dashboard replay
        # 2. X264 - H.264 fallback
        # 3. mp4v - MPEG-4, common but often not web-playable
        # 4. MJPG - Universal fallback, uses AVI container
        codecs = ['avc1', 'X264', 'mp4v', 'MJPG']
        
        for codec in codecs:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            ext = ".mp4" if codec != 'MJPG' else ".avi"
            out_file = str(filepath.with_suffix(ext))
            
            # Create writer (suppress OpenH264 warnings from stderr)
            with SuppressStderr():
                self.writer = cv2.VideoWriter(out_file, fourcc, self.fps, (w, h))
            
            # --------------------------------------------------
            # Pre-flight Check
            # --------------------------------------------------
            # On Windows, isOpened() can return True even if codec fails later.
            # Write a blank frame to verify it actually works.
            if self.writer.isOpened():
                blank = np.zeros(frame_shape, dtype=np.uint8)
                self.writer.write(blank)
                
                # If write succeeded and still open, use this codec
                if self.writer.isOpened():
                    self.current_file = out_file
                    logger.info(f"[{self.prefix}] Recording: {Path(out_file).name} (codec: {codec})")
                    break
            
            # Codec failed, clean up and try next
            self.writer.release()
            self.writer = None
        
        # --------------------------------------------------
        # Nuclear Fallback: XVID or RAW
        # --------------------------------------------------
        if self.writer is None or not self.writer.isOpened():
            self.current_file = str(filepath.with_suffix(".avi"))
            with SuppressStderr():
                self.writer = cv2.VideoWriter(
                    self.current_file, 
                    cv2.VideoWriter_fourcc(*'XVID'), 
                    self.fps, 
                    (w, h)
                )
            if self.writer is None or not self.writer.isOpened():
                # Absolute last resort: uncompressed
                with SuppressStderr():
                    self.writer = cv2.VideoWriter(self.current_file, 0, self.fps, (w, h))
                logger.warning(f"[{self.prefix}] Using uncompressed fallback!")
        
        # --------------------------------------------------
        # Reset State for New Recording
        # --------------------------------------------------
        self.frame_count = 0
        self.start_time = time.time()
        self.detection_events = []
    
    def _should_rotate(self) -> bool:
        """
        Check if file rotation is needed.
        
        Rotation happens when:
        1. Force rotation flag is set (via rotate() method)
        2. No recording has started yet (start_time is None)
        3. Recording duration exceeds max_duration
        
        Returns:
            True if rotation is needed, False otherwise
        """
        # Check force rotation flag
        if self._force_rotate:
            self._force_rotate = False
            return True
        
        # Check if recording not started
        if self.start_time is None:
            return True
        
        # Check duration
        return (time.time() - self.start_time) >= self.max_duration
    
    def rotate(self) -> None:
        """
        Force rotation to new file on next write() call.
        
        This is useful when you want to split recordings at specific
        events (e.g., detection started, camera reconnected) rather
        than waiting for max_duration.
        
        Example:
            >>> recorder.rotate()  # Force new file on next write
        """
        self._force_rotate = True
    
    # ==========================================================================
    # MAIN RECORDING METHOD
    # ==========================================================================
    
    def write(self, frame: np.ndarray, detections: Optional[List[Dict]] = None) -> None:
        """
        Write frame to video file (NON-BLOCKING during rotation).
        
        This is the main method called for each frame. It handles:
        1. Checking if rotation is needed
        2. NON-BLOCKING handoff of old writer to background thread
        3. Creating new writer if needed
        4. Writing the frame
        5. Recording detection events
        
        The rotation process is optimized to minimize blocking:
        - Old writer is pushed to background queue (not released inline)
        - New writer is created immediately
        - Background thread handles slow finalization
        
        Args:
            frame: Video frame as numpy array (BGR format, shape HxWx3)
            detections: Optional list of detection dicts with 'class' key.
                        Used to record events in metadata JSON.
        
        Example:
            >>> recorder.write(frame)
            >>> recorder.write(frame, detections=[{"class": "face", "x1": 100}])
        """
        # --------------------------------------------------
        # Check Rotation Needed
        # --------------------------------------------------
        if self.writer is None or self._should_rotate():
            if self.writer is not None:
                # --------------------------------------------------
                # NON-BLOCKING ROTATION
                # --------------------------------------------------
                # Instead of blocking to release(), push to background queue
                old_writer = self.writer
                old_file = self.current_file
                old_count = self.frame_count
                old_events = self.detection_events.copy()
                
                # Queue for background finalization
                self._finalize_queue.put((old_writer, old_file, old_count, old_events))
                
                # Clear references (background thread now owns the writer)
                self.writer = None
            
            # Create new writer immediately
            self._create_writer(frame.shape)
        
        # --------------------------------------------------
        # Resize Frame if Needed
        # --------------------------------------------------
        if frame.shape[:2] != (self.resolution[1], self.resolution[0]):
            frame = cv2.resize(frame, self.resolution)
        
        # --------------------------------------------------
        # Write Frame
        # --------------------------------------------------
        self.writer.write(frame)
        
        # --------------------------------------------------
        # Record Detection Events
        # --------------------------------------------------
        if detections:
            # Store frame index and unique classes found
            classes = list(set([d.get("class", "unknown") for d in detections]))
            self.detection_events.append({
                "f": self.frame_count,  # Frame index
                "c": classes            # Classes detected
            })
        
        self.frame_count += 1
    
    # ==========================================================================
    # SHUTDOWN AND CLEANUP
    # ==========================================================================
    
    def close(self) -> None:
        """
        Close video writer and finalize recording.
        
        This method:
        1. Queues current writer for finalization
        2. Waits for all background finalization to complete
        3. Stops the background worker thread
        
        Should be called when stopping recording to ensure all data is saved.
        
        Example:
            >>> recorder.close()
        """
        # Queue current writer for finalization
        if self.writer is not None:
            self._finalize_queue.put((
                self.writer, 
                self.current_file, 
                self.frame_count, 
                self.detection_events.copy()
            ))
            self.writer = None
        
        # Stop background worker
        self._stop_finalize = True
        
        # Wait for all finalization to complete (with timeout)
        if self._finalize_thread is not None and self._finalize_thread.is_alive():
            self._finalize_thread.join(timeout=self.FINALIZE_TIMEOUT_SECONDS)
            if self._finalize_thread.is_alive():
                logger.warning(f"[{self.prefix}] Finalize thread still running after timeout")
        
        logger.info(f"[{self.prefix}] Recorder closed")
    
    def stop(self) -> None:
        """
        Alias for close() - for consistency with other modules.
        
        Example:
            >>> recorder.stop()  # Same as recorder.close()
        """
        self.close()
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def get_recording_list(self) -> List[Dict[str, Any]]:
        """
        Get list of recording files in output directory.
        
        Scans the output directory for video files matching this recorder's
        prefix and returns metadata about each file.
        
        Returns:
            List of dicts with keys:
            - filename: File name (e.g., "public_cam0_20240115_120000.mp4")
            - path: Full file path
            - size_mb: File size in megabytes
            - created: ISO timestamp of creation
            - is_active: True if this is the currently recording file
        
        Example:
            >>> recordings = recorder.get_recording_list()
            >>> for r in recordings:
            ...     print(f"{r['filename']}: {r['size_mb']} MB")
        """
        recordings = []
        
        # Support both .mp4 and .avi (for fallback codecs)
        files = []
        for ext in ['*.mp4', '*.avi']:
            files.extend(list(self.output_dir.glob(f"{self.prefix}_{ext}")))
        
        # Sort by modification time, newest first
        for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
            stat = f.stat()
            is_active = (str(f) == self.current_file)
            
            recordings.append({
                "filename": f.name,
                "path": str(f),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_active": is_active
            })
        
        return recordings


# ==============================================================================
# MODULE TEST
# ==============================================================================

if __name__ == "__main__":
    """
    Simple test to verify VideoRecorder functionality.
    
    Creates a test recording with rotation to verify non-blocking behavior.
    """
    import sys
    
    print("=" * 60)
    print("VideoRecorder Test")
    print("=" * 60)
    
    # Create test recorder
    recorder = VideoRecorder(
        output_dir="/tmp/test_recordings",
        prefix="test",
        fps=30,
        max_duration=3  # Short duration for testing
    )
    
    # Generate test frames
    print("\nWriting 200 frames (~6.7 seconds at 30fps)...")
    print("This should trigger rotation around frame 90")
    
    for i in range(200):
        # Create test frame with frame number
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(frame, f"Frame {i}", (500, 400), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Write frame
        start = time.time()
        recorder.write(frame, detections=[{"class": "test"}] if i % 30 == 0 else None)
        elapsed = (time.time() - start) * 1000
        
        # Print timing info for rotation frames
        if elapsed > 10:
            print(f"  Frame {i}: {elapsed:.1f}ms (rotation occurred)")
        
        time.sleep(1/30)  # Simulate 30fps
    
    print("\nClosing recorder...")
    recorder.close()
    
    print("\nRecordings:")
    for r in recorder.get_recording_list():
        print(f"  {r['filename']}: {r['size_mb']} MB")
    
    print("\n✓ Test complete!")
