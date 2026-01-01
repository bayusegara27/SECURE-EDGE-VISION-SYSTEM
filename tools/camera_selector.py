"""
Camera Selector Utility
Lists available cameras and allows user to select one
"""

import cv2
import logging
from typing import List, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def list_available_cameras(max_cameras: int = 10) -> List[dict]:
    """
    Detect available camera devices
    
    Args:
        max_cameras: Maximum number of cameras to check
        
    Returns:
        List of available camera info dicts
    """
    cameras = []
    
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            cameras.append({
                "index": i,
                "name": f"Camera {i}",
                "resolution": f"{width}x{height}",
                "fps": fps
            })
            cap.release()
    
    return cameras


def select_camera_interactive() -> Optional[int]:
    """
    Interactive camera selection
    
    Returns:
        Selected camera index or None if cancelled
    """
    print("\n" + "=" * 50)
    print("  CAMERA SELECTION")
    print("=" * 50)
    print("\nScanning for cameras...")
    
    cameras = list_available_cameras()
    
    if not cameras:
        print("No cameras found!")
        return None
    
    print(f"\nFound {len(cameras)} camera(s):\n")
    
    for cam in cameras:
        print(f"  [{cam['index']}] {cam['name']}")
        print(f"      Resolution: {cam['resolution']}")
        print(f"      FPS: {cam['fps']}")
        print()
    
    print("  [r] Enter RTSP URL")
    print("  [q] Quit\n")
    
    while True:
        choice = input("Select camera: ").strip().lower()
        
        if choice == 'q':
            return None
        
        if choice == 'r':
            url = input("Enter RTSP URL: ").strip()
            if url:
                return url
            continue
        
        try:
            index = int(choice)
            if any(c["index"] == index for c in cameras):
                return index
            print("Invalid selection")
        except ValueError:
            print("Invalid input")


def test_camera(source: int | str) -> Tuple[bool, Optional[str]]:
    """
    Test camera connection
    
    Args:
        source: Camera index or RTSP URL
        
    Returns:
        (success, error_message)
    """
    try:
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            return False, "Cannot open camera"
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return False, "Cannot read frame"
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def preview_camera(source: int | str, duration: int = 5) -> None:
    """
    Preview camera feed for a few seconds
    
    Args:
        source: Camera index or RTSP URL
        duration: Preview duration in seconds
    """
    import time
    
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    print(f"\nPreviewing camera (Press Q to stop)...")
    
    start = time.time()
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Add info text
        cv2.putText(
            frame,
            f"Camera {source} - Press Q to stop",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        cv2.imshow("Camera Preview", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        if time.time() - start > duration:
            break
    
    cap.release()
    cv2.destroyAllWindows()


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(
        description="📹 Camera Selection & Diagnostic Tool - Secure Edge CCTV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🔥 COMMON WORKFLOWS & EXAMPLES:

1. List Available Cameras (Interactive):
   python tools/camera_selector.py

2. Test a Specific Camera Index:
   python tools/camera_selector.py --test 0

3. Test an RTSP URL:
   python tools/camera_selector.py --test rtsp://admin:password@192.168.1.100/stream

4. Preview Camera for a Specific Duration (e.g., 30s):
   python tools/camera_selector.py --preview 0 --duration 30

💡 Use this tool to verify your hardware configuration before starting the main server.
        """
    )
    parser.add_argument("--list", action="store_true", help="List available cameras")
    parser.add_argument("--test", type=str, metavar="SOURCE", help="Test connection to camera index or RTSP URL")
    parser.add_argument("--preview", type=str, metavar="SOURCE", help="Preview camera feed")
    parser.add_argument("--duration", type=int, default=10, help="Preview duration in seconds (default: 10)")
    
    args = parser.parse_args()
    
    if args.test:
        source = int(args.test) if args.test.isdigit() else args.test
        success, error = test_camera(source)
        if success:
            print(f"✓ {source}: Connection Successful")
        else:
            print(f"✗ {source}: Connection Failed - {error}")
    elif args.preview:
        source = int(args.preview) if args.preview.isdigit() else args.preview
        preview_camera(source, duration=args.duration)
    else:
        # Default behavior: Interactive selection
        selected = select_camera_interactive()
        if selected is not None:
            print(f"\nSelected: {selected}")
            success, _ = test_camera(selected)
            if success:
                preview_camera(selected, duration=5)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
