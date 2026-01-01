# Secure Edge Vision System

## Version History

### v1.3.0-stable (2026-01-01) - CURRENT
**The Documentation & Analytics Update**

#### Features:
- ✅ **New Documentation Center**: Comprehensive Wiki Forgejo dengan Mermaid diagrams.
- ✅ **Advanced Analytics**: Real-time storage metrics, usage velocity forecast, dan interactive charts.
- ✅ **Multi-Drive Dashboard**: Monitor semua disk drive yang digunakan untuk recording.
- ✅ **Evidence Search**: Filter evidence berdasarkan nama file, tanggal, atau ukuran.
- ✅ **Selective Recording**: Efisiensi storage hingga 80% (record hanya saat ada wajah).
- ✅ **AES-256-GCM Encryption**: Keamanan tingkat militer untuk bukti forensik.
- ✅ **In-Browser Decryption**: Buka evidence langsung dari dashboard via PIN aman.

#### Technical Improvements:
- Removed 5GB duplicate venv for optimized development.
- Updated .gitignore for Frontmatter CMS and other cache files.
- Synchronized all documentation (README, Masterplan, Encryption Flow) with Mermaid.

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
