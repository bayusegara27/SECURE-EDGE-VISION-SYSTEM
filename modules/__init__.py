"""
Secure Edge Vision System - Modules Package
All core components for video processing and security
"""

from modules.processor import FrameProcessor
from modules.recorder import VideoRecorder
from modules.evidence import EvidenceManager
from modules.security import SecureVault

__all__ = [
    'FrameProcessor',
    'VideoRecorder', 
    'EvidenceManager',
    'SecureVault'
]
