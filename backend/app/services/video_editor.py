import shutil
import tempfile
from pathlib import Path
from typing import Any

from app.core.logger import logger

from app.utils.ffmpeg_ops import FFmpegOperations


class VideoEditor:
    """Edit videos based on AI instructions"""

    def __init__(self):
        self.ffmpeg = FFmpegOperations()
        self.ffmpeg_available = getattr(self.ffmpeg, "available", False)

    async def edit_video(
        self,
        input_path: str,
        instructions: dict[str, Any],
        output_path: str,
        platform: str,
    ) -> dict[str, Any]:
        """Edit video based on AI instructions"""
        logger.info(f"Editing video: {input_path} for {platform}")

        # If ffmpeg is missing, fallback by copying input to output (best-effort salvage)
        if not self.ffmpeg_available:
            try:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(input_path, output_path)

                logger.warning(
                    "FFmpeg not available - skipped editing and copied input to output to avoid failing job"
                )

                result = {
                    "output_path": output_path,
                    "thumbnail_path": None,
                    "duration": await self._get_duration(output_path),
                    "resolution": await self._get_resolution(output_path),
                    "file_size": Path(output_path).stat().st_size
                    if Path(output_path).exists()
                    else 0,
                    "clips_used": 0,
                    "skipped_editing": True,
                }

                return result
            except Exception as e:
                logger.error(f"Fallback copy failed: {e}")
                raise Exception(f"Video editing failed: {str(e)}")

        try:
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Step 1: Extract clips based on instructions
                clips = await self._extract_clips(input_path, instructions, temp_path)

                # Step 2: Apply effects to clips
                processed_clips = await self._process_clips(clips, instructions, temp_path)

                # Step 3: Concatenate clips
                final_video = await self._concatenate_clips(
                    processed_clips, instructions, temp_path
                )

                # Step 4: Apply final processing
                await self._apply_final_processing(final_video, output_path, instructions, platform)

                # Step 5: Generate thumbnail
                thumbnail_path = await self._generate_thumbnail(output_path, temp_path)

                result = {
                    "output_path": output_path,
                    "thumbnail_path": thumbnail_path,
                    "duration": await self._get_duration(output_path),
                    "resolution": await self._get_resolution(output_path),
                    "file_size": Path(output_path).stat().st_size,
                    "clips_used": len(clips),
                }

                logger.info(f"Video editing completed: {output_path}")
                return result

        except Exception as e:
            if "FFmpeg" in str(e) or "ffmpeg" in str(e).lower() or "not available" in str(e):
                logger.warning(f"FFmpeg related error ({e}); attempting fallback copy")
                try:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(input_path, output_path)
                    return {
                        "output_path": output_path,
                        "thumbnail_path": None,
                        "duration": await self._get_duration(output_path),
                        "resolution": await self._get_resolution(output_path),
                        "file_size": Path(output_path).stat().st_size
                        if Path(output_path).exists()
                        else 0,
                        "clips_used": 0,
                        "skipped_editing": True,
                    }
                except Exception as e2:
                    logger.error(f"Fallback copy also failed: {e2}")
                    raise Exception(f"Video editing failed: {str(e2)}")

            logger.error(f"Video editing failed: {e}")
            raise Exception(f"Video editing failed: {str(e)}")

    async def _extract_clips(
        self, input_path: str, instructions: dict[str, Any], temp_dir: Path
    ) -> list[dict[str, Any]]:
        """Extract clips from original video"""
        clips = []

        for i, clip_info in enumerate(instructions.get("clips", [])):
            start_time = clip_info.get("start_time", 0)
            end_time = clip_info.get("end_time", 0)
            action = clip_info.get("action", "keep")

            if action == "cut":
                continue  # Skip this clip

            clip_path = temp_dir / f"clip_{i:03d}.mp4"

            # Extract clip
            await self.ffmpeg.extract_clip(
                input_path=input_path,
                output_path=str(clip_path),
                start_time=start_time,
                end_time=end_time,
            )

            clips.append(
                {
                    "path": str(clip_path),
                    "index": i,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": end_time - start_time,
                    "action": action,
                    "info": clip_info,
                }
            )

        return clips

    async def _process_clips(
        self, clips: list[dict[str, Any]], instructions: dict[str, Any], temp_dir: Path
    ) -> list[dict[str, Any]]:
        """Process individual clips with effects"""
        processed_clips = []

        for clip in clips:
            clip_info = clip["info"]
            input_path = clip["path"]
            output_path = temp_dir / f"processed_{clip['index']:03d}.mp4"

            # Build FFmpeg filter chain
            filter_chain = []

            # Apply speed change
            if clip_info.get("speed_factor", 1.0) != 1.0:
                speed = clip_info["speed_factor"]
                filter_chain.append(f"setpts={1 / speed}*PTS")
                # Note: Need separate audio filter for speed

            # Apply text overlay
            # Subtitle text may come from clip_info or global instructions
            subtitle_text = clip_info.get("subtitle_text") or instructions.get("subtitle_text")
            if clip_info.get("text_overlay"):
                text_info = clip_info.get("text_overlay")
                subtitle_text = text_info.get("text", subtitle_text)

            if subtitle_text:
                text = subtitle_text.replace("'", "''")[:800]
                pos = "x=(w-text_w)/2:y=h-text_h-50"
                filter_chain.append(
                    f"drawtext=text='{text}':fontsize=36:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=5:{pos}"
                )

            # Apply watermark removal (best-effort): draw box over common watermark area
            if "watermark_removal" in clip_info.get("effects", []) or instructions.get(
                "platform_specific_settings", {}
            ).get("watermark_removal"):
                # Draw a semi-opaque box in top-right corner (best-effort)
                filter_chain.append("drawbox=x=main_w-220:y=10:w=200:h=60:color=black@0.6:t=fill")

            # Apply zoom effect
            if "zoom_in" in clip_info.get("effects", []):
                filter_chain.append("zoompan=z='min(zoom+0.0015,1.5)':d=1")

            # Apply color filter
            if "color_filter" in clip_info.get("effects", []):
                filter_chain.append(
                    "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131"
                )

            # Determine audio filters if we need to mute/change music
            audio_filters = None
            if clip_info.get("mute_audio"):
                audio_filters = "volume=0.0"

            # Process clip with filters
            if filter_chain or audio_filters:
                logger.info(
                    f"Applying filters: {','.join(filter_chain) if filter_chain else '<none>'} audio_filters: {audio_filters}"
                )
                await self.ffmpeg.apply_filters(
                    input_path=input_path,
                    output_path=str(output_path),
                    filters=",".join(filter_chain) if filter_chain else None,
                    audio_filters=audio_filters,
                )
                clip["path"] = str(output_path)

            processed_clips.append(clip)

        return processed_clips

    async def _concatenate_clips(
        self, clips: list[dict[str, Any]], instructions: dict[str, Any], temp_dir: Path
    ) -> str:
        """Concatenate processed clips"""
        if len(clips) == 1:
            return clips[0]["path"]

        # Create concat file
        concat_file = temp_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for clip in clips:
                f.write(f"file '{clip['path']}'\n")

        output_path = temp_dir / "concatenated.mp4"

        await self.ffmpeg.concatenate_videos(
            concat_file=str(concat_file), output_path=str(output_path)
        )

        return str(output_path)

    async def _apply_final_processing(
        self,
        input_path: str,
        output_path: str,
        instructions: dict[str, Any],
        platform: str,
    ):
        """Apply final processing to video"""
        # Get platform-specific settings
        platform_settings = instructions.get("platform_specific_settings", {})
        aspect_ratio = platform_settings.get("aspect_ratio", "9:16")
        target_resolution = platform_settings.get("target_resolution", "1080x1920")

        # Build processing chain
        filters = []

        # Scale to target resolution
        if aspect_ratio == "9:16":
            filters.append(f"scale={target_resolution}")
        elif aspect_ratio == "16:9":
            filters.append(f"scale={target_resolution}")

        # Add watermark removal if needed
        if platform_settings.get("watermark_removal", False):
            # This would require more sophisticated watermark detection
            pass

        # Normalize audio
        if platform_settings.get("audio_normalization", False):
            filters.append("loudnorm=I=-16:LRA=11:TP=-1.5")

        # Apply filters if any
        if filters:
            await self.ffmpeg.apply_filters(
                input_path=input_path,
                output_path=output_path,
                filters=",".join(filters),
            )
        else:
            # Just copy if no filters
            shutil.copy2(input_path, output_path)

    async def _generate_thumbnail(self, video_path: str, temp_dir: Path) -> str | None:
        """Generate thumbnail from video"""
        try:
            thumbnail_path = temp_dir / "thumbnail.jpg"

            # Extract frame at 25% of video
            await self.ffmpeg.extract_frame(
                input_path=video_path,
                output_path=str(thumbnail_path),
                time_offset="25%",
            )

            return str(thumbnail_path)
        except Exception as e:
            logger.warning(f"Thumbnail generation failed: {e}")
            return None

    async def _get_duration(self, video_path: str) -> float:
        """Get video duration"""
        try:
            result = await self.ffmpeg.get_video_info(video_path)
            return float(result.get("duration", 0))
        except:
            return 0

    async def _get_resolution(self, video_path: str) -> str:
        """Get video resolution"""
        try:
            result = await self.ffmpeg.get_video_info(video_path)
            width = result.get("width", 0)
            height = result.get("height", 0)
            return f"{width}x{height}"
        except:
            return "0x0"
