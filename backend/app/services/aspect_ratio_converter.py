"""
Aspect Ratio Converter Service
Converts videos to different aspect ratios for various platforms
"""

import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from app.core.logger import logger
from app.core.config import settings
from app.utils.ffmpeg_ops import ffmpeg_ops
from app.services.video_downloader import VideoDownloader


# Platform aspect ratio recommendations
PLATFORM_RATIOS = {
    "tiktok": {"primary": "9:16", "alternatives": ["1:1"]},
    "youtube_shorts": {"primary": "9:16", "alternatives": ["1:1"]},
    "youtube": {"primary": "16:9", "alternatives": ["1:1", "4:3"]},
    "instagram_reels": {"primary": "9:16", "alternatives": ["1:1", "4:5"]},
    "instagram_feed": {"primary": "1:1", "alternatives": ["4:5", "16:9"]},
    "instagram_story": {"primary": "9:16", "alternatives": []},
    "facebook": {"primary": "16:9", "alternatives": ["1:1", "9:16", "4:5"]},
    "twitter": {"primary": "16:9", "alternatives": ["1:1"]},
}

RATIO_DIMENSIONS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "4:3": (1440, 1080),
}


class AspectRatioConverter:
    """Convert videos to different aspect ratios"""
    
    def __init__(self):
        self.downloader = VideoDownloader()
    
    def get_platform_ratio(self, platform: str) -> str:
        """Get recommended aspect ratio for platform"""
        platform_lower = platform.lower().replace(" ", "_")
        if platform_lower in PLATFORM_RATIOS:
            return PLATFORM_RATIOS[platform_lower]["primary"]
        return "9:16"  # Default to vertical
    
    def get_ratio_dimensions(self, ratio: str) -> tuple[int, int]:
        """Get width, height for aspect ratio"""
        return RATIO_DIMENSIONS.get(ratio, (1080, 1920))
    
    async def convert(
        self,
        source_url: str,
        target_ratio: str,
        method: str = "pad",  # pad, crop, fit
        bg_color: str = "000000",
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Convert video to target aspect ratio
        
        Methods:
        - pad: Add black bars (maintains all content)
        - crop: Crop to fill (loses some content)
        - fit: Scale to fit (may have letterbox)
        """
        job_id = str(uuid.uuid4())[:8]
        temp_dir = Path(settings.TEMP_DIR) / f"aspect_{job_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Starting aspect ratio conversion job {job_id}")
            
            # Download video
            logger.info(f"Downloading video...")
            video_path = await self.downloader.download(source_url, temp_dir)
            
            # Get original video info
            original_info = await ffmpeg_ops.get_video_info(video_path)
            
            # Convert
            output_path = output_path or Path(settings.PROCESSED_DIR) / f"converted_{job_id}.mp4"
            
            logger.info(f"Converting to {target_ratio} using {method} method...")
            result_path = await ffmpeg_ops.convert_aspect_ratio(
                video_path=video_path,
                target_ratio=target_ratio,
                output_path=output_path,
                method=method,
                bg_color=bg_color
            )
            
            # Get result info
            result_info = await ffmpeg_ops.get_video_info(result_path)
            
            # Cleanup
            try:
                video_path.unlink()
                temp_dir.rmdir()
            except:
                pass
            
            return {
                "success": True,
                "job_id": job_id,
                "output_path": str(result_path),
                "output_url": f"/api/videos/converted/{job_id}",
                "original": {
                    "width": original_info.get("width"),
                    "height": original_info.get("height"),
                    "aspect_ratio": f"{original_info.get('width')}:{original_info.get('height')}"
                },
                "result": {
                    "width": result_info.get("width"),
                    "height": result_info.get("height"),
                    "aspect_ratio": target_ratio,
                    "duration": result_info.get("duration")
                },
                "method": method,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Aspect ratio conversion error: {e}")
            return {
                "success": False,
                "job_id": job_id,
                "output_path": None,
                "error": str(e)
            }
    
    async def convert_for_platform(
        self,
        source_url: str,
        platform: str,
        method: str = "pad",
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Convert video to recommended ratio for platform"""
        target_ratio = self.get_platform_ratio(platform)
        result = await self.convert(
            source_url=source_url,
            target_ratio=target_ratio,
            method=method,
            output_path=output_path
        )
        result["platform"] = platform
        result["recommended_ratio"] = target_ratio
        return result
    
    async def convert_batch(
        self,
        source_url: str,
        target_ratios: list[str],
        method: str = "pad"
    ) -> Dict[str, Any]:
        """Convert video to multiple aspect ratios at once"""
        job_id = str(uuid.uuid4())[:8]
        temp_dir = Path(settings.TEMP_DIR) / f"batch_{job_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Starting batch conversion job {job_id}")
            
            # Download video once
            logger.info("Downloading video...")
            video_path = await self.downloader.download(source_url, temp_dir)
            
            results = []
            for ratio in target_ratios:
                try:
                    output_path = Path(settings.PROCESSED_DIR) / f"batch_{job_id}_{ratio.replace(':', 'x')}.mp4"
                    
                    await ffmpeg_ops.convert_aspect_ratio(
                        video_path=video_path,
                        target_ratio=ratio,
                        output_path=output_path,
                        method=method
                    )
                    
                    video_info = await ffmpeg_ops.get_video_info(output_path)
                    
                    results.append({
                        "ratio": ratio,
                        "success": True,
                        "output_path": str(output_path),
                        "output_url": f"/api/videos/batch/{job_id}/{ratio.replace(':', 'x')}",
                        "width": video_info.get("width"),
                        "height": video_info.get("height"),
                        "duration": video_info.get("duration")
                    })
                except Exception as e:
                    results.append({
                        "ratio": ratio,
                        "success": False,
                        "error": str(e)
                    })
            
            # Cleanup source
            try:
                video_path.unlink()
                temp_dir.rmdir()
            except:
                pass
            
            return {
                "success": True,
                "job_id": job_id,
                "results": results,
                "total": len(target_ratios),
                "successful": len([r for r in results if r.get("success")]),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Batch conversion error: {e}")
            return {
                "success": False,
                "job_id": job_id,
                "results": [],
                "error": str(e)
            }


# Global instance
aspect_ratio_converter = AspectRatioConverter()
