"""
Video Merger Service
Handles split-screen and video merging operations
"""

import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from app.core.logger import logger
from app.core.config import settings
from app.utils.ffmpeg_ops import ffmpeg_ops
from app.services.video_downloader import VideoDownloader


class VideoMerger:
    """Service for merging multiple videos"""
    
    def __init__(self):
        self.downloader = VideoDownloader()
    
    async def merge_split_screen(
        self,
        video1_url: str,
        video2_url: str,
        layout: str = "horizontal",  # horizontal, vertical
        ratio: str = "1:1",
        output_ratio: str = "9:16",
        audio_source: str = "both",
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Download two videos and merge them into split screen
        
        Args:
            video1_url: URL of first video (left/top)
            video2_url: URL of second video (right/bottom)
            layout: horizontal (side by side) or vertical (top-bottom)
            ratio: Split ratio - "1:1", "2:1", "1:2"
            output_ratio: Output aspect ratio - "9:16", "16:9", "1:1"
            audio_source: Which audio to use - "video1", "video2", "both", "none"
        """
        job_id = str(uuid.uuid4())[:8]
        temp_dir = Path(settings.TEMP_DIR) / f"merge_{job_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Starting split-screen merge job {job_id}")
            
            # Download videos
            logger.info("Downloading video 1...")
            video1_path = await self.downloader.download(video1_url, temp_dir)
            
            logger.info("Downloading video 2...")
            video2_path = await self.downloader.download(video2_url, temp_dir)
            
            # Determine output dimensions based on ratio
            ratio_dimensions = {
                "9:16": (1080, 1920),
                "16:9": (1920, 1080),
                "1:1": (1080, 1080),
                "4:5": (1080, 1350),
            }
            
            output_width, output_height = ratio_dimensions.get(output_ratio, (1080, 1920))
            
            # Merge videos
            output_path = output_path or Path(settings.PROCESSED_DIR) / f"merged_{job_id}.mp4"
            
            logger.info(f"Merging videos with {layout} layout...")
            result_path = await ffmpeg_ops.merge_split_screen(
                video1_path=video1_path,
                video2_path=video2_path,
                output_path=output_path,
                layout=layout,
                ratio=ratio,
                output_width=output_width,
                output_height=output_height,
                audio_source=audio_source
            )
            
            # Get video info
            video_info = await ffmpeg_ops.get_video_info(result_path)
            
            # Cleanup temp files
            try:
                video1_path.unlink()
                video2_path.unlink()
                temp_dir.rmdir()
            except:
                pass
            
            logger.info(f"Split-screen merge completed: {result_path}")
            
            return {
                "success": True,
                "job_id": job_id,
                "output_path": str(result_path),
                "output_url": f"/api/videos/merged/{job_id}",
                "duration": video_info.get("duration", 0),
                "width": video_info.get("width", output_width),
                "height": video_info.get("height", output_height),
                "layout": layout,
                "ratio": ratio,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Split-screen merge error: {e}")
            return {
                "success": False,
                "job_id": job_id,
                "output_path": None,
                "error": str(e)
            }
    
    async def merge_videos_sequential(
        self,
        video_urls: list[str],
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Download and concatenate multiple videos sequentially
        """
        job_id = str(uuid.uuid4())[:8]
        temp_dir = Path(settings.TEMP_DIR) / f"concat_{job_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Starting sequential merge job {job_id} with {len(video_urls)} videos")
            
            # Download all videos
            video_paths = []
            for i, url in enumerate(video_urls):
                logger.info(f"Downloading video {i+1}/{len(video_urls)}...")
                path = await self.downloader.download(url, temp_dir)
                video_paths.append(path)
            
            # Concatenate
            output_path = output_path or Path(settings.PROCESSED_DIR) / f"concat_{job_id}.mp4"
            
            logger.info("Concatenating videos...")
            result_path = await ffmpeg_ops.concatenate_videos(video_paths, output_path)
            
            # Get video info
            video_info = await ffmpeg_ops.get_video_info(result_path)
            
            # Cleanup
            for path in video_paths:
                try:
                    path.unlink()
                except:
                    pass
            try:
                temp_dir.rmdir()
            except:
                pass
            
            return {
                "success": True,
                "job_id": job_id,
                "output_path": str(result_path),
                "output_url": f"/api/videos/concat/{job_id}",
                "duration": video_info.get("duration", 0),
                "num_videos": len(video_urls),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Sequential merge error: {e}")
            return {
                "success": False,
                "job_id": job_id,
                "output_path": None,
                "error": str(e)
            }


# Global instance
video_merger = VideoMerger()
