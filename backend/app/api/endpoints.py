import shutil
import time
import uuid
from pathlib import Path
from typing import Any

import anyio
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import logger
from app.database import SessionLocal, get_db
from app.models import JobStatus, Platform, VideoJob, VideoType, JobEvent
from app.schemas import (
    VideoAnalyzeRequest,
    VideoCreateRequest,
)
from app.services.content_analyzer import ContentAnalyzer
from app.services.platform_detector import PlatformDetector
from app.services.video_downloader import VideoDownloader
from app.services.video_editor import VideoEditor
from app.utils.file_utils import ensure_dirs

router = APIRouter()


def _enum_value(x):
    return getattr(x, "value", x)


def _get_attr(obj, *names, default=None):
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return default


def _order_col():
    return (
        getattr(VideoJob, "created_at", None)
        or getattr(VideoJob, "createdAt", None)
        or getattr(VideoJob, "id", None)
    )


def serialize_job(job: VideoJob) -> dict[str, Any]:
    return jsonable_encoder(
        {
            "id": str(getattr(job, "id", "")),
            "title": getattr(job, "title", None),
            "source_url": getattr(job, "source_url", None),
            "source_platform": _enum_value(getattr(job, "source_platform", None)),
            "target_platform": _enum_value(getattr(job, "target_platform", None)),
            "video_type": _enum_value(getattr(job, "video_type", None)),
            "duration": getattr(job, "duration", None),
            "add_subtitles": getattr(job, "add_subtitles", None),
            "change_music": getattr(job, "change_music", None),
            "remove_watermark": getattr(job, "remove_watermark", None),
            "add_effects": getattr(job, "add_effects", None),
            "meme_template": getattr(job, "meme_template", None),
            "status": _enum_value(getattr(job, "status", None)),
            "progress": getattr(job, "progress", 0),
            "current_step": getattr(job, "current_step", None),
            "error_message": getattr(job, "error_message", None),
            "input_path": getattr(job, "input_path", None),
            "output_path": getattr(job, "output_path", None),
            "output_filename": getattr(job, "output_filename", None),
            "analysis_result": getattr(job, "analysis_result", None),
            "ai_instructions": getattr(job, "ai_instructions", None),
            "processing_flow": getattr(job, "processing_flow", None),
            "processing_options": getattr(job, "processing_options", None),
            "created_at": _get_attr(job, "created_at", "createdAt"),
            "updated_at": _get_attr(job, "updated_at", "updatedAt"),
        }
    )


@router.get("/health")
async def health_check():
    from redis import Redis

    uptime = None
    try:
        import psutil

        uptime = time.time() - psutil.boot_time()
    except Exception:
        uptime = None

    checks = {
        "api": True,
        "database": False,
        "redis": False,
        "storage": False,
        "ai_services": {
            "openai": bool(settings.OPENAI_API_KEY),
            "gemini": bool(settings.GEMINI_API_KEY),
        },
        "queue_size": 0,
        "active_jobs": 0,
        "total_jobs": 0,
        "uptime": uptime,
        "version": settings.APP_VERSION,
        "timestamp": time.time(),
    }

    try:
        ensure_dirs()
        test_file = Path("data") / "__healthcheck.txt"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        checks["storage"] = True
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        checks["database"] = True

        checks["total_jobs"] = db.query(VideoJob).count()
        checks["active_jobs"] = (
            db.query(VideoJob)
            .filter(
                VideoJob.status.in_(
                    [JobStatus.PROCESSING, JobStatus.ANALYZING, JobStatus.DOWNLOADING]
                )
            )
            .count()
        )
        db.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    try:
        if getattr(settings, "REDIS_URL", None):
            redis_client = Redis.from_url(settings.REDIS_URL)
            redis_client.ping()
            checks["redis"] = True
        else:
            checks["redis"] = False
    except Exception as e:
        logger.warning(f"Redis health check failed (optional): {e}")

    status_code = 200 if checks["database"] else 503
    return JSONResponse(status_code=status_code, content=jsonable_encoder(checks))


