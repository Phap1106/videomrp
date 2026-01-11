"""Audio separation utilities

Provides a simple, robust wrapper that runs an external separation tool
(spleeter by default, or demucs if configured) and returns paths to
produced stems along with durations.

The implementation is deliberately light-weight (calls subprocess) so it
does not impose heavy pip dependencies. Unit tests mock the command
behavior to allow CI without installing spleeter/demucs.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.core.logger import logger

from app.core.config import settings
from app.utils.ffmpeg_ops import FFmpegOperations

_ffops = FFmpegOperations()


class SeparationError(RuntimeError):
    pass


async def separate_audio(
    input_path: str, output_dir: str | None = None
) -> dict[str, object | None]:
    """Run audio separation and return stem file paths and durations.

    Returns a dict like:
    {
        "vocals": "/abs/path/to/vocals.wav",
        "accompaniment": "/abs/path/to/accompaniment.wav",
        "durations": {"vocals": 3.12, "accompaniment": 3.12}
    }

    Raises SeparationError if the configured separation binary is not
    available or the separation process fails.
    """
    input_p = Path(input_path)
    if not input_p.exists():
        raise SeparationError(f"Input audio file does not exist: {input_path}")

    # Decide output_dir
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = Path(settings.SEPARATION_OUTPUT_DIR) / input_p.stem

    out_dir.mkdir(parents=True, exist_ok=True)

    # Choose tool
    tool = "demucs" if settings.USE_DEMUCS or settings.SEPARATION_TOOL == "demucs" else "spleeter"

    # Ensure binary present
    if shutil.which(tool) is None:
        raise SeparationError(
            f"Separation tool '{tool}' not found on PATH. "
            "Install the tool or set USE_DEMUCS accordingly."
        )

    # Build command
    if tool == "demucs":
        # Example: demucs --two-stems -o out_dir input_path
        cmd = ["demucs", "separate", "-n", "htdemucs", "-o", str(out_dir), str(input_p)]
    else:
        # Spleeter: spleeter separate -p spleeter:2stems -o out_dir input_path
        cmd = [
            "spleeter",
            "separate",
            "-p",
            "spleeter:2stems",
            "-o",
            str(out_dir),
            str(input_p),
        ]

    logger.info("Running audio separation: %s", " ".join(cmd))

    try:
        # subprocess.run is blocking; wrap in thread pool to avoid blocking event loop
        proc = await subprocess.to_thread(subprocess.run, cmd, check=True, capture_output=True)
        logger.debug("Separation stdout: %s", proc.stdout)
        logger.debug("Separation stderr: %s", proc.stderr)
    except Exception as exc:
        logger.error("Audio separation failed: %s", exc)
        raise SeparationError(f"Audio separation failed: {exc}") from exc

    # Find produced stems
    # Spleeter usually creates <out_dir>/<stemdir>/vocals.wav and accompaniment.wav
    vocals_candidates = list(out_dir.glob("**/vocals*.wav"))
    accompaniment_candidates = list(out_dir.glob("**/accompaniment*.wav"))

    # Some tools name instrumental or accompaniment differently
    if not accompaniment_candidates:
        accompaniment_candidates = list(out_dir.glob("**/*instrumental*.wav"))
    if not accompaniment_candidates:
        accompaniment_candidates = list(out_dir.glob("**/*accomp*.wav"))

    vocals = str(vocals_candidates[0]) if vocals_candidates else None
    accompaniment = str(accompaniment_candidates[0]) if accompaniment_candidates else None

    durations: dict[str, float] = {}

    # Use ffprobe wrapper to get durations if available
    if vocals and _ffops.available:
        info = await _ffops.get_video_info(vocals)
        durations["vocals"] = info.get("duration", 0)
    if accompaniment and _ffops.available:
        info = await _ffops.get_video_info(accompaniment)
        durations["accompaniment"] = info.get("duration", 0)

    result = {
        "vocals": vocals,
        "accompaniment": accompaniment,
        "durations": durations,
    }

    logger.info("Separation result: %s", result)
    return result
