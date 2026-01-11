"""
Advanced text overlay engine with styling support
"""

from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass
from app.core.logger import logger
from app.core.config import settings
from app.utils.ffmpeg_ops import ffmpeg_ops
import json


@dataclass
class TextStyle:
    """Text styling configuration"""
    font_file: Optional[Path] = None
    font_size: int = 60
    font_color: str = "FFFFFF"  # Hex color
    bold: bool = False
    italic:  bool = False
    bg_color: str = "000000"
    bg_alpha: float = 0.7
    position: str = "bottom"  # top, center, bottom, custom
    x:  Optional[int] = None
    y: Optional[int] = None
    border_width: int = 2
    border_color: str = "000000"
    shadow: bool = False
    shadow_offset: int = 2

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "font_file": str(self.font_file) if self.font_file else None,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "bold": self.bold,
            "italic":  self.italic,
            "bg_color": self.bg_color,
            "bg_alpha":  self.bg_alpha,
            "position": self.position,
            "x": self.x,
            "y": self.y,
            "border_width":  self.border_width,
            "border_color": self.border_color,
            "shadow":  self.shadow,
            "shadow_offset": self.shadow_offset,
        }

    @staticmethod
    def from_dict(data: dict) -> "TextStyle":
        """Create from dictionary"""
        return TextStyle(**{k: v for k, v in data.items() if k in TextStyle.__dataclass_fields__})


class TextOverlayEngine:
    """Engine for advanced text overlays"""

    async def add_styled_text(
        self,
        video_path: Path,
        text_segments: list[dict],  # [{"start": 0, "end": 5, "text": "Hello", "style": {... }}]
        output_path:  Path,
    ) -> Path:
        """Add styled text to video"""
        try:
            logger.info(f"Adding styled text to {video_path}")
            
            # Process styles
            processed_segments = []
            for seg in text_segments:
                style_data = seg.get("style", {})
                style = TextStyle.from_dict(style_data) if isinstance(style_data, dict) else style_data
                
                processed_segments.append({
                    **seg,
                    "style":  style,
                })
            
            # Use FFmpeg for rendering
            return await ffmpeg_ops.add_text_overlay(
                video_path,
                processed_segments,
                output_path,
                font_path=processed_segments[0]["style"].font_file if processed_segments else None,
                font_size=processed_segments[0]["style"].font_size if processed_segments else 60,
                font_color=processed_segments[0]["style"].font_color if processed_segments else "white",
                bg_color=processed_segments[0]["style"].bg_color if processed_segments else "black",
                bg_alpha=processed_segments[0]["style"]. bg_alpha if processed_segments else 0.7,
                position=processed_segments[0]["style"].position if processed_segments else "bottom",
            )

        except Exception as e:
            logger.error(f"Text overlay error: {e}")
            raise

    async def generate_subtitle_file(
        self,
        segments: list[dict],
        output_path: Path,
        format: str = "srt",
    ) -> Path:
        """Generate subtitle file (SRT, VTT, ASS)"""
        try:
            logger.info(f"Generating {format} subtitle file")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if format == "srt":
                return await self._generate_srt(segments, output_path)
            elif format == "vtt": 
                return await self._generate_vtt(segments, output_path)
            elif format == "ass": 
                return await self._generate_ass(segments, output_path)
            else:
                raise ValueError(f"Unknown subtitle format: {format}")

        except Exception as e:
            logger.error(f"Subtitle generation error: {e}")
            raise

    async def _generate_srt(self, segments: list[dict], output_path: Path) -> Path:
        """Generate SRT subtitle file"""
        with open(output_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start = self._seconds_to_srt_time(seg["start"])
                end = self._seconds_to_srt_time(seg["end"])
                text = seg.get("text", "")
                
                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")
        
        return output_path

    async def _generate_vtt(self, segments: list[dict], output_path: Path) -> Path:
        """Generate VTT subtitle file"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            
            for seg in segments:
                start = self._seconds_to_vtt_time(seg["start"])
                end = self._seconds_to_vtt_time(seg["end"])
                text = seg.get("text", "")
                
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")
        
        return output_path

    async def _generate_ass(self, segments: list[dict], output_path: Path) -> Path:
        """Generate ASS subtitle file (Advanced SubStation Alpha)"""
        with open(output_path, "w", encoding="utf-8") as f:
            # ASS header
            f.write("[Script Info]\n")
            f.write("Title: Generated Subtitles\n\n")
            
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write("Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n\n")
            
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            for seg in segments:
                start = self._seconds_to_ass_time(seg["start"])
                end = self._seconds_to_ass_time(seg["end"])
                text = seg. get("text", "")
                
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
        
        return output_path

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _seconds_to_vtt_time(seconds: float) -> str:
        """Convert seconds to VTT time format (HH:MM:SS. mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    @staticmethod
    def _seconds_to_ass_time(seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS. cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


text_overlay_engine = TextOverlayEngine()