@echo off
REM Fix CUDA for PyTorch with Python 3.12
REM Run this script to install CUDA-enabled PyTorch

echo ============================================
echo  CUDA Fix for PyTorch
echo ============================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo ERROR: Virtual environment not found
    echo Run setup.bat first!
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Uninstalling CPU-only PyTorch...
pip uninstall -y torch torchvision 2>nul

echo.
echo Installing PyTorch with CUDA 12.1...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

echo.
echo Reinstalling ultralytics...
pip install ultralytics --upgrade

echo.
echo ============================================
echo  Testing CUDA Installation
echo ============================================
python -c "import torch; cuda = torch.cuda.is_available(); print(f'CUDA Available: {cuda}'); print(f'GPU: {torch.cuda.get_device_name(0)}' if cuda else 'No GPU detected')"

echo.
echo ============================================
if errorlevel 1 (
    echo  CUDA installation may have issues
    echo  Check CUDA_SETUP.md for troubleshooting
) else (
    echo  CUDA installed successfully!
)
echo ============================================
echo.
pause
