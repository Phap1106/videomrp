"""
Main API Endpoints for Video Processing
"""

import uuid
import time
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Query, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.config import settings
from app.database import get_db, SessionLocal
from app.models import VideoJob, JobStatus
from app.schemas import (
    VideoCreateRequest,
    StoryVideoRequest,
    TTSRequest,
    VoicePreviewRequest,
    VideoAnalyzeRequest,
    TextOverlayRequest,
    VideoOutputResponse,
    HealthResponse,
    VoiceOption,
    ProcessingFlowOption,
)
from app.services.ai.tts_provider import get_tts_provider
from app.services.ai.transcription_service import get_transcription_provider
from app.services.ai.story_generator import get_story_generator
from app.services.video_downloader import VideoDownloader
from app.services.audio_processor import audio_processor
from app.services.text_overlay_engine import text_overlay_engine, TextStyle
from app.services.video_editor import video_editor
from app.utils.file_utils import ensure_dirs

router = APIRouter()


# ==================== HEALTH & INFO ====================

@router.get("/health")
async def health_check() -> HealthResponse:
    """Check system health"""
    try:
        from redis import Redis
        redis_client = Redis.from_url(settings.REDIS_URL)
        redis_ok = bool(redis_client.ping())
    except:
        redis_ok = False

    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db_ok = True
        db.close()
    except:
        db_ok = False

    try:
        import psutil
        uptime = time.time() - psutil.boot_time()
    except:
        uptime = 0

    # Check AI services
    ai_services = {}
    if settings.OPENAI_API_KEY:
        ai_services["openai"] = True
    if settings.GOOGLE_API_KEY:
        ai_services["google"] = True

    return HealthResponse(
        api=True,
        database=db_ok,
        redis=redis_ok,
        storage=Path(settings.DATA_DIR).exists(),
        ai_services=ai_services,
        queue_size=0,
        active_jobs=0,
        uptime=uptime,
    )


@router.get("/voices")
async def get_available_voices(ai_provider: Optional[str] = None) -> list[VoiceOption]:
    """Get available TTS voices"""
    try:
        provider = ai_provider or settings.TTS_PROVIDER
        tts = await get_tts_provider(provider)
        voices = await tts.get_available_voices()

        return [
            VoiceOption(
                id=v.get("id", ""),
                name=v.get("name", ""),
                gender=v.get("gender", ""),
                language=v.get("language", ""),
            )
            for v in voices
        ]
    except Exception as e:
        logger.error(f"Error fetching voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processing-flows")
async def get_processing_flows() -> list[ProcessingFlowOption]:
    """Get available processing flows"""
    return [
        ProcessingFlowOption(
            key="auto",
            label="Auto (Recommended)",
            description="Automatically optimize for the target platform",
            duration_estimate=300,
            options={},
        ),
        ProcessingFlowOption(
            key="fast",
            label="Fast Processing",
            description="Quick processing with minimal AI operations",
            duration_estimate=120,
            options={
                "skip_analysis": True,
                "skip_optimization": True,
            },
        ),
        ProcessingFlowOption(
            key="ai",
            label="AI-Enhanced",
            description="Full AI processing for best quality",
            duration_estimate=600,
            options={
                "full_analysis": True,
                "ai_rewrite": True,
                "copyright_check": True,
            },
        ),
        ProcessingFlowOption(
            key="full",
            label="Full Processing",
            description="Complete processing with all features",
            duration_estimate=900,
            options={
                "full_analysis": True,
                "ai_rewrite": True,
                "copyright_check": True,
                "optimize_quality": True,
            },
        ),
    ]


# ==================== TTS ENDPOINTS ====================

