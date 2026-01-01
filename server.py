"""
FastAPI Web Server
Provides MJPEG streaming, dashboard, and replay functionality
"""

import os
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional, AsyncGenerator
from datetime import datetime

import cv2
import numpy as np
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Secure Edge Vision System",
    description="Real-time video anonymization with dual-path architecture",
    version="1.0.0"
)

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Frame buffer for streaming
_latest_frame: Optional[np.ndarray] = None
_frame_timestamp: float = 0
_detection_count: int = 0
_fps: float = 0


def update_frame(frame: np.ndarray, detections: int = 0):
    """Update the latest frame for streaming"""
    global _latest_frame, _frame_timestamp, _detection_count
    _latest_frame = frame
    _frame_timestamp = time.time()
    _detection_count = detections


async def frame_generator() -> AsyncGenerator[bytes, None]:
    """Generate MJPEG stream frames"""
    global _latest_frame, _fps
    
    last_frame_time = 0
    frame_count = 0
    fps_start = time.time()
    
    while True:
        if _latest_frame is not None and _frame_timestamp > last_frame_time:
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', _latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            
            # MJPEG format
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            )
            
            last_frame_time = _frame_timestamp
            frame_count += 1
            
            # Calculate FPS
            elapsed = time.time() - fps_start
            if elapsed >= 1.0:
                _fps = frame_count / elapsed
                frame_count = 0
                fps_start = time.time()
        else:
            await asyncio.sleep(0.01)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Secure Edge Vision System",
            "camera_source": os.getenv("CAMERA_SOURCES", "0")
        }
    )


@app.get("/stream")
async def video_stream():
    """MJPEG video stream endpoint"""
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "running" if _latest_frame is not None else "waiting",
        "fps": round(_fps, 1),
        "detections": _detection_count,
        "last_update": _frame_timestamp,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/recordings")
async def list_recordings():
    """List public recordings"""
    public_dir = Path(os.getenv("PUBLIC_RECORDINGS_PATH", "recordings/public"))
    
    if not public_dir.exists():
        return {"recordings": []}
    
    recordings = []
    for f in sorted(public_dir.glob("*.mp4"), reverse=True):
        stat = f.stat()
        recordings.append({
            "filename": f.name,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "url": f"/replay/{f.name}"
        })
    
    return {"recordings": recordings}


@app.get("/api/evidence")
async def list_evidence():
    """List encrypted evidence files (metadata only)"""
    evidence_dir = Path(os.getenv("EVIDENCE_RECORDINGS_PATH", "recordings/evidence"))
    
    if not evidence_dir.exists():
        return {"evidence": []}
    
    evidence = []
    for f in sorted(evidence_dir.glob("*.enc"), reverse=True):
        stat = f.stat()
        evidence.append({
            "filename": f.name,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "status": "encrypted"
        })
    
    return {"evidence": evidence}


# ============ DECRYPTION ENDPOINTS ============

@app.get("/decrypt", response_class=HTMLResponse)
async def decrypt_page(request: Request):
    """Decryption dashboard page"""
    return templates.TemplateResponse("decrypt.html", {"request": request})


@app.get("/api/evidence-decrypt")
async def list_evidence_for_decrypt():
    """List encrypted evidence files with format detection"""
    from modules.security import HybridVault
    
    evidence_dir = Path(os.getenv("EVIDENCE_RECORDINGS_PATH", "recordings/evidence"))
    
    if not evidence_dir.exists():
        return {"evidence": []}
    
    evidence = []
    for f in sorted(evidence_dir.rglob("*.enc"), reverse=True):
        stat = f.stat()
        
        # Detect format
        is_hybrid = HybridVault.is_hybrid_format(str(f))
        
        evidence.append({
            "filename": f.name,
            "path": str(f),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
            "format": "hybrid" if is_hybrid else "symmetric"
        })
    
    return {"evidence": evidence}


from pydantic import BaseModel

class DecryptRequest(BaseModel):
    filename: str
    pin: Optional[str] = None
    show_boxes: bool = True  # Option to show/hide detection boxes


# Temporary storage for decrypted videos
_decrypted_cache = {}


