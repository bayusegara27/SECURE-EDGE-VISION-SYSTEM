"""
YouTube Stream Handler Module
Extracts playable stream URLs from YouTube live streams using yt-dlp
"""

import logging
import subprocess
import shutil
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


def is_youtube_url(url: str) -> bool:
    """
    Check if a URL is a YouTube URL (video or live stream)
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/live/VIDEO_ID
    """
    if not isinstance(url, str):
        return False
    
    url_lower = url.lower()
    youtube_domains = [
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "m.youtube.com"
    ]
    
    try:
        parsed = urlparse(url_lower)
        return any(domain in parsed.netloc for domain in youtube_domains)
    except Exception:
        return False


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL
    
    Returns:
        Video ID string or None if not found
    """
    try:
        parsed = urlparse(url)
        
        # Format: youtu.be/VIDEO_ID
        if "youtu.be" in parsed.netloc:
            return parsed.path.strip("/")
        
        # Format: youtube.com/watch?v=VIDEO_ID
        if "v" in parse_qs(parsed.query):
            return parse_qs(parsed.query)["v"][0]
        
        # Format: youtube.com/live/VIDEO_ID
        if "/live/" in parsed.path:
            return parsed.path.split("/live/")[1].split("/")[0]
        
        return None
    except Exception as e:
        logger.error(f"Failed to extract video ID: {e}")
        return None


def check_ytdlp_available() -> bool:
    """Check if yt-dlp is available in the system"""
    return shutil.which("yt-dlp") is not None


def extract_stream_url(youtube_url: str, quality: str = "best") -> Optional[str]:
    """
    Extract playable stream URL from YouTube using yt-dlp
    
    Args:
        youtube_url: Full YouTube URL
        quality: Stream quality preference ('best', 'worst', '720p', etc.)
    
    Returns:
        Direct stream URL (m3u8/mpd) or None if extraction fails
    """
    if not is_youtube_url(youtube_url):
        logger.error(f"Not a valid YouTube URL: {youtube_url}")
        return None
    
    # Check if yt-dlp is available
    if not check_ytdlp_available():
        logger.error("yt-dlp is not installed. Install with: pip install yt-dlp")
        return None
    
    try:
        logger.info(f"Extracting stream URL from: {youtube_url}")
        
        # Use yt-dlp to get the direct stream URL
        # -f best: get best quality
        # -g: print URL only (don't download)
        # --no-warnings: suppress warnings
        cmd = [
            "yt-dlp",
            "-f", quality,
            "-g",  # Get URL only
            "--no-warnings",
            "--no-playlist",
            youtube_url
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        if result.returncode != 0:
            logger.error(f"yt-dlp failed: {result.stderr}")
            return None
        
        stream_url = result.stdout.strip()
        
        if not stream_url:
            logger.error("yt-dlp returned empty URL")
            return None
        
        # For live streams, yt-dlp may return multiple URLs (video + audio)
        # Take the first one (usually video with audio for live streams)
        if "\n" in stream_url:
            stream_url = stream_url.split("\n")[0]
        
        logger.info(f"Successfully extracted stream URL (length: {len(stream_url)})")
        return stream_url
        
    except subprocess.TimeoutExpired:
        logger.error("yt-dlp timed out")
        return None
    except FileNotFoundError:
        logger.error("yt-dlp not found. Install with: pip install yt-dlp")
        return None
    except Exception as e:
        logger.error(f"Failed to extract stream URL: {e}")
        return None


def get_stream_info(youtube_url: str) -> Optional[dict]:
    """
    Get metadata about a YouTube stream
    
    Returns:
        Dictionary with stream info or None if failed
    """
    if not is_youtube_url(youtube_url):
        return None
    
    if not check_ytdlp_available():
        return None
    
    try:
        import json
        
        cmd = [
            "yt-dlp",
            "-j",  # JSON output
            "--no-warnings",
            "--no-playlist",
            youtube_url
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return None
        
        info = json.loads(result.stdout)
        
        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "is_live": info.get("is_live", False),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "view_count": info.get("view_count"),
            "thumbnail": info.get("thumbnail")
        }
        
    except Exception as e:
        logger.error(f"Failed to get stream info: {e}")
        return None


class YouTubeStreamHandler:
    """
    Handler class for YouTube stream management with caching and reconnection
    """
    
    def __init__(self, youtube_url: str):
        self.youtube_url = youtube_url
        self.stream_url: Optional[str] = None
        self.stream_info: Optional[dict] = None
        self._last_refresh = 0
        self._refresh_interval = 3600  # Refresh URL every hour (live streams may change)
    
    def get_stream_url(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get stream URL with caching
        
        Args:
            force_refresh: Force re-extraction even if cached
        
        Returns:
            Stream URL or None
        """
        import time
        
        current_time = time.time()
        
        # Check if we need to refresh
        if (self.stream_url is None or 
            force_refresh or 
            current_time - self._last_refresh > self._refresh_interval):
            
            self.stream_url = extract_stream_url(self.youtube_url)
            self._last_refresh = current_time
        
        return self.stream_url
    
    def get_info(self) -> Optional[dict]:
        """Get cached or fresh stream info"""
        if self.stream_info is None:
            self.stream_info = get_stream_info(self.youtube_url)
        return self.stream_info
    
    def is_valid(self) -> bool:
        """Check if YouTube URL is valid"""
        return is_youtube_url(self.youtube_url)


# ============================================================
# Module-level convenience functions
# ============================================================

def prepare_youtube_source(url: str) -> Tuple[Optional[str], str]:
    """
    Prepare a YouTube URL for use with cv2.VideoCapture
    
    Args:
        url: YouTube URL
    
    Returns:
        Tuple of (stream_url, source_type)
        - stream_url: Direct stream URL or None if failed
        - source_type: "youtube_live" or "youtube_video" or "error"
    """
    if not is_youtube_url(url):
        return None, "error"
    
    info = get_stream_info(url)
    source_type = "youtube_live" if info and info.get("is_live") else "youtube_video"
    
    stream_url = extract_stream_url(url)
    
    if stream_url:
        return stream_url, source_type
    
    return None, "error"


# Test code
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python youtube.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print(f"\nTesting URL: {url}")
    print(f"Is YouTube URL: {is_youtube_url(url)}")
    print(f"Video ID: {extract_video_id(url)}")
    print(f"yt-dlp available: {check_ytdlp_available()}")
    
    print("\nExtracting stream URL...")
    stream_url = extract_stream_url(url)
    
    if stream_url:
        print(f"Stream URL (truncated): {stream_url[:100]}...")
        
        # Test with OpenCV
        print("\nTesting with OpenCV...")
        import cv2
        cap = cv2.VideoCapture(stream_url)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✓ Successfully read frame: {frame.shape}")
            else:
                print("✗ Failed to read frame")
            cap.release()
        else:
            print("✗ Failed to open stream")
    else:
        print("✗ Failed to extract stream URL")
