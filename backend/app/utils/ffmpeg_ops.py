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
        # Get from settings, with fallback to backend directory
        ffmpeg_path = settings.FFMPEG_PATH
        ffprobe_path = settings.FFPROBE_PATH
        
        # If settings have simple 'ffmpeg' or 'ffprobe', look for exe in backend dir
        backend_dir = Path(__file__).resolve().parents[2]
        
        if ffmpeg_path == "ffmpeg" or not Path(ffmpeg_path).exists():
            local_ffmpeg = backend_dir / "ffmpeg.exe"
            if local_ffmpeg.exists():
                ffmpeg_path = str(local_ffmpeg)
                
        if ffprobe_path == "ffprobe" or not Path(ffprobe_path).exists():
            local_ffprobe = backend_dir / "ffprobe.exe"
            if local_ffprobe.exists():
                ffprobe_path = str(local_ffprobe)
        
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        logger.info(f"FFmpegOps initialized: ffmpeg={self.ffmpeg_path}, ffprobe={self.ffprobe_path}")

    async def _run_command(self, cmd: list[str], timeout: int = 600) -> Tuple[int, str, str]:
        """Run FFmpeg command - using subprocess.run for better Windows compatibility"""
        import subprocess
        try:
            logger.info(f"Running FFmpeg command: {cmd[0]} ... (timeout={timeout}s)")
            logger.debug(f"Full command: {' '.join(cmd)}")
            
            # Use Popen with proper pipe handling to prevent buffer overflow
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,  # Discard stderr to prevent buffer overflow
                    timeout=timeout,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                )
            )
            stdout = result.stdout.decode('utf-8', errors='ignore') if result.stdout else ""
            logger.info(f"FFmpeg command completed with code {result.returncode}")
            return result.returncode, stdout, ""
        except subprocess.TimeoutExpired as e:
            logger.error(f"FFmpeg command timed out after {timeout}s")
            raise FFmpegError(f"FFmpeg command timed out after {timeout}s")
        except Exception as e:
            logger.error(f"FFmpeg command failed: {str(e)}")
            raise FFmpegError(f"Failed to run command: {str(e)}")

    async def get_video_info(self, video_path: Path) -> dict[str, Any]:
        """Get video information using ffprobe"""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "format=duration,size:stream=width,height,r_frame_rate,codec_name",
                "-of", "json",
                str(video_path),
            ]
            
            logger.info(f"Running ffprobe: {' '.join(cmd)}")

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                logger.error(f"ffprobe failed with code {returncode}: {stderr}")
                raise FFmpegError(f"ffprobe error: {stderr}")

            if not stdout.strip():
                logger.error("ffprobe returned empty output")
                raise FFmpegError("ffprobe returned empty output")

            data = json.loads(stdout)
            
            format_info = data.get("format", {})
            stream_info = data.get("streams", [{}])[0]
            
            # Parse framerate
            fps_str = stream_info.get("r_frame_rate", "30/1")
            fps_parts = fps_str.split("/")
            fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

            result = {
                "duration": float(format_info.get("duration", 0)),
                "size": int(format_info.get("size", 0)),
                "width": int(stream_info.get("width", 1920)),
                "height": int(stream_info.get("height", 1080)),
                "fps": fps,
                "codec": stream_info.get("codec_name", "h264"),
            }
            logger.info(f"Video info: {result}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ffprobe JSON output: {e}, stdout: {stdout[:500]}")
            raise FFmpegError(f"Failed to parse ffprobe output: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
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
        loop_audio: bool = False,
        mix_with_original: bool = False,  # Changed: Mute original audio by default
    ) -> Path:
        """Replace or mix audio in video. Keeps original video duration."""
        try:
            logger.info(f"Replacing audio in {video_path} with {audio_path}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Validate audio file exists and has content
            if not audio_path.exists():
                logger.error(f"Audio file not found: {audio_path}")
                raise FFmpegError(f"Audio file not found: {audio_path}")
            
            audio_size = audio_path.stat().st_size
            if audio_size < 1000:  # Less than 1KB is likely invalid
                logger.error(f"Audio file too small: {audio_size} bytes")
                raise FFmpegError(f"Audio file appears invalid: {audio_size} bytes")
            
            logger.info(f"Audio file validated: {audio_path} ({audio_size} bytes)")

            # Check if source video has audio stream
            has_audio = await self._check_has_audio(video_path)
            logger.info(f"Source video has audio: {has_audio}")

            if mix_with_original and has_audio:
                # Mix new audio with original (original at 20% volume)
                cmd = [
                    self.ffmpeg_path,
                    "-i", str(video_path),
                    "-i", str(audio_path),
                    "-filter_complex", 
                    "[0:a]volume=0.2[orig];[1:a]volume=1.0[new];[orig][new]amix=inputs=2:duration=first[aout]",
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-y",
                    str(output_path),
                ]
            else:
                # Replace audio entirely (or source has no audio)
                # This is the simpler and more reliable approach
                cmd = [
                    self.ffmpeg_path,
                    "-i", str(video_path),
                    "-i", str(audio_path),
                    "-map", "0:v",      # Take video from first input
                    "-map", "1:a",      # Take audio from second input
                    "-c:v", "copy",     # Copy video codec (fast)
                    "-c:a", "aac",      # Convert audio to AAC
                    # "-shortest",      # REMOVED: Prevent cutting video short
                    "-y",
                    str(output_path),
                ]

            logger.info(f"Running audio replace command...")
            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                logger.error(f"Audio replacement failed with code {returncode}")
                # Fallback: Try simpler command without mixing
                if mix_with_original:
                    logger.info("Retrying without audio mixing...")
                    cmd_simple = [
                        self.ffmpeg_path,
                        "-i", str(video_path),
                        "-i", str(audio_path),
                        "-map", "0:v",
                        "-map", "1:a",
                        "-c:v", "copy",
                        "-c:a", "aac",
                        # "-shortest",  # REMOVED
                        "-y",
                        str(output_path),
                    ]
                    returncode, stdout, stderr = await self._run_command(cmd_simple)
                    
                    if returncode != 0:
                        logger.warning("Simple audio replace also failed, copying video as-is")
                        import shutil
                        shutil.copy(str(video_path), str(output_path))
                        return output_path
                else:
                    logger.warning("Falling back to simple video copy...")
                    import shutil
                    shutil.copy(str(video_path), str(output_path))
                    return output_path

            # Validate output
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Audio replaced successfully, output: {output_path}")
            else:
                logger.warning(f"Output file missing or empty, copying original")
                import shutil
                shutil.copy(str(video_path), str(output_path))
                
            return output_path

        except Exception as e:
            logger.error(f"Audio replacement error: {e}")
            # Last resort fallback
            try:
                import shutil
                shutil.copy(str(video_path), str(output_path))
                logger.info(f"Fallback: copied original video to {output_path}")
                return output_path
            except:
                raise

    async def add_background_music(
        self,
        voice_path: Path,
        bgm_path: Path,
        output_path: Path,
        bgm_volume: float = 0.15,
        voice_volume: float = 1.0,
    ) -> Path:
        """Mix voice narration with background music"""
        try:
            logger.info(f"Mixing BGM {bgm_path} with voice {voice_path}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build filter complex to loop BGM and mix
            # [1:a]aloop=loop=-1:size=2e9 [bgm]; loops BGM
            # [0:a]volume=1.0[v]; voice
            # [bgm]volume=0.15[bgmv]; bgm volume
            # [v][bgmv]amix=inputs=2:duration=first[out]
            
            filter_complex = (
                f"[1:a]aloop=loop=-1:size=2e9,volume={bgm_volume}[bgm];"
                f"[0:a]volume={voice_volume}[v];"
                f"[v][bgm]amix=inputs=2:duration=first:dropout_transition=3[out]"
            )

            cmd = [
                self.ffmpeg_path,
                "-i", str(voice_path),
                "-i", str(bgm_path),
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-c:a", "aac",
                "-b:a", "192k",
                "-y",
                str(output_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            if returncode != 0:
                logger.warning(f"BGM mixing failed, returning original voice: {stderr}")
                import shutil
                shutil.copy(str(voice_path), str(output_path))
                return output_path

            return output_path
        except Exception as e:
            logger.error(f"Error mixing BGM: {e}")
            return voice_path

    async def normalize_audio(self, audio_path: Path, output_path: Path) -> Path:
        """Normalize audio to professional standards (Loudnorm)"""
        try:
            logger.info(f"Normalizing audio: {audio_path}")
            cmd = [
                self.ffmpeg_path,
                "-i", str(audio_path),
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-c:a", "aac",
                "-b:a", "192k",
                "-y",
                str(output_path),
            ]
            returncode, stdout, stderr = await self._run_command(cmd)
            return output_path if returncode == 0 else audio_path
        except:
            return audio_path

    async def _check_has_audio(self, video_path: Path) -> bool:
        """Check if video has audio stream"""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=codec_type",
                "-of", "json",
                str(video_path),
            ]
            returncode, stdout, stderr = await self._run_command(cmd)
            if returncode == 0 and stdout.strip():
                data = json.loads(stdout)
                return len(data.get("streams", [])) > 0
            return False
        except:
            return False

    async def add_text_overlay(
        self,
        video_path: Path,
        text_segments: list[dict],  # [{"start": 0, "end": 5, "text": "Hello", "style": {... }}]
        output_path: Path,
        font_path: Optional[Path] = None,
        font_size: int = 70,
        font_color: str = "yellow",
        bg_color: str = "black",
        bg_alpha: float = 0.5,
        position: str = "center",  # top, center, bottom
    ) -> Path:
        """Add text overlay to video with timing and advanced styling"""
        try:
            logger. info(f"Adding advanced text overlay to {video_path}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Fallback font discovery if not provided
            if not font_path:
                # Use same discovery as before but simplified for readability
                font_path = Path("C:/Windows/Fonts/arialbd.ttf") if Path("C:/Windows/Fonts/arialbd.ttf").exists() else None
            
            # Get video info for positioning
            video_info = await self.get_video_info(video_path)
            width = video_info["width"]
            height = video_info["height"]

            # Build filter complex
            filters = []
            
            for i, seg in enumerate(text_segments):
                start = seg. get("start", 0)
                end = seg.get("end", 1.0)
                raw_text = seg.get("text", "").strip()
                if not raw_text: continue
                
                # Dynamic captions for Shorts are often UPPERCASE
                text = raw_text.upper().replace("'", "\\'").replace('"', '\\"').replace(":", "\\:")
                
                # Use segment-specific style if exists, else defaults
                s = seg.get("style", {})
                f_size = s.get("font_size", font_size)
                f_color = s.get("font_color", font_color)
                b_color = s.get("bg_color", bg_color)
                b_alpha = s.get("bg_alpha", bg_alpha)
                pos = s.get("position", position)
                
                # Position calculation
                if pos == "top": 
                    y_pos = int(height * 0.15)
                elif pos == "center":
                    y_pos = int((height - f_size) / 2)
                else:  # bottom
                    y_pos = int(height - f_size - 100)
                
                # Center horizontally
                # Rough estimate of text width: chars * size * factor
                text_width_est = len(text) * f_size * 0.55
                x_pos = int((width - text_width_est) / 2)

                # Font path handling
                font_path_str = str(font_path).replace('\\', '/') if font_path else ""
                font_arg = f": fontfile='{font_path_str}'" if font_path else ""
                
                # Style components: Box background
                box_arg = f": box=1: boxcolor={b_color}@{b_alpha}: boxborderw=10" if b_alpha > 0 else ""
                
                # Shadow & Border (adds "premium" feel)
                border_arg = f": borderw=3: bordercolor=black"
                shadow_arg = f": shadowx=3: shadowy=3: shadowcolor=black"
                
                # Create text filter with timing
                text_filter = (
                    f"drawtext=text='{text}': fontsize={f_size}: fontcolor={f_color}: "
                    f"x={x_pos}: y={y_pos}: enable='between(t,{start},{end})'"
                    f"{font_arg}{box_arg}{border_arg}{shadow_arg}"
                )
                
                filters.append(text_filter)

            # Combine all filters
            if not filters:
                import shutil
                shutil.copy(str(video_path), str(output_path))
                return output_path

            # FFmpeg can handle hundreds of filters but it might be long
            # If too many filters, we might need a filter_script file
            filter_complex = ",".join(filters)

            # Build command
            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-vf", filter_complex,
                "-c:a", "copy", # Keep audio as is
                "-c:v", settings.VIDEO_CODEC,
                "-preset", "veryfast", # Speed over compression for previews
                "-y",
                str(output_path)
            ]

            returncode, stdout, stderr = await self._run_command(cmd)
            
            if returncode != 0:
                raise FFmpegError(f"Advanced text overlay failed: {stderr}")

            return output_path

        except Exception as e:
            logger. error(f"Advanced text overlay error:  {e}")
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
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-c:v", settings.VIDEO_CODEC,
                "-preset", settings.VIDEO_PRESET,
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