@router.get("/debug/db-columns")
async def debug_db_columns():
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Debug endpoints disabled")

    try:
        db = SessionLocal()
        res = db.execute(
            text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'video_jobs'"
            )
        )
        cols = [r[0] for r in res.fetchall()]
        db.close()
        return {"columns": cols}
    except Exception as e:
        logger.error(f"Failed to read video_jobs columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug/ensure-schema")
async def debug_ensure_schema(background_tasks: BackgroundTasks):
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Debug endpoints disabled")

    try:
        from app.database import ensure_video_jobs_columns

        await anyio.to_thread.run_sync(ensure_video_jobs_columns)
        return {"status": "ok", "message": "Schema ensure attempted"}
    except Exception as e:
        logger.error(f"Failed to ensure schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms")
async def get_platforms():
    detector = PlatformDetector()
    platforms: list[dict[str, Any]] = []

    for platform in Platform:
        if platform == Platform.GENERIC:
            continue

        enabled_attr = f"ENABLE_{platform.value.upper()}"
        if not getattr(settings, enabled_attr, True):
            continue

        rules = detector.get_platform_rules(platform)
        platforms.append(
            jsonable_encoder(
                {
                    "platform": platform.value,
                    "name": platform.value.capitalize(),
                    **rules,
                }
            )
        )

    return JSONResponse(content=jsonable_encoder(platforms))


@router.get("/processing-flows")
async def processing_flows():
    try:
        presets = getattr(settings, "PROCESSING_FLOW_PRESETS", {})
        items = [
            {
                "key": k,
                "label": v.get("label"),
                "description": v.get("description"),
                "options": v.get("options", {}),
            }
            for k, v in presets.items()
        ]
        return JSONResponse(content=jsonable_encoder(items))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs")
async def create_job(
    request: VideoCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    enabled_attr = f"ENABLE_{request.target_platform.value.upper()}"
    if not getattr(settings, enabled_attr, True):
        raise HTTPException(
            status_code=400,
            detail=f"Platform {request.target_platform.value} is not enabled",
        )

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
        processing_flow=getattr(request, "processing_flow", None).value
        if getattr(request, "processing_flow", None) is not None
        else "auto",
        processing_options=request.processing_options or {},
        status=JobStatus.PENDING,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_video_job, job_id)

    return JSONResponse(content=jsonable_encoder(serialize_job(job)))


@router.get("/jobs/{job_id}/logs")
async def get_job_logs(job_id: str, db: Session = Depends(get_db)):
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    events = (
        db.query(JobEvent)
        .filter(JobEvent.job_id == job_id)
        .order_by(JobEvent.created_at.asc())
        .all()
    )
    return JSONResponse(
        content=jsonable_encoder(
            [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "message": e.message,
                    "data": e.data,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ]
        )
    )


@router.get("/jobs")
async def list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: JobStatus | None = None,
    platform: Platform | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(VideoJob)

    if status:
        query = query.filter(VideoJob.status == status)
    if platform:
        query = query.filter(VideoJob.target_platform == platform)

    total = query.count()

    col = _order_col()
    if col is not None:
        try:
            query = query.order_by(col.desc())
        except Exception:
            pass

    items = query.offset((page - 1) * size).limit(size).all()

    payload = {
        "items": [serialize_job(x) for x in items],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }
    return JSONResponse(content=jsonable_encoder(payload))


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse(content=jsonable_encoder(serialize_job(job)))


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if getattr(job, "input_path", None) and Path(job.input_path).exists():
        Path(job.input_path).unlink(missing_ok=True)
    if getattr(job, "output_path", None) and Path(job.output_path).exists():
        Path(job.output_path).unlink(missing_ok=True)

    db.delete(job)
    db.commit()

    return JSONResponse(
        content=jsonable_encoder({"success": True, "message": "Job deleted successfully"})
    )


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.FAILED:
        raise HTTPException(status_code=400, detail="Job is not in failed state")

    job.status = JobStatus.PENDING
    job.progress = 0
    job.current_step = "initializing"
    job.error_message = None
    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_video_job, job_id)

    return JSONResponse(content=jsonable_encoder(serialize_job(job)))


