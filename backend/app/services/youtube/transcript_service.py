"""
YouTube Video Analyzer - Stage 3: Transcript & NLP
===================================================
Multi-provider transcript extraction with automatic fallback.
Providers: YouTube Transcript API (free) → Whisper (local)
"""

import asyncio
import re
import json
from pathlib import Path
from typing import Optional, Any, Literal
from dataclasses import dataclass
import httpx

from app.core.logger import logger
from app.core.config import settings


@dataclass
class TranscriptSegment:
    """Single transcript segment with timestamp"""
    start: float
    end: float
    text: str


@dataclass
class TranscriptResult:
    """Complete transcript result"""
    success: bool
    video_id: str
    language: str
    full_text: str
    segments: list[TranscriptSegment]
    duration_seconds: float
    provider: str  # which provider was used
    confidence: float
    error: Optional[str] = None


class TranscriptProvider:
    """Base class for transcript providers"""
    
    name: str = "base"
    
    async def get_transcript(self, video_id: str) -> Optional[TranscriptResult]:
        raise NotImplementedError


class YouTubeTranscriptProvider(TranscriptProvider):
    """
    Free YouTube Transcript API
    No API key needed, extracts existing captions
    """
    
    name = "youtube_transcript_api"
    
    async def get_transcript(self, video_id: str) -> Optional[TranscriptResult]:
        """Get transcript using youtube-transcript-api library"""
        try:
            # Import here to avoid soft dependency issues if not installed
            import youtube_transcript_api
            from youtube_transcript_api import YouTubeTranscriptApi
            
            loop = asyncio.get_event_loop()
            
            
            def _fetch():
                # Try to get Vietnamese first, then English, then any
                try:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    
                    # Priority: vi > en > any
                    for lang in ['vi', 'en']:
                        try:
                            transcript = transcript_list.find_transcript([lang])
                            return transcript.fetch(), lang
                        except:
                            continue
                    
                    # Fallback to any available
                    transcript = transcript_list.find_transcript(['vi', 'en', 'auto'])
                    return transcript.fetch(), 'auto'
                    
                except Exception as e:
                    logger.warning(f"Transcript list error: {e}")
                    # Direct fetch as fallback
                    try:
                        data = YouTubeTranscriptApi.get_transcript(video_id)
                        return data, 'auto'
                    except Exception as e2:
                        logger.error(f"YouTubeTranscriptApi direct fetch failed: {e2}")
                        return None, None
            
            transcript_data, language = await loop.run_in_executor(None, _fetch)
            
            if not transcript_data:
                return None
            
            # Convert to segments
            segments = []
            full_text_parts = []
            
            for item in transcript_data:
                start = item.get('start', 0)
                duration = item.get('duration', 0)
                text = item.get('text', '').strip()
                
                if text:
                    segments.append(TranscriptSegment(
                        start=round(start, 2),
                        end=round(start + duration, 2),
                        text=text
                    ))
                    full_text_parts.append(text)
            
            total_duration = segments[-1].end if segments else 0
            
            return TranscriptResult(
                success=True,
                video_id=video_id,
                language=language,
                full_text=" ".join(full_text_parts),
                segments=segments,
                duration_seconds=total_duration,
                provider=self.name,
                confidence=0.95 if language != 'auto' else 0.85
            )
            
        except Exception as e:
            logger.error(f"YouTube Transcript API error: {e}")
            return None


