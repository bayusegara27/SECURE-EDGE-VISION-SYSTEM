# Secure Edge Vision System

## Version History

### v1.0.0-stable (2026-01-01)
**Production Ready Release**

#### Features:
- ✅ Multi-camera support (3 streams)
- ✅ Real-time face detection (YOLOv8-Face)
- ✅ Dual-path recording (Public MP4 + Encrypted Evidence)
- ✅ AES-256-GCM encryption with SHA-256 integrity
- ✅ Web dashboard (Live, Gallery, Analytics, Decrypt)
- ✅ Storage optimization (selective recording, JPEG quality)
- ✅ FIFO retention policy (auto-cleanup)
- ✅ Analytics dashboard with charts

#### Bug Fixes:
- Fixed evidence filename None timestamp
- Fixed shutdown AttributeError
- Fixed camera disconnect styling (transparent overlay)
- Added stop() methods for API consistency

#### Technical Stack:
- Python 3.12
- FastAPI + Uvicorn
- PyTorch + YOLOv8
- OpenCV (CUDA accelerated)
- AES-GCM encryption
- Chart.js analytics

#### System Requirements:
- CPU: Intel i5 Gen 11+
- GPU: NVIDIA RTX 3050 (4GB VRAM)
- RAM: 16GB
- Storage: 512GB SSD
- OS: Windows 10/11

#### Known Issues:
- RTSP camera timeout (hardware issue, not code)
- JavaScript lint warnings (Jinja2 template syntax, cosmetic)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run system
python main.py

# Access dashboard
http://localhost:8000
```

## Documentation
- `MASTERPLAN.md` - Complete thesis guide
- `audit_report.md` - System health check
- `README.md` - This file

## License
MIT License - For Academic Use (Thesis Project)
