@echo off
echo ============================================
echo   TruthLens - Setup and Run
echo ============================================

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install fastapi uvicorn jinja2 python-multipart groq speechrecognition requests python-dotenv pillow moviepy

REM Create uploads folder if missing
if not exist "uploads\" mkdir uploads

echo.
echo ============================================
echo   Starting TruthLens on http://127.0.0.1:8000
echo   Press Ctrl+C to stop
echo ============================================
echo.

python run.py

pause
