"""
Speech-to-Text / Transcription Service
Supports:  OpenAI Whisper, Google Speech-to-Text, Deepgram
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional
import asyncio
from app.core.logger import logger
from app.core.config import settings


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers"""

    @abstractmethod
    async def transcribe(
        self,
        audio_path: Path,
        language: str = "vi",  # Vietnamese default
    ) -> dict[str, Any]:
        """
        Transcribe audio to text with timing information
        
        Args: 
            audio_path: Path to audio file
            language: Language code (vi, en, etc.)
            
        Returns:
            {
                "text": "Full transcript",
                "segments": [
                    {"start": 0.0, "end": 2.5, "text": "Hello"},
                    ... 
                ],
                "language": "vi",
                "duration": 45.5
            }
        """
        pass


class OpenAIWhisperProvider(TranscriptionProvider):
    """OpenAI Whisper transcription provider"""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings. OPENAI_API_KEY)

    async def transcribe(
        self,
        audio_path:  Path,
        language: str = "vi",
    ) -> dict[str, Any]:
        """Transcribe using OpenAI Whisper API"""
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            with open(audio_path, "rb") as f:
                transcript = await self. client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language=language,
                    response_format="verbose_json",
                )

            # Extract segments with timing
            segments = []
            if hasattr(transcript, 'segments'):
                for seg in transcript.segments:
                    segments.append({
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg. text,
                        "confidence":  getattr(seg, 'confidence', 1.0),
                    })

            result = {
                "text": transcript.text,
                "segments":  segments,
                "language": transcript.language if hasattr(transcript, 'language') else language,
                "duration": getattr(transcript, 'duration', 0),
            }

            logger.info(f"Transcription completed: {len(result['text'])} chars")
            return result

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            raise


class GoogleSpeechToTextProvider(TranscriptionProvider):
    """Google Cloud Speech-to-Text provider"""

    def __init__(self):
        if not settings. GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set")
        
        try:
            from google.cloud import speech
            self.client = speech. SpeechClient()
        except Exception as e:
            logger. error(f"Google Speech initialization error: {e}")
            raise

    async def transcribe(
        self,
        audio_path: Path,
        language: str = "vi",
    ) -> dict[str, Any]:
        """Transcribe using Google Cloud Speech-to-Text"""
        try:
            from google.cloud import speech
            
            logger.info(f"Transcribing audio with Google Speech-to-Text: {audio_path}")
            
            with open(audio_path, "rb") as f:
                content = f.read()

            audio = speech.RecognitionAudio(content=content)
            
            # Language code mapping
            language_code = "vi-VN" if language == "vi" else f"{language}-{language. upper()}"
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding. LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_word_time_offsets=True,
            )

            operation = self.client.long_running_recognize(config=config, audio=audio)
            response = operation.result(timeout=300)

            # Extract segments with timing
            full_text = ""
            segments = []
            
            for result in response.results:
                if not result.alternatives:
                    continue
                    
                alternative = result.alternatives[0]
                full_text += alternative.transcript

                for word_info in alternative.words:
                    start_time = word_info.start_time. total_seconds()
                    end_time = word_info.end_time.total_seconds()
                    segments.append({
                        "start": start_time,
                        "end": end_time,
                        "text": word_info.word,
                        "confidence": word_info.confidence,
                    })

            return {
                "text": full_text,
                "segments": segments,
                "language": language,
                "duration": 0,  # Not directly available
            }

        except Exception as e:
            logger.error(f"Google Speech-to-Text error: {e}")
            raise


class MockTranscriptionProvider(TranscriptionProvider):
    """Mock transcription provider for testing"""

    async def transcribe(
        self,
        audio_path: Path,
        language: str = "vi",
    ) -> dict[str, Any]:
        """Return mock transcript"""
        return {
            "text": "This is a mock transcription for testing purposes.",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": "This is a mock"},
                {"start": 1.5, "end": 3.0, "text": "transcription for testing"},
                {"start": 3.0, "end": 4.5, "text": "purposes."},
            ],
            "language": language,
            "duration": 4.5,
        }


async def get_transcription_provider(provider: str = None) -> TranscriptionProvider:
    """Get transcription provider based on settings"""
    provider = provider or settings.AI_PROVIDER
    
    if provider == "openai":
        return OpenAIWhisperProvider()
    elif provider == "google":
        return GoogleSpeechToTextProvider()
    else:
        logger.warning(f"Unknown transcription provider: {provider}, using mock")
        return MockTranscriptionProvider()