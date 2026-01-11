# 📦 Installation Guide

Chi tiết cài đặt Video Reup AI Factory.

## Prerequisites

### System Requirements

- **OS**: Linux, macOS, Windows 10+ (WSL2)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**:  20GB SSD
- **CPU**: 2 cores minimum, 4+ cores recommended

### Software Requirements

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.11+ (if running locally)
- **Node**: 18+ (if running locally)

### API Keys Required

- **OpenAI**:  https://platform.openai.com/api-keys
- **Google Cloud**: https://console.cloud.google.com
- (Optional) **Deepgram**: https://console.deepgram.com

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/videomrp.git
cd videomrp
```

### 2. Setup Environment Variables

```bash
# Backend
cp backend/.env.example backend/.env
nano backend/.env  # Edit with your values

# Frontend
cp frontend/.env.example frontend/.env.local
nano frontend/.env.local
```

### 3. Configure API Keys

Edit `backend/.env`:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Google
GEMINI_API_KEY=your-gemini-key
GOOGLE_API_KEY=your-google-cloud-key

# Or use auto mode
AI_PROVIDER=auto
```

### 4. Start with Docker

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start services
bash scripts/start.sh

# Or manually
docker-compose up -d
```

### 5. Initialize Database

```bash
# Run migrations
docker-compose exec backend python -m alembic upgrade head

# Or just wait - tables are auto-created
```

### 6. Verify Installation

```bash
# Health check
bash scripts/health-check.sh

# Or manually
curl http://localhost:8000/health
curl http://localhost:3000
```

## Local Development Setup

### Backend Development

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env
cp . env.example .env
nano .env

# Setup database (PostgreSQL must be running)
python -m alembic upgrade head

# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Create .env. local
cp .env.example .env.local

# Start development server
npm run dev
```

Access: http://localhost:3000

## Troubleshooting

### Docker Issues

#### Cannot connect to Docker daemon

```bash
# Linux
sudo systemctl start docker
sudo usermod -aG docker $USER

# macOS
open -a Docker

# Windows
Start-Service docker
```

#### Port already in use

```bash
# Find and kill process using port 8000
lsof -i :8000
kill -9 <PID>

# Or change port in docker-compose. yml
```

### Database Issues

#### Database connection failed

```bash
# Check PostgreSQL
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up postgres -d
```

#### Tables not created

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Or check database directly
docker-compose exec postgres psql -U video_user -d video_reup -c "\dt"
```

### API Issues

#### Backend returns 502

```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Check if backend is listening
curl http://localhost:8000/health
```

#### Frontend cannot reach backend

```bash
# Check NEXT_PUBLIC_API_URL in frontend/. env.local
# Should be: http://localhost:8000/api (development)
# Or: http://backend:8000/api (Docker)

# Test backend connectivity
curl http://localhost:8000/api/health
```

### FFmpeg Issues

#### FFmpeg not found

```bash
# Linux
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows - download from ffmpeg.org or: 
# Already included in Docker image
```

## Next Steps

1. **Configure AI Providers**
   - Get API keys from OpenAI/Google
   - Test TTS and story generation

2. **Upload Test Video**
   - Use the UI to upload a test video
   - Try Reup feature

3. **Customize Settings**
   - Adjust video quality
   - Configure fonts and styles
   - Set processing timeouts

4. **Deploy to Production**
   - See [DEPLOYMENT.md](DEPLOYMENT.md)

## Getting Help

- Check logs: `docker-compose logs -f`
- API docs: http://localhost:8000/docs
- GitHub Issues
- Discord/Forum (if available)

---

**Happy video processing! 🎬**