@echo off
echo ============================================
echo AI Video Tool - Installation for Python 3.11
echo ============================================

REM 1. Check Python version
python --version | findstr "3.11" > nul
if errorlevel 1 (
    echo ERROR: Python 3.11 is required!
    echo Current version:
    python --version
    echo.
    echo Please install Python 3.11 from:
    echo https://www.python.org/downloads/release/python-3110/
    echo.
    pause
    exit /b 1
)

echo ✓ Python 3.11 detected

REM 2. Clean previous installation
if exist "venv" (
    echo Removing old virtual environment...
    rmdir /s /q venv
)

if exist "__pycache__" rmdir /s /q __pycache__
if exist "uploads" rmdir /s /q uploads
if exist "processed" rmdir /s /q processed

REM 3. Create fresh directories
mkdir uploads
mkdir processed

echo Creating virtual environment...
python -m venv venv

REM 4. Activate venv
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment activated

REM 5. Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip==23.3.1
echo ✓ Pip upgraded

REM 6. Install wheel và setuptools
echo Installing build tools...
pip install wheel==0.42.0 setuptools==68.2.2
echo ✓ Build tools installed

REM 7. Install packages step by step
echo Installing packages...

REM Core packages
pip install Flask==2.3.3
pip install flask-cors==4.0.0
pip install requests==2.31.0
pip install python-dotenv==1.0.0

REM Database
pip install supabase==1.0.3

REM Video/Audio
pip install yt-dlp==2023.10.13
pip install Pillow==10.1.0
pip install pydub==0.25.1

REM TTS/ML
pip install transformers==4.35.2
pip install tokenizers==0.15.0

REM Production
pip install gunicorn==21.2.0

REM 8. Create .env file
if not exist ".env" (
    echo Creating .env file...
    echo # Supabase Configuration > .env
    echo SUPABASE_URL=your_supabase_url >> .env
    echo SUPABASE_KEY=your_supabase_key >> .env
    echo. >> .env
    echo # Application Settings >> .env
    echo SECRET_KEY=change-this-to-random-secret-key >> .env
    echo DEBUG=True >> .env
    echo HOST=0.0.0.0 >> .env
    echo PORT=5000 >> .env
    echo ✓ .env file created
)

echo.
echo ============================================
echo INSTALLATION COMPLETE!
echo ============================================
echo.
echo To start the backend:
echo   1. venv\Scripts\activate
echo   2. python app.py
echo.
echo The API will run at: http://localhost:5000
echo.
echo Frontend should run at: http://localhost:3000
echo.
pause