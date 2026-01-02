"""
Secure Edge Vision System - Modules Package
All core components for video processing and security
"""

from modules.processor import FrameProcessor
from modules.recorder import VideoRecorder
from modules.evidence import EvidenceManager
from modules.security import SecureVault
from modules.youtube import is_youtube_url, extract_stream_url, YouTubeStreamHandler

__all__ = [
    'FrameProcessor',
    'VideoRecorder', 
    'EvidenceManager',
    'SecureVault',
    'is_youtube_url',
    'extract_stream_url',
    'YouTubeStreamHandler'
]
