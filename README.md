# SECURE EDGE - Intelligent Surveillance System

![Version](https://img.shields.io/badge/version-1.3.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

**Advanced AI-powered surveillance system with end-to-end encryption for evidence protection.**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Wiki Documentation](#📖-wiki-documentation)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Security](#security)
- [Version History](#version-history)
- [License](#license)

---

## 🎯 Overview

SECURE EDGE is an intelligent surveillance system designed for undergraduate thesis research. It combines real-time AI object detection with military-grade encryption to provide secure evidence management for surveillance applications.

**Key Highlights:**
- 🤖 **AI Detection**: YOLOv8-powered real-time object detection
- 🔒 **End-to-End Encryption**: AES-256-GCM for evidence protection
- 📊 **Advanced Analytics**: Comprehensive storage and activity insights
- 🎥 **Multi-Camera Support**: Handle multiple RTSP streams simultaneously
- 💾 **Smart Storage**: Automatic cleanup with configurable retention policies

---

## ✨ Features

### Core Surveillance
- **Multi-Camera RTSP Support**: Connect multiple IP cameras simultaneously
- **Real-Time AI Detection**: YOLOv8 object detection with configurable confidence threshold
- **Dual Recording System**:
  - Public recordings (MP4/AVI) for general viewing
  - Encrypted evidence (`.enc`) for forensic integrity
- **Automatic Segmentation**: 5-minute video segments for easy management

### Security & Encryption
- **AES-256-GCM Encryption**: Military-grade authenticated encryption
- **SHA-256 Hashing**: Integrity verification for all evidence
- **PIN-Protected Decryption**: Secure access to encrypted evidence
- **In-Browser Playback**: Decrypt and view evidence without saving to disk

### Analytics Dashboard
- **Real-Time Metrics**: Events today, peak hour, average per hour
- **Storage Health**: Multi-drive analysis with usage forecasting
- **Storage Efficiency**: File counts, average sizes, compression ratios
- **Peak Activity Analysis**: Busiest hours and cameras
- **Interactive Charts**: Chart.js visualizations with enhanced tooltips

### Web Interface
- **Live View**: Real-time camera feeds with detection boxes
- **Gallery**: Browse and playback recorded videos
- **Analytics**: Comprehensive system insights
- **Decrypt**: Secure evidence decryption interface
- **Search**: Quick filtering in evidence list

---

## 📖 Wiki Documentation

Dokumentasi lengkap, panduan teknis, dan FAQ tersedia di Wiki Forgejo:
👉 **[SECURE EDGE VISION SYSTEM WIKI](http://192.168.0.135:3000/nakumi/SECURE-EDGE-VISION-SYSTEM/wiki)**

Wiki mencakup:
- **Architecture Detail**: Penjelasan mendalam komponen sistem.
- **Dual-Path Processing**: Cara kerja privasi vs forensik.
- **Security Guide**: Detail teknis enkripsi AES-256-GCM.
- **Quick-Start Guide**: Panduan instalasi 5 menit.
- **FAQ**: Pertanyaan dan jawaban untuk sidang skripsi.

---

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 (tested), Linux (compatible)
- **Python**: 3.11 or higher
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 50GB+ for recordings
- **Network**: Gigabit Ethernet for multiple cameras

### Recommended for AI Detection
- **GPU**: NVIDIA GPU with CUDA support
- **VRAM**: 4GB+ for optimal performance
- **CPU**: Intel i5/AMD Ryzen 5 or better

---

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/secure-edge.git
cd secure-edge
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download YOLOv8 Model
```bash
# Model will be auto-downloaded on first run
# Or manually download to models/ directory
```

### 5. Setup Environment
```bash
# Copy example environment file
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env with your configuration
notepad .env
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# Camera Configuration
CAMERA_SOURCES=rtsp://192.168.1.100:554/stream,rtsp://192.168.1.101:554/stream
CAMERA_NAMES=Front Door,Backyard

# Detection Settings
DETECTION_CONFIDENCE=0.5
DETECTION_FPS=30

# Storage Configuration
PUBLIC_RECORDINGS_PATH=H:\SkripsiRecord\public
EVIDENCE_RECORDINGS_PATH=H:\SkripsiRecord\evidence
MAX_STORAGE_GB=100
RETENTION_DAYS=30

# Server Settings
HOST=0.0.0.0
PORT=8000
```

### Master Key Setup

```bash
# Generate master encryption key
python -c "from modules.evidence import generate_master_key; generate_master_key()"
```

---

## 📖 Usage

### Start the System

```bash
python main.py
```

### Access Web Interface

Open browser and navigate to:
- **Live View**: http://localhost:8000/
- **Gallery**: http://localhost:8000/gallery
- **Analytics**: http://localhost:8000/analytics
- **Decrypt**: http://localhost:8000/decrypt

### Stop the System

Press `Ctrl+C` in the terminal

---

## 🏗️ Architecture

```
SECURE EDGE
├── main.py                 # FastAPI application entry point
├── modules/
│   ├── engine.py          # Core surveillance engine
│   ├── recorder.py        # Video recording logic
│   ├── evidence.py        # Encryption/decryption
│   └── storage.py         # Storage management
├── templates/             # Jinja2 HTML templates
├── static/               # CSS, JS, assets
├── recordings/
│   ├── public/           # MP4/AVI recordings
│   └── evidence/         # Encrypted .enc files
├── models/               # YOLOv8 model files
└── keys/                 # Encryption keys (gitignored)
```

### Technology Stack

**Backend:**
- FastAPI + Uvicorn (async web server)
- OpenCV (video processing)
- Ultralytics YOLOv8 (AI detection)
- cryptography (AES-256-GCM)
- psutil (system metrics)

**Frontend:**
- Jinja2 Templates
- Chart.js (analytics visualizations)
- Lucide Icons
- Vanilla JavaScript

---

## 🔐 Security

### Encryption Specifications

- **Algorithm**: AES-256-GCM (Galois/Counter Mode)
- **Key Derivation**: SHA-256
- **Authentication**: Built-in AEAD (Authenticated Encryption with Associated Data)
- **File Format**: Custom `.enc` with metadata header

### Security Best Practices

1. **Never commit** `master.key` to version control
2. **Use strong PINs** for key protection (8+ characters)
3. **Backup encryption keys** securely
4. **Rotate keys** periodically for long-term deployments
5. **Restrict network access** to trusted devices only

For detailed security analysis, see [`encryption_flow.md`](encryption_flow.md)

---

## 📊 Version History

### v1.3.0 (2026-01-01) - Current
- ✅ Comprehensive analytics dashboard
- ✅ Multi-drive support
- ✅ Search functionality
- ✅ Enhanced chart tooltips

### v1.2.0 (2025-12-31)
- ✅ Dashboard decryption system
- ✅ Encryption documentation
- ✅ PIN-protected access

### v1.1.0 (2025-12-30)
- ✅ Multi-camera support
- ✅ YOLOv8 integration
- ✅ Web interface

### v1.0.0 (2025-12-29)
- ✅ Initial release
- ✅ Basic recording
- ✅ FastAPI backend

See [`VERSION.md`](VERSION.md) for complete changelog.

---

## 📝 License

This project is developed as part of an undergraduate thesis (Skripsi) at [Your University].

**For Academic Use Only**

---

## 👨‍💻 Author

**[Your Name]**  
Undergraduate Student - Computer Science  
[Your University]  
Year: 2025-2026

---

## 🙏 Acknowledgments

- Ultralytics for YOLOv8
- FastAPI team for excellent framework
- OpenCV community
- Chart.js for visualization library

---

## 📧 Contact

For questions or issues, please contact:
- Email: [your.email@university.edu]
- GitHub: [@yourusername](https://github.com/yourusername)

---

**⭐ Star this repo if you find it useful!**
