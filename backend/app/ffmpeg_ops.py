import subprocess
from pathlib import Path
from .core.config import settings

def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "FFmpeg failed")

def trim(input_path: Path, output_path: Path, seconds: int) -> None:
    # take first N seconds
    run([settings.ffmpeg_bin, "-y", "-i", str(input_path), "-t", str(seconds),
         "-c:v", "libx264", "-c:a", "aac", str(output_path)])

def normalize_audio(input_path: Path, output_path: Path) -> None:
    # EBU R128 loudnorm (simple 2-pass is better; keep simple here)
    run([settings.ffmpeg_bin, "-y", "-i", str(input_path),
         "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
         "-c:v", "copy", "-c:a", "aac", str(output_path)])

def burn_subtitles(input_path: Path, srt_path: Path, output_path: Path) -> None:
    run([settings.ffmpeg_bin, "-y", "-i", str(input_path),
         "-vf", f"subtitles={str(srt_path)}",
         "-c:v", "libx264", "-c:a", "aac", str(output_path)])

def replace_audio(input_path: Path, audio_path: Path, output_path: Path) -> None:
    run([settings.ffmpeg_bin, "-y",
         "-i", str(input_path), "-i", str(audio_path),
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac",
         "-shortest", str(output_path)])
