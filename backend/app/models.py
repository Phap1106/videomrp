import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Float, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class JobStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class VideoJob(Base):
    __tablename__ = "video_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    source_type: Mapped[str] = mapped_column(String(20), default="url")  # url | upload
    source_url: Mapped[str] = mapped_column(Text, default="")
    input_path: Mapped[str] = mapped_column(Text, default="")
    output_path: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.pending)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    current_step: Mapped[str] = mapped_column(String(64), default="initializing")
    error_message: Mapped[str] = mapped_column(Text, default="")

    # options
    target_lang: Mapped[str] = mapped_column(String(16), default="vi")
    make_shorts: Mapped[int] = mapped_column(Integer, default=0)  # 0/1
    clip_seconds: Mapped[int] = mapped_column(Integer, default=0) # 0 = keep
    style_preset: Mapped[str] = mapped_column(String(32), default="standard") # standard|viral|meme|cinematic
    subtitles: Mapped[int] = mapped_column(Integer, default=1)
    voiceover: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
