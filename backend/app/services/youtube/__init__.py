"""
YouTube Video Analyzer - Package Init (Complete)
=================================================
Exports all services for the complete 10-stage pipeline.
"""

# Stage 1: Video Ingestion
from app.services.youtube.ingestion import (
    VideoIngestionService,
    ingestion_service,
    InputType,
    ValidationResult,
    VideoMetadata,
    IngestionResult
)

# Stage 2: Signal Analysis
from app.services.youtube.signal_analyzer import (
    SignalAnalyzer,
    signal_analyzer,
    EngagementMetrics,
    SignalAnalysisResult
)

# Stage 2b: Channel Analysis
from app.services.youtube.channel_analyzer import (
    ChannelAnalyzer,
    channel_analyzer,
    ChannelInfo,
    ChannelVideoInfo,
    ChannelAnalysis
)

# Stage 3: Transcription
from app.services.youtube.transcript_service import (
    TranscriptService,
    transcript_service,
    TranscriptResult,
    TranscriptSegment
)

# Stage 4: NLP Analysis
from app.services.youtube.nlp_service import (
    NLPService,
    nlp_service,
    NLPResult,
    TopicSegment
)

# Stage 5: Policy Evaluation
from app.services.youtube.policy_evaluator import (
    PolicyEvaluator,
    policy_evaluator,
    PolicyCheckResult
)

# Stage 6: Scoring Engine
from app.services.youtube.scoring_engine import (
    ScoringEngine,
    scoring_engine,
    ScoreBreakdown,
    ScoreDeduction,
    FinalScoreResult
)

# Stage 7-8: Batch Processing
from app.services.youtube.batch_processor import (
    BatchProcessor,
    batch_processor,
    BatchJob,
    BatchVideoItem,
    BatchStatus,
    VideoStatus
)

# Stage 9: Drive Upload
from app.services.youtube.drive_uploader import (
    GoogleDriveUploader,
    drive_uploader,
    DriveFolder,
    DriveFile,
    UploadResult
)

# Master Orchestrator
from app.services.youtube.orchestrator import (
    MasterOrchestrator,
    orchestrator,
    PipelineConfig,
    PipelineStatus,
    PipelineStage,
    PipelineState
)

# Agent Prompts
from app.services.youtube.agent_prompts import (
    AgentPrompt,
    AGENT_REGISTRY,
    get_agent_prompt,
    get_all_agents,
    format_agent_system_prompt,
    GLOBAL_RULES
)


__all__ = [
    # Stage 1
    "VideoIngestionService", "ingestion_service", "InputType",
    "ValidationResult", "VideoMetadata", "IngestionResult",
    
    # Stage 2
    "SignalAnalyzer", "signal_analyzer", "EngagementMetrics", "SignalAnalysisResult",
    
    # Stage 2b
    "ChannelAnalyzer", "channel_analyzer", "ChannelInfo", "ChannelVideoInfo", "ChannelAnalysis",
    
    # Stage 3
    "TranscriptService", "transcript_service", "TranscriptResult", "TranscriptSegment",
    
    # Stage 4
    "NLPService", "nlp_service", "NLPResult", "TopicSegment",
    
    # Stage 5
    "PolicyEvaluator", "policy_evaluator", "PolicyCheckResult",
    
    # Stage 6
    "ScoringEngine", "scoring_engine", "ScoreBreakdown", "ScoreDeduction", "FinalScoreResult",
    
    # Stage 7-8
    "BatchProcessor", "batch_processor", "BatchJob", "BatchVideoItem", "BatchStatus", "VideoStatus",
    
    # Stage 9
    "GoogleDriveUploader", "drive_uploader", "DriveFolder", "DriveFile", "UploadResult",
    
    # Orchestrator
    "MasterOrchestrator", "orchestrator", "PipelineConfig", "PipelineStatus", "PipelineStage", "PipelineState",
    
    # Prompts
    "AgentPrompt", "AGENT_REGISTRY", "get_agent_prompt", "get_all_agents", "format_agent_system_prompt", "GLOBAL_RULES",
]
