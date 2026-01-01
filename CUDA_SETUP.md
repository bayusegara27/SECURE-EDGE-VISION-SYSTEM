# 🎮 Panduan Setup CUDA untuk PyTorch

> Panduan ini untuk mengaktifkan GPU acceleration pada sistem Secure Edge Vision.  
> Dengan CUDA: **25-30 FPS** | Tanpa CUDA: **5-10 FPS**

---

## 📋 Persyaratan

- **GPU NVIDIA** (RTX 3050, 3060, 3070, dll)
- **NVIDIA Driver** terinstall
- **Python 3.9+** dengan virtual environment

---

## 🔍 Langkah 1: Cek GPU & CUDA Version

Buka terminal/PowerShell:

```bash
nvidia-smi
```

Contoh output:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 536.23    Driver Version: 536.23    CUDA Version: 12.2          |
|   0  NVIDIA GeForce RTX 3050 Laptop GPU                                    |
+-----------------------------------------------------------------------------+
```

**Catat CUDA Version** (contoh: 12.2) - ini menentukan versi PyTorch yang diinstall.

---

## 🚀 Langkah 2: Install PyTorch dengan CUDA

### Metode 1: Script Otomatis (Windows)

```bash
# Pastikan di folder project
cd E:\Kuliah\ProjectSkripsi

# Jalankan script
.\fix_cuda.bat
```

### Metode 2: Manual

```bash
# 1. Aktifkan venv terlebih dahulu!
.\venv\Scripts\activate

# 2. Uninstall PyTorch lama (jika ada)
pip uninstall torch torchvision -y

# 3. Install PyTorch dengan CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

> **Catatan**: CUDA 12.1 kompatibel dengan Driver CUDA 12.2+

### Alternatif untuk CUDA 11.8

Jika CUDA Version di nvidia-smi adalah 11.x:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

---

## ✅ Langkah 3: Verifikasi Instalasi

```bash
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}' if torch.cuda.is_available() else 'No GPU')"
```

**Output yang benar:**
```
CUDA: True
GPU: NVIDIA GeForce RTX 3050 Laptop GPU
```

**Jika CUDA: False**, lihat Troubleshooting di bawah.

---

## 🧪 Langkah 4: Test dengan Demo

```bash
python demo.py --quick
```

Lihat output:
```
✓ CUDA available: NVIDIA GeForce RTX 3050 Laptop GPU
  Memory: 4.0 GB
```

---

## ⚠️ Troubleshooting

### Problem: CUDA: False

**1. Pastikan install di dalam venv:**
```bash
# Cek path Python
where python

# Harus menunjuk ke: E:\...\venv\Scripts\python.exe
# BUKAN ke: C:\Users\...\Python\python.exe
```

**2. Cek venv aktif:**
```bash
# Prompt harus ada (venv) di depan:
(venv) PS E:\Kuliah\ProjectSkripsi>
```

**3. Reinstall di venv:**
```bash
.\venv\Scripts\pip.exe uninstall torch torchvision -y
.\venv\Scripts\pip.exe install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Problem: DLL Load Failed

Install Visual C++ Redistributable:
1. Download dari: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Install dan restart

### Problem: NVIDIA Driver Outdated

1. Buka: https://www.nvidia.com/download/index.aspx
2. Download driver terbaru untuk GPU Anda
3. Install dan restart komputer

---

## 📊 Perbandingan Performa

| Mode | FPS | Latency | Memory |
|------|-----|---------|--------|
| CPU  | 5-10 | 150-200ms | 2GB RAM |
| CUDA | 25-30 | 30-50ms | 2GB VRAM |

---

## 🔗 Referensi

- [PyTorch Installation](https://pytorch.org/get-started/locally/)
- [NVIDIA Driver Download](https://www.nvidia.com/download/index.aspx)
- [CUDA Compatibility](https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/)
