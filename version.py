# Application Version
VERSION = "1.4.0"
VERSION_NAME = "Overlay & System Enhancement"
RELEASE_DATE = "2026-01-02"

# Version History
CHANGELOG = {
    "1.4.0": {
        "date": "2026-01-02",
        "name": "Overlay & System Enhancement",
        "features": [
            "Smart Video Overlays (Timestamp & Debug Info)",
            "Configurable overlay toggles via .env",
            "Stability fix for multi-camera stream processing",
            "YouTube stream support module integration"
        ]
    },
    "1.3.0": {
        "date": "2026-01-01",
        "name": "Analytics & System Enhancement",
        "features": [
            "Comprehensive analytics dashboard overhaul",
            "Multi-drive support with automatic detection",
            "Professional Forgejo Wiki with Mermaid diagrams",
            "Synchronized local documentation (README, Flow, etc.)",
            "Search functionality in decrypt page",
            "Project cleanup: Removed 5GB duplicate venv"
        ]
    },
    "1.2.0": {
        "date": "2025-12-31",
        "name": "Encryption & Security",
        "features": [
            "Dashboard decryption system with PIN protection",
            "Encryption flow documentation",
            "AES-256-GCM encryption implementation"
        ]
    },
    "1.1.0": {
        "date": "2025-12-30",
        "name": "Core Surveillance System",
        "features": [
            "Multi-camera RTSP support",
            "YOLOv8 AI detection",
            "Dual recording system",
            "Web interface (live view, gallery, analytics)"
        ]
    },
    "1.0.0": {
        "date": "2025-12-29",
        "name": "Initial Release",
        "features": [
            "FastAPI backend architecture",
            "Basic recording functionality",
            "Single camera support"
        ]
    }
}

def get_version_info():
    """Get current version information"""
    return {
        "version": VERSION,
        "name": VERSION_NAME,
        "release_date": RELEASE_DATE,
        "changelog": CHANGELOG
    }
