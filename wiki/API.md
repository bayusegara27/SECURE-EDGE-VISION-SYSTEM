# 🔌 API Documentation

*Dokumentasi lengkap API endpoints SECURE EDGE VISION SYSTEM*

---

## 📋 Daftar Isi

1. [Overview](#-overview)
2. [Base URL & Authentication](#-base-url--authentication)
3. [Dashboard Endpoints](#-dashboard-endpoints)
4. [Streaming Endpoints](#-streaming-endpoints)
5. [Gallery Endpoints](#-gallery-endpoints)
6. [Analytics Endpoints](#-analytics-endpoints)
7. [Decryption Endpoints](#-decryption-endpoints)
8. [System Endpoints](#-system-endpoints)

---

## 🔍 Overview

### Technology Stack

| Component | Technology |
|:----------|:-----------|
| **Framework** | FastAPI 0.104+ |
| **Server** | Uvicorn (ASGI) |
| **Streaming** | MJPEG over HTTP |
| **Templates** | Jinja2 |
| **Validation** | Pydantic |

### API Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  HTML Pages │  │  API Routes │  │  Static Files       │  │
│  │  (Jinja2)   │  │  (JSON)     │  │  (CSS/JS)           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Streaming Routes                      ││
│  │  /video_feed/{camera_id} ──► MJPEG StreamingResponse    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌐 Base URL & Authentication

### Base URL

```
http://localhost:8000
```

### Authentication

> **Catatan:** Sistem saat ini tidak memerlukan autentikasi untuk web interface.
> Untuk production, tambahkan authentication middleware.

```python
# Future: JWT Authentication
headers = {
    "Authorization": "Bearer <token>"
}
```

---

## 📊 Dashboard Endpoints

### GET `/`

Halaman utama dashboard dengan live streaming.

**Response:** HTML Page

**Features:**
- Multi-camera live stream
- Camera switching
- Detection counter
- FPS monitor

**Example:**
```
GET http://localhost:8000/
```

---

## 📹 Streaming Endpoints

### GET `/stream/{camera_idx}`

MJPEG live video stream untuk camera tertentu.

**Parameters:**

| Name | Type | Location | Required | Description |
|:-----|:-----|:---------|:---------|:------------|
| `camera_idx` | int | path | Yes | Camera index (0, 1, 2, ...) |

**Response:**
- Content-Type: `multipart/x-mixed-replace; boundary=frame`
- Body: Continuous MJPEG stream

**Example:**
```html
<img src="/stream/0" />
```

**Implementation:**
```python
@app.get("/stream/{camera_idx}")
async def video_stream(camera_idx: int):
    """MJPEG video stream for specific camera"""
    return StreamingResponse(
        generate_frames(camera_idx),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
```

### GET `/api/status`

Get full system status including all cameras.

**Response:**
```json
{
    "status": "running",
    "cameras": [
        {
            "id": 0,
            "fps": 28.5,
            "detections": 2,
            "source": "0",
            "state": "online"
        }
    ],
    "timestamp": "2024-01-15T14:30:00"
}
```

### GET `/api/cameras`

Get list of available cameras dan statusnya.

**Response:**
```json
{
    "cameras": [
        {
            "index": 0,
            "source": "0",
            "status": "online",
            "fps": 28.5,
            "detections": 2
        },
        {
            "index": 1,
            "source": "rtsp://192.168.1.100:554/stream",
            "status": "online",
            "fps": 25.0,
            "detections": 0
        }
    ]
}
```

---

## 🖼️ Gallery Endpoints

### GET `/gallery`

Halaman gallery untuk browse dan replay video recordings.

**Response:** HTML Page

**Features:**
- List recorded videos
- Date filter
- Video playback
- Search by filename

### GET `/api/recordings`

Get list of public recordings.

**Query Parameters:**

| Name | Type | Required | Default | Description |
|:-----|:-----|:---------|:--------|:------------|
| `date` | string | No | today | Filter by date (YYYY-MM-DD) |
| `camera` | string | No | all | Filter by camera prefix |
| `limit` | int | No | 50 | Max results |

**Response:**
```json
{
    "recordings": [
        {
            "filename": "public_cam0_20240115143000_0001.mp4",
            "path": "/recordings/public/public_cam0_20240115143000_0001.mp4",
            "size_mb": 52.3,
            "duration_sec": 300,
            "created": "2024-01-15T14:30:00",
            "camera": "cam0",
            "thumbnail": "/thumbnails/public_cam0_20240115143000_0001.jpg"
        }
    ],
    "total": 24,
    "date": "2024-01-15"
}
```

### GET `/recordings/public/{filename}`

Download atau stream video file.

**Parameters:**

| Name | Type | Location | Required | Description |
|:-----|:-----|:---------|:---------|:------------|
| `filename` | string | path | Yes | Video filename |

**Response:**
- Content-Type: `video/mp4`
- Body: Video file stream

**Example:**
```html
<video src="/recordings/public/public_cam0_20240115143000_0001.mp4" controls></video>
```

### GET `/api/recordings/search`

Search recordings by query.

**Query Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `q` | string | Yes | Search query |
| `from_date` | string | No | Start date (YYYY-MM-DD) |
| `to_date` | string | No | End date (YYYY-MM-DD) |

**Response:**
```json
{
    "results": [...],
    "query": "cam0",
    "count": 12
}
```

---

## 📈 Analytics Endpoints

### GET `/analytics`

Halaman analytics dengan charts dan statistics.

**Response:** HTML Page

**Features:**
- Storage usage chart
- Detection heatmap
- Activity timeline
- Camera statistics

### GET `/api/analytics/storage`

Get storage usage statistics.

**Response:**
```json
{
    "public": {
        "total_files": 156,
        "total_size_gb": 8.4,
        "oldest_file": "2024-01-10T08:00:00",
        "newest_file": "2024-01-15T14:30:00"
    },
    "evidence": {
        "total_files": 89,
        "total_size_gb": 24.2,
        "oldest_file": "2024-01-10T08:00:00",
        "newest_file": "2024-01-15T14:30:00"
    },
    "disk": {
        "total_gb": 512,
        "used_gb": 245,
        "free_gb": 267,
        "percent_used": 47.8
    },
    "prediction": {
        "days_until_full": 45,
        "daily_rate_gb": 5.8
    }
}
```

### GET `/api/analytics/detections`

Get detection statistics.

**Query Parameters:**

| Name | Type | Required | Default | Description |
|:-----|:-----|:---------|:--------|:------------|
| `days` | int | No | 7 | Number of days to analyze |
| `camera` | string | No | all | Filter by camera |

**Response:**
```json
{
    "daily_counts": [
        {"date": "2024-01-15", "count": 1234},
        {"date": "2024-01-14", "count": 1456},
        ...
    ],
    "hourly_heatmap": [
        {"hour": 0, "avg_count": 12},
        {"hour": 1, "avg_count": 8},
        ...
    ],
    "peak_hours": [9, 12, 17],
    "total_detections": 8956
}
```

### GET `/api/system/status`

Get system status dan health.

**Response:**
```json
{
    "status": "running",
    "uptime_seconds": 3600,
    "cameras": {
        "total": 3,
        "online": 3,
        "offline": 0
    },
    "ai": {
        "model": "YOLOv8-Face",
        "device": "cuda",
        "gpu_name": "NVIDIA GeForce RTX 3050",
        "gpu_memory_used_mb": 1234
    },
    "performance": {
        "avg_fps": 28.5,
        "avg_latency_ms": 35,
        "cpu_percent": 45,
        "ram_percent": 62
    },
    "storage": {
        "public_gb": 8.4,
        "evidence_gb": 24.2,
        "free_gb": 267
    }
}
```

---

## 🔐 Decryption Endpoints

### GET `/decrypt`

Halaman decryption interface untuk admin.

**Response:** HTML Page

**Features:**
- List encrypted evidence files
- Select file to decrypt
- Enter PIN/password
- Preview decrypted frames
- Download decrypted video

### GET `/api/evidence`

Get list of encrypted evidence files.

**Query Parameters:**

| Name | Type | Required | Default | Description |
|:-----|:-----|:---------|:--------|:------------|
| `date` | string | No | all | Filter by date |
| `camera` | string | No | all | Filter by camera |

**Response:**
```json
{
    "evidence": [
        {
            "filename": "evidence_cam0_20240115143000_0001.enc",
            "path": "recordings/evidence/cam0/evidence_cam0_20240115143000_0001.enc",
            "size_mb": 156.8,
            "created": "2024-01-15T14:35:00",
            "camera": "cam0",
            "metadata": {
                "frame_count": 6000,
                "start_time": 1705328400.0,
                "end_time": 1705328700.0,
                "total_detections": 1234
            },
            "matching_public": "public_cam0_20240115143000_0001.mp4"
        }
    ],
    "total": 89
}
```

### POST `/api/decrypt`

Decrypt evidence file.

**Request Body:**
```json
{
    "filename": "evidence_cam0_20240115143000_0001.enc",
    "pin": "1234"
}
```

**Response (Success):**
```json
{
    "success": true,
    "message": "Evidence decrypted successfully",
    "integrity": {
        "verified": true,
        "hash": "a3f5b8c9d2e1f4a7b6c5d8e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0"
    },
    "metadata": {
        "frame_count": 6000,
        "start_time": "2024-01-15T14:30:00",
        "end_time": "2024-01-15T14:35:00",
        "total_detections": 1234
    },
    "preview_url": "/api/decrypt/preview/abc123",
    "download_url": "/api/decrypt/download/abc123"
}
```

**Response (Error):**
```json
{
    "success": false,
    "error": "INTEGRITY_FAILED",
    "message": "Evidence integrity verification failed - file may have been tampered with"
}
```

### GET `/api/decrypt/preview/{session_id}`

Stream preview of decrypted evidence.

**Parameters:**

| Name | Type | Location | Required | Description |
|:-----|:-----|:---------|:---------|:------------|
| `session_id` | string | path | Yes | Decryption session ID |
| `frame` | int | query | No | Specific frame number |

**Response:**
- Content-Type: `image/jpeg`
- Body: JPEG frame

### GET `/api/decrypt/download/{session_id}`

Download decrypted evidence as video.

**Parameters:**

| Name | Type | Location | Required | Description |
|:-----|:-----|:---------|:---------|:------------|
| `session_id` | string | path | Yes | Decryption session ID |
| `format` | string | query | No | Output format (mp4, avi) |

**Response:**
- Content-Type: `video/mp4`
- Content-Disposition: `attachment; filename="decrypted_evidence.mp4"`

---

## ⚙️ System Endpoints

### GET `/api/config`

Get current system configuration.

**Response:**
```json
{
    "cameras": {
        "sources": ["0", "rtsp://192.168.1.100:554/stream"],
        "count": 2
    },
    "ai": {
        "model": "models/model.pt",
        "device": "cuda",
        "confidence": 0.5,
        "blur_intensity": 51
    },
    "recording": {
        "fps": 30,
        "duration_sec": 300,
        "detection_only": true,
        "jpeg_quality": 75
    },
    "storage": {
        "public_path": "recordings/public",
        "evidence_path": "recordings/evidence",
        "max_gb": 50
    }
}
```

### GET `/api/health`

Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T14:30:00Z",
    "version": "1.3.0"
}
```

### GET `/docs`

FastAPI auto-generated API documentation (Swagger UI).

### GET `/redoc`

FastAPI auto-generated API documentation (ReDoc).

---

## 📝 Error Responses

### Standard Error Format

```json
{
    "detail": {
        "error": "ERROR_CODE",
        "message": "Human readable error message",
        "timestamp": "2024-01-15T14:30:00Z"
    }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|:-----|:------------|:------------|
| `CAMERA_NOT_FOUND` | 404 | Camera index tidak valid |
| `FILE_NOT_FOUND` | 404 | File tidak ditemukan |
| `DECRYPTION_FAILED` | 400 | Decryption gagal (wrong key/PIN) |
| `INTEGRITY_FAILED` | 400 | File telah dimodifikasi |
| `INVALID_FORMAT` | 400 | Format file tidak valid |
| `UNAUTHORIZED` | 401 | Autentikasi diperlukan |
| `SERVER_ERROR` | 500 | Internal server error |

---

## 🧪 Testing API

### Using cURL

```bash
# Get cameras list
curl http://localhost:8000/api/cameras

# Get storage analytics
curl http://localhost:8000/api/analytics/storage

# Health check
curl http://localhost:8000/api/health
```

### Using Python requests

```python
import requests

# Get system status
response = requests.get("http://localhost:8000/api/system/status")
print(response.json())

# Decrypt evidence
response = requests.post(
    "http://localhost:8000/api/decrypt",
    json={
        "filename": "evidence_cam0_20240115143000_0001.enc",
        "pin": "1234"
    }
)
print(response.json())
```

---

## ➡️ Navigasi Wiki

| Sebelumnya | Selanjutnya |
|:-----------|:------------|
| [Modules](Modules.md) | [Performance](Performance.md) |
