from fastapi import FastAPI, Depends, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path

from .core.config import settings
from .core.paths import ensure_dirs, PROCESSED_DIR, UPLOADS_DIR
from .db import Base, engine, get_db
from .schemas import JobCreate, JobOut
from .models import VideoJob
from .pipeline import create_job, process_job

app = FastAPI(title=settings.app_name)

@app.on_event("startup")
def on_startup():
    ensure_dirs()
    Base.metadata.create_all(bind=engine)

app.mount("/processed", StaticFiles(directory=str(PROCESSED_DIR)), name="processed")

@app.get("/api/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

@app.post("/api/jobs", response_model=JobOut)
async def api_create_job(payload: JobCreate, bg: BackgroundTasks, db: Session = Depends(get_db)):
    job = create_job(
        db,
        title=payload.title,
        source_url=payload.source_url,
        target_lang=payload.target_lang,
        clip_seconds=payload.clip_seconds,
        style_preset=payload.style_preset,
        subtitles=payload.subtitles,
        voiceover=payload.voiceover,
        make_shorts=payload.make_shorts,
    )
    bg.add_task(process_job, db, job.id)
    return JobOut(
        id=job.id, title=job.title, status=job.status.value, progress=job.progress,
        current_step=job.current_step, error_message=job.error_message,
        created_at=job.created_at.isoformat(), updated_at=job.updated_at.isoformat(),
        processed_filename=f"{job.id}.mp4" if job.output_path else None
    )

@app.post("/api/jobs/upload", response_model=JobOut)
async def api_upload_job(
    bg: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = "",
    target_lang: str = "vi",
    clip_seconds: int = 0,
    subtitles: bool = True,
    voiceover: bool = False,
    db: Session = Depends(get_db),
):
    import uuid
    jid = str(uuid.uuid4())
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    in_path = UPLOADS_DIR / f"{jid}_{file.filename}"
    content = await file.read()
    in_path.write_bytes(content)

    job = VideoJob(
        id=jid, title=title or file.filename, source_type="upload", source_url="",
        input_path=str(in_path), target_lang=target_lang,
        clip_seconds=clip_seconds, subtitles=1 if subtitles else 0, voiceover=1 if voiceover else 0
    )
    db.add(job); db.commit()
    bg.add_task(process_job, db, job.id)

    return JobOut(
        id=job.id, title=job.title, status=job.status.value, progress=job.progress,
        current_step=job.current_step, error_message=job.error_message,
        created_at=job.created_at.isoformat(), updated_at=job.updated_at.isoformat()
    )

@app.get("/api/jobs", response_model=list[JobOut])
def api_list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(VideoJob).order_by(VideoJob.created_at.desc()).all()
    out = []
    for j in jobs:
        out.append(JobOut(
            id=j.id, title=j.title, status=j.status.value, progress=j.progress,
            current_step=j.current_step, error_message=j.error_message,
            created_at=j.created_at.isoformat(), updated_at=j.updated_at.isoformat(),
            processed_filename=f"{j.id}.mp4" if j.output_path else None
        ))
    return out