@router.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    """Generate text-to-speech audio"""
    try:
        logger.info(f"Generating TTS:  {request.text[: 100]}...")

        provider = request.ai_provider or settings.TTS_PROVIDER
        tts = await get_tts_provider(provider)

        output_path = await tts.synthesize(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            pitch=request.pitch,
            output_path=Path(settings.TEMP_DIR) / f"tts_{uuid.uuid4()}.mp3",
        )

        return {
            "success": True,
            "audio_path": str(output_path),
            "provider": provider,
            "voice":  request.voice,
        }
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts/preview-voice")
async def preview_voice(request: VoicePreviewRequest):
    """Preview AI voice"""
    try:
        provider = request.ai_provider or settings.TTS_PROVIDER
        tts = await get_tts_provider(provider)

        audio_path = await tts.preview_voice(
            voice=request.voice_id,
            text=request.sample_text,
        )

        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename=f"preview_{request.voice_id}.mp3",
        )
    except Exception as e:
        logger.error(f"Voice preview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TRANSCRIPTION ENDPOINTS ====================

@router.post("/transcription/transcribe")
async def transcribe_video(
    video_url: str = Query(...),
    language: str = Query(default="vi"),
):
    """Transcribe video audio"""
    try:
        logger.info(f"Transcribing video: {video_url}")

        # Download video
        downloader = VideoDownloader()
        download_result = await downloader.download(
            video_url,
            Path(settings.TEMP_DIR),
        )

        video_path = Path(download_result["path"])

        # Extract audio
        audio_path = await audio_processor.extract_audio(video_path)

        # Transcribe
        transcriber = await get_transcription_provider(settings.AI_PROVIDER)
        result = await transcriber.transcribe(audio_path, language=language)

        return {
            "success": True,
            "text": result["text"],
            "segments": result["segments"],
            "language": result["language"],
            "duration": result["duration"],
        }
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STORY GENERATION ENDPOINTS ====================

@router.post("/story/generate")
async def generate_story(
    prompt: str = Query(...),
    max_length: int = Query(default=1000),
    style: str = Query(default="narrative"),
    language: str = Query(default="vi"),
):
    """Generate AI story"""
    try:
        logger.info(f"Generating {style} story")

        story_gen = await get_story_generator(settings.AI_PROVIDER)
        story = await story_gen.generate_story(
            prompt=prompt,
            max_length=max_length,
            style=style,
            language=language,
        )

        return {
            "success": True,
            "story": story,
            "style": style,
            "length": len(story),
        }
    except Exception as e:
        logger.error(f"Story generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/story/rewrite-transcript")
async def rewrite_transcript(
    original_text: str = Query(...),
    style: str = Query(default="improved"),
):
    """Rewrite transcript with AI"""
    try: 
        logger.info(f"Rewriting transcript in {style} style")

        story_gen = await get_story_generator(settings.AI_PROVIDER)
        result = await story_gen.rewrite_transcript(
            original_text=original_text,
            segments=[],  # Simplified - no timing info
            style=style,
        )

        return {
            "success": True,
            "original":  result["original_text"],
            "rewritten": result["rewritten_text"],
            "style": style,
        }
    except Exception as e:
        logger.error(f"Transcript rewriting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/story/narration")
async def generate_narration(
    topic: str = Query(...),
    duration: int = Query(default=60),
    tone: str = Query(default="professional"),
):
    """Generate narration for video"""
    try: 
        logger.info(f"Generating {tone} narration for {duration}s")

        story_gen = await get_story_generator(settings.AI_PROVIDER)
        narration = await story_gen.generate_narration(
            topic=topic,
            duration=duration,
            tone=tone,
        )

        return {
            "success":  True,
            "narration":  narration,
            "duration":  duration,
            "tone": tone,
        }
    except Exception as e: 
        logger.error(f"Narration generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== VIDEO PROCESSING ENDPOINTS ====================

@router.post("/videos/process-reup")
async def process_reup_video(
    request: VideoCreateRequest,
    background_tasks: BackgroundTasks,
):
    """Process video for reupload with AI"""
    try:
        logger.info(f"Processing reup video: {request.source_url}")

        job_id = str(uuid.uuid4())

        # Create job record
        db = SessionLocal()
        job = VideoJob(
            id=job_id,
            title=request.title or "Reup Video",
            source_url=request.source_url,
            target_platform=request.target_platform,
            video_type=request.video_type,
            duration=request.duration,
            status=JobStatus.PENDING,
            processing_flow=request.processing_flow,
            processing_options=request.processing_options,
        )
        db.add(job)
        db.commit()
        db.close()

        # Queue processing
        background_tasks.add_task(
            _process_reup_video_task,
            job_id,
            request,
        )

        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
        }
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/process-story")
async def process_story_video(
    request: StoryVideoRequest,
    background_tasks: BackgroundTasks,
):
    """Process video with story narration"""
    try:
        logger.info(f"Processing story video: {request.source_url}")

        job_id = str(uuid.uuid4())

        # Create job record
        db = SessionLocal()
        job = VideoJob(
            id=job_id,
            title=request.title,
            source_url=request.source_url,
            duration=request.duration,
            status=JobStatus.PENDING,
        )
        db.add(job)
        db.commit()
        db.close()

        # Queue processing
        background_tasks.add_task(
            _process_story_video_task,
            job_id,
            request,
        )

        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
        }
    except Exception as e:
        logger.error(f"Story video processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/job/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get job status"""
    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        output_links = []
        if job.output_path:
            output_links.append(f"/api/videos/download/{job_id}")

        return {
            "id": job.id,
            "title": job.title,
            "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
            "progress": job.progress,
            "current_step": job.current_step,
            "created_at": job.created_at,
            "output_links": output_links,
            "error_message": job.error_message,
        }
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/download/{job_id}")
async def download_video(job_id: str, db: Session = Depends(get_db)):
    """Download processed video"""
    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job or not job.output_path:
            raise HTTPException(status_code=404, detail="Video not found")

        output_path = Path(job.output_path)
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")

        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=job.output_filename or "video.mp4",
        )
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HELPER FUNCTIONS ====================

