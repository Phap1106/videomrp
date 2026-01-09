FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    pkg-config \
    libavcodec-dev \
    libavdevice-dev \
    libavfilter-dev \
    libavformat-dev \
    libavutil-dev \
    libswresample-dev \
    libswscale-dev \
    libpostproc-dev \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    git \
    wget \
    curl \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*


# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install PyTorch with CPU only
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/data/uploads /app/data/processed /app/data/temp /app/logs && \
    chown -R appuser:appuser /app/data /app/logs

# Download AI models on build (optional)
RUN mkdir -p /app/models && \
    python -c "from faster_whisper import WhisperModel; print('Downloading Whisper model...'); model = WhisperModel('small')"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run application
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]