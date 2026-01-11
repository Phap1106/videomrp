from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Video Reup AI Tool"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = Field(default="development", env="APP_ENV")
    DEBUG: bool = Field(default=False, env="DEBUG")
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"], env="CORS_ORIGINS"
    )

    # Database
    DATABASE_URL: str = Field(
        default="mysql+pymysql://user:password@localhost/video_reup", env="DATABASE_URL"
    )

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Storage
    UPLOAD_DIR: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    PROCESSED_DIR: str = Field(default="./data/processed", env="PROCESSED_DIR")
    TEMP_DIR: str = Field(default="./data/temp", env="TEMP_DIR")
    MAX_UPLOAD_SIZE: int = Field(default=500, env="MAX_UPLOAD_SIZE")  # MB

    # AI APIs
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    DEEPGRAM_API_KEY: str | None = Field(default=None, env="DEEPGRAM_API_KEY")
    AI_PROVIDER: str = Field(default="openai", env="AI_PROVIDER")

    # Video APIs
    TIKWM_API_KEY: str | None = Field(default=None, env="TIKWM_API_KEY")
    DOUYIN_API_KEY: str | None = Field(default=None, env="DOUYIN_API_KEY")
    YOUTUBE_API_KEY: str | None = Field(default=None, env="YOUTUBE_API_KEY")

    # FFmpeg
    FFMPEG_PATH: str = Field(default="ffmpeg", env="FFMPEG_PATH")
    FFPROBE_PATH: str = Field(default="ffprobe", env="FFPROBE_PATH")

    # TTS
    TTS_PROVIDER: str = Field(default="piper", env="TTS_PROVIDER")
    PIPER_PATH: str = Field(default="piper", env="PIPER_PATH")
    PIPER_MODEL_PATH: str | None = Field(default=None, env="PIPER_MODEL_PATH")

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    MAX_CONCURRENT_JOBS: int = Field(default=5, env="MAX_CONCURRENT_JOBS")

    # Platforms enabled
    ENABLE_TIKTOK: bool = Field(default=True, env="ENABLE_TIKTOK")
    ENABLE_YOUTUBE: bool = Field(default=True, env="ENABLE_YOUTUBE")
    ENABLE_FACEBOOK: bool = Field(default=True, env="ENABLE_FACEBOOK")
    ENABLE_INSTAGRAM: bool = Field(default=True, env="ENABLE_INSTAGRAM")
    ENABLE_DOUYIN: bool = Field(default=True, env="ENABLE_DOUYIN")

    # Security
    JWT_SECRET_KEY: str = Field(default="your-jwt-secret-key", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, env="JWT_EXPIRE_MINUTES")  # 7 days

    # Monitoring
    SENTRY_DSN: str | None = Field(default=None, env="SENTRY_DSN")
    ENABLE_PROMETHEUS: bool = Field(default=False, env="ENABLE_PROMETHEUS")

    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL must be set")
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()