async def _process_reup_video_task(job_id: str, request: VideoCreateRequest):
    """Background task for reup video processing"""
    db = SessionLocal()
    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()

        # Update status
        job.status = JobStatus.DOWNLOADING
        job.current_step = "Downloading video"
        db.commit()

        # Download video
        downloader = VideoDownloader()
        download_result = await downloader.download(
            request.source_url,
            Path(settings.TEMP_DIR),
        )
        video_path = Path(download_result["path"])

        # Generate TTS narration if requested
        text_segments = []
        new_audio = None

        if request.add_ai_narration:
            job.current_step = "Generating narration"
            db.commit()

            # Use story generator to create narration
            story_gen = await get_story_generator(request.ai_provider or settings.AI_PROVIDER)
            narration = await story_gen.generate_narration(
                topic=request.description or request.title or "Video content",
                duration=request.duration,
                tone=request.narration_style or "professional",
            )

            # Generate TTS
            tts = await get_tts_provider(request.ai_provider or settings.TTS_PROVIDER)
            new_audio = await tts.synthesize(
                text=narration,
                voice=request.tts_voice,
                output_path=Path(settings.TEMP_DIR) / f"narration_{job_id}.mp3",
            )

            # Create text segments
            text_segments = video_editor._create_subtitle_segments(narration)

        # Process video
        job.current_step = "Processing video"
        db.commit()

        result = await video_editor.process_video_for_reup(
            video_path=video_path,
            target_duration=request.duration,
            target_platform=request.target_platform,
            add_text=request.add_text_overlay and len(text_segments) > 0,
            text_segments=text_segments if request.add_text_overlay else None,
            new_audio_path=new_audio,
            output_path=Path(settings.PROCESSED_DIR) / f"reup_{job_id}.mp4",
        )

        if result["success"]:
            job.status = JobStatus.COMPLETED
            job.output_path = result["output_path"]
            job.output_filename = f"reup_{job_id}.mp4"
            job.progress = 100
            job.current_step = "Completed"
        else:
            job.status = JobStatus.FAILED
            job.error_message = result.get("error", "Unknown error")
            job.current_step = "Failed"

        db.commit()

    except Exception as e:
        logger.error(f"Reup processing error: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.current_step = "Error"
        db.commit()
    finally:
        db.close()


async def _process_story_video_task(job_id: str, request: StoryVideoRequest):
    """Background task for story video processing"""
    db = SessionLocal()
    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()

        # Update status
        job.status = JobStatus.DOWNLOADING
        job.current_step = "Downloading video"
        db.commit()

        # Download video
        downloader = VideoDownloader()
        download_result = await downloader.download(
            request.source_url,
            Path(settings.TEMP_DIR),
        )
        video_path = Path(download_result["path"])

        # Generate story
        job.current_step = "Generating story"
        db.commit()

        story_gen = await get_story_generator(settings.AI_PROVIDER)
        story = await story_gen.generate_story(
            prompt=request.story_topic,
            style=request.story_style,
            max_length=int(request.duration * 2.5),
        )

        # Generate TTS for story
        job.current_step = "Generating narration"
        db.commit()

        tts = await get_tts_provider(settings.TTS_PROVIDER)
        audio_path = await tts.synthesize(
            text=story,
            voice=request.tts_voice,
            output_path=Path(settings.TEMP_DIR) / f"story_audio_{job_id}.mp3",
        )

        # Generate video
        job.current_step = "Creating video"
        db.commit()

        output_path = await video_editor.generate_story_video(
            base_video_path=video_path,
            story_text=story,
            audio_path=audio_path,
            output_path=Path(settings.PROCESSED_DIR) / f"story_{job_id}.mp4",
        )

        if output_path:
            job.status = JobStatus.COMPLETED
            job.output_path = str(output_path)
            job.output_filename = f"story_{job_id}.mp4"
            job.progress = 100
            job.current_step = "Completed"
        else: 
            job.status = JobStatus.FAILED
            job.error_message = "Failed to generate video"
            job.current_step = "Failed"

        db.commit()

    except Exception as e:
        logger.error(f"Story video processing error: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.current_step = "Error"
        db.commit()
    finally:
        db.close()