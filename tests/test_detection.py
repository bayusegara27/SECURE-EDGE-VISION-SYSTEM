"""
Unit Tests for Detection Module
Tests YOLO detection and blur functionality
"""

import os
import sys
import pytest
import numpy as np
import cv2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFaceDetector:
    """Tests for FaceDetector"""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        from modules.detection import FaceDetector
        return FaceDetector(device="cpu", blur_intensity=51)
    
    def test_detector_creation(self, detector):
        """Test detector initialization"""
        assert detector.blur_intensity == 51
        assert detector.confidence_threshold == 0.5
    
    def test_blur_application(self, detector):
        """Test that blur is applied correctly"""
        from modules.detection import Detection
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:200] = 255  # White square
        
        # Create fake detection
        detections = [Detection(
            x1=100, y1=100, x2=200, y2=200,
            confidence=0.9, timestamp=0
        )]
        
        # Apply blur
        blurred = detector._apply_blur(frame, detections)
        
        # Check that the region is blurred (not all same value anymore)
        original_region = frame[100:200, 100:200]
        blurred_region = blurred[100:200, 100:200]
        
        # Original is uniform white, blurred should be different at edges
        assert not np.array_equal(original_region, blurred_region)
    
    def test_empty_frame(self, detector):
        """Test detection on empty frame"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        blurred, detections = detector.detect_faces(frame)
        
        assert blurred.shape == frame.shape
        assert isinstance(detections, list)
    
    def test_blur_intensity_odd(self):
        """Test that blur intensity is always odd"""
        from modules.detection import FaceDetector
        
        detector_even = FaceDetector(blur_intensity=50)
        assert detector_even.blur_intensity == 51
        
        detector_odd = FaceDetector(blur_intensity=51)
        assert detector_odd.blur_intensity == 51


class TestBlurQuality:
    """Tests for blur quality"""
    
    def test_gaussian_blur_properties(self):
        """Test that Gaussian blur reduces high frequencies"""
        import cv2
        
        # Create image with sharp edges
        img = np.zeros((100, 100), dtype=np.uint8)
        img[40:60, 40:60] = 255
        
        # Apply blur
        blurred = cv2.GaussianBlur(img, (51, 51), 0)
        
        # Calculate variance (should be lower for blurred)
        original_var = np.var(img)
        blurred_var = np.var(blurred)
        
        # Blurred should be smoother (lower variance of differences)
        assert blurred_var < original_var
    
    def test_blur_irreversibility(self):
        """Test that blur cannot be perfectly reversed"""
        # This test documents that blur destroys information
        
        # Original detailed pattern
        original = np.zeros((100, 100), dtype=np.uint8)
        for i in range(100):
            for j in range(100):
                original[i, j] = (i * j) % 256
        
        # Apply heavy blur
        blurred = cv2.GaussianBlur(original, (51, 51), 0)
        
        # Try to "unblur" with sharpening
        kernel = np.array([[-1, -1, -1],
                          [-1, 9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(blurred, -1, kernel)
        
        # Should NOT be able to recover original
        mse = np.mean((original.astype(float) - sharpened.astype(float)) ** 2)
        assert mse > 100  # Significant difference remains


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
