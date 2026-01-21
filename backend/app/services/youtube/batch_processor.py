"""
YouTube Video Analyzer - Stage 3: Batch Processor
==================================================
Multi-video download and processing queue with parallel execution.
"""

import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

from app.core.logger import logger
from app.core.config import settings
from app.services.youtube.ingestion import ingestion_service
from app.services.youtube.orchestrator import orchestrator, PipelineConfig


class BatchStatus(str, Enum):
    """Batch job status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoStatus(str, Enum):
    """Individual video status in batch"""
    QUEUED = "queued"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchVideoItem:
    """Video item in batch queue"""
    video_id: str
    title: str = ""
    status: VideoStatus = VideoStatus.QUEUED
    score: float = 0
    analysis_result: dict = field(default_factory=dict)
    processed_path: Optional[Path] = None
    error: Optional[str] = None


@dataclass
class BatchJob:
    """Batch processing job"""
    batch_id: str
    status: BatchStatus
    videos: list[BatchVideoItem]
    config: dict
    
    # Progress tracking
    total_count: int = 0
    analyzed_count: int = 0
    processed_count: int = 0
    failed_count: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    output_folder: Optional[Path] = None
    
    @property
    def progress(self) -> float:
        if self.total_count == 0:
            return 0
        return ((self.analyzed_count + self.processed_count) / (self.total_count * 2)) * 100


class BatchProcessor:
    """
    Batch video processing service.
    - Queue management
    - Parallel analysis
    - Progress tracking
    - Error recovery
    """
    
    MAX_CONCURRENT = 3  # Max parallel analyses
    MIN_SCORE_FOR_DOWNLOAD = 6.0
    
    def __init__(self):
        self._jobs: dict[str, BatchJob] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._lock = asyncio.Lock()
    
    async def create_batch(
        self,
        video_ids: list[str],
        config: dict = None
    ) -> BatchJob:
        """
        Create a new batch processing job.
        
        Args:
            video_ids: List of YouTube video IDs
            config: Processing configuration
        """
        batch_id = str(uuid.uuid4())[:8]
        
        # Create video items
        videos = [
            BatchVideoItem(video_id=vid)
            for vid in video_ids
        ]
        
        job = BatchJob(
            batch_id=batch_id,
            status=BatchStatus.PENDING,
            videos=videos,
            config=config or {},
            total_count=len(videos)
        )
        
        self._jobs[batch_id] = job
        
        return job
    
    async def start_batch(
        self,
        batch_id: str,
        progress_callback: Callable = None
    ) -> BatchJob:
        """Start processing a batch job"""
        job = self._jobs.get(batch_id)
        if not job:
            raise ValueError(f"Batch not found: {batch_id}")
        
        job.status = BatchStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        # Start processing
        asyncio.create_task(self._process_batch(job, progress_callback))
        
        return job
    
    async def _process_batch(
        self,
        job: BatchJob,
        progress_callback: Callable = None
    ):
        """Process all videos in batch"""
        try:
            # Phase 1: Analyze all videos
            await self._analyze_batch(job, progress_callback)
            
            # Phase 2: Filter and download recommended videos
            recommended = [v for v in job.videos if v.score >= self.MIN_SCORE_FOR_DOWNLOAD]
            
            logger.info(f"Batch {job.batch_id}: {len(recommended)}/{len(job.videos)} videos recommended")
            
            # Phase 3: Process videos (if configured)
            if job.config.get("auto_process", False):
                await self._process_videos(job, recommended, progress_callback)
            
            job.status = BatchStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            job.status = BatchStatus.FAILED
            job.completed_at = datetime.utcnow()
        
        if progress_callback:
            await self._notify(progress_callback, job)
    
    async def _analyze_batch(
        self,
        job: BatchJob,
        progress_callback: Callable = None
    ):
        """Analyze all videos in parallel"""
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        
        async def analyze_one(video: BatchVideoItem):
            async with semaphore:
                try:
                    video.status = VideoStatus.ANALYZING
                    
                    # Get video metadata first
                    metadata = await ingestion_service.get_video_metadata(video.video_id)
                    if metadata:
                        video.title = metadata.title
                    
                    # Run quick analysis
                    config = PipelineConfig(
                        video_url=f"https://youtube.com/watch?v={video.video_id}",
                        min_score=0  # Analyze all, filter later
                    )
                    
                    result = await orchestrator.run_pipeline(config)
                    
                    if result.status.value == "completed":
                        video.status = VideoStatus.ANALYZED
                        video.analysis_result = result.results
                        video.score = result.results.get("scoring", {}).get("final_score", 0)
                    else:
                        video.status = VideoStatus.FAILED
                        video.error = result.error
                        job.failed_count += 1
                    
                    job.analyzed_count += 1
                    
                except Exception as e:
                    logger.error(f"Analysis error for {video.video_id}: {e}")
                    video.status = VideoStatus.FAILED
                    video.error = str(e)
                    job.failed_count += 1
                    job.analyzed_count += 1
                
                if progress_callback:
                    await self._notify(progress_callback, job)
        
        # Process all videos in parallel
        tasks = [analyze_one(v) for v in job.videos]
        await asyncio.gather(*tasks)
    
    async def _process_videos(
        self,
        job: BatchJob,
        videos: list[BatchVideoItem],
        progress_callback: Callable = None
    ):
        """Download and process recommended videos"""
        from app.services.video_editor import video_editor
        
        output_dir = settings.PROCESSED_DIR / f"batch_{job.batch_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        job.output_folder = output_dir
        
        for video in videos:
            try:
                video.status = VideoStatus.DOWNLOADING
                
                # Download video
                result = await ingestion_service.download_video(
                    video.video_id,
                    output_dir
                )
                
                if not result.success:
                    video.status = VideoStatus.FAILED
                    video.error = result.error
                    continue
                
                video.status = VideoStatus.PROCESSING
                
                # Process video (basic reup processing)
                processed_path = await video_editor.process_video_for_reup(
                    video_path=result.local_path,
                    output_dir=output_dir,
                    target_platform=job.config.get("target_platform", "tiktok")
                )
                
                if processed_path and processed_path.exists():
                    video.status = VideoStatus.COMPLETED
                    video.processed_path = processed_path
                    job.processed_count += 1
                else:
                    video.status = VideoStatus.FAILED
                    video.error = "Processing failed"
                
            except Exception as e:
                logger.error(f"Processing error for {video.video_id}: {e}")
                video.status = VideoStatus.FAILED
                video.error = str(e)
            
            if progress_callback:
                await self._notify(progress_callback, job)
    
    async def _notify(self, callback: Callable, job: BatchJob):
        """Notify progress callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(job)
            else:
                callback(job)
        except Exception as e:
            logger.warning(f"Callback error: {e}")
    
    def get_job(self, batch_id: str) -> Optional[BatchJob]:
        """Get batch job by ID"""
        return self._jobs.get(batch_id)
    
    def get_job_summary(self, batch_id: str) -> dict:
        """Get batch job summary"""
        job = self._jobs.get(batch_id)
        if not job:
            return {}
        
        return {
            "batch_id": job.batch_id,
            "status": job.status.value,
            "progress": round(job.progress, 1),
            "total": job.total_count,
            "analyzed": job.analyzed_count,
            "processed": job.processed_count,
            "failed": job.failed_count,
            "recommended": len([v for v in job.videos if v.score >= self.MIN_SCORE_FOR_DOWNLOAD]),
            "videos": [
                {
                    "video_id": v.video_id,
                    "title": v.title,
                    "status": v.status.value,
                    "score": v.score,
                    "error": v.error
                }
                for v in job.videos
            ]
        }
    
    def cancel_job(self, batch_id: str) -> bool:
        """Cancel a batch job"""
        job = self._jobs.get(batch_id)
        if job and job.status == BatchStatus.RUNNING:
            job.status = BatchStatus.CANCELLED
            return True
        return False
    
    def get_recommendations(self, batch_id: str) -> list[dict]:
        """Get recommended videos from batch"""
        job = self._jobs.get(batch_id)
        if not job:
            return []
        
        recommended = [
            v for v in job.videos 
            if v.score >= self.MIN_SCORE_FOR_DOWNLOAD
        ]
        
        # Sort by score
        recommended.sort(key=lambda x: x.score, reverse=True)
        
        return [
            {
                "video_id": v.video_id,
                "title": v.title,
                "score": v.score,
                "reasoning": v.analysis_result.get("scoring", {}).get("explanation", "")
            }
            for v in recommended
        ]


# Singleton instance
batch_processor = BatchProcessor()
