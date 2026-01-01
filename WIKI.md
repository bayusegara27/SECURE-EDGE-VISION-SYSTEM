# SECURE EDGE VISION SYSTEM - Wiki Documentation

![Version](https://img.shields.io/badge/version-1.3.0-blue) ![Python](https://img.shields.io/badge/python-3.11+-green) ![License](https://img.shields.io/badge/license-MIT-yellow)

**Advanced AI-powered surveillance system with end-to-end encryption for evidence protection**

---

## 📚 Daftar Isi

### Memulai
- [Gambaran Sistem](#gambaran-sistem)
- [Panduan Cepat](#panduan-cepat)
- [Instalasi](#instalasi)
- [Konfigurasi](#konfigurasi)

### Konsep Inti
- [Arsitektur Sistem](#arsitektur-sistem)
- [Dual-Path Processing](#dual-path-processing)
- [Keamanan & Enkripsi](#keamanan--enkripsi)
- [Manajemen Storage](#manajemen-storage)

### Dokumentasi Teknis
- [Referensi Modul](#referensi-modul)
- [API Endpoints](#api-endpoints)
- [Optimasi Performa](#optimasi-performa)
- [Troubleshooting](#troubleshooting)

### Topik Lanjutan
- [Panduan Development](#panduan-development)
- [Testing](#testing)
- [Deployment](#deployment)
- [FAQ](#faq)

---

## Gambaran Sistem

### Apa itu SECURE EDGE VISION SYSTEM?

SECURE EDGE VISION SYSTEM adalah sistem surveillance cerdas yang dirancang untuk **skripsi S1** dengan fokus pada:

1. **Privacy Protection** - Anonimisasi wajah real-time menggunakan AI
2. **Forensic Evidence** - Penyimpanan terenkripsi untuk investigasi hukum
3. **Edge Computing** - Pemrosesan lokal di laptop gaming (RTX 3050)
4. **Multi-Camera Support** - Hingga 3 kamera simultan (webcam + RTSP)

### Fitur Utama

#### 🤖 AI Detection
- **YOLOv8-Face** - Model khusus deteksi wajah dari WIDER Face dataset
- **GPU Accelerated** - CUDA support untuk RTX 3050 (25-30 FPS)
- **Real-time Processing** - Latency < 500ms dari capture ke display

#### 🔒 Security
- **AES-256-GCM** - Military-grade authenticated encryption
- **SHA-256 Hashing** - Double integrity protection
- **PIN Protection** - Secure access to decryption tools
- **Tamper Detection** - Cryptographic proof of evidence integrity

#### 📊 Analytics
- **Real-time Metrics** - Events, peak hours, activity trends
- **Storage Health** - Multi-drive analysis with forecasting
- **Interactive Charts** - Chart.js visualizations
- **Search & Filter** - Quick evidence lookup

#### 💾 Storage
- **Dual Recording** - Public (blurred MP4) + Evidence (encrypted .enc)
- **Auto Rotation** - 5-minute segments for easy management
- **FIFO Cleanup** - Automatic deletion when storage limit reached
- **Selective Recording** - Only save evidence when face detected (80% storage saving)

---

## Panduan Cepat

### Persyaratan Sistem

```bash
# System Requirements
- Windows 10/11
- Python 3.11+
- 16GB RAM (minimum 8GB)
- NVIDIA GPU with CUDA (optional but recommended)
- 50GB+ free storage
```

### Instalasi (5 Menit)

```bash
# 1. Clone repository
git clone http://192.168.0.135:3000/nakumi/SECURE-EDGE-VISION-SYSTEM.git
cd SECURE-EDGE-VISION-SYSTEM

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run setup (generates keys, downloads models)
python setup.py

# 5. Configure cameras
notepad .env
# Edit CAMERA_SOURCES=0,1,rtsp://your-camera-ip:port

# 6. Start system
python main.py
```

### First Run

1. Open browser: `http://localhost:8000`
2. You'll see live view from all cameras
3. Faces are automatically blurred
4. Recordings saved to `recordings/public/` (MP4)
5. Evidence saved to `recordings/evidence/` (encrypted .enc)

---

## Arsitektur Sistem

### Diagram Arsitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Webcam 0  │  Webcam 1  │  RTSP Camera                          │
└──────┬───────────┬────────────┬─────────────────────────────────┘
       │           │            │
       ▼           ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│              EDGE SERVER (Laptop RTX 3050)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │         Camera Threads (Parallel Processing)         │      │
│  │  Thread 0  │  Thread 1  │  Thread 2                  │      │
│  └────────┬─────────┬──────────┬─────────────────────────┘      │
│           │         │          │                                │
│           └─────────┴──────────┘                                │
│                     │                                           │
│           ┌─────────▼──────────┐                                │
│           │   AI Engine (CUDA) │                                │
│           │   YOLOv8-Face      │                                │
│           │   GPU Accelerated  │                                │
│           └─────────┬──────────┘                                │
│                     │                                           │
│           ┌─────────┴──────────┐                                │
│           │  Dual-Path Split   │                                │
│           └─────┬──────────┬───┘                                │
│                 │          │                                    │
│        ┌────────▼──┐  ┌────▼────────┐                          │
│        │ Gaussian  │  │ AES-256-GCM │                          │
│        │   Blur    │  │ Encryption  │                          │
│        │ 51x51     │  │             │                          │
│        └────┬──────┘  └────┬────────┘                          │
│             │              │                                    │
│        ┌────▼──────┐  ┌────▼────────┐                          │
│        │ Public    │  │  Evidence   │                          │
│        │ MP4       │  │  .enc       │                          │
│        │ H.264     │  │  Encrypted  │                          │
│        └────┬──────┘  └────┬────────┘                          │
│             │              │                                    │
└─────────────┼──────────────┼─────────────────────────────────────┘
              │              │
              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       OUTPUT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Web Dashboard  │  Analytics  │  Decryption Tool                │
│  FastAPI+MJPEG  │  Chart.js   │  Admin Only                     │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.12 | AI/ML ecosystem |
| **AI Core** | PyTorch + Ultralytics YOLOv8 | Face detection |
| **Parallelism** | threading.Thread | Multi-camera processing |
| **Async I/O** | queue.Queue + Background Worker | Non-blocking evidence flush |
| **Web Framework** | FastAPI + Uvicorn | Modern async API |
| **Streaming** | MJPEG over HTTP | Browser-native video |
| **Security** | cryptography (AES-GCM) | NIST-approved encryption |
| **Video Codec** | OpenCV + H.264 (avc1) | Web-compatible compression |
| **Frontend** | Vanilla JS + Chart.js | Lightweight, no build step |

---

## Dual-Path Processing

### Konsep Fundamental

Sistem membagi aliran data menjadi **dua jalur independen**:

#### 1. Jalur Publik (Public Stream)
**Tujuan:** Monitoring harian satpam & replay kejadian biasa

```
Frame → YOLOv8 Detection → Gaussian Blur → MP4 Recording → Web Stream
```

**Karakteristik:**
- ✅ Wajah di-blur dengan Gaussian kernel 51x51
- ✅ Tidak dapat di-reverse (irreversible)
- ✅ Akses terbuka untuk staf umum
- ✅ Format: MP4 (H.264 codec)
- ✅ Segmentasi: 5 menit per file

#### 2. Jalur Forensik (Evidence Path)
**Tujuan:** Investigasi kriminal (Polisi/Manajer)

```
Frame → AES-256-GCM Encryption → .enc File → Secure Storage
```

**Karakteristik:**
- 🔒 Terenkripsi dengan AES-256-GCM
- 🔒 SHA-256 hash untuk integrity check
- 🔒 Butuh private key untuk dekripsi
- 🔒 Format: Custom .enc binary
- 🔒 Selective recording (hanya saat ada deteksi)

### Perbandingan Pendekatan

| Aspek | Single Path | Dual-Path (Kami) |
|-------|------------|------------------|
| **Privacy** | Harus pilih: blur ATAU raw | Blur untuk publik, raw terenkripsi |
| **Forensik** | Blur tidak bisa di-reverse | Raw tersimpan aman |
| **Storage** | Boros (semua raw) | Efisien (selective evidence) |
| **Compliance** | Sulit balance privacy vs law | Memenuhi kedua requirement |

---

## Keamanan & Enkripsi

### Alur Enkripsi

```
┌──────────────────────────────────────────────────────────────┐
│                    ENCRYPTION FLOW                           │
└──────────────────────────────────────────────────────────────┘

1. Camera Capture Frame
   ↓
2. YOLOv8 Face Detection
   ↓
3. Dual Path Split
   ├─→ [PUBLIC PATH]
   │   ├─→ Gaussian Blur (51x51)
   │   └─→ Save to MP4 (H.264)
   │
   └─→ [EVIDENCE PATH]
       ├─→ Buffer Frames (6000 frames or 5 min)
       ├─→ Serialize (pickle.dumps)
       ├─→ Compute SHA-256 Hash
       ├─→ Create Payload (hash + '::' + data)
       ├─→ Generate Nonce (12 random bytes)
       ├─→ AES-256-GCM Encrypt
       ├─→ Create Package (nonce + ciphertext + metadata)
       └─→ Save to .enc file
```

### Security Layers

1. **AES-256 Encryption** - Confidentiality (2^256 possible keys)
2. **GCM Auth Tag** - Integrity (16-byte authentication)
3. **SHA-256 Hash** - Double integrity (embedded in ciphertext)
4. **Nonce Uniqueness** - Replay protection (12 random bytes)

### Format File .enc

```
┌──────────────────────────────────────────────────────┐
│                  .enc File Structure                 │
├──────────────────────────────────────────────────────┤
│  [Nonce]                    12 bytes                 │
│  [Timestamp]                 8 bytes (double)        │
│  [Metadata Length]           4 bytes (uint32)        │
│  [Metadata JSON]             Variable (e.g., 200B)   │
│  [Ciphertext + Auth Tag]     ~500 MB + 16 bytes      │
└──────────────────────────────────────────────────────┘
```

### Proses Dekripsi

```
1. Load .enc File
   ↓
2. Read File Structure
   ├─→ Extract Nonce (12 bytes)
   ├─→ Extract Timestamp (8 bytes)
   ├─→ Extract Metadata (variable)
   └─→ Extract Ciphertext (rest)
   ↓
3. AES-256-GCM Decrypt
   ↓
4. Verify Auth Tag
   ├─→ [INVALID] → REJECT (File Tampered!)
   └─→ [VALID] → Continue
   ↓
5. Split Payload (hash + '::' + data)
   ↓
6. Compute SHA-256 of decrypted data
   ↓
7. Compare Hashes
   ├─→ [MISMATCH] → REJECT (Integrity Failed!)
   └─→ [MATCH] → Continue
   ↓
8. Unpickle Data
   ↓
9. Restore Frames (numpy arrays + metadata)
   ↓
10. ✅ Evidence Verified
```

---

## Referensi Modul

### 1. `modules/engine.py` - System Orchestrator

**Class:** `EdgeVisionSystem`

**Purpose:** Koordinasi semua komponen untuk multi-camera processing

**Key Methods:**
```python
def start(self) -> None:
    """Initialize core components and metadata"""
    
def process_frame(self, camera_idx: int) -> bool:
    """Capture and process one frame for specific camera"""
    
def get_frame(self, camera_idx: int) -> Optional[np.ndarray]:
    """Get latest frame for streaming"""
    
def stop(self) -> None:
    """Stop all components"""
```

**Thread Architecture:**
- 1 thread per camera (parallel processing)
- Independent frame locks (no race condition)
- Synchronized timestamp untuk matching public-evidence

---

### 2. `modules/processor.py` - AI Detection

**Class:** `FrameProcessor`

**Purpose:** YOLOv8-Face detection dan Gaussian blur

**Key Methods:**
```python
def process(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[dict]]:
    """
    Process frame: detect faces and apply blur
    
    Returns:
        (blurred_frame, raw_frame, detections_list)
    """
```

**Detection Output:**
```python
{
    "x1": int,  # Bounding box top-left X
    "y1": int,  # Bounding box top-left Y
    "x2": int,  # Bounding box bottom-right X
    "y2": int,  # Bounding box bottom-right Y
    "class": "face",
    "confidence": 0.95,
    "timestamp": 1735729200.123
}
```

**Blur Algorithm:**
- Gaussian kernel: 51x51 pixels
- Padding: 15% untuk coverage lebih baik
- Irreversible: Tidak bisa di-reverse dengan AI

---

### 3. `modules/recorder.py` - Public MP4 Recording

**Class:** `VideoRecorder`

**Purpose:** Rekam video blur ke MP4 dengan auto-rotation

**Key Features:**
- Auto-rotation setiap 5 menit
- Codec priority: avc1 (H.264) → X264 → mp4v → MJPG
- Metadata JSON untuk setiap file (frame count, detections)

**File Naming:**
```
recording_cam0_20260101_210000.mp4
recording_cam0_20260101_210000.json  # Metadata
```

---

### 4. `modules/evidence.py` - Encrypted Evidence

**Class:** `EvidenceManager`

**Purpose:** Buffer frames dan save ke encrypted .enc files

**Key Features:**
- **Selective Recording** - Hanya rekam saat ada deteksi wajah
- **Pre-roll Buffer** - 30 frames (~1 detik) sebelum deteksi untuk konteks
- **Background Flush** - Non-blocking encryption di thread terpisah
- **JPEG Compression** - Quality 75 untuk balance forensik vs size

**Storage Savings:**
```
Tanpa selective: 15 GB/jam (semua frame)
Dengan selective: ~3 GB/jam (hanya deteksi)
Penghematan: 80%
```

---

### 5. `modules/security.py` - Encryption Vault

**Class:** `SecureVault`

**Purpose:** AES-256-GCM encryption dengan SHA-256 integrity

**Key Methods:**
```python
def lock_evidence(self, raw_bytes: bytes, metadata: dict) -> EncryptedPackage:
    """Encrypt evidence with integrity protection"""
    
def unlock_evidence(self, package: EncryptedPackage) -> Tuple[bytes, str]:
    """Decrypt and verify evidence integrity"""
    
def save_encrypted_file(self, data: bytes, output_path: str, metadata: dict):
    """Encrypt and save data to file"""
    
def load_encrypted_file(self, input_path: str) -> Tuple[bytes, dict]:
    """Load and decrypt file"""
```

**Security Guarantees:**
- ✅ Confidentiality (AES-256)
- ✅ Integrity (GCM auth tag + SHA-256)
- ✅ Authenticity (GCM proves origin)

---

### 6. `modules/storage.py` - Storage Management

**Functions:**

```python
def cleanup_storage(public_path: str, evidence_path: str, max_gb: int):
    """
    Enforce storage retention policy (FIFO)
    Deletes oldest files if total usage exceeds max_gb
    """
```

**Cleanup Strategy:**
- Monitor total storage usage
- Delete oldest files first (FIFO)
- Triggered setiap analytics request
- Configurable via `MAX_STORAGE_GB` in .env

---

## API Endpoints

### GET `/api/status`

**Response:**
```json
{
  "running": true,
  "cameras": [
    {
      "index": 0,
      "source": "0",
      "name": "Webcam 0",
      "active": true,
      "fps": 28.5,
      "detections": 2
    }
  ],
  "processor": {
    "model": "models/model.pt",
    "device": "cuda",
    "is_loaded": true
  }
}
```

---

### GET `/api/analytics`

**Response:**
```json
{
  "summary": {
    "events_today": 1234,
    "peak_hour": "14:00",
    "avg_per_hour": 51.4
  },
  "storage": {
    "drives": [
      {
        "drive": "H:",
        "total_gb": 931.5,
        "used_gb": 45.2,
        "free_gb": 886.3,
        "percent": 4.9
      }
    ],
    "forecast": {
      "days_remaining": 45.2,
      "estimated_full_date": "2026-02-15"
    }
  },
  "hourly_activity": [
    {"hour": "00:00", "count": 12},
    {"hour": "01:00", "count": 8}
  ],
  "camera_activity": [
    {"camera": "Webcam 0", "count": 456},
    {"camera": "Webcam 1", "count": 389}
  ]
}
```

---

### POST `/api/decrypt`

**Request:**
```json
{
  "filename": "evidence_cam0_20260101_210000_0000.enc",
  "pin": "your-secure-pin",
  "show_boxes": true
}
```

**Response (Success):**
```json
{
  "status": "success",
  "video_id": "abc123def456",
  "video_url": "/api/decrypted/abc123def456",
  "metadata": {
    "frame_count": 6000,
    "start_time": 1735729200.0,
    "end_time": 1735729500.0,
    "total_detections": 1234
  }
}
```

---

## Konfigurasi

### Environment Variables (.env)

```env
# ============ Camera Settings ============
CAMERA_SOURCES=0,1,rtsp://192.168.0.144:1935
# Comma-separated: webcam index or RTSP URL

# ============ AI/Detection Settings ============
MODEL_PATH=models/yolov8n.pt
DETECTION_CONFIDENCE=0.5
DEVICE=cuda  # or 'cpu'
BLUR_INTENSITY=51  # Must be odd number

# ============ Server Settings ============
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# ============ Recording Settings ============
RECORDING_DURATION_SECONDS=300  # 5 minutes
TARGET_FPS=24

# ============ Storage Paths ============
PUBLIC_RECORDINGS_PATH=H:\SkripsiRecord\public
EVIDENCE_RECORDINGS_PATH=H:\SkripsiRecord\evidence

# ============ Security Settings ============
ENCRYPTION_KEY_PATH=keys/master.key
RSA_PUBLIC_KEY_PATH=keys/rsa_public.pem
RSA_PRIVATE_KEY_PATH=keys/rsa_private.pem

# ============ Storage Optimization ============
EVIDENCE_DETECTION_ONLY=True  # Only record when face detected
EVIDENCE_JPEG_QUALITY=75  # 1-100

# ============ Retention Policy ============
MAX_STORAGE_GB=100  # Auto-delete oldest files if exceeded
```

---

## Optimasi Performa

### GPU Acceleration

**Setup CUDA:**
```bash
# 1. Check CUDA version
nvidia-smi

# 2. Install PyTorch with CUDA
pip uninstall torch torchvision -y
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 3. Verify
python -c "import torch; print(torch.cuda.is_available())"
```

**Performance Metrics:**

| Mode | FPS | Latency | Memory |
|------|-----|---------|--------|
| CPU  | 5-10 | 150-200ms | 2GB RAM |
| CUDA | 25-30 | 30-50ms | 2GB VRAM |

---

### Storage Optimization

**Selective Recording:**
```python
# .env
EVIDENCE_DETECTION_ONLY=True
```

**Impact:**
- Tanpa: 15 GB/jam (semua frame)
- Dengan: ~3 GB/jam (hanya deteksi)
- **Penghematan: 80%**

**JPEG Quality:**
```python
# .env
EVIDENCE_JPEG_QUALITY=75  # Balance forensik vs size
```

| Quality | File Size | Forensik |
|---------|-----------|----------|
| 95 | 100% | Excellent |
| 75 | 40% | Good |
| 50 | 20% | Fair |

---

## Troubleshooting

### Issue: CUDA: False

**Diagnosis:**
```bash
python -c "import torch; print(torch.cuda.is_available())"
# Output: False
```

**Solution:**
```bash
# 1. Check NVIDIA driver
nvidia-smi

# 2. Reinstall PyTorch with CUDA
.venv\Scripts\pip.exe uninstall torch torchvision -y
.venv\Scripts\pip.exe install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 3. Verify
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

---

### Issue: Video tidak play di browser

**Diagnosis:**
```
File: recording_cam0_20260101_210000.avi
Codec: XVID atau MJPG
```

**Solution:**
```bash
# Install OpenH264 codec
python setup.py

# Or manual download:
# https://github.com/cisco/openh264/releases/download/v1.8.0/openh264-1.8.0-win64.dll
# Copy to: venv\Lib\site-packages\cv2\
```

---

### Issue: Decryption failed

**Diagnosis:**
```
Error: INTEGRITY CHECK FAILED - Evidence tampered!
```

**Possible Causes:**
1. File corrupted (disk error)
2. Wrong encryption key
3. File modified (tampered)

**Solution:**
```bash
# 1. Verify key
python tools/key_manager.py --verify

# 2. Check file integrity
python tools/verify_integrity.py evidence_file.enc

# 3. Restore from backup (if available)
cp keys/backups/master_20251231_191158.key keys/master.key
```

---

## Panduan Development

### Struktur Project

```
ProjectSkripsi/
├── main.py                    # FastAPI server & orchestrator
├── config.py                  # Configuration utility
├── requirements.txt           # Dependencies
├── .env                       # Environment variables
├── modules/
│   ├── __init__.py
│   ├── camera.py              # RTSP/Webcam capture
│   ├── processor.py           # YOLOv8-Face detection & blur
│   ├── engine.py              # Multi-camera processing engine
│   ├── recorder.py            # Public MP4 recording
│   ├── evidence.py            # Encrypted evidence manager
│   ├── security.py            # AES-GCM + SHA-256 crypto
│   ├── rsa_crypto.py          # RSA hybrid encryption
│   └── storage.py             # Storage utilities & cleanup
├── models/
│   └── model.pt               # YOLOv8-Face model
├── recordings/
│   ├── public/                # MP4 files (blurred)
│   └── evidence/              # .enc files (encrypted)
├── keys/
│   └── master.key             # AES-256 encryption key
├── templates/
│   ├── index.html             # Live dashboard
│   ├── gallery.html           # Replay interface
│   ├── analytics.html         # Analytics dashboard
│   └── decrypt.html           # Evidence decryption
├── static/
│   ├── css/shared.css
│   └── js/...
├── tools/
│   ├── decryptor.py           # CLI decryption tool
│   ├── key_manager.py         # Key generation utility
│   └── verify_integrity.py   # Hash verification
└── tests/
    ├── test_security.py
    ├── test_detection.py
    └── test_storage.py
```

---

### Menambah Camera Source Baru

**1. Edit .env:**
```env
CAMERA_SOURCES=0,1,rtsp://192.168.0.144:1935,rtsp://new-camera:554/stream
```

**2. Restart system:**
```bash
# Stop: Ctrl+C
python main.py
```

**3. Verify in dashboard:**
- Open `http://localhost:8000`
- Check "Camera 3" appears in grid

---

## Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_security.py

# Run with coverage
pytest --cov=modules tests/
```

---

### Integration Tests

```bash
# Test camera capture
python -c "from modules.camera import CameraIngester; c = CameraIngester(0); c.start()"

# Test detection
python demo.py --quick

# Test encryption
python tools/key_manager.py --test
```

---

### Performance Benchmarking

```bash
# Run benchmark
python benchmark.py

# Output:
# ========================================
# BENCHMARK RESULTS
# ========================================
# Camera FPS: 28.5
# Detection FPS: 27.2
# Encryption Time: 2.3s per 6000 frames
# Storage Rate: 3.2 GB/hour
# ========================================
```

---

## Deployment

### Production Checklist

- [ ] Backup encryption key (`keys/master.key`)
- [ ] Configure storage paths (external drive recommended)
- [ ] Set `MAX_STORAGE_GB` appropriate for your disk
- [ ] Test all cameras before deployment
- [ ] Create admin PIN for decryption
- [ ] Document camera locations
- [ ] Setup monitoring (disk space, system health)
- [ ] Test disaster recovery (restore from backup)

---

### Windows Service (NSSM)

```bash
# 1. Download NSSM
# https://nssm.cc/download

# 2. Install service
nssm install SecureEdge "C:\Path\To\.venv\Scripts\python.exe" "C:\Path\To\main.py"

# 3. Configure
nssm set SecureEdge AppDirectory "C:\Path\To\ProjectSkripsi"
nssm set SecureEdge Start SERVICE_AUTO_START

# 4. Start
nssm start SecureEdge
```

---

## FAQ

### Q: Apakah video blur bisa di-reverse?

**A:** **TIDAK BISA**. Gaussian blur menghancurkan pixel wajah dan menggantinya dengan rata-rata tetangga. Tidak ada AI yang bisa mengembalikan wajah asli dengan akurat 100% (itu hanya halusinasi AI/DeepFake). Makanya kita butuh sistem **Dual-Path Storage** yang menyimpan file asli secara terenkripsi.

---

### Q: Bagaimana membuktikan video bukti tidak diedit?

**A:** Sistem menggunakan **Authenticated Encryption (AES-GCM)** dengan **SHA-256 hash**:

1. Sebelum enkripsi, sistem menghitung hash SHA-256 dari frame asli
2. Hash ini ikut dikunci di dalam file encrypted
3. Saat dekripsi, hash dihitung ulang dan dibandingkan
4. Jika admin edit video lalu encrypt ulang, hash tidak akan cocok
5. AES-GCM auth tag juga akan gagal validasi

Ini adalah **cryptographic proof** yang tidak bisa dipalsukan tanpa private key.

---

### Q: Kenapa pakai Laptop Gaming? Kenapa bukan Raspberry Pi?

**A:** Untuk skenario Edge AI modern yang menangani **multiple streams** dengan algoritma enkripsi real-time AES-256, Raspberry Pi tidak memiliki throughput yang cukup. Laptop ini merepresentasikan **Industrial Edge Server** (seperti NVIDIA Jetson Orin) yang umum dipakai di Smart City. RTX 3050 memberikan 25-30 FPS untuk 3 kamera simultan, yang tidak mungkin dicapai Raspberry Pi.

---

### Q: Apa batasan (Limitation) sistem?

**A:** Sistem bergantung pada **Line of Sight**. Jika wajah tertutup masker full-face, helm, atau menghadap belakang, YOLOv8 tidak mendeteksi wajah, sehingga:
- Tidak ada blurring (tapi juga tidak ada identitas terlihat)
- Tidak ada evidence recording (karena selective mode)

Ini adalah batasan umum **Computer Vision**, bukan bug sistem. Untuk mengatasi, bisa:
- Tambah model person detection (blur seluruh tubuh)
- Tambah kamera dari sudut berbeda
- Kombinasi dengan sensor lain (thermal, LiDAR)

---

## Referensi Tambahan

### Dokumentasi Lengkap
- [MASTERPLAN.md](MASTERPLAN.md) - Complete thesis guide
- [ENCRYPTION_FLOW.md](ENCRYPTION_FLOW.md) - Detailed encryption analysis
- [CUDA_SETUP.md](CUDA_SETUP.md) - GPU setup guide
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [VERSION.txt](VERSION.txt) - Current version info

### Tools
- [tools/decryptor.py](tools/decryptor.py) - CLI decryption tool
- [tools/key_manager.py](tools/key_manager.py) - Key management
- [tools/verify_integrity.py](tools/verify_integrity.py) - Integrity checker

---

## License

This project is developed as part of an undergraduate thesis (Skripsi).

**For Academic Use Only**

---

## Contact

- Repository: http://192.168.0.135:3000/nakumi/SECURE-EDGE-VISION-SYSTEM
- Author: Nakumi
- Year: 2025-2026

---

**⭐ Last Updated: January 1, 2026 | Version 1.3.0**
