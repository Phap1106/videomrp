# backend/app/models.py
import enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Platform(str, enum.Enum):
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    DOUYIN = "douyin"
    TWITTER = "twitter"
    GENERIC = "generic"


class VideoType(str, enum.Enum):
    SHORT = "short"
    HIGHLIGHT = "highlight"
    VIRAL = "viral"
    MEME = "meme"
    FULL = "full"
    REEL = "reel"


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False, default="Untitled Video")
    description = Column(Text, nullable=True)

    source_url = Column(Text, nullable=False)
    source_platform = Column(Enum(Platform), default=Platform.GENERIC)
    original_filename = Column(String(255), nullable=True)
    input_path = Column(Text, nullable=True)

    output_path = Column(Text, nullable=True)
    output_filename = Column(String(255), nullable=True)
    thumbnail_path = Column(Text, nullable=True)

    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    progress = Column(Float, default=0.0)
    current_step = Column(String(100), default="initializing")
    error_message = Column(Text, nullable=True)

    target_platform = Column(Enum(Platform), default=Platform.TIKTOK)
    video_type = Column(Enum(VideoType), default=VideoType.SHORT)

    duration = Column(Integer, default=60)
    add_subtitles = Column(Boolean, default=True)
    change_music = Column(Boolean, default=True)
    remove_watermark = Column(Boolean, default=True)
    add_effects = Column(Boolean, default=True)
    meme_template = Column(String(100), nullable=True)

    # New: processing flow and options (frontend can choose processing flow and custom options)
    processing_flow = Column(String(50), nullable=True, default="auto")
    processing_options = Column(JSON, nullable=True)

    analysis_result = Column(JSON, nullable=True)
    ai_instructions = Column(JSON, nullable=True)
    hashtags = Column(JSON, nullable=True)

    # ✅ FK để relationship User.jobs không lỗi mapper
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    segments = relationship("VideoSegment", back_populates="job", cascade="all, delete-orphan")
    events = relationship("JobEvent", back_populates="job", cascade="all, delete-orphan")

    # ✅ relationship 2 chiều rõ ràng
    user = relationship("User", back_populates="jobs")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value if self.status else None,
            "progress": self.progress,
            "current_step": self.current_step,
            "source_platform": self.source_platform.value if self.source_platform else None,
            "target_platform": self.target_platform.value if self.target_platform else None,
            "video_type": self.video_type.value if self.video_type else None,
            "duration": self.duration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output_filename": self.output_filename,
            "error_message": self.error_message,
        }


class VideoSegment(Base):
    __tablename__ = "video_segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("video_jobs.id"), nullable=False)

    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)

    text = Column(Text, nullable=True)
    translated_text = Column(Text, nullable=True)
    has_text = Column(Boolean, default=False)
    has_face = Column(Boolean, default=False)
    scene_type = Column(String(50), nullable=True)
    importance = Column(Float, default=0.0)

    emotions = Column(JSON, nullable=True)
    keywords = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("VideoJob", back_populates="segments")


class JobEvent(Base):
    __tablename__ = "job_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("video_jobs.id"), nullable=False)

    event_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("VideoJob", back_populates="events")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    subscription_tier = Column(String(50), default="free")
    subscription_expires = Column(DateTime(timezone=True), nullable=True)
    credits_remaining = Column(Integer, default=100)

    preferences = Column(JSON, default=dict)
    api_key = Column(String(255), unique=True, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    jobs = relationship("VideoJob", back_populates="user")


class APILog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    method = Column(String(10), nullable=False)
    endpoint = Column(String(255), nullable=False)
    user_id = Column(String(36), nullable=True)  # log: không bắt buộc FK
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    status_code = Column(Integer, nullable=False)
    response_time = Column(Float, nullable=False)

    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