@router.post("/analyze")
async def analyze_video(
    request: VideoAnalyzeRequest,
    db: Session = Depends(get_db),
):
    job_id = str(uuid.uuid4())

    detector = PlatformDetector()
    source_platform = detector.detect(request.source_url)

    job = VideoJob(
        id=job_id,
        title="Video Analysis",
        source_url=request.source_url,
        source_platform=source_platform,
        target_platform=request.target_platform,
        status=JobStatus.ANALYZING,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        downloader = VideoDownloader()
        work_dir = Path(settings.TEMP_DIR) / job_id
        work_dir.mkdir(parents=True, exist_ok=True)

        download_result = await downloader.download(request.source_url, work_dir)
        job.input_path = download_result["path"]
        db.commit()

        analyzer = ContentAnalyzer()
        options = {"duration": 60, "add_subtitles": False}
        analysis_result = await analyzer.analyze_video(
            video_path=download_result["path"],
            platform=request.target_platform.value,
            video_type="short",
            options=options,
        )

        job.analysis_result = analysis_result
        job.status = JobStatus.COMPLETED
        db.commit()

        try:
            Path(download_result["path"]).unlink(missing_ok=True)
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass

        payload = {
            "job_id": job_id,
            "summary": analysis_result.get("analysis", {}).get("summary", ""),
            "category": analysis_result.get("analysis", {}).get("category", ""),
            "mood": analysis_result.get("analysis", {}).get("mood", ""),
            "duration": analysis_result.get("video_metadata", {}).get("duration", 0),
            "key_moments": analysis_result.get("analysis", {}).get("key_moments", []),
            "scenes": analysis_result.get("segments", []),
            "copyright_risks": analysis_result.get("copyright_check", {}).get(
                "copyright_risks", []
            ),
            "suggestions": analysis_result.get("editing_instructions", []),
            "used_rule_based": bool(
                (analysis_result.get("editing_instructions") or {}).get("used_rule_based", False)
            ),
            "used_provider": (analysis_result.get("editing_instructions") or {}).get(
                "used_provider"
            ),
            "hashtags": analysis_result.get("hashtags", {}).get("hashtags", []),
            "titles": analysis_result.get("hashtags", {}).get("titles", []),
            "viral_score": analysis_result.get("analysis", {}).get("viral_potential", 0),
            "processing_time": analysis_result.get("processing_time", 0),
        }
        return JSONResponse(content=jsonable_encoder(payload))

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/processed/{filename}")
async def get_processed_video(filename: str):
    file_path = Path(settings.PROCESSED_DIR) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, media_type="video/mp4", filename=filename)


@router.post("/batch")
async def create_batch_jobs(
    requests: list[VideoCreateRequest],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    detector = PlatformDetector()
    jobs: list[VideoJob] = []

    for request in requests:
        enabled_attr = f"ENABLE_{request.target_platform.value.upper()}"
        if not getattr(settings, enabled_attr, True):
            continue

        job_id = str(uuid.uuid4())
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
            status=JobStatus.PENDING,
        )
        db.add(job)
        jobs.append(job)

    db.commit()

    for job in jobs:
        background_tasks.add_task(process_video_job, job.id)

    return JSONResponse(content=jsonable_encoder([serialize_job(j) for j in jobs]))


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_platform: Platform = Platform.TIKTOK,
    video_type: VideoType = VideoType.SHORT,
    duration: int = 60,
    db: Session = Depends(get_db),
):
    max_size = settings.MAX_UPLOAD_SIZE * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE}MB",
        )

    allowed_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )

    ensure_dirs()
    job_id = str(uuid.uuid4())
    upload_dir = Path(settings.UPLOAD_DIR) / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job = VideoJob(
        id=job_id,
        title=file.filename,
        source_url=f"file://{file_path}",
        source_platform=Platform.GENERIC,
        target_platform=target_platform,
        video_type=video_type,
        duration=duration,
        input_path=str(file_path),
        status=JobStatus.PENDING,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_video_job, job_id)

    return JSONResponse(content=jsonable_encoder(serialize_job(job)))


