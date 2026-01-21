"""
Main Video Editor Service - Orchestrates all video processing
"""

from pathlib import Path
from typing import Optional, Any, Tuple
from app.core.logger import logger
from app.core.config import settings
from app.utils.ffmpeg_ops import ffmpeg_ops, FFmpegError
from app. services.audio_processor import audio_processor
from app.services. text_overlay_engine import text_overlay_engine, TextStyle


class VideoEditor:
    """Main video editor service"""

    async def process_video_for_reup(
        self,
        video_path: Path,
        target_duration: int = 60,
        target_platform: str = "tiktok",
        add_text: bool = True,
        text_segments: Optional[list[dict]] = None,
        new_audio_path: Optional[Path] = None,
        output_path: Optional[Path] = None,
        bgm_style: str = "cheerful",
        normalize_audio: bool = True,
    ) -> dict[str, Any]:
        """
        Process video for reupload with AI narration and text

        Args:
            video_path: Source video path
            target_duration:   Target duration in seconds
            target_platform: Target platform (tiktok, youtube, etc.)
            add_text: Whether to add text overlay
            text_segments: Text segments with timing
            new_audio_path:   New AI narration audio path
            output_path: Output video path
            bgm_style: Style of background music to add (e.g., "cheerful", "epic")
            normalize_audio: Whether to normalize the new audio
        Returns:
            Processing result with metadata
        """
        try:
            logger.info(f"Processing video for {target_platform} reup")
            output_path = output_path or Path(settings.PROCESSED_DIR) / f"reup_{video_path.stem}.mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Get video info
            logger.info("Step 1: Getting video info...")
            video_info = await ffmpeg_ops.get_video_info(video_path)
            logger.info(f"Video info: {video_info}")

            # Resize if needed based on platform
            logger.info(f"Step 2: Resizing for platform {target_platform}...")
            resized_video = await self._resize_for_platform(video_path, target_platform)
            logger.info(f"Resized video: {resized_video}")

            # Replace audio if provided
            if new_audio_path:
                logger.info("Step 3: Processing audio with AI narration...")
                
                # Step 3a: Normalize Narration
                normalized_narration = Path(settings.TEMP_DIR) / f"norm_{new_audio_path.name}"
                new_audio_path = await ffmpeg_ops.normalize_audio(new_audio_path, normalized_narration)
                
                # Step 3b: Add Background Music if requested
                bgm_path = Path("data/bgm") / f"{bgm_style}.mp3"
                
                if bgm_path.exists():
                    logger.info(f"Adding background music: {bgm_style}")
                    mixed_audio = Path(settings.TEMP_DIR) / f"mixed_{new_audio_path.name}"
                    new_audio_path = await ffmpeg_ops.add_background_music(
                        new_audio_path, 
                        bgm_path, 
                        mixed_audio,
                        bgm_volume=0.15
                    )

                video_with_audio = await ffmpeg_ops.replace_audio(
                    resized_video,
                    new_audio_path,
                    Path(settings.TEMP_DIR) / f"with_audio_{video_path.stem}.mp4",
                )
                logger.info(f"Audio replaced: {video_with_audio}")
            else:
                video_with_audio = resized_video
                logger.info("Step 3: No audio replacement needed")

            # Add text overlay if provided
            if add_text and text_segments:
                logger.info(f"Step 4: Adding {len(text_segments)} text segments...")
                final_video = await text_overlay_engine.add_styled_text(
                    video_with_audio,
                    text_segments,
                    output_path,
                )
                logger.info(f"Text added: {final_video}")
            else:
                final_video = video_with_audio
                if final_video != output_path:
                    import shutil
                    shutil.copy(str(final_video), str(output_path))
                    logger.info(f"Copied to output: {output_path}")
                else:
                    logger.info("Step 4: No text overlay needed")

            # Generate thumbnail
            logger.info("Step 5: Generating thumbnail...")
            thumbnail_path = await ffmpeg_ops.generate_thumbnail(
                output_path,
                timestamp=0,
                output_path=Path(settings.PROCESSED_DIR) / f"{output_path.stem}_thumb.jpg",
            )
            logger.info(f"Thumbnail generated: {thumbnail_path}")

            return {
                "success": True,
                "output_path": str(output_path),
                "thumbnail_path": str(thumbnail_path),
                "duration": video_info["duration"],
                "platform": target_platform,
            }

        except Exception as e:
            logger.error(f"Video processing error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_video_info(self, video_path: Path) -> dict[str, Any]:
        """Get video information using ffmpeg_ops"""
        return await ffmpeg_ops.get_video_info(video_path)

    async def cut_video(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        output_path: Path,
    ) -> Path:
        """Cut a single segment from video"""
        return await ffmpeg_ops.cut_video(video_path, start_time, end_time, output_path)

    async def cut_and_merge_video(
        self,
        video_path: Path,
        cut_points: list[Tuple[float, float]],
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Cut video at specified points and merge back

        Args:
            video_path: Source video path
            cut_points: List of (start, end) tuples in seconds
            output_path: Output video path

        Returns:
            Output video path
        """
        try:
            output_path = output_path or Path(settings.PROCESSED_DIR) / f"cut_{video_path.stem}.mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Cutting and merging video at {len(cut_points)} points")

            # Cut segments
            cut_videos = []
            for i, (start, end) in enumerate(cut_points):
                cut_path = Path(settings.TEMP_DIR) / f"cut_{i}_{video_path.stem}. mp4"
                cut_video = await ffmpeg_ops.cut_video(video_path, start, end, cut_path)
                cut_videos.append(cut_video)

            # Merge segments
            if len(cut_videos) == 1:
                import shutil
                shutil.copy(str(cut_videos[0]), str(output_path))
            else:
                await ffmpeg_ops.concatenate_videos(cut_videos, output_path)

            # Cleanup temp files
            for cv in cut_videos:
                cv.unlink(missing_ok=True)

            logger.info(f"Cut and merge completed:   {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Cut and merge error:  {e}")
            raise

    async def _resize_for_platform(self, video_path: Path, platform: str) -> Path:
        """Resize video for specific platform - skip if already correct aspect ratio"""
        # Platform aspect ratios
        platform_sizes = {
            "tiktok": (1080, 1920),      # 9:16
            "youtube": (1920, 1080),      # 16:9
            "instagram": (1080, 1080),    # 1:1
            "facebook": (1200, 630),      # Landscape
            "douyin": (1080, 1920),       # 9:16
            "twitter": (1200, 675),       # 16:9
        }

        target_size = platform_sizes.get(platform, (1920, 1080))

        # Check if resize needed
        video_info = await ffmpeg_ops.get_video_info(video_path)
        current_width = video_info["width"]
        current_height = video_info["height"]
        
        # Calculate aspect ratios
        current_ratio = current_width / current_height if current_height > 0 else 1
        target_ratio = target_size[0] / target_size[1]
        
        # Skip resize if:
        # 1. Already exact match
        # 2. Already correct aspect ratio (within 5% tolerance)
        if (current_width == target_size[0] and current_height == target_size[1]):
            logger.info(f"Video already at target size {target_size}, skipping resize")
            return video_path
            
        if abs(current_ratio - target_ratio) < 0.05:
            logger.info(f"Video already has correct aspect ratio ({current_ratio:.2f} ≈ {target_ratio:.2f}), skipping resize")
            return video_path

        logger.info(f"Resizing video from {current_width}x{current_height} to {target_size} for {platform}")
        resized_path = Path(settings.TEMP_DIR) / f"resized_{video_path.stem}.mp4"

        return await ffmpeg_ops.resize_video(
            video_path,
            target_size[0],
            target_size[1],
            resized_path,
        )

    async def generate_story_video(
        self,
        base_video_path: Path,
        story_text: str,
        audio_path: Path,
        output_path: Optional[Path] = None,
        bgm_style: str = "cheerful",
        normalize_audio: bool = True,
    ) -> Path:
        """
        Generate story-based video with narration
        """
        try:
            output_path = output_path or Path(settings.PROCESSED_DIR) / f"story_{base_video_path.stem}. mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info("Generating story video")

            # Split story into subtitle segments
            segments = self._create_subtitle_segments(story_text)

            # Create subtitle file
            subtitle_path = await text_overlay_engine.generate_subtitle_file(
                segments,
                Path(settings.TEMP_DIR) / f"subtitles_{base_video_path.stem}.srt",
                format="srt",
            )

            # Process video with audio and text
            result = await self.process_video_for_reup(
                base_video_path,
                add_text=True,
                text_segments=segments,
                new_audio_path=audio_path,
                output_path=output_path,
                bgm_style=bgm_style,
                normalize_audio=normalize_audio,
            )

            return output_path if result["success"] else None

        except Exception as e:
            logger.error(f"Story video generation error: {e}")
            raise

    def _create_subtitle_segments(self, text: str, words_per_second: float = 2.5) -> list[dict]:
        """Create subtitle segments from text"""
        words = text.split()
        duration_per_word = 1.0 / words_per_second

        segments = []
        current_time = 0
        i = 0

        # Group words into logical segments (e.g., sentences or phrases)
        while i < len(words):
            # Find sentence end - use 2-3 words for high energy Shorts
            j = min(i + 2, len(words)) 
            segment_text = " ".join(words[i:j])

            start = current_time
            end = current_time + (j - i) * duration_per_word

            segments.append({
                "start": start,
                "end": end,
                "text":  segment_text,
                "style": {
                    "font_size": 60,
                    "font_color": "FFFFFF",
                    "bg_color": "000000",
                    "position": "bottom",
                },
            })

            current_time = end
            i = j

        return segments


video_editor = VideoEditor()