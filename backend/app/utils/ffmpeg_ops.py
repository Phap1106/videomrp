"""
FFmpeg Operations - Video processing utilities
"""

import subprocess
import json
from pathlib import Path
from typing import Any, Optional, Tuple
import asyncio
from app.core.logger import logger
from app.core.config import settings


class FFmpegError(Exception):
    """FFmpeg operation error"""
    pass


class FFmpegOps:
    """FFmpeg wrapper for video operations"""

    def __init__(self):
        self.ffmpeg_path = settings.FFMPEG_PATH
        self.ffprobe_path = settings. FFPROBE_PATH

    async def _run_command(self, cmd: list[str]) -> Tuple[int, str, str]:
        """Run FFmpeg command asynchronously"""
        try: 
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess. PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=3600)
            return process.returncode, stdout.decode(), stderr.decode()
        except asyncio.TimeoutError:
            raise FFmpegError("FFmpeg command timed out")

    async def get_video_info(self, video_path: Path) -> dict[str, Any]:
        """Get video information using ffprobe"""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "error",
                "-select_streams", "v: 0",
                "-show_entries",
                "format=duration,size: stream=width,height,r_frame_rate,codec_name",
                "-of", "json",
                str(video_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"ffprobe error: {stderr}")

            data = json. loads(stdout)
            
            format_info = data.get("format", {})
            stream_info = data.get("streams", [{}])[0]
            
            # Parse framerate
            fps_str = stream_info.get("r_frame_rate", "30/1")
            fps_parts = fps_str.split("/")
            fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

            return {
                "duration": float(format_info.get("duration", 0)),
                "size": int(format_info.get("size", 0)),
                "width": int(stream_info.get("width", 1920)),
                "height": int(stream_info.get("height", 1080)),
                "fps": fps,
                "codec":  stream_info.get("codec_name", "h264"),
            }

        except Exception as e:
            logger. error(f"Error getting video info: {e}")
            raise FFmpegError(f"Failed to get video info: {str(e)}")

    async def extract_audio(self, video_path: Path, output_audio: Path) -> Path:
        """Extract audio from video"""
        try:
            logger.info(f"Extracting audio from {video_path}")
            output_audio.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-q:a", "0",
                "-map", "a",
                "-y",
                str(output_audio),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Audio extraction failed: {stderr}")

            logger.info(f"Audio extracted to {output_audio}")
            return output_audio

        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            raise

    async def replace_audio(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> Path:
        """Replace video audio with new audio"""
        try:
            logger.info(f"Replacing audio in {video_path}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c:v", "copy",  # Copy video codec
                "-c:a", "aac",   # Use AAC for audio
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Audio replacement failed:  {stderr}")

            logger.info(f"Audio replaced, output:  {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Audio replacement error: {e}")
            raise

    async def add_text_overlay(
        self,
        video_path: Path,
        text_segments: list[dict],  # [{"start": 0, "end": 5, "text": "Hello", "style": {... }}]
        output_path: Path,
        font_path: Optional[Path] = None,
        font_size: int = 60,
        font_color: str = "white",
        bg_color: str = "black",
        bg_alpha: float = 0.7,
        position: str = "bottom",  # top, center, bottom
    ) -> Path:
        """Add text overlay to video with timing"""
        try:
            logger. info(f"Adding text overlay to {video_path}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            font_path = font_path or Path(settings.DEFAULT_FONT_FILE)
            if not font_path.exists():
                logger.warning(f"Font not found: {font_path}, using default")
                font_path = None

            # Get video info for positioning
            video_info = await self.get_video_info(video_path)
            width = video_info["width"]
            height = video_info["height"]

            # Build filter complex
            filters = []
            
            for i, seg in enumerate(text_segments):
                start = seg. get("start", 0)
                end = seg.get("end", 10)
                text = seg.get("text", "").replace("'", "\\'").replace('"', '\\"')
                
                # Position calculation
                if position == "top": 
                    y_pos = int(height * 0.1)
                elif position == "center":
                    y_pos = int((height - font_size) / 2)
                else:  # bottom
                    y_pos = int(height - font_size - 20)
                
                x_pos = int((width - len(text) * font_size * 0.5) / 2)  # center x

                # Font path handling
                font_arg = f": fontfile={str(font_path)}" if font_path else ""
                
                # Create text filter with timing
                text_filter = f"drawtext=text='{text}': fontsize={font_size}: fontcolor={font_color}: x={x_pos}:y={y_pos}:enable='between(t,{start},{end})'{font_arg}"
                
                filters.append(text_filter)

            # Combine all filters
            if filters:
                filter_complex = ",".join(filters)
            else:
                filter_complex = None

            # Build command
            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-c:a", "aac",
                "-b:a", settings.AUDIO_BITRATE,
                "-y",
            ]

            if filter_complex:
                cmd. extend(["-vf", filter_complex])

            cmd.extend(["-c:v", settings.VIDEO_CODEC, "-preset", settings.VIDEO_PRESET])
            cmd.append(str(output_path))

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Text overlay failed: {stderr}")

            logger.info(f"Text overlay added, output: {output_path}")
            return output_path

        except Exception as e:
            logger. error(f"Text overlay error:  {e}")
            raise

    async def cut_video(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        output_path: Path,
    ) -> Path:
        """Cut video segment"""
        try:
            logger.info(f"Cutting video from {start_time}s to {end_time}s")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            duration = end_time - start_time

            cmd = [
                self. ffmpeg_path,
                "-i", str(video_path),
                "-ss", str(start_time),
                "-t", str(duration),
                "-c:v", settings.VIDEO_CODEC,
                "-preset", settings.VIDEO_PRESET,
                "-c:a", "aac",
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Video cut failed: {stderr}")

            logger.info(f"Video cut completed, output: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Video cut error: {e}")
            raise

    async def concatenate_videos(
        self,
        video_paths: list[Path],
        output_path:  Path,
    ) -> Path:
        """Concatenate multiple videos"""
        try:
            logger.info(f"Concatenating {len(video_paths)} videos")
            output_path.parent. mkdir(parents=True, exist_ok=True)

            # Create concat file
            concat_file = output_path. parent / "concat_list.txt"
            with open(concat_file, "w") as f:
                for vp in video_paths:
                    f.write(f"file '{str(vp)}'\n")

            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Concatenation failed: {stderr}")

            # Cleanup concat file
            concat_file.unlink()

            logger. info(f"Videos concatenated, output: {output_path}")
            return output_path

        except Exception as e: 
            logger.error(f"Video concatenation error: {e}")
            raise

    async def resize_video(
        self,
        video_path: Path,
        width: int,
        height: int,
        output_path: Path,
    ) -> Path:
        """Resize video"""
        try:
            logger.info(f"Resizing video to {width}x{height}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-vf", f"scale={width}:{height}",
                "-c: v", settings.VIDEO_CODEC,
                "-preset", settings. VIDEO_PRESET,
                "-c:a", "aac",
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Video resize failed: {stderr}")

            logger.info(f"Video resized, output: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Video resize error: {e}")
            raise

    async def generate_thumbnail(
        self,
        video_path: Path,
        timestamp: float,
        output_path: Path,
        width: int = 320,
        height: int = 180,
    ) -> Path:
        """Generate thumbnail from video"""
        try:
            logger.info(f"Generating thumbnail at {timestamp}s")
            output_path. parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-ss", str(timestamp),
                "-vframes", "1",
                "-vf", f"scale={width}:{height}",
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Thumbnail generation failed:  {stderr}")

            logger.info(f"Thumbnail generated, output: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Thumbnail generation error:  {e}")
            raise

    async def convert_video_format(
        self,
        video_path: Path,
        output_format: str,
        output_path: Path,
        quality: str = "high",
    ) -> Path:
        """Convert video to different format"""
        try:
            logger. info(f"Converting video to {output_format}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Quality presets
            bitrate_map = {
                "low": "2000k",
                "medium": "5000k",
                "high":  "10000k",
                "very_high": "20000k",
            }

            bitrate = bitrate_map.get(quality, bitrate_map["high"])

            cmd = [
                self. ffmpeg_path,
                "-i", str(video_path),
                "-c:v", settings.VIDEO_CODEC,
                "-preset", settings.VIDEO_PRESET,
                "-b:v", bitrate,
                "-c:a", "aac",
                "-b:a", settings.AUDIO_BITRATE,
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Format conversion failed: {stderr}")

            logger.info(f"Video converted, output: {output_path}")
            return output_path

        except Exception as e:
            logger. error(f"Video conversion error: {e}")
            raise


# Global instance
ffmpeg_ops = FFmpegOps()