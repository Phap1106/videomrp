from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
import asyncio
from pathlib import Path
import shutil

from app.database import get_db
from app.models import VideoJob, JobStatus, Platform, VideoType
from app.schemas import (
    VideoCreateRequest, VideoAnalyzeRequest, JobResponse, 
    AnalysisResult, PlatformSettings, SystemStatus, 
    PaginatedResponse, SuccessResponse, ErrorResponse
)
from app.services.video_downloader import VideoDownloader
from app.services.content_analyzer import ContentAnalyzer
from app.services.video_editor import VideoEditor
from app.services.platform_detector import PlatformDetector
from app.core.config import settings
from app.core.logger import logger
from app.utils.file_utils import ensure_dirs, get_file_hash


router = APIRouter()


# Health and status endpoints
@router.get("/health", response_model=SystemStatus)
async def health_check():
    """Health check endpoint"""
    from redis import Redis
    import psutil
    import time
    
    checks = {
        "api": True,
        "database": False,
        "redis": False,
        "storage": False,
        "ai_services": {},
        "queue_size": 0,
        "active_jobs": 0,
        "total_jobs": 0,
        "uptime": time.time() - psutil.boot_time(),
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }
    
    try:
        # Test database
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    try:
        # Test Redis
        redis_client = Redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        checks["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    # Test storage
    if Path("data").exists() and Path("data").is_dir():
        try:
            test_file = Path("data/test.txt")
            test_file.write_text("test")
            test_file.unlink()
            checks["storage"] = True
        except:
            pass
    
    # Check AI services
    checks["ai_services"] = {
        "openai": bool(settings.OPENAI_API_KEY),
        "gemini": bool(settings.GEMINI_API_KEY),
    }
    
    # Get job statistics
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        checks["total_jobs"] = db.query(VideoJob).count()
        checks["active_jobs"] = db.query(VideoJob).filter(
            VideoJob.status.in_([JobStatus.PROCESSING, JobStatus.ANALYZING, JobStatus.DOWNLOADING])
        ).count()
        db.close()
    except:
        pass
    
    status_code = 200 if all([checks["api"], checks["database"], checks["redis"], checks["storage"]]) else 503
    
    return JSONResponse(
        status_code=status_code,
        content=checks
    )


@router.get("/platforms", response_model=List[PlatformSettings])
async def get_platforms():
    """Get available platforms and their settings"""
    detector = PlatformDetector()
    platforms = []
    
    for platform in Platform:
        if platform == Platform.GENERIC:
            continue
            
        # Check if platform is enabled
        enabled_attr = f"ENABLE_{platform.value.upper()}"
        if not getattr(settings, enabled_attr, True):
            continue
        
        rules = detector.get_platform_rules(platform)
        platforms.append(PlatformSettings(
            platform=platform,
            name=platform.value.capitalize(),
            **rules
        ))
    
    return platforms


# Video job endpoints
@router.post("/jobs", response_model=JobResponse)
async def create_job(
    request: VideoCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new video processing job"""
    # Validate platform is enabled
    enabled_attr = f"ENABLE_{request.target_platform.value.upper()}"
    if not getattr(settings, enabled_attr, True):
        raise HTTPException(
            status_code=400,
            detail=f"Platform {request.target_platform.value} is not enabled"
        )
    
    # Create job record
    job_id = str(uuid.uuid4())
    
    # Detect source platform
    detector = PlatformDetector()
    source_platform = detector.detect(request.source_url)
    
    job = VideoJob(
        id=job_id,
        title=request.title or f"Video {job_id[:8]}",
        source_url=request.source_url,
        source_platform=source_platform,
        target_platform=request.target_platform,
        video_type=request.video_type,
        duration=request.duration,
        add_subtitles=request.add_subtitles,
        change_music=request.change_music,
        remove_watermark=request.remove_watermark,
        add_effects=request.add_effects,
        meme_template=request.meme_template,
        status=JobStatus.PENDING
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start processing in background
    background_tasks.add_task(process_video_job, db, job_id)
    
    return job


@router.get("/jobs", response_model=PaginatedResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[JobStatus] = None,
    platform: Optional[Platform] = None,
    db: Session = Depends(get_db)
):
    """List video jobs with pagination"""
    query = db.query(VideoJob)
    
    # Apply filters
    if status:
        query = query.filter(VideoJob.status == status)
    if platform:
        query = query.filter(VideoJob.target_platform == platform)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    items = query.order_by(VideoJob.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return PaginatedResponse(
        items=[item.to_dict() for item in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job details"""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job.to_dict()


@router.delete("/jobs/{job_id}", response_model=SuccessResponse)
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job"""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete associated files
    if job.input_path and Path(job.input_path).exists():
        Path(job.input_path).unlink(missing_ok=True)
    if job.output_path and Path(job.output_path).exists():
        Path(job.output_path).unlink(missing_ok=True)
    
    db.delete(job)
    db.commit()
    
    return SuccessResponse(success=True, message="Job deleted successfully")


@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry a failed job"""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.FAILED:
        raise HTTPException(status_code=400, detail="Job is not in failed state")
    
    # Reset job status
    job.status = JobStatus.PENDING
    job.progress = 0
    job.current_step = "initializing"
    job.error_message = None
    db.commit()
    
    # Restart processing
    background_tasks.add_task(process_video_job, db, job_id)
    
    return job.to_dict()


# Video processing endpoints
@router.post("/analyze", response_model=AnalysisResult)
async def analyze_video(
    request: VideoAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """Analyze video without processing"""
    # Create temporary job for analysis
    job_id = str(uuid.uuid4())
    
    detector = PlatformDetector()
    source_platform = detector.detect(request.source_url)
    
    job = VideoJob(
        id=job_id,
        title="Video Analysis",
        source_url=request.source_url,
        source_platform=source_platform,
        target_platform=request.target_platform,
        status=JobStatus.ANALYZING
    )
    
    db.add(job)
    db.commit()
    
    try:
        # Download video
        downloader = VideoDownloader()
        work_dir = Path(settings.TEMP_DIR) / job_id
        work_dir.mkdir(parents=True, exist_ok=True)
        
        download_result = await downloader.download(request.source_url, work_dir)
        job.input_path = download_result["path"]
        db.commit()
        
        # Analyze content
        analyzer = ContentAnalyzer()
        
        analysis_result = await analyzer.analyze_video(
            video_path=download_result["path"],
            platform=request.target_platform.value,
            video_type="short"
        )
        
        # Update job with analysis result
        job.analysis_result = analysis_result
        job.status = JobStatus.COMPLETED
        db.commit()
        
        # Clean up downloaded file
        if Path(download_result["path"]).exists():
            Path(download_result["path"]).unlink()
        
        return AnalysisResult(
            job_id=job_id,
            summary=analysis_result["analysis"].get("summary", ""),
            category=analysis_result["analysis"].get("category", ""),
            mood=analysis_result["analysis"].get("mood", ""),
            duration=analysis_result["video_metadata"].get("duration", 0),
            key_moments=analysis_result["analysis"].get("key_moments", []),
            scenes=analysis_result.get("segments", []),
            copyright_risks=analysis_result["copyright_check"].get("copyright_risks", []),
            suggestions=analysis_result["editing_instructions"],
            hashtags=analysis_result["hashtags"].get("hashtags", []),
            titles=analysis_result["hashtags"].get("titles", []),
            viral_score=analysis_result["analysis"].get("viral_potential", 0),
            processing_time=analysis_result["processing_time"]
        )
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/processed/{filename}")
async def get_processed_video(filename: str):
    """Get processed video file"""
    file_path = Path(settings.PROCESSED_DIR) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename
    )


# Batch operations
@router.post("/batch", response_model=List[JobResponse])
async def create_batch_jobs(
    requests: List[VideoCreateRequest],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create multiple jobs in batch"""
    jobs = []
    
    for request in requests:
        job_id = str(uuid.uuid4())
        
        detector = PlatformDetector()
        source_platform = detector.detect(request.source_url)
        
        job = VideoJob(
            id=job_id,
            title=request.title or f"Video {job_id[:8]}",
            source_url=request.source_url,
            source_platform=source_platform,
            target_platform=request.target_platform,
            video_type=request.video_type,
            duration=request.duration,
            add_subtitles=request.add_subtitles,
            change_music=request.change_music,
            remove_watermark=request.remove_watermark,
            add_effects=request.add_effects,
            meme_template=request.meme_template,
            status=JobStatus.PENDING
        )
        
        db.add(job)
        jobs.append(job)
    
    db.commit()
    
    # Start processing for each job
    for job in jobs:
        background_tasks.add_task(process_video_job, db, job.id)
    
    return [job.to_dict() for job in jobs]


# Upload endpoint
@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    target_platform: Platform = Platform.TIKTOK,
    video_type: VideoType = VideoType.SHORT,
    duration: int = 60,
    db: Session = Depends(get_db)
):
    """Upload video file"""
    # Validate file size
    max_size = settings.MAX_UPLOAD_SIZE * 1024 * 1024  # Convert MB to bytes
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE}MB"
        )
    
    # Validate file type
    allowed_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file
    ensure_dirs()
    job_id = str(uuid.uuid4())
    upload_dir = Path(settings.UPLOAD_DIR) / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create job record
    job = VideoJob(
        id=job_id,
        title=file.filename,
        source_url=f"file://{file_path}",
        source_platform=Platform.GENERIC,
        target_platform=target_platform,
        video_type=video_type,
        duration=duration,
        input_path=str(file_path),
        status=JobStatus.PENDING
    )
    
    db.add(job)
    db.commit()
    
    # Start processing in background
    from app.main import process_video_job
    import asyncio
    asyncio.create_task(process_video_job(db, job_id))
    
    return job.to_dict()


# System endpoints
@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    stats = {}
    
    # Job statistics
    stats["total_jobs"] = db.query(VideoJob).count()
    stats["completed_jobs"] = db.query(VideoJob).filter(
        VideoJob.status == JobStatus.COMPLETED
    ).count()
    stats["failed_jobs"] = db.query(VideoJob).filter(
        VideoJob.status == JobStatus.FAILED
    ).count()
    stats["active_jobs"] = db.query(VideoJob).filter(
        VideoJob.status.in_([JobStatus.PROCESSING, JobStatus.ANALYZING, JobStatus.DOWNLOADING])
    ).count()
    
    # Platform distribution
    platforms = {}
    for platform in Platform:
        count = db.query(VideoJob).filter(VideoJob.target_platform == platform).count()
        if count > 0:
            platforms[platform.value] = count
    stats["platform_distribution"] = platforms
    
    # Storage usage
    upload_dir = Path(settings.UPLOAD_DIR)
    processed_dir = Path(settings.PROCESSED_DIR)
    
    stats["storage_usage"] = {
        "uploads": sum(f.stat().st_size for f in upload_dir.rglob('*') if f.is_file()),
        "processed": sum(f.stat().st_size for f in processed_dir.rglob('*') if f.is_file()),
    }
    
    return stats


# Background task function
async def process_video_job(db: Session, job_id: str):
    """Process video job in background"""
    from app.database import SessionLocal
    
    # Create new session for background task
    db = SessionLocal()
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    
    if not job:
        logger.error(f"Job {job_id} not found")
        return
    
    try:
        # Update job status
        job.status = JobStatus.DOWNLOADING
        job.progress = 10
        job.current_step = "Downloading video"
        db.commit()
        
        # Step 1: Download video
        downloader = VideoDownloader()
        work_dir = Path(settings.TEMP_DIR) / job_id
        work_dir.mkdir(parents=True, exist_ok=True)
        
        download_result = await downloader.download(job.source_url, work_dir)
        job.input_path = download_result["path"]
        job.progress = 30
        job.current_step = "Analyzing content"
        db.commit()
        
        # Step 2: Analyze content
        analyzer = ContentAnalyzer()
        analysis_result = await analyzer.analyze_video(
            video_path=download_result["path"],
            platform=job.target_platform.value,
            video_type=job.video_type.value
        )
        
        job.analysis_result = analysis_result
        job.progress = 50
        job.current_step = "Generating editing instructions"
        db.commit()
        
        # Step 3: Generate editing instructions
        editing_instructions = analysis_result["editing_instructions"]
        job.ai_instructions = editing_instructions
        job.progress = 60
        job.current_step = "Editing video"
        db.commit()
        
        # Step 4: Edit video
        editor = VideoEditor()
        
        # Ensure processed directory exists
        processed_dir = Path(settings.PROCESSED_DIR) / job_id
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = processed_dir / f"{job_id}.mp4"
        
        edit_result = await editor.edit_video(
            input_path=download_result["path"],
            instructions=editing_instructions,
            output_path=str(output_path),
            platform=job.target_platform.value
        )
        
        job.output_path = str(output_path)
        job.output_filename = f"{job_id}.mp4"
        job.progress = 90
        job.current_step = "Finalizing"
        db.commit()
        
        # Step 5: Clean up temporary files
        if work_dir.exists():
            shutil.rmtree(work_dir)
        
        # Step 6: Update job as completed
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.current_step = "Completed"
        db.commit()
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.current_step = "Failed"
        db.commit()
    
    finally:
        db.close()