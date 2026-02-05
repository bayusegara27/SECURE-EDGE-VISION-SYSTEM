# 🚀 Quick Start Guide

_Panduan cepat untuk memulai SECURE EDGE VISION SYSTEM_

---

## 📋 Daftar Isi

1. [Requirements](#-requirements)
2. [5-Minute Setup](#-5-minute-setup)
3. [Basic Usage](#-basic-usage)
4. [Configuration](#-configuration)
5. [Testing the System](#-testing-the-system)
6. [Next Steps](#-next-steps)

---

## 📦 Requirements

### Hardware

| Component | Minimum            | Recommended              |
| :-------- | :----------------- | :----------------------- |
| CPU       | Intel i5 / Ryzen 5 | Intel i7 / Ryzen 7       |
| RAM       | 8 GB               | 16 GB                    |
| GPU       | GTX 1050 Ti (4GB)  | RTX 3050+ (4GB+)         |
| Storage   | 50 GB SSD          | 256 GB+ SSD              |
| Camera    | 720p Webcam        | 1080p Webcam / IP Camera |

### Software

- **Python**: 3.9 - 3.11
- **CUDA**: 11.x atau 12.x (untuk GPU)
- **OS**: Windows 10/11, Ubuntu 20.04+

---

## ⚡ 5-Minute Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/bayusegara27/SECURE-EDGE-VISION-SYSTEM.git
cd SECURE-EDGE-VISION-SYSTEM
```

### Step 2: Install Dependencies

**Windows (Recommended):**

```batch
# Run setup script
setup.bat
```

**Linux/macOS:**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Manual Installation:**

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install ultralytics opencv-python fastapi uvicorn python-dotenv cryptography
```

### Step 3: Generate Encryption Keys

```bash
# Generate AES-256 encryption key
python tools/key_manager.py --generate

# (Optional) Generate RSA keys for enhanced security
python tools/key_manager.py --generate-rsa
```

### Step 4: Configure Camera

```bash
# Test default webcam
python tools/camera_selector.py --test 0

# If using IP camera, test RTSP
python tools/camera_selector.py --test "rtsp://admin:password@192.168.1.100:554/stream"
```

### Step 5: Start the System

```bash
# Start with default preset (YOLOv8-Face + BoT-SORT)
python main.py

# Or use alternative preset (YOLOv11-Face + ByteTrack)
python main.py --preset 2

# Using environment variable
DETECTION_PRESET=2 python main.py
```

**Note**: If you see OpenH264 warnings:

```
Failed to load OpenH264 library: openh264-1.8.0-win64.dll
[libopenh264] Incorrect library version loaded
```

Don't worry! The system automatically uses the `avc1` codec fallback. Your recordings work perfectly. If you want to remove the warnings, run:

```bash
python fix_openh264.py
```

See [OPENH264_FIX.md](../OPENH264_FIX.md) for more details.

### Step 6: Open Web Dashboard

Open browser and go to: **http://localhost:8000**

🎉 **Done!** System is now running.

---

## 💡 Basic Usage

### Web Dashboard

Akses dashboard di `http://localhost:8000`:

| Page        | URL           | Function                |
| :---------- | :------------ | :---------------------- |
| Dashboard   | `/`           | Main control panel      |
| Live Stream | `/stream/0`   | Camera 0 live feed      |
| Recordings  | `/recordings` | View public recordings  |
| Evidence    | `/evidence`   | View encrypted evidence |
| Status      | `/api/status` | System status JSON      |

### Starting & Stopping

```bash
# Start system with default preset
python main.py

# Start with alternative preset
python main.py --preset 2

# Combine preset with other options
python main.py --preset 2 --device cuda --port 8080

# Stop system
# Press Ctrl+C in terminal
# Or access http://localhost:8000/shutdown (if enabled)
```

### View Recordings

```bash
# Public recordings (blurred faces)
# Located in: recordings/public/
# Format: MP4, playable in any video player

# Evidence recordings (original, encrypted)
# Located in: recordings/evidence/cam0/
# Requires decryption tool
```

### Decrypt Evidence

```bash
# List evidence files
python tools/decryptor.py --list

# Decrypt and play
python tools/decryptor.py --file evidence_cam0_20240115_120000_0001.enc

# Export to MP4
python tools/decryptor.py --file evidence.enc --export output.mp4
```

---

## ⚙️ Configuration

### Environment Variables (.env)

Create `.env` file in project root:

```env
# === Camera Settings ===
# Webcam: 0, 1, 2...
# RTSP: rtsp://user:pass@ip:port/stream
# Multiple: 0,1,rtsp://...
CAMERA_SOURCES=0

# === Detection Preset ===
# Preset 1 (Default): YOLOv8-Face + BoT-SORT (conf=0.35, iou=0.45)
# Preset 2 (Alternative): YOLOv11-Face + ByteTrack (conf=0.30, iou=0.50)
DETECTION_PRESET=1

# === AI Settings ===
DEVICE=cuda
MODEL_PATH=models/model.pt
DETECTION_CONFIDENCE=0.5
BLUR_INTENSITY=51

# === Server Settings ===
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# === Recording Settings ===
TARGET_FPS=30
RECORDING_DURATION_SECONDS=300

# === Storage Paths ===
PUBLIC_RECORDINGS_PATH=recordings/public
EVIDENCE_RECORDINGS_PATH=recordings/evidence

# === Security ===
ENCRYPTION_KEY_PATH=keys/master.key
```

### Quick Configuration Examples

**Single Webcam (Default):**

```env
CAMERA_SOURCES=0
DEVICE=cuda
```

**Multiple Cameras:**

```env
CAMERA_SOURCES=0,1,2
```

**IP Camera (RTSP):**

```env
CAMERA_SOURCES=rtsp://admin:password@192.168.1.100:554/stream1
```

**Mixed (Webcam + IP Camera):**

```env
CAMERA_SOURCES=0,rtsp://admin:password@192.168.1.100:554/stream1
```

**CPU Mode (No GPU):**

```env
DEVICE=cpu
DETECTION_CONFIDENCE=0.6
```

**High Security Mode:**

```env
EVIDENCE_DETECTION_ONLY=True
EVIDENCE_JPEG_QUALITY=90
```

**Alternative Detection Preset:**

```env
DETECTION_PRESET=2
```

### Using Detection Presets

The system supports 2 detection presets for easy configuration switching:

| Preset              | Detector     | Tracker   | Confidence | IoU  |
| :------------------ | :----------- | :-------- | :--------- | :--- |
| **1** (Default)     | YOLOv8-Face  | BoT-SORT  | 0.35       | 0.45 |
| **2** (Alternative) | YOLOv11-Face | ByteTrack | 0.30       | 0.50 |

**How to switch presets:**

```bash
# CLI argument (priority)
python main.py --preset 2

# Environment variable
DETECTION_PRESET=2 python main.py

# In .env file
DETECTION_PRESET=2
```

### Validate Configuration

```bash
python config.py --validate

# Output:
# ✓ Configuration valid!
```

---

## 🧪 Testing the System

### Test 1: Camera Connection

```bash
python tools/camera_selector.py --test 0
# ✓ 0: Connection Successful
```

### Test 2: Face Detection

```bash
python demo.py
# Shows live video with face detection
# Press Q to quit
```

### Test 3: Encryption

```bash
python tools/verify_integrity.py --demo
# Shows tamper detection capabilities
```

### Test 4: Full System

```bash
# Start system
python main.py

# In another terminal, check status
curl http://localhost:8000/api/status

# Or open browser to http://localhost:8000
```

### Test 5: Evidence Workflow

```bash
# Wait for some detections to occur...
# Then:

# List evidence files
python tools/decryptor.py --list

# Decrypt and verify
python tools/verify_integrity.py --verify recordings/evidence/cam0/evidence_*.enc
```

---

## 📊 System Status Indicators

### Web Dashboard Status

| Indicator     | Meaning                         |
| :------------ | :------------------------------ |
| 🟢 Online     | Camera connected and processing |
| 🟡 Connecting | Camera connecting...            |
| 🔴 Offline    | Camera disconnected             |
| FPS: 30       | Current processing speed        |
| DET: 2        | Number of faces detected        |

### Console Logs

```bash
# Normal operation
INFO: [Cam 0] Connected successfully
INFO: [public_cam0] Recording: public_cam0_20240115_143000.mp4

# Detection event
INFO: [BG] Saved evidence: evidence_cam0_20240115_143000_0001.enc (150 frames)

# Camera issues
WARNING: [Cam 0] Connection failed, retrying in 5s...
```

---

## 📈 Performance Tips

### For Better FPS

1. **Use GPU**: Set `DEVICE=cuda`
2. **Lower Resolution**: Camera 720p is sufficient
3. **Reduce Detection Confidence**: `DETECTION_CONFIDENCE=0.4`
4. **Use Selective Recording**: `EVIDENCE_DETECTION_ONLY=True`

### For Better Detection

1. **Increase Confidence**: `DETECTION_CONFIDENCE=0.6`
2. **Use Face Model**: Ensure `models/model.pt` is face detection model
3. **Good Lighting**: Ensure adequate lighting for camera

### For Better Security

1. **Use RSA Keys**: `python tools/key_manager.py --generate-rsa`
2. **Backup Keys**: `python tools/key_manager.py --backup`
3. **Higher JPEG Quality**: `EVIDENCE_JPEG_QUALITY=90`

---

## 🎯 Next Steps

### After Basic Setup

1. **📖 Read Full Documentation**
   - [Installation Guide](Installation.md)
   - [Architecture](Architecture.md)
   - [Security](Security.md)

2. **🔧 Advanced Configuration**
   - Multiple cameras setup
   - RTSP camera integration
   - Storage management

3. **🛠️ Learn the Tools**
   - [Tools Documentation](Tools.md)
   - [API Reference](API.md)

4. **📊 Performance Tuning**
   - Run `python benchmark.py`
   - Optimize based on results

5. **🔐 Security Hardening**
   - Setup RSA hybrid encryption
   - Configure key backup procedures

---

## ❓ Common Issues

### Camera Not Detected

```bash
# Check available cameras
python tools/camera_selector.py --list

# On Linux, install v4l-utils
sudo apt install v4l-utils
v4l2-ctl --list-devices
```

### CUDA Not Available

```bash
# Check CUDA status
python config.py --info

# If CUDA not working, use CPU mode
# Edit .env:
DEVICE=cpu
```

### Port Already in Use

```bash
# Change port in .env
SERVER_PORT=8080

# Or kill existing process
# Windows: netstat -ano | findstr :8000
# Linux: lsof -i :8000
```

### Out of Memory (GPU)

```bash
# Reduce model size or use CPU
DEVICE=cpu

# Or reduce batch size by lowering FPS
TARGET_FPS=15
```

---

## 🆘 Getting Help

1. **📚 Documentation**: Read the [Wiki](Home.md)
2. **❓ FAQ**: Check [FAQ](FAQ.md)
3. **🐛 Troubleshooting**: See [Troubleshooting](Troubleshooting.md)
4. **💬 Issues**: Open GitHub Issue

---

## ➡️ Navigasi Wiki

| Sebelumnya      | Selanjutnya                     |
| :-------------- | :------------------------------ |
| [Home](Home.md) | [Installation](Installation.md) |