@app.post("/api/decrypt")
async def decrypt_evidence(request: DecryptRequest):
    """Decrypt an evidence file and return video for preview"""
    import pickle
    import tempfile
    import uuid
    import hashlib
    from modules.security import SecureVault, HybridVault
    
    evidence_dir = Path(os.getenv("EVIDENCE_RECORDINGS_PATH", "recordings/evidence"))
    
    # Find file
    filepath = None
    for f in evidence_dir.rglob("*.enc"):
        if f.name == request.filename:
            filepath = f
            break
    
    if not filepath:
        raise HTTPException(status_code=404, detail="Evidence file not found")
    
    # Detect format and decrypt
    is_hybrid = HybridVault.is_hybrid_format(str(filepath))
    
    try:
        if is_hybrid:
            private_key_path = os.getenv("RSA_PRIVATE_KEY_PATH", "keys/rsa_private.pem")
            vault = HybridVault(private_key_path=private_key_path)
        else:
            key_path = os.getenv("ENCRYPTION_KEY_PATH", "keys/master.key")
            vault = SecureVault(key_path=key_path)
        
        data, metadata = vault.load_encrypted_file(str(filepath))
        
    except FileNotFoundError as e:
        if is_hybrid:
            raise HTTPException(status_code=400, detail="RSA private key not found. Please ensure keys/rsa_private.pem exists.")
        else:
            raise HTTPException(status_code=400, detail="Encryption key not found. Please ensure keys/master.key exists.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    # Deserialize frames
    try:
        frames_data = pickle.loads(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deserialize frames: {str(e)}")
    
    # Export to temp video
    video_id = str(uuid.uuid4())[:8]
    temp_dir = Path(tempfile.gettempdir()) / "secure_edge_decrypt"
    temp_dir.mkdir(exist_ok=True)
    temp_video_path = temp_dir / f"{video_id}.mp4"
    
    # Create video from frames
    if frames_data:
        try:
            # Get first frame to determine dimensions
            first_frame_data = frames_data[0]
            frame_key = "frame_jpg" if "frame_jpg" in first_frame_data else "frame"
            
            first_frame = cv2.imdecode(
                np.frombuffer(first_frame_data[frame_key], np.uint8),
                cv2.IMREAD_COLOR
            )
            h, w = first_frame.shape[:2]
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(str(temp_video_path), fourcc, 30, (w, h))
            
            for frame_data in frames_data:
                frame = cv2.imdecode(
                    np.frombuffer(frame_data[frame_key], np.uint8),
                    cv2.IMREAD_COLOR
                )
                
                # Draw detection boxes (if enabled)
                if request.show_boxes:
                    for det in frame_data.get("detections", []):
                        x1, y1 = det.get("x1", 0), det.get("y1", 0)
                        x2, y2 = det.get("x2", 0), det.get("y2", 0)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                writer.write(frame)
            
            writer.release()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create video: {str(e)}")
    
    # Cache video path
    _decrypted_cache[video_id] = str(temp_video_path)
    
    # Calculate duration
    frame_count = metadata.get("frame_count", len(frames_data))
    start_time = metadata.get("start_time", 0)
    end_time = metadata.get("end_time", 0)
    duration = end_time - start_time if end_time > start_time else frame_count / 30
    
    # Get hash for verification display
    data_hash = hashlib.sha256(data).hexdigest()
    
    return {
        "success": True,
        "frame_count": frame_count,
        "duration": duration,
        "hash": data_hash,
        "format": "hybrid" if is_hybrid else "symmetric",
        "video_url": f"/api/decrypt-video/{video_id}"
    }


@app.get("/api/decrypt-video/{video_id}")
async def serve_decrypted_video(video_id: str, download: int = 0):
    """Serve decrypted video from temp cache"""
    if video_id not in _decrypted_cache:
        raise HTTPException(status_code=404, detail="Video not found or expired")
    
    video_path = _decrypted_cache[video_id]
    
    if not Path(video_path).exists():
        del _decrypted_cache[video_id]
        raise HTTPException(status_code=404, detail="Video file not found")
    
    if download:
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=f"evidence_{video_id}.mp4"
        )
    
    return FileResponse(video_path, media_type="video/mp4")


@app.get("/replay/{filename}")
async def replay_recording(filename: str):
    """Serve a public recording file"""
    public_dir = Path(os.getenv("PUBLIC_RECORDINGS_PATH", "recordings/public"))
    filepath = public_dir / filename
    
    if not filepath.exists() or not filepath.suffix == ".mp4":
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return FileResponse(
        str(filepath),
        media_type="video/mp4",
        filename=filename
    )


@app.get("/replay-page/{filename}", response_class=HTMLResponse)
async def replay_page(request: Request, filename: str):
    """Replay page for a specific recording"""
    public_dir = Path(os.getenv("PUBLIC_RECORDINGS_PATH", "recordings/public"))
    filepath = public_dir / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return templates.TemplateResponse(
        "replay.html",
        {
            "request": request,
            "filename": filename,
            "video_url": f"/replay/{filename}"
        }
    )


# Background task to receive frames from main system
async def frame_receiver():
    """Receive frames from the main system queue"""
    from main import get_system
    
    system = get_system()
    
    while True:
        try:
            frame_data = system.get_latest_frame()
            if frame_data:
                update_frame(
                    frame_data.get("frame"),
                    frame_data.get("detections", 0)
                )
        except Exception as e:
            logger.error(f"Frame receiver error: {e}")
        
        await asyncio.sleep(0.01)


@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup"""
    # Note: Frame receiving is handled by main.py when run together
    logger.info("Web server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    logger.info("Web server shutting down")


# Standalone run for development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
