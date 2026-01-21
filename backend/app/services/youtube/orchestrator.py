"""
YouTube Video Analyzer - Master Orchestrator
=============================================
Coordinates all 10-stage pipeline with proper sequencing,
error handling, retry logic, and progress tracking.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from app.core.logger import logger
from app.core.config import settings

# Import all stage services
from app.services.youtube.ingestion import ingestion_service, IngestionResult
from app.services.youtube.signal_analyzer import signal_analyzer, SignalAnalysisResult
from app.services.youtube.transcript_service import transcript_service, TranscriptResult
from app.services.youtube.nlp_service import nlp_service, NLPResult
from app.services.youtube.policy_evaluator import policy_evaluator, PolicyCheckResult
from app.services.youtube.scoring_engine import scoring_engine, FinalScoreResult
from app.services.youtube.trend_miner import trend_miner
from app.services.youtube.recommender import recommender
from app.services.youtube.report_generator import report_generator
from app.services.youtube.channel_analyzer import channel_analyzer
from app.services.storage.google_drive import google_drive_service


class PipelineStage(str, Enum):
    """Pipeline stages"""
    INGESTION = "ingestion"
    SIGNAL_ANALYSIS = "signal_analysis"
    TRANSCRIPTION = "transcription"
    NLP_ANALYSIS = "nlp_analysis"
    POLICY_CHECK = "policy_check"
    TREND_MINING = "trend_mining"
    SCORING = "scoring"
    RECOMMENDATION = "recommendation"
    FINALIZATION = "finalization" # Combined Processing & Export
    REPORTING = "reporting"


class PipelineStatus(str, Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StageResult:
    """Result from a single stage"""
    stage: PipelineStage
    success: bool
    data: Any
    duration_seconds: float
    error: Optional[str] = None


@dataclass
class PipelineState:
    """Current state of pipeline execution"""
    job_id: str
    status: PipelineStatus
    current_stage: Optional[PipelineStage]
    completed_stages: list[PipelineStage]
    results: dict[str, Any]
    progress: float  # 0-100
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    video_url: str
    max_duration: int = 3600
    min_score: float = 6.0
    skip_processing: bool = False
    skip_export: bool = False
    target_platform: str = "tiktok"


class MasterOrchestrator:
    """
    Master orchestrator for the 10-stage pipeline.
    
    Responsibilities:
    - Execute stages in order
    - Handle failures and retries
    - Track progress
    - Stop on policy violations
    - Aggregate results
    """
    
    MAX_RETRIES = 1
    STAGE_TIMEOUT = 300  # 5 minutes
    
    # Stage weights for progress calculation
    STAGE_WEIGHTS = {
        PipelineStage.INGESTION: 10,
        PipelineStage.SIGNAL_ANALYSIS: 10,
        PipelineStage.TRANSCRIPTION: 15,
        PipelineStage.NLP_ANALYSIS: 15,
        PipelineStage.POLICY_CHECK: 10,
        PipelineStage.TREND_MINING: 10,
        PipelineStage.SCORING: 5,
        PipelineStage.RECOMMENDATION: 10,
        PipelineStage.FINALIZATION: 10,
        PipelineStage.REPORTING: 10,
    }
    
    def __init__(self):
        self._active_jobs: dict[str, PipelineState] = {}
        self._progress_callbacks: dict[str, Callable] = {}
    
    async def run_pipeline(
        self,
        config: PipelineConfig,
        progress_callback: Callable = None
    ) -> PipelineState:
        """
        Run complete analysis pipeline.
        
        Args:
            config: Pipeline configuration
            progress_callback: Optional callback for progress updates
        """
        job_id = str(uuid.uuid4())
        
        state = PipelineState(
            job_id=job_id,
            status=PipelineStatus.RUNNING,
            current_stage=None,
            completed_stages=[],
            results={},
            progress=0,
            start_time=datetime.utcnow()
        )
        
        self._active_jobs[job_id] = state
        if progress_callback:
            self._progress_callbacks[job_id] = progress_callback
        
        try:
            # Stage 1: Video Ingestion
            await self._run_stage(
                state, 
                PipelineStage.INGESTION,
                self._stage_ingestion,
                config
            )
            
            # Check if ingestion succeeded
            if not state.results.get("ingestion", {}).get("success"):
                raise Exception("Video ingestion failed")
            
            video_id = state.results["ingestion"]["video_id"]
            
            # Stage 2: Signal Analysis
            await self._run_stage(
                state,
                PipelineStage.SIGNAL_ANALYSIS,
                self._stage_signal_analysis,
                video_id,
                state.results["ingestion"].get("metadata")
            )
            
            # Stage 3: Transcription
            await self._run_stage(
                state,
                PipelineStage.TRANSCRIPTION,
                self._stage_transcription,
                video_id,
                state.results["ingestion"].get("local_path")
            )
            
            # Check if transcript available
            transcript_text = state.results.get("transcription", {}).get("full_text", "")
            if not transcript_text:
                logger.warning("No transcript available, using metadata")
                transcript_text = state.results.get("ingestion", {}).get("metadata", {}).get("description", "")
            
            # Stage 4: NLP Analysis
            await self._run_stage(
                state,
                PipelineStage.NLP_ANALYSIS,
                self._stage_nlp_analysis,
                transcript_text,
                state.results.get("transcription", {}).get("segments", [])
            )
            
            # Stage 5: Policy Check
            await self._run_stage(
                state,
                PipelineStage.POLICY_CHECK,
                self._stage_policy_check,
                transcript_text,
                state.results.get("nlp_analysis", {}).get("keywords", [])
            )
            
            # Check policy - stop if high risk
            policy_result = state.results.get("policy_check", {})
            if policy_result.get("risk_level") == "high":
                logger.warning("High policy risk detected - stopping pipeline")
                state.results["recommendation"] = {
                    "download": False,
                    "reason": "High policy risk detected"
                }
                # Skip to scoring for final report
            
            # Stage 6: Trend Mining
            await self._run_stage(
                state,
                PipelineStage.TREND_MINING,
                self._stage_trend_mining,
                state.results["ingestion"].get("metadata"),
                state.results.get("nlp_analysis", {}).get("keywords", [])
            )
            
            # Stage 7: Scoring (Renumerated as Scoring follows Trend/Policy)
            # Need to get channel data first for accurate scoring
            await self._run_stage(
                state,
                PipelineStage.SCORING, # This is the "internal" scoring name
                self._stage_scoring,
                state.results,
                state.results["ingestion"].get("metadata", {}).get("channel_id")
            )
            
            # Check score threshold
            final_score = state.results.get("scoring", {}).get("final_score", 0)
            
            # Stage 8: Recommendation
            await self._run_stage(
                state,
                PipelineStage.RECOMMENDATION,
                self._stage_recommendation,
                state.results.get("ingestion", {}).get("metadata"),
                state.results.get("signal_analysis", {}),
                final_score
            )
            
            # Stage 9: Finalization (Processing & Optional Drive Sync)
            await self._run_stage(
                state,
                PipelineStage.FINALIZATION,
                self._stage_finalization,
                state,
                config
            )
            
            # Stage 10: Reporting
            await self._run_stage(
                state,
                PipelineStage.REPORTING,
                self._stage_reporting,
                state.results
            )
            
            # Mark complete
            state.status = PipelineStatus.COMPLETED
            state.progress = 100
            state.end_time = datetime.utcnow()
            
            await self._notify_progress(state)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            state.status = PipelineStatus.FAILED
            state.error = str(e)
            state.end_time = datetime.utcnow()
        
        finally:
            # Cleanup callbacks
            self._progress_callbacks.pop(job_id, None)
        
        return state
    
    async def _run_stage(
        self,
        state: PipelineState,
        stage: PipelineStage,
        handler: Callable,
        *args
    ):
        """Run a single stage with retry logic"""
        state.current_stage = stage
        logger.info(f"[{state.job_id}] Starting stage: {stage.value}")
        
        start_time = datetime.utcnow()
        last_error = None
        
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                # Run with timeout
                result = await asyncio.wait_for(
                    handler(*args),
                    timeout=self.STAGE_TIMEOUT
                )
                
                # Store result
                state.results[stage.value] = result
                state.completed_stages.append(stage)
                
                # Update progress
                completed_weight = sum(
                    self.STAGE_WEIGHTS.get(s, 0) 
                    for s in state.completed_stages
                )
                total_weight = sum(self.STAGE_WEIGHTS.values())
                state.progress = (completed_weight / total_weight) * 100
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"[{state.job_id}] Stage {stage.value} completed in {duration:.1f}s")
                
                await self._notify_progress(state)
                return
                
            except asyncio.TimeoutError:
                last_error = f"Stage {stage.value} timed out"
                logger.warning(f"Attempt {attempt + 1}: {last_error}")
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All retries failed
        state.results[stage.value] = {"error": last_error}
        logger.error(f"Stage {stage.value} failed after {self.MAX_RETRIES + 1} attempts")
    
    async def _notify_progress(self, state: PipelineState):
        """Notify progress callback if registered"""
        callback = self._progress_callbacks.get(state.job_id)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(state)
                else:
                    callback(state)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    # ==================== Stage Handlers ====================
    
    async def _stage_ingestion(self, config: PipelineConfig) -> dict:
        """Stage 1: Video Ingestion"""
        input_type, video_id = ingestion_service.detect_input_type(config.video_url)
        
        if not video_id:
            return {"success": False, "error": "Could not parse video ID"}
        
        # Validate video
        validation = await ingestion_service.validate_video(video_id)
        
        if not validation.can_download:
            return {
                "success": False,
                "error": validation.error_message,
                "validation": {
                    "is_available": validation.is_available,
                    "is_age_restricted": validation.is_age_restricted,
                    "duration_valid": validation.duration_valid
                }
            }
        
        # Get metadata
        metadata = await ingestion_service.get_video_metadata(video_id)
        
        return {
            "success": True,
            "video_id": video_id,
            "input_type": input_type.value,
            "metadata": {
                "title": metadata.title if metadata else "",
                "channel": metadata.channel_title if metadata else "",
                "duration": metadata.duration_seconds if metadata else 0,
                "views": metadata.view_count if metadata else 0,
                "likes": metadata.like_count if metadata else 0,
            } if metadata else None
        }
    
    async def _stage_signal_analysis(
        self,
        video_id: str,
        metadata: dict = None
    ) -> dict:
        """Stage 2: Signal Analysis"""
        result = await signal_analyzer.analyze(video_id, metadata)
        
        return {
            "engagement_score": result.engagement_score,
            "reasoning": result.reasoning,
            "metrics": {
                "like_view_ratio": result.engagement_metrics.like_view_ratio,
                "comment_view_ratio": result.engagement_metrics.comment_view_ratio,
                "views_per_day": result.engagement_metrics.views_per_day,
                "velocity_score": result.engagement_metrics.velocity_score
            }
        }
    
    async def _stage_transcription(
        self,
        video_id: str,
        local_path: str = None
    ) -> dict:
        """Stage 3: Transcription"""
        audio_path = Path(local_path).with_suffix(".mp3") if local_path else None
        
        result = await transcript_service.get_transcript(
            video_id,
            audio_path=audio_path
        )
        
        return {
            "success": result.success,
            "language": result.language,
            "full_text": result.full_text,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in result.segments
            ],
            "duration": result.duration_seconds,
            "provider": result.provider,
            "confidence": result.confidence
        }
    
    async def _stage_nlp_analysis(
        self,
        text: str,
        segments: list = None
    ) -> dict:
        """Stage 4: NLP Analysis"""
        result = await nlp_service.analyze(text, segments)
        
        return {
            "topics": [
                {"name": t.name, "keywords": t.keywords}
                for t in result.topics
            ],
            "keywords": result.keywords,
            "keyphrases": result.keyphrases,
            "sentiment": result.sentiment,
            "summary": result.summary,
            "provider": result.provider
        }
    
    async def _stage_policy_check(
        self,
        text: str,
        keywords: list[str] = None
    ) -> dict:
        """Stage 5: Policy Check"""
        result = await policy_evaluator.evaluate(text, keywords)
        
        return {
            "policy_safe": result.policy_safe,
            "risk_level": result.risk_level,
            "violations": result.violations,
            "positive_value": result.positive_value,
            "sensitive_topics": result.sensitive_topics,
            "reup_safe_score": result.reup_safe_score,
            "reasoning": result.reasoning,
            "provider": result.provider
        }
    
    async def _stage_scoring(self, all_results: dict, channel_id: str = None) -> dict:
        """Stage 7: Final Scoring"""
        # Extract data from previous stages
        content_data = all_results.get("nlp_analysis", {})
        engagement_data = all_results.get("signal_analysis", {})
        trend_data = all_results.get("trend_mining", {})
        policy_data = all_results.get("policy_check", {})
        
        # Fetch real channel data if available
        channel_data = {"channel_score": 5.0, "reasoning": "Channel ID missing"}
        if channel_id:
            logger.info(f"Fetching authority data for channel {channel_id}")
            channel_data = await channel_analyzer.analyze(channel_id)
        
        result = scoring_engine.calculate(
            content_data=content_data,
            engagement_data=engagement_data,
            trend_data=trend_data,
            policy_data=policy_data,
            channel_data=channel_data
        )
        
        return {
            "final_score": result.final_score,
            "grade": result.grade,
            "breakdown": result.breakdown,
            "deductions": result.deductions,
            "explanation": result.explanation,
            "recommendation": result.recommendation
        }
    
    async def _stage_trend_mining(self, metadata: dict, topics: list) -> dict:
        """Stage 6: Trend Mining"""
        return await trend_miner.mine_trends(metadata, topics)
        
    async def _stage_recommendation(self, metadata: dict, signals: dict, score: float) -> dict:
        """Stage 8: Recommendation"""
        return await recommender.generate_recommendations(metadata, signals, score)
        
    async def _stage_finalization(self, state: PipelineState, config: PipelineConfig) -> dict:
        """Stage 9: Finalization (Processing & Export)"""
        results = {}
        
        # 1. Automated Processing (Auto-trigger Reup logic)
        final_score = state.results.get("scoring", {}).get("final_score", 0)
        if not config.skip_processing and final_score >= 8.0:
            logger.info(f"Auto-triggering processing for high-score video: {state.job_id}")
            results["processing"] = {
                "auto_triggered": True,
                "status": "READY_FOR_REUP",
                "message": f"High score {final_score} - Recommended for Reup."
            }
            
        # 2. Export & Drive Sync
        if not config.skip_export:
            try:
                # Create a summary JSON for export
                export_path = Path(settings.TEMP_DIR) / f"analysis_export_{state.job_id}.json"
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(state.results, f, indent=2, ensure_ascii=False)
                
                # Upload to Drive
                if settings.GOOGLE_DRIVE_FOLDER_ID:
                    drive_id = await google_drive_service.upload_file(
                        export_path,
                        f"Analysis_{state.job_id}.json",
                        settings.GOOGLE_DRIVE_FOLDER_ID
                    )
                    results["export"] = {"success": True, "drive_id": drive_id}
                else:
                    results["export"] = {"success": True, "local_path": str(export_path)}
            except Exception as e:
                logger.error(f"Export failed: {e}")
                results["export"] = {"success": False, "error": str(e)}
        
        return results

    async def _stage_reporting(self, all_data: dict) -> dict:
        """Stage 10: Reporting"""
        return await report_generator.generate_final_report(all_data)
    
    def get_job_status(self, job_id: str) -> Optional[PipelineState]:
        """Get status of a pipeline job"""
        return self._active_jobs.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        job = self._active_jobs.get(job_id)
        if job and job.status == PipelineStatus.RUNNING:
            job.status = PipelineStatus.CANCELLED
            return True
        return False


# Singleton instance
orchestrator = MasterOrchestrator()
