import os
import logging
import tempfile
from typing import List, Tuple, Optional
from pathlib import Path
import numpy as np

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
    from moviepy.video.fx import all as vfx
    from scenedetect import detect, AdaptiveDetector, ContentDetector
    from scenedetect.video_stream import VideoStream
    import cv2
except ImportError as e:
    logging.warning(f"Video processing libraries not fully installed: {e}")

from config import Config

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Process videos: detect scenes, cut, merge, add effects"""
    
    def __init__(self, input_video: str):
        self.input_video = input_video
        self.output_dir = Config.OUTPUT_FOLDER
        self.temp_dir = Config.TEMP_FOLDER
        
        # Ensure directories exist
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Scene detection settings
        self.scene_threshold = Config.SCENE_DETECTION_THRESHOLD
        self.min_scene_duration = Config.MIN_SCENE_DURATION
        
    def detect_scenes(self, threshold: Optional[float] = None) -> List[Tuple[float, float]]:
        """Detect scenes in video"""
        try:
            if threshold is None:
                threshold = self.scene_threshold
            
            logger.info(f"Detecting scenes in {self.input_video} with threshold {threshold}")
            
            # Try adaptive detector first
            detector = AdaptiveDetector(
                threshold=threshold,
                min_scene_len=int(self.min_scene_duration * 30)  # Convert to frames
            )
            
            # Detect scenes
            scene_list = detect(self.input_video, detector)
            
            if not scene_list:
                logger.info("No scenes detected with adaptive detector, trying content detector")
                # Fallback to content detector
                detector = ContentDetector(threshold=threshold)
                scene_list = detect(self.input_video, detector)
            
            if not scene_list:
                # If still no scenes, create one scene for entire video
                duration = self.get_video_duration()
                scenes = [(0.0, duration)]
                logger.info(f"No scenes detected, using entire video: {duration:.2f}s")
            else:
                scenes = []
                for i, (start, end) in enumerate(scene_list):
                    start_sec = start.get_seconds()
                    end_sec = end.get_seconds()
                    scene_duration = end_sec - start_sec
                    
                    # Skip scenes that are too short
                    if scene_duration >= self.min_scene_duration:
                        scenes.append((start_sec, end_sec))
                        logger.info(f"Scene {i+1}: {start_sec:.2f}s - {end_sec:.2f}s ({scene_duration:.2f}s)")
                    else:
                        logger.info(f"Skipping short scene {i+1}: {scene_duration:.2f}s")
            
            logger.info(f"Detected {len(scenes)} scenes")
            return scenes
            
        except Exception as e:
            logger.error(f"Scene detection error: {str(e)}")
            # Return full video as single scene
            duration = self.get_video_duration()
            return [(0.0, duration)]
    
    def get_video_duration(self) -> float:
        """Get video duration in seconds"""
        try:
            with VideoFileClip(self.input_video) as clip:
                return clip.duration
        except Exception as e:
            logger.error(f"Error getting video duration: {str(e)}")
            return 0.0
    
    def cut_scenes(self, scenes: List[Tuple[float, float]]) -> List[str]:
        """Cut video into scenes"""
        try:
            if not scenes:
                logger.warning("No scenes to cut")
                return []
            
            logger.info(f"Cutting {len(scenes)} scenes")
            scene_files = []
            
            with VideoFileClip(self.input_video) as video_clip:
                for i, (start, end) in enumerate(scenes):
                    scene_duration = end - start
                    
                    if scene_duration < self.min_scene_duration:
                        logger.info(f"Skipping scene {i+1} (too short: {scene_duration:.2f}s)")
                        continue
                    
                    # Create scene clip
                    scene_clip = video_clip.subclip(start, end)
                    
                    # Save scene to temp file
                    scene_filename = f"scene_{i+1:03d}_{int(start)}_{int(end)}.mp4"
                    scene_filepath = self.temp_dir / scene_filename
                    
                    logger.info(f"Saving scene {i+1}: {scene_filename} ({scene_duration:.2f}s)")
                    
                    # Write scene with optimal settings
                    scene_clip.write_videofile(
                        str(scene_filepath),
                        codec='libx264',
                        audio_codec='aac',
                        temp_audiofile=str(self.temp_dir / f'temp_audio_{i}.m4a'),
                        remove_temp=True,
                        verbose=False,
                        logger=None,
                        preset='fast',
                        ffmpeg_params=[
                            '-crf', '23',  # Good quality
                            '-movflags', '+faststart'  # Web optimized
                        ]
                    )
                    
                    scene_clip.close()
                    scene_files.append(str(scene_filepath))
            
            logger.info(f"Cut {len(scene_files)} scenes successfully")
            return scene_files
            
        except Exception as e:
            logger.error(f"Error cutting scenes: {str(e)}")
            return []
    
    def auto_select_scenes(self, scenes: List[Tuple[float, float]], 
                          key_moments: List[int] = None,
                          target_duration: float = None) -> List[int]:
        """Automatically select scenes for highlight reel"""
        if target_duration is None:
            target_duration = Config.TARGET_VIDEO_DURATION
        
        if not scenes:
            return []
        
        # Calculate scene durations
        scene_durations = [end - start for start, end in scenes]
        
        # If key moments provided, prioritize those scenes
        if key_moments:
            # Convert key moments to scene indices
            selected = []
            total_duration = 0
            
            for moment in key_moments:
                # Find scene containing this moment
                for i, (start, end) in enumerate(scenes):
                    if start <= moment <= end and i not in selected:
                        if total_duration + scene_durations[i] <= target_duration:
                            selected.append(i)
                            total_duration += scene_durations[i]
                            break
            
            if selected:
                selected.sort()
                return selected
        
        # Default algorithm: select longest scenes first
        selected = []
        total_duration = 0
        
        # Sort scenes by duration (longest first)
        indexed_scenes = list(enumerate(scene_durations))
        indexed_scenes.sort(key=lambda x: x[1], reverse=True)
        
        for idx, duration in indexed_scenes:
            if total_duration + duration <= target_duration:
                selected.append(idx)
                total_duration += duration
            elif total_duration < target_duration * 0.5:  # If less than half filled
                # Add this scene even if it exceeds target
                selected.append(idx)
                total_duration += duration
                break
        
        selected.sort()
        logger.info(f"Selected {len(selected)} scenes (total: {total_duration:.2f}s)")
        return selected
    
    def merge_scenes(self, scene_files: List[str], 
                    output_path: Optional[str] = None,
                    fade_duration: float = None) -> str:
        """Merge scenes into final video"""
        try:
            if not scene_files:
                raise ValueError("No scene files to merge")
            
            if fade_duration is None:
                fade_duration = Config.FADE_DURATION
            
            if output_path is None:
                # Generate output filename
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = str(self.output_dir / f"merged_{timestamp}.mp4")
            
            logger.info(f"Merging {len(scene_files)} scenes")
            
            clips = []
            for i, scene_file in enumerate(scene_files):
                logger.info(f"Loading scene {i+1}: {Path(scene_file).name}")
                clip = VideoFileClip(scene_file)
                
                # Add fade effects
                if fade_duration > 0:
                    clip = clip.fadein(fade_duration).fadeout(fade_duration)
                
                clips.append(clip)
            
            # Concatenate clips
            logger.info("Concatenating clips...")
            final_clip = concatenate_videoclips(clips, method="compose")
            
            # Write final video
            logger.info(f"Saving to: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=str(self.temp_dir / 'temp_audio_final.m4a'),
                remove_temp=True,
                verbose=False,
                logger=None,
                preset='medium',
                ffmpeg_params=[
                    '-crf', '21',  # Better quality
                    '-movflags', '+faststart',
                    '-pix_fmt', 'yuv420p'  # Better compatibility
                ]
            )
            
            # Close clips
            final_clip.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Merged video saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error merging scenes: {str(e)}")
            raise
    
    def add_effects(self, video_path: str, effects: List[str] = None) -> str:
        """Add effects to video"""
        try:
            if effects is None:
                effects = ['color_correction', 'stabilize']
            
            logger.info(f"Adding effects to {video_path}: {effects}")
            
            with VideoFileClip(video_path) as clip:
                processed_clip = clip
                
                for effect in effects:
                    if effect == 'color_correction':
                        processed_clip = self._apply_color_correction(processed_clip)
                    elif effect == 'stabilize':
                        processed_clip = self._stabilize_video(processed_clip)
                    elif effect == 'slow_motion':
                        processed_clip = processed_clip.fx(vfx.speedx, 0.5)
                    elif effect == 'fast_motion':
                        processed_clip = processed_clip.fx(vfx.speedx, 2.0)
                    elif effect == 'text_overlay':
                        # Add text overlay (example)
                        txt_clip = self._create_text_clip("Processed by AI Tool", clip.duration)
                        processed_clip = CompositeVideoClip([processed_clip, txt_clip])
                
                # Save processed video
                output_path = str(self.output_dir / f"effected_{Path(video_path).name}")
                processed_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                processed_clip.close()
                
                logger.info(f"Effects applied, saved to: {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error applying effects: {str(e)}")
            return video_path  # Return original if fails
    
    def _apply_color_correction(self, clip):
        """Apply basic color correction"""
        # Simple brightness/contrast adjustment
        def adjust_frame(frame):
            frame = frame.astype(np.float32)
            frame = np.clip(frame * 1.1, 0, 255)  # Increase brightness
            return frame.astype(np.uint8)
        
        return clip.fl_image(adjust_frame)
    
    def _stabilize_video(self, clip):
        """Simple video stabilization"""
        # This is a simplified version
        # In production, use OpenCV's stabilization algorithms
        return clip  # Placeholder
    
    def _create_text_clip(self, text: str, duration: float):
        """Create text overlay clip"""
        from moviepy.editor import TextClip
        
        txt_clip = TextClip(
            text,
            fontsize=24,
            color='white',
            stroke_color='black',
            stroke_width=1
        )
        
        txt_clip = txt_clip.set_position(('center', 'bottom'))
        txt_clip = txt_clip.set_duration(duration)
        
        return txt_clip
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """Extract audio from video"""
        try:
            if output_path is None:
                output_path = str(self.temp_dir / f"audio_{Path(video_path).stem}.mp3")
            
            with VideoFileClip(video_path) as clip:
                if clip.audio is not None:
                    clip.audio.write_audiofile(
                        output_path,
                        verbose=False,
                        logger=None
                    )
                    logger.info(f"Audio extracted: {output_path}")
                    return output_path
                else:
                    logger.warning("No audio track found")
                    return ""
                    
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            return ""
    
    def add_subtitles(self, video_path: str, subtitles: List[dict]) -> str:
        """Add subtitles to video"""
        try:
            # This is a simplified implementation
            # In production, use proper subtitle rendering
            logger.info(f"Adding {len(subtitles)} subtitles to video")
            
            # For now, return original
            # TODO: Implement proper subtitle rendering
            return video_path
            
        except Exception as e:
            logger.error(f"Error adding subtitles: {str(e)}")
            return video_path