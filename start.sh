#!/bin/bash
echo "============================================"
echo "  TruthLens - Setup and Run"
echo "============================================"

# Create virtual environment if missing
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install deps
echo "Installing dependencies..."
pip install fastapi uvicorn jinja2 python-multipart groq speechrecognition requests python-dotenv pillow moviepy

# Create uploads folder
mkdir -p uploads

echo ""
echo "============================================"
echo "  Starting TruthLens on http://127.0.0.1:8000"
echo "  Press Ctrl+C to stop"
echo "============================================"
echo ""

python run.py