@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    stats: dict[str, Any] = {}

    stats["total_jobs"] = db.query(VideoJob).count()
    stats["completed_jobs"] = (
        db.query(VideoJob).filter(VideoJob.status == JobStatus.COMPLETED).count()
    )
    stats["failed_jobs"] = db.query(VideoJob).filter(VideoJob.status == JobStatus.FAILED).count()
    stats["active_jobs"] = (
        db.query(VideoJob)
        .filter(
            VideoJob.status.in_([JobStatus.PROCESSING, JobStatus.ANALYZING, JobStatus.DOWNLOADING])
        )
        .count()
    )

    platforms: dict[str, int] = {}
    for p in Platform:
        count = db.query(VideoJob).filter(VideoJob.target_platform == p).count()
        if count > 0:
            platforms[p.value] = count
    stats["platform_distribution"] = platforms

    upload_dir = Path(settings.UPLOAD_DIR)
    processed_dir = Path(settings.PROCESSED_DIR)

    stats["storage_usage"] = {
        "uploads": sum(f.stat().st_size for f in upload_dir.rglob("*") if f.is_file())
        if upload_dir.exists()
        else 0,
        "processed": sum(f.stat().st_size for f in processed_dir.rglob("*") if f.is_file())
        if processed_dir.exists()
        else 0,
    }

    return JSONResponse(content=jsonable_encoder(stats))


