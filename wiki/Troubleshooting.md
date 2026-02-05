# 🔧 Troubleshooting Guide

_Panduan mengatasi masalah umum di SECURE EDGE VISION SYSTEM_

---

## 📋 Daftar Isi

1. [Camera Issues](#-camera-issues)
2. [GPU/CUDA Issues](#-gpucuda-issues)
3. [Performance Issues](#-performance-issues)
4. [Recording Issues](#-recording-issues)
5. [Encryption Issues](#-encryption-issues)
6. [Web Dashboard Issues](#-web-dashboard-issues)
7. [Installation Issues](#-installation-issues)
8. [Error Messages Reference](#-error-messages-reference)

---

## 📹 Camera Issues

### Camera Not Detected

**Symptoms:**

```
No cameras found!
Cannot open camera
```

**Solutions:**

1. **Check physical connection:**

   ```bash
   # Windows: Device Manager → Cameras
   # Linux:
   ls /dev/video*
   v4l2-ctl --list-devices
   ```

2. **Test with OpenCV:**

   ```bash
   python tools/camera_selector.py --list
   ```

3. **Try different index:**

   ```bash
   python tools/camera_selector.py --test 0
   python tools/camera_selector.py --test 1
   python tools/camera_selector.py --test 2
   ```

4. **Install camera drivers:**

   ```bash
   # Linux
   sudo apt install v4l-utils

   # Windows: Download from manufacturer
   ```

### RTSP Camera Not Connecting

**Symptoms:**

```
[Cam 0] Connection failed, retrying in 5s...
Cannot open camera
```

**Solutions:**

1. **Verify RTSP URL format:**

   ```
   rtsp://username:password@ip_address:port/stream_path

   Examples:
   rtsp://admin:admin123@192.168.1.100:554/stream1
   rtsp://admin:admin123@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0
   ```

2. **Test with VLC first:**

   ```bash
   vlc rtsp://admin:password@192.168.1.100:554/stream1
   ```

3. **Check network connectivity:**

   ```bash
   ping 192.168.1.100
   telnet 192.168.1.100 554
   ```

4. **Try different stream path:**
   - Hikvision: `/Streaming/Channels/101`
   - Dahua: `/cam/realmonitor?channel=1&subtype=0`
   - Generic: `/stream1`, `/live`, `/h264`

5. **Check firewall:**

   ```bash
   # Linux
   sudo ufw allow 554/tcp

   # Windows: Windows Defender Firewall
   ```

### Camera Lag/Delay

**Symptoms:**

- Video stream delays 2-5 seconds
- High latency in dashboard

**Solutions:**

1. **Reduce buffer size (already done in code):**

   ```python
   cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
   ```

2. **Use TCP for RTSP:**

   ```bash
   # Environment variable (automatic)
   OPENCV_FFMPEG_CAPTURE_OPTIONS="rtsp_transport;tcp"
   ```

3. **Lower resolution:**
   - Configure camera to output 720p instead of 1080p

4. **Use substream:**
   ```
   # Instead of main stream
   rtsp://admin:pass@192.168.1.100:554/stream2
   ```

### Camera Keeps Reconnecting

**Symptoms:**

```
[Cam 0] Feed lost or read error
[Cam 0] Attempting to connect...
```

**Solutions:**

1. **Check cable/WiFi stability**

2. **Increase timeout:**
   - Check camera power supply
   - Use wired connection instead of WiFi

3. **Check camera settings:**
   - Disable "auto-disconnect idle"
   - Enable "keep alive"

---

## 🎮 GPU/CUDA Issues

### CUDA Not Available

**Symptoms:**

```
CUDA not available
Using CPU instead
```

**Solutions:**

1. **Check CUDA installation:**

   ```bash
   nvidia-smi
   nvcc --version
   ```

2. **Check PyTorch CUDA:**

   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.version.cuda)
   ```

3. **Reinstall PyTorch with CUDA:**

   ```bash
   pip uninstall torch torchvision
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

4. **Match CUDA versions:**
   - NVIDIA Driver → CUDA Toolkit → PyTorch CUDA
   - Check compatibility: https://pytorch.org/get-started/locally/

### GPU Out of Memory

**Symptoms:**

```
CUDA out of memory
RuntimeError: CUDA error: out of memory
```

**Solutions:**

1. **Use CPU mode:**

   ```env
   DEVICE=cpu
   ```

2. **Reduce batch/resolution:**

   ```env
   TARGET_FPS=15
   ```

3. **Close other GPU applications**

4. **Use smaller model:**
   - YOLOv8n instead of YOLOv8s/m/l

### Slow GPU Performance

**Symptoms:**

- Low FPS despite having GPU
- GPU utilization low

**Solutions:**

1. **Update NVIDIA drivers:**

   ```bash
   # Check current version
   nvidia-smi

   # Update from NVIDIA website
   ```

2. **Enable GPU in settings:**

   ```env
   DEVICE=cuda
   ```

3. **Check power mode:**
   ```bash
   # Windows: NVIDIA Control Panel → Power Management → Prefer Maximum Performance
   # Linux:
   nvidia-smi -pm 1
   ```

---

## ⚡ Performance Issues

### Low FPS

**Symptoms:**

- FPS below 20
- Choppy video stream

**Solutions:**

1. **Enable GPU:**

   ```env
   DEVICE=cuda
   ```

2. **Lower confidence threshold:**

   ```env
   DETECTION_CONFIDENCE=0.4
   ```

3. **Reduce resolution:**
   - Set camera to 720p

4. **Use selective recording:**

   ```env
   EVIDENCE_DETECTION_ONLY=True
   ```

5. **Check background processes:**
   ```bash
   # Windows: Task Manager
   # Linux: htop
   ```

### High CPU Usage

**Symptoms:**

- 100% CPU usage
- System slowdown

**Solutions:**

1. **Use GPU for detection:**

   ```env
   DEVICE=cuda
   ```

2. **Reduce number of cameras:**

   ```env
   CAMERA_SOURCES=0  # Instead of 0,1,2
   ```

3. **Lower target FPS:**
   ```env
   TARGET_FPS=15
   ```

### Stream Freezes During Recording

**Symptoms:**

- Video freezes every 5 minutes
- Lag when file rotates

**Solutions:**

This issue has been **FIXED** in the latest version!

The fix implements:

1. Background thread for file finalization
2. Non-blocking VideoWriter rotation
3. Async evidence encryption

If still experiencing issues:

```bash
# Update to latest version
git pull origin main
```

---

## 💾 Recording Issues

### Recordings Not Saving

**Symptoms:**

- No files in `recordings/public/`
- Empty recordings directory

**Solutions:**

1. **Check directory permissions:**

   ```bash
   # Linux
   chmod 755 recordings/

   # Windows: Run as Administrator
   ```

2. **Check disk space:**

   ```bash
   df -h  # Linux
   ```

3. **Verify configuration:**

   ```env
   PUBLIC_RECORDINGS_PATH=recordings/public
   EVIDENCE_RECORDINGS_PATH=recordings/evidence
   ```

4. **Check logs for errors:**
   ```bash
   # Look for codec errors
   OpenCV: Using codec MJPG for ...
   ```

### Video Codec Issues

**Symptoms:**

```
Failed to load OpenH264 library: openh264-1.8.0-win64.dll
[libopenh264] Incorrect library version loaded
OpenCV: Using codec MJPG for ... (fallback)
Videos only play in VLC, not browser
```

**Solutions:**

1. **Automatic Fix (Recommended):**

   ```bash
   python fix_openh264.py
   ```

   This will:
   - Download the correct OpenH264 library (v2.4.1)
   - Install it in the OpenCV directory
   - Test if the codec works

2. **Manual Download:**
   - Visit: https://github.com/cisco/openh264/releases
   - Download: `openh264-2.4.1-win64.dll.bz2` (Windows 64-bit)
   - Extract the DLL file
   - Copy to: `<Python>\Lib\site-packages\cv2\` directory

3. **Install FFmpeg (Alternative):**

   ```bash
   # Windows (winget)
   winget install ffmpeg

   # Linux
   sudo apt install ffmpeg

   # macOS
   brew install ffmpeg
   ```

4. **Verify H264 support:**

   ```python
   import cv2
   fourcc = cv2.VideoWriter_fourcc(*'avc1')
   # If returns 0, H264 not available
   ```

5. **System Already Works with Fallback:**
   If you see messages like:
   ```
   INFO:modules.recorder:[public_cam0] Recording: public_cam0_20260205_232014.mp4 (codec: avc1)
   ```
   Your system is already using the `avc1` codec successfully! The OpenH264 warnings can be safely ignored.
   The system automatically falls back to working codecs.

### Evidence Files Too Large

**Symptoms:**

- Evidence files are 100MB+ for 5 minutes
- Disk filling up quickly

**Solutions:**

1. **Enable selective recording:**

   ```env
   EVIDENCE_DETECTION_ONLY=True
   ```

2. **Lower JPEG quality:**

   ```env
   EVIDENCE_JPEG_QUALITY=60
   ```

3. **Reduce recording duration:**

   ```env
   RECORDING_DURATION_SECONDS=180
   ```

4. **Setup automatic cleanup:**
   ```env
   MAX_STORAGE_GB=50
   ```

---

## 🔐 Encryption Issues

### Key Not Found

**Symptoms:**

```
❌ Key not found: keys/master.key
```

**Solutions:**

1. **Generate new key:**

   ```bash
   python tools/key_manager.py --generate
   ```

2. **Restore from backup:**
   ```bash
   python tools/key_manager.py --restore keys/backups/master_20240115.key
   ```

### Cannot Decrypt Evidence

**Symptoms:**

```
❌ DECRYPTION FAILED!
Decryption failed - evidence may have been tampered with
```

**Solutions:**

1. **Use correct key:**

   ```bash
   python tools/decryptor.py -f evidence.enc --key correct/path/master.key
   ```

2. **For hybrid-encrypted files, use private key:**

   ```bash
   python tools/decryptor.py -f evidence.enc --private-key keys/rsa_private.pem
   ```

3. **Verify file isn't corrupted:**
   ```bash
   python tools/verify_integrity.py --verify evidence.enc
   ```

### Lost Encryption Key

**⚠️ WARNING: Without the key, encrypted evidence CANNOT be recovered!**

**Prevention:**

```bash
# Always backup keys immediately after generation
python tools/key_manager.py --backup

# Store backups in multiple secure locations:
# - USB drive in safe
# - Encrypted cloud storage
# - Paper printout (for emergencies)
```

---

## 🌐 Web Dashboard Issues

### Dashboard Not Loading

**Symptoms:**

- `http://localhost:8000` shows error
- Connection refused

**Solutions:**

1. **Check if server is running:**

   ```bash
   # Look for running process
   ps aux | grep python

   # Or check port
   netstat -an | grep 8000
   ```

2. **Check port configuration:**

   ```env
   SERVER_HOST=0.0.0.0
   SERVER_PORT=8000
   ```

3. **Try different port:**

   ```env
   SERVER_PORT=8080
   ```

4. **Check firewall:**

   ```bash
   # Linux
   sudo ufw allow 8000

   # Windows: Allow in Windows Firewall
   ```

### Stream Not Showing

**Symptoms:**

- Dashboard loads but no video
- Spinning loading indicator

**Solutions:**

1. **Check camera status in dashboard:**
   - Red indicator = Camera offline
   - Check console for errors

2. **Verify camera connection:**

   ```bash
   python tools/camera_selector.py --test 0
   ```

3. **Check browser console:**
   - Press F12 → Console tab
   - Look for errors

4. **Try different browser:**
   - Chrome recommended

### Port Already in Use

**Symptoms:**

```
ERROR: [Errno 98] Address already in use
ERROR: [Errno 10048] Only one usage of each socket address
```

**Solutions:**

1. **Use different port:**

   ```env
   SERVER_PORT=8080
   ```

2. **Kill existing process:**

   ```bash
   # Linux
   kill $(lsof -t -i:8000)

   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

---

## 📦 Installation Issues

### Module Not Found

**Symptoms:**

```
ModuleNotFoundError: No module named 'ultralytics'
ModuleNotFoundError: No module named 'cv2'
```

**Solutions:**

1. **Activate virtual environment:**

   ```bash
   # Windows
   venv\Scripts\activate

   # Linux/macOS
   source venv/bin/activate
   ```

2. **Install missing modules:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install specific module:**
   ```bash
   pip install ultralytics opencv-python
   ```

### PyTorch Installation Failed

**Symptoms:**

```
ERROR: Could not find a version that satisfies the requirement torch
```

**Solutions:**

1. **Check Python version (3.9-3.11 required):**

   ```bash
   python --version
   ```

2. **Install from official source:**

   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

3. **For CPU only:**
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   ```

---

## 📝 Error Messages Reference

| Error                | Cause                  | Solution                |
| :------------------- | :--------------------- | :---------------------- |
| `No cameras found`   | Camera not connected   | Check USB/connection    |
| `CUDA not available` | GPU not detected       | Install CUDA/use CPU    |
| `Out of memory`      | GPU VRAM full          | Use CPU or reduce load  |
| `Key not found`      | Missing encryption key | Generate key            |
| `Decryption failed`  | Wrong key or corrupted | Use correct key         |
| `Address in use`     | Port conflict          | Change port             |
| `Module not found`   | Missing dependency     | pip install             |
| `Feed lost`          | Camera disconnected    | Check connection        |
| `Codec fallback`     | Missing H264           | Install OpenH264/FFmpeg |

---

## 🆘 Getting More Help

### Collect Debug Information

```bash
# Save system info
python config.py --info > debug_info.txt

# Check logs
# Look at terminal output for errors
```

### Report Issue

Include the following when reporting issues:

1. **System info:** `python config.py --info`
2. **Configuration:** `.env` (redact passwords)
3. **Error message:** Full traceback
4. **Steps to reproduce**

---

## ➡️ Navigasi Wiki

| Sebelumnya        | Selanjutnya   |
| :---------------- | :------------ |
| [Tools](Tools.md) | [FAQ](FAQ.md) |
