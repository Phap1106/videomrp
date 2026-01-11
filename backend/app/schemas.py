"""
Pydantic schemas for API requests and responses
"""

from typing import Optional, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== REQUEST SCHEMAS ====================

class VideoCreateRequest(BaseModel):
    """Request to create and process video"""
    source_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    target_platform: str = "tiktok"
    video_type: str = "short"
    duration: int = 60
    
    # Processing options
    add_subtitles: bool = True
    add_ai_narration: bool = True
    add_text_overlay: bool = False
    remove_watermark: bool = True
    
    # AI options
    ai_provider: Optional[str] = "auto"
    tts_voice: Optional[str] = None
    narration_style: Optional[str] = "professional"  # professional, casual, dramatic
    
    # Processing flow
    processing_flow: str = "auto"  # auto, fast, ai, full, custom
    processing_options: Optional[dict] = None


class StoryVideoRequest(BaseModel):
    """Request to create story-based video"""
    source_url: str
    title: str
    story_topic: str  # Topic for story generation
    duration: int = 60
    
    # Text styling
    font_size: int = 60
    font_color: str = "FFFFFF"
    text_position: str = "bottom"
    
    # AI options
    story_style: str = "narrative"  # narrative, dramatic, humorous, educational
    ai_provider: Optional[str] = "auto"
    tts_voice: Optional[str] = None


class TextOverlayRequest(BaseModel):
    """Request to add text overlay to video"""
    job_id: str
    text_segments: List[dict]  # [{"start": 0, "end": 5, "text": "Hello", "style": {...}}]
    font_size: int = 60
    font_color: str = "FFFFFF"
    text_position: str = "bottom"
    apply_and_output: bool = True


class VideoAnalyzeRequest(BaseModel):
    """Request to analyze video"""
    source_url: str
    target_platform: str = "tiktok"
    analyze_content: bool = True
    detect_scenes: bool = True
    check_copyright: bool = True


class TTSRequest(BaseModel):
    """Request to generate text-to-speech"""
    text: str
    voice: Optional[str] = None
    speed:  float = 1.0
    pitch: float = 0.0
    ai_provider: Optional[str] = "auto"


class VoicePreviewRequest(BaseModel):
    """Request to preview AI voice"""
    voice_id: str
    sample_text: str = "Hello, this is a voice preview."
    ai_provider: Optional[str] = "auto"


# ==================== RESPONSE SCHEMAS ====================

class JobStatus(BaseModel):
    """Job status response"""
    id: str
    title: str
    status: str  # pending, downloading, analyzing, processing, completed, failed
    progress: float
    current_step: str
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    output_path: Optional[str]
    error_message: Optional[str]


class VoiceOption(BaseModel):
    """Available voice option"""
    id: str
    name: str
    gender: str
    language: str
    preview_url: Optional[str] = None


class ProcessingFlowOption(BaseModel):
    """Processing flow option"""
    key: str
    label: str
    description: str
    duration_estimate: int  # seconds
    cost_estimate: Optional[str]
    options: dict


class HealthResponse(BaseModel):
    """Health check response"""
    api:  bool
    database: bool
    redis: bool
    storage: bool
    ai_services: dict
    queue_size: int
    active_jobs: int
    uptime:  float


class AnalysisResult(BaseModel):
    """Video analysis result"""
    content_summary: str
    scene_breakdown: List[dict]
    copyright_risk: str  # low, medium, high
    recommended_edits: List[str]
    optimal_platforms: List[str]
    best_cuts: List[dict]  # timing for cuts


class VideoOutputResponse(BaseModel):
    """Video processing output"""
    success: bool
    job_id: str
    output_path: Optional[str] = None
    output_url: Optional[str] = None
    duration: Optional[float] = None
    thumbnail_url: Optional[str] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


class TranscriptSegment(BaseModel):
    """Transcript segment with timing"""
    start: float
    end: float
    text:  str
    confidence: Optional[float] = None


class TranscriptionResult(BaseModel):
    """Transcription result"""
    full_text: str
    language: str
    duration: float
    segments: List[TranscriptSegment]
    confidence: Optional[float] = None


class StoryGenerationResult(BaseModel):
    """Story generation result"""
    original_text: Optional[str]
    generated_story: str
    segments: List[dict]
    style: str
    estimated_duration: Optional[int]