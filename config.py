"""
================================================================================
Configuration Module
================================================================================
Central configuration management for the Secure Edge Vision System.

This module provides:
1. Config class - Loads and validates all system settings from environment
2. load_preset() - Loads detection presets from presets.yaml
3. validate_config() - Checks configuration validity
4. show_system_info() - Displays system information (Python, CUDA, etc.)
5. generate_env_template() - Creates default .env template

Environment Variables:
    CAMERA_SOURCES         - Camera sources (comma-separated: "0", "0,1", "rtsp://...")
    DEVICE                 - Compute device ("cuda" or "cpu")
    MODEL_PATH             - Path to YOLOv8 face detection model
    DETECTION_CONFIDENCE   - Detection confidence threshold (0.0-1.0)
    BLUR_INTENSITY         - Gaussian blur kernel size (odd number)
    SERVER_HOST            - FastAPI server host (default: 0.0.0.0)
    SERVER_PORT            - FastAPI server port (default: 8000)
    PUBLIC_RECORDINGS_PATH - Directory for blurred public videos
    EVIDENCE_RECORDINGS_PATH - Directory for encrypted evidence
    ENCRYPTION_KEY_PATH    - Path to AES-256 encryption key
    TARGET_FPS             - Target frames per second
    RECORDING_DURATION_SECONDS - Max seconds before file rotation
    EVIDENCE_DETECTION_ONLY - Only save evidence when detections present
    EVIDENCE_JPEG_QUALITY  - JPEG quality for evidence frames (0-100)
    MAX_STORAGE_GB         - Maximum storage limit in gigabytes
    SHOW_TIMESTAMP         - Show timestamp overlay on stream
    SHOW_DEBUG_OVERLAY     - Show debug info overlay on stream
    DETECTION_PRESET       - Detection preset (1 or 2, default: 1)

Presets:
    Preset 1 (Default):
        - Detector: YOLOv8-Face (nano)
        - Tracker: BoT-SORT
        - conf=0.35, iou=0.45
    
    Preset 2 (Alternative):
        - Detector: YOLOv11-Face (nano)
        - Tracker: ByteTrack
        - conf=0.30, iou=0.50

Usage:
    from config import Config
    config = Config()
    print(f"Using device: {config.device}")
    print(f"Camera sources: {config.camera_sources}")
    print(f"Active preset: {config.preset_name}")

CLI Usage:
    python config.py --validate    # Validate configuration
    python config.py --info        # Show system information
    python config.py --create-env  # Create default .env file
    python config.py --template    # Print .env template
    
    # Preset selection:
    python main.py --preset 2
    DETECTION_PRESET=2 python main.py

Author: SECURE EDGE VISION SYSTEM
License: MIT
================================================================================
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


# ================================================================================
# Preset Management
# ================================================================================

def load_presets(preset_file: str = "presets.yaml") -> Dict[int, Dict[str, Any]]:
    """
    Load detection presets from YAML configuration file.
    
    Args:
        preset_file: Path to presets.yaml file (relative or absolute)
        
    Returns:
        Dictionary mapping preset IDs to their configurations
        
    Example:
        >>> presets = load_presets()
        >>> print(presets[1]["name"])
        "Default (YOLOv8-Face + BoT-SORT)"
    """
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not installed. Using default preset configuration.")
        return _get_default_presets()
    
    # Try multiple paths to find presets.yaml
    base_dir = Path(__file__).parent
    possible_paths = [
        Path(preset_file),  # As provided
        base_dir / preset_file,  # Relative to config.py
        base_dir / "presets.yaml",  # Default name in same directory
    ]
    
    for path in possible_paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and "presets" in data:
                        logger.info(f"Loaded presets from: {path}")
                        return data["presets"]
            except Exception as e:
                logger.warning(f"Failed to parse {path}: {e}")
    
    logger.warning(f"Presets file not found, using defaults")
    return _get_default_presets()


def _get_default_presets() -> Dict[int, Dict[str, Any]]:
    """
    Return hardcoded default presets as fallback.
    
    These match the presets.yaml configuration exactly.
    """
    return {
        1: {
            "name": "Default (YOLOv8-Face + BoT-SORT)",
            "description": "Balanced preset for general surveillance use",
            "detector": "yolov8n-face",
            "tracker": "botsort",
            "confidence": 0.35,
            "iou": 0.45
        },
        2: {
            "name": "Alternative (YOLOv11-Face + ByteTrack)",
            "description": "Experimental preset with newer detector and faster tracker",
            "detector": "yolov11n-face",
            "tracker": "bytetrack",
            "confidence": 0.30,
            "iou": 0.50
        }
    }


def get_preset(preset_id: int, presets: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Get a specific preset by ID with fallback to default.
    
    Args:
        preset_id: Preset number (1 or 2)
        presets: Optional presets dict. If None, loads from file.
        
    Returns:
        Preset configuration dictionary
        
    Note:
        Invalid preset IDs will log a warning and fall back to preset 1.
    """
    if presets is None:
        presets = load_presets()
    
    if preset_id not in presets:
        logger.warning(f"Invalid preset {preset_id}, falling back to preset 1")
        preset_id = 1
    
    return presets[preset_id]


