"""
Secure Edge Vision System
Main Entry Point & Web Server
"""

import os
import sys
import logging
import asyncio
import threading
import time
import re
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Silencing OpenCV/FFMPEG persistent warnings
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8" # Deep silence for FFMPEG
import pickle
import tempfile
import uuid
import hashlib
import psutil
from typing import Optional, Dict

from config import Config
from modules.engine import get_system, processing_loop

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Custom exception handler to suppress Windows connection reset errors
def handle_exception(loop, context):
    """Suppress ConnectionResetError on Windows (WinError 10054)"""
    exception = context.get("exception")
    if isinstance(exception, ConnectionResetError):
        # Browser closed connection - this is normal
        return
    if exception:
        logger.error(f"Asyncio error: {exception}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan manager"""
    system = get_system()
    
    # Set custom exception handler
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)
    
    try:
        system.start()
        
        # Start processing thread for each configured camera
        for i in range(len(system.config.camera_sources)):
            thread = threading.Thread(target=processing_loop, args=(i,), daemon=True)
            thread.start()
        
        yield
        
    finally:
        system.stop()


from fastapi.staticfiles import StaticFiles

# Handle versioning from VERSION.txt
def get_app_version():
    try:
        with open("VERSION.txt", "r") as f:
            for line in f:
                if line.startswith("Version "):
                    return line.replace("Version ", "").strip()
    except:
        pass
    return "1.0.0"

app = FastAPI(
    title="Secure Edge Vision System",
    description="Real-time video anonymization",
    version=get_app_version(),
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount public recordings as snapshots/thumbnails source
# We mount the parent folder or specific folders.
# Since config says "recordings/public", let's mount that.
public_path = os.getenv("PUBLIC_RECORDINGS_PATH", "recordings/public")
if not os.path.exists(public_path):
    os.makedirs(public_path, exist_ok=True)
app.mount("/thumbnails", StaticFiles(directory=public_path), name="thumbnails")

templates = Jinja2Templates(directory="templates")

# ... (generate_frames, dashboard, video_stream, status endpoints remain same) ...

@app.get("/gallery", response_class=HTMLResponse)
async def gallery_page(request: Request):
    """Gallery / Explorer View"""
    return templates.TemplateResponse("gallery.html", {"request": request})


async def generate_frames(camera_idx: int):
    """Generate MJPEG frames for a specific camera"""
    system = get_system()
    
    while system.running:  # Exit immediately when system stops
        frame, detections, fps = system.get_frame(camera_idx)
        
        if frame is not None:
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + 
                   buffer.tobytes() + b'\r\n')
        
        await asyncio.sleep(0.04)  # ~25 FPS for streaming bandwidth


@app.get("/")
async def dashboard(request: Request):
    """Dashboard page showing all cameras"""
    system = get_system()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Secure Edge Vision System",
        "cameras": list(range(len(system.config.camera_sources))),
        "sources": system.config.camera_sources
    })


