import uuid
from pathlib import Path
import aiofiles
import httpx
from sqlalchemy.orm import Session

from .core.paths import JOBS_DIR, PROCESSED_DIR
from .models import VideoJob, JobStatus
from .core.config import settings
from . import ffmpeg_ops
from .ai_stt import transcribe, to_srt
from .ai_translate import translate
from .ai_tts import tts_piper

def _is_direct_file_url(url: str) -> bool:
    # Chỉ cho phép URL kết thúc bằng đuôi video phổ biến nếu ALLOW_NON_FILE_URL=false
    lower = url.lower()
    return any(lower.endswith(ext) for ext in [".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"])

async def download_to(url: str, out_path: Path) -> None:
    if not settings.allow_non_file_url and not _is_direct_file_url(url):
        raise RuntimeError("URL must be a direct video file link (mp4/mov/...) or enable ALLOW_NON_FILE_URL=true")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            async with aiofiles.open(out_path, "wb") as f:
                async for chunk in r.aiter_bytes(chunk_size=1024 * 1024):
                    await f.write(chunk)

async def process_job(db: Session, job_id: str) -> None:
    job: VideoJob | None = db.get(VideoJob, job_id)
    if not job:
        return

    def set_step(step: str, prog: float):
        job.current_step = step
        job.progress = prog
        db.add(job); db.commit()

    try:
        job.status = JobStatus.processing
        db.add(job); db.commit()

        workdir = JOBS_DIR / job.id
        workdir.mkdir(parents=True, exist_ok=True)

        input_path = workdir / "input.mp4"
        set_step("downloading", 5)

        if job.source_type == "url":
            await download_to(job.source_url, input_path)
        else:
            input_path = Path(job.input_path)

        job.input_path = str(input_path)
        db.add(job); db.commit()

        cur = input_path

        # 1) trim
        if job.clip_seconds and job.clip_seconds > 0:
            set_step("trimming", 15)
            trimmed = workdir / "trimmed.mp4"
            ffmpeg_ops.trim(cur, trimmed, job.clip_seconds)
            cur = trimmed

        # 2) normalize audio
        set_step("audio_normalize", 25)
        normed = workdir / "normed.mp4"
        ffmpeg_ops.normalize_audio(cur, normed)
        cur = normed

        # 3) subtitles (STT -> translate optional -> srt -> burn)
        srt_path = workdir / "subtitles.srt"
        if settings.enable_subtitles and job.subtitles:
            set_step("transcribing", 45)
            raw_text, segments = transcribe(cur)

            if job.target_lang and job.target_lang.lower() != "auto":
                set_step("translating", 55)
                translated = await translate(raw_text, job.target_lang)
                # simplest: replace all segment text by translated full text (baseline)
                # (nâng cấp sau: dịch theo từng segment)
                segments = [{"start": segments[0]["start"], "end": segments[-1]["end"], "text": translated}] if segments else []

            async with aiofiles.open(srt_path, "w", encoding="utf-8") as f:
                await f.write(to_srt(segments))

            set_step("burning_subtitles", 70)
            subbed = workdir / "subbed.mp4"
            ffmpeg_ops.burn_subtitles(cur, srt_path, subbed)
            cur = subbed

        # 4) voiceover (TTS)
        if settings.enable_voiceover and job.voiceover:
            set_step("voiceover_tts", 80)
            # nếu không có subtitle thì vẫn STT để lấy text
            raw_text, _ = transcribe(cur)
            text_for_tts = await translate(raw_text, job.target_lang) if job.target_lang else raw_text

            wav_path = workdir / "voiceover.wav"
            tts_piper(text_for_tts, wav_path)

            set_step("mix_audio", 90)
            voiced = workdir / "voiced.mp4"
            ffmpeg_ops.replace_audio(cur, wav_path, voiced)
            cur = voiced

        # 5) export
        set_step("exporting", 97)
        out_name = f"{job.id}.mp4"
        out_path = PROCESSED_DIR / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(Path(cur).read_bytes())

        job.output_path = str(out_path)
        job.status = JobStatus.completed
        job.progress = 100
        job.current_step = "completed"
        db.add(job); db.commit()

    except Exception as e:
        job.status = JobStatus.failed
        job.error_message = str(e)
        job.current_step = "failed"
        db.add(job); db.commit()

def create_job(db: Session, title: str, source_url: str, **opts) -> VideoJob:
    jid = str(uuid.uuid4())
    job = VideoJob(
        id=jid,
        title=title or f"Video {jid[:8]}",
        source_type="url",
        source_url=source_url,
        target_lang=opts.get("target_lang", "vi"),
        clip_seconds=int(opts.get("clip_seconds", 0) or 0),
        style_preset=opts.get("style_preset", "standard"),
        subtitles=1 if opts.get("subtitles", True) else 0,
        voiceover=1 if opts.get("voiceover", False) else 0,
        make_shorts=1 if opts.get("make_shorts", False) else 0,
    )
    db.add(job); db.commit()
    return job
