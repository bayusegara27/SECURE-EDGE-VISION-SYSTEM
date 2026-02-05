# 📦 Modules Documentation

*Dokumentasi teknis modul-modul Python SECURE EDGE VISION SYSTEM*

---

## 📋 Daftar Isi

1. [Overview](#-overview)
2. [modules/processor.py](#modulesprocessorpy)
3. [modules/engine.py](#modulesenginepy)
4. [modules/recorder.py](#modulesrecorderpy)
5. [modules/evidence.py](#modulesevidencepy)
6. [modules/security.py](#modulessecuritypy)
7. [modules/storage.py](#modulesstoragepy)
8. [modules/rsa_crypto.py](#modulesrsa_cryptopy)
9. [config.py](#configpy)

---

## 🔍 Overview

### Module Dependency Graph

```
                    ┌──────────────┐
                    │   main.py    │
                    │  (FastAPI)   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ config.py    │
                    │ (Settings)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐  ┌──▼───────┐  ┌▼───────────┐
       │  engine.py  │  │ tools/   │  │ templates/ │
       │ (Orchestr.) │  │ (CLI)    │  │ (HTML)     │
       └──────┬──────┘  └──────────┘  └────────────┘
              │
    ┌─────────┼─────────┬───────────┐
    │         │         │           │
┌───▼────┐ ┌──▼─────┐ ┌─▼──────┐ ┌──▼──────┐
│process.│ │record. │ │eviden. │ │storage. │
│py      │ │py      │ │py      │ │py       │
└───┬────┘ └────────┘ └───┬────┘ └─────────┘
    │                     │
┌───▼────┐           ┌────▼─────┐
│YOLOv8  │           │security. │
│(Extern)│           │py        │
└────────┘           └────┬─────┘
                          │
                    ┌─────▼──────┐
                    │rsa_crypto. │
                    │py (Hybrid) │
                    └────────────┘
```

---

## 📁 modules/processor.py

### Class: `FrameProcessor`

Frame processor untuk deteksi wajah dan blur real-time menggunakan YOLOv8.

#### Constructor

```python
FrameProcessor(
    model_path: str = "models/model.pt",
    device: str = "cuda",
    confidence: float = 0.5,
    iou: float = 0.45,
    blur_intensity: int = 51,
    tracker: str = "botsort",
    use_face_detection: bool = True
)
```

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `model_path` | str | `"models/model.pt"` | Path ke YOLOv8 model weights |
| `device` | str | `"cuda"` | Device untuk inference (`cuda` or `cpu`) |
| `confidence` | float | `0.5` | Minimum confidence threshold (0.0-1.0) |
| `iou` | float | `0.45` | IoU threshold for NMS/tracking (0.0-1.0) |
| `blur_intensity` | int | `51` | Gaussian blur kernel size (must be odd) |
| `tracker` | str | `"botsort"` | Tracking algorithm (`botsort` or `bytetrack`) |
| `use_face_detection` | bool | `True` | Compatibility flag |

#### Methods

##### `load_model() -> bool`
Load YOLOv8 model ke memory dan GPU.

```python
processor = FrameProcessor(device="cuda")
success = processor.load_model()
# Returns: True if model loaded successfully
```

##### `process(frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[dict]]`
Process satu frame: deteksi wajah dan apply blur.

```python
blurred, raw, detections = processor.process(frame)
# blurred: Frame dengan wajah ter-blur
# raw: Frame original (untuk evidence)
# detections: List of detected faces [{x1, y1, x2, y2, confidence}, ...]
```

##### `get_info() -> dict`
Get processor information.

```python
info = processor.get_info()
# Returns: {
#     "model": "models/model.pt",
#     "is_face_model": True,
#     "device": "cuda",
#     "confidence": 0.5,
#     "iou": 0.45,
#     "blur_intensity": 51,
#     "tracker": "botsort",
#     "is_loaded": True
# }
```

#### Internal Methods

| Method | Description |
|:-------|:------------|
| `_detect_faces(frame)` | Run YOLOv8 inference |
| `_apply_blur(frame, faces)` | Apply Gaussian blur ke face regions |

---

## 📁 modules/engine.py

### Class: `EdgeVisionSystem`

Main system orchestrator - koordinasi semua komponen untuk multiple cameras.

#### Constructor

```python
EdgeVisionSystem(config: Optional[Config] = None)
```

#### Attributes

| Attribute | Type | Description |
|:----------|:-----|:------------|
| `processor` | FrameProcessor | Shared AI processor |
| `caps` | Dict[int, VideoCapture] | Camera captures per index |
| `public_recorders` | Dict[int, VideoRecorder] | Public MP4 recorders |
| `evidence_managers` | Dict[int, EvidenceManager] | Evidence managers |
| `latest_frames` | Dict[int, np.ndarray] | Latest frames for streaming |
| `camera_status` | Dict[int, str] | Status per camera |

#### Methods

##### `start() -> None`
Initialize semua komponen dan metadata.

```python
system = EdgeVisionSystem()
system.start()  # Initialize cameras, AI, recorders
```

##### `process_frame(camera_idx: int) -> bool`
Process satu frame dari camera tertentu.

```python
success = system.process_frame(0)  # Process frame from camera 0
# Returns: False if read fails
```

##### `get_frame(camera_idx: int) -> Tuple[np.ndarray, int, float]`
Get latest frame untuk streaming.

```python
frame, detections, fps = system.get_frame(0)
# Returns: (frame, detection_count, current_fps)
```

##### `stop() -> None`
Stop semua komponen gracefully.

### Function: `processing_loop(camera_idx: int)`

Background processing loop dengan auto-reconnect logic.

```python
import threading
thread = threading.Thread(target=processing_loop, args=(0,), daemon=True)
thread.start()
```

### Function: `get_system() -> EdgeVisionSystem`

Get or create singleton system instance.

```python
system = get_system()  # Returns global instance
```

---

## 📁 modules/recorder.py

### Class: `VideoRecorder`

Public video recorder menggunakan OpenCV VideoWriter.

#### Constructor

```python
VideoRecorder(
    output_dir: str,
    prefix: str = "recording",
    fps: int = 30,
    max_duration: int = 300,
    resolution: tuple = (1280, 720)
)
```

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `output_dir` | str | - | Output directory path |
| `prefix` | str | `"recording"` | Filename prefix |
| `fps` | int | `30` | Frames per second |
| `max_duration` | int | `300` | Max seconds before rotation |
| `resolution` | tuple | `(1280, 720)` | Video resolution |

#### Methods

##### `write(frame: np.ndarray, detections: List = None) -> None`
Write frame ke video file.

```python
recorder = VideoRecorder("recordings/public")
recorder.write(blurred_frame, detections=[...])
```

##### `close() -> None`
Close current video file.

```python
recorder.close()  # Finalize current MP4
```

#### File Naming

```
{prefix}_{timestamp}.mp4
Example: public_cam0_20240115_143000.mp4
```

> **Note**: Timestamp format adalah `YYYYMMDD_HHMMSS`. File bisa berekstensi `.mp4` atau `.avi` tergantung codec yang tersedia.

---

## 📁 modules/evidence.py

### Class: `EvidenceManager`

Manages encrypted evidence storage dengan buffering dan selective recording.

#### Constructor

```python
EvidenceManager(
    output_dir: str,
    key_path: str = "keys/master.key",
    max_duration: int = 300,
    prefix: str = "cam0",
    detection_only: bool = True,
    jpeg_quality: int = 75
)
```

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `output_dir` | str | - | Output directory for .enc files |
| `key_path` | str | `"keys/master.key"` | Path to encryption key |
| `max_duration` | int | `300` | Seconds before auto-flush |
| `prefix` | str | `"cam0"` | Filename prefix |
| `detection_only` | bool | `True` | Only save frames with detections |
| `jpeg_quality` | int | `75` | JPEG compression quality |

#### Methods

##### `add_frame(frame, detections, timestamp=None, sync_timestamp=None) -> None`
Add frame ke buffer dengan optional selective recording.

```python
manager = EvidenceManager("recordings/evidence")
manager.add_frame(raw_frame, detections, sync_timestamp="20240115_143000")
```

##### `flush(blocking: bool = False) -> Optional[str]`
Encrypt dan save buffer ke file.

```python
filepath = manager.flush(blocking=True)  # Blocking
manager.flush()  # Non-blocking (default)
```

##### `close() -> None`
Flush remaining buffer dan close.

##### `get_evidence_list() -> List[dict]`
Get list of evidence files.

```python
files = manager.get_evidence_list()
# Returns: [{filename, path, size_mb, created, status}, ...]
```

#### Selective Recording Flow

```
Frame arrives
     │
     ├─── No detection ───► Add to pre_roll buffer (30 frames)
     │                            │
     │                      Buffer full? ► Remove oldest
     │
     └─── Detection found ───► Include pre_roll + frame
                                      │
                               Add to main buffer
                                      │
                               Duration > 5 min? ► Flush
```

---

## 📁 modules/security.py

### Class: `SecureVault`

AES-256-GCM encryption vault untuk forensic evidence.

#### Constructor

```python
SecureVault(
    key: Optional[bytes] = None,
    key_path: Optional[str] = None
)
```

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `key` | bytes | Raw 32-byte encryption key |
| `key_path` | str | Path to key file (will create if not exists) |

#### Class Constants

| Constant | Value | Description |
|:---------|:------|:------------|
| `NONCE_SIZE` | 12 | GCM nonce size in bytes |
| `KEY_SIZE` | 32 | AES-256 key size in bytes |
| `SALT_SIZE` | 16 | PBKDF2 salt size |

#### Methods

##### `lock_evidence(raw_bytes, metadata=None) -> EncryptedPackage`
Encrypt evidence dengan integrity protection.

```python
vault = SecureVault(key_path="keys/master.key")
package = vault.lock_evidence(data, {"camera": "cam0"})
# Returns: EncryptedPackage(nonce, ciphertext, original_hash, timestamp, metadata)
```

##### `unlock_evidence(package) -> Tuple[bytes, str]`
Decrypt dan verify integrity.

```python
data, hash = vault.unlock_evidence(package)
# Raises ValueError if tampered
```

##### `save_encrypted_file(data, output_path, metadata=None) -> None`
Encrypt dan save ke file.

```python
vault.save_encrypted_file(data, "evidence.enc", {"frames": 6000})
```

##### `load_encrypted_file(input_path) -> Tuple[bytes, dict]`
Load dan decrypt file.

```python
data, metadata = vault.load_encrypted_file("evidence.enc")
```

### Class: `EncryptedPackage`

Data class untuk encrypted package.

```python
@dataclass
class EncryptedPackage:
    nonce: bytes          # 12 bytes
    ciphertext: bytes     # Encrypted payload + auth tag
    original_hash: str    # SHA-256 hex string
    timestamp: float      # Unix timestamp
    metadata: dict        # Additional info
```

### Class: `HybridVault`

Hybrid RSA+AES encryption vault.

#### Constructor

```python
HybridVault(
    public_key_path: Optional[str] = None,
    private_key_path: Optional[str] = None,
    private_key_password: Optional[str] = None
)
```

#### Methods

##### `lock_evidence(raw_bytes, metadata=None) -> bytes`
Encrypt dengan hybrid RSA+AES.

##### `unlock_evidence(encrypted_data) -> Tuple[bytes, dict]`
Decrypt hybrid encrypted data.

##### `is_hybrid_format(filepath) -> bool`
Check if file is hybrid encrypted format.

### Helper Functions

```python
# Create vault from environment
vault = create_vault_from_env()

# Create hybrid vault
hybrid = create_hybrid_vault_from_env(for_encryption=True)
```

---

## 📁 modules/storage.py

### Classes

#### `RecordingConfig`
Dataclass for recording configuration.

```python
@dataclass
class RecordingConfig:
    output_dir: str
    max_duration_seconds: int = 300  # 5 minutes
    max_size_mb: int = 100
    fps: int = 30
    resolution: tuple = (1280, 720)
```

#### `PublicRecorder`
Records blurred video to MP4 files with automatic rotation.

#### `EvidenceRecorder`
Records encrypted evidence (raw frames) using Hybrid RSA+AES encryption.

#### `StorageManager`
Manages both public and evidence storage with background processes.

### Functions

#### `get_recording_list(directory: str) -> List[dict]`
Get list of recordings in directory.

```python
recordings = get_recording_list("recordings/public")
# Returns: [{filename, path, size_mb, created}, ...]
```

#### `cleanup_storage(public_path, evidence_path, max_gb) -> int`
Enforce storage retention policy (FIFO). Deletes oldest files when total exceeds limit.

```python
total_bytes = cleanup_storage(
    "recordings/public",
    "recordings/evidence",
    max_gb=50
)
```

---

## 📁 modules/rsa_crypto.py

### Functions

#### `generate_rsa_keypair(key_size=2048) -> Tuple[PrivateKey, PublicKey]`
Generate RSA key pair.

```python
private_key, public_key = generate_rsa_keypair()
```

#### `save_private_key(key, path, password=None)`
Save private key to PEM file.

#### `save_public_key(key, path)`
Save public key to PEM file.

#### `load_private_key(path, password=None) -> PrivateKey`
Load private key from PEM file.

#### `load_public_key(path) -> PublicKey`
Load public key from PEM file.

#### `encrypt_session_key(session_key, public_key) -> bytes`
Encrypt session key dengan RSA-OAEP.

#### `decrypt_session_key(encrypted_key, private_key) -> bytes`
Decrypt session key dengan RSA-OAEP.

#### `get_key_fingerprint(public_key) -> str`
Get SHA-256 fingerprint of public key.

---

## 📁 config.py

### Class: `Config`

System configuration from environment variables with preset support.

#### Constructor

```python
Config(preset_id: Optional[int] = None)
```

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `preset_id` | int | `None` | Override preset ID (1 or 2). If None, reads from `DETECTION_PRESET` env var |

#### Attributes

| Attribute | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `preset_id` | int | `1` | Active preset ID |
| `preset_name` | str | - | Human-readable preset name |
| `detector` | str | `"yolov8n-face"` | Detector model from preset |
| `tracker` | str | `"botsort"` | Tracker algorithm from preset |
| `camera_sources` | List | `[0]` | Camera sources |
| `device` | str | `"cuda"` | AI device |
| `model_path` | str | `"models/model.pt"` | Model path |
| `confidence` | float | `0.35` | Detection confidence (from preset) |
| `iou` | float | `0.45` | IoU threshold (from preset) |
| `blur_intensity` | int | `51` | Blur kernel size |
| `server_host` | str | `"0.0.0.0"` | Server bind host |
| `server_port` | int | `8000` | Server port |
| `public_path` | str | `"recordings/public"` | Public recordings path |
| `evidence_path` | str | `"recordings/evidence"` | Evidence path |
| `key_path` | str | `"keys/master.key"` | Encryption key path |
| `target_fps` | int | `30` | Target FPS |
| `max_duration` | int | `300` | Max recording duration |
| `evidence_detection_only` | bool | `True` | Selective recording |
| `evidence_quality` | int | `75` | JPEG quality |
| `max_storage_gb` | int | `50` | Storage limit |
| `show_timestamp` | bool | `True` | Show timestamp overlay |
| `show_debug_overlay` | bool | `False` | Show debug overlay |

#### Methods

##### `get_preset_info() -> dict`
Get information about currently loaded preset.

```python
config = Config(preset_id=1)
info = config.get_preset_info()
# Returns: {
#     "preset_id": 1,
#     "preset_name": "Default (YOLOv8-Face + BoT-SORT)",
#     "detector": "yolov8n-face",
#     "tracker": "botsort",
#     "confidence": 0.35,
#     "iou": 0.45
# }
```

### Preset Functions

#### `load_presets(preset_file: str = "presets.yaml") -> Dict[int, Dict]`
Load detection presets from YAML file.

```python
presets = load_presets()
# Returns: {1: {...}, 2: {...}}
```

#### `get_preset(preset_id: int, presets: Optional[Dict] = None) -> Dict`
Get a specific preset by ID with fallback.

```python
preset = get_preset(1)
# Returns: {"name": "...", "detector": "...", "tracker": "...", ...}
```

### Other Functions

#### `validate_config() -> Tuple[bool, List[str]]`
Validate system configuration.

```python
is_valid, issues = validate_config()
```

#### `show_system_info()`
Display system information.

#### `create_default_env()`
Create default .env file if not exists.

---

## 📁 presets.yaml

### Structure

Detection presets are defined in `presets.yaml`:

```yaml
presets:
  1:
    name: "Default (YOLOv8-Face + BoT-SORT)"
    description: "Balanced preset for general surveillance use"
    detector: "yolov8n-face"
    tracker: "botsort"
    confidence: 0.35
    iou: 0.45

  2:
    name: "Alternative (YOLOv11-Face + ByteTrack)"
    description: "Experimental preset with newer detector and faster tracker"
    detector: "yolov11n-face"
    tracker: "bytetrack"
    confidence: 0.30
    iou: 0.50
```

### Usage

```bash
# CLI argument (priority)
python main.py --preset 2

# Environment variable
DETECTION_PRESET=2 python main.py

# In .env file
DETECTION_PRESET=2
```

---

## 📊 Module Statistics

| Module | Lines | Classes | Functions | Description |
|:-------|:------|:--------|:----------|:------------|
| `processor.py` | ~300 | 1 | 4 | AI detection & blur |
| `engine.py` | ~490 | 1 | 3 | System orchestrator |
| `recorder.py` | ~690 | 1 | 3 | Public recording |
| `evidence.py` | ~700 | 1 | 6 | Evidence management |
| `security.py` | ~670 | 4 | 10 | Cryptography |
| `storage.py` | ~480 | 0 | 4 | Storage utilities |
| `rsa_crypto.py` | ~250 | 0 | 8 | RSA operations |
| `config.py` | ~600 | 1 | 8 | Configuration + presets |

---

## ➡️ Navigasi Wiki

| Sebelumnya | Selanjutnya |
|:-----------|:------------|
| [Installation](Installation.md) | [API](API.md) |
