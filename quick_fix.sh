#!/bin/bash

echo "🔧 Quick Fix - Reinstalling Backend Dependencies"
echo "================================================"

cd "$(dirname "$0")/backend"

echo "1. Removing old virtual environment..."
rm -rf venv

echo "2. Creating new virtual environment..."
python3 -m venv venv

echo "3. Activating virtual environment..."
source venv/bin/activate

echo "4. Upgrading pip..."
pip install --upgrade pip

echo "5. Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "To start the backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m uvicorn app.main:app --reload"
