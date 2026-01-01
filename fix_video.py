import os
import urllib.request
import bz2
import sys
from pathlib import Path

def setup_h264():
    """
    Downloads and installs Cisco OpenH264 DLL for Windows.
    Handles 'Incorrect library version' by providing options.
    """
    print("\n" + "="*50)
    print("  OPENH264 RECOVERY TOOL")
    print("="*50)

    if os.name != 'nt':
        print("This script is only for Windows systems.")
        return

    # Versions to try
    versions = [
        {"v": "1.8.0", "url": "http://ciscobinary.openh264.org/openh264-1.8.0-win64.dll.bz2"},
        {"v": "1.7.0", "url": "http://ciscobinary.openh264.org/openh264-1.7.0-win64.dll.bz2"}
    ]

    print("Detecting old installations...")
    for f in Path('.').glob("openh264*.dll"):
        print(f"Removing old version: {f.name}")
        try:
            f.unlink()
        except:
            print(f"!! Could not remove {f.name}. Make sure Python is CLOSED first.")
            return

    # Try 1.8.0 first
    ver = versions[0]
    print(f"\nAttempting to install version {ver['v']} (Default)...")
    
    bz2_file = f"openh264-{ver['v']}-win64.dll.bz2"
    dll_name = f"openh264-{ver['v']}-win64.dll"

    try:
        print(f"Downloading from Cisco...")
        urllib.request.urlretrieve(ver['url'], bz2_file)
        
        print("Extracting...")
        with bz2.BZ2File(bz2_file) as f:
            with open(dll_name, 'wb') as dest:
                dest.write(f.read())
        
        os.remove(bz2_file)
        
        # Also create a copy without the version number, some FFMPEG builds look for this
        import shutil
        shutil.copy(dll_name, "openh264.dll")
        
        print(f"✓ Installed {dll_name} and openh264.dll")
        print("\n" + "="*50)
        print("  SUCCESS!")
        print("="*50)
        print("1. Please CLOSE ALL terminal windows.")
        print("2. Open a NEW terminal.")
        print("3. Run 'python main.py' again.")
        print("\nIf you still see 'Incorrect library version', run this script")
        print("again but try to manually download version 1.7.0.")
        print("="*50 + "\n")

    except Exception as e:
        print(f"✕ ERROR: {e}")

if __name__ == "__main__":
    setup_h264()
