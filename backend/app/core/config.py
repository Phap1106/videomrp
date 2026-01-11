# app/core/config.py
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _backend_dir() -> Path:
    """Get backend directory path"""
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings with full compatibility"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== APPLICATION ====================
    APP_NAME: str = "Video Reup AI Tool"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = Field(default="development", env="APP_ENV")
    ENV: str = Field(default="dev", env="ENV")  # Alias for APP_ENV
    DEBUG: bool = Field(default=False, env="DEBUG")
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")

    # ==================== SERVER ====================
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")

    # ==================== PATHS ====================
    BACKEND_DIR: Path = Field(default_factory=_backend_dir)
    DATA_DIR: Path = Field(default_factory=lambda: _backend_dir() / "data")
    TEMP_DIR: Path = Field(default_factory=lambda: _backend_dir() / "data" / "temp")
    JOBS_DIR: Path = Field(default_factory=lambda: _backend_dir() / "data" / "jobs")
    PROCESSED_DIR: Path = Field(default_factory=lambda: _backend_dir() / "data" / "processed")
    UPLOAD_DIR: Path = Field(default_factory=lambda: _backend_dir() / "uploads")
    LOG_DIR: Path = Field(default_factory=lambda: _backend_dir() / "logs")

    # ==================== CORS ====================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS",
    )

    # ==================== DATABASE ====================
    DATABASE_URL: str = Field(
        default="mysql+pymysql://user:password@localhost/video_reup",
        env="DATABASE_URL",
    )

    # ==================== REDIS ====================
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # ==================== STORAGE ====================
    MAX_UPLOAD_SIZE: int = Field(default=500, env="MAX_UPLOAD_SIZE")  # MB

    # ==================== AI PROVIDERS ====================
    # ==================== AI PROVIDERS ====================
    AI_PROVIDER: str = Field(
        default="auto", env="AI_PROVIDER"
    )  # auto | openai | groq | gemini | mock

    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")

    # Groq (OpenAI-compatible)
    GROQ_API_KEY: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama-3.1-70b-versatile", env="GROQ_MODEL")

    # Gemini
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-pro", env="GEMINI_MODEL")

    # Other AI
    DEEPGRAM_API_KEY: Optional[str] = Field(default=None, env="DEEPGRAM_API_KEY")

    # ==================== VIDEO APIs ====================
    TIKWM_API_KEY: Optional[str] = Field(default=None, env="TIKWM_API_KEY")
    DOUYIN_API_KEY: Optional[str] = Field(default=None, env="DOUYIN_API_KEY")
    YOUTUBE_API_KEY: Optional[str] = Field(default=None, env="YOUTUBE_API_KEY")

    # ==================== EXTERNAL TOOLS ====================
    FFMPEG_PATH: str = Field(default="ffmpeg", env="FFMPEG_PATH")
    FFPROBE_PATH: str = Field(default="ffprobe", env="FFPROBE_PATH")
    YTDLP_PATH: str = Field(default="yt-dlp", env="YTDLP_PATH")

    # ==================== AUDIO SEPARATION ====================
    # Choose separation tool: 'spleeter' or 'demucs'. If using demucs, set USE_DEMUCS=True.
    USE_DEMUCS: bool = Field(default=False, env="USE_DEMUCS")
    SEPARATION_TOOL: str = Field(default="spleeter", env="SEPARATION_TOOL")  # spleeter|demucs
    SEPARATION_THREADS: int = Field(default=2, env="SEPARATION_THREADS")
    SEPARATION_OUTPUT_DIR: Path = Field(
        default_factory=lambda: _backend_dir() / "data" / "processed" / "stems"
    )

    # ==================== TTS ====================
    TTS_PROVIDER: str = Field(default="piper", env="TTS_PROVIDER")
    PIPER_PATH: str = Field(default="piper", env="PIPER_PATH")
    PIPER_MODEL_PATH: Optional[str] = Field(default=None, env="PIPER_MODEL_PATH")

    # ==================== RATE LIMITING ====================
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    MAX_CONCURRENT_JOBS: int = Field(default=5, env="MAX_CONCURRENT_JOBS")

    # ==================== PLATFORM TOGGLES ====================
    ENABLE_TIKTOK: bool = Field(default=True, env="ENABLE_TIKTOK")
    ENABLE_YOUTUBE: bool = Field(default=True, env="ENABLE_YOUTUBE")
    ENABLE_FACEBOOK: bool = Field(default=True, env="ENABLE_FACEBOOK")
    ENABLE_INSTAGRAM: bool = Field(default=True, env="ENABLE_INSTAGRAM")
    ENABLE_DOUYIN: bool = Field(default=True, env="ENABLE_DOUYIN")

    # ==================== SECURITY ====================
    JWT_SECRET_KEY: str = Field(default="your-jwt-secret-key", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, env="JWT_EXPIRE_MINUTES")  # 7 days

    # ==================== MONITORING ====================
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    ENABLE_PROMETHEUS: bool = Field(default=False, env="ENABLE_PROMETHEUS")

    # ==================== PROCESSING FLOW PRESETS ====================
    PROCESSING_FLOW_PRESETS: dict = Field(
        default_factory=lambda: {
            "auto": {
                "label": "Auto",
                "description": "Automatically choose flow based on available AI keys and user options.",
                "options": {},
            },
            "fast": {
                "label": "Fast",
                "description": "Rule-based minimal processing (fast). Good for quick trims and basic edits.",
                "options": {
                    "separate_audio": False,
                    "diarization": False,
                    "ocr": False,
                    "auto_reup": False,
                    "change_music": True,
                    "add_effects": True,
                },
            },
            "ai": {
                "label": "AI",
                "description": "Use transcription + AI-generated editing instructions for richer cuts and subtitles.",
                "options": {
                    "separate_audio": False,
                    "diarization": True,
                    "ocr": False,
                    "auto_reup": False,
                },
            },
            "full": {
                "label": "Full",
                "description": "Full pipeline: audio separation, OCR, diarization, AI edits and optional auto reup.",
                "options": {
                    "separate_audio": True,
                    "diarization": True,
                    "ocr": True,
                    "auto_reup": True,
                    "change_music": True,
                    "add_effects": True,
                },
            },
            "custom": {
                "label": "Custom",
                "description": "Choose individual options manually.",
                "options": {},
            },
        }
    )

    # ==================== VALIDATORS ====================
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Validate database URL is not empty"""
        if not v:
            raise ValueError("DATABASE_URL must be set")
        return v

    @validator("ENV", always=True)
    def sync_env(cls, v, values):
        """Sync ENV with APP_ENV"""
        return values.get("APP_ENV", v)

    # ==================== PROPERTIES ====================
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.APP_ENV.lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.APP_ENV.lower() in ("development", "dev")

    # ==================== METHODS ====================
    def ensure_dirs(self) -> None:
        """Create all required directories"""
        for p in [
            self.DATA_DIR,
            self.TEMP_DIR,
            self.JOBS_DIR,
            self.PROCESSED_DIR,
            self.SEPARATION_OUTPUT_DIR,
            self.UPLOAD_DIR,
            self.LOG_DIR,
        ]:
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                # Don't crash app if directory creation fails
                print(f"Warning: Could not create directory {p}: {e}")


# ==================== GLOBAL INSTANCE ====================
settings = Settings()
settings.ensure_dirs()
