# 🔒 Secure Edge Vision System

> **Sistem Anonimisasi Video Real-Time dengan Arsitektur Dual-Path**  
> Menggunakan YOLO + GPU Acceleration untuk deteksi wajah dan Gaussian Blur

---

## 📋 Tentang Project

Sistem CCTV pintar yang melindungi privasi dengan:
- **Path Publik**: Wajah otomatis di-blur → Aman untuk monitoring harian
- **Path Forensik**: Video asli dienkripsi AES-256 → Hanya untuk investigasi

```
Camera → YOLO Detection → [Blur] → Web Dashboard + MP4
                       ↓
                    [Raw] → Encrypt AES-256 → .enc File
```

---

## 🚀 Quick Start (5 Menit)

### 1️⃣ Clone & Setup Virtual Environment

```bash
cd E:\Kuliah\ProjectSkripsi

# Buat virtual environment
python -m venv venv

# Aktifkan venv (WAJIB setiap buka terminal baru!)
# Windows:
.\venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

### 2️⃣ Install Dependencies

```bash
# Install semua package
pip install -r requirements.txt
```

### 3️⃣ Setup CUDA (Untuk GPU - SANGAT DISARANKAN)

> ⚠️ **PENTING**: Tanpa CUDA, sistem akan lambat (5-10 FPS). Dengan CUDA bisa 25-30 FPS!

Lihat panduan lengkap di **[CUDA_SETUP.md](CUDA_SETUP.md)** atau jalankan:

```bash
# Windows - jalankan script otomatis
.\fix_cuda.bat

# Atau manual:
pip uninstall torch torchvision -y
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 4️⃣ Test Sistem

```bash
# Test semua komponen
python demo.py --quick

# Test dengan video live (tekan Q untuk stop)
python demo.py
```

### 5️⃣ Jalankan Sistem

```bash
python main.py
```

Buka browser: **http://localhost:8000**

---

## 📁 Struktur Project

```
ProjectSkripsi/
├── main.py              # Entry point utama (Web + Processing)
├── demo.py              # Test komponen + live preview
├── benchmark.py         # Ukur performa (untuk BAB 5)
│
├── modules/             # Core modules (terpisah & modular)
│   ├── processor.py     # YOLO detection + Gaussian blur
│   ├── recorder.py      # Video recording ke MP4
│   ├── evidence.py      # Encrypted evidence storage
│   ├── security.py      # AES-256-GCM encryption
│   └── camera.py        # Camera capture
│
├── templates/           # HTML untuk web dashboard
├── tools/
│   ├── key_manager.py   # Kelola encryption key
│   ├── decryptor.py     # Decrypt file evidence
│   ├── camera_selector.py  # Pilih kamera
│   └── verify_integrity.py # Demo tamper detection
│
├── recordings/
│   ├── public/          # Video blur (.mp4)
│   └── evidence/        # Video encrypted (.enc)
│
├── keys/                # Encryption keys (BACKUP INI!)
├── venv/                # Virtual environment
│
├── .env                 # Konfigurasi
├── requirements.txt     # Dependencies
├── CUDA_SETUP.md        # Panduan install CUDA
└── README.md            # File ini
```

---

## ⚙️ Konfigurasi (.env)

```env
# Multi-camera sources (comma-separated: 0, 1, rtsp://...)
CAMERA_SOURCES=0,1,rtsp://192.XXX.XXX.XXX:PORT

# Device (cuda untuk GPU, cpu untuk CPU only)
DEVICE=cuda

# Intensitas blur (angka ganjil, makin tinggi makin blur)
BLUR_INTENSITY=51

# Port web server
SERVER_PORT=8000
```

---

## 🎮 Cara Penggunaan

### Monitoring Harian (Satpam)
1. Buka `http://localhost:8000`
2. Lihat live stream (wajah otomatis blur)
3. Klik recordings untuk playback

### Investigasi Forensik (Manager/Polisi)
```bash
# List file evidence
python tools/decryptor.py --list

# Decrypt dan play
python tools/decryptor.py -f evidence_xxx.enc

# Export ke MP4
python tools/decryptor.py -f evidence.enc --export output.mp4
```

### Pilih Kamera
```bash
# List kamera tersedia
python demo.py --cameras

# Gunakan kamera tertentu
python demo.py --camera 1

# Atau edit .env
CAMERA_SOURCES=0,1,rtsp://...
```

---

## 📊 Benchmark (Untuk BAB 5 Skripsi)

```bash
# Jalankan benchmark 60 detik
python benchmark.py --duration 60

# Output: latency, FPS, GPU usage → disimpan ke CSV
```

---

## 🔒 Fitur Keamanan

| Fitur | Deskripsi |
|-------|-----------|
| **AES-256-GCM** | Military-grade encryption |
| **SHA-256 Hash** | Integrity verification |
| **Tamper Detection** | Jika file diubah → decrypt gagal |

Demo tamper detection:
```bash
python tools/verify_integrity.py
```

---

## ⚠️ Catatan Penting

1. **BACKUP `keys/master.key`** - Tanpa file ini, evidence tidak bisa didecrypt!
2. **Aktifkan venv** setiap buka terminal baru: `.\venv\Scripts\activate`
3. **Blur tidak bisa di-reverse** - Itu sebabnya kita simpan evidence terenkripsi

---

## 🔑 Key Management

### First-Time Setup
```bash
python setup.py
```
Script ini akan:
- Generate encryption key baru
- Buat backup otomatis
- Download face detection model

### Backup Key (WAJIB!)
```bash
python tools/key_manager.py --backup
```
Output: `keys/backups/master_YYYYMMDD_HHMMSS.key`

### Restore Key
```bash
python tools/key_manager.py --restore keys/backups/master_xxx.key
```

### Lihat Info Key
```bash
python tools/key_manager.py
```

---

## ❓ Troubleshooting

### CUDA Not Available
```bash
# 1. Cek nvidia driver
nvidia-smi

# 2. Reinstall PyTorch dengan CUDA
pip uninstall torch torchvision -y
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 3. Verifikasi
python -c "import torch; print(torch.cuda.is_available())"
```

### Camera Not Found

```bash
python demo.py --cameras  # List kamera
```

### RTSP Not Working

1.  **Cek Port**: Pastikan port di `.env` sama dengan port yang bisa dibuka di VLC (Contoh: 1935 vs 1395).
2.  **Koneksi Jaringan**: Pastikan IP kamera bisa di-ping dari PC ini.
3.  **Transport Protocol**: Sistem dipaksa menggunakan **RTSP over TCP** untuk stabilitas. Pastikan kamera mendukung mode TCP.

### ModuleNotFoundError
```bash
pip install -r requirements.txt
```

---

## 📝 License

Academic Use Only - Skripsi Project © 2024
