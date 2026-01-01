"""
Tests for Storage Module
Tests video recording and encrypted evidence storage
"""

import os
import sys
import time
import tempfile
import pytest
import numpy as np
import cv2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestVideoRecorder:
    """Tests for PublicRecorder"""
    
    def test_recorder_creation(self):
        """Test creating video recorder"""
        from modules.storage import PublicRecorder, RecordingConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RecordingConfig(
                output_dir=tmpdir,
                max_duration_seconds=10,
                fps=30,
                resolution=(640, 480)
            )
            
            recorder = PublicRecorder(config)
            assert recorder.output_dir.exists()
    
    def test_write_frames(self):
        """Test writing frames to video"""
        from modules.storage import PublicRecorder, RecordingConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RecordingConfig(
                output_dir=tmpdir,
                max_duration_seconds=60,
                fps=30,
                resolution=(640, 480)
            )
            
            recorder = PublicRecorder(config)
            
            # Write test frames
            for i in range(30):
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                recorder.write_frame(frame)
            
            recorder.close()
            
            # Check file exists
            files = list(Path(tmpdir).glob("*.mp4"))
            assert len(files) == 1
            assert files[0].stat().st_size > 0
    
    def test_file_rotation(self):
        """Test automatic file rotation"""
        from modules.storage import PublicRecorder, RecordingConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RecordingConfig(
                output_dir=tmpdir,
                max_duration_seconds=1,  # Very short for testing
                fps=30,
                resolution=(320, 240)
            )
            
            recorder = PublicRecorder(config)
            
            # Write frames over time
            start = time.time()
            while time.time() - start < 2.5:
                frame = np.zeros((240, 320, 3), dtype=np.uint8)
                recorder.write_frame(frame)
                time.sleep(0.033)
            
            recorder.close()
            
            # Should have multiple files due to rotation
            files = list(Path(tmpdir).glob("*.mp4"))
            assert len(files) >= 2


class TestEvidenceRecorder:
    """Tests for EvidenceRecorder"""
    
    def test_evidence_buffer(self):
        """Test evidence buffering"""
        from modules.storage import EvidenceRecorder, RecordingConfig
        from modules.security import SecureVault
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RecordingConfig(
                output_dir=tmpdir,
                max_duration_seconds=300
            )
            vault = SecureVault()
            
            recorder = EvidenceRecorder(config, vault)
            
            # Add frames
            for i in range(10):
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                recorder.add_frame(frame, [{"x1": 0, "y1": 0, "x2": 100, "y2": 100}], time.time())
            
            assert len(recorder._buffer) == 10
            
            # Flush
            recorder.flush()
            
            assert len(recorder._buffer) == 0
            
            # Check file
            files = list(Path(tmpdir).glob("*.enc"))
            assert len(files) == 1


class TestGetRecordingList:
    """Tests for get_recording_list function"""
    
    def test_empty_directory(self):
        """Test listing empty directory"""
        from modules.storage import get_recording_list
        
        with tempfile.TemporaryDirectory() as tmpdir:
            recordings = get_recording_list(tmpdir)
            assert recordings == []
    
    def test_list_recordings(self):
        """Test listing recordings"""
        from modules.storage import get_recording_list
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            for i in range(3):
                filepath = Path(tmpdir) / f"test_{i}.mp4"
                filepath.write_bytes(b"test" * 1000)
            
            recordings = get_recording_list(tmpdir)
            
            assert len(recordings) == 3
            assert all(r["filename"].endswith(".mp4") for r in recordings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