async def _process_video_job_async(job_id: str):
    db = SessionLocal()

    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()

        if not job:
            logger.error(f"Job {job_id} not found in database")
            return

        logger.info(f"Processing job {job_id}: {job.source_url}")

        job.status = JobStatus.DOWNLOADING
        job.progress = 10
        job.current_step = "Downloading video"
        db.commit()

        downloader = VideoDownloader()
        work_dir = Path(settings.TEMP_DIR) / job_id
        work_dir.mkdir(parents=True, exist_ok=True)

        download_result = await downloader.download(job.source_url, work_dir)
        job.input_path = download_result["path"]
        job.progress = 30
        job.current_step = "Analyzing content"
        db.commit()

        analyzer = ContentAnalyzer()

        requested_flow = getattr(job, "processing_flow", "auto") or "auto"
        presets = getattr(settings, "PROCESSING_FLOW_PRESETS", {}) or {}

        effective_flow = requested_flow
        effective_options = (getattr(job, "processing_options", {}) or {}).copy()

        if requested_flow == "auto":
            if any(
                [
                    getattr(settings, "DEEPGRAM_API_KEY", None),
                    getattr(settings, "OPENAI_API_KEY", None),
                    getattr(settings, "GROQ_API_KEY", None),
                    getattr(settings, "GEMINI_API_KEY", None),
                ]
            ):
                effective_flow = "ai"
            else:
                effective_flow = "fast"

        preset = presets.get(effective_flow, {}) if isinstance(presets, dict) else {}
        preset_opts = preset.get("options", {}) if isinstance(preset, dict) else {}

        for k, v in (preset_opts or {}).items():
            if k not in effective_options:
                effective_options[k] = v

        options = {
            "duration": job.duration,
            "add_subtitles": bool(job.add_subtitles),
            "add_effects": bool(job.add_effects),
            "remove_watermark": bool(job.remove_watermark),
            "change_music": bool(job.change_music),
            "processing_flow": effective_flow,
            "processing_options": effective_options,
        }

        try:
            job.processing_flow = effective_flow
            job.processing_options = effective_options
            db.commit()
        except Exception:
            db.rollback()

        if effective_flow == "fast":
            logger.info("Using fast (rule-based) processing flow for job %s" % job_id)
            video_meta = await analyzer._get_video_metadata(download_result["path"])
            analysis_result = {
                "transcript": "",
                "segments": [],
                "analysis": analyzer._mock_analysis(
                    "", _enum_value(job.target_platform), _enum_value(job.video_type) or "short"
                ),
                "copyright_check": analyzer._mock_copyright_check(),
                "editing_instructions": analyzer._rule_based_editing_instructions(
                    "",
                    _enum_value(job.target_platform),
                    _enum_value(job.video_type) or "short",
                    options,
                ),
                "hashtags": analyzer._mock_hashtags(_enum_value(job.target_platform)),
                "processing_time": 0,
                "video_metadata": video_meta,
            }
        else:
            analysis_result = await analyzer.analyze_video(
                video_path=download_result["path"],
                platform=_enum_value(job.target_platform),
                video_type=_enum_value(job.video_type) or "short",
                options=options,
            )

        job.analysis_result = analysis_result
        job.progress = 50
        job.current_step = "Generating editing instructions"
        db.commit()

        editing_instructions = analysis_result.get("editing_instructions") or {}
        if isinstance(editing_instructions, list):
            editing_instructions = {"clips": editing_instructions}

        editing_instructions.setdefault(
            "processing_options", getattr(job, "processing_options", {}) or {}
        )
        editing_instructions.setdefault("processing_flow", getattr(job, "processing_flow", "auto"))

        if not editing_instructions.get("clips"):
            duration = (
                analysis_result.get("video_metadata", {}).get("duration") or job.duration or 60
            )
            clip = {
                "start_time": 0,
                "end_time": min(duration, job.duration or 60),
                "action": "keep",
                "effects": [],
            }

            if job.remove_watermark:
                clip["effects"].append("watermark_removal")
            if job.add_effects:
                clip["effects"].append("zoom_in")
            if job.change_music:
                clip["mute_audio"] = True

            editing_instructions["clips"] = [clip]

            if job.add_subtitles:
                editing_instructions["subtitle_text"] = analysis_result.get("transcript", "")[:800]

        editing_instructions.setdefault("platform_specific_settings", {})
        editing_instructions["platform_specific_settings"].setdefault(
            "aspect_ratio",
            "9:16" if _enum_value(job.target_platform) == "tiktok" else "16:9",
        )

        job.ai_instructions = editing_instructions
        job.progress = 60
        job.current_step = "Editing video"
        db.commit()

        editor = VideoEditor()
        processed_dir = Path(settings.PROCESSED_DIR) / job_id
        processed_dir.mkdir(parents=True, exist_ok=True)
        output_path = processed_dir / f"{job_id}.mp4"

        edit_result = await editor.edit_video(
            input_path=download_result["path"],
            instructions=editing_instructions,
            output_path=str(output_path),
            platform=_enum_value(job.target_platform),
        )

        job.output_path = str(output_path)
        job.output_filename = f"{job_id}.mp4"

        if isinstance(edit_result, dict) and edit_result.get("skipped_editing"):
            job.progress = 90
            job.current_step = "Skipped editing (ffmpeg not available)"
            job.error_message = job.error_message or None
            logger.warning(
                f"Job {job_id}: ffmpeg missing, skipped editing and copied input to output"
            )
            try:
                ev = JobEvent(
                    job_id=job.id,
                    event_type="warning",
                    message="FFmpeg not available - skipped editing and copied input to output",
                    data=edit_result,
                )
                db.add(ev)
                db.commit()
            except Exception:
                db.rollback()
            db.commit()
        else:
            job.progress = 90
            job.current_step = "Finalizing"
            db.commit()

        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)

        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.current_step = "Completed"
        db.commit()

        logger.info(f"✅ Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}", exc_info=True)

        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.current_step = "Failed"
            try:
                ev = JobEvent(
                    job_id=job.id, event_type="error", message=str(e), data={"step": "processing"}
                )
                db.add(ev)
                db.commit()
            except Exception:
                db.rollback()
            db.commit()

    finally:
        db.close()


def process_video_job(job_id: str):
    anyio.run(_process_video_job_async, job_id)


api_router = router