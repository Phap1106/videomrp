import os
import re
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from config import Config

logger = logging.getLogger(__name__)

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename"""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'mp4'
    unique_id = uuid.uuid4().hex[:8]
    safe_name = re.sub(r'[^\w\-_\.]', '_', original_filename.rsplit('.', 1)[0])[:50]
    return f"{unique_id}_{safe_name}.{ext}"

def get_file_size_mb(filepath: str) -> float:
    """Get file size in MB"""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0.0

def format_duration(seconds: float) -> str:
    """Format duration as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def format_file_size(bytes_size: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def cleanup_temp_files(file_paths: List[str]) -> None:
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp file {file_path}: {str(e)}")

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple spaces
    filename = re.sub(r'\s+', ' ', filename).strip()
    # Limit length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    return filename

def create_directory(path: Path) -> bool:
    """Create directory if it doesn't exist"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {str(e)}")
        return False

def validate_video_file(filepath: str) -> tuple[bool, Optional[str]]:
    """Validate video file"""
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            return False, "File does not exist"
        
        # Check file size
        file_size_mb = get_file_size_mb(filepath)
        max_size_mb = Config.MAX_CONTENT_LENGTH / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            return False, f"File too large ({file_size_mb:.1f}MB > {max_size_mb:.0f}MB)"
        
        # Check file extension
        if not allowed_file(filepath):
            return False, "Invalid file type"
        
        # Basic file validation (could be extended with actual video validation)
        if os.path.getsize(filepath) == 0:
            return False, "File is empty"
        
        return True, None
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def extract_video_metadata(filepath: str) -> dict:
    """Extract basic video metadata"""
    try:
        from moviepy.editor import VideoFileClip
        
        with VideoFileClip(filepath) as clip:
            metadata = {
                'duration': clip.duration,
                'fps': clip.fps,
                'size': clip.size,
                'has_audio': clip.audio is not None
            }
        
        # File info
        metadata.update({
            'file_size': os.path.getsize(filepath),
            'filename': os.path.basename(filepath),
            'filepath': filepath,
            'created_time': os.path.getctime(filepath),
            'modified_time': os.path.getmtime(filepath)
        })
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata: {str(e)}")
        return {
            'filename': os.path.basename(filepath),
            'file_size': os.path.getsize(filepath),
            'error': str(e)
        }

def get_platform_from_url(url: str) -> str:
    """Extract platform from URL"""
    url_lower = url.lower()
    
    platform_patterns = {
        'tiktok': ['tiktok.com', 'musical.ly'],
        'douyin': ['douyin.com'],
        'youtube': ['youtube.com', 'youtu.be'],
        'instagram': ['instagram.com'],
        'twitter': ['twitter.com', 'x.com'],
        'facebook': ['facebook.com', 'fb.watch'],
        'twitch': ['twitch.tv']
    }
    
    for platform, patterns in platform_patterns.items():
        if any(pattern in url_lower for pattern in patterns):
            return platform
    
    return 'unknown'

def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    pattern = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'([\da-z\.-]+)\.'  # domain
        r'([a-z\.]{2,6})'  # top level domain
        r'([/\w \.-]*)*/?$'  # path
    )
    return bool(pattern.match(url))

def chunk_list(lst: list, chunk_size: int) -> list:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def retry_on_failure(func, max_attempts: int = 3, delay: float = 1.0, **kwargs):
    """Retry function on failure"""
    import time
    
    for attempt in range(max_attempts):
        try:
            return func(**kwargs)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise e
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
            time.sleep(delay)
    
    return None