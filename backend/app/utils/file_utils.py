import hashlib
from pathlib import Path

from app.core.config import settings


def ensure_dirs():
    """Ensure required directories exist"""
    dirs = [
        settings.UPLOAD_DIR,
        settings.PROCESSED_DIR,
        settings.TEMP_DIR,
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    return dirs


def get_file_hash(file_path: str) -> str:
    """Get file hash"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
