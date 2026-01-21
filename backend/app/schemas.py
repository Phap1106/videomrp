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
    
    # Audio options
    add_background_music: bool = False
    bgm_style: str = "cheerful"  # cheerful, dramatic, cinematic, tech, lo-fi
    normalize_audio: bool = True
    
    # AI options
    ai_provider: Optional[str] = "auto"
    tts_voice: Optional[str] = None
    narration_style: Optional[str] = "viral"  # viral, review, storytelling, professional, hài hước, dramatic
    rewrite_from_original: bool = True  # If True, transcribes original audio and rewrites it
    
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
    
    # Audio options
    background_music: bool = True
    bgm_style: str = "cinematic"
    normalize_audio: bool = True
    
    # AI options
    story_style: str = "storytelling"  # narrative, dramatic, humorous, viral, storytelling
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
    cost_estimate: Optional[str] = None
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


# ==================== EOA CHATBOT SCHEMAS ====================

class ChatMessage(BaseModel):
    """Single chat message"""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[dict] = None


class EOAChatRequest(BaseModel):
    """Request to chat with EOA AI"""
    message: str
    conversation_history: List[ChatMessage] = []
    session_id: Optional[str] = None
    ai_provider: Optional[str] = "auto"


class EOAChatResponse(BaseModel):
    """Response from EOA AI"""
    success: bool
    message: str
    suggestions: Optional[List[str]] = None
    collected_info: Optional[dict] = None
    ready_to_process: bool = False
    action_required: Optional[str] = None  # None | "confirm" | "process"


class EOAProcessRequest(BaseModel):
    """Request to process story and generate audio"""
    session_id: str
    conversation_history: List[ChatMessage]
    story_config: Optional[dict] = None  # Override AI-collected config
    voice: Optional[str] = None
    speed: float = 1.0
    add_pauses: bool = True
    ai_provider: Optional[str] = "auto"


class EOAProcessResponse(BaseModel):
    """Response after processing story to audio"""
    success: bool
    story_text: str
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    word_count: int = 0
    error: Optional[str] = None


# ==================== SPLIT SCREEN & ASPECT RATIO SCHEMAS ====================

class AspectRatioConvertRequest(BaseModel):
    """Request to convert video aspect ratio"""
    source_url: str
    target_ratio: str = "9:16"  # 9:16, 16:9, 1:1, 4:5
    method: str = "pad"  # pad, crop, fit
    background_color: str = "000000"


class SplitScreenMergeRequest(BaseModel):
    """Request to merge two videos side by side"""
    video1_url: str
    video2_url: str
    split_ratio: str = "1:1"  # 1:1, 2:1, 1:2
    output_ratio: str = "9:16"
    audio_source: str = "both"  # video1, video2, both, none


class HighlightExtractionRequest(BaseModel):
    """Request to extract highlights from long video"""
    source_url: str
    target_duration: int = 60  # Target output duration in seconds
    num_highlights: int = 5
class SeriesCreateRequest(BaseModel):
    """Request to create multi-part video series"""
    source_url: str
    topic: str
    num_parts: int = 3
    target_platform: str = "tiktok"
    voice_style: str = "cynical" # cynical, emotional, engaging
    bgm_style: str = "dramatic"
    ai_provider: Optional[str] = "auto"
    tts_provider: Optional[str] = "auto"
    tts_voice: Optional[str] = None


# ==================== YOUTUBE ANALYZER SCHEMAS ====================

class YouTubeAnalyzeRequest(BaseModel):
    """Request to analyze YouTube video"""
    youtube_url: str
    include_transcript: bool = True
    include_channel_analysis: bool = False
    min_score_threshold: float = 6.0
    target_platforms: List[str] = ["youtube", "tiktok", "facebook"]


class YouTubeChannelRequest(BaseModel):
    """Request to analyze YouTube channel"""
    channel_url: str
    max_videos: int = 50
    include_recommendations: bool = True


class YouTubeBatchRequest(BaseModel):
    """Request for batch video processing"""
    video_ids: List[str]
    filters: Optional[dict] = None
    processing_config: Optional[dict] = None


class AnalysisJobResponse(BaseModel):
    """Response for analysis job creation"""
    success: bool
    job_id: str
    message: str


class AnalysisScoreBreakdown(BaseModel):
    """Score breakdown for a single criteria"""
    score: float
    weight: float
    weighted: float
    reasoning: str


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    job_id: str
    status: str
    progress: float
    video_info: Optional[dict] = None
    engagement: Optional[dict] = None
    transcript: Optional[dict] = None
    nlp_analysis: Optional[dict] = None
    policy_check: Optional[dict] = None
    scoring: Optional[dict] = None
    recommendation: Optional[dict] = None
    error: Optional[str] = None


class ReportExportRequest(BaseModel):
    """Request to export analysis report"""
    job_id: str
    format: str = "json"  # json, pdf, csv
    include_transcript: bool = True
