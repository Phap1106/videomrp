# app/core/config.py
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Any, Dict, Union

from pydantic import Field, validator, field_validator
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
    APP_NAME: str = "Video Reup AI Factory"
    APP_VERSION: str = "3.0.0"
    APP_ENV: str = Field(default="development", env="APP_ENV")
    ENV:  str = Field(default="dev", env="ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
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
    VOICE_SAMPLES_DIR: Path = Field(default_factory=lambda: _backend_dir() / "data" / "voice_samples")
    FONTS_DIR: Path = Field(default_factory=lambda: _backend_dir() / "data" / "fonts")

    # ==================== CORS ====================
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"],
        env="CORS_ORIGINS",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # ==================== DATABASE ====================
    DATABASE_URL:  str = Field(
        default="mysql+pymysql://user:password@localhost/video_reup",
        env="DATABASE_URL",
    )

    # ==================== REDIS ====================
    REDIS_URL:  str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # ==================== STORAGE ====================
    MAX_UPLOAD_SIZE: int = Field(default=2000, env="MAX_UPLOAD_SIZE")  # MB
    MAX_VIDEO_DURATION: int = Field(default=3600, env="MAX_VIDEO_DURATION")  # seconds (1 hour)

    # ==================== AI PROVIDERS ====================
    AI_PROVIDER: str = Field(default="auto", env="AI_PROVIDER")  # auto | openai | gemini | mock
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    OPENAI_TTS_VOICE: str = Field(default="nova", env="OPENAI_TTS_VOICE")  # nova, echo, fable, onyx, shimmer, alloy
    
    # Google Cloud
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    GOOGLE_PROJECT_ID:  Optional[str] = Field(default=None, env="GOOGLE_PROJECT_ID")
    GOOGLE_TTS_VOICE: str = Field(default="en-US-Standard-A", env="GOOGLE_TTS_VOICE")
    
    # YouTube Data API
    YOUTUBE_API_KEY: Optional[str] = Field(default=None, env="YOUTUBE_API_KEY")
    
    # Gemini AI (uses GOOGLE_API_KEY if not set)
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    
    # Groq (OpenAI-compatible) - FREE API
    GROQ_API_KEY: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama-3.1-8b-instant", env="GROQ_MODEL")  # Fast, free model
    
    # Speech Recognition
    WHISPER_MODEL: str = Field(default="base", env="WHISPER_MODEL")  # tiny, base, small, medium, large
    DEEPGRAM_API_KEY: Optional[str] = Field(default=None, env="DEEPGRAM_API_KEY")

    # ==================== TTS SETTINGS ====================
    TTS_PROVIDER: str = Field(default="edge", env="TTS_PROVIDER")  # edge, openai, google, elevenlabs, viettel, fpt, gtts
    TTS_VOICE_GENDER: str = Field(default="female", env="TTS_VOICE_GENDER")  # male, female, neutral
    TTS_SPEAKING_RATE: float = Field(default=1.0, env="TTS_SPEAKING_RATE")
    TTS_PITCH: float = Field(default=0.0, env="TTS_PITCH")
    
    # ElevenLabs (Free tier: 10,000 chars/month)
    ELEVENLABS_API_KEY: Optional[str] = Field(default=None, env="ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID: str = Field(default="21m00Tcm4TlvDq8ikWAM", env="ELEVENLABS_VOICE_ID")  # Rachel - English
    
    # ViettelAI TTS (Free tier available)
    VIETTEL_API_KEY: Optional[str] = Field(default=None, env="VIETTEL_API_KEY")
    VIETTEL_TTS_VOICE: str = Field(default="hn-quynhanh", env="VIETTEL_TTS_VOICE")  # Vietnamese voices
    
    # FPT.AI TTS (Free 50,000 chars/month)
    FPT_API_KEY: Optional[str] = Field(default=None, env="FPT_API_KEY")
    FPT_TTS_VOICE: str = Field(default="banmai", env="FPT_TTS_VOICE")  # Vietnamese voices
    
    # Edge TTS (FREE - no API key needed)
    EDGE_TTS_VOICE: str = Field(default="vi-VN-HoaiMyNeural", env="EDGE_TTS_VOICE")  # Vietnamese Neural voice

    # Custom AI (e.g. via ngrok/local server)
    CUSTOM_AI_URL: Optional[str] = Field(default=None, env="CUSTOM_AI_URL")
    CUSTOM_AI_MODEL: str = Field(default="custom-model", env="CUSTOM_AI_MODEL")

    # ==================== AUDIO SETTINGS ====================
    ENABLE_BGM: bool = Field(default=True, env="ENABLE_BGM")
    BGM_VOLUME: float = Field(default=0.15, env="BGM_VOLUME")  # Default background music volume
    DEFAULT_BGM_PATH: Optional[str] = Field(default="data/background_music/default.mp3", env="DEFAULT_BGM_PATH")

    # ==================== VIDEO PROCESSING ====================
    FFMPEG_PATH: str = Field(default=str(Path(__file__).resolve().parents[2] / "ffmpeg.exe"), env="FFMPEG_PATH")
    FFPROBE_PATH: str = Field(default=str(Path(__file__).resolve().parents[2] / "ffprobe.exe"), env="FFPROBE_PATH")
    
    # Video quality settings
    VIDEO_CODEC: str = Field(default="libx264", env="VIDEO_CODEC")
    VIDEO_PRESET: str = Field(default="fast", env="VIDEO_PRESET")  # ultrafast, faster, fast, medium, slow, slower
    VIDEO_BITRATE: str = Field(default="5000k", env="VIDEO_BITRATE")
    AUDIO_BITRATE: str = Field(default="192k", env="AUDIO_BITRATE")

    # ==================== TEXT OVERLAY SETTINGS ====================
    DEFAULT_FONT_FILE: str = Field(default="C:/Windows/Fonts/arial.ttf", env="DEFAULT_FONT_FILE")
    DEFAULT_FONT_SIZE: int = Field(default=60, env="DEFAULT_FONT_SIZE")
    DEFAULT_FONT_COLOR: str = Field(default="FFFFFF", env="DEFAULT_FONT_COLOR")  # Hex color
    DEFAULT_TEXT_POSITION: str = Field(default="bottom", env="DEFAULT_TEXT_POSITION")  # top, center, bottom
    DEFAULT_TEXT_BG_ALPHA: float = Field(default=0.7, env="DEFAULT_TEXT_BG_ALPHA")

    # ==================== PROCESSING DEFAULTS ====================
    DEFAULT_PROCESSING_FLOW: str = Field(default="auto", env="DEFAULT_PROCESSING_FLOW")
    MAX_CONCURRENT_JOBS: int = Field(default=5, env="MAX_CONCURRENT_JOBS")
    JOB_TIMEOUT: int = Field(default=7200, env="JOB_TIMEOUT")  # 2 hours

    # ==================== SUBTITLE SETTINGS ====================
    SUBTITLE_LANGUAGE: str = Field(default="vi", env="SUBTITLE_LANGUAGE")  # Vietnamese
    SUBTITLE_FORMAT: str = Field(default="srt", env="SUBTITLE_FORMAT")  # srt, vtt, ass

    # ==================== RATE LIMITING ====================
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    # ==================== FEATURE FLAGS ====================
    ENABLE_TTS: bool = Field(default=True, env="ENABLE_TTS")
    ENABLE_TRANSCRIPTION: bool = Field(default=True, env="ENABLE_TRANSCRIPTION")
    ENABLE_STORY_GENERATION: bool = Field(default=True, env="ENABLE_STORY_GENERATION")
    ENABLE_TEXT_OVERLAY: bool = Field(default=True, env="ENABLE_TEXT_OVERLAY")

    # ==================== GOOGLE DRIVE ====================
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(default="credentials.json", env="GOOGLE_APPLICATION_CREDENTIALS")
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = Field(default=None, env="GOOGLE_DRIVE_FOLDER_ID")


settings = Settings()