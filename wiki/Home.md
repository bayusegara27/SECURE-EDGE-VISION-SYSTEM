# 🛡️ SECURE EDGE VISION SYSTEM - Wiki Documentation

<div align="center">
  
![Version](https://img.shields.io/badge/version-1.3.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.12+-green?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)
![CUDA](https://img.shields.io/badge/cuda-enabled-emerald?style=for-the-badge)

**Intelligent Surveillance System with Dual-Path Encryption**

*Dokumentasi Teknis untuk Kebutuhan Skripsi Sarjana*

</div>

---

## 📋 Daftar Isi Wiki

| No | Halaman | Deskripsi |
|:---:|:---|:---|
| 1 | **[Home](Home.md)** | Halaman utama dan gambaran umum sistem |
| 2 | **[QuickStart](QuickStart.md)** | 🚀 Panduan cepat memulai dalam 5 menit |
| 3 | **[Architecture](Architecture.md)** | Arsitektur sistem, komponen, dan alur data |
| 4 | **[Security](Security.md)** | Spesifikasi enkripsi dan keamanan data |
| 5 | **[DualPath](DualPath.md)** | Mekanisme Dual-Path (Public vs Evidence) |
| 6 | **[Installation](Installation.md)** | Panduan instalasi dan konfigurasi |
| 7 | **[Modules](Modules.md)** | Dokumentasi modul-modul Python |
| 8 | **[API](API.md)** | Dokumentasi API endpoints |
| 9 | **[Tools](Tools.md)** | 🛠️ Dokumentasi CLI tools lengkap |
| 10 | **[Performance](Performance.md)** | Metrik performa dan benchmark |
| 11 | **[Troubleshooting](Troubleshooting.md)** | 🔧 Panduan mengatasi masalah |
| 12 | **[FAQ](FAQ.md)** | FAQ untuk persiapan sidang skripsi |

---

## 🎯 Overview

**SECURE EDGE VISION SYSTEM** adalah sistem surveilans cerdas berbasis **Edge Computing** yang menggabungkan deteksi objek AI real-time dengan enkripsi kriptografi. Sistem ini dirancang khusus untuk skenario di mana:

1. **Privasi publik** harus dijaga (wajah di-blur secara real-time)
2. **Kebutuhan forensik** tetap terpenuhi (video asli terenkripsi aman)
3. **Performa real-time** dengan GPU acceleration (25-30 FPS)

### 🔬 Konteks Akademis

> **Catatan Penting:**  
> Proyek ini dikembangkan sebagai bagian dari penelitian skripsi sarjana dengan fokus pada:
> - **Edge AI** (YOLOv8 Face Detection pada GPU lokal)
> - **Sistem Keamanan Informasi** (AES-256-GCM Encryption)
> - **Privasi Data** (Real-time Video Anonymization)

### 📊 Spesifikasi Utama

| Aspek | Spesifikasi |
|:------|:------------|
| **Bahasa Pemrograman** | Python 3.12+ |
| **AI Framework** | PyTorch + Ultralytics YOLOv8 |
| **Web Framework** | FastAPI + Uvicorn |
| **Algoritma Deteksi** | YOLOv8-Face / YOLOv11-Face (via presets) |
| **Algoritma Tracking** | BoT-SORT / ByteTrack (via presets) |
| **Algoritma Enkripsi** | AES-256-GCM (Authenticated Encryption) |
| **Algoritma Hash** | SHA-256 (Integrity Verification) |
| **Target Hardware** | NVIDIA RTX 3050 (atau setara) |
| **Target FPS** | 25-30 FPS @ 720p |

---

## ✨ Fitur Utama

### 🤖 1. Intelligent AI Engine
- **Face Detection**: Deteksi wajah real-time menggunakan YOLOv8-Face / YOLOv11-Face
- **Detection Presets**: 2 preset konfigurasi (Default & Alternative) yang mudah dipilih
- **Smart Blur**: Gaussian Blur (51x51 kernel) dengan 15% padding
- **GPU Accelerated**: Optimisasi CUDA untuk performa maksimal
- **Multi-Camera**: Dukungan hingga 3 kamera simultan

### 🔒 2. Dual-Path Security Architecture
- **Public Path**: Video teranonymize (`.mp4`) untuk monitoring harian
- **Evidence Path**: Video asli terenkripsi (`.enc`) untuk barang bukti
- **Cryptographic Integrity**: SHA-256 hash embedded dalam ciphertext

### 📊 3. Advanced Analytics Dashboard
- **Real-time Streaming**: MJPEG over HTTP
- **Storage Monitoring**: Prediksi kapasitas dan multi-drive monitor
- **Activity Charts**: Grafik aktivitas harian dengan Chart.js

### 🛠️ 4. Professional Tooling
- **Key Manager**: CLI tool untuk manajemen kunci enkripsi
- **Decryptor**: Tool untuk dekripsi evidence dengan verifikasi integritas
- **Benchmark**: Tool untuk mengukur performa sistem

---

## 🏗️ Arsitektur Tingkat Tinggi

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────────────┐                │
│  │ Webcam 0│   │ Webcam 1│   │ RTSP IP Camera  │                │
│  └────┬────┘   └────┬────┘   └────────┬────────┘                │
└───────┼─────────────┼─────────────────┼─────────────────────────┘
        │             │                 │
        ▼             ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EDGE SERVER (RTX 3050)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 Camera Threads (Parallel)                 │   │
│  │   Thread 0         Thread 1         Thread 2              │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │              AI Engine (YOLOv8-Face, CUDA)                │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│            ┌────────────────┴────────────────┐                  │
│            ▼                                 ▼                   │
│  ┌─────────────────┐              ┌─────────────────────┐       │
│  │   Public Path   │              │   Evidence Path     │       │
│  │  Gaussian Blur  │              │   AES-256-GCM       │       │
│  │    H.264 MP4    │              │   Encrypted .enc    │       │
│  └────────┬────────┘              └──────────┬──────────┘       │
└───────────┼─────────────────────────────────┼───────────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OUTPUT LAYER                              │
│  ┌───────────────┐  ┌────────────┐  ┌──────────────────┐        │
│  │ Web Dashboard │  │  Gallery   │  │ Decryption Tool  │        │
│  │ (Live Stream) │  │  (Replay)  │  │  (Admin Only)    │        │
│  └───────────────┘  └────────────┘  └──────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Struktur Proyek

```
SECURE-EDGE-VISION-SYSTEM/
├── main.py                    # FastAPI server & orchestrator
├── server.py                  # Alternative server entry
├── config.py                  # Configuration utility
├── presets.yaml               # Detection presets configuration
├── benchmark.py               # Performance benchmark tool
├── demo.py                    # Component test & demo
├── requirements.txt           # Python dependencies
├── .env                       # Environment configuration
│
├── modules/                   # Core Python modules
│   ├── __init__.py
│   ├── camera.py              # Camera capture handlers
│   ├── processor.py           # YOLOv8 detection & blur
│   ├── engine.py              # Multi-camera orchestrator
│   ├── recorder.py            # Public MP4 recording
│   ├── evidence.py            # Encrypted evidence manager
│   ├── security.py            # AES-GCM + SHA-256 crypto
│   ├── rsa_crypto.py          # RSA hybrid encryption
│   └── storage.py             # Storage utilities
│
├── tools/                     # CLI utilities
│   ├── decryptor.py           # Evidence decryption tool
│   ├── key_manager.py         # Encryption key manager
│   └── verify_integrity.py    # Hash verification tool
│
├── models/                    # AI model files
│   └── model.pt               # YOLOv8-Face weights
│
├── recordings/                # Output storage
│   ├── public/                # Blurred MP4 files
│   └── evidence/              # Encrypted .enc files
│
├── keys/                      # Encryption keys (SECURE!)
│   └── master.key             # AES-256 master key
│
├── templates/                 # HTML templates
│   ├── index.html             # Live dashboard
│   ├── gallery.html           # Video gallery
│   ├── analytics.html         # Analytics page
│   └── decrypt.html           # Decryption interface
│
├── static/                    # Static assets
│   ├── css/shared.css
│   └── js/...
│
├── tests/                     # Unit tests
│   ├── test_security.py
│   ├── test_detection.py
│   └── test_storage.py
│
└── wiki/                      # Wiki documentation
    ├── Home.md
    ├── Architecture.md
    └── ...
```

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone <repository-url>
cd SECURE-EDGE-VISION-SYSTEM

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Run
```bash
# Default preset (YOLOv8-Face + BoT-SORT)
python main.py

# Alternative preset (YOLOv11-Face + ByteTrack)
python main.py --preset 2

# Using environment variable
DETECTION_PRESET=2 python main.py
```

### 4. Access
Buka browser: `http://localhost:8000`

---

## 📖 Navigasi Wiki

Untuk memahami sistem secara mendalam, ikuti urutan berikut:

### 🚀 Untuk Pemula
1. **[QuickStart](QuickStart.md)** - Setup dalam 5 menit
2. **[Installation](Installation.md)** - Instalasi lengkap dengan CUDA

### 📚 Untuk Memahami Sistem
3. **[Architecture](Architecture.md)** - Pahami arsitektur dan komponen sistem
4. **[Security](Security.md)** - Pelajari mekanisme keamanan dan enkripsi
5. **[DualPath](DualPath.md)** - Pahami konsep dual-path storage

### 💻 Untuk Developer
6. **[Modules](Modules.md)** - Referensi kode per-modul
7. **[API](API.md)** - Dokumentasi endpoint API
8. **[Tools](Tools.md)** - CLI tools dan contoh penggunaan

### 📊 Untuk Evaluasi
9. **[Performance](Performance.md)** - Data benchmark dan metrik
10. **[Troubleshooting](Troubleshooting.md)** - Solusi masalah umum
11. **[FAQ](FAQ.md)** - Persiapan sidang skripsi

---

## 👨‍💻 Informasi Proyek

| Aspek | Detail |
|:------|:-------|
| **Nama Proyek** | SECURE EDGE VISION SYSTEM |
| **Peneliti** | Muhammad Bayu Segara |
| **Kategori** | Skripsi Sarjana (S1) |
| **Universitas** | Universitas Amikom Yogyakarta |
| **Fokus Penelitian** | Edge AI & Sistem Keamanan Informasi |

---

<div align="center">
  
*Dokumentasi ini disusun untuk keperluan akademis*

**© 2025 SECURE EDGE VISION SYSTEM**

</div>
