"""
System Initialization Script
First-time setup and configuration
"""

import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


def print_banner():
    """Print setup banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   SECURE EDGE VISION SYSTEM                                  ║
║   First-Time Setup                                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


def create_directories() -> bool:
    """Create required directories"""
    print("\n[1/5] Creating directories...")
    
    dirs = [
        "models",
        "keys",
        "keys/backups",
        "recordings/public",
        "recordings/evidence",
        "static"
    ]
    
    for d in dirs:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {d}")
        else:
            print(f"  → Exists: {d}")
    
    return True


def generate_encryption_key() -> bool:
    """Generate master encryption key"""
    print("\n[2/5] Setting up encryption key...")
    
    key_path = Path(os.getenv("ENCRYPTION_KEY_PATH", "keys/master.key"))
    
    if key_path.exists():
        print(f"  → Key already exists: {key_path}")
        
        # Offer backup
        print(f"  → Creating backup...")
        from tools.key_manager import backup_key
        backup_key()
        return True
    
    # Generate new key
    from modules.security import SecureVault
    
    key_path.parent.mkdir(parents=True, exist_ok=True)
    vault = SecureVault(key_path=str(key_path))
    
    print(f"  ✓ Generated encryption key: {key_path}")
    
    # Create initial backup
    from tools.key_manager import backup_key
    backup_key()
    
    return True


def download_face_model() -> bool:
    """Download face detection model"""
    print("\n[3/5] Setting up AI model...")
    
    model_path = Path("models/model.pt")
    
    if model_path.exists():
        print(f"  → Model already exists: {model_path}")
        return True
    
    print("  → Downloading YOLOv8-Face model...")
    
    try:
        from huggingface_hub import hf_hub_download
        
        path = hf_hub_download(
            repo_id="arnabdhar/YOLOv8-Face-Detection",
            filename="model.pt",
            local_dir="models"
        )
        
        print(f"  ✓ Downloaded: {path}")
        return True
        
    except Exception as e:
        print(f"  ⚠ Could not download face model: {e}")
        print("  → Will use default YOLO model (person detection)")
        return True


def download_openh264() -> bool:
    """Download OpenH264 codec for browser-compatible video recording"""
    print("\n[4/5] Setting up video codec (OpenH264)...")
    
    import urllib.request
    import bz2
    
    # Find OpenCV installation path
    try:
        import cv2
        cv2_path = Path(cv2.__file__).parent
    except ImportError:
        print("  ⚠ OpenCV not installed, skipping codec setup")
        return True
    
    dll_path = cv2_path / "openh264-1.8.0-win64.dll"
    
    if dll_path.exists():
        print(f"  → Codec already exists: {dll_path.name}")
        return True
    
    # Also check project directory
    local_dll = Path("openh264-1.8.0-win64.dll")
    if local_dll.exists():
        print(f"  → Found local codec, copying to OpenCV...")
        import shutil
        shutil.copy(local_dll, dll_path)
        print(f"  ✓ Codec installed: {dll_path}")
        return True
    
    print("  → Downloading OpenH264 codec from Cisco...")
    
    url = "https://github.com/cisco/openh264/releases/download/v1.8.0/openh264-1.8.0-win64.dll.bz2"
    bz2_path = cv2_path / "openh264-1.8.0-win64.dll.bz2"
    
    try:
        # Download
        urllib.request.urlretrieve(url, bz2_path)
        print(f"  ✓ Downloaded: {bz2_path.name}")
        
        # Extract
        with bz2.open(bz2_path, 'rb') as f_in:
            with open(dll_path, 'wb') as f_out:
                f_out.write(f_in.read())
        
        # Cleanup
        bz2_path.unlink()
        
        print(f"  ✓ Codec installed: {dll_path.name}")
        return True
        
    except Exception as e:
        print(f"  ⚠ Could not download codec: {e}")
        print("  → Video recordings may not play in browser")
        print("  → Manual download: https://github.com/cisco/openh264/releases")
        return True


def verify_setup() -> bool:
    """Verify everything is set up correctly"""
    print("\n[5/5] Verifying setup...")
    
    checks = []
    
    # Check key
    key_path = Path(os.getenv("ENCRYPTION_KEY_PATH", "keys/master.key"))
    if key_path.exists():
        print("  ✓ Encryption key: OK")
        checks.append(True)
    else:
        print("  ✗ Encryption key: MISSING")
        checks.append(False)
    
    # Check model
    if Path("models/model.pt").exists():
        print("  ✓ Face model: OK")
        checks.append(True)
    else:
        print("  ⚠ Face model: Not found (will use fallback)")
        checks.append(True)
    
    # Check directories
    dirs_ok = all([
        Path("recordings/public").exists(),
        Path("recordings/evidence").exists()
    ])
    if dirs_ok:
        print("  ✓ Directories: OK")
        checks.append(True)
    else:
        print("  ✗ Directories: MISSING")
        checks.append(False)
    
    # Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("  ⚠ GPU: Not available (will use CPU)")
        checks.append(True)
    except:
        print("  ⚠ GPU: Cannot check")
        checks.append(True)
    
    return all(checks)


def main():
    """Run first-time setup"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Secure Edge Vision System - First-time Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script performs first-time setup:
  1. Creates required directories
  2. Generates encryption key
  3. Downloads AI face detection model
  4. Downloads H264 video codec
  5. Verifies system configuration

Examples:
  python setup.py              # Run full setup
  python setup.py --skip-model # Skip model download
        """
    )
    
    parser.add_argument("--skip-model", action="store_true",
                       help="Skip AI model download")
    parser.add_argument("--skip-key", action="store_true",
                       help="Skip key generation (if already exists)")
    parser.add_argument("--skip-codec", action="store_true",
                       help="Skip H264 codec download")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Force regenerate key (WARNING: will lose access to old evidence!)")
    
    args = parser.parse_args()
    
    print_banner()
    
    try:
        create_directories()
        
        if not args.skip_key:
            generate_encryption_key()
        else:
            print("\n[2/5] Skipping encryption key (--skip-key)")
        
        if not args.skip_model:
            download_face_model()
        else:
            print("\n[3/5] Skipping model download (--skip-model)")
        
        if not args.skip_codec:
            download_openh264()
        else:
            print("\n[4/5] Skipping codec download (--skip-codec)")
        
        success = verify_setup()
        
        print("\n" + "═" * 60)
        
        if success:
            print("""
  ✓ Setup complete!
  
  Next steps:
    1. Test components: python demo.py
    2. Run system: python main.py
    3. Open browser: http://localhost:8000
  
  IMPORTANT:
    - Backup keys/master.key to a safe location
    - Without this key, encrypted evidence cannot be recovered
            """)
        else:
            print("""
  ⚠ Setup completed with warnings.
  
  Please check the issues above before continuing.
            """)
        
        print("═" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

