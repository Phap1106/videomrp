"""
Multi-Provider TTS Service
Supports: Edge TTS (Free), ViettelAI, FPT.AI, ElevenLabs, OpenAI, Google, gTTS
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, List, Dict
import asyncio
import uuid
import httpx
from app.core.logger import logger
from app.core.config import settings


class TTSProvider(ABC):
    """Abstract base class for TTS providers"""

    provider_id: str = "base"
    provider_name: str = "Base Provider"
    requires_api_key: bool = True
    supports_vietnamese: bool = False
    is_free: bool = False

    def __init__(self):
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        output_path: Path = None,
        with_timing: bool = False,
    ) -> tuple[Path, Optional[list[dict]]]:
        """Synthesize text to speech
        
        Returns:
            Tuple of (audio_path, Optional[word_timing])
            word_timing list: [{"start": 0, "end": 0.5, "text": "word"}]
        """
        pass

    @abstractmethod
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get provider info"""
        return {
            "id": self.provider_id,
            "name": self.provider_name,
            "requires_api_key": self.requires_api_key,
            "supports_vietnamese": self.supports_vietnamese,
            "is_free": self.is_free,
        }


class EdgeTTSProvider(TTSProvider):
    """
    Microsoft Edge TTS Provider - COMPLETELY FREE
    No API key required, supports many languages including Vietnamese
    """
    
    provider_id = "edge"
    provider_name = "Edge TTS (Free)"
    requires_api_key = False
    supports_vietnamese = True
    is_free = True

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.15,
        output_path: Path = None,
        with_timing: bool = False,
    ) -> tuple[Path, Optional[list[dict]]]:
        """Synthesize using Edge TTS"""
        try:
            import edge_tts
            
            voice = voice or settings.EDGE_TTS_VOICE
            output_path = output_path or Path(settings.TEMP_DIR) / f"tts_edge_{uuid.uuid4().hex[:8]}.mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Synthesizing with Edge TTS: {voice}, speed: {speed}, with_timing: {with_timing}")
            
            # Calculate rate string
            rate_percent = int((speed - 1.0) * 100)
            rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
            
            communicate = edge_tts.Communicate(text, voice, rate=rate_str)
            
            word_timing = []
            if with_timing:
                with open(output_path, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            word_timing.append({
                                "start": chunk["offset"] / 10**7, # Convert 100ns units to seconds
                                "end": (chunk["offset"] + chunk["duration"]) / 10**7,
                                "text": chunk["text"]
                            })
            else:
                await communicate.save(str(output_path))

            logger.info(f"Edge TTS output saved to {output_path}")
            return output_path, word_timing if with_timing else None

        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            raise
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add SSML-like pauses for more natural speech"""
        import re
        # Add longer pause after sentences
        text = re.sub(r'([.!?])\s+', r'\1... ', text)
        # Add brief pause after commas
        text = re.sub(r',\s+', ', ', text)
        return text

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get available Edge TTS voices"""
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            
            # Filter to show Vietnamese and English voices
            result = []
            for voice in voices:
                locale = voice.get("Locale", "")
                if locale.startswith("vi-") or locale.startswith("en-"):
                    result.append({
                        "id": voice["ShortName"],
                        "name": voice["FriendlyName"],
                        "gender": voice.get("Gender", "").lower(),
                        "language": locale,
                        "provider": "edge",
                    })
            
            # Sort: Vietnamese first
            result.sort(key=lambda x: (0 if x["language"].startswith("vi-") else 1, x["language"]))
            
            return result[:100]  # Increased limit
        except Exception as e:
            logger.error(f"Error fetching Edge voices: {e}")
            return self._get_default_voices()

    def _get_default_voices(self) -> List[Dict[str, Any]]:
        """Default Vietnamese and English voices - curated list"""
        return [
            # Vietnamese voices (miền Bắc, miền Nam style)
            {"id": "vi-VN-HoaiMyNeural", "name": "Hoài My (Nữ - Miền Bắc)", "gender": "female", "language": "vi-VN", "provider": "edge"},
            {"id": "vi-VN-NamMinhNeural", "name": "Nam Minh (Nam - Miền Bắc)", "gender": "male", "language": "vi-VN", "provider": "edge"},
            
            # English voices - diverse options
            {"id": "en-US-JennyNeural", "name": "Jenny (Nữ - US)", "gender": "female", "language": "en-US", "provider": "edge"},
            {"id": "en-US-GuyNeural", "name": "Guy (Nam - US)", "gender": "male", "language": "en-US", "provider": "edge"},
            {"id": "en-US-AriaNeural", "name": "Aria (Nữ - US)", "gender": "female", "language": "en-US", "provider": "edge"},
            {"id": "en-US-DavisNeural", "name": "Davis (Nam - US)", "gender": "male", "language": "en-US", "provider": "edge"},
            {"id": "en-GB-SoniaNeural", "name": "Sonia (Nữ - UK)", "gender": "female", "language": "en-GB", "provider": "edge"},
            {"id": "en-GB-RyanNeural", "name": "Ryan (Nam - UK)", "gender": "male", "language": "en-GB", "provider": "edge"},
            {"id": "en-AU-NatashaNeural", "name": "Natasha (Nữ - Australia)", "gender": "female", "language": "en-AU", "provider": "edge"},
            {"id": "en-AU-WilliamNeural", "name": "William (Nam - Australia)", "gender": "male", "language": "en-AU", "provider": "edge"},
            {"id": "en-SG-LunaNeural", "name": "Luna (Nữ - Singapore)", "gender": "female", "language": "en-SG", "provider": "edge"},
            {"id": "en-ZA-LeahNeural", "name": "Leah (Nữ - South Africa)", "gender": "female", "language": "en-ZA", "provider": "edge"},
        ]


class ViettelAITTSProvider(TTSProvider):
    """
    ViettelAI TTS Provider
    Vietnamese voice synthesis with natural expressions
    Free tier available
    """
    
    provider_id = "viettel"
    provider_name = "ViettelAI TTS"
    requires_api_key = True
    supports_vietnamese = True
    is_free = False  # Has free tier

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        output_path: Path = None,
    ) -> Path:
        """Synthesize using ViettelAI TTS"""
        try:
            if not settings.VIETTEL_API_KEY:
                raise ValueError("VIETTEL_API_KEY not set")
            
            voice = voice or settings.VIETTEL_TTS_VOICE
            output_path = output_path or Path(settings.TEMP_DIR) / f"tts_viettel_{uuid.uuid4().hex[:8]}.wav"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Synthesizing with ViettelAI TTS: {voice}")
            
            # ViettelAI TTS API
            url = "https://viettelai.vn/tts/speech_synthesis"
            headers = {
                "token": settings.VIETTEL_API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "voice": voice,
                "speed": speed,
                "tts_return_option": 2,  # Return audio file
                "token": settings.VIETTEL_API_KEY,
                "without_filter": False
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"ViettelAI TTS output saved to {output_path}")
                    return output_path, None
                else:
                    raise Exception(f"ViettelAI API error: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"ViettelAI TTS error: {e}")
            raise

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get available ViettelAI voices"""
        return [
            {"id": "hn-quynhanh", "name": "Quỳnh Anh (Nữ Hà Nội)", "gender": "female", "language": "vi-VN", "provider": "viettel"},
            {"id": "hn-thanhtung", "name": "Thanh Tùng (Nam Hà Nội)", "gender": "male", "language": "vi-VN", "provider": "viettel"},
            {"id": "sg-linhsan", "name": "Linh San (Nữ Sài Gòn)", "gender": "female", "language": "vi-VN", "provider": "viettel"},
            {"id": "sg-phuongly", "name": "Phương Ly (Nữ Sài Gòn)", "gender": "female", "language": "vi-VN", "provider": "viettel"},
            {"id": "hue-maianh", "name": "Mai Anh (Nữ Huế)", "gender": "female", "language": "vi-VN", "provider": "viettel"},
        ]


class FPTAITTSProvider(TTSProvider):
    """
    FPT.AI TTS Provider
    Vietnamese voice synthesis - Free 50,000 characters/month
    """
    
    provider_id = "fpt"
    provider_name = "FPT.AI TTS"
    requires_api_key = True
    supports_vietnamese = True
    is_free = False  # Has free tier

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        output_path: Path = None,
    ) -> Path:
        """Synthesize using FPT.AI TTS"""
        try:
            if not settings.FPT_API_KEY:
                raise ValueError("FPT_API_KEY not set")
            
            voice = voice or settings.FPT_TTS_VOICE
            output_path = output_path or Path(settings.TEMP_DIR) / f"tts_fpt_{uuid.uuid4().hex[:8]}.mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Synthesizing with FPT.AI TTS: {voice}")
            
            # FPT.AI TTS API
            url = "https://api.fpt.ai/hmi/tts/v5"
            headers = {
                "api-key": settings.FPT_API_KEY,
                "speed": str(speed),
                "voice": voice,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, content=text.encode('utf-8'), headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if "async" in result:
                        # Download audio from async URL
                        audio_url = result["async"]
                        await asyncio.sleep(1)  # Wait for processing
                        audio_response = await client.get(audio_url)
                        with open(output_path, "wb") as f:
                            f.write(audio_response.content)
                    logger.info(f"FPT.AI TTS output saved to {output_path}")
                    return output_path, None
                else:
                    raise Exception(f"FPT.AI API error: {response.status_code}")

        except Exception as e:
            logger.error(f"FPT.AI TTS error: {e}")
            raise

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get available FPT.AI voices"""
        return [
            {"id": "banmai", "name": "Ban Mai (Nữ Bắc)", "gender": "female", "language": "vi-VN", "provider": "fpt"},
            {"id": "leminh", "name": "Lê Minh (Nam Bắc)", "gender": "male", "language": "vi-VN", "provider": "fpt"},
            {"id": "thuminh", "name": "Thu Minh (Nữ Bắc)", "gender": "female", "language": "vi-VN", "provider": "fpt"},
            {"id": "giahuy", "name": "Gia Huy (Nam Bắc)", "gender": "male", "language": "vi-VN", "provider": "fpt"},
            {"id": "lannhi", "name": "Lan Nhi (Nữ Nam)", "gender": "female", "language": "vi-VN", "provider": "fpt"},
            {"id": "myan", "name": "Mỹ An (Nữ Nam)", "gender": "female", "language": "vi-VN", "provider": "fpt"},
            {"id": "linhsan", "name": "Linh San (Nữ Trung)", "gender": "female", "language": "vi-VN", "provider": "fpt"},
        ]


class ElevenLabsTTSProvider(TTSProvider):
    """
    ElevenLabs TTS Provider
    High-quality AI voices - Free tier: 10,000 characters/month
    """
    
    provider_id = "elevenlabs"
    provider_name = "ElevenLabs"
    requires_api_key = True
    supports_vietnamese = False  # English only
    is_free = False  # Has free tier

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        output_path: Path = None,
    ) -> Path:
        """Synthesize using ElevenLabs TTS"""
        try:
            if not settings.ELEVENLABS_API_KEY:
                raise ValueError("ELEVENLABS_API_KEY not set")
            
            voice_id = voice or settings.ELEVENLABS_VOICE_ID
            output_path = output_path or Path(settings.TEMP_DIR) / f"tts_eleven_{uuid.uuid4().hex[:8]}.mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Synthesizing with ElevenLabs TTS: {voice_id}")
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "speed": speed
                }
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"ElevenLabs TTS output saved to {output_path}")
                    return output_path, None
                else:
                    raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            raise

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get available ElevenLabs voices"""
        try:
            if not settings.ELEVENLABS_API_KEY:
                return self._get_default_voices()
            
            url = "https://api.elevenlabs.io/v1/voices"
            headers = {"xi-api-key": settings.ELEVENLABS_API_KEY}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "id": v["voice_id"],
                            "name": v["name"],
                            "gender": v.get("labels", {}).get("gender", "unknown"),
                            "language": "en",
                            "provider": "elevenlabs",
                        }
                        for v in data.get("voices", [])[:10]
                    ]
        except Exception as e:
            logger.error(f"Error fetching ElevenLabs voices: {e}")
        
        return self._get_default_voices()

    def _get_default_voices(self) -> List[Dict[str, Any]]:
        """Default ElevenLabs voices"""
        return [
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female", "language": "en", "provider": "elevenlabs"},
            {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female", "language": "en", "provider": "elevenlabs"},
            {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female", "language": "en", "provider": "elevenlabs"},
            {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male", "language": "en", "provider": "elevenlabs"},
            {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male", "language": "en", "provider": "elevenlabs"},
        ]


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS Provider"""
    
    provider_id = "openai"
    provider_name = "OpenAI TTS"
    requires_api_key = True
    supports_vietnamese = True
    is_free = False

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        output_path: Path = None,
    ) -> Path:
        """Synthesize using OpenAI TTS API"""
        try:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set")
            
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            voice = voice or settings.OPENAI_TTS_VOICE
            valid_voices = ["alloy", "echo", "fable", "onyx", "shimmer", "nova"]
            if voice not in valid_voices:
                voice = "nova"

            output_path = output_path or Path(settings.TEMP_DIR) / f"tts_openai_{uuid.uuid4().hex[:8]}.mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Synthesizing with OpenAI TTS: {voice}")
            
            response = await client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=text,
                speed=speed,
            )

            audio_data = await response.aread()
            with open(output_path, "wb") as f:
                f.write(audio_data)

            logger.info(f"OpenAI TTS output saved to {output_path}")
            return output_path, None

        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            raise

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get available OpenAI voices"""
        return [
            {"id": "nova", "name": "Nova (Female)", "gender": "female", "language": "multi", "provider": "openai"},
            {"id": "shimmer", "name": "Shimmer (Female)", "gender": "female", "language": "multi", "provider": "openai"},
            {"id": "alloy", "name": "Alloy (Neutral)", "gender": "neutral", "language": "multi", "provider": "openai"},
            {"id": "echo", "name": "Echo (Male)", "gender": "male", "language": "multi", "provider": "openai"},
            {"id": "fable", "name": "Fable (Male)", "gender": "male", "language": "multi", "provider": "openai"},
            {"id": "onyx", "name": "Onyx (Male)", "gender": "male", "language": "multi", "provider": "openai"},
        ]


class GTTSProvider(TTSProvider):
    """
    Google Text-to-Speech (gTTS) Provider
    FREE - No API key required, but lower quality
    """
    
    provider_id = "gtts"
    provider_name = "Google TTS (Free)"
    requires_api_key = False
    supports_vietnamese = True
    is_free = True

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        output_path: Path = None,
    ) -> Path:
        """Synthesize using gTTS"""
        try:
            from gtts import gTTS
            
            # Parse language from voice (e.g., "vi" or "en")
            lang = voice if voice and len(voice) == 2 else "vi"
            output_path = output_path or Path(settings.TEMP_DIR) / f"tts_gtts_{uuid.uuid4().hex[:8]}.mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Synthesizing with gTTS: {lang}")
            
            # gTTS doesn't support speed in API, we'll use ffmpeg later if needed
            tts = gTTS(text=text, lang=lang, slow=(speed < 0.8))
            
            # Run in thread pool since gTTS is synchronous
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, tts.save, str(output_path))

            logger.info(f"gTTS output saved to {output_path}")
            return output_path, None

        except Exception as e:
            logger.error(f"gTTS error: {e}")
            raise

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get available gTTS languages"""
        return [
            {"id": "vi", "name": "Tiếng Việt", "gender": "female", "language": "vi", "provider": "gtts"},
            {"id": "en", "name": "English", "gender": "female", "language": "en", "provider": "gtts"},
            {"id": "zh-CN", "name": "中文", "gender": "female", "language": "zh-CN", "provider": "gtts"},
            {"id": "ja", "name": "日本語", "gender": "female", "language": "ja", "provider": "gtts"},
            {"id": "ko", "name": "한국어", "gender": "female", "language": "ko", "provider": "gtts"},
        ]