class WhisperTranscriptProvider(TranscriptProvider):
    """
    Local Whisper transcription
    Requires audio file, more accurate but slower
    """
    
    name = "whisper_local"
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None
    
    async def get_transcript(
        self,
        video_id: str,
        audio_path: Optional[Path] = None
    ) -> Optional[TranscriptResult]:
        """Transcribe audio using Whisper"""
        if not audio_path:
            logger.error("Whisper requires audio_path")
            return None
        
        try:
            # Try faster-whisper first (faster)
            return await self._transcribe_faster_whisper(video_id, audio_path)
        except ImportError:
            # Fallback to regular whisper
            return await self._transcribe_whisper(video_id, audio_path)
    
    async def _transcribe_faster_whisper(
        self,
        video_id: str,
        audio_path: Path
    ) -> Optional[TranscriptResult]:
        """Use faster-whisper for GPU-accelerated transcription"""
        try:
            from faster_whisper import WhisperModel
            
            loop = asyncio.get_event_loop()
            
            def _transcribe():
                model = WhisperModel(
                    self.model_size,
                    device="cuda" if self._has_cuda() else "cpu",
                    compute_type="float16" if self._has_cuda() else "int8"
                )
                
                segments_gen, info = model.transcribe(
                    str(audio_path),
                    beam_size=5,
                    word_timestamps=True
                )
                
                return list(segments_gen), info
            
            segments_data, info = await loop.run_in_executor(None, _transcribe)
            
            segments = []
            full_text_parts = []
            
            for seg in segments_data:
                segments.append(TranscriptSegment(
                    start=round(seg.start, 2),
                    end=round(seg.end, 2),
                    text=seg.text.strip()
                ))
                full_text_parts.append(seg.text.strip())
            
            return TranscriptResult(
                success=True,
                video_id=video_id,
                language=info.language,
                full_text=" ".join(full_text_parts),
                segments=segments,
                duration_seconds=info.duration,
                provider="faster_whisper",
                confidence=info.language_probability
            )
            
        except Exception as e:
            logger.error(f"Faster-whisper error: {e}")
            return None
    
    async def _transcribe_whisper(
        self,
        video_id: str,
        audio_path: Path
    ) -> Optional[TranscriptResult]:
        """Use OpenAI Whisper for transcription"""
        try:
            import whisper
            
            loop = asyncio.get_event_loop()
            
            def _transcribe():
                if self._model is None:
                    self._model = whisper.load_model(self.model_size)
                
                result = self._model.transcribe(str(audio_path))
                return result
            
            result = await loop.run_in_executor(None, _transcribe)
            
            segments = []
            for seg in result.get("segments", []):
                segments.append(TranscriptSegment(
                    start=round(seg["start"], 2),
                    end=round(seg["end"], 2),
                    text=seg["text"].strip()
                ))
            
            return TranscriptResult(
                success=True,
                video_id=video_id,
                language=result.get("language", "unknown"),
                full_text=result.get("text", ""),
                segments=segments,
                duration_seconds=segments[-1].end if segments else 0,
                provider="whisper",
                confidence=0.90
            )
            
        except Exception as e:
            logger.error(f"Whisper error: {e}")
            return None
    
    def _has_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False


class TranscriptService:
    """
    Multi-provider transcript service with automatic fallback.
    
    Priority:
    1. YouTube Transcript API (free, fast, no processing)
    2. Whisper local (accurate, requires audio download)
    """
    
    def __init__(self):
        self.providers = [
            YouTubeTranscriptProvider(),
            WhisperTranscriptProvider(model_size="base")
        ]
    
    async def get_transcript(
        self,
        video_id: str,
        audio_path: Optional[Path] = None,
        preferred_provider: Optional[str] = None
    ) -> TranscriptResult:
        """
        Get transcript with automatic fallback.
        
        Args:
            video_id: YouTube video ID
            audio_path: Local audio file path (required for Whisper)
            preferred_provider: Force specific provider
        """
        errors = []
        
        # If preferred provider specified, try it first
        if preferred_provider:
            for provider in self.providers:
                if provider.name == preferred_provider:
                    if isinstance(provider, WhisperTranscriptProvider):
                        result = await provider.get_transcript(video_id, audio_path)
                    else:
                        result = await provider.get_transcript(video_id)
                    
                    if result and result.success:
                        return result
                    
                    errors.append(f"{provider.name}: failed")
                    break
        
        # Try all providers in order
        for provider in self.providers:
            try:
                logger.info(f"Trying transcript provider: {provider.name}")
                
                if isinstance(provider, WhisperTranscriptProvider):
                    # Whisper needs audio path
                    if not audio_path:
                        logger.info("Skipping Whisper (no audio path)")
                        continue
                    result = await provider.get_transcript(video_id, audio_path)
                else:
                    result = await provider.get_transcript(video_id)
                
                if result and result.success:
                    logger.info(f"Transcript obtained from {provider.name}")
                    return result
                
                errors.append(f"{provider.name}: no result")
                
            except Exception as e:
                error_msg = f"{provider.name}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
                continue
        
        # All providers failed
        return TranscriptResult(
            success=False,
            video_id=video_id,
            language="",
            full_text="",
            segments=[],
            duration_seconds=0,
            provider="none",
            confidence=0,
            error=f"All providers failed: {'; '.join(errors)}"
        )
    
    async def extract_audio(self, video_path: Path, output_path: Path) -> bool:
        """Extract audio from video for Whisper transcription"""
        try:
            from app.utils.ffmpeg_ops import ffmpeg_ops
            
            await ffmpeg_ops.extract_audio(video_path, output_path)
            return output_path.exists()
            
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            return False


# Singleton instance
transcript_service = TranscriptService()