class Config:
    """
    System configuration loaded from environment variables.
    
    This class centralizes all configuration settings for the system.
    Settings are loaded from environment variables with sensible defaults.
    Supports detection presets via --preset CLI argument or DETECTION_PRESET env var.
    
    Attributes:
        camera_sources (List[int|str]): List of camera sources
        device (str): Compute device - "cuda" or "cpu"
        model_path (str): Path to YOLOv8 model file
        confidence (float): Detection confidence threshold (0.0-1.0)
        iou (float): IoU threshold for NMS/tracking (0.0-1.0)
        blur_intensity (int): Gaussian blur kernel size (must be odd)
        server_host (str): FastAPI server host address
        server_port (int): FastAPI server port
        public_path (str): Directory for public (blurred) recordings
        evidence_path (str): Directory for encrypted evidence
        key_path (str): Path to encryption key file
        target_fps (int): Target frames per second for recording
        max_duration (int): Maximum recording duration before rotation
        evidence_detection_only (bool): Only save evidence with detections
        evidence_quality (int): JPEG quality for evidence (0-100)
        max_storage_gb (int): Maximum storage limit
        show_timestamp (bool): Show timestamp on video stream
        show_debug_overlay (bool): Show debug info on video stream
        preset_id (int): Active preset ID (1 or 2)
        preset_name (str): Human-readable name of active preset
        detector (str): Detector model name from preset
        tracker (str): Tracker algorithm name from preset
    
    Example:
        >>> config = Config()
        >>> print(f"Device: {config.device}")
        >>> print(f"Cameras: {config.camera_sources}")
        >>> print(f"Preset: {config.preset_name}")
        >>> print(f"Detector: {config.detector}")
    """
    
    def __init__(self, preset_id: Optional[int] = None):
        """
        Initialize configuration with optional preset override.
        
        Args:
            preset_id: Override preset ID. If None, reads from DETECTION_PRESET env var
                       or defaults to 1.
        """
        # ====================================================================
        # Preset Loading (Priority: CLI arg > env var > default)
        # ====================================================================
        if preset_id is None:
            preset_id = int(os.getenv("DETECTION_PRESET", "1"))
        
        # Validate preset ID
        if preset_id not in (1, 2):
            logger.warning(f"Invalid preset {preset_id}, using preset 1")
            preset_id = 1
        
        self.preset_id = preset_id
        
        # Load preset configuration
        presets = load_presets()
        preset = get_preset(preset_id, presets)
        
        # Store preset attributes
        self.preset_name = preset.get("name", f"Preset {preset_id}")
        self.detector = preset.get("detector", "yolov8n-face")
        self.tracker = preset.get("tracker", "botsort")
        
        # Log preset loading
        logger.info("=" * 60)
        logger.info(f"LOADING DETECTION PRESET {preset_id}")
        logger.info("=" * 60)
        logger.info(f"  Name: {self.preset_name}")
        logger.info(f"  Detector: {self.detector}")
        logger.info(f"  Tracker: {self.tracker}")
        logger.info(f"  Confidence: {preset.get('confidence', 0.35)}")
        logger.info(f"  IoU: {preset.get('iou', 0.45)}")
        logger.info("=" * 60)
        
        # ====================================================================
        # Camera Sources
        # ====================================================================
        sources_str = os.getenv("CAMERA_SOURCES", "0")
        self.camera_sources = []
        for src in sources_str.split(","):
            src = src.strip()
            if src.isdigit():
                self.camera_sources.append(int(src))
            else:
                self.camera_sources.append(src)
        
        # ====================================================================
        # Detection Settings (from preset, with env var override)
        # ====================================================================
        self.device = os.getenv("DEVICE", "cuda")
        
        # Map detector name to model file path
        # If detector is specified in preset, use corresponding model
        detector_model_map = {
            "yolov8n-face": "models/model.pt",          # YOLOv8-Face (custom trained - WIDER Face)
            "yolov11n-face": "models/yolov11n-face.pt", # YOLOv11-Face (YapaLab - WIDER Face)
            "yolov8n": "yolov8n.pt",                    # YOLOv8 nano COCO (auto-download)
            "yolov11n": "yolo11n.pt"                    # YOLOv11 nano COCO (auto-download)
        }
        
        # Determine model path based on detector from preset
        default_model = detector_model_map.get(self.detector, "models/model.pt")
        self.model_path = os.getenv("MODEL_PATH", default_model)
        
        # Log which model will be used
        logger.info(f"  Model Path: {self.model_path}")
        
        # Use preset values as defaults, allow env var override
        self.confidence = float(os.getenv("DETECTION_CONFIDENCE", str(preset.get("confidence", 0.35))))
        self.iou = float(os.getenv("DETECTION_IOU", str(preset.get("iou", 0.45))))
        self.blur_intensity = int(os.getenv("BLUR_INTENSITY", "51"))
        
        # ====================================================================
        # Server Settings
        # ====================================================================
        self.server_host = os.getenv("SERVER_HOST", "0.0.0.0")
        self.server_port = int(os.getenv("SERVER_PORT", "8000"))
        
        # ====================================================================
        # Storage Paths
        # ====================================================================
        self.public_path = os.getenv("PUBLIC_RECORDINGS_PATH", "recordings/public")
        self.evidence_path = os.getenv("EVIDENCE_RECORDINGS_PATH", "recordings/evidence")
        self.key_path = os.getenv("ENCRYPTION_KEY_PATH", "keys/master.key")
        
        # ====================================================================
        # Recording Settings
        # ====================================================================
        self.target_fps = int(os.getenv("TARGET_FPS", "30"))
        self.max_duration = int(os.getenv("RECORDING_DURATION_SECONDS", "300"))
        
        # ====================================================================
        # Storage Optimization
        # ====================================================================
        self.evidence_detection_only = os.getenv("EVIDENCE_DETECTION_ONLY", "True").lower() == "true"
        self.evidence_quality = int(os.getenv("EVIDENCE_JPEG_QUALITY", "75"))
        
        # ====================================================================
        # Retention Policy
        # ====================================================================
        self.max_storage_gb = int(os.getenv("MAX_STORAGE_GB", "50"))
        
        # ====================================================================
        # Overlay Settings
        # ====================================================================
        self.show_timestamp = os.getenv("SHOW_TIMESTAMP", "True").lower() == "true"
        self.show_debug_overlay = os.getenv("SHOW_DEBUG_OVERLAY", "False").lower() == "true"
    
    def get_preset_info(self) -> Dict[str, Any]:
        """
        Get information about the currently loaded preset.
        
        Returns:
            Dictionary with preset details
        """
        return {
            "preset_id": self.preset_id,
            "preset_name": self.preset_name,
            "detector": self.detector,
            "tracker": self.tracker,
            "confidence": self.confidence,
            "iou": self.iou
        }