class MockTTSProvider(TTSProvider):
    """Mock TTS Provider for testing"""
    
    provider_id = "mock"
    provider_name = "Mock TTS"
    requires_api_key = False
    supports_vietnamese = True
    is_free = True

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        output_path: Path = None,
    ) -> Path:
        """Generate mock audio file"""
        output_path = output_path or Path(settings.TEMP_DIR) / f"tts_mock_{uuid.uuid4().hex[:8]}.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import wave
        with wave.open(str(output_path), 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(b'\x00\x00' * 44100)

        logger.info(f"Mock TTS output saved to {output_path}")
        return output_path, None

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get mock voices"""
        return [
            {"id": "mock_female", "name": "Mock Female", "gender": "female", "language": "multi", "provider": "mock"},
            {"id": "mock_male", "name": "Mock Male", "gender": "male", "language": "multi", "provider": "mock"},
        ]


# ==================== PROVIDER REGISTRY ====================

TTS_PROVIDERS: Dict[str, type] = {
    "edge": EdgeTTSProvider,
    "viettel": ViettelAITTSProvider,
    "fpt": FPTAITTSProvider,
    "elevenlabs": ElevenLabsTTSProvider,
    "openai": OpenAITTSProvider,
    "gtts": GTTSProvider,
    "mock": MockTTSProvider,
}


async def get_tts_provider(provider: str = None) -> TTSProvider:
    """Get TTS provider by name"""
    provider = provider or settings.TTS_PROVIDER
    
    if provider in TTS_PROVIDERS:
        try:
            return TTS_PROVIDERS[provider]()
        except Exception as e:
            logger.warning(f"Failed to init {provider} provider: {e}, falling back to edge")
    
    # Default to Edge TTS (free, no key required)
    return EdgeTTSProvider()


async def get_all_providers_info() -> List[Dict[str, Any]]:
    """Get info about all available TTS providers"""
    result = []
    for provider_id, provider_class in TTS_PROVIDERS.items():
        try:
            provider = provider_class()
            info = provider.get_info()
            
            # Check if API key is configured
            if provider.requires_api_key:
                if provider_id == "viettel":
                    info["configured"] = bool(settings.VIETTEL_API_KEY)
                elif provider_id == "fpt":
                    info["configured"] = bool(settings.FPT_API_KEY)
                elif provider_id == "elevenlabs":
                    info["configured"] = bool(settings.ELEVENLABS_API_KEY)
                elif provider_id == "openai":
                    info["configured"] = bool(settings.OPENAI_API_KEY)
                else:
                    info["configured"] = False
            else:
                info["configured"] = True
            
            result.append(info)
        except Exception as e:
            logger.error(f"Error getting info for {provider_id}: {e}")
    
    return result


async def get_all_voices(provider: str = None) -> List[Dict[str, Any]]:
    """Get voices from one or all providers"""
    if provider:
        try:
            p = await get_tts_provider(provider)
            return await p.get_available_voices()
        except Exception as e:
            logger.error(f"Error getting voices for {provider}: {e}")
            return []
    
    # Get voices from all configured providers
    all_voices = []
    for provider_id in TTS_PROVIDERS:
        try:
            p = TTS_PROVIDERS[provider_id]()
            voices = await p.get_available_voices()
            all_voices.extend(voices)
        except Exception:
            pass
    
    return all_voices