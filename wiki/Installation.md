# 💻 Installation & Setup Guide

*Panduan lengkap instalasi dan konfigurasi SECURE EDGE VISION SYSTEM*

---

## 📋 Daftar Isi

1. [System Requirements](#-system-requirements)
2. [Quick Install](#-quick-install)
3. [Detailed Installation](#-detailed-installation)
4. [Configuration](#-configuration)
5. [First Run](#-first-run)
6. [Troubleshooting](#-troubleshooting)
7. [CUDA Setup](#-cuda-setup)

---

## 🖥️ System Requirements

### Minimum Requirements

| Component | Minimum | Recommended |
|:----------|:--------|:------------|
| **OS** | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| **CPU** | Intel i5 8th Gen | Intel i5 10th Gen+ |
| **RAM** | 8 GB | 16 GB |
| **GPU** | NVIDIA GTX 1650 (4GB) | NVIDIA RTX 3050+ (6GB+) |
| **Storage** | 256 GB SSD | 512 GB NVMe SSD |
| **Python** | 3.10 | 3.11+ |

### GPU Requirements (CUDA)

Sistem memerlukan **NVIDIA GPU dengan CUDA support** untuk performa real-time:

| GPU | VRAM | Expected FPS | Status |
|:----|:-----|:-------------|:-------|
| GTX 1650 | 4 GB | 20-25 FPS | ✅ Minimum |
| GTX 1660 | 6 GB | 25-28 FPS | ✅ Good |
| RTX 3050 | 4 GB | 28-30 FPS | ✅ Recommended |
| RTX 3060 | 12 GB | 30+ FPS | ✅ Excellent |
| RTX 4060 | 8 GB | 30+ FPS | ✅ Excellent |

**Tanpa GPU:**
- Sistem akan fallback ke CPU
- FPS turun drastis (~5-10 FPS)
- Tidak disarankan untuk production

### Software Dependencies

- Python 3.10 - 3.12+
- CUDA Toolkit 11.8 atau 12.1
- cuDNN 8.x
- Visual C++ Redistributable 2019+ (Windows)

---

## 🚀 Quick Install

### Windows (Recommended)

```cmd
# 1. Clone repository
git clone <repository-url>
cd SECURE-EDGE-VISION-SYSTEM

# 2. Run setup script
setup.bat
```

### Linux/Mac

```bash
# 1. Clone repository
git clone <repository-url>
cd SECURE-EDGE-VISION-SYSTEM

# 2. Make setup script executable
chmod +x setup.sh

# 3. Run setup
./setup.sh
```

---

## 📦 Detailed Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd SECURE-EDGE-VISION-SYSTEM
```

### Step 2: Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Install PyTorch with CUDA (GPU Support)

**CUDA 12.1 (Recommended):**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**CUDA 11.8:**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**CPU Only (No GPU):**
```bash
pip install torch torchvision
```

### Step 6: Create Directories

```bash
mkdir -p models keys recordings/public recordings/evidence
```

### Step 7: Download YOLOv8-Face Model (Optional)

Sistem akan auto-download `yolov8n.pt` jika model tidak ditemukan. Untuk model face detection khusus:

```bash
# Download model ke folder models/
# Rename to model.pt
```

### Step 8: Generate Encryption Key

```bash
python tools/key_manager.py --generate
```

---

## ⚙️ Configuration

### Environment File (.env)

Copy template dan edit sesuai kebutuhan:

```bash
# Linux/Mac
cp .env.example .env
nano .env

# Windows
copy .env.example .env
notepad .env
```

### Configuration Options

```env
# ═══════════════════════════════════════════════════════════════
# SECURE EDGE VISION SYSTEM - Configuration
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# CAMERA SETTINGS
# ═══════════════════════════════════════════════════════════════
# Single camera (webcam index)
CAMERA_SOURCES=0

# Multiple cameras (comma separated)
# CAMERA_SOURCES=0,1,rtsp://192.168.1.100:554/stream

# ═══════════════════════════════════════════════════════════════
# AI/DETECTION SETTINGS
# ═══════════════════════════════════════════════════════════════
# Model path (will auto-download yolov8n.pt if not found)
MODEL_PATH=models/model.pt

# Detection preset (1 or 2)
# Preset 1: YOLOv8-Face + BoT-SORT (conf=0.35, iou=0.45)
# Preset 2: YOLOv11-Face + ByteTrack (conf=0.30, iou=0.50)
DETECTION_PRESET=1

# Detection confidence threshold (0.0 - 1.0)
# Note: Can be overridden by preset values
DETECTION_CONFIDENCE=0.5

# IoU threshold for NMS/tracking (0.0 - 1.0)
# Note: Can be overridden by preset values
DETECTION_IOU=0.45

# Device: cuda (GPU) or cpu
DEVICE=cuda

# Blur kernel size (must be ODD number, higher = more blur)
BLUR_INTENSITY=51

# ═══════════════════════════════════════════════════════════════
# SERVER SETTINGS
# ═══════════════════════════════════════════════════════════════
# Host to bind (0.0.0.0 = all interfaces)
SERVER_HOST=0.0.0.0

# Port number
SERVER_PORT=8000

# ═══════════════════════════════════════════════════════════════
# RECORDING SETTINGS
# ═══════════════════════════════════════════════════════════════
# Max recording duration before file rotation (seconds)
RECORDING_DURATION_SECONDS=300

# Target frames per second
TARGET_FPS=30

# ═══════════════════════════════════════════════════════════════
# STORAGE OPTIMIZATION
# ═══════════════════════════════════════════════════════════════
# Only record evidence when faces detected (saves 80% storage)
EVIDENCE_DETECTION_ONLY=True

# JPEG quality for evidence frames (0-100, lower = smaller files)
EVIDENCE_JPEG_QUALITY=75

# Maximum storage limit (GB) - auto-cleanup when exceeded
MAX_STORAGE_GB=50

# ═══════════════════════════════════════════════════════════════
# STORAGE PATHS
# ═══════════════════════════════════════════════════════════════
# Where to save blurred public recordings
PUBLIC_RECORDINGS_PATH=recordings/public

# Where to save encrypted evidence
EVIDENCE_RECORDINGS_PATH=recordings/evidence

# ═══════════════════════════════════════════════════════════════
# SECURITY SETTINGS
# ═══════════════════════════════════════════════════════════════
# Path to AES-256 encryption key (auto-generated if not exists)
# ⚠️ BACKUP THIS FILE! Without it, evidence cannot be decrypted!
ENCRYPTION_KEY_PATH=keys/master.key

# RSA keys for hybrid encryption (optional)
RSA_PUBLIC_KEY_PATH=keys/rsa_public.pem
RSA_PRIVATE_KEY_PATH=keys/rsa_private.pem

# ═══════════════════════════════════════════════════════════════
# OVERLAY SETTINGS
# ═══════════════════════════════════════════════════════════════
# Show timestamp on video stream
SHOW_TIMESTAMP=True

# Show debug overlay (FPS, detection count, status)
SHOW_DEBUG_OVERLAY=False
```

### Camera Source Examples

| Source Type | Format | Example |
|:------------|:-------|:--------|
| USB Webcam | Integer index | `0`, `1`, `2` |
| IP Camera (RTSP) | URL | `rtsp://192.168.1.100:554/stream` |
| IP Camera with Auth | URL with credentials | `rtsp://user:pass@192.168.1.100:554/stream` |
| Video File | File path | `videos/test.mp4` |
| Multiple | Comma separated | `0,1,rtsp://192.168.1.100:554/stream` |

---

## 🎬 First Run

### 1. Test Components

Sebelum menjalankan sistem penuh, test komponen individual:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Run component tests
python demo.py --quick
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════╗
║   SECURE EDGE VISION - Demo                                  ║
╚══════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────┐
│ Camera                                                       │
└──────────────────────────────────────────────────────────────┘
  ✓ Camera opened: 0
  → Resolution: 1280x720 @ 30fps

┌──────────────────────────────────────────────────────────────┐
│ GPU (CUDA)                                                   │
└──────────────────────────────────────────────────────────────┘
  ✓ CUDA Available
  → GPU: NVIDIA GeForce RTX 3050
  → Memory: 4.0 GB
  → CUDA: 12.1

┌──────────────────────────────────────────────────────────────┐
│ AI Model (YOLOv8)                                            │
└──────────────────────────────────────────────────────────────┘
  ✓ Model loaded: Face Detection
  → Path: models/model.pt
  ✓ Detection test passed
  → Found 1 object(s) in 15ms

┌──────────────────────────────────────────────────────────────┐
│ Security (AES-256-GCM)                                       │
└──────────────────────────────────────────────────────────────┘
  ✓ Encryption working
  → Original: 46 bytes → Encrypted: 158 bytes
  ✓ Decryption verified
  ✓ Tamper detection working

══════════════════════════════════════════════════════════════
  TEST SUMMARY
══════════════════════════════════════════════════════════════

  ✓ Camera
  ✓ GPU
  ✓ AI Model
  ✓ Security

  🎉 All tests passed!

  Next steps:
    python main.py
    Open: http://localhost:8000
```

### 2. Run Main Application

```bash
# With default preset
python main.py

# With alternative preset
python main.py --preset 2

# With custom options
python main.py --preset 1 --device cuda --port 8000
```

**Expected Output:**
```
============================================================
Starting Secure Edge Vision System (Multi-Camera)
============================================================
INFO: Active Preset: Default (YOLOv8-Face + BoT-SORT)
INFO: Detector: yolov8n-face
INFO: Tracker: botsort
INFO: Loaded: models/model.pt (Face model)
INFO: Detection config: conf=0.35, iou=0.45, tracker=botsort
INFO: Processor ready on CUDA
INFO: Initializing Channel 0: 0
INFO: System ready! All 1 threads starting...
============================================================
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 3. Access Web Dashboard

Buka browser dan navigate ke:
```
http://localhost:8000
```

**Dashboard Features:**
- Live stream (blurred)
- Detection counter
- FPS monitor
- Multi-camera switching

---

## 🔧 Troubleshooting

### Error: "CUDA not available"

**Penyebab:** PyTorch tidak terinstall dengan CUDA support

**Solusi:**
```bash
# Uninstall CPU version
pip uninstall torch torchvision

# Install CUDA version
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Error: "Cannot open camera 0"

**Penyebab:** Kamera tidak terdeteksi atau sudah digunakan aplikasi lain

**Solusi:**
1. Pastikan tidak ada aplikasi lain yang menggunakan kamera
2. Coba index kamera berbeda: `CAMERA_SOURCES=1`
3. Windows: Restart service "Camera" di Services
4. Check device manager untuk driver

### Error: "Key file not found"

**Penyebab:** Encryption key belum di-generate

**Solusi:**
```bash
python tools/key_manager.py --generate
```

### Error: "OpenH264 library not found" (Windows)

**Penyebab:** Missing video codec DLL

**Solusi:**
```bash
python fix_video.py
```

### Error: "Port 8000 already in use"

**Penyebab:** Port sudah digunakan aplikasi lain

**Solusi:**
1. Ubah port di `.env`: `SERVER_PORT=8080`
2. Atau matikan aplikasi yang menggunakan port 8000

### Low FPS (<15 FPS)

**Penyebab:** GPU tidak digunakan atau model terlalu berat

**Solusi:**
1. Verify CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
2. Check device setting: `DEVICE=cuda`
3. Lower resolution: ubah kamera ke 720p
4. Use lighter model: `MODEL_PATH=yolov8n.pt`

---

## 🎮 CUDA Setup

### Check CUDA Installation

```bash
# Check if CUDA is installed
nvidia-smi

# Check PyTorch CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

### Install CUDA Toolkit (If Missing)

**Windows:**
1. Download CUDA Toolkit from [NVIDIA](https://developer.nvidia.com/cuda-downloads)
2. Run installer (Express installation)
3. Restart computer
4. Verify: `nvcc --version`

**Ubuntu:**
```bash
# Add NVIDIA repository
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update

# Install CUDA
sudo apt-get install cuda-toolkit-12-1

# Add to PATH
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### Fix CUDA for PyTorch (Windows)

Jika CUDA terinstall tapi PyTorch tetap pakai CPU:

```cmd
# Run fix script
fix_cuda.bat
```

Atau manual:
```bash
pip uninstall -y torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install ultralytics --upgrade
```

---

## 📁 Directory Structure After Installation

```
SECURE-EDGE-VISION-SYSTEM/
├── venv/                  # Virtual environment
├── keys/
│   └── master.key         # Auto-generated encryption key
├── models/
│   └── model.pt           # YOLOv8 model (auto-downloaded)
├── recordings/
│   ├── public/            # MP4 files (blurred)
│   └── evidence/          # .enc files (encrypted)
├── .env                   # Your configuration
└── ...
```

---

## ✅ Verification Checklist

Setelah instalasi, pastikan semua item berikut ✅:

- [ ] Python 3.11+ terinstall
- [ ] Virtual environment aktif
- [ ] Dependencies terinstall (`pip list | grep torch`)
- [ ] CUDA working (`python -c "import torch; print(torch.cuda.is_available())"`)
- [ ] Camera accessible (`python demo.py --quick`)
- [ ] Encryption key generated (`ls keys/master.key`)
- [ ] `.env` file configured
- [ ] Main app runs without error (`python main.py`)
- [ ] Web dashboard accessible (`http://localhost:8000`)

---

## ➡️ Navigasi Wiki

| Sebelumnya | Selanjutnya |
|:-----------|:------------|
| [DualPath](DualPath.md) | [Modules](Modules.md) |
