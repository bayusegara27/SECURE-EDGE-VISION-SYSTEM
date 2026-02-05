"""
Unit Tests for Preset Configuration
Tests the preset switching functionality for detection configuration.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPresetLoading:
    """Tests for preset loading and configuration"""
    
    def test_load_presets_from_yaml(self):
        """Test that presets can be loaded from YAML file"""
        from config import load_presets
        
        presets = load_presets()
        
        # Should have exactly 2 presets
        assert 1 in presets
        assert 2 in presets
        assert len(presets) == 2
    
    def test_preset_1_default_values(self):
        """Test that Preset 1 has correct default values"""
        from config import get_preset
        
        preset = get_preset(1)
        
        assert preset["detector"] == "yolov8n-face"
        assert preset["tracker"] == "botsort"
        assert preset["confidence"] == 0.35
        assert preset["iou"] == 0.45
    
    def test_preset_2_values(self):
        """Test that Preset 2 has correct values"""
        from config import get_preset
        
        preset = get_preset(2)
        
        assert preset["detector"] == "yolov11n-face"
        assert preset["tracker"] == "bytetrack"
        assert preset["confidence"] == 0.30
        assert preset["iou"] == 0.50
    
    def test_invalid_preset_falls_back_to_1(self):
        """Test that invalid preset ID falls back to preset 1"""
        from config import get_preset
        
        # Invalid preset should return preset 1 values
        preset = get_preset(99)
        
        assert preset["detector"] == "yolov8n-face"
        assert preset["tracker"] == "botsort"
    
    def test_default_presets_fallback(self):
        """Test that default presets are returned when YAML not found"""
        from config import _get_default_presets
        
        presets = _get_default_presets()
        
        assert 1 in presets
        assert 2 in presets
        assert presets[1]["detector"] == "yolov8n-face"
        assert presets[2]["detector"] == "yolov11n-face"


class TestConfigWithPresets:
    """Tests for Config class with preset support"""
    
    def test_config_default_preset(self):
        """Test that Config uses preset 1 by default"""
        # Clear any preset env var
        env_backup = os.environ.get("DETECTION_PRESET")
        if "DETECTION_PRESET" in os.environ:
            del os.environ["DETECTION_PRESET"]
        
        try:
            from config import Config
            config = Config()
            
            assert config.preset_id == 1
            assert config.detector == "yolov8n-face"
            assert config.tracker == "botsort"
        finally:
            if env_backup:
                os.environ["DETECTION_PRESET"] = env_backup
    
    def test_config_preset_from_env(self):
        """Test that Config reads preset from DETECTION_PRESET env var"""
        env_backup = os.environ.get("DETECTION_PRESET")
        os.environ["DETECTION_PRESET"] = "2"
        
        try:
            from config import Config
            config = Config()
            
            assert config.preset_id == 2
            assert config.detector == "yolov11n-face"
            assert config.tracker == "bytetrack"
        finally:
            if env_backup:
                os.environ["DETECTION_PRESET"] = env_backup
            elif "DETECTION_PRESET" in os.environ:
                del os.environ["DETECTION_PRESET"]
    
    def test_config_preset_from_argument(self):
        """Test that Config accepts preset_id as constructor argument"""
        from config import Config
        
        config = Config(preset_id=2)
        
        assert config.preset_id == 2
        assert config.detector == "yolov11n-face"
        assert config.tracker == "bytetrack"
    
    def test_config_argument_overrides_env(self):
        """Test that constructor argument takes priority over env var"""
        env_backup = os.environ.get("DETECTION_PRESET")
        os.environ["DETECTION_PRESET"] = "2"
        
        try:
            from config import Config
            config = Config(preset_id=1)  # Should use 1 despite env var
            
            assert config.preset_id == 1
            assert config.detector == "yolov8n-face"
        finally:
            if env_backup:
                os.environ["DETECTION_PRESET"] = env_backup
            elif "DETECTION_PRESET" in os.environ:
                del os.environ["DETECTION_PRESET"]
    
    def test_config_invalid_preset_falls_back(self):
        """Test that invalid preset falls back to 1"""
        from config import Config
        
        config = Config(preset_id=99)
        
        assert config.preset_id == 1
    
    def test_config_preset_info(self):
        """Test get_preset_info method"""
        from config import Config
        
        config = Config(preset_id=1)
        info = config.get_preset_info()
        
        assert info["preset_id"] == 1
        assert info["detector"] == "yolov8n-face"
        assert info["tracker"] == "botsort"
        assert "confidence" in info
        assert "iou" in info
    
    def test_config_confidence_from_preset(self):
        """Test that confidence is loaded from preset"""
        from config import Config
        
        # Clear env var override
        env_backup = os.environ.get("DETECTION_CONFIDENCE")
        if "DETECTION_CONFIDENCE" in os.environ:
            del os.environ["DETECTION_CONFIDENCE"]
        
        try:
            config1 = Config(preset_id=1)
            config2 = Config(preset_id=2)
            
            assert config1.confidence == 0.35
            assert config2.confidence == 0.30
        finally:
            if env_backup:
                os.environ["DETECTION_CONFIDENCE"] = env_backup
    
    def test_config_iou_from_preset(self):
        """Test that IoU is loaded from preset"""
        from config import Config
        
        # Clear env var override
        env_backup = os.environ.get("DETECTION_IOU")
        if "DETECTION_IOU" in os.environ:
            del os.environ["DETECTION_IOU"]
        
        try:
            config1 = Config(preset_id=1)
            config2 = Config(preset_id=2)
            
            assert config1.iou == 0.45
            assert config2.iou == 0.50
        finally:
            if env_backup:
                os.environ["DETECTION_IOU"] = env_backup


class TestPresetIntegration:
    """Integration tests for preset system"""
    
    def test_processor_receives_preset_values(self):
        """Test that FrameProcessor receives values from preset"""
        from config import Config
        from modules.processor import FrameProcessor
        
        config = Config(preset_id=2)
        
        processor = FrameProcessor(
            model_path=config.model_path,
            device="cpu",  # Use CPU for test
            confidence=config.confidence,
            iou=config.iou,
            blur_intensity=config.blur_intensity,
            tracker=config.tracker
        )
        
        assert processor.confidence == 0.30
        assert processor.iou == 0.50
        assert processor.tracker == "bytetrack"
    
    def test_processor_info_includes_preset_params(self):
        """Test that processor info includes preset parameters"""
        from modules.processor import FrameProcessor
        
        processor = FrameProcessor(
            device="cpu",
            confidence=0.35,
            iou=0.45,
            tracker="botsort"
        )
        
        info = processor.get_info()
        
        assert "confidence" in info
        assert "iou" in info
        assert "tracker" in info
        assert info["confidence"] == 0.35
        assert info["iou"] == 0.45
        assert info["tracker"] == "botsort"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
