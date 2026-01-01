import cv2
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def generate_thumbnails():
    config = Config()
    public_path = Path(config.public_path)
    
    if not public_path.exists():
        print(f"Directory not found: {public_path}")
        return

    print(f"Scanning {public_path} for missing thumbnails...")
    
    count = 0
    videos = list(public_path.glob("*.mp4"))
    
    for vid_path in videos:
        thumb_path = vid_path.with_suffix('.jpg')
        
        if not thumb_path.exists():
            print(f"Generating thumbnail for: {vid_path.name}")
            try:
                cap = cv2.VideoCapture(str(vid_path))
                ret, frame = cap.read()
                if ret:
                    # Resize to 320x180 (16:9)
                    frame = cv2.resize(frame, (320, 180))
                    cv2.imwrite(str(thumb_path), frame)
                    count += 1
                cap.release()
            except Exception as e:
                print(f"Error processing {vid_path.name}: {e}")
    
    print(f"Done! Generated {count} new thumbnails.")

if __name__ == "__main__":
    generate_thumbnails()
