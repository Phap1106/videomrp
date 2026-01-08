from pathlib import Path
from .config import settings

DATA_DIR = Path(settings.data_dir).resolve()
JOBS_DIR = DATA_DIR / "jobs"
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"

def ensure_dirs():
    for p in [DATA_DIR, JOBS_DIR, UPLOADS_DIR, PROCESSED_DIR]:
        p.mkdir(parents=True, exist_ok=True)
