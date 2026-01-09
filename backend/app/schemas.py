from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
import enum


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


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Request schemas
class VideoCreateRequest(BaseModel):
    """Request schema for creating a video job"""
    source_url: str = Field(..., description="Source video URL")
    title: Optional[str] = Field(None, description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    
    target_platform: Platform = Field(default=Platform.TIKTOK, description="Target platform")
    video_type: VideoType = Field(default=VideoType.SHORT, description="Video type")
    
    duration: int = Field(default=60, ge=5, le=600, description="Duration in seconds")
    add_subtitles: bool = Field(default=True, description="Add subtitles")
    change_music: bool = Field(default=True, description="Change background music")
    remove_watermark: bool = Field(default=True, description="Remove watermarks")
    add_effects: bool = Field(default=True, description="Add effects")
    meme_template: Optional[str] = Field(None, description="Meme template name")
    
    @validator("source_url")
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class VideoAnalyzeRequest(BaseModel):
    """Request schema for analyzing a video"""
    source_url: str = Field(..., description="Source video URL")
    target_platform: Platform = Field(default=Platform.TIKTOK, description="Target platform")
    analyze_content: bool = Field(default=True, description="Analyze video content")
    detect_scenes: bool = Field(default=True, description="Detect scenes")
    check_copyright: bool = Field(default=True, description="Check for copyright issues")


class VideoEditRequest(BaseModel):
    """Request schema for editing a video"""
    job_id: str = Field(..., description="Job ID")
    instructions: Dict[str, Any] = Field(..., description="Editing instructions")


class BatchCreateRequest(BaseModel):
    """Request schema for batch creation"""
    videos: List[VideoCreateRequest] = Field(..., description="List of videos to process")
    parallel: bool = Field(default=False, description="Process in parallel")


# Response schemas
class JobResponse(BaseModel):
    """Response schema for job"""
    id: str
    title: str
    status: str
    progress: float
    current_step: str
    source_platform: str
    target_platform: str
    video_type: str
    duration: int
    created_at: str
    updated_at: Optional[str]
    completed_at: Optional[str]
    output_filename: Optional[str]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    """Response schema for analysis result"""
    job_id: str
    summary: str
    category: str
    mood: str
    duration: float
    key_moments: List[Dict[str, Any]]
    scenes: List[Dict[str, Any]]
    copyright_risks: List[Dict[str, Any]]
    suggestions: Dict[str, Any]
    hashtags: List[str]
    titles: List[str]
    viral_score: float
    processing_time: float


class VideoSegmentResponse(BaseModel):
    """Response schema for video segment"""
    id: int
    start_time: float
    end_time: float
    duration: float
    text: Optional[str]
    has_text: bool
    has_face: bool
    scene_type: Optional[str]
    importance: float
    description: Optional[str]


class PlatformSettings(BaseModel):
    """Response schema for platform settings"""
    platform: Platform
    name: str
    max_duration: int
    aspect_ratios: List[str]
    watermark_allowed: bool
    copyright_strictness: str
    recommended_formats: List[str]
    max_size_mb: int
    audio_requirements: Dict[str, Any]


class SystemStatus(BaseModel):
    """Response schema for system status"""
    api: bool
    database: bool
    redis: bool
    storage: bool
    ai_services: Dict[str, bool]
    queue_size: int
    active_jobs: int
    total_jobs: int
    uptime: float
    version: str
    timestamp: datetime


class PaginatedResponse(BaseModel):
    """Response schema for paginated results"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


class ErrorResponse(BaseModel):
    """Response schema for errors"""
    detail: str
    code: Optional[str] = None
    field: Optional[str] = None


class SuccessResponse(BaseModel):
    """Response schema for success"""
    success: bool
    message: str
    data: Optional[Any] = None


# User schemas
class UserCreate(BaseModel):
    """Request schema for user creation"""
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(None, description="Full name")


class UserLogin(BaseModel):
    """Request schema for user login"""
    email: str = Field(..., description="Email")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Response schema for user"""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    subscription_tier: str
    credits_remaining: int
    created_at: str
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response schema for token"""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


# WebSocket schemas
class WebSocketMessage(BaseModel):
    """WebSocket message schema"""
    type: str
    data: Dict[str, Any]
    job_id: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())