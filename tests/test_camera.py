"""
Unit Tests for Camera Module
Tests camera capture and shared memory functionality
"""

import os
import sys
import time
import pytest
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSharedFrameBuffer:
    """Tests for SharedFrameBuffer"""
    
    def test_buffer_creation(self):
        """Test creating shared memory buffer"""
        from modules.camera import SharedFrameBuffer
        
        shape = (480, 640, 3)
        buffer = SharedFrameBuffer("test_buffer_1", shape, create=True)
        
        assert buffer.shape == shape
        assert buffer.buffer.shape == shape
        
        buffer.close()
        buffer.unlink()
    
    def test_write_and_read(self):
        """Test writing and reading from buffer"""
        from modules.camera import SharedFrameBuffer
        
        shape = (480, 640, 3)
        
        # Create buffer
        writer = SharedFrameBuffer("test_buffer_2", shape, create=True)
        
        # Write test frame
        test_frame = np.random.randint(0, 255, shape, dtype=np.uint8)
        writer.write(test_frame)
        
        # Read back
        read_frame = writer.read()
        
        assert np.array_equal(test_frame, read_frame)
        
        writer.close()
        writer.unlink()
    
    def test_buffer_attach(self):
        """Test attaching to existing buffer"""
        from modules.camera import SharedFrameBuffer
        
        shape = (480, 640, 3)
        
        # Create
        creator = SharedFrameBuffer("test_buffer_3", shape, create=True)
        
        # Write
        test_frame = np.ones(shape, dtype=np.uint8) * 128
        creator.write(test_frame)
        
        # Attach
        reader = SharedFrameBuffer("test_buffer_3", shape, create=False)
        read_frame = reader.read()
        
        assert np.array_equal(test_frame, read_frame)
        
        reader.close()
        creator.close()
        creator.unlink()


class TestCameraIngester:
    """Tests for CameraIngester"""
    
    def test_buffer_info(self):
        """Test getting buffer info"""
        from modules.camera import CameraIngester
        
        cam = CameraIngester(
            source=0,
            output_width=1280,
            output_height=720,
            buffer_name="test_cam_buffer"
        )
        
        info = cam.get_buffer_info()
        
        assert info["name"] == "test_cam_buffer"
        assert info["shape"] == (720, 1280, 3)
        assert info["dtype"] == "uint8"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
