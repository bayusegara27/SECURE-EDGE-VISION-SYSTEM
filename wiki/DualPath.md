# 🔀 Dual-Path Storage Mechanism

*Dokumentasi mekanisme penyimpanan dual-path: Public vs Evidence*

---

## 📋 Daftar Isi

1. [Konsep Dual-Path](#-konsep-dual-path)
2. [Public Path (Jalur Publik)](#-public-path-jalur-publik)
3. [Evidence Path (Jalur Forensik)](#-evidence-path-jalur-forensik)
4. [Perbandingan Kedua Jalur](#-perbandingan-kedua-jalur)
5. [Selective Recording](#-selective-recording)
6. [Storage Optimization](#-storage-optimization)
7. [Use Case Scenarios](#-use-case-scenarios)

---

## 🎯 Konsep Dual-Path

### Filosofi Desain

Sistem surveilans modern menghadapi dilema fundamental:

```
                    PRIVACY ◄────────────────► SECURITY
                    
    "Wajah harus                         "Investigator butuh
     dilindungi"                          identitas pelaku"
```

**Solusi: Dual-Path Architecture**

Menyimpan **dua versi** dari setiap rekaman secara simultan:
1. **Public Path**: Wajah ter-blur, dapat diakses semua staf
2. **Evidence Path**: Video asli terenkripsi, hanya admin

### Diagram Konsep

```
                         ┌──────────────────────────┐
                         │     Camera Frame         │
                         │     (1280x720 RGB)       │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │    YOLOv8 Detection      │
                         │    - Face bounding box   │
                         │    - Confidence score    │
                         └────────────┬─────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
      ┌─────────────────────────┐       ┌─────────────────────────┐
      │      PUBLIC PATH        │       │     EVIDENCE PATH       │
      │                         │       │                         │
      │  ┌─────────────────┐    │       │  ┌─────────────────┐    │
      │  │  Gaussian Blur  │    │       │  │  JPEG Encode    │    │
      │  │  (51x51 kernel) │    │       │  │  Quality: 75%   │    │
      │  └────────┬────────┘    │       │  └────────┬────────┘    │
      │           │             │       │           │             │
      │  ┌────────▼────────┐    │       │  ┌────────▼────────┐    │
      │  │  H.264 Encode   │    │       │  │  Buffer Frames  │    │
      │  │  VideoWriter    │    │       │  │  (6000 frames)  │    │
      │  └────────┬────────┘    │       │  └────────┬────────┘    │
      │           │             │       │           │             │
      │           ▼             │       │  ┌────────▼────────┐    │
      │  recordings/public/     │       │  │  AES-256-GCM    │    │
      │  public_cam0_*.mp4      │       │  │  Encrypt        │    │
      │                         │       │  └────────┬────────┘    │
      │  👁️ VISIBLE TO ALL      │       │           │             │
      │  🔓 NO KEY REQUIRED     │       │           ▼             │
      │                         │       │  recordings/evidence/   │
      │                         │       │  evidence_cam0_*.enc    │
      │                         │       │                         │
      │                         │       │  🔒 ENCRYPTED           │
      │                         │       │  🔑 KEY REQUIRED        │
      └─────────────────────────┘       └─────────────────────────┘
```

---

## 👁️ Public Path (Jalur Publik)

### Tujuan
- Monitoring harian oleh satpam/staf
- Replay kejadian biasa
- Memastikan **privasi terlindungi** untuk semua orang terekam

### Proses Teknis

```python
# modules/processor.py

def _apply_blur(self, frame: np.ndarray, faces: List[dict]) -> np.ndarray:
    """Apply Gaussian blur ke area wajah"""
    blurred = frame.copy()
    
    for face in faces:
        x1, y1, x2, y2 = face["x1"], face["y1"], face["x2"], face["y2"]
        
        # Add 15% padding untuk coverage lebih baik
        fw, fh = x2 - x1, y2 - y1
        pad_x = int(fw * 0.15)
        pad_y = int(fh * 0.15)
        
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w, x2 + pad_x)
        y2 = min(h, y2 + pad_y)
        
        # Gaussian Blur (51x51 kernel)
        roi = blurred[y1:y2, x1:x2]
        blurred_roi = cv2.GaussianBlur(
            roi,
            (self.blur_intensity, self.blur_intensity),  # 51x51
            0  # sigmaX (auto-calculated)
        )
        blurred[y1:y2, x1:x2] = blurred_roi
    
    return blurred
```

### Spesifikasi Output

| Parameter | Nilai | Keterangan |
|:----------|:------|:-----------|
| **Format** | MP4 (H.264) | Web-compatible, efficient compression |
| **Resolution** | 1280x720 (720p) | Balance quality vs storage |
| **FPS** | 30 fps | Standard surveillance framerate |
| **Blur Kernel** | 51x51 pixels | Completely obscures facial features |
| **File Rotation** | 5 menit | ~50 MB per file |
| **Storage Location** | `recordings/public/` | Accessible by all authorized staff |

### Filename Format

```
public_cam0_20240115123045_0001.mp4
│       │     │             │
│       │     │             └── Sequence number
│       │     └──────────────── Timestamp (YYYYMMDDHHmmss)
│       └────────────────────── Camera ID (cam0, cam1, rtsp)
└────────────────────────────── Prefix
```

### Mengapa Blur Tidak Bisa Di-Reverse?

**Gaussian Blur adalah operasi irreversible:**

```
Original Pixel Values:    [100, 150, 200, 180, 90]
                              │     │     │
                              └─────┼─────┘
                                    │
Kernel Average:           [    144     ]  ◄── Information LOST!

Setelah blur: tidak ada cara untuk mengetahui pixel mana yang 
bernilai 100, 150, 200, dll. Informasi sudah dihancurkan.
```

**Bukan DeepFake atau AI Enhancement:**
- AI "un-blur" tools hanya **hallucinate** (menebak) wajah
- Hasilnya BUKAN wajah asli, tapi generasi baru
- Tidak dapat digunakan untuk identifikasi legal

---

## 🔐 Evidence Path (Jalur Forensik)

### Tujuan
- Menyimpan video **ASLI** (tanpa blur) untuk investigasi
- Melindungi data dengan enkripsi kuat
- Memastikan **integritas forensik** (tidak dapat dimanipulasi)

### Proses Teknis

```python
# modules/evidence.py

def add_frame(self, frame: np.ndarray, detections: List[dict], ...):
    """Add frame ke buffer dengan metadata"""
    
    # 1. Encode frame sebagai JPEG
    _, encoded = cv2.imencode(
        '.jpg', 
        frame, 
        [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]  # 75%
    )
    
    # 2. Create frame data structure
    frame_data = {
        "frame_jpg": encoded.tobytes(),
        "detections": detections,
        "timestamp": timestamp
    }
    
    # 3. Add to buffer
    self.buffer.append(frame_data)
    
    # 4. Auto-flush when duration exceeded
    if (timestamp - self.buffer_start) >= self.max_duration:
        self.flush()

def flush(self, blocking: bool = True):
    """Encrypt and save buffer to file"""
    
    # 1. Serialize buffer
    data = pickle.dumps(self.buffer)
    
    # 2. Create metadata
    metadata = {
        "frame_count": len(self.buffer),
        "start_time": self.buffer_start,
        "end_time": self.buffer[-1]["timestamp"],
        "total_detections": sum(len(f["detections"]) for f in self.buffer)
    }
    
    # 3. Encrypt and save
    self.vault.save_encrypted_file(data, str(filepath), metadata)
```

### Spesifikasi Output

| Parameter | Nilai | Keterangan |
|:----------|:------|:-----------|
| **Format** | Custom binary (.enc) | Proprietary encrypted format |
| **Frame Compression** | JPEG 75% | Balance quality vs size |
| **Encryption** | AES-256-GCM | NIST-approved authenticated encryption |
| **Integrity** | SHA-256 hash | Embedded inside ciphertext |
| **File Rotation** | 5 menit / 6000 frames | ~300 MB per file (typical) |
| **Storage Location** | `recordings/evidence/{camera}/` | Admin access only |

### Filename Format

```
evidence_cam0_20240115123045_0001.enc
│         │     │             │
│         │     │             └── Sequence number
│         │     └──────────────── Timestamp (synced with public)
│         └────────────────────── Camera ID
└──────────────────────────────── Prefix
```

### File Synchronization

Public dan Evidence files memiliki **timestamp yang sama** untuk memudahkan matching:

```
Public:   public_cam0_20240115123045_0001.mp4
Evidence: evidence_cam0_20240115123045_0001.enc
                     └───────────────────┘
                      Same timestamp = Same recording session
```

---

## ⚖️ Perbandingan Kedua Jalur

| Aspek | Public Path | Evidence Path |
|:------|:------------|:--------------|
| **Privasi Wajah** | ✅ Terlindungi (blur) | ❌ Terlihat (raw) |
| **Enkripsi** | ❌ Tidak | ✅ AES-256-GCM |
| **Akses** | Semua staf | Admin + Key only |
| **Format** | MP4 (H.264) | Custom .enc |
| **Use Case** | Monitoring harian | Investigasi kriminal |
| **Playback** | Browser/VLC | Custom decryptor tool |
| **Storage Size** | ~100 MB/5min | ~300 MB/5min |
| **Legal Status** | Non-evidence | Forensic evidence |

### Visual Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                        SAME SCENE                                │
├──────────────────────────────┬──────────────────────────────────┤
│        PUBLIC VERSION        │        EVIDENCE VERSION          │
│                              │                                  │
│    ┌────────────────────┐    │    ┌────────────────────┐        │
│    │                    │    │    │                    │        │
│    │    ┌──────────┐    │    │    │    ┌──────────┐    │        │
│    │    │ ▓▓▓▓▓▓▓▓ │ ◄──┼────┼────┤    │  WAJAH   │    │        │
│    │    │ ▓▓▓▓▓▓▓▓ │    │    │    │  (Terlihat) │    │        │
│    │    │ ▓▓▓▓▓▓▓▓ │    │    │    │             │    │        │
│    │    └──────────┘    │    │    └──────────┘    │        │
│    │      BLURRED       │    │      CLEAR        │        │
│    │                    │    │                    │        │
│    └────────────────────┘    │    └────────────────────┘        │
│                              │                                  │
│    📂 public_cam0_*.mp4      │    🔒 evidence_cam0_*.enc        │
│    🔓 No password needed     │    🔑 Requires decryption key    │
│                              │                                  │
└──────────────────────────────┴──────────────────────────────────┘
```

---

## 🎯 Selective Recording

### Konsep

Alih-alih merekam SEMUA frame ke evidence (yang akan menghabiskan storage), sistem hanya merekam frame yang **mengandung deteksi wajah**.

### Manfaat

| Metrik | Tanpa Selective | Dengan Selective | Penghematan |
|:-------|:----------------|:-----------------|:------------|
| **Storage/jam** | ~15 GB | ~3 GB | **80%** |
| **File Count** | Continuous | Event-based | Lebih sedikit |
| **Review Time** | Scan semua | Langsung ke event | Lebih cepat |

### Implementation

```python
# modules/evidence.py

def add_frame(self, frame, detections, ...):
    """Selective recording dengan pre-roll buffer"""
    
    if self.detection_only:
        if not detections:
            # NO DETECTION: Add to pre-roll only
            self.pre_roll.append(frame_data)
            if len(self.pre_roll) > self.pre_roll_size:  # 30 frames
                self.pre_roll.pop(0)
            
            # Don't save to main buffer
            if not self.buffer:
                return
        else:
            # DETECTION FOUND!
            # If this is start of new event, include pre-roll
            if not self.buffer:
                self.buffer.extend(self.pre_roll)
                self.pre_roll = []
```

### Pre-Roll Buffer

Untuk memberikan **konteks sebelum deteksi**, sistem menyimpan 30 frame (~1 detik) di circular buffer:

```
Timeline:
    
    [No Detection] [No Detection] [No Detection] [DETECTION!] [Detection] ...
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                     PRE-ROLL (30 frames)
                           │
                           ▼
              Included when detection starts
```

**Manfaat:**
- Melihat apa yang terjadi SEBELUM wajah terdeteksi
- Tidak kehilangan momen penting
- Overhead minimal (hanya 30 frames di memory)

---

## 💾 Storage Optimization

### FIFO Cleanup Policy

Ketika storage hampir penuh, sistem otomatis menghapus file tertua:

```python
# modules/storage.py

def cleanup_old_files(directory: Path, max_gb: float):
    """Delete oldest files when storage > 90% of limit"""
    
    files = sorted(directory.glob("*.*"), key=lambda f: f.stat().st_mtime)
    total_size = sum(f.stat().st_size for f in files)
    
    limit_bytes = max_gb * 1024 * 1024 * 1024
    target_bytes = limit_bytes * 0.9  # Keep 10% buffer
    
    while total_size > target_bytes and files:
        oldest = files.pop(0)
        size = oldest.stat().st_size
        oldest.unlink()
        total_size -= size
        logger.info(f"Deleted old file: {oldest.name}")
```

### Storage Estimation

**Asumsi:**
- 1 kamera @ 720p @ 30fps
- 8 jam/hari monitoring
- Deteksi rate ~20%

```
Public Path:
  30fps × 8jam × 3600s = 864,000 frames
  Setelah H.264 compression: ~100 MB / 5 menit
  Total: ~9.6 GB / hari / kamera

Evidence Path (dengan Selective Recording):
  20% detection rate × 864,000 = 172,800 frames
  JPEG 75% × metadata: ~300 MB / 5 menit active
  Total: ~2 GB / hari / kamera (80% saving!)

Combined (3 kamera):
  (9.6 + 2) × 3 = ~35 GB / hari
```

### Recommended Storage

| Durasi Retensi | Storage Needed (3 Kamera) |
|:---------------|:--------------------------|
| 1 hari | 50 GB |
| 1 minggu | 350 GB |
| 1 bulan | 1.5 TB |
| 3 bulan | 4.5 TB |

---

## 📋 Use Case Scenarios

### Scenario 1: Satpam Monitoring Harian

```
Actor:    Security Guard (Satpam)
Goal:     Monitor live feed dan review kejadian kemarin
Access:   Public path only

Flow:
1. Buka browser → localhost:8000
2. Lihat 3 live stream (wajah sudah blur)
3. Ada paket hilang kemarin?
   - Klik "Gallery"
   - Filter tanggal: kemarin
   - Cari file sekitar waktu kejadian
4. Putar video MP4
   - Wajah tetap blur
   - Bisa lihat aksi, tapi tidak bisa identifikasi
5. Report ke manager jika perlu investigasi lebih lanjut

Privacy: ✅ PROTECTED (wajah blur)
Evidence: ❌ NOT ACCESSIBLE (tidak punya key)
```

### Scenario 2: Investigasi Manager

```
Actor:    Store Manager
Goal:     Identifikasi pelaku pencurian
Access:   Has decryption key

Flow:
1. Terima report dari satpam: ada insiden jam 14:30
2. Cari evidence file yang match:
   - evidence_cam0_20240115143000_*.enc
3. Jalankan decryptor:
   $ python tools/decryptor.py decrypt evidence_cam0_*.enc --output ./
4. Masukkan PIN/password
5. Evidence terdekripsi → video asli muncul
6. Identifikasi pelaku dari wajah yang terlihat
7. Simpan sebagai barang bukti

Privacy: Dibuka dengan legitimate reason
Evidence: ✅ DECRYPTED, integrity verified
```

### Scenario 3: Penyerahan ke Polisi

```
Actor:    Police Investigator
Goal:     Memperoleh barang bukti yang SAH di pengadilan
Access:   Diberikan akses oleh admin

Flow:
1. Polisi datang dengan surat permintaan
2. Admin verifikasi legitimacy
3. Admin decrypt evidence file
4. Sistem otomatis verify:
   - SHA-256 hash match ✅
   - AES-GCM auth tag valid ✅
   - Timestamp consistent ✅
5. Generate integrity report
6. Serahkan decrypted video + integrity report
7. Polisi bisa gunakan di pengadilan

Legal Status: ✅ VALID FORENSIC EVIDENCE
Integrity:    ✅ MATHEMATICALLY PROVEN
```

---

## 🔗 Kode Referensi

| Fungsi | File | Method |
|:-------|:-----|:-------|
| Apply blur | `modules/processor.py` | `FrameProcessor._apply_blur()` |
| Record public | `modules/recorder.py` | `VideoRecorder.write()` |
| Buffer evidence | `modules/evidence.py` | `EvidenceManager.add_frame()` |
| Encrypt & save | `modules/security.py` | `SecureVault.save_encrypted_file()` |
| Decrypt | `tools/decryptor.py` | `decrypt_evidence()` |

---

## ➡️ Navigasi Wiki

| Sebelumnya | Selanjutnya |
|:-----------|:------------|
| [Security](Security.md) | [Installation](Installation.md) |