def validate_config() -> Tuple[bool, List[str]]:
    """
    Validate system configuration
    Returns: (is_valid, list_of_issues)
    """
    # ... existing validation logic ...
    issues = []
    warnings = []
    
    # Check camera source
    camera = os.getenv("CAMERA_SOURCES", "0")
    if camera.startswith("rtsp://"):
        warnings.append(f"Using RTSP source: {camera[:50]}...")
    elif camera.isdigit():
        try:
            import cv2
            cap = cv2.VideoCapture(int(camera))
            if not cap.isOpened():
                issues.append(f"Cannot open camera {camera}")
            cap.release()
        except Exception as e:
            issues.append(f"Camera test failed: {e}")
    
    # Check directories
    for dir_var in ["PUBLIC_RECORDINGS_PATH", "EVIDENCE_RECORDINGS_PATH"]:
        path = Path(os.getenv(dir_var, f"recordings/{dir_var.split('_')[0].lower()}"))
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create {dir_var}: {e}")
    
    # Check key directory
    key_path = Path(os.getenv("ENCRYPTION_KEY_PATH", "keys/master.key"))
    key_dir = key_path.parent
    if not key_dir.exists():
        try:
            key_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create key directory: {e}")
    
    # Check CUDA
    device = os.getenv("DEVICE", "cuda")
    if device == "cuda":
        try:
            import torch
            if not torch.cuda.is_available():
                warnings.append("CUDA requested but not available, will use CPU")
        except ImportError:
            warnings.append("PyTorch not installed, cannot check CUDA")
    
    # Check blur intensity
    blur = int(os.getenv("BLUR_INTENSITY", "51"))
    if blur % 2 == 0:
        warnings.append(f"BLUR_INTENSITY should be odd, will use {blur + 1}")
    if blur < 11:
        warnings.append("BLUR_INTENSITY < 11 may not provide adequate privacy")
    
    # Check port
    port = int(os.getenv("SERVER_PORT", "8000"))
    if port < 1024:
        warnings.append(f"Port {port} may require admin privileges")
    
    # Print results
    print("\n" + "=" * 50)
    print("  CONFIGURATION VALIDATION")
    print("=" * 50)
    
    print(f"\nCamera: {os.getenv('CAMERA_SOURCES', '0')}")
    print(f"Device: {os.getenv('DEVICE', 'cuda')}")
    print(f"Port: {os.getenv('SERVER_PORT', '8000')}")
    print(f"Blur: {os.getenv('BLUR_INTENSITY', '51')}")
    print(f"FPS: {os.getenv('TARGET_FPS', '30')}")
    
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"   • {w}")
    
    if issues:
        print(f"\n❌ Issues ({len(issues)}):")
        for i in issues:
            print(f"   • {i}")
        return False, issues
    
    print("\n✓ Configuration valid!")
    return True, []


