#!/bin/bash
# Secure Edge Vision System - Setup Script for Linux/Mac
# Run: chmod +x setup.sh && ./setup.sh

echo "============================================"
echo " Secure Edge Vision System - Setup"
echo "============================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python 3.9+"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Created venv"
else
    echo "venv already exists"
fi

echo
echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo
echo "[3/5] Upgrading pip..."
pip install --upgrade pip

echo
echo "[4/5] Installing dependencies..."
pip install -r requirements.txt

echo
echo "[5/5] Creating directories..."
mkdir -p models keys recordings/public recordings/evidence

echo
echo "============================================"
echo " Setup Complete!"
echo "============================================"
echo
echo "Next steps:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Test components: python demo.py"
echo "  3. Run system: python main.py"
echo "  4. Open browser: http://localhost:8000"
echo
