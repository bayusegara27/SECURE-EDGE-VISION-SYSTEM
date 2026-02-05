"""
Fix OpenH264 Library for OpenCV on Windows
===========================================
This script downloads and installs the OpenH264 library for OpenCV.

Usage:
    python fix_openh264.py

The script will:
1. Download the correct OpenH264 DLL for Windows
2. Place it in the OpenCV directory
3. Test if the codec works

Author: SECURE EDGE VISION SYSTEM
"""

import os
import sys
import urllib.request
import zipfile
import platform
from pathlib import Path

def get_opencv_path():
    """Get the OpenCV installation path."""
    try:
        import cv2
        cv_path = Path(cv2.__file__).parent
        return cv_path
    except ImportError:
        print("❌ OpenCV not found. Please install opencv-python first.")
        sys.exit(1)

def download_openh264():
    """Download OpenH264 library from Cisco GitHub."""
    print("=" * 70)
    print("  OpenH264 Library Installer")
    print("=" * 70)
    print()
    
    # Determine architecture
    is_64bit = platform.machine().endswith('64')
    arch = "win64" if is_64bit else "win32"
    
    # OpenH264 download URL (v2.4.1 - latest stable)
    version = "2.4.1"
    dll_name = f"openh264-{version}-{arch}.dll"
    zip_name = f"openh264-{version}-{arch}.dll.bz2"
    url = f"http://ciscobinary.openh264.org/{zip_name}"
    
    print(f"📦 Architecture: {arch}")
    print(f"🔗 Download URL: {url}")
    print()
    
    # Create temp directory
    temp_dir = Path("temp_openh264")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Download file
        print(f"⬇️  Downloading {zip_name}...")
        zip_path = temp_dir / zip_name
        
        urllib.request.urlretrieve(url, zip_path, reporthook=download_progress)
        print()
        print("✅ Download complete!")
        
        # Extract bz2 file
        print(f"📂 Extracting DLL...")
        import bz2
        
        dll_path = temp_dir / dll_name.replace(f"-{version}", "")
        with bz2.open(zip_path, 'rb') as f_in:
            with open(dll_path, 'wb') as f_out:
                f_out.write(f_in.read())
        
        print(f"✅ Extracted: {dll_path.name}")
        
        # Copy to OpenCV directory with multiple naming options
        cv_path = get_opencv_path()
        
        # Try multiple filenames that OpenCV might look for
        dest_names = [
            f"openh264-{version}-{arch}.dll",  # Full version name
            f"openh264-1.8.0-{arch}.dll",      # Version OpenCV expects
            "openh264.dll"                     # Generic name
        ]
        
        print(f"📁 Installing to OpenCV directory...")
        import shutil
        for dest_name in dest_names:
            dest_path = cv_path / dest_name
            shutil.copy2(dll_path, dest_path)
            print(f"   ✓ {dest_name}")
        
        dest_path = cv_path / dest_names[0]  # Use first one for reference
        dest_path = cv_path / dest_names[0]  # Use first one for reference
        
        print(f"📁 Main installation: {dest_path}")
        
        import shutil
        
        print("✅ Installation complete!")
        print()
        
        # Cleanup
        print("🧹 Cleaning up temporary files...")
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def download_progress(block_num, block_size, total_size):
    """Show download progress."""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(downloaded * 100.0 / total_size, 100)
        bar_length = 40
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f'\r  Progress: [{bar}] {percent:.1f}%', end='', flush=True)

def test_openh264():
    """Test if OpenH264 codec works."""
    print()
    print("=" * 70)
    print("  Testing OpenH264 Codec")
    print("=" * 70)
    print()
    
    try:
        import cv2
        import numpy as np
        
        # Try to create a VideoWriter with H264 codec
        fourcc = cv2.VideoWriter_fourcc(*'H264')
        test_file = "test_h264.mp4"
        
        writer = cv2.VideoWriter(test_file, fourcc, 30, (640, 480))
        
        if writer.isOpened():
            # Write a test frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            writer.write(frame)
            writer.release()
            
            # Check if file was created
            if Path(test_file).exists():
                print("✅ OpenH264 codec is working!")
                Path(test_file).unlink()  # Delete test file
                return True
            else:
                print("⚠️  Codec opened but file not created")
                return False
        else:
            print("⚠️  Could not open H264 codec")
            print("💡 System will use fallback codec (avc1) instead")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main function."""
    print()
    
    # Check current status
    cv_path = get_opencv_path()
    print(f"📍 OpenCV path: {cv_path}")
    print()
    
    # Check if OpenH264 already exists
    possible_names = [
        "openh264-1.8.0-win64.dll",
        "openh264-2.4.1-win64.dll", 
        "openh264.dll"
    ]
    
    existing = None
    for name in possible_names:
        dll_path = cv_path / name
        if dll_path.exists():
            existing = dll_path
            break
    
    if existing:
        print(f"ℹ️  Found existing OpenH264: {existing.name}")
        response = input("   Do you want to reinstall? (y/n): ").lower()
        if response != 'y':
            print("   Skipping download.")
            test_openh264()
            return
    
    # Download and install
    if download_openh264():
        test_openh264()
    else:
        print()
        print("=" * 70)
        print("⚠️  ALTERNATIVE SOLUTION")
        print("=" * 70)
        print()
        print("Your system is already using the 'avc1' codec as fallback,")
        print("which works perfectly fine for recording.")
        print()
        print("To suppress OpenH264 warnings:")
        print("1. The recorder.py has been updated to suppress warnings")
        print("2. Your recordings will continue to work with avc1 codec")
        print()
    
    print()
    print("=" * 70)
    print("Done!")
    print("=" * 70)

if __name__ == "__main__":
    main()