def generate_env_template():
    """Generate .env template with all options"""
    template = '''# Secure Edge Vision System Configuration
# Copy this file to .env and modify as needed

# ============ Camera Settings ============
# Use 0 for default webcam
# Use 1, 2, etc. for other cameras
# Use RTSP URL for IP cameras: rtsp://user:pass@192.168.1.100:554/stream
CAMERA_SOURCES=0

# ============ AI/Detection Settings ============
# Model path (will auto-download if not exists)
MODEL_PATH=models/yolov8n.pt

# Detection confidence threshold (0.0 - 1.0)
DETECTION_CONFIDENCE=0.5

# Device: cuda for GPU, cpu for CPU only
DEVICE=cuda

# Blur kernel size (must be odd number, higher = more blur)
BLUR_INTENSITY=51

# ============ Server Settings ============
# Host to bind (0.0.0.0 for all interfaces)
SERVER_HOST=0.0.0.0

# Port number
SERVER_PORT=8000

# ============ Recording Settings ============
# Maximum recording duration in seconds before rotating
RECORDING_DURATION_SECONDS=300

# Maximum file size in MB (optional)
MAX_RECORDING_SIZE_MB=100

# Target FPS for recording
TARGET_FPS=30

# ============ Storage Paths ============
# Where to save blurred public recordings
PUBLIC_RECORDINGS_PATH=recordings/public

# Where to save encrypted evidence
EVIDENCE_RECORDINGS_PATH=recordings/evidence

# ============ Security Settings ============
# Path to encryption key (will be auto-generated if not exists)
# WARNING: Backup this file! Without it, evidence cannot be decrypted
ENCRYPTION_KEY_PATH=keys/master.key
'''
    return template


def create_default_env():
    """Create default .env file if not exists"""
    env_path = Path(".env")
    
    if env_path.exists():
        print(".env already exists, skipping")
        return False
    
    env_path.write_text(generate_env_template())
    print("Created .env with default settings")
    return True


def show_system_info():
    """Display system information"""
    print("\n" + "=" * 50)
    print("  SYSTEM INFORMATION")
    print("=" * 50)
    
    # Python
    print(f"\nPython: {sys.version}")
    
    # OpenCV
    try:
        import cv2
        print(f"OpenCV: {cv2.__version__}")
    except ImportError:
        print("OpenCV: NOT INSTALLED")
    
    # PyTorch
    try:
        import torch
        print(f"PyTorch: {torch.__version__}")
        print(f"CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"CUDA Version: {torch.version.cuda}")
    except ImportError:
        print("PyTorch: NOT INSTALLED")
    
    # Ultralytics
    try:
        import ultralytics
        print(f"Ultralytics: {ultralytics.__version__}")
    except ImportError:
        print("Ultralytics: NOT INSTALLED")
    
    # FastAPI
    try:
        import fastapi
        print(f"FastAPI: {fastapi.__version__}")
    except ImportError:
        print("FastAPI: NOT INSTALLED")
    
    # Cryptography
    try:
        import cryptography
        print(f"Cryptography: {cryptography.__version__}")
    except ImportError:
        print("Cryptography: NOT INSTALLED")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration Utility")
    parser.add_argument("--validate", "-v", action="store_true", help="Validate configuration")
    parser.add_argument("--info", "-i", action="store_true", help="Show system information")
    parser.add_argument("--create-env", action="store_true", help="Create default .env file")
    parser.add_argument("--template", "-t", action="store_true", help="Print .env template")
    
    args = parser.parse_args()
    
    if args.template:
        print(generate_env_template())
        return 0
    
    if args.create_env:
        create_default_env()
        return 0
    
    if args.info:
        show_system_info()
        return 0
    
    if args.validate:
        valid, _ = validate_config()
        return 0 if valid else 1
    
    # Default: show all info
    show_system_info()
    validate_config()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
