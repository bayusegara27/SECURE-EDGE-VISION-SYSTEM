"""
Download YOLOv11-Face model from YapaLab for Preset 2
Source: https://github.com/YapaLab/yolo-face
"""
import urllib.request
import os
from pathlib import Path

print("=" * 70)
print("  Downloading YOLOv11-Face Model from YapaLab")
print("=" * 70)
print()

# Create models directory if not exists
os.makedirs("models", exist_ok=True)

# Download URL
url = "https://github.com/YapaLab/yolo-face/releases/download/1.0.0/yolov11n-face.pt"
target_path = "models/yolov11n-face.pt"

print(f"📥 Downloading from: {url}")
print(f"📁 Saving to: {target_path}")
print()

try:
    def show_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(downloaded * 100.0 / total_size, 100)
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            size_mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            print(f'\r  Progress: [{bar}] {percent:.1f}% ({size_mb:.1f}/{total_mb:.1f} MB)', end='', flush=True)
    
    urllib.request.urlretrieve(url, target_path, reporthook=show_progress)
    print()
    print()
    print(f"✅ Model downloaded successfully!")
    print(f"   Saved to: {target_path}")
    
    # Check file size
    file_size = os.path.getsize(target_path) / (1024 * 1024)
    print(f"   File size: {file_size:.2f} MB")
    
except Exception as e:
    print()
    print(f"❌ Error: {e}")

print()
print("=" * 70)
print("Done!")
print("=" * 70)
