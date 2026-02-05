# ❓ FAQ - Persiapan Sidang Skripsi

*Frequently Asked Questions dan strategi pertahanan sidang*

---

## 📋 Daftar Isi

1. [Pertanyaan Teknis](#-pertanyaan-teknis)
2. [Pertanyaan Keamanan](#-pertanyaan-keamanan)
3. [Pertanyaan Desain](#-pertanyaan-desain)
4. [Pertanyaan Performa](#-pertanyaan-performa)
5. [Pertanyaan Akademis](#-pertanyaan-akademis)
6. [Pertanyaan Aplikasi](#-pertanyaan-aplikasi)
7. [Tips Sidang](#-tips-sidang)

---

## 💻 Pertanyaan Teknis

### Q1: Kenapa pakai Laptop Gaming? Kenapa bukan Raspberry Pi?

**Jawaban:**

> "Untuk skenario **Edge AI modern** yang menangani multiple streams dengan algoritma enkripsi real-time AES-256, **Raspberry Pi tidak memiliki throughput yang cukup**. 
>
> Raspberry Pi 4 hanya bisa mencapai 3-5 FPS untuk deteksi wajah, sedangkan surveillance membutuhkan minimal 25 FPS. Laptop dengan **RTX 3050** merepresentasikan **Industrial Edge Server** (seperti NVIDIA Jetson Orin) yang umum dipakai di Smart City modern.
>
> RTX 3050 memberikan **25-30 FPS untuk 3 kamera simultan**, yang tidak mungkin dicapai Raspberry Pi. Ini adalah trade-off yang umum di dunia nyata: performa vs harga."

**Data Pendukung:**
- Raspberry Pi 4: 3-5 FPS (YOLOv8n, no GPU)
- RTX 3050: 28-30 FPS (YOLOv8n, CUDA)
- Faktor: ~6x lebih cepat

---

### Q2: Bagaimana cara kerja deteksi wajah dalam sistem?

**Jawaban:**

> "Sistem menggunakan **YOLOv8-Face**, model deteksi wajah yang di-training pada dataset **WIDER Face** dengan 32,000+ gambar wajah.
>
> Proses deteksi:
> 1. Frame di-resize ke 640x640 untuk konsistensi
> 2. Model YOLOv8 melakukan forward pass (~15ms di GPU)
> 3. Output berupa bounding box [x1, y1, x2, y2] dengan confidence score
> 4. Box dengan confidence > 0.5 dianggap valid detection
> 5. Setiap box diperbesar 15% untuk coverage lebih baik
> 6. Area tersebut kemudian di-blur dengan Gaussian filter 51x51"

**Diagram:**
```
Input Frame → YOLOv8 Inference → Bounding Boxes → Padding 15% → Gaussian Blur
```

---

### Q3: Mengapa memilih FastAPI dibanding Flask atau Django?

**Jawaban:**

> "**FastAPI** dipilih karena tiga alasan utama:
>
> 1. **Native Async Support**: Streaming MJPEG membutuhkan asynchronous I/O. FastAPI berbasis Starlette yang async-native, sementara Flask synchronous by default.
>
> 2. **Automatic Documentation**: FastAPI auto-generate Swagger UI dan ReDoc. Ini penting untuk dokumentasi skripsi dan maintenance.
>
> 3. **Type Safety**: FastAPI menggunakan Pydantic untuk validasi. Mengurangi bug dan mempermudah debugging.
>
> Performance: FastAPI ~3x lebih cepat dari Flask untuk endpoint sederhana, karena berbasis ASGI bukan WSGI."

---

### Q4: Bagaimana sistem menangani multiple kamera secara paralel?

**Jawaban:**

> "Sistem menggunakan **Python threading** dengan model **Producer-Consumer**:
>
> 1. **Main Thread**: Menjalankan FastAPI server
> 2. **Camera Threads**: Satu thread per kamera, melakukan capture + processing
> 3. **AI Model**: Shared instance untuk menghemat GPU memory
> 4. **Thread Safety**: Per-camera Lock untuk akses frame terbaru
>
> Kenapa threading bukan multiprocessing? Karena:
> - GPU model tidak bisa di-share antar process (harus copy)
> - Threading lebih ringan untuk I/O-bound tasks (camera capture)
> - GIL tidak jadi masalah karena computation di GPU (release GIL)"

---

## 🔐 Pertanyaan Keamanan

### Q5: Apakah video yang sudah di-blur bisa dikembalikan (un-blur)?

**Jawaban:**

> "Secara matematis **TIDAK BISA**. Gaussian blur adalah operasi **irreversible** yang menghancurkan informasi.
>
> Prosesnya:
> ```
> Pixel asli: [100, 150, 200, 180, 90] 
>              ↓ Gaussian Average
> Pixel blur: [144, 144, 144, 144, 144]
> ```
>
> Informasi bahwa pixel pertama bernilai 100 sudah **hilang permanen**. Tidak ada cara matematika untuk mengetahui nilai asli dari hasil rata-rata.
>
> **Tentang AI Un-blur:**
> AI tools seperti GFPGAN atau CodeFormer hanya **hallucinate** (menebak/generate) wajah baru. Hasilnya **BUKAN wajah asli**, tapi generasi AI. Tidak dapat digunakan untuk identifikasi legal karena itu fabrication."

**Demo:** Tunjukkan hasil blur → tidak ada detail wajah tersisa.

---

### Q6: Bagaimana membuktikan video bukti tidak diedit admin?

**Jawaban:**

> "Sistem menggunakan **dual-layer integrity protection**:
>
> **Layer 1: SHA-256 Hash**
> - Sebelum enkripsi, sistem menghitung hash SHA-256 dari frame asli
> - Hash ini **embedded di dalam ciphertext**
> - Saat dekripsi, hash dihitung ulang dan dibandingkan
> - Jika admin edit video lalu re-encrypt, hash akan berbeda
>
> **Layer 2: AES-GCM Authentication Tag**
> - GCM mode menghasilkan 16-byte authentication tag
> - Tag ini meng-cover seluruh ciphertext
> - Modifikasi sekecil apapun akan invalidate tag
> - Dekripsi akan **GAGAL** jika tag tidak valid
>
> Ini adalah **cryptographic proof** yang tidak bisa dipalsukan tanpa private key."

**Demo:** Tunjukkan test tampering:
```bash
# 1. Encrypt file
python tools/decryptor.py encrypt test.mp4

# 2. Edit 1 byte dengan hex editor
# (Change byte di posisi random)

# 3. Try decrypt
python tools/decryptor.py decrypt test.enc
# Result: ERROR - Integrity check failed!
```

---

### Q7: Kenapa pakai AES-GCM bukan AES-CBC?

**Jawaban:**

> "**AES-GCM** adalah **Authenticated Encryption** yang memberikan:
> - **Confidentiality** (enkripsi)
> - **Integrity** (deteksi modifikasi)
> - **Authenticity** (verifikasi sumber)
>
> dalam **satu operasi**.
>
> **AES-CBC** hanya memberikan confidentiality. Untuk integrity, perlu tambahan HMAC (HMAC-SHA256). Ini berarti:
> - 2 operasi kriptografi (lebih lambat)
> - 2 keys harus dikelola
> - Rentan terhadap **padding oracle attacks** jika implementasi salah
>
> AES-GCM lebih modern, lebih cepat (parallelizable), dan lebih aman. Standar NIST (SP 800-38D) merekomendasikan GCM untuk authenticated encryption."

---

### Q8: Bagaimana key management dalam sistem?

**Jawaban:**

> "Sistem mendukung dua mode:
>
> **Mode 1: Symmetric (AES-256)**
> - Single master key di `keys/master.key`
> - Key di-generate sekali, digunakan untuk semua file
> - Pro: Simpel
> - Con: Single point of failure
>
> **Mode 2: Hybrid (RSA + AES)**
> - RSA key pair untuk key encryption
> - Random AES session key per-file
> - Pro: Forward secrecy, private key bisa offline
> - Con: Lebih kompleks
>
> **Key Generation:**
> ```bash
> # Symmetric
> python tools/key_manager.py --generate
>
> # Hybrid dengan PIN
> python tools/key_manager.py --generate-rsa --pin 1234
> ```
>
> **Backup Strategy:**
> - Primary: `keys/master.key`
> - Backup 1: USB terenkripsi (offline)
> - Backup 2: Secure cloud (encrypted)
> - Backup 3: Paper backup (in safe)"

---

## 🎨 Pertanyaan Desain

### Q9: Kenapa tidak pakai segmentation seperti Google?

**Jawaban:**

> "Trade-off **speed vs precision**:
>
> | Metode | Akurasi | Speed | Use Case |
> |--------|---------|-------|----------|
> | **Segmentation** (Mask R-CNN) | Pixel-perfect | 5-10x lebih lambat | Offline processing |
> | **Detection** (YOLO) | Bounding box | Real-time | Live surveillance |
>
> Google Street View memproses gambar **offline** dalam batch. Mereka bisa spend hours per image. Surveillance system butuh **real-time** (<200ms latency).
>
> Bounding box dengan **padding 15%** sudah cukup menutupi wajah. Dari perspektif privasi, tidak ada perbedaan praktis antara blur kotak vs blur pixel-perfect."

---

### Q10: Apa batasan (Limitation) sistem kamu?

**Jawaban (Jujur & Akademis):**

> "**Limitations:**
>
> 1. **Occlusion Dependency**
>    - Jika wajah tertutup masker full-face, helm, atau menghadap belakang, YOLOv8 tidak mendeteksi wajah
>    - Solusi: Tambah model person detection (blur seluruh tubuh)
>
> 2. **Lighting Conditions**
>    - Low-light atau backlight mengurangi accuracy
>    - Solusi: Use IR cameras atau HDR preprocessing
>
> 3. **Small Faces**
>    - Wajah yang terlalu kecil (<20px) sulit terdeteksi
>    - Solusi: Use higher resolution atau zoom
>
> 4. **Network Latency (RTSP)**
>    - IP cameras menambah 100-300ms latency
>    - Solusi: Use local network, minimize hops
>
> 5. **Key Security**
>    - Jika key dicuri, semua evidence bisa dibuka
>    - Solusi: Use HSM atau secure enclave untuk production"

---

## ⚡ Pertanyaan Performa

### Q11: Bagaimana sistem mencapai real-time performance?

**Jawaban:**

> "Beberapa optimisasi kunci:
>
> 1. **GPU Acceleration**: YOLOv8 inference di CUDA (~15ms vs ~200ms di CPU)
> 2. **Shared Model**: Satu instance untuk semua kamera (hemat 2GB VRAM)
> 3. **Smart Resize**: All frames ke 720p untuk konsistensi
> 4. **Minimal Buffer**: `CAP_PROP_BUFFERSIZE=1` mengurangi latency
> 5. **Background Flush**: Encryption di thread terpisah (no blocking)
> 6. **Selective Recording**: Hanya save frame dengan deteksi (80% storage saving)
>
> **Result:**
> - Latency: 122ms average (target <500ms) ✅
> - FPS: 28-30 (target 25-30) ✅
> - GPU: 52% usage (target <80%) ✅"

---

### Q12: Kenapa selective recording bisa menghemat 80% storage?

**Jawaban:**

> "Analisis aktivitas surveillance menunjukkan:
>
> - 80% waktu: Frame kosong atau tanpa wajah
> - 20% waktu: Ada wajah terdeteksi (yang perlu disimpan)
>
> Dengan **selective recording**:
> - Sistem hanya menyimpan frame saat ada deteksi
> - Ditambah **pre-roll buffer** 30 frames (~1 detik) untuk konteks
> - Tidak ada evidence yang hilang, tapi 80% 'noise' dibuang
>
> **Calculation:**
> ```
> Full recording: 15 GB/jam
> Selective (20%): 3 GB/jam
> Saving: 12 GB/jam = 80%
> ```
>
> Ini penting untuk **sustainability** - tidak ada gunanya sistem bagus jika storage penuh dalam 1 hari."

---

## 🎓 Pertanyaan Akademis

### Q13: Apa kontribusi akademis dari penelitian ini?

**Jawaban:**

> "Tiga kontribusi utama:
>
> 1. **Arsitektur Dual-Path untuk Surveillance**
>    - Novel approach: Memisahkan privasi publik dan kebutuhan forensik
>    - Public path (blur) + Evidence path (encrypted) berjalan simultan
>    - Belum ada sistem open-source yang implementasi ini secara lengkap
>
> 2. **Optimisasi Edge AI untuk Multi-Camera**
>    - Teknik shared model + smart resize + selective recording
>    - Benchmark data untuk hardware edge computing
>    - Reproducible dengan GPU consumer-grade
>
> 3. **Framework Keamanan Forensik**
>    - Implementasi chain-of-custody dengan AES-GCM + SHA-256
>    - Tamper detection yang dapat diverifikasi
>    - Dokumentasi lengkap untuk referensi"

---

### Q14: Apa perbedaan dengan penelitian sejenis?

**Jawaban:**

> "| Aspek | Penelitian Lain | Penelitian Ini |
> |-------|-----------------|----------------|
> | **Processing** | Umumnya offline/batch | Real-time (<200ms) |
> | **Evidence** | Tidak ada | Encrypted + integrity |
> | **Hardware** | Cloud atau high-end server | Edge device (laptop) |
> | **Multi-camera** | Single camera | 3+ simultaneous |
> | **Open Source** | Jarang | Fully documented |
>
> Fokus penelitian ini adalah **practical implementation** yang bisa di-deploy di dunia nyata, bukan hanya proof-of-concept akademis."

---

## 🏢 Pertanyaan Aplikasi

### Q15: Dimana sistem ini bisa diimplementasikan?

**Jawaban:**

> "**Use Cases:**
>
> 1. **Retail Stores**
>    - Monitor CCTV tanpa melanggar privasi pelanggan
>    - Evidence tersedia jika ada pencurian
>
> 2. **Offices**
>    - Surveillance area kerja
>    - Compliance dengan data protection (GDPR-like)
>
> 3. **Public Spaces**
>    - Mall, stasiun, bandara
>    - Balance keamanan vs privasi warga
>
> 4. **Healthcare**
>    - Monitor area sensitif
>    - Protect patient privacy (HIPAA compliance)
>
> 5. **Education**
>    - Sekolah, kampus
>    - Protect student privacy"

---

### Q16: Bagaimana skalabilitas sistem?

**Jawaban:**

> "**Current Capacity (Single Edge Server):**
> - 3 cameras @ 720p @ 30fps
> - RTX 3050 (4GB VRAM)
>
> **Scaling Options:**
>
> 1. **Vertical Scaling** (Better GPU)
>    - RTX 3060 (12GB): ~5 cameras
>    - RTX 4080 (16GB): ~10 cameras
>
> 2. **Horizontal Scaling** (Multiple Servers)
>    - Each server handles 3 cameras
>    - Central storage server untuk recordings
>    - Load balancer untuk web access
>
> **Architecture for 30 Cameras:**
> ```
> [10 Edge Servers] → [Central NAS] → [Web Server]
>       ↓                  ↓              ↓
>   3 cams each      Recordings      Dashboard
> ```"

---

## 💡 Tips Sidang

### Persiapan Demo

1. **Backup Laptop** - Bawa charger dan extension cord
2. **Pre-record Video** - Jika kamera bermasalah, putar recording
3. **Offline Mode** - Pastikan sistem jalan tanpa internet
4. **Test Tamper** - Siapkan file yang sudah di-tamper untuk demo
5. **Slides** - Backup di USB dan cloud

### Yang Harus Disiapkan

- [ ] Laptop dengan sistem running
- [ ] Webcam external (backup)
- [ ] Pre-recorded test videos
- [ ] Slides presentation
- [ ] Code snippets di clipboard
- [ ] Terminal commands ready
- [ ] Benchmark data di Excel
- [ ] Architecture diagram print-out

### Jawaban Template

**Untuk pertanyaan yang tidak tahu:**
> "Itu pertanyaan yang bagus. Dalam scope penelitian ini, saya belum mengeksplorasi [X]. Namun untuk future work, pendekatan yang bisa diambil adalah [Y]. Ini bisa menjadi topik penelitian lanjutan."

**Untuk kritik:**
> "Terima kasih atas masukannya. Memang [X] adalah limitation dari sistem ini. Dalam konteks skripsi S1 dengan waktu dan resource terbatas, saya memilih fokus pada [Y] sebagai core contribution. [X] bisa menjadi improvement di versi selanjutnya."

---

## 📚 Referensi Cepat

### Commands yang Perlu Dihapal

```bash
# Run system
python main.py

# Quick test
python demo.py --quick

# Generate key
python tools/key_manager.py --generate

# Generate RSA keys (hybrid encryption)
python tools/key_manager.py --generate-rsa

# Run benchmark
python benchmark.py --duration 60

# List evidence files
python tools/decryptor.py --list

# Decrypt and play evidence
python tools/decryptor.py --file evidence.enc

# Export decrypted evidence to video
python tools/decryptor.py --file evidence.enc --export output.mp4
```

### Angka Penting

| Metrik | Nilai |
|:-------|:------|
| Latency | 122ms |
| FPS | 28-30 |
| GPU Usage | 52% |
| Storage Saving | 80% |
| AES Key Size | 256-bit |
| Hash | SHA-256 |

---

## ➡️ Navigasi Wiki

| Sebelumnya | Kembali ke Home |
|:-----------|:----------------|
| [Performance](Performance.md) | [Home](Home.md) |

---

<div align="center">

**🎓 Semoga sukses sidangnya!**

*"The best preparation for tomorrow is doing your best today."*

</div>
