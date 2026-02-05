# 🛠️ Tools Documentation

*Dokumentasi lengkap semua CLI tools dalam SECURE EDGE VISION SYSTEM*

---

## 📋 Daftar Isi

1. [Overview](#-overview)
2. [tools/decryptor.py](#-toolsdecryptorpy)
3. [tools/key_manager.py](#-toolskey_managerpy)
4. [tools/camera_selector.py](#-toolscamera_selectorpy)
5. [tools/verify_integrity.py](#-toolsverify_integritypy)
6. [tools/generate_thumbnails.py](#-toolsgenerate_thumbnailspy)
7. [demo.py](#-demopy)
8. [benchmark.py](#-benchmarkpy)
9. [config.py](#-configpy-cli)

---

## 🔍 Overview

### Tools Directory Structure

```
tools/
├── decryptor.py          # Decrypt & play evidence files
├── key_manager.py        # Encryption key management
├── camera_selector.py    # Camera detection & testing
├── verify_integrity.py   # Tamper detection demonstration
└── generate_thumbnails.py # Generate video thumbnails

Root tools:
├── demo.py               # Face detection demo (standalone)
├── benchmark.py          # Performance benchmarking
└── config.py             # Configuration validation CLI
```

### Quick Reference

| Tool | Purpose | Common Use |
|:-----|:--------|:-----------|
| `main.py` | Run system | `python main.py --preset 2` |
| `decryptor.py` | Decrypt evidence | `python tools/decryptor.py --list` |
| `key_manager.py` | Manage keys | `python tools/key_manager.py --generate` |
| `camera_selector.py` | Test cameras | `python tools/camera_selector.py --test 0` |
| `verify_integrity.py` | Security demo | `python tools/verify_integrity.py --demo` |
| `demo.py` | Face detection test | `python demo.py` |
| `benchmark.py` | Performance test | `python benchmark.py` |
| `config.py` | Validate config | `python config.py --validate` |

---

## 🚀 main.py

### Purpose

Main application entry point. Runs the FastAPI server with the complete surveillance system.

### Usage

```bash
# Run with default preset (YOLOv8-Face + BoT-SORT)
python main.py

# Run with alternative preset (YOLOv11-Face + ByteTrack)
python main.py --preset 2

# Run with custom port and device
python main.py --preset 1 --device cuda --port 8080

# Using environment variable
DETECTION_PRESET=2 python main.py
```

### Arguments Reference

| Argument | Short | Default | Description |
|:---------|:------|:--------|:------------|
| `--preset` | - | `1` | Detection preset (1 or 2) |
| `--port` | `-p` | `8000` | Web server port |
| `--host` | - | `0.0.0.0` | Web server host |
| `--camera` | `-c` | `0` | Camera source |
| `--device` | `-d` | `cuda` | Device (`cuda` or `cpu`) |

### Detection Presets

| Preset | Detector | Tracker | Confidence | IoU |
|:-------|:---------|:--------|:-----------|:----|
| **1** (Default) | YOLOv8-Face | BoT-SORT | 0.35 | 0.45 |
| **2** (Alternative) | YOLOv11-Face | ByteTrack | 0.30 | 0.50 |

### Example Output

```bash
python main.py --preset 2

# ============================================================
#   SECURE EDGE VISION SYSTEM
# ============================================================
# 
#   Preset: Alternative (YOLOv11-Face + ByteTrack)
#   Detector: yolov11n-face
#   Tracker: bytetrack
#   Cameras: [0]
#   Device: cuda
#   Dashboard: http://localhost:8000
# 
#   Press Ctrl+C to stop
```

---

## 🔓 tools/decryptor.py

### Purpose

Decrypt dan putar file evidence terenkripsi (.enc) untuk keperluan forensik. Tool ini hanya untuk authorized personnel.

### Installation Requirements

```bash
pip install opencv-python numpy
```

### Usage

```bash
# List all evidence files
python tools/decryptor.py --list

# Decrypt specific file
python tools/decryptor.py --file evidence_cam0_20240115_120000_0001.enc

# Export to MP4 (without playing)
python tools/decryptor.py --file evidence.enc --export output.mp4

# Use custom key file
python tools/decryptor.py --file evidence.enc --key custom/path/master.key

# Decrypt hybrid-encrypted file (RSA+AES)
python tools/decryptor.py --file evidence.enc --private-key keys/rsa_private.pem

# Export without detection boxes
python tools/decryptor.py --file evidence.enc --export output.mp4 --no-boxes
```

### Arguments Reference

| Argument | Short | Default | Description |
|:---------|:------|:--------|:------------|
| `--list` | `-l` | - | List all evidence files |
| `--file` | `-f` | - | Evidence file to decrypt (.enc) |
| `--key` | `-k` | `keys/master.key` | Symmetric key path |
| `--private-key` | `-p` | `keys/rsa_private.pem` | RSA private key (hybrid) |
| `--evidence-dir` | `-d` | `recordings/evidence` | Evidence directory |
| `--export` | `-e` | - | Export to MP4 file |
| `--no-boxes` | - | False | Disable detection overlays |

### Example: Complete Workflow

```bash
# 1. List available evidence
python tools/decryptor.py --list

# Output:
# Found 3 evidence file(s):
#   1. evidence_cam0_20240115_143000_0001.enc
#      Size: 45.2 MB
#      Created: 2024-01-15 14:30:00
#   ...

# 2. Decrypt and play
python tools/decryptor.py -f evidence_cam0_20240115_143000_0001.enc

# Playback controls:
# - Q: Quit
# - SPACE: Pause/Resume
# - N: Next frame (when paused)
# - P: Previous frame (when paused)

# 3. Export for court submission
python tools/decryptor.py -f evidence_cam0_20240115_143000_0001.enc \
    --export court_evidence_2024.mp4
```

### Output Format

Exported MP4 contains:
- Original RAW frames (not blurred)
- Detection bounding boxes (unless `--no-boxes`)
- Frame number and timestamp overlay
- "CONFIDENTIAL EVIDENCE" watermark

### Error Handling

```bash
# Wrong key error
❌ DECRYPTION FAILED!
   Decryption failed - evidence may have been tampered with

# File not found
❌ File not found: evidence_cam0_20240115.enc

# Tampered file
⚠️  This evidence file may have been tampered with!
```

---

## 🔐 tools/key_manager.py

### Purpose

Manage encryption keys untuk sistem. Mendukung:
- Symmetric AES-256 keys (standard)
- RSA key pairs (hybrid encryption)
- Key backup dan restore

### Usage

```bash
# Show key status (default)
python tools/key_manager.py

# Generate new symmetric key
python tools/key_manager.py --generate

# Generate RSA key pair
python tools/key_manager.py --generate-rsa

# Generate RSA with PIN protection
python tools/key_manager.py --generate-rsa --pin 1234

# Backup current key
python tools/key_manager.py --backup

# Restore from backup
python tools/key_manager.py --restore keys/backups/master_20240115.key

# Force overwrite (WARNING!)
python tools/key_manager.py --generate --force

# Export with password protection
python tools/key_manager.py --export
```

### Arguments Reference

| Argument | Short | Description |
|:---------|:------|:------------|
| `--generate` | `-g` | Generate new AES-256 key |
| `--generate-rsa` | - | Generate RSA-2048 key pair |
| `--pin` | - | Password for RSA private key |
| `--rsa-info` | - | Show RSA key information |
| `--force` | `-f` | Overwrite existing key |
| `--backup` | `-b` | Backup current key |
| `--restore` | `-r` | Restore from backup |
| `--export` | `-e` | Export with password |

### Example: Setup Encryption Keys

```bash
# === OPTION 1: Standard Setup (AES only) ===
python tools/key_manager.py --generate

# Output:
# ✓ Key generated: keys/master.key
#   Size: 32 bytes (256-bit)
#   Hash: a1b2c3d4e5f6...
#
# ⚠️  IMPORTANT: Backup this key immediately!

# === OPTION 2: Enhanced Security (RSA + AES) ===
python tools/key_manager.py --generate-rsa

# Interactive prompt:
# Protect private key with a PIN/Password? (y/n): y
# Enter Private Key PIN: ****
# Confirm Private Key PIN: ****

# Output:
# ✓ RSA key pair generated:
#   📤 Public key: keys/rsa_public.pem
#   🔐 Private key: keys/rsa_private.pem
#   Fingerprint: AB:CD:EF:12:34...
#   Key size: 2048 bits

# === BACKUP KEYS ===
python tools/key_manager.py --backup

# Output:
# ✓ Key backed up to: keys/backups/master_20240115_143000.key
```

### Key Status Display

```bash
python tools/key_manager.py

# ┌────────────────────────────────────────────────────────┐
# │ ENCRYPTION KEY INFORMATION                             │
# └────────────────────────────────────────────────────────┘
#
#   Status: ✓ ACTIVE
#   Path: keys/master.key
#   Size: 32 bytes (256-bit)
#   SHA-256: a1b2c3d4e5f67890...
#   Created: 2024-01-15 14:30:00
#
#   Backups: 2 found
#     → master_20240115_100000.key
#     → master_20240115_140000.key
#
# ┌────────────────────────────────────────────────────────┐
# │ RSA KEY PAIR INFORMATION (Hybrid Encryption)           │
# └────────────────────────────────────────────────────────┘
#
#   📤 PUBLIC KEY (for encryption):
#      Status: ✓ AVAILABLE
#      Path: keys/rsa_public.pem
#      Fingerprint: AB:CD:EF:12...
#
#   🔐 PRIVATE KEY (for decryption):
#      Status: ✓ AVAILABLE
#      Path: keys/rsa_private.pem
```

---

## 📹 tools/camera_selector.py

### Purpose

Detect, test, dan preview kamera yang tersedia di sistem. Berguna untuk:
- Menemukan webcam yang terhubung
- Testing koneksi RTSP camera
- Preview sebelum konfigurasi

### Usage

```bash
# Interactive mode (default)
python tools/camera_selector.py

# List cameras without interaction
python tools/camera_selector.py --list

# Test specific camera
python tools/camera_selector.py --test 0

# Test RTSP URL
python tools/camera_selector.py --test "rtsp://admin:password@192.168.1.100:554/stream"

# Preview camera for 30 seconds
python tools/camera_selector.py --preview 0 --duration 30
```

### Arguments Reference

| Argument | Default | Description |
|:---------|:--------|:------------|
| `--list` | - | List available cameras |
| `--test` | - | Test camera connection |
| `--preview` | - | Preview camera feed |
| `--duration` | 10 | Preview duration (seconds) |

### Example: Find and Configure Camera

```bash
# 1. Find available cameras
python tools/camera_selector.py

# ══════════════════════════════════════════════════════
#   CAMERA SELECTION
# ══════════════════════════════════════════════════════
#
# Scanning for cameras...
#
# Found 2 camera(s):
#
#   [0] Camera 0
#       Resolution: 1920x1080
#       FPS: 30
#
#   [1] Camera 1
#       Resolution: 640x480
#       FPS: 30
#
#   [r] Enter RTSP URL
#   [q] Quit
#
# Select camera: 0

# 2. Test RTSP connection
python tools/camera_selector.py --test "rtsp://admin:admin123@192.168.1.100:554/stream1"

# ✓ rtsp://...: Connection Successful

# 3. Update .env
# CAMERA_SOURCES=0,rtsp://admin:admin123@192.168.1.100:554/stream1
```

### Troubleshooting Camera Issues

```bash
# Camera not detected
python tools/camera_selector.py --list
# No cameras found!
# → Check USB connection
# → Install camera drivers
# → Try: sudo apt install v4l-utils && v4l2-ctl --list-devices

# RTSP timeout
python tools/camera_selector.py --test "rtsp://..."
# ✗ rtsp://...: Cannot open camera
# → Check IP/port is correct
# → Verify username/password
# → Test with VLC first: vlc rtsp://...
```

---

## 🛡️ tools/verify_integrity.py

### Purpose

Demonstrate tamper detection capability untuk sidang skripsi. Menunjukkan bahwa:
- File evidence tidak bisa dibaca tanpa key
- File evidence tidak bisa dimodifikasi tanpa terdeteksi
- AES-256-GCM memberikan authenticated encryption

### Usage

```bash
# Run full security demo (recommended for sidang)
python tools/verify_integrity.py --demo

# Run file-level integrity test
python tools/verify_integrity.py --test-file

# Verify specific evidence file
python tools/verify_integrity.py --verify recordings/evidence/cam0/evidence_20240115.enc
```

### Arguments Reference

| Argument | Description |
|:---------|:------------|
| `--demo` | Run complete tamper detection demo |
| `--test-file` | Test with actual file I/O |
| `--verify` | Verify specific file integrity |

### Example: Sidang Demo

```bash
python tools/verify_integrity.py --demo

# ══════════════════════════════════════════════════════════
#   TAMPER DETECTION DEMONSTRATION
#   For Thesis Defense (Sidang)
# ══════════════════════════════════════════════════════════
#
# 1. Original Data Size: 6600 bytes
#
# 2. Encrypting evidence...
#    Ciphertext size: 6716 bytes
#    Original hash: a1b2c3d4e5f6...
#
# 3. Verifying normal decryption...
#    ✓ Decryption successful, data matches!
#
# ──────────────────────────────────────────────────────────
#   TAMPERING SIMULATION
# ──────────────────────────────────────────────────────────
#
# 4. Test 1: Modifying 1 byte in ciphertext...
#    ✓ DETECTED! Decryption failed as expected
#
# 5. Test 2: Modifying nonce...
#    ✓ DETECTED! Decryption failed as expected
#
# 6. Test 3: Appending data to ciphertext...
#    ✓ DETECTED! Decryption failed as expected
#
# 7. Test 4: Truncating ciphertext...
#    ✓ DETECTED! Decryption failed as expected
#
# 8. Test 5: Using wrong encryption key...
#    ✓ DETECTED! Wrong key rejected
#
# ══════════════════════════════════════════════════════════
#   SUMMARY
# ══════════════════════════════════════════════════════════
#
#     The AES-256-GCM encryption provides:
#
#     1. CONFIDENTIALITY: Data is encrypted and unreadable without key
#     2. INTEGRITY: Any modification is detected via authentication tag
#     3. AUTHENTICITY: Only the correct key can decrypt
#
#     Answer for thesis defense:
#     "Sistem menggunakan AES-256-GCM yang merupakan Authenticated Encryption.
#      Mode GCM menghasilkan authentication tag yang terverifikasi saat dekripsi.
#      Jika file dimodifikasi walau 1 bit, dekripsi akan gagal."
```

---

## 🖼️ tools/generate_thumbnails.py

### Purpose

Generate thumbnail images untuk video recordings di dashboard web.

### Usage

```bash
python tools/generate_thumbnails.py
```

### Output

```bash
# Scanning recordings/public for missing thumbnails...
# Generating thumbnail for: public_cam0_20240115_143000.mp4
# Generating thumbnail for: public_cam0_20240115_150000.mp4
# Done! Generated 2 new thumbnails.
```

### How It Works

1. Scans `recordings/public/` for `.mp4` files
2. Checks if corresponding `.jpg` thumbnail exists
3. If not, extracts first frame and saves as 320x180 JPEG

---

## 🎬 demo.py

### Purpose

Standalone face detection demo tanpa recording. Berguna untuk:
- Test model detection
- Verify GPU/CUDA setup
- Quick demo tanpa full system

### Usage

```bash
# Run demo with default camera
python demo.py

# With custom camera
python demo.py --source 1

# With RTSP
python demo.py --source "rtsp://..."

# Adjust detection settings
python demo.py --confidence 0.6 --blur 71

# Use CPU instead of GPU
python demo.py --device cpu
```

### Arguments Reference

| Argument | Default | Description |
|:---------|:--------|:------------|
| `--source` | `0` | Camera source (index or URL) |
| `--confidence` | `0.5` | Detection confidence threshold |
| `--blur` | `51` | Blur intensity (odd number) |
| `--device` | `cuda` | Device (cuda/cpu) |

### Example Output

```bash
python demo.py

# ══════════════════════════════════════════════════════════
#   SECURE EDGE VISION - FACE DETECTION DEMO
# ══════════════════════════════════════════════════════════
#
# Loading YOLOv8 face model...
# ✓ Model loaded on CUDA (NVIDIA RTX 3050)
#
# Starting camera 0...
# ✓ Camera opened: 1920x1080 @ 30fps
#
# Press 'Q' to quit
#
# [Shows real-time video with blurred faces]
#
# Detection stats:
#   FPS: 28.5
#   Faces detected: 2
```

---

## 📊 benchmark.py

### Purpose

Performance benchmarking tool untuk mengukur:
- Detection FPS
- Encryption throughput
- Overall system performance

### Usage

```bash
# Run full benchmark
python benchmark.py

# Quick benchmark (100 frames)
python benchmark.py --frames 100

# Benchmark specific component
python benchmark.py --component detection
python benchmark.py --component encryption

# Save results to CSV
python benchmark.py --output results.csv
```

### Arguments Reference

| Argument | Default | Description |
|:---------|:--------|:------------|
| `--frames` | `500` | Number of frames to test |
| `--component` | `all` | Component to benchmark |
| `--output` | - | Save results to CSV |
| `--resolution` | `720p` | Test resolution |

### Example Output

```bash
python benchmark.py

# ══════════════════════════════════════════════════════════
#   SECURE EDGE VISION BENCHMARK
# ══════════════════════════════════════════════════════════
#
# System: NVIDIA RTX 3050, CUDA 11.8
# Resolution: 1280x720
# Frames: 500
#
# ─────────────────────────────────────────────────────────
# DETECTION BENCHMARK
# ─────────────────────────────────────────────────────────
# Avg detection time: 15.2 ms
# Detection FPS: 65.8
# Min/Max: 12.1ms / 23.4ms
#
# ─────────────────────────────────────────────────────────
# ENCRYPTION BENCHMARK
# ─────────────────────────────────────────────────────────
# Avg encryption time: 2.1 ms per frame
# Throughput: 476 frames/sec
# Size ratio: 1.02x (after JPEG compression)
#
# ─────────────────────────────────────────────────────────
# OVERALL SYSTEM
# ─────────────────────────────────────────────────────────
# Total processing: 18.5 ms/frame
# Achievable FPS: 54.0
# Bottleneck: Detection
#
# ✓ Results saved to recordings/benchmark_20240115_143000.csv
```

---

## ⚙️ config.py (CLI)

### Purpose

Configuration validation dan system information display.

### Usage

```bash
# Show all info (default)
python config.py

# Validate configuration
python config.py --validate

# Show system info
python config.py --info

# Create default .env file
python config.py --create-env

# Print .env template
python config.py --template
```

### Arguments Reference

| Argument | Short | Description |
|:---------|:------|:------------|
| `--validate` | `-v` | Validate configuration |
| `--info` | `-i` | Show system information |
| `--create-env` | - | Create default .env file |
| `--template` | `-t` | Print .env template |

### Example: System Validation

```bash
python config.py --validate

# ══════════════════════════════════════════════════════
#   CONFIGURATION VALIDATION
# ══════════════════════════════════════════════════════
#
# Camera: 0
# Device: cuda
# Port: 8000
# Blur: 51
# FPS: 30
#
# ⚠️  Warnings (1):
#    • BLUR_INTENSITY should be odd, will use 51
#
# ✓ Configuration valid!
```

### Example: System Info

```bash
python config.py --info

# ══════════════════════════════════════════════════════
#   SYSTEM INFORMATION
# ══════════════════════════════════════════════════════
#
# Python: 3.10.12
# OpenCV: 4.8.1
# PyTorch: 2.1.0
# CUDA Available: True
# GPU: NVIDIA GeForce RTX 3050
# CUDA Version: 11.8
# Ultralytics: 8.0.200
# FastAPI: 0.104.1
# Cryptography: 41.0.5
```

---

## 📚 Workflow Examples

### Workflow 1: Initial Setup

```bash
# 1. Check system requirements
python config.py --info

# 2. Create configuration
python config.py --create-env

# 3. Generate encryption keys
python tools/key_manager.py --generate
python tools/key_manager.py --generate-rsa

# 4. Test camera
python tools/camera_selector.py --test 0

# 5. Run demo to verify detection
python demo.py

# 6. Start full system
python main.py
```

### Workflow 2: Forensic Investigation

```bash
# 1. List evidence files
python tools/decryptor.py --list

# 2. Verify file integrity
python tools/verify_integrity.py --verify recordings/evidence/cam0/evidence_20240115.enc

# 3. Decrypt and review
python tools/decryptor.py -f evidence_20240115.enc

# 4. Export for legal use
python tools/decryptor.py -f evidence_20240115.enc --export court_exhibit_001.mp4 --no-boxes
```

### Workflow 3: Thesis Defense Demo

```bash
# 1. Show security capabilities
python tools/verify_integrity.py --demo

# 2. Show face detection
python demo.py

# 3. Show evidence decryption
python tools/decryptor.py --list
python tools/decryptor.py -f [select_file]

# 4. Show performance metrics
python benchmark.py
```

---

## ➡️ Navigasi Wiki

| Sebelumnya | Selanjutnya |
|:-----------|:------------|
| [API](API.md) | [Performance](Performance.md) |
