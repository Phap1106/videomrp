"""
Audio processing service for extracting, converting, and mixing audio
"""

from pathlib import Path
from typing import Optional, Tuple
import asyncio
from app.core.logger import logger
from app.core.config import settings
from app.utils.ffmpeg_ops import ffmpeg_ops


class AudioProcessor: 
    """Handle audio operations"""

    async def extract_audio(self, video_path: Path) -> Path:
        """Extract audio from video"""
        return await ffmpeg_ops.extract_audio(
            video_path,
            Path(settings.TEMP_DIR) / f"audio_{video_path.stem}.wav",
        )

    async def get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration in seconds"""
        try:
            import wave
            with wave.open(str(audio_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                return duration
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0

    async def create_silence(self, duration: float, output_path: Path) -> Path:
        """Create silence audio file"""
        try:
            import wave
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            sample_rate = 44100
            num_frames = int(duration * sample_rate)
            
            with wave. open(str(output_path), 'w') as wav_file:
                wav_file.setnchannels(2)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(b'\x00\x00' * num_frames * 2)
            
            logger.info(f"Silence created:  {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating silence: {e}")
            raise


audio_processor = AudioProcessor()