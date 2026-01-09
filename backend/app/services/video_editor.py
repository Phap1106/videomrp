import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import shutil
from loguru import logger
import asyncio

from app.core.config import settings
from app.utils.ffmpeg_ops import FFmpegOperations


class VideoEditor:
    """Edit videos based on AI instructions"""
    
    def __init__(self):
        self.ffmpeg = FFmpegOperations()
    
    async def edit_video(
        self,
        input_path: str,
        instructions: Dict[str, Any],
        output_path: str,
        platform: str
    ) -> Dict[str, Any]:
        """Edit video based on AI instructions"""
        logger.info(f"Editing video: {input_path} for {platform}")
        
        try:
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Step 1: Extract clips based on instructions
                clips = await self._extract_clips(input_path, instructions, temp_path)
                
                # Step 2: Apply effects to clips
                processed_clips = await self._process_clips(clips, instructions, temp_path)
                
                # Step 3: Concatenate clips
                final_video = await self._concatenate_clips(processed_clips, instructions, temp_path)
                
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
            logger.error(f"Video editing failed: {e}")
            raise Exception(f"Video editing failed: {str(e)}")
    
    async def _extract_clips(
        self, 
        input_path: str, 
        instructions: Dict[str, Any], 
        temp_dir: Path
    ) -> List[Dict[str, Any]]:
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
                end_time=end_time
            )
            
            clips.append({
                "path": str(clip_path),
                "index": i,
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "action": action,
                "info": clip_info
            })
        
        return clips
    
    async def _process_clips(
        self, 
        clips: List[Dict[str, Any]], 
        instructions: Dict[str, Any],
        temp_dir: Path
    ) -> List[Dict[str, Any]]:
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
                filter_chain.append(f"setpts={1/speed}*PTS")
                # Note: Need separate audio filter for speed
            
            # Apply text overlay
            if clip_info.get("text_overlay"):
                text_info = clip_info["text_overlay"]
                text = text_info.get("text", "").replace("'", "''")
                position = text_info.get("position", "bottom")
                duration = text_info.get("duration", clip["duration"])
                
                # Map position to coordinates
                position_map = {
                    "top": "x=(w-text_w)/2:y=50",
                    "center": "x=(w-text_w)/2:y=(h-text_h)/2",
                    "bottom": "x=(w-text_w)/2:y=h-text_h-50"
                }
                
                pos = position_map.get(position, position_map["bottom"])
                filter_chain.append(
                    f"drawtext=text='{text}':fontsize=48:fontcolor=white:"
                    f"box=1:boxcolor=black@0.5:boxborderw=5:{pos}"
                )
            
            # Apply zoom effect
            if "zoom_in" in clip_info.get("effects", []):
                filter_chain.append("zoompan=z='min(zoom+0.0015,1.5)':d=1")
            
            # Apply color filter
            if "color_filter" in clip_info.get("effects", []):
                filter_chain.append("colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131")
            
            # Process clip with filters
            if filter_chain:
                await self.ffmpeg.apply_filters(
                    input_path=input_path,
                    output_path=str(output_path),
                    filters=",".join(filter_chain)
                )
                clip["path"] = str(output_path)
            
            processed_clips.append(clip)
        
        return processed_clips
    
    async def _concatenate_clips(
        self, 
        clips: List[Dict[str, Any]], 
        instructions: Dict[str, Any],
        temp_dir: Path
    ) -> str:
        """Concatenate processed clips"""
        if len(clips) == 1:
            return clips[0]["path"]
        
        # Create concat file
        concat_file = temp_dir / "concat.txt"
        with open(concat_file, 'w') as f:
            for clip in clips:
                f.write(f"file '{clip['path']}'\n")
        
        output_path = temp_dir / "concatenated.mp4"
        
        await self.ffmpeg.concatenate_videos(
            concat_file=str(concat_file),
            output_path=str(output_path)
        )
        
        return str(output_path)
    
    async def _apply_final_processing(
        self, 
        input_path: str, 
        output_path: str, 
        instructions: Dict[str, Any],
        platform: str
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
                filters=",".join(filters)
            )
        else:
            # Just copy if no filters
            shutil.copy2(input_path, output_path)
    
    async def _generate_thumbnail(self, video_path: str, temp_dir: Path) -> Optional[str]:
        """Generate thumbnail from video"""
        try:
            thumbnail_path = temp_dir / "thumbnail.jpg"
            
            # Extract frame at 25% of video
            await self.ffmpeg.extract_frame(
                input_path=video_path,
                output_path=str(thumbnail_path),
                time_offset="25%"
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