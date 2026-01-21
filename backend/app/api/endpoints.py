"""
Main API Endpoints for Video Processing
"""

import uuid
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Query, HTTPException, BackgroundTasks, Depends
from fastapi. responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core. config import settings
from app.database import get_db, SessionLocal
from app.models import VideoJob, JobStatus, VideoType
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
    SeriesCreateRequest,
    # YouTube Analyzer
    YouTubeAnalyzeRequest,
    YouTubeChannelRequest,
    AnalysisJobResponse,
    AnalysisResult,
)
from app.services.ai. tts_provider import get_tts_provider
from app.services.ai.transcription_service import get_transcription_provider
from app.services.ai.story_generator import get_story_generator
from app.services.ai.series_generator import series_generator
from app.services.video_downloader import VideoDownloader
from app.services.audio_processor import audio_processor
from app.services. text_overlay_engine import text_overlay_engine, TextStyle
from app.services. video_editor import video_editor
from app.services.storage.google_drive import google_drive_service
from app.utils.file_utils import ensure_dirs

# YouTube Analyzer imports
from app.services.youtube.orchestrator import orchestrator, PipelineConfig, PipelineStatus

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
    """Get available TTS voices - Always use Edge TTS for best Vietnamese support"""
    try:
        # Always use Edge TTS for voice listing - it has Vietnamese voices and is free
        from app.services.ai.tts_provider import EdgeTTSProvider
        tts = EdgeTTSProvider()
        voices = await tts.get_available_voices()

        # Sort voices: Vietnamese first, then by language
        def voice_sort_key(v):
            lang = v.get("language", "")
            if lang.startswith("vi-"):
                return (0, lang, v.get("name", ""))  # Vietnamese first
            return (1, lang, v.get("name", ""))
        
        sorted_voices = sorted(voices, key=voice_sort_key)
        
        return [
            VoiceOption(
                id=v.get("id", ""),
                name=v.get("name", ""),
                gender=v.get("gender", ""),
                language=v.get("language", ""),
            )
            for v in sorted_voices
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

        output_path, _ = await tts.synthesize(
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

        output_path, _ = await tts.synthesize(
            text=f"This is a preview of the {request.voice_id} voice.",
            voice=request.voice_id,
            output_path=Path(settings.TEMP_DIR) / f"preview_{uuid.uuid4()}.mp3",
        )

        return FileResponse(
            path=output_path,
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
            filename=job.output_filename or f"video_{job_id}.mp4",
            content_disposition_type="inline"
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
    """Background task for reup video processing with detailed status tracking"""
    db = SessionLocal()
    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()

        def update_status(step: str, progress: int = 0):
            """Helper to update job status"""
            job.current_step = step
            job.progress = progress
            db.commit()
            logger.info(f"Job {job_id}: {step} ({progress}%)")

        # Step 1: Downloading
        job.status = JobStatus.DOWNLOADING
        update_status("🔄 Đang tải video từ nguồn...", 5)

        downloader = VideoDownloader()
        try:
            download_result = await downloader.download(
                request.source_url,
                Path(settings.TEMP_DIR),
            )
            video_path = Path(download_result["path"])
            update_status(f"✅ Đã tải video: {download_result.get('title', 'video')[:50]}", 20)
        except Exception as e:
            update_status(f"❌ Lỗi tải video: {str(e)[:80]}", 0)
            raise

        # Step 2: Generate TTS narration if requested
        text_segments = []
        new_audio = None
        narration = None # Initialize narration here

        if request.add_ai_narration:
            job.status = JobStatus.PROCESSING
            update_status("🧠 Đang phân tích và viết lại nội dung...", 30)
            try:
                # Log which provider will be used
                provider_name = request.ai_provider or settings.AI_PROVIDER
                logger.info(f"[NARRATION] Starting narration process with: {provider_name}")
                story_gen = await get_story_generator(provider_name)
                
                # NEW: Transcription-based Rewrite Logic
                if request.rewrite_from_original:
                    try:
                        update_status("📻 Đang trích xuất âm thanh gốc...", 32)
                        original_audio = await audio_processor.extract_audio(video_path)
                        
                        update_status("📝 Đang chuyển âm thanh thành văn bản...", 35)
                        transcriber = await get_transcription_provider(provider_name)
                        transcription_result = await transcriber.transcribe(original_audio)
                        original_text = transcription_result.get("text", "")
                        
                        if original_text and len(original_text) > 10:
                            update_status("✍️ Đang tối ưu nội dung chuẩn...", 38)
                            rewrite_result = await story_gen.rewrite_transcript(
                                original_text=original_text,
                                segments=transcription_result.get("segments", []),
                                style=request.narration_style or "viral"
                            )
                            narration = rewrite_result.get("rewritten_text")
                            text_segments = rewrite_result.get("segments", [])
                            logger.info(f"[REWRITE] Success. Chars: {len(narration) if narration else 0}, Segments: {len(text_segments)}")
                        else:
                            logger.warning("[REWRITE] Original text too short or empty, falling back to topic-based")
                    except Exception as e:
                        logger.error(f"[REWRITE] Failed: {e}")
                        update_status("⚠️ Không thể transcribe, dùng AI tạo nội dung mới", 35)
                
                # Fallback to Topic-based generation if transcription failed or disabled
                if not narration:
                    logger.info("[NARRATION] Generating from topic/metadata...")
                    narration = await story_gen.generate_narration(
                        topic=request.description or request.title or "Nội dung video hấp dẫn",
                        duration=request.duration,
                        tone=request.narration_style or "professional",
                    )
                
                if narration:
                    update_status("✅ Đã chuẩn bị nội dung chuẩn", 40)
                    logger.info(f"[NARRATION] Final script prepared: {len(narration)} chars")
                
            except Exception as e:
                logger.error(f"[NARRATION] Overall AI error: {e}")
                update_status("⚠️ Lỗi AI, thử dùng mode cơ bản...", 35)
                # Final fallback
                try:
                    from app.services.ai.story_generator import SimpleStoryGenerator
                    simple_gen = SimpleStoryGenerator()
                    narration = await simple_gen.generate_narration(
                        topic=request.title or "Video Content",
                        duration=request.duration,
                        tone=request.narration_style or "professional"
                    )
                except Exception:
                    narration = None

            if narration:
                update_status("🔊 Đang chuyển văn bản thành giọng nói (TTS)...", 45)
                try:
                    logger.info("[TTS] Getting TTS provider...")
                    tts = await get_tts_provider(request.ai_provider or settings.TTS_PROVIDER)
                    logger.info(f"[TTS] Got provider: {type(tts).__name__}")
                    
                    output_audio_path = Path(settings.TEMP_DIR) / f"narration_{job_id}.mp3"
                    logger.info(f"[TTS] Synthesizing to: {output_audio_path}")
                    # Generate audio
                    new_audio, timing = await tts.synthesize(
                        text=narration,
                        voice=request.tts_voice,
                        output_path=output_audio_path,
                        with_timing=True # Request timing information
                    )
                    
                    if new_audio and new_audio.exists():
                        audio_size = new_audio.stat().st_size
                        logger.info(f"[TTS] Audio created: {new_audio} ({audio_size} bytes)")
                        update_status("✅ Đã tạo audio TTS", 55)
                        
                        # Use timing for segments if available, otherwise fall back to simple segmentation
                        if timing:
                            # Apply Shorts styling to granular word timing
                            text_segments = [
                                {**t, "style": {"font_size": 80, "position": "center"}} 
                                for t in timing
                            ]
                            logger.info(f"[TTS] Created {len(text_segments)} subtitle segments from timing")
                        else:
                            text_segments = video_editor._create_subtitle_segments(narration)
                            logger.info(f"[TTS] Created {len(text_segments)} subtitle segments from text")
                    else:
                        logger.error(f"[TTS] Audio file not created or missing")
                        new_audio = None
                        
                except Exception as e:
                    logger.error(f"[TTS] Error: {type(e).__name__}: {e}")
                    update_status(f"⚠️ Lỗi TTS: {str(e)[:80]}", 50)
                    new_audio = None

        # Step 3: Get video info
        job.status = JobStatus.PROCESSING
        update_status("📊 Đang phân tích thông tin video...", 60)

        try:
            from app.utils.ffmpeg_ops import ffmpeg_ops
            video_info = await ffmpeg_ops.get_video_info(video_path)
            update_status(f"✅ Video: {video_info.get('width')}x{video_info.get('height')}, {video_info.get('duration', 0):.1f}s", 65)
        except Exception as e:
            error_msg = f"❌ Lỗi FFprobe - Không thể đọc video: {str(e)[:70]}"
            update_status(error_msg, 60)
            job.status = JobStatus.FAILED
            job.error_message = error_msg
            db.commit()
            raise

        # Step 4: Process video
        update_status("🎬 Đang xử lý và chỉnh sửa video...", 70)

        try:
            result = await video_editor.process_video_for_reup(
                video_path=video_path,
                target_duration=request.duration,
                target_platform=request.target_platform,
                add_text=request.add_text_overlay and len(text_segments) > 0,
                text_segments=text_segments if request.add_text_overlay else None,
                new_audio_path=new_audio,
                output_path=Path(settings.PROCESSED_DIR) / f"reup_{job_id}.mp4",
                bgm_style=request.bgm_style if request.add_background_music else None,
                normalize_audio=request.normalize_audio,
            )
        except Exception as e:
            error_msg = f"❌ Lỗi xử lý video: {str(e)[:80]}"
            update_status(error_msg, 70)
            job.status = JobStatus.FAILED
            job.error_message = error_msg
            db.commit()
            raise

        # Step 5: Finalize
        if result.get("success"):
            job.status = JobStatus.COMPLETED
            job.output_path = result["output_path"]
            job.output_filename = f"reup_{job_id}.mp4"
            
            # Archive to Google Drive
            try:
                update_status("📤 Đang lưu trữ lên Google Drive...", 95)
                uploaded_link = google_drive_service.upload_file(result["output_path"])
                if uploaded_link:
                    logger.info(f"Archived reup video to Drive: {uploaded_link}")
            except Exception as e:
                logger.error(f"Drive archive failed: {e}")

            update_status("✅ Hoàn thành! Video đã sẵn sàng tải xuống và đã lưu Drive.", 100)
        else:
            error_msg = result.get("error", "Unknown error")
            job.status = JobStatus.FAILED
            job.error_message = error_msg
            update_status(f"❌ Thất bại: {error_msg[:100]}", 0)

        db.commit()

    except Exception as e:
        logger.error(f"Reup processing error: {e}", exc_info=True)
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)[:500]
            job.current_step = f"❌ Lỗi: {str(e)[:100]}"
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

        story_gen = await get_story_generator(request.ai_provider or settings.AI_PROVIDER)
        story = await story_gen.generate_story(
            prompt=request.story_topic,
            style=request.story_style,
            max_length=int(request.duration * 2.5),
        )

        # Generate TTS for story
        job.current_step = "Generating narration"
        db.commit()

        tts = await get_tts_provider(request.ai_provider or settings.AI_PROVIDER)
        audio_path, timing = await tts.synthesize(
            text=story,
            voice=request.tts_voice,
            output_path=Path(settings.TEMP_DIR) / f"story_audio_{job_id}.mp3",
            with_timing=True
        )

        # Use improved timing if available
        if timing:
            text_segments = timing
        else:
            text_segments = video_editor._create_subtitle_segments(story)

        # Generate video
        job.current_step = "Creating video"
        db.commit()

        output_path = await video_editor.generate_story_video(
            base_video_path=video_path,
            story_text=story,
            audio_path=audio_path,
            output_path=Path(settings.PROCESSED_DIR) / f"story_{job_id}.mp4",
            bgm_style=request.bgm_style if request.background_music else None,
            normalize_audio=request.normalize_audio,
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

# ==================== STORY SERIES ====================

@router.post("/story-series/create", response_model=VideoOutputResponse)
async def create_story_series(
    request: SeriesCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a multi-part video series from a long video.
    """
    job_id = str(uuid.uuid4())
    
    # Create job record
    job = VideoJob(
        id=job_id,
        title=f"Series: {request.topic}",
        status=JobStatus.PENDING,
        updated_at=datetime.utcnow(),
        processing_options=request.dict(),
        source_url=request.source_url,
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(
        _process_series_video_task,
        job_id,
        request,
    )

    return VideoOutputResponse(
        success=True,
        job_id=job_id,
        processing_time=0
    )

async def _process_series_video_task(job_id: str, request: SeriesCreateRequest):
    """
    Background task to process video series
    """
    db = SessionLocal()
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    
    def update_status(status_msg, progress):
        logger.info(f"[Job {job_id}] {status_msg} ({progress}%)")
        job.status = JobStatus.PROCESSING
        job.current_step = status_msg
        job.progress = progress
        job.updated_at = datetime.utcnow()
        db.commit()

    try:
        update_status("📥 Đang tải video gốc...", 10)
        
        # 1. Download Video
        try:
            downloader = VideoDownloader()
            video_info = await downloader.download(request.source_url, output_dir=ensure_dirs()[0])
            video_path = Path(video_info["path"])  # Convert to Path for consistency
            logger.info(f"Downloaded video to {video_path}")
        except Exception as e:
            update_status(f"❌ Lỗi tải video: {str(e)}", 0)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            db.commit()
            return

        # 2. Get Info & Calculate Splits
        update_status("📏 Đang tính toán phân chia series...", 20)
        video_info = await video_editor.get_video_info(video_path)
        total_duration = int(video_info["duration"])
        part_duration = total_duration // request.num_parts
        
        # 3. Generate Outline (AI)
        update_status("🧠 AI đang lên kịch bản trọn bộ...", 25)
        outline = await series_generator.generate_series_outline(
            topic=request.topic,
            num_parts=request.num_parts,
            total_duration=total_duration,
            style=request.voice_style
        )
        logger.info(f"Series Outline: {outline}")
        
        # 4. Process Each Part
        generated_parts = []
        
        for i in range(request.num_parts):
            part_num = i + 1
            update_status(f"🎬 Đang sản xuất Tập {part_num}/{request.num_parts}...", 30 + (i * 10))
            
            # 4a. Cut Segment
            start_time = i * part_duration
            end_time = (i + 1) * part_duration if i < request.num_parts - 1 else total_duration
            
            part_video_path = Path(settings.TEMP_DIR) / f"{job_id}_part_{part_num}.mp4"
            await video_editor.cut_video(
                video_path, start_time, end_time, part_video_path
            )
            
            # 4b. Generate Script
            script = await series_generator.generate_part_script(
                part_index=i,
                total_parts=request.num_parts,
                outline=outline,
                duration=int(end_time - start_time)
            )
            
            # 4c. TTS
            tts_provider = await get_tts_provider(request.tts_voice or settings.TTS_PROVIDER)
            audio_path = Path(settings.TEMP_DIR) / f"{job_id}_audio_part_{part_num}.mp3"
            await tts_provider.synthesize(
                text=script,
                output_path=audio_path,
                voice=request.tts_voice or settings.EDGE_TTS_VOICE,
                speed=settings.TTS_SPEAKING_RATE
            )
            
            # 4d. Create Subtitles
            segments = video_editor._create_subtitle_segments(script)
            
            # 4e. Merge (Audio + Video + Subs + BGM)
            final_part_path = Path(settings.PROCESSED_DIR) / f"Series_{job_id}_Part_{part_num}.mp4"
            
            # Process using main video editor flow
            await video_editor.process_video_for_reup(
                video_path=part_video_path,
                target_duration=int(end_time - start_time),
                target_platform=request.target_platform,
                add_text=True,
                text_segments=segments,
                new_audio_path=audio_path,
                output_path=final_part_path,
                bgm_style=request.bgm_style,
                normalize_audio=True
            )
            
            generated_parts.append(str(final_part_path))
            
            # Cleanup temp part files
            if part_video_path.exists(): part_video_path.unlink()
            if audio_path.exists(): audio_path.unlink()

        # Finalize
        job.status = JobStatus.COMPLETED
        job.output_path = json.dumps(generated_parts) # Store list of paths
        job.progress = 100
        
        # Archive all parts to Google Drive
        try:
            update_status("📤 Đang lưu trữ trọn bộ lên Google Drive...", 95)
            for part_path in generated_parts:
                drive_link = google_drive_service.upload_file(part_path)
                if drive_link:
                    logger.info(f"Archived part {Path(part_path).name} to Drive: {drive_link}")
        except Exception as e:
            logger.error(f"Drive series archive failed: {e}")

        job.current_step = "✅ Đã hoàn thành trọn bộ series và lưu Drive!"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        # Cleanup source
        if video_path.exists():
            video_path.unlink()

    except Exception as e:
        logger.error(f"Series processing failed: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()


# ==================== YOUTUBE VIDEO ANALYZER ====================

# Store analysis jobs in memory (TODO: move to database/Redis)
# Store analysis jobs in memory (REMOVED - Now using DB)
# _analysis_jobs: dict = {}


@router.post("/youtube/analyze", response_model=AnalysisJobResponse)
async def analyze_youtube_video(
    request: YouTubeAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start analysis pipeline for a YouTube video.
    Returns job_id to track progress.
    """
    job_id = str(uuid.uuid4())
    
    # Create DB Job
    new_job = VideoJob(
        id=job_id,
        title=f"Analysis: {request.youtube_url}",
        source_url=request.youtube_url,
        status=JobStatus.PENDING,
        video_type=VideoType.FULL, # Placeholder
        processing_options={"min_score": request.min_score_threshold},
        created_at=datetime.utcnow()
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Create pipeline config
    config = PipelineConfig(
        video_url=request.youtube_url,
        min_score=request.min_score_threshold
    )
    
    # Start pipeline in background
    async def run_analysis(job_id: str):
        # Create new session for background task
        db_task = SessionLocal()
        try:
            db_job = db_task.query(VideoJob).filter(VideoJob.id == job_id).first()
            if not db_job:
                logger.error(f"Job {job_id} not found in background task")
                return

            def update_progress(state):
                # Map PipelineStatus to JobStatus
                status_map = {
                    "pending": JobStatus.PENDING,
                    "running": JobStatus.ANALYZING,
                    "completed": JobStatus.COMPLETED,
                    "failed": JobStatus.FAILED,
                    "cancelled": JobStatus.CANCELLED
                }
                
                db_job.status = status_map.get(state.status.value, JobStatus.PROCESSING)
                db_job.progress = state.progress
                db_job.current_step = state.current_stage.value if state.current_stage else "initializing"
                
                # Store intermediate results
                if state.results:
                    db_job.analysis_result = {
                        "status": state.status.value,
                        "progress": state.progress,
                        "current_stage": state.current_stage.value if state.current_stage else None,
                        "results": state.results,
                        "error": state.error
                    }
                
                db_task.commit()
            
            # Execute Pipeline
            result = await orchestrator.run_pipeline(config, update_progress)
            
            # Final Update
            status_map = {
                "completed": JobStatus.COMPLETED,
                "failed": JobStatus.FAILED
            }
            db_job.status = status_map.get(result.status.value, JobStatus.FAILED)
            db_job.progress = result.progress
            db_job.analysis_result = {
                 "status": result.status.value,
                 "progress": result.progress,
                 "results": result.results,
                 "error": result.error
            }
            
            if result.error:
                db_job.error_message = result.error
                
            db_task.commit()

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            if db_job:
                db_job.status = JobStatus.FAILED
                db_job.error_message = str(e)
                db_task.commit()
        finally:
            db_task.close()
    
    background_tasks.add_task(run_analysis, job_id)
    
    return AnalysisJobResponse(
        success=True,
        job_id=job_id,
        message="Analysis started. Use /youtube/analysis/{job_id} to check status."
    )


@router.get("/youtube/analysis/{job_id}", response_model=AnalysisResult)
async def get_analysis_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get status and results of an analysis job.
    """
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    
    # Fallback to in-memory if not found in DB (sanity check during migration? No, clean break)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    # Extract data from stored JSON
    analysis_data = job.analysis_result or {}
    results = analysis_data.get("results", {})
    
    # If job just started, analysis_result might be None, but status is PENDING
    status = job.status.value if hasattr(job.status, "value") else job.status
    
    return AnalysisResult(
        job_id=job_id,
        status=status,
        progress=job.progress,
        video_info=results.get("ingestion"),
        engagement=results.get("signal_analysis"),
        transcript=results.get("transcription"),
        nlp_analysis=results.get("nlp_analysis"),
        policy_check=results.get("policy_check"),
        scoring=results.get("scoring"),
        recommendation=results.get("recommendation"),
        error=job.error_message or analysis_data.get("error")
    )


@router.get("/youtube/analysis/{job_id}/report")
async def get_analysis_report(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get formatted analysis report for a completed job.
    """
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()

    
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    analysis_data = job.analysis_result or {}
    results = analysis_data.get("results", {})
    
    # Check status (VideoJob uses Enum, analysis_result has string)
    status = job.status.value if hasattr(job.status, "value") else str(job.status)
    
    if status != "completed":
        raise HTTPException(status_code=400, detail="Analysis not yet complete")
    
    scoring = results.get("scoring", {})
    
    # Generate executive summary
    final_score = scoring.get("final_score", 0)
    grade = scoring.get("grade", "N/A")
    
    # If the professional Stage 10 report exists, use it
    reporting_data = results.get("reporting", {})
    if reporting_data and not reporting_data.get("error"):
        # Enrich basic report with professional insights
        report = {
            "executive_summary": reporting_data.get("executive_summary", f"Video analysis complete. Score: {final_score}/10"),
            "key_insights": reporting_data.get("key_takeaways", []),
            "score_visualization": {
                "overall": final_score,
                "breakdown": scoring.get("breakdown", {})
            },
            "recommendation": scoring.get("recommendation", ""),
            "policy_status": results.get("policy_check", {}).get("risk_level", "unknown"),
            "keywords": results.get("nlp_analysis", {}).get("keywords", [])[:10],
            "action_plan": reporting_data.get("three_step_action_plan", [])
        }
        return report

    # Fallback to basic logic for older/failed reporting jobs
    report = {
        "executive_summary": f"Video analysis complete. Score: {final_score}/10 (Grade: {grade})",
        "key_insights": [],
        "score_visualization": {
            "overall": final_score,
            "breakdown": scoring.get("breakdown", {})
        },
        "recommendation": scoring.get("recommendation", ""),
        "policy_status": results.get("policy_check", {}).get("risk_level", "unknown"),
        "keywords": results.get("nlp_analysis", {}).get("keywords", [])[:10]
    }
    
    # Add insights
    engagement = results.get("signal_analysis", {})
    if engagement.get("engagement_score", 0) >= 7:
        report["key_insights"].append("✅ High engagement metrics")
    
    policy = results.get("policy_check", {})
    if policy.get("policy_safe"):
        report["key_insights"].append("✅ Content safe for all platforms")
    elif policy.get("risk_level") == "medium":
        report["key_insights"].append("⚠️ Some policy concerns detected")
    else:
        report["key_insights"].append("❌ High policy risk - not recommended")
    
    nlp = results.get("nlp_analysis", {})
    if nlp.get("sentiment") == "positive":
        report["key_insights"].append("✅ Positive content sentiment")
    
    return report


@router.post("/youtube/analyze-quick")
async def analyze_youtube_quick(request: YouTubeAnalyzeRequest):
    """
    Quick synchronous analysis for a single video.
    Returns results directly (may take 30-60 seconds).
    """
    config = PipelineConfig(
        video_url=request.youtube_url,
        min_score=request.min_score_threshold
    )
    
    try:
        result = await orchestrator.run_pipeline(config)
        
        return {
            "success": result.status == PipelineStatus.COMPLETED,
            "status": result.status.value,
            "results": result.results,
            "error": result.error
        }
    except Exception as e:
        logger.error(f"Quick analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PHASE 2: CHANNEL ANALYSIS ====================

from app.services.youtube.channel_analyzer import channel_analyzer


@router.post("/youtube/channel/analyze")
async def analyze_channel(request: YouTubeChannelRequest, background_tasks: BackgroundTasks):
    """
    Analyze a YouTube channel with video listing and metrics.
    """
    job_id = str(uuid.uuid4())
    
    _analysis_jobs[job_id] = {"status": "pending", "type": "channel"}
    
    async def run_channel_analysis():
        try:
            result = await channel_analyzer.analyze_channel(
                request.channel_url,
                max_videos=request.max_videos
            )
            
            _analysis_jobs[job_id] = {
                "status": "completed",
                "type": "channel",
                "results": {
                    "channel_info": {
                        "id": result.channel_info.channel_id,
                        "title": result.channel_info.title,
                        "subscribers": result.channel_info.subscriber_count,
                        "videos": result.channel_info.video_count,
                        "total_views": result.channel_info.total_views,
                        "thumbnail": result.channel_info.thumbnail_url
                    },
                    "videos": [
                        {
                            "id": v.video_id,
                            "title": v.title,
                            "views": v.view_count,
                            "likes": v.like_count,
                            "duration": v.duration_seconds,
                            "published": v.published_at,
                            "thumbnail": v.thumbnail_url
                        }
                        for v in result.videos
                    ],
                    "metrics": result.metrics,
                    "score": result.channel_score,
                    "status": result.channel_status,
                    "reasoning": result.reasoning
                }
            }
        except Exception as e:
            logger.error(f"Channel analysis failed: {e}")
            _analysis_jobs[job_id] = {
                "status": "failed",
                "error": str(e)
            }
    
    background_tasks.add_task(run_channel_analysis)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Channel analysis started"
    }


@router.get("/youtube/channel/{job_id}")
async def get_channel_analysis(job_id: str):
    """Get channel analysis results"""
    job = _analysis_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/youtube/channel/filter-videos")
async def filter_channel_videos(
    job_id: str,
    min_views: int = 0,
    max_duration: int = None,
    days_ago: int = None,
    sort_by: str = "views"
):
    """Filter videos from a channel analysis"""
    job = _analysis_jobs.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Analysis not complete")
    
    videos = job.get("results", {}).get("videos", [])
    
    # Apply filters
    filtered = []
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    for v in videos:
        if v["views"] < min_views:
            continue
        if max_duration and v["duration"] > max_duration:
            continue
        if days_ago:
            try:
                pub = datetime.fromisoformat(v["published"].replace("Z", "+00:00"))
                if (now - pub).days > days_ago:
                    continue
            except:
                pass
        filtered.append(v)
    
    # Sort
    if sort_by == "views":
        filtered.sort(key=lambda x: x["views"], reverse=True)
    elif sort_by == "likes":
        filtered.sort(key=lambda x: x["likes"], reverse=True)
    elif sort_by == "date":
        filtered.sort(key=lambda x: x["published"], reverse=True)
    
    return {
        "total": len(filtered),
        "videos": filtered
    }


# ==================== PHASE 3: BATCH PROCESSING ====================

from app.services.youtube.batch_processor import batch_processor

# Store batch jobs
_batch_jobs: dict = {}


@router.post("/youtube/batch/create")
async def create_batch(video_ids: list[str], config: dict = None):
    """Create a batch processing job"""
    job = await batch_processor.create_batch(video_ids, config or {})
    
    return {
        "success": True,
        "batch_id": job.batch_id,
        "total_videos": len(video_ids),
        "message": "Batch created. Use /youtube/batch/{batch_id}/start to begin processing."
    }


@router.post("/youtube/batch/{batch_id}/start")
async def start_batch(batch_id: str, background_tasks: BackgroundTasks):
    """Start batch processing"""
    try:
        async def progress_update(job):
            _batch_jobs[batch_id] = batch_processor.get_job_summary(batch_id)
        
        await batch_processor.start_batch(batch_id, progress_update)
        
        return {
            "success": True,
            "message": "Batch processing started"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/youtube/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """Get batch processing status"""
    summary = batch_processor.get_job_summary(batch_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Batch not found")
    return summary


@router.get("/youtube/batch/{batch_id}/recommendations")
async def get_batch_recommendations(batch_id: str):
    """Get recommended videos from batch analysis"""
    recommendations = batch_processor.get_recommendations(batch_id)
    return {
        "count": len(recommendations),
        "recommendations": recommendations
    }


@router.post("/youtube/batch/{batch_id}/cancel")
async def cancel_batch(batch_id: str):
    """Cancel batch processing"""
    success = batch_processor.cancel_job(batch_id)
    return {"success": success}


# ==================== PHASE 4: GOOGLE DRIVE ====================

from app.services.youtube.drive_uploader import drive_uploader


@router.post("/drive/connect")
async def connect_drive(access_token: str, refresh_token: str = None):
    """Connect Google Drive with OAuth token"""
    drive_uploader.set_credentials(access_token, refresh_token)
    
    return {
        "success": True,
        "authenticated": drive_uploader.is_authenticated,
        "message": "Drive connected successfully"
    }


@router.post("/drive/upload")
async def upload_to_drive(
    batch_id: str,
    folder_name: str = None,
    background_tasks: BackgroundTasks = None
):
    """Upload batch results to Google Drive"""
    if not drive_uploader.is_authenticated:
        raise HTTPException(status_code=401, detail="Drive not connected")
    
    job = batch_processor.get_job(batch_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get processed files
    files = [
        v.processed_path for v in job.videos
        if v.processed_path and v.processed_path.exists()
    ]
    
    if not files:
        raise HTTPException(status_code=400, detail="No processed files to upload")
    
    # Generate folder name
    folder_path = folder_name or drive_uploader.generate_folder_name(
        channel_name=f"Batch_{batch_id}"
    )
    
    # Upload
    result = await drive_uploader.upload_batch(files, folder_path)
    
    return {
        "success": result.success,
        "folder_url": result.folder.url if result.folder else None,
        "files_uploaded": len(result.files),
        "total_size_mb": round(result.total_size_bytes / (1024 * 1024), 2),
        "upload_time": result.upload_time_seconds,
        "failed": result.failed_files
    }


@router.post("/drive/create-folder")
async def create_drive_folder(name: str, parent_id: str = None):
    """Create a folder in Google Drive"""
    if not drive_uploader.is_authenticated:
        raise HTTPException(status_code=401, detail="Drive not connected")
    
    folder = await drive_uploader.create_folder(name, parent_id)
    
    if not folder:
        raise HTTPException(status_code=500, detail="Failed to create folder")
    
    return {
        "success": True,
        "folder_id": folder.folder_id,
        "folder_url": folder.url
    }
