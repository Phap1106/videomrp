import json
import subprocess
from typing import Any

from app.core.logger import logger

from app.core.config import settings


class FFmpegOperations:
    """FFmpeg operations wrapper"""

    def __init__(self):
        self.ffmpeg_path = settings.FFMPEG_PATH
        self.ffprobe_path = settings.FFPROBE_PATH

        # Check availability of binaries early to provide clearer error messages
        self.available = True
        self.missing_binaries: list[str] = []

        import shutil

        # If provided paths look like names, try shutil.which
        ffmpeg_ok = (
            shutil.which(self.ffmpeg_path) is not None
            if isinstance(self.ffmpeg_path, str)
            else False
        )
        ffprobe_ok = (
            shutil.which(self.ffprobe_path) is not None
            if isinstance(self.ffprobe_path, str)
            else False
        )

        # Also accept explicit paths that exist
        from pathlib import Path

        if not ffmpeg_ok and Path(self.ffmpeg_path).exists():
            ffmpeg_ok = True
        if not ffprobe_ok and Path(self.ffprobe_path).exists():
            ffprobe_ok = True

        if not ffmpeg_ok:
            self.missing_binaries.append(str(self.ffmpeg_path))
        if not ffprobe_ok:
            self.missing_binaries.append(str(self.ffprobe_path))

        if self.missing_binaries:
            self.available = False
            logger.warning(
                f"FFmpeg/FFprobe binaries not found ({', '.join(self.missing_binaries)}). "
                "Install ffmpeg and/or set FFMPEG_PATH / FFPROBE_PATH in env to enable video operations."
            )

    def _ensure_available(self):
        if not self.available:
            raise RuntimeError(
                f"FFmpeg/FFprobe not available ({', '.join(self.missing_binaries)}). "
                "Install ffmpeg and/or set FFMPEG_PATH / FFPROBE_PATH in env."
            )

    async def get_video_info(self, video_path: str) -> dict[str, Any]:
        """Get video information"""
        try:
            self._ensure_available()

            cmd = [
                self.ffprobe_path,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(video_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            info = {
                "duration": float(data["format"].get("duration", 0)),
                "size": int(data["format"].get("size", 0)),
                "bitrate": int(data["format"].get("bit_rate", 0)),
            }

            for stream in data.get("streams", []):
                if stream["codec_type"] == "video":
                    info.update(
                        {
                            "width": stream.get("width", 0),
                            "height": stream.get("height", 0),
                            "codec": stream.get("codec_name", ""),
                            "fps": eval(stream.get("avg_frame_rate", "0/1"))
                            if "avg_frame_rate" in stream
                            else 0,
                        }
                    )
                    break

            return info
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return {}

    async def extract_clip(
        self, input_path: str, output_path: str, start_time: float, end_time: float
    ):
        """Extract clip from video"""
        self._ensure_available()

        cmd = [
            self.ffmpeg_path,
            "-i",
            input_path,
            "-ss",
            str(start_time),
            "-to",
            str(end_time),
            "-c",
            "copy",
            "-y",
            output_path,
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    async def apply_filters(
        self,
        input_path: str,
        output_path: str,
        filters: str | None,
        audio_filters: str | None = None,
    ):
        """Apply video filters (supports optional audio filters)

        - If filters is None, no -vf is passed.
        - If audio_filters provided, we encode audio (aac) and apply -af.
        """
        self._ensure_available()

        cmd = [self.ffmpeg_path, "-i", input_path]
        if filters:
            cmd += ["-vf", filters]

        if audio_filters:
            cmd += ["-af", audio_filters, "-c:a", "aac", "-b:a", "128k"]
        else:
            cmd += ["-c:a", "copy"]

        cmd += ["-y", output_path]

        subprocess.run(cmd, check=True, capture_output=True)

    async def concatenate_videos(self, concat_file: str, output_path: str):
        """Concatenate multiple videos"""
        self._ensure_available()

        cmd = [
            self.ffmpeg_path,
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-c",
            "copy",
            "-y",
            output_path,
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    async def extract_frame(self, input_path: str, output_path: str, time_offset: str):
        """Extract single frame"""
        self._ensure_available()

        cmd = [
            self.ffmpeg_path,
            "-i",
            input_path,
            "-ss",
            time_offset,
            "-vframes",
            "1",
            "-y",
            output_path,
        ]

        subprocess.run(cmd, check=True, capture_output=True)
