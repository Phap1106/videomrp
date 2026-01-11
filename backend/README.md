# Backend - Setup Notes

Quick setup notes to run the backend locally:

1. Create and activate a virtual environment (recommended):
   - python -m venv .venv
   - .\.venv\Scripts\activate  (Windows)

2. Install Python dependencies:
   - pip install -r requirements.txt

3. Make sure external tools are installed and available in PATH:
   - ffmpeg and ffprobe (https://ffmpeg.org/)
   - yt-dlp (the project also installs the package, but system yt-dlp helps in some environments)

4. Start the server:
   - (.venv) uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Notes:
- If you see errors about `psutil` missing, run `pip install psutil` or `pip install -r requirements.txt`.
- If TikTok downloads fail with yt-dlp, try updating yt-dlp (`pip install -U yt-dlp`) or ensure the package version is recent.

AI / Transcription providers:
- You can let the app pick the best provider automatically by setting in `.env`:
  - AI_PROVIDER=auto
  - GROQ_API_KEY=...   # optional (preferred if available)
  - GROQ_MODEL=llama-3.1-70b-versatile
  - OPENAI_API_KEY=... # optional fallback
  - GEMINI_API_KEY=... # optional
  - DEEPGRAM_API_KEY=... # optional for transcript extraction (recommended)

Important: If using Deepgram for transcription, FFmpeg must be available to extract WAV audio (see above).

Database schema updates:
- If you see an error like "column video_jobs.processing_flow does not exist", run the provided script to apply lightweight runtime schema fixes:
  - `python scripts/ensure_schema.py`
- In production, prefer applying proper Alembic migrations; the above script is intended for development/demo environments only.