# 💻 Usage Examples

*Contoh penggunaan lengkap SECURE EDGE VISION SYSTEM*

---

## 📋 Daftar Isi

1. [Running the System](#-running-the-system)
2. [Web Dashboard Usage](#-web-dashboard-usage)
3. [API Usage Examples](#-api-usage-examples)
4. [CLI Tools Examples](#-cli-tools-examples)
5. [Python Integration](#-python-integration)
6. [Advanced Configurations](#-advanced-configurations)

---

## 🚀 Running the System

### Basic Start

```bash
# Start with default configuration
python main.py

# Output:
# ══════════════════════════════════════════════════════
#   SECURE EDGE VISION SYSTEM
# ══════════════════════════════════════════════════════
#
#   Cameras: [0]
#   Device: cuda
#   Dashboard: http://localhost:8000
#
#   Press Ctrl+C to stop
```

### Start with Custom Settings

```bash
# Specify port
python main.py --port 8080

# Specify camera
python main.py --camera 1

# Specify RTSP camera
python main.py --camera "rtsp://admin:pass@192.168.1.100:554/stream"

# Use CPU instead of GPU
python main.py --device cpu

# Combine options
python main.py --port 8080 --camera 0 --device cuda
```

### Command Line Arguments

| Argument | Short | Default | Description |
|:---------|:------|:--------|:------------|
| `--port` | `-p` | 8000 | Web server port |
| `--host` | - | 0.0.0.0 | Web server host |
| `--camera` | `-c` | From .env | Camera source |
| `--device` | `-d` | cuda | Device (cuda/cpu) |

---

## 🌐 Web Dashboard Usage

### Accessing the Dashboard

Open browser and navigate to: `http://localhost:8000`

### Dashboard Features

```
┌─────────────────────────────────────────────────────────┐
│  SECURE EDGE VISION SYSTEM                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────┐               │
│  │                                     │               │
│  │      Live Video Stream              │               │
│  │      (Faces blurred in real-time)   │               │
│  │                                     │               │
│  └─────────────────────────────────────┘               │
│                                                         │
│  Status: 🟢 Online | FPS: 28.5 | Detections: 2         │
│                                                         │
│  [Gallery] [Analytics] [Evidence] [Decrypt]            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Pages

| Page | URL | Description |
|:-----|:----|:------------|
| Dashboard | `/` | Live stream and controls |
| Gallery | `/gallery` | Browse public recordings |
| Analytics | `/analytics` | Charts and statistics |
| Decrypt | `/decrypt` | Evidence decryption tool |
| Replay | `/replay-page/{filename}` | Play specific recording |

---

## 🔌 API Usage Examples

### Get System Status

```bash
# Using curl
curl http://localhost:8000/api/status

# Response:
{
  "status": "running",
  "cameras": [
    {
      "id": 0,
      "fps": 28.5,
      "detections": 2,
      "source": "0",
      "state": "online"
    }
  ],
  "timestamp": "2024-01-15T14:30:00.123456"
}
```

### List Public Recordings

```bash
curl http://localhost:8000/api/recordings

# Response:
{
  "recordings": [
    {
      "filename": "public_cam0_20240115_143000.mp4",
      "path": "recordings/public/public_cam0_20240115_143000.mp4",
      "size_mb": 45.2,
      "created": "2024-01-15T14:30:00",
      "is_active": false
    }
  ]
}
```

### Get Analytics Data

```bash
curl http://localhost:8000/api/analytics

# Response:
{
  "storage": {
    "total_mb": 1250.5,
    "max_gb": 50,
    "public_mb": 980.3,
    "evidence_mb": 270.2,
    "days_left": 12.5
  },
  "trends": {
    "labels": ["00:00", "01:00", ...],
    "values": [5, 2, 0, 0, 1, ...]
  },
  "classification": {
    "face": 150,
    "person": 45
  },
  "health": {
    "cameras_online": 1,
    "total_cameras": 1,
    "disk_free_gb": 256.5
  }
}
```

### Stream Live Video

```html
<!-- Embed in HTML -->
<img src="http://localhost:8000/stream/0" />

<!-- For multiple cameras -->
<img src="http://localhost:8000/stream/0" /> <!-- Camera 0 -->
<img src="http://localhost:8000/stream/1" /> <!-- Camera 1 -->
```

### Decrypt Evidence via API

```bash
# List evidence files
curl http://localhost:8000/api/evidence-decrypt

# Decrypt specific file
curl -X POST http://localhost:8000/api/decrypt \
  -H "Content-Type: application/json" \
  -d '{"filename": "evidence_cam0_20240115_143000_0001.enc", "show_boxes": true}'

# Response:
{
  "success": true,
  "frame_count": 6000,
  "duration": 200.5,
  "hash": "a1b2c3d4e5f6...",
  "video_url": "/api/decrypt-video/abc12345"
}

# Download decrypted video
curl -o decrypted.mp4 "http://localhost:8000/api/decrypt-video/abc12345?download=true"
```

### Python API Client Example

```python
import requests

# Get system status
response = requests.get("http://localhost:8000/api/status")
status = response.json()
print(f"System: {status['status']}")
print(f"Cameras online: {sum(1 for c in status['cameras'] if c['state'] == 'online')}")

# List recordings
response = requests.get("http://localhost:8000/api/recordings")
recordings = response.json()["recordings"]
for rec in recordings[:5]:
    print(f"{rec['filename']}: {rec['size_mb']} MB")

# Decrypt evidence
response = requests.post(
    "http://localhost:8000/api/decrypt",
    json={"filename": "evidence_cam0_20240115.enc", "show_boxes": True}
)
result = response.json()
if result["success"]:
    # Download video
    video_url = f"http://localhost:8000{result['video_url']}"
    video_response = requests.get(video_url)
    with open("decrypted.mp4", "wb") as f:
        f.write(video_response.content)
```

---

## 🛠️ CLI Tools Examples

### Key Management

```bash
# Check key status
python tools/key_manager.py

# Generate AES key
python tools/key_manager.py --generate

# Generate RSA key pair with PIN
python tools/key_manager.py --generate-rsa --pin 1234

# Backup key
python tools/key_manager.py --backup

# Restore key
python tools/key_manager.py --restore keys/backups/master_20240115.key
```

### Evidence Decryption

```bash
# List evidence files
python tools/decryptor.py --list

# Decrypt and play
python tools/decryptor.py --file evidence_cam0_20240115_0001.enc

# Export to MP4
python tools/decryptor.py --file evidence.enc --export output.mp4

# Export without detection boxes
python tools/decryptor.py --file evidence.enc --export clean.mp4 --no-boxes

# Use custom key
python tools/decryptor.py --file evidence.enc --key custom/master.key
```

### Camera Testing

```bash
# List available cameras
python tools/camera_selector.py --list

# Test specific camera
python tools/camera_selector.py --test 0

# Preview camera for 30 seconds
python tools/camera_selector.py --preview 0 --duration 30

# Test RTSP URL
python tools/camera_selector.py --test "rtsp://admin:pass@192.168.1.100:554/stream"
```

### Security Verification

```bash
# Run tamper detection demo (for thesis)
python tools/verify_integrity.py --demo

# Verify specific file
python tools/verify_integrity.py --verify recordings/evidence/cam0/evidence.enc

# Test file-level integrity
python tools/verify_integrity.py --test-file
```

### Configuration

```bash
# Show system info
python config.py --info

# Validate configuration
python config.py --validate

# Create default .env
python config.py --create-env

# Print .env template
python config.py --template > .env.example
```

### Face Detection Demo

```bash
# Run demo with webcam
python demo.py

# With specific camera
python demo.py --source 1

# Adjust settings
python demo.py --confidence 0.6 --blur 71 --device cpu
```

### Performance Benchmark

```bash
# Run full benchmark
python benchmark.py

# Quick test with 100 frames
python benchmark.py --frames 100

# Save results
python benchmark.py --output benchmark_results.csv
```

---

## 🐍 Python Integration

### Using FrameProcessor Directly

```python
from modules.processor import FrameProcessor
import cv2

# Initialize processor
processor = FrameProcessor(
    model_path="models/model.pt",
    device="cuda",
    confidence=0.5,
    blur_intensity=51
)

# Load model
if not processor.load_model():
    raise RuntimeError("Failed to load model")

# Open camera
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Process frame
    blurred, raw, detections = processor.process(frame)
    
    # Display
    cv2.imshow("Blurred", blurred)
    print(f"Detected {len(detections)} faces")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### Using EvidenceManager

```python
from modules.evidence import EvidenceManager
import cv2
import numpy as np

# Initialize manager
manager = EvidenceManager(
    output_dir="recordings/evidence/test",
    key_path="keys/master.key",
    max_duration=60,  # 1 minute files
    detection_only=True
)

# Add frames
for i in range(300):  # 10 seconds at 30fps
    # Create test frame
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Simulate detection every 30 frames
    detections = []
    if i % 30 == 0:
        detections = [{"class": "face", "x1": 100, "y1": 100, "x2": 200, "y2": 200}]
    
    # Add frame
    manager.add_frame(frame, detections)

# Flush and close
manager.close()

# List saved files
for f in manager.get_evidence_list():
    print(f"Saved: {f['filename']} ({f['size_mb']} MB)")
```

### Using SecureVault

```python
from modules.security import SecureVault
import hashlib

# Create vault
vault = SecureVault(key_path="keys/master.key")

# Encrypt data
original_data = b"Sensitive video frame data" * 1000
package = vault.lock_evidence(original_data, {"camera": "cam0"})

print(f"Original size: {len(original_data)} bytes")
print(f"Encrypted size: {len(package.ciphertext)} bytes")
print(f"Hash: {package.original_hash[:32]}...")

# Decrypt and verify
decrypted, verified_hash = vault.unlock_evidence(package)

assert decrypted == original_data
assert verified_hash == hashlib.sha256(original_data).hexdigest()
print("✓ Decryption and verification successful!")

# Save to file
vault.save_encrypted_file(original_data, "test.enc", {"test": True})

# Load from file
loaded_data, metadata = vault.load_encrypted_file("test.enc")
assert loaded_data == original_data
print("✓ File save/load successful!")
```

### Using VideoRecorder

```python
from modules.recorder import VideoRecorder
import cv2
import numpy as np
import time

# Initialize recorder
recorder = VideoRecorder(
    output_dir="recordings/public",
    prefix="test_video",
    fps=30,
    max_duration=10  # 10 seconds per file
)

# Write frames
for i in range(600):  # 20 seconds = 2 files
    # Create test frame
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.putText(frame, f"Frame {i}", (500, 360),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    
    # Write frame
    detections = [{"class": "face"}] if i % 60 == 0 else None
    recorder.write(frame, detections)
    
    time.sleep(1/30)  # Simulate 30fps

# Close recorder
recorder.close()

# List recordings
for rec in recorder.get_recording_list():
    print(f"Recorded: {rec['filename']} ({rec['size_mb']} MB)")
```

---

## ⚙️ Advanced Configurations

### Multi-Camera Setup

```env
# .env file
CAMERA_SOURCES=0,1,rtsp://admin:pass@192.168.1.100:554/stream
```

```python
# In code
from config import Config
config = Config()
print(f"Cameras: {config.camera_sources}")
# Output: Cameras: [0, 1, 'rtsp://admin:pass@192.168.1.100:554/stream']
```

### High Security Mode

```env
# .env file
EVIDENCE_DETECTION_ONLY=True
EVIDENCE_JPEG_QUALITY=90
MAX_STORAGE_GB=100

# Use RSA keys
RSA_PUBLIC_KEY_PATH=keys/rsa_public.pem
RSA_PRIVATE_KEY_PATH=keys/rsa_private.pem
```

### Performance Optimization

```env
# For low-power devices
DEVICE=cpu
DETECTION_CONFIDENCE=0.6
TARGET_FPS=15
EVIDENCE_JPEG_QUALITY=60

# For high-end GPUs
DEVICE=cuda
DETECTION_CONFIDENCE=0.5
TARGET_FPS=30
EVIDENCE_JPEG_QUALITY=85
```

### Storage Management

```env
# Auto-cleanup when storage reaches limit
MAX_STORAGE_GB=50
PUBLIC_RECORDINGS_PATH=/mnt/storage/public
EVIDENCE_RECORDINGS_PATH=/mnt/storage/evidence
```

---

## 📊 Integration Examples

### Webhook Notification

```python
# Custom event handler (add to main.py)
import requests

def on_detection(camera_idx, detections):
    """Called when faces are detected"""
    if len(detections) > 0:
        requests.post("https://your-webhook.com/alert", json={
            "camera": camera_idx,
            "count": len(detections),
            "timestamp": time.time()
        })
```

### Database Integration

```python
import sqlite3
from datetime import datetime

def log_detection(camera_idx, detection_count):
    """Log detection to SQLite database"""
    conn = sqlite3.connect("detections.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY,
            camera INTEGER,
            count INTEGER,
            timestamp TEXT
        )
    """)
    
    cursor.execute(
        "INSERT INTO detections (camera, count, timestamp) VALUES (?, ?, ?)",
        (camera_idx, detection_count, datetime.now().isoformat())
    )
    
    conn.commit()
    conn.close()
```

---

## ➡️ Navigasi Wiki

| Sebelumnya | Selanjutnya |
|:-----------|:------------|
| [API](API.md) | [Tools](Tools.md) |
