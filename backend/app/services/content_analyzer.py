from __future__ import annotations

# Optional AI provider libraries - import lazily and handle missing packages
try:
    from openai import AsyncOpenAI as AsyncOpenAI  # type: ignore
except Exception:
    AsyncOpenAI = None  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None  # type: ignore

from typing import List, Dict, Any, Optional
import json
import time
import subprocess
from fractions import Fraction

from app.core.logger import logger

from app.core.config import settings
from app.services.platform_detector import PlatformDetector
from app.ai_prompts import VideoPrompts


class ContentAnalyzer:
    """Analyze video content using AI"""

    def __init__(self) -> None:
        self.platform_detector = PlatformDetector()
        self.ai_provider: str = getattr(settings, "AI_PROVIDER", "auto")

        # Pick provider based on configuration and availability (auto prefers Groq)
        def _pick_provider() -> str:
            if self.ai_provider != "auto":
                return self.ai_provider
            if getattr(settings, "GROQ_API_KEY", None):
                return "groq"
            if getattr(settings, "OPENAI_API_KEY", None):
                return "openai"
            if getattr(settings, "GEMINI_API_KEY", None):
                return "gemini"
            return "mock"

        self.ai_provider = _pick_provider()

        self.openai_client: Optional[AsyncOpenAI] = None
        # Track whether OpenAI/Groq auth appears valid to avoid repeated 401 noise
        self._openai_valid = True

        if self.ai_provider == "openai" and getattr(settings, "OPENAI_API_KEY", None):
            try:
                self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"OpenAI client initialization failed: {e}. Using mock analysis")
                self.openai_client = None
                self._openai_valid = False
        elif self.ai_provider == "groq" and getattr(settings, "GROQ_API_KEY", None):
            try:
                # Groq exposes an OpenAI-compatible endpoint
                self.openai_client = AsyncOpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url="https://api.groq.com/openai/v1",
                )
            except Exception as e:
                logger.warning(f"Groq client initialization failed: {e}. Using mock analysis")
                self.openai_client = None
                self._openai_valid = False
        elif self.ai_provider == "gemini" and getattr(settings, "GEMINI_API_KEY", None):
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Gemini client initialization failed: {e}. Using mock analysis")
        else:
            logger.warning("No AI API key configured, using non-AI fallback")

    async def analyze_video(
        self,
        video_path: str,
        platform: str,
        video_type: str = "short",
        transcript: Optional[str] = None,
        segments: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze video content comprehensively"""
        logger.info(f"Analyzing video: {video_path} for {platform}/{video_type}")
        start_time = time.time()

        try:
            # Get transcript if not provided
            if not transcript or not segments:
                # Lazy import with robust fallback if the optional TextDetector is missing
                try:
                    from app.services.text_detector import TextDetector  # keep lazy import
                except Exception as e:
                    logger.warning(f"TextDetector import failed ({e}), using mock extractor")

                    class TextDetector:
                        async def extract_text(self, _video_path: str):
                            return (
                                "",
                                [
                                    {
                                        "start_time": 0,
                                        "end_time": 0,
                                        "text": "",
                                        "has_text": False,
                                        "has_face": False,
                                    }
                                ],
                            )

                detector = TextDetector()
                transcript, segments = await detector.extract_text(video_path)

            # Analyze content with AI
            analysis = await self._analyze_with_ai(transcript, platform, video_type)

            # Check copyright
            copyright_check = await self._check_copyright(transcript)

            # Generate editing instructions (pass job options if provided)
            editing_instructions = await self._generate_editing_instructions(
                analysis, platform, video_type, options or {}
            )

            # Generate hashtags and titles
            hashtags = await self._generate_hashtags(transcript, platform)

            processing_time = time.time() - start_time

            result: Dict[str, Any] = {
                "transcript": transcript,
                "segments": segments,
                "analysis": analysis,
                "copyright_check": copyright_check,
                "editing_instructions": editing_instructions,
                "hashtags": hashtags,
                "processing_time": processing_time,
                "video_metadata": await self._get_video_metadata(video_path),
            }

            logger.info(f"Analysis completed in {processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise Exception(f"Video analysis failed: {str(e)}") from e

    async def _analyze_with_ai(
        self, transcript: str, platform: str, video_type: str
    ) -> Dict[str, Any]:
        """Analyze content using AI"""
        if not self._has_ai_credentials():
            return self._mock_analysis(transcript, platform, video_type)

        prompt = VideoPrompts.get_content_analysis_prompt(transcript, platform, video_type)

        try:
            if self.ai_provider in ("openai", "groq"):
                return await self._call_openai(prompt)
            if self.ai_provider == "gemini":
                return await self._call_gemini(prompt)
            return self._mock_analysis(transcript, platform, video_type)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._mock_analysis(transcript, platform, video_type)

    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI-compatible API (supports OpenAI and Groq endpoints)"""
        if not self.openai_client:
            raise RuntimeError(
                "OpenAI/Groq client not initialized. Check API key and AI_PROVIDER setting"
            )

        # choose model name by provider
        if self.ai_provider == "groq":
            model = getattr(settings, "GROQ_MODEL", None) or "llama-3.1-70b-versatile"
        else:
            model = getattr(settings, "OPENAI_MODEL", None) or "gpt-4o-mini"

        try:
            # Prefer JSON mode if model supports it
            try:
                resp = await self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a video content analysis expert."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
            except Exception as e:
                # Fallback: call without response_format if provider/model rejects it
                logger.warning(
                    f"OpenAI/Groq response_format not supported or failed, retrying without it: {e}"
                )
                resp = await self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a video content analysis expert."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )

            content = (resp.choices[0].message.content or "").strip()
            return self._safe_json_loads(content)

        except Exception as e:
            # If authentication error (invalid API key / 401), disable further OpenAI/Groq calls to avoid noisy retries
            msg = str(e).lower()
            if "invalid_api_key" in msg or "incorrect api key" in msg or "401" in msg:
                logger.warning(
                    f"{self.ai_provider} authentication failed (invalid API key). Falling back to mock analysis for this run and future calls."
                )
                self.openai_client = None
                self._openai_valid = False
            logger.error(f"OpenAI/Groq API error: {e}")
            raise

    async def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Call Google Gemini API"""
        try:
            # Keep default model name to match your existing setup
            model_name = getattr(settings, "GEMINI_MODEL", None) or "gemini-pro"
            model = genai.GenerativeModel(model_name)

            response = await model.generate_content_async(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2000,
                },
            )

            text = (response.text or "").strip()
            return self._safe_json_loads(text)

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def _check_copyright(self, content: str) -> Dict[str, Any]:
        """Check for copyright issues"""
        if not self._has_ai_credentials():
            return self._mock_copyright_check()

        prompt = VideoPrompts.get_copyright_avoidance_prompt(content)

        try:
            if self.ai_provider == "openai":
                return await self._call_openai(prompt)
            if self.ai_provider == "gemini":
                return await self._call_gemini(prompt)
            return self._mock_copyright_check()
        except Exception as e:
            logger.error(f"Copyright check failed: {e}")
            return self._mock_copyright_check()

    async def _generate_editing_instructions(
        self,
        analysis: Dict[str, Any],
        platform: str,
        video_type: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate editing instructions using AI or rule-based fallback"""
        if not self._has_ai_credentials():
            result = self._rule_based_editing_instructions(
                analysis.get("transcript", ""), platform, video_type, options or {}
            )
            result["used_rule_based"] = True
            return result

        prompt = VideoPrompts.get_editing_instructions_prompt(analysis, platform, video_type)

        try:
            if self.ai_provider in ("openai", "groq"):
                res = await self._call_openai(prompt)
                if isinstance(res, dict):
                    res["used_provider"] = self.ai_provider
                return res
            if self.ai_provider == "gemini":
                res = await self._call_gemini(prompt)
                if isinstance(res, dict):
                    res["used_provider"] = "gemini"
                return res
            result = self._rule_based_editing_instructions(
                analysis.get("transcript", ""), platform, video_type, options or {}
            )
            result["used_rule_based"] = True
            return result
        except Exception as e:
            logger.error(f"Editing instructions generation failed: {e}")
            result = self._rule_based_editing_instructions(
                analysis.get("transcript", ""), platform, video_type, options or {}
            )
            result["used_rule_based"] = True
            return result

    async def _generate_hashtags(self, content: str, platform: str) -> Dict[str, Any]:
        """Generate hashtags and titles"""
        if not self._has_ai_credentials():
            return self._mock_hashtags(platform)

        prompt = VideoPrompts.get_hashtag_generation_prompt(content, platform)

        try:
            if self.ai_provider == "openai":
                return await self._call_openai(prompt)
            if self.ai_provider == "gemini":
                return await self._call_gemini(prompt)
            return self._mock_hashtags(platform)
        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            return self._mock_hashtags(platform)

    async def _get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata via ffprobe"""
        try:
            ffprobe_path = getattr(settings, "FFPROBE_PATH", None) or "ffprobe"

            cmd = [
                ffprobe_path,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(video_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if not result.stdout.strip():
                return {}

            metadata = json.loads(result.stdout)

            fmt = metadata.get("format", {}) or {}
            video_info: Dict[str, Any] = {
                "duration": float(fmt.get("duration", 0) or 0),
                "size": int(fmt.get("size", 0) or 0),
                "bitrate": int(fmt.get("bit_rate", 0) or 0),
                "format": fmt.get("format_name", "") or "",
            }

            # Find video stream
            for stream in metadata.get("streams", []) or []:
                if stream.get("codec_type") == "video":
                    fps = 0.0
                    afr = stream.get("avg_frame_rate")
                    if afr and isinstance(afr, str) and "/" in afr:
                        try:
                            fps = float(Fraction(afr))
                        except Exception:
                            fps = 0.0

                    video_info.update(
                        {
                            "width": int(stream.get("width", 0) or 0),
                            "height": int(stream.get("height", 0) or 0),
                            "codec": stream.get("codec_name", "") or "",
                            "fps": fps,
                        }
                    )
                    break

            return video_info

        except Exception as e:
            logger.warning(f"Failed to get video metadata: {e}")
            return {}

    def _has_ai_credentials(self) -> bool:
        """Check if AI credentials are available"""
        if self.ai_provider == "openai":
            return bool(getattr(settings, "OPENAI_API_KEY", None)) and getattr(
                self, "_openai_valid", True
            )
        if self.ai_provider == "groq":
            return bool(getattr(settings, "GROQ_API_KEY", None)) and getattr(
                self, "_openai_valid", True
            )
        if self.ai_provider == "gemini":
            return bool(getattr(settings, "GEMINI_API_KEY", None))
        return False

    def _safe_json_loads(self, text: str) -> Dict[str, Any]:
        """
        Parse JSON robustly:
        - strips ```json fences
        - extracts first {...} block if model returns extra text
        """
        raw = (text or "").strip()

        # Remove fenced code blocks
        if raw.startswith("```json"):
            raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
        elif raw.startswith("```"):
            raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        # First try direct JSON
        try:
            val = json.loads(raw)
            return val if isinstance(val, dict) else {"result": val}
        except json.JSONDecodeError:
            pass

        # Try to extract first JSON object substring
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = raw[start : end + 1]
            try:
                val = json.loads(candidate)
                return val if isinstance(val, dict) else {"result": val}
            except json.JSONDecodeError:
                logger.error(f"AI returned non-JSON content (first 300 chars): {raw[:300]}")
                raise

        logger.error(f"AI returned non-JSON content (first 300 chars): {raw[:300]}")
        raise json.JSONDecodeError("No JSON object found in response", raw, 0)

    # -------------------- MOCKS --------------------

    def _mock_analysis(self, transcript: str, platform: str, video_type: str) -> Dict[str, Any]:
        """Mock analysis for testing"""
        return {
            "summary": "This is a mock analysis for testing purposes.",
            "category": "entertainment",
            "mood": "funny",
            "key_moments": [
                {
                    "start": 0,
                    "end": 10,
                    "description": "Opening scene",
                    "importance": "high",
                    "reason": "Hook for viewers",
                }
            ],
            "viral_potential": 75,
            "recommended_duration": 60,
            "editing_style": "fast_paced",
            "hashtag_suggestions": ["#funny", "#viral", "#test"],
            "title_suggestions": ["Test Video Title"],
            "platform_specific_notes": f"Mock analysis for {platform} ({video_type})",
        }

    def _mock_copyright_check(self) -> Dict[str, Any]:
        """Mock copyright check"""
        return {
            "copyright_risks": [],
            "safe_to_use_score": 100,
            "required_modifications": [],
        }

    def _rule_based_editing_instructions(
        self, transcript: str, platform: str, video_type: str, opts: dict
    ) -> Dict[str, Any]:
        """Rule-based editing instructions used when AI is unavailable or fails.

        Creates a single clip trimmed to target duration and applies basic effects
        according to job options: add_effects, add_subtitles, remove_watermark, change_music.
        """
        target = int(opts.get("duration") or (60 if video_type == "short" else 600))
        add_fx = bool(opts.get("add_effects"))
        add_sub = bool(opts.get("add_subtitles"))
        remove_wm = bool(opts.get("remove_watermark"))
        change_music = bool(opts.get("change_music"))

        subtitle = ""
        if add_sub and transcript:
            subtitle = " ".join(transcript.strip().split()[:20])

        effects = []
        if add_fx:
            effects = ["zoom_in", "color_filter"]

        clip = {
            "start_time": 0,
            "end_time": target,
            "action": "keep",
            "speed_factor": 1.0,
            "effects": effects,
        }
        if subtitle:
            clip["subtitle_text"] = subtitle

        if remove_wm:
            # conservative crop of bottom area to hide watermark (best-effort)
            clip["crop"] = {"x": 0, "y": 0, "w": "iw", "h": "ih*0.92"}

        if change_music:
            clip["mute_audio"] = True

        return {
            "clips": [clip],
            "platform_specific_settings": {
                "resolution": "1080:1920" if platform in ("tiktok", "reel") else "1920:1080",
                "audio_normalization": True,
            },
        }

    def _mock_hashtags(self, platform: str) -> Dict[str, Any]:
        """Mock hashtags"""
        return {
            "hashtags": ["#test", "#video", "#edit", f"#{platform}"],
            "titles": ["Test Video"],
            "description": "Test description",
        }
