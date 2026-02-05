"""
================================================================================
Configuration Module
================================================================================
Central configuration management for the Secure Edge Vision System.

This module provides:
1. Config class - Loads and validates all system settings from environment
2. validate_config() - Checks configuration validity
3. show_system_info() - Displays system information (Python, CUDA, etc.)
4. generate_env_template() - Creates default .env template

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

Usage:
    from config import Config
    config = Config()
    print(f"Using device: {config.device}")
    print(f"Camera sources: {config.camera_sources}")

CLI Usage:
    python config.py --validate    # Validate configuration
    python config.py --info        # Show system information
    python config.py --create-env  # Create default .env file
    python config.py --template    # Print .env template

Author: SECURE EDGE VISION SYSTEM
License: MIT
================================================================================
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    """
    System configuration loaded from environment variables.
    
    This class centralizes all configuration settings for the system.
    Settings are loaded from environment variables with sensible defaults.
    
    Attributes:
        camera_sources (List[int|str]): List of camera sources
        device (str): Compute device - "cuda" or "cpu"
        model_path (str): Path to YOLOv8 model file
        confidence (float): Detection confidence threshold (0.0-1.0)
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
    
    Example:
        >>> config = Config()
        >>> print(f"Device: {config.device}")
        >>> print(f"Cameras: {config.camera_sources}")
        >>> print(f"Target FPS: {config.target_fps}")
    """
    
    def __init__(self):
        # Support multiple camera sources separated by comma
        sources_str = os.getenv("CAMERA_SOURCES", "0")
        self.camera_sources = []
        for src in sources_str.split(","):
            src = src.strip()
            if src.isdigit():
                self.camera_sources.append(int(src))
            else:
                self.camera_sources.append(src)
        
        self.device = os.getenv("DEVICE", "cuda")
        self.model_path = os.getenv("MODEL_PATH", "models/model.pt")  # Face detection model
        self.confidence = float(os.getenv("DETECTION_CONFIDENCE", "0.5"))
        self.blur_intensity = int(os.getenv("BLUR_INTENSITY", "51"))
        
        self.server_host = os.getenv("SERVER_HOST", "0.0.0.0")
        self.server_port = int(os.getenv("SERVER_PORT", "8000"))
        
        self.public_path = os.getenv("PUBLIC_RECORDINGS_PATH", "recordings/public")
        self.evidence_path = os.getenv("EVIDENCE_RECORDINGS_PATH", "recordings/evidence")
        self.key_path = os.getenv("ENCRYPTION_KEY_PATH", "keys/master.key")
        
        self.target_fps = int(os.getenv("TARGET_FPS", "30"))
        self.max_duration = int(os.getenv("RECORDING_DURATION_SECONDS", "300"))
        
        # Storage Optimization
        self.evidence_detection_only = os.getenv("EVIDENCE_DETECTION_ONLY", "True").lower() == "true"
        self.evidence_quality = int(os.getenv("EVIDENCE_JPEG_QUALITY", "75"))
        
        # Retention Policy
        self.max_storage_gb = int(os.getenv("MAX_STORAGE_GB", "50"))
        
        # Overlay Settings
        self.show_timestamp = os.getenv("SHOW_TIMESTAMP", "True").lower() == "true"
        self.show_debug_overlay = os.getenv("SHOW_DEBUG_OVERLAY", "False").lower() == "true"


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