@app.get("/stream/{camera_idx}")
async def video_stream(camera_idx: int):
    """MJPEG video stream for specific camera"""
    return StreamingResponse(
        generate_frames(camera_idx),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/api/status")
async def get_status():
    """Full system status including all cameras"""
    system = get_system()
    
    cameras_status = []
    for i, src in enumerate(system.config.camera_sources):
        # Use i directly as index, src is just for label
        _, detections, fps = system.get_frame(i)
        cameras_status.append({
            "id": i,
            "fps": round(fps, 1),
            "detections": detections,
            "source": str(src),
            "state": system.camera_status.get(i, "offline")
        })
    
    return {
        "status": "running" if system.running else "stopped",
        "cameras": cameras_status,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/recordings")
async def list_recordings():
    """List public recordings from all cameras"""
    system = get_system()
    all_recordings = []
    for idx, rec in system.public_recorders.items():
        all_recordings.extend(rec.get_recording_list())
    return {"recordings": all_recordings}


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Analytics dashboard page"""
    return templates.TemplateResponse("analytics.html", {"request": request})


@app.get("/api/analytics")
async def get_analytics_data():
    """Aggregate data for charts: detections, storage, and system health"""
    system = get_system()
    import json
    
    # 1. Storage Stats
    public_path = Path(os.getenv("PUBLIC_RECORDINGS_PATH", "recordings/public"))
    evidence_path = Path(os.getenv("EVIDENCE_RECORDINGS_PATH", "recordings/evidence"))
    
    storage_data = {
        "public": 0,
        "evidence": 0,
        "by_camera": {}
    }
    
    if public_path.exists():
        for f in list(public_path.glob("*.mp4")) + list(public_path.glob("*.avi")):
            size = f.stat().st_size / (1024 * 1024)
            storage_data["public"] += size
            parts = f.name.split('_')
            if len(parts) > 1:
                cam = parts[1]
                storage_data["by_camera"][cam] = storage_data["by_camera"].get(cam, 0) + size

    if evidence_path.exists():
        for f in evidence_path.rglob("*.enc"):
            storage_data["evidence"] += f.stat().st_size / (1024 * 1024)

    # 2. Deep Detection Analysis
    hourly_counts = {i: 0 for i in range(24)}
    class_distribution = {}
    camera_activity = {}
    recent_logs = []
    total_events = 0
    
    meta_files = sorted(list(public_path.glob("*.json")), key=lambda x: x.stat().st_mtime, reverse=True)
    now = datetime.now()
    
    for meta_file in meta_files:
        try:
            mtime = datetime.fromtimestamp(meta_file.stat().st_mtime)
            is_recent = (now - mtime).days == 0
            
            with open(meta_file, 'r') as f:
                data = json.load(f)
                detections = data.get("detections", [])
                
                # Clustering Algorithm: Group frames into logical events
                # Threshold: 60 frames (~2 seconds at 30 fps) gap
                file_event_count = 0
                last_frame = -999
                current_event_classes = set()
                
                match = re.search(r'public_(cam\d+|rtsp)_', meta_file.name)
                cam_name = match.group(1) if match else "unknown"

                for d in detections:
                    # Compatibility: handle both raw int and new dict format
                    frame_idx = d if isinstance(d, int) else d.get("f", 0)
                    classes = ["person"] if isinstance(d, int) else d.get("c", [])
                    
                    if frame_idx > last_frame + 60:
                        file_event_count += 1
                        # Push previous event summary to logs
                        if last_frame != -999 and len(recent_logs) < 50:
                            recent_logs.append({
                                "timestamp": mtime.strftime("%H:%M:%S"),
                                "node": cam_name,
                                "class": ", ".join([c.capitalize() for c in current_event_classes]) or "Activity",
                                "conf": "High"
                            })
                        # Update stats for previous event
                        if last_frame != -999 and is_recent:
                            for c in current_event_classes:
                                class_distribution[c] = class_distribution.get(c, 0) + 1
                        
                        current_event_classes = set(classes)
                    else:
                        current_event_classes.update(classes)
                    
                    last_frame = frame_idx
                
                # Finalize last event in file
                if last_frame != -999:
                    if len(recent_logs) < 50:
                        recent_logs.append({
                            "timestamp": mtime.strftime("%H:%M:%S"),
                            "node": cam_name,
                            "class": ", ".join([c.capitalize() for c in current_event_classes]) or "Activity",
                            "conf": "High"
                        })
                    if is_recent:
                        total_events += file_event_count
                        hourly_counts[mtime.hour] += file_event_count
                        camera_activity[cam_name] = camera_activity.get(cam_name, 0) + file_event_count
                        for c in current_event_classes:
                            class_distribution[c] = class_distribution.get(c, 0) + 1
        except Exception as e:
            logger.error(f"Error parsing metadata {meta_file}: {e}")
            continue

    # 3. Storage Forecast & Retention (Thesis-level accuracy)
    from modules.storage import cleanup_storage
    
    # Force retention check every time analytics is requested
    current_total_mb = (storage_data["public"] + storage_data["evidence"])
    cleanup_storage(str(public_path), str(evidence_path), system.config.max_storage_gb)
    
    # Calculate more accurate hourly rate (usage in last 60 mins)
    recent_mb = 0
    now_ts = time.time()
    for f in list(public_path.rglob("*.*")) + list(evidence_path.rglob("*.*")):
        if f.is_file():
            stat = f.stat()
            # If created in last 1 hour
            if now_ts - stat.st_mtime < 3600:
                recent_mb += stat.st_size / (1024 * 1024)
    
    # Hourly rate calculation:
    # Use recent activity if available, else fallback to average
    hourly_rate = recent_mb if recent_mb > 1 else (current_total_mb / 24)
    hourly_rate = max(hourly_rate, 50) # Safety floor 50MB/hr
    
    # Get disk usage from ACTUAL recordings path, not current directory
    # Use public_path as reference since that's where most data is stored
    recordings_disk = psutil.disk_usage(str(public_path))
    
    # Get all disk partitions for comprehensive analysis
    all_disks = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            all_disks.append({
                "drive": partition.device,
                "mountpoint": partition.mountpoint,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent,
                "fstype": partition.fstype
            })
        except (PermissionError, OSError):
            # Skip drives that can't be accessed
            continue
    
    # Calculate remaining space based on CONFIGURED LIMIT, not total disk
    max_storage_mb = system.config.max_storage_gb * 1024  # Convert GB to MB
    remaining_mb = max_storage_mb - current_total_mb  # Space left until limit
    
    # Project days left based on hourly rate * 24
    # If remaining is negative (over limit), show 0 days
    if remaining_mb <= 0:
        days_left = 0.0
    else:
        daily_rate_mb = hourly_rate * 24
        days_left = round(remaining_mb / daily_rate_mb, 1) if daily_rate_mb > 0 else 999.9

    # 4. Forensic Markers
    evidence_count = len(list(evidence_path.rglob("*.enc")))
    
    # Sort hourly counts nicely for Chart.js
    trend_labels = []
    trend_values = []
    current_hour = now.hour
    for i in range(24):
        h = (current_hour - 23 + i) % 24
        trend_labels.append(f"{h:02d}:00")
        trend_values.append(hourly_counts[h])

    
    # Calculate additional metrics
    peak_hour = max(hourly_counts.items(), key=lambda x: x[1])[0] if any(hourly_counts.values()) else 0
    total_detections_today = sum(hourly_counts.values())
    
    # File statistics
    public_files = len(list(public_path.glob("*.mp4"))) + len(list(public_path.glob("*.avi")))
    evidence_files = len(list(evidence_path.rglob("*.enc")))
    
    # Average file sizes
    avg_public_size = (storage_data["public"] / public_files) if public_files > 0 else 0
    avg_evidence_size = (storage_data["evidence"] / evidence_files) if evidence_files > 0 else 0
    
    # Storage efficiency (compression ratio)
    compression_ratio = (storage_data["evidence"] / storage_data["public"]) if storage_data["public"] > 0 else 1.0
    
    return {
        "storage": {
            "total_mb": round(current_total_mb, 2),
            "max_gb": system.config.max_storage_gb,
            "hourly_rate_mb": round(hourly_rate, 1),
            "public_mb": round(storage_data["public"], 2),
            "evidence_mb": round(storage_data["evidence"], 2),
            "by_camera": {k: round(v, 2) for k, v in storage_data["by_camera"].items()},
            "days_left": days_left,
            "public_files": public_files,
            "evidence_files": evidence_files,
            "avg_public_size_mb": round(avg_public_size, 2),
            "avg_evidence_size_mb": round(avg_evidence_size, 2),
            "compression_ratio": round(compression_ratio, 2),
            "recordings_path": str(public_path)
        },
        "trends": {
            "labels": trend_labels,
            "values": trend_values,
            "peak_hour": f"{peak_hour:02d}:00",
            "total_today": total_detections_today
        },
        "classification": class_distribution,
        "camera_activity": camera_activity,
        "recent_logs": recent_logs,
        "health": {
            "disk_total_gb": round(recordings_disk.total / (1024**3), 2),
            "disk_free_gb": round(recordings_disk.free / (1024**3), 2),
            "disk_percent": recordings_disk.percent,
            "cameras_online": sum(1 for s in system.camera_status.values() if s == "online"),
            "total_cameras": len(system.config.camera_sources),
            "total_detections": total_events,
            "evidence_files": evidence_count,
            "all_disks": all_disks,
            "recordings_drive": str(public_path.drive) if hasattr(public_path, 'drive') else str(public_path)[:2]
        }
    }


# =============================================================================
# DECRYPTION ENDPOINTS
# =============================================================================

class DecryptRequest(BaseModel):
    filename: str
    pin: Optional[str] = None
    show_boxes: bool = True


# Temporary storage for decrypted videos
_decrypted_cache = {}


@app.get("/decrypt", response_class=HTMLResponse)
async def decrypt_page(request: Request):
    """Decrypt tool page"""
    return templates.TemplateResponse("decrypt.html", {"request": request})


@app.get("/api/evidence-decrypt")
async def list_evidence_for_decrypt():
    """List evidence files with format detection for decrypt page"""
    from modules.security import HybridVault
    
    system = get_system()
    active_files = []
    for manager in system.evidence_managers.values():
        if manager.current_target:
            active_files.append(manager.current_target)

    evidence_path = Path(os.getenv("EVIDENCE_RECORDINGS_PATH", "recordings/evidence"))
    evidence = []
    
    if evidence_path.exists():
        for f in sorted(evidence_path.rglob("*.enc"), reverse=True):
            stat = f.stat()
            is_hybrid = HybridVault.is_hybrid_format(str(f))
            is_active = (f.name in active_files)
            evidence.append({
                "filename": f.name,
                "path": str(f),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "format": "hybrid" if is_hybrid else "symmetric",
                "is_active": is_active
            })
    
    return {"evidence": evidence}


@app.post("/api/decrypt")
async def decrypt_evidence(request: DecryptRequest):
    """Decrypt an evidence file and return video for preview"""
    from modules.security import SecureVault, HybridVault
    import pickle
    import tempfile
    
    # 1. Generate a stable video ID based on filename and settings
    # This allows us to reuse existing decrypted files
    config_string = f"{request.filename}_{request.show_boxes}"
    video_id = hashlib.md5(config_string.encode()).hexdigest()[:12]
    
    temp_dir = Path(tempfile.gettempdir()) / "secure_edge_decrypt"
    temp_dir.mkdir(exist_ok=True)
    temp_video_path = temp_dir / f"{video_id}.mp4"
    
    logger.info(f"AUDIT: Decryption requested for evidence: {request.filename}")
    
    # Smart Cache: Check if video already exists
    if temp_video_path.exists():
        logger.info(f"AUDIT: Serving cached decryption (Instant Recovery) for: {request.filename}")
        # We still need metadata (frame count, duration) for the UI
        # For simplicity, we'll store small meta files next to the videos
        meta_cache_path = temp_video_path.with_suffix('.json')
        if meta_cache_path.exists():
            import json
            with open(meta_cache_path, 'r') as f:
                cached_meta = json.load(f)
            
            _decrypted_cache[video_id] = str(temp_video_path)
            return {
                "success": True,
                "frame_count": cached_meta["frame_count"],
                "duration": cached_meta["duration"],
                "hash": cached_meta["hash"],
                "video_url": f"/api/decrypt-video/{video_id}"
            }

    # Find the file
    evidence_path = Path(os.getenv("EVIDENCE_RECORDINGS_PATH", "recordings/evidence"))
    filepath = None
    
    for f in evidence_path.rglob("*.enc"):
        if f.name == request.filename:
            filepath = f
            break
    
    if not filepath or not filepath.exists():
        raise HTTPException(status_code=404, detail="Evidence file not found")
    
    # Detect format
    is_hybrid = HybridVault.is_hybrid_format(str(filepath))
    show_boxes = request.show_boxes
    
    def do_decrypt():
        """Heavy decryption work - runs in thread pool"""
        # Load vault
        if is_hybrid:
            private_key_path = os.getenv("RSA_PRIVATE_KEY_PATH", "keys/rsa_private.pem")
            if not Path(private_key_path).exists():
                raise ValueError("RSA private key not found")
            vault = HybridVault(
                private_key_path=private_key_path,
                private_key_password=request.pin
            )
        else:
            key_path = os.getenv("ENCRYPTION_KEY_PATH", "keys/master.key")
            if not Path(key_path).exists():
                raise ValueError("Encryption key not found")
            vault = SecureVault(key_path=key_path)
        
        # Decrypt
        data, metadata = vault.load_encrypted_file(str(filepath))
        frames_data = pickle.loads(data)
        
        # Create video from frames
        if frames_data:
            first_frame_data = frames_data[0]
            frame_key = "frame_jpg" if "frame_jpg" in first_frame_data else "frame"
            
            first_frame = cv2.imdecode(
                np.frombuffer(first_frame_data[frame_key], np.uint8),
                cv2.IMREAD_COLOR
            )
            h, w = first_frame.shape[:2]
            
            # Use H.264 codec for browser compatibility
            codecs = ['avc1', 'X264', 'H264', 'mp4v']
            writer = None
            for codec in codecs:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                writer = cv2.VideoWriter(str(temp_video_path), fourcc, 30, (w, h))
                if writer.isOpened():
                    break
                writer.release()
            
            for frame_data in frames_data:
                frame = cv2.imdecode(
                    np.frombuffer(frame_data[frame_key], np.uint8),
                    cv2.IMREAD_COLOR
                )
                
                # Draw detection boxes (if enabled)
                if show_boxes:
                    for det in frame_data.get("detections", []):
                        x1, y1 = det.get("x1", 0), det.get("y1", 0)
                        x2, y2 = det.get("x2", 0), det.get("y2", 0)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                writer.write(frame)
            
            writer.release()
        
        # Calculate stats
        frame_count = metadata.get("frame_count", len(frames_data))
        start_time = metadata.get("start_time", 0)
        end_time = metadata.get("end_time", 0)
        duration = end_time - start_time if end_time > start_time else frame_count / 30
        data_hash = hashlib.sha256(data).hexdigest()
        
        # Save meta cache for next time
        import json
        with open(temp_video_path.with_suffix('.json'), 'w') as f:
            json.dump({
                "frame_count": frame_count,
                "duration": duration,
                "hash": data_hash
            }, f)
        
        return {
            "video_id": video_id,
            "video_path": str(temp_video_path),
            "frame_count": frame_count,
            "duration": duration,
            "hash": data_hash
        }
    
    # Run decrypt in thread pool to avoid blocking server
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, do_decrypt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")
    
    # Cache video path
    _decrypted_cache[result["video_id"]] = result["video_path"]
    
    return {
        "success": True,
        "frame_count": result["frame_count"],
        "duration": result["duration"],
        "hash": result["hash"],
        "video_url": f"/api/decrypt-video/{result['video_id']}"
    }


@app.get("/api/decrypt-video/{video_id}")
async def get_decrypted_video(video_id: str, download: bool = False):
    """Serve decrypted video from temp storage"""
    if video_id not in _decrypted_cache:
        raise HTTPException(status_code=404, detail="Video not found or expired")
    
    video_path = Path(_decrypted_cache[video_id])
    if not video_path.exists():
        del _decrypted_cache[video_id]
        raise HTTPException(status_code=404, detail="Video file not found")
    
    if download:
        return FileResponse(
            str(video_path),
            media_type="video/mp4",
            filename=f"decrypted_{video_id}.mp4"
        )
    
    return FileResponse(str(video_path), media_type="video/mp4")


@app.get("/api/recording-metadata/{filename}")
async def get_recording_metadata(filename: str):
    """Get detection metadata for a specific recording"""
    public_path = os.getenv("PUBLIC_RECORDINGS_PATH", "recordings/public")
    meta_path = Path(public_path) / filename.replace(".mp4", ".json")
    
    if not meta_path.exists():
        return {"filename": filename, "detections": []}
    
    try:
        import json
        with open(meta_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading metadata {filename}: {e}")
        return {"filename": filename, "detections": []}


@app.get("/replay/{filename}")
async def replay_file(filename: str, request: Request):
    """Serve recording file with Range request support for video streaming"""
    path = Path(os.getenv("PUBLIC_RECORDINGS_PATH", "recordings/public")) / filename
    if not path.exists() or path.suffix != ".mp4":
        raise HTTPException(status_code=404)
    
    file_size = path.stat().st_size
    range_header = request.headers.get("range")
    
    if range_header:
        try:
            range_str = range_header.replace("bytes=", "")
            start_str, end_str = range_str.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
        except:
            start = 0
            end = file_size - 1
        
        if start >= file_size:
            raise HTTPException(status_code=416, detail="Range not satisfiable")
        
        end = min(end, file_size - 1)
        content_length = end - start + 1
        
        def iter_file():
            with open(path, "rb") as f:
                f.seek(start)
                remaining = content_length
                chunk_size = 1024 * 1024
                while remaining > 0:
                    chunk = f.read(min(chunk_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
        
        return StreamingResponse(
            iter_file(),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(content_length),
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache"
            }
        )
    
    return FileResponse(
        str(path), 
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size)
        }
    )


@app.get("/replay-page/{filename}", response_class=HTMLResponse)
async def replay_page(request: Request, filename: str):
    """Replay page with on-demand rotation for active files"""
    system = get_system()
    
    # Check if this is the active recording file for any camera
    for idx, recorder in system.public_recorders.items():
        if recorder.current_file:
            active_filename = Path(recorder.current_file).name
            if filename == active_filename:
                logger.info(f"User requested active recording {filename} from Cam {idx}, forcing rotation...")
                recorder.rotate()
                await asyncio.sleep(0.5)
                break
    
    return templates.TemplateResponse("replay.html", {
        "request": request,
        "filename": filename,
        "video_url": f"/replay/{filename}"
    })


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Secure Edge Vision System - Real-time Video Anonymization",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--port", "-p", type=int, default=None, help="Web server port")
    parser.add_argument("--host", type=str, default=None, help="Web server host")
    parser.add_argument("--camera", "-c", type=str, default=None, help="Camera source")
    parser.add_argument("--device", "-d", type=str, choices=["cuda", "cpu"], default=None, help="Device")
    
    args = parser.parse_args()
    
    # Updates to config are handled by environment variables or could be injected here
    # For now, simplistic override is fine but config.py is source of truth
    if args.port: os.environ["SERVER_PORT"] = str(args.port)
    if args.host: os.environ["SERVER_HOST"] = args.host
    if args.camera: os.environ["CAMERA_SOURCES"] = args.camera
    if args.device: os.environ["DEVICE"] = args.device
    
    config = Config()
    
    print("\n" + "=" * 60)
    print("  SECURE EDGE VISION SYSTEM")
    print("=" * 60)
    print(f"\n  Cameras: {config.camera_sources}")
    print(f"  Device: {config.device}")
    print(f"  Dashboard: http://localhost:{config.server_port}")
    print("\n  Press Ctrl+C to stop\n")
    
    uvicorn.run(
        app, 
        host=config.server_host, 
        port=config.server_port, 
        log_level="info",
        timeout_graceful_shutdown=2  # Fast shutdown even with active connections
    )


if __name__ == "__main__":
    main()
