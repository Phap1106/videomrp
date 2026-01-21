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

AI / Narration Features:
- **Conversational Narration**: Uses advanced prompts (Viral, Review, Storytelling, Professional, Hài hước) for natural scripts.
- **Flexible Providers**: 
  - **Auto**: Automatic best-effort selection.
  - **OpenAI**: High-quality (API Key required).
  - **Gemini**: Smart context (API Key required).
  - **Groq**: Near-instant inference (API Key required).
  - **Custom AI**: Local LLMs/Ngrok via `CUSTOM_AI_URL`.
- **Key Env Vars**:
  - `AI_PROVIDER=auto`
  - `CUSTOM_AI_URL=http://localhost:11434/v1` (for Ollama/Local)
  - `GROQ_API_KEY=...`

Professional Audio Engineering:
- **Normalization**: Automatic volume leveling (EBU R128).
- **Background Music (BGM)**: Place `.mp3` files in `backend/data/bgm/` (e.g., `cheerful.mp3`, `dramatic.mp3`) to enable themed mixing.

Database & Schema:
- If column errors occur, run: `python scripts/ensure_schema.py`
- This applies lightweight dev-mode schema fixes.