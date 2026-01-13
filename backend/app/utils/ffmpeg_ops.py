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

    async def mute_video(
        self,
        video_path: Path,
        output_path: Path,
    ) -> Path:
        """Mute video audio completely"""
        try:
            logger.info(f"Muting audio in {video_path}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-c:v", "copy",
                "-an",  # Remove audio stream
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Mute video failed: {stderr}")

            logger.info(f"Video muted, output: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Mute video error: {e}")
            raise

    async def convert_aspect_ratio(
        self,
        video_path: Path,
        target_ratio: str,
        output_path: Path,
        method: str = "pad",  # pad, crop, fit
        bg_color: str = "black",
    ) -> Path:
        """
        Convert video to target aspect ratio
        
        Supported ratios: 9:16, 16:9, 1:1, 4:5, 4:3
        Methods:
        - pad: Add black bars to maintain content
        - crop: Crop video to fill target ratio
        - fit: Scale video to fit within target ratio
        """
        try:
            logger.info(f"Converting aspect ratio to {target_ratio} using {method}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Get source video info
            video_info = await self.get_video_info(video_path)
            src_width = video_info["width"]
            src_height = video_info["height"]

            # Parse target ratio
            ratio_map = {
                "9:16": (1080, 1920),   # TikTok, Shorts, Reels
                "16:9": (1920, 1080),   # YouTube landscape
                "1:1": (1080, 1080),     # Instagram square
                "4:5": (1080, 1350),     # Instagram portrait
                "4:3": (1440, 1080),     # Traditional TV
            }

            if target_ratio not in ratio_map:
                raise FFmpegError(f"Unsupported aspect ratio: {target_ratio}")

            target_width, target_height = ratio_map[target_ratio]

            # Build filter based on method
            if method == "pad":
                # Scale to fit within target, then pad
                filter_complex = (
                    f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
                    f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color={bg_color}"
                )
            elif method == "crop":
                # Scale to cover target, then crop
                filter_complex = (
                    f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
                    f"crop={target_width}:{target_height}"
                )
            else:  # fit
                # Just scale to fit
                filter_complex = f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease"

            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-vf", filter_complex,
                "-c:v", settings.VIDEO_CODEC,
                "-preset", settings.VIDEO_PRESET,
                "-c:a", "aac",
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Aspect ratio conversion failed: {stderr}")

            logger.info(f"Aspect ratio converted, output: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Aspect ratio conversion error: {e}")
            raise

    async def merge_split_screen(
        self,
        video1_path: Path,
        video2_path: Path,
        output_path: Path,
        layout: str = "horizontal",  # horizontal, vertical
        ratio: str = "1:1",  # 1:1, 2:1, 1:2
        output_width: int = 1080,
        output_height: int = 1920,
        audio_source: str = "both",  # video1, video2, both, none
    ) -> Path:
        """
        Merge two videos into split screen
        
        Layout:
        - horizontal: Side by side (left-right)
        - vertical: Top-bottom
        
        Ratio options for horizontal: 1:1 (50-50), 2:1 (66-33), 1:2 (33-66)
        """
        try:
            logger.info(f"Merging videos with {layout} layout, ratio {ratio}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Parse ratio
            ratio_parts = ratio.split(":")
            ratio_left = int(ratio_parts[0])
            ratio_right = int(ratio_parts[1])
            total_ratio = ratio_left + ratio_right

            if layout == "horizontal":
                # Calculate widths based on ratio
                width1 = int(output_width * ratio_left / total_ratio)
                width2 = output_width - width1
                height1 = height2 = output_height

                # Scale and crop both videos, then hstack
                filter_complex = (
                    f"[0:v]scale={width1}:{height1}:force_original_aspect_ratio=increase,"
                    f"crop={width1}:{height1}[v0];"
                    f"[1:v]scale={width2}:{height2}:force_original_aspect_ratio=increase,"
                    f"crop={width2}:{height2}[v1];"
                    f"[v0][v1]hstack=inputs=2[outv]"
                )
            else:  # vertical
                # Calculate heights based on ratio
                height1 = int(output_height * ratio_left / total_ratio)
                height2 = output_height - height1
                width1 = width2 = output_width

                filter_complex = (
                    f"[0:v]scale={width1}:{height1}:force_original_aspect_ratio=increase,"
                    f"crop={width1}:{height1}[v0];"
                    f"[1:v]scale={width2}:{height2}:force_original_aspect_ratio=increase,"
                    f"crop={width2}:{height2}[v1];"
                    f"[v0][v1]vstack=inputs=2[outv]"
                )

            # Audio handling
            audio_filter = ""
            audio_mapping = []
            
            if audio_source == "video1":
                audio_mapping = ["-map", "0:a?"]
            elif audio_source == "video2":
                audio_mapping = ["-map", "1:a?"]
            elif audio_source == "both":
                # Mix both audio tracks
                filter_complex += ";[0:a][1:a]amix=inputs=2:duration=shortest[outa]"
                audio_mapping = ["-map", "[outa]"]
            # else: no audio

            cmd = [
                self.ffmpeg_path,
                "-i", str(video1_path),
                "-i", str(video2_path),
                "-filter_complex", filter_complex,
                "-map", "[outv]",
            ] + audio_mapping + [
                "-c:v", settings.VIDEO_CODEC,
                "-preset", settings.VIDEO_PRESET,
                "-c:a", "aac",
                "-shortest",
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Split screen merge failed: {stderr}")

            logger.info(f"Split screen merged, output: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Split screen merge error: {e}")
            raise

    async def extract_segments(
        self,
        video_path: Path,
        segments: list[dict],  # [{"start": 0, "end": 10}, {"start": 30, "end": 45}]
        output_dir: Path,
    ) -> list[Path]:
        """Extract multiple segments from video"""
        try:
            logger.info(f"Extracting {len(segments)} segments from video")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_paths = []
            for i, seg in enumerate(segments):
                start = seg.get("start", 0)
                end = seg.get("end", start + 10)
                
                output_path = output_dir / f"segment_{i:03d}.mp4"
                await self.cut_video(video_path, start, end, output_path)
                output_paths.append(output_path)

            logger.info(f"Extracted {len(output_paths)} segments")
            return output_paths

        except Exception as e:
            logger.error(f"Segment extraction error: {e}")
            raise

    async def add_watermark(
        self,
        video_path: Path,
        watermark_path: Path,
        output_path: Path,
        position: str = "bottom_right",  # top_left, top_right, bottom_left, bottom_right, center
        opacity: float = 0.7,
        scale: float = 0.15,  # Scale relative to video width
    ) -> Path:
        """Add image watermark to video"""
        try:
            logger.info(f"Adding watermark to video")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            video_info = await self.get_video_info(video_path)
            video_width = video_info["width"]
            video_height = video_info["height"]

            wm_width = int(video_width * scale)
            padding = 20

            # Position mapping
            pos_map = {
                "top_left": f"x={padding}:y={padding}",
                "top_right": f"x=W-w-{padding}:y={padding}",
                "bottom_left": f"x={padding}:y=H-h-{padding}",
                "bottom_right": f"x=W-w-{padding}:y=H-h-{padding}",
                "center": "x=(W-w)/2:y=(H-h)/2",
            }

            pos = pos_map.get(position, pos_map["bottom_right"])

            filter_complex = (
                f"[1:v]scale={wm_width}:-1,format=rgba,colorchannelmixer=aa={opacity}[wm];"
                f"[0:v][wm]overlay={pos}"
            )

            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-i", str(watermark_path),
                "-filter_complex", filter_complex,
                "-c:v", settings.VIDEO_CODEC,
                "-preset", settings.VIDEO_PRESET,
                "-c:a", "copy",
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Watermark failed: {stderr}")

            logger.info(f"Watermark added, output: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Watermark error: {e}")
            raise

    async def adjust_speed(
        self,
        video_path: Path,
        output_path: Path,
        speed: float = 1.0,  # 0.5 = slow, 2.0 = fast
    ) -> Path:
        """Adjust video and audio speed"""
        try:
            logger.info(f"Adjusting video speed to {speed}x")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if speed <= 0 or speed > 4:
                raise FFmpegError("Speed must be between 0.1 and 4.0")

            # Video speed adjustment
            video_filter = f"setpts={1/speed}*PTS"
            
            # Audio speed adjustment
            audio_filter = f"atempo={speed}" if 0.5 <= speed <= 2.0 else None
            
            # For speeds outside atempo range, we need to chain multiple atempo
            if speed > 2.0:
                audio_filter = f"atempo=2.0,atempo={speed/2.0}"
            elif speed < 0.5:
                audio_filter = f"atempo=0.5,atempo={speed/0.5}"

            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-filter:v", video_filter,
            ]
            
            if audio_filter:
                cmd.extend(["-filter:a", audio_filter])

            cmd.extend([
                "-c:v", settings.VIDEO_CODEC,
                "-preset", settings.VIDEO_PRESET,
                "-y",
                str(output_path),
            ])

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Speed adjustment failed: {stderr}")

            logger.info(f"Speed adjusted, output: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Speed adjustment error: {e}")
            raise


# Global instance
ffmpeg_ops = FFmpegOps()