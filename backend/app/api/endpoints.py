"""
Main API Endpoints for Video Processing
"""

import uuid
import time
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Query, HTTPException, BackgroundTasks
from fastapi. responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core. config import settings
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
    EOAChatRequest,
    EOAChatResponse,
    EOAProcessRequest,
    EOAProcessResponse,
    ChatMessage,
)
from app.services.ai. tts_provider import get_tts_provider
from app.services.ai.transcription_service import get_transcription_provider
from app.services.ai.story_generator import get_story_generator
from app.services.video_downloader import VideoDownloader
from app.services.audio_processor import audio_processor
from app.services. text_overlay_engine import text_overlay_engine, TextStyle
from app.services. video_editor import video_editor
from app.utils.file_utils import ensure_dirs

router = APIRouter()


# ==================== HEALTH & INFO ====================

@router.get("/health")
async def health_check() -> HealthResponse:
    """Check system health"""
    try:
        from redis import Redis
        redis_client = Redis. from_url(settings.REDIS_URL)
        redis_ok = bool(redis_client.ping())
    except:
        redis_ok = False

    try:
        db = SessionLocal()
        db. execute("SELECT 1")
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
    if settings. OPENAI_API_KEY:
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
                name=v. get("name", ""),
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


# ==================== EOA CHATBOT ENDPOINTS ====================

@router.post("/eoa/chat")
async def eoa_chat(request: EOAChatRequest) -> EOAChatResponse:
    """Chat with EOA AI assistant"""
    try:
        from app.services.ai.eoa_chatbot import eoa_chatbot
        
        # Convert ChatMessage to dict
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]
        
        result = await eoa_chatbot.chat(
            message=request.message,
            session_id=request.session_id,
            conversation_history=history,
            ai_provider=request.ai_provider
        )
        
        return EOAChatResponse(
            success=result["success"],
            message=result["message"],
            suggestions=result.get("suggestions", []),
            collected_info=result.get("collected_info", {}),
            ready_to_process=result.get("ready_to_process", False),
            action_required=result.get("action_required")
        )
    except Exception as e:
        logger.error(f"EOA chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eoa/process")
async def eoa_process(request: EOAProcessRequest) -> EOAProcessResponse:
    """Process collected info and generate audio"""
    try:
        from app.services.ai.eoa_chatbot import eoa_chatbot
        
        # Restore session if needed
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]
        
        # Ensure session exists with history
        session_id = eoa_chatbot.get_or_create_session(request.session_id)
        if history:
            eoa_chatbot.sessions[session_id]["messages"] = history
        if request.story_config:
            eoa_chatbot.sessions[session_id]["collected_info"] = request.story_config
        
        result = await eoa_chatbot.process_and_generate(
            session_id=session_id,
            voice=request.voice,
            speed=request.speed,
            add_pauses=request.add_pauses,
            ai_provider=request.ai_provider
        )
        
        return EOAProcessResponse(
            success=result["success"],
            story_text=result.get("story_text", ""),
            audio_path=result.get("audio_path"),
            audio_url=result.get("audio_url"),
            duration=result.get("duration"),
            word_count=result.get("word_count", 0),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"EOA process error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/eoa/download/{session_id}")
async def eoa_download_audio(session_id: str):
    """Download generated audio file"""
    try:
        audio_path = Path(settings.PROCESSED_DIR) / f"eoa_audio_{session_id}.mp3"
        
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename=f"eoa_story_{session_id}.mp3",
            headers={"Content-Disposition": f"attachment; filename=eoa_story_{session_id}.mp3"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EOA download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/eoa/session/{session_id}")
async def eoa_clear_session(session_id: str):
    """Clear EOA session"""
    try:
        from app.services.ai.eoa_chatbot import eoa_chatbot
        eoa_chatbot.clear_session(session_id)
        return {"success": True, "message": "Session cleared"}
    except Exception as e:
        logger.error(f"EOA clear session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SPLIT-SCREEN MERGE ENDPOINTS ====================

@router.post("/videos/merge-split-screen")
async def merge_split_screen(
    video1_url: str = Query(..., description="URL of first video (left/top)"),
    video2_url: str = Query(..., description="URL of second video (right/bottom)"),
    layout: str = Query("horizontal", description="Layout: horizontal or vertical"),
    ratio: str = Query("1:1", description="Split ratio: 1:1, 2:1, 1:2"),
    output_ratio: str = Query("9:16", description="Output aspect ratio: 9:16, 16:9, 1:1"),
    audio_source: str = Query("both", description="Audio source: video1, video2, both, none"),
):
    """Merge two videos into split screen"""
    try:
        from app.services.video_merger import video_merger
        
        result = await video_merger.merge_split_screen(
            video1_url=video1_url,
            video2_url=video2_url,
            layout=layout,
            ratio=ratio,
            output_ratio=output_ratio,
            audio_source=audio_source
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Merge failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Split-screen merge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/merged/{job_id}")
async def download_merged_video(job_id: str):
    """Download merged video"""
    try:
        output_path = Path(settings.PROCESSED_DIR) / f"merged_{job_id}.mp4"
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")
        
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"merged_{job_id}.mp4"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download merged video error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ASPECT RATIO CONVERSION ENDPOINTS ====================

@router.post("/videos/convert-aspect-ratio")
async def convert_aspect_ratio(
    source_url: str = Query(..., description="Source video URL"),
    target_ratio: str = Query("9:16", description="Target ratio: 9:16, 16:9, 1:1, 4:5, 4:3"),
    method: str = Query("pad", description="Method: pad, crop, fit"),
    bg_color: str = Query("000000", description="Background color (hex)"),
):
    """Convert video aspect ratio"""
    try:
        from app.services.aspect_ratio_converter import aspect_ratio_converter
        
        result = await aspect_ratio_converter.convert(
            source_url=source_url,
            target_ratio=target_ratio,
            method=method,
            bg_color=bg_color
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Conversion failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Aspect ratio conversion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/convert-for-platform")
async def convert_for_platform(
    source_url: str = Query(..., description="Source video URL"),
    platform: str = Query(..., description="Target platform: tiktok, youtube, instagram_reels, etc."),
    method: str = Query("pad", description="Method: pad, crop, fit"),
):
    """Convert video to recommended aspect ratio for platform"""
    try:
        from app.services.aspect_ratio_converter import aspect_ratio_converter
        
        result = await aspect_ratio_converter.convert_for_platform(
            source_url=source_url,
            platform=platform,
            method=method
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Conversion failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Platform conversion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/converted/{job_id}")
async def download_converted_video(job_id: str):
    """Download converted video"""
    try:
        output_path = Path(settings.PROCESSED_DIR) / f"converted_{job_id}.mp4"
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")
        
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"converted_{job_id}.mp4"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download converted video error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aspect-ratios")
async def get_aspect_ratios():
    """Get available aspect ratios and platform recommendations"""
    from app.services.aspect_ratio_converter import PLATFORM_RATIOS, RATIO_DIMENSIONS
    
    return {
        "ratios": [
            {"id": "9:16", "name": "Vertical (TikTok/Reels)", "width": 1080, "height": 1920},
            {"id": "16:9", "name": "Landscape (YouTube)", "width": 1920, "height": 1080},
            {"id": "1:1", "name": "Square (Instagram)", "width": 1080, "height": 1080},
            {"id": "4:5", "name": "Portrait (Instagram)", "width": 1080, "height": 1350},
            {"id": "4:3", "name": "Traditional (TV)", "width": 1440, "height": 1080},
        ],
        "platforms": PLATFORM_RATIOS,
        "methods": [
            {"id": "pad", "name": "Pad", "description": "Add black bars to maintain all content"},
            {"id": "crop", "name": "Crop", "description": "Crop to fill target (may lose content)"},
            {"id": "fit", "name": "Fit", "description": "Scale to fit within target"},
        ]
    }


# ==================== HIGHLIGHT EXTRACTION ENDPOINTS ====================

@router.post("/videos/extract-highlights")
async def extract_highlights(
    source_url: str = Query(..., description="Source video URL"),
    target_duration: int = Query(60, description="Target highlight duration in seconds"),
    num_highlights: int = Query(5, description="Number of highlight segments"),
    style: str = Query("engaging", description="Style: engaging, informative, dramatic, funny"),
    ai_provider: str = Query("auto", description="AI provider: auto, openai, gemini"),
    background_tasks: BackgroundTasks = None
):
    """Extract highlights from long video"""
    try:
        from app.services.highlight_extractor import highlight_extractor
        from app.services.video_downloader import VideoDownloader
        from app.services.ai.transcription_service import get_transcription_provider
        
        job_id = str(uuid.uuid4())[:8]
        temp_dir = Path(settings.TEMP_DIR) / f"highlight_{job_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Download video
        logger.info(f"Downloading video for highlight extraction...")
        downloader = VideoDownloader()
        video_path = await downloader.download(source_url, temp_dir)
        
        # Transcribe video
        logger.info("Transcribing video...")
        transcription_provider = await get_transcription_provider(ai_provider)
        transcript_result = await transcription_provider.transcribe(video_path, language="vi")
        
        # Extract highlights
        result = await highlight_extractor.extract_highlights(
            video_path=video_path,
            transcript_segments=transcript_result.get("segments", []),
            target_duration=target_duration,
            num_highlights=num_highlights,
            style=style,
            ai_provider=ai_provider
        )
        
        # Cleanup temp video
        try:
            video_path.unlink()
            temp_dir.rmdir()
        except:
            pass
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Extraction failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Highlight extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/highlights/{job_id}")
async def download_highlights_video(job_id: str):
    """Download highlights video"""
    try:
        output_path = Path(settings.PROCESSED_DIR) / f"highlights_{job_id}.mp4"
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")
        
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"highlights_{job_id}.mp4"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download highlights video error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TTS ENDPOINTS ====================

@router.get("/tts/providers")
async def get_tts_providers():
    """Get all available TTS providers with configuration status"""
    try:
        from app.services.ai.tts_provider import get_all_providers_info, TTS_PROVIDERS
        
        providers = await get_all_providers_info()
        
        return {
            "success": True,
            "providers": providers,
            "default_provider": settings.TTS_PROVIDER,
            "total": len(providers)
        }
    except Exception as e:
        logger.error(f"Get TTS providers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tts/voices")
async def get_tts_voices(provider: str = None):
    """Get available voices from provider(s)"""
    try:
        from app.services.ai.tts_provider import get_all_voices, get_tts_provider
        
        if provider:
            tts = await get_tts_provider(provider)
            voices = await tts.get_available_voices()
        else:
            voices = await get_all_voices()
        
        return {
            "success": True,
            "voices": voices,
            "total": len(voices),
            "provider": provider
        }
    except Exception as e:
        logger.error(f"Get TTS voices error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    """Generate text-to-speech audio"""
    try:
        from app.services.ai.tts_provider import get_tts_provider
        
        logger.info(f"Generating TTS: {request.text[:100]}...")

        provider_name = request.ai_provider or settings.TTS_PROVIDER
        tts = await get_tts_provider(provider_name)

        output_path = await tts.synthesize(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            output_path=Path(settings.TEMP_DIR) / f"tts_{uuid.uuid4()}.mp3",
        )

        return {
            "success": True,
            "audio_path": str(output_path),
            "audio_url": f"/api/tts/download/{output_path.stem}",
            "provider": provider_name,
            "voice": request.voice,
        }
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tts/download/{audio_id}")
async def download_tts_audio(audio_id: str):
    """Download generated TTS audio"""
    try:
        # Search for audio file
        for ext in [".mp3", ".wav"]:
            audio_path = Path(settings.TEMP_DIR) / f"{audio_id}{ext}"
            if audio_path.exists():
                return FileResponse(
                    path=audio_path,
                    media_type="audio/mpeg",
                    filename=f"{audio_id}.mp3"
                )
        
        raise HTTPException(status_code=404, detail="Audio file not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts/preview-voice")
async def preview_voice(request: VoicePreviewRequest):
    """Preview AI voice"""
    try:
        from app.services.ai.tts_provider import get_tts_provider
        
        provider_name = request.ai_provider or settings.TTS_PROVIDER
        tts = await get_tts_provider(provider_name)

        audio_path = await tts.synthesize(
            text=request.sample_text,
            voice=request.voice_id,
        )

        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename=f"preview_{request.voice_id}.mp3",
        )
    except Exception as e:
        logger. error(f"Voice preview error: {e}")
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

@router. post("/story/generate")
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

@router. post("/videos/process-reup")
async def process_reup_video(
    request: VideoCreateRequest,
    background_tasks: BackgroundTasks,
):
    """Process video for reupload with AI"""
    try:
        logger. info(f"Processing reup video: {request.source_url}")

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
            title=request. title,
            source_url=request. source_url,
            duration=request.duration,
            status=JobStatus.PENDING,
        )
        db.add(job)
        db.commit()
        db.close()

        # Queue processing
        background_tasks. add_task(
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
async def get_job_status(job_id: str):
    """Get job status"""
    db = SessionLocal()
    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        output_links = []
        if job.output_path:
            output_links. append(f"/api/videos/download/{job_id}")

        return {
            "id": job.id,
            "title": job.title,
            "status": job.status. value if hasattr(job.status, 'value') else str(job.status),
            "progress": job.progress,
            "current_step": job.current_step,
            "created_at": job.created_at,
            "output_links": output_links,
            "error_message": job.error_message,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/videos/download/{job_id}")
async def download_video(job_id: str):
    """Download processed video"""
    db = SessionLocal()
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
            filename=job.output_filename or "video. mp4",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


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
            tts = await get_tts_provider(request. ai_provider or settings.TTS_PROVIDER)
            new_audio = await tts.synthesize(
                text=narration,
                voice=request.tts_voice,
                output_path=Path(settings. TEMP_DIR) / f"narration_{job_id}.mp3",
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
            output_path=Path(settings. PROCESSED_DIR) / f"reup_{job_id}.mp4",
        )

        if result["success"]:
            job.status = JobStatus.COMPLETED
            job.output_path = result["output_path"]
            job.output_filename = f"reup_{job_id}.mp4"
            job.progress = 100
            job.current_step = "Completed"
        else:
            job.status = JobStatus.FAILED
            job.error_message = result. get("error", "Unknown error")
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
        job. current_step = "Downloading video"
        db.commit()

        # Download video
        downloader = VideoDownloader()
        download_result = await downloader.download(
            request.source_url,
            Path(settings. TEMP_DIR),
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

        tts = await get_tts_provider(settings. TTS_PROVIDER)
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
            output_path=Path(settings.PROCESSED_DIR) / f"story_{job_id}. mp4",
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

        db. commit()

    except Exception as e:
        logger.error(f"Story video processing error: {e}")
        job.status = JobStatus. FAILED
        job.error_message = str(e)
        job.current_step = "Error"
        db.commit()
    finally:
        db.close()