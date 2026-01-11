"""
Text-to-Speech Provider Base class and implementations
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional
import asyncio
from app.core.logger import logger
from app.core.config import settings


class TTSProvider(ABC):
    """Abstract base class for TTS providers"""

    def __init__(self):
        self.provider_name = self.__class__.__name__

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice:  str = None,
        speed: float = 1.0,
        pitch: float = 0.0,
        output_path: Path = None,
    ) -> Path:
        """
        Synthesize text to speech
        
        Args:
            text:  Text to synthesize
            voice:  Voice identifier (provider-specific)
            speed: Speaking speed (0.5-2.0)
            pitch: Pitch adjustment (-20 to 20)
            output_path: Output file path
            
        Returns:
            Path to generated audio file
        """
        pass

    @abstractmethod
    async def get_available_voices(self) -> list[dict[str, Any]]:
        """
        Get list of available voices
        
        Returns:
            List of voice configs with name, gender, language, etc.
        """
        pass

    async def preview_voice(self, voice:  str, text: str = "Hello, this is a preview.") -> Path:
        """Generate preview audio for a voice"""
        return await self.synthesize(text, voice=voice)


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS Provider using the TTS API"""

    def __init__(self):
        super().__init__()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        self.available_voices = ["alloy", "echo", "fable", "onyx", "shimmer", "nova"]

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        pitch: float = 0.0,
        output_path: Path = None,
    ) -> Path:
        """Synthesize using OpenAI TTS API"""
        try:
            voice = voice or settings.OPENAI_TTS_VOICE
            if voice not in self.available_voices:
                voice = self.available_voices[0]

            output_path = output_path or Path(settings.TEMP_DIR) / f"tts_{id(text)}.mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Synthesizing with OpenAI TTS: {voice}")
            
            response = await self.client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=text,
                speed=speed,
            )

            # Write audio to file
            audio_data = await response.aread()
            with open(output_path, "wb") as f:
                f.write(audio_data)

            logger.info(f"TTS output saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            raise

    async def get_available_voices(self) -> list[dict[str, Any]]:
        """Get available OpenAI voices"""
        return [
            {"id": "alloy", "name":  "Alloy", "gender": "neutral", "language": "en"},
            {"id": "echo", "name": "Echo", "gender":  "male", "language": "en"},
            {"id": "fable", "name": "Fable", "gender": "male", "language": "en"},
            {"id": "onyx", "name": "Onyx", "gender": "male", "language": "en"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female", "language": "en"},
            {"id": "nova", "name": "Nova", "gender": "female", "language": "en"},
        ]


class GoogleTTSProvider(TTSProvider):
    """Google Cloud Text-to-Speech Provider"""

    def __init__(self):
        super().__init__()
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set")
        
        try:
            from google.cloud import texttospeech
            from google.oauth2 import service_account
            
            # Setup credentials
            import json
            if settings.GOOGLE_PROJECT_ID:
                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(settings.GOOGLE_API_KEY)
                )
                self.client = texttospeech.TextToSpeechClient(credentials=credentials)
            else:
                self.client = texttospeech.TextToSpeechClient()
        except Exception as e:
            logger.error(f"Google TTS initialization error: {e}")
            raise

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        pitch: float = 0.0,
        output_path: Path = None,
    ) -> Path:
        """Synthesize using Google Cloud TTS"""
        try:
            from google.cloud import texttospeech
            
            voice = voice or settings.GOOGLE_TTS_VOICE
            output_path = output_path or Path(settings.TEMP_DIR) / f"tts_{id(text)}.mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Synthesizing with Google TTS: {voice}")
            
            # Parse voice string (format: "en-US-Standard-A")
            parts = voice.split("-")
            language_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else "en-US"
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voices = self.client.list_voices(language_code=language_code)
            if voices.voices:
                selected_voice = voices.voices[0]
                voice_params = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    name=voice,
                )
            else:
                voice_params = texttospeech.VoiceSelectionParams(language_code=language_code)
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speed,
                pitch=pitch,
            )

            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config,
            )

            with open(output_path, "wb") as f:
                f. write(response.audio_content)

            logger.info(f"TTS output saved to {output_path}")
            return output_path

        except Exception as e: 
            logger.error(f"Google TTS error: {e}")
            raise

    async def get_available_voices(self) -> list[dict[str, Any]]: 
        """Get available Google voices"""
        try:
            from google.cloud import texttospeech
            
            voices = self.client.list_voices()
            result = []
            
            for voice in voices.voices[: 20]:  # Limit to first 20
                result.append({
                    "id": voice.name,
                    "name": voice.name. split("-")[-1],
                    "gender": str(voice.ssml_gender),
                    "language": voice. language_codes[0] if voice.language_codes else "en",
                })
            
            return result
        except Exception as e:
            logger.error(f"Error fetching Google voices: {e}")
            return []


class MockTTSProvider(TTSProvider):
    """Mock TTS Provider for testing"""

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        pitch: float = 0.0,
        output_path: Path = None,
    ) -> Path:
        """Generate mock audio file"""
        output_path = output_path or Path(settings.TEMP_DIR) / f"tts_mock_{id(text)}.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a simple WAV file (silence)
        import wave
        with wave.open(str(output_path), 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            # Write 1 second of silence
            wav_file.writeframes(b'\x00\x00' * 44100)

        logger.info(f"Mock TTS output saved to {output_path}")
        return output_path

    async def get_available_voices(self) -> list[dict[str, Any]]:
        """Get mock voices"""
        return [
            {"id": "mock_male", "name": "Mock Male", "gender": "male", "language": "en"},
            {"id": "mock_female", "name": "Mock Female", "gender":  "female", "language": "en"},
        ]


# Factory function
async def get_tts_provider(provider:  str = None) -> TTSProvider:
    """Get TTS provider based on settings"""
    provider = provider or settings.TTS_PROVIDER
    
    if provider == "openai": 
        return OpenAITTSProvider()
    elif provider == "google":
        return GoogleTTSProvider()
    else:
        logger.warning(f"Unknown TTS provider: {provider}, using mock")
        return MockTTSProvider()