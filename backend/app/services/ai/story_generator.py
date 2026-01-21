"""
AI Story Generation Service
Generates creative stories, rewrites content, creates narration
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import json
from app.core.logger import logger
from app.core.config import settings
from app.ai_prompts import VideoPrompts

class StoryGenerator(ABC):
    """Abstract base class for story generation"""

    @abstractmethod
    async def generate_story(
        self,
        prompt: str,
        max_length: int = 1000,
        style: str = "narrative",  # narrative, humorous, dramatic, educational
        language: str = "vi",
    ) -> str:
        """Generate a story based on prompt"""
        pass

    @abstractmethod
    async def rewrite_transcript(
        self,
        original_text: str,
        segments: list[dict],  # timing info
        style: str = "improved",
        preserve_meaning: bool = True,
    ) -> dict[str, Any]:
        """Rewrite transcript maintaining timing"""
        pass

    @abstractmethod
    async def generate_narration(
        self,
        topic: str,
        duration: int = 60,  # seconds
        tone: str = "professional",
    ) -> str:
        """Generate narration for video"""
        pass


class OpenAIStoryGenerator(StoryGenerator):
    """OpenAI-powered story generation using GPT"""

    def __init__(self):
        if not settings. OPENAI_API_KEY: 
            raise ValueError("OPENAI_API_KEY not set")
        
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def generate_story(
        self,
        prompt:  str,
        max_length:  int = 1000,
        style: str = "narrative",
        language: str = "vi",
    ) -> str:
        """Generate story using OpenAI GPT"""
        try:
            logger.info(f"Generating {style} story in {language}")
            
            system_prompt = f"""You are a creative storyteller. Generate a {style} story in {language}. 
            The story should be engaging, vivid, and suitable for video content.
            Maximum length: {max_length} words."""

            response = await self.client.chat. completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_length,
                temperature=0.7,
            )

            story = response.choices[0].message.content
            logger. info(f"Story generated: {len(story)} chars")
            return story

        except Exception as e:
            logger. error(f"Story generation error: {e}")
            raise

    async def rewrite_transcript(
        self,
        original_text: str,
        segments: list[dict],
        style: str = "improved",
        preserve_meaning: bool = True,
    ) -> dict[str, Any]:
        """Rewrite transcript while preserving timing"""
        try:
            logger.info(f"Rewriting transcript with style: {style}")
            
            # Calculate approximate characters per second
            total_duration = segments[-1]["end"] if segments else 1
            chars_per_second = len(original_text) / total_duration if total_duration > 0 else 0
            
            system_prompt = VideoPrompts.get_transcript_rewrite_prompt(original_text, style)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Hãy viết lại bản transcript này theo phong cách {style}."},
                ],
                max_tokens=int(len(original_text) * 1.5),
                temperature=0.7,
            )

            rewritten_text = response.choices[0].message.content. strip()
            
            # Preserve original segments but with rewritten text
            # This is a simplified approach - in production, you'd want more sophisticated mapping
            words_original = original_text.split()
            words_rewritten = rewritten_text.split()
            
            rewritten_segments = []
            word_idx = 0
            total_words = len(words_rewritten)
            
            for i, seg in enumerate(segments):
                seg_duration = seg["end"] - seg["start"]
                remaining_duration = total_duration - seg["start"]
                
                if remaining_duration > 0:
                    words_left = total_words - word_idx
                    proportion = seg_duration / remaining_duration if remaining_duration > 0 else 0
                    seg_word_count = round(proportion * words_left)
                else:
                    seg_word_count = total_words - word_idx
                
                # Boundary check
                seg_word_count = min(seg_word_count, total_words - word_idx)
                if i == len(segments) - 1: # Last segment gets all remaining words
                    seg_word_count = total_words - word_idx
                    
                seg_words = words_rewritten[word_idx:word_idx + seg_word_count]
                
                rewritten_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": " ".join(seg_words),
                    "original_text": seg.get("text"),
                })
                
                word_idx += seg_word_count

            return {
                "original_text": original_text,
                "rewritten_text": rewritten_text,
                "segments": rewritten_segments,
                "style": style,
            }

        except Exception as e: 
            logger.error(f"Transcript rewriting error: {e}")
            raise

    async def generate_narration(
        self,
        topic: str,
        duration: int = 60,
        tone: str = "professional",
    ) -> str:
        """Generate narration for a topic"""
        try:
            logger.info(f"Generating {tone} narration for {duration}s using OpenAI")
            
            # Use specialized conversational prompt if tone matches or by default for high quality
            system_prompt = VideoPrompts.get_conversational_narration_prompt(topic, duration, tone)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Chủ đề cụ thể cần tập trung: {topic}"},
                ],
                max_tokens=int(duration * 5), # Allow room for formatting
                temperature=0.8,
            )

            narration = response.choices[0].message.content.strip()
            # Remove markdown formatting if AI adds it
            narration = narration.replace('"', '').replace("**", "").replace("__", "")
            
            logger.info(f"Narration generated: {len(narration)} chars")
            return narration

        except Exception as e:
            logger.error(f"Narration generation error: {e}")
            raise


class GeminiStoryGenerator(StoryGenerator):
    """Google Gemini-powered story generation"""

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set")
        
        import google.generativeai as genai
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-flash-latest')

    async def generate_story(
        self,
        prompt: str,
        max_length: int = 1000,
        style: str = "narrative",
        language: str = "vi",
    ) -> str:
        """Generate story using Gemini"""
        try: 
            logger.info(f"Generating {style} story with Gemini in {language}")
            
            full_prompt = f"""Generate a {style} story in {language} language.
            Maximum length: {max_length} words.
            Prompt: {prompt}"""

            response = await asyncio.to_thread(self.model.generate_content, full_prompt)
            story = response.text
            logger.info(f"Story generated: {len(story)} chars")
            return story

        except Exception as e:
            logger.error(f"Gemini story generation error: {e}")
            raise

    async def rewrite_transcript(
        self,
        original_text: str,
        segments: list[dict],
        style: str = "improved",
        preserve_meaning: bool = True,
    ) -> dict[str, Any]:
        """Rewrite transcript using Gemini"""
        try: 
            logger.info(f"Rewriting transcript with Gemini: {style}")
            
            total_duration = segments[-1]["end"] if segments else 1
            
            prompt = VideoPrompts.get_transcript_rewrite_prompt(original_text, style)
            prompt += f"\n\nTranscript gốc: {original_text}"

            response = await asyncio.to_thread(self.model.generate_content, prompt)
            rewritten_text = response.text.strip()
            
            # Similar segment mapping as OpenAI version
            rewritten_segments = []
            word_idx = 0
            total_words = len(words_rewritten)
            
            for i, seg in enumerate(segments):
                seg_duration = seg["end"] - seg["start"]
                remaining_duration = total_duration - seg["start"]
                
                if remaining_duration > 0:
                    words_left = total_words - word_idx
                    proportion = seg_duration / remaining_duration
                    seg_word_count = round(proportion * words_left)
                else:
                    seg_word_count = total_words - word_idx
                    
                seg_word_count = min(seg_word_count, total_words - word_idx)
                if i == len(segments) - 1:
                    seg_word_count = total_words - word_idx

                seg_words = words_rewritten[word_idx:word_idx + seg_word_count]
                
                rewritten_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": " ".join(seg_words),
                    "original_text": seg.get("text"),
                })
                
                word_idx += seg_word_count

            return {
                "original_text": original_text,
                "rewritten_text": rewritten_text,
                "segments": rewritten_segments,
                "style": style,
            }

        except Exception as e:
            logger.error(f"Gemini transcript rewriting error: {e}")
            raise

    async def generate_narration(
        self,
        topic: str,
        duration: int = 60,
        tone: str = "professional",
    ) -> str:
        """Generate narration using Gemini"""
        try: 
            logger.info(f"Generating {tone} narration with Gemini for {duration}s")
            
            prompt = VideoPrompts.get_conversational_narration_prompt(topic, duration, tone)
            prompt += f"\n\nChủ đề: {topic}"

            response = await asyncio.to_thread(self.model.generate_content, prompt)
            narration = response.text.strip()
            # Cleanup
            narration = narration.replace('"', '').replace("**", "").replace("__", "")
            
            logger.info(f"Narration generated with Gemini: {len(narration)} chars")
            return narration

        except Exception as e:
            logger.error(f"Gemini narration generation error: {e}")
            raise


class GroqStoryGenerator(StoryGenerator):
    """
    Groq-powered story generation using Llama/Mixtral models
    FREE API with generous rate limits (~30 requests/minute)
    """

    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set")
        
        import httpx
        self.client = httpx.AsyncClient(
            base_url="https://api.groq.com/openai/v1",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
        self.model = getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant')

    async def generate_story(
        self,
        prompt: str,
        max_length: int = 1000,
        style: str = "narrative",
        language: str = "vi",
    ) -> str:
        """Generate story using Groq"""
        try:
            logger.info(f"Generating {style} story with Groq in {language}")
            
            system_prompt = f"""You are a creative storyteller. Generate a {style} story in {language}. 
            The story should be engaging, vivid, and suitable for video content.
            Maximum length: {max_length} words."""

            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": max_length,
                    "temperature": 0.7,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.status_code} - {response.text}")
            
            data = response.json()
            story = data["choices"][0]["message"]["content"]
            logger.info(f"Story generated with Groq: {len(story)} chars")
            return story

        except Exception as e:
            logger.error(f"Groq story generation error: {e}")
            raise

    async def rewrite_transcript(
        self,
        original_text: str,
        segments: list[dict],
        style: str = "improved",
        preserve_meaning: bool = True,
    ) -> dict[str, Any]:
        """Rewrite transcript using Groq"""
        try:
            logger.info(f"Rewriting transcript with Groq: {style}")
            
            total_duration = segments[-1]["end"] if segments else 1
            
            system_prompt = VideoPrompts.get_transcript_rewrite_prompt(original_text, style)

            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Viết lại: {original_text}"},
                    ],
                    "max_tokens": int(len(original_text) * 1.5),
                    "temperature": 0.7,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.status_code}")
            
            data = response.json()
            rewritten_text = data["choices"][0]["message"]["content"].strip()
            
            # Segment mapping
            rewritten_segments = []
            word_idx = 0
            total_words = len(words_rewritten)
            
            for i, seg in enumerate(segments):
                seg_duration = seg["end"] - seg["start"]
                remaining_duration = total_duration - seg["start"]
                
                if remaining_duration > 0:
                    words_left = total_words - word_idx
                    proportion = seg_duration / remaining_duration
                    seg_word_count = round(proportion * words_left)
                else:
                    seg_word_count = total_words - word_idx
                    
                seg_word_count = min(seg_word_count, total_words - word_idx)
                if i == len(segments) - 1:
                    seg_word_count = total_words - word_idx

                seg_words = words_rewritten[word_idx:word_idx + seg_word_count]
                
                rewritten_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": " ".join(seg_words),
                    "original_text": seg.get("text"),
                })
                
                word_idx += seg_word_count

            return {
                "original_text": original_text,
                "rewritten_text": rewritten_text,
                "segments": rewritten_segments,
                "style": style,
            }

        except Exception as e:
            logger.error(f"Groq transcript rewriting error: {e}")
            raise

    async def generate_narration(
        self,
        topic: str,
        duration: int = 60,
        tone: str = "professional",
    ) -> str:
        """Generate narration using Groq"""
        try:
            logger.info(f"Generating {tone} narration with Groq for {duration}s")
            
            system_prompt = VideoPrompts.get_conversational_narration_prompt(topic, duration, tone)

            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Chủ đề cụ thể: {topic}"},
                    ],
                    "max_tokens": int(duration * 6),
                    "temperature": 0.8,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.status_code}")
            
            data = response.json()
            narration = data["choices"][0]["message"]["content"].strip()
            # Cleanup
            narration = narration.replace('"', '').replace("**", "").replace("__", "")
            
            logger.info(f"Narration generated with Groq: {len(narration)} chars")
            return narration

        except Exception as e:
            logger.error(f"Groq narration generation error: {e}")
            raise


class SimpleStoryGenerator(StoryGenerator):
    """
    Simple story generator that creates basic narration from title/description
    No external API required - works offline
    """

    async def generate_story(
        self,
        prompt: str,
        max_length: int = 1000,
        style: str = "narrative",
        language: str = "vi",
    ) -> str:
        """Generate simple story without AI"""
        logger.info(f"Generating simple story without AI")
        
        # Create a simple template-based story
        if language == "vi":
            return f"""Đây là câu chuyện về {prompt[:200]}. 
            Một câu chuyện hấp dẫn và đầy ý nghĩa sẽ được kể qua video này.
            Hãy cùng khám phá và tìm hiểu thêm về những điều thú vị.
            Cảm ơn bạn đã theo dõi!"""
        else:
            return f"""This is a story about {prompt[:200]}. 
            An engaging and meaningful story will be told through this video.
            Let's explore and discover more interesting things.
            Thank you for watching!"""

    async def rewrite_transcript(
        self,
        original_text: str,
        segments: list[dict],
        style: str = "improved",
        preserve_meaning: bool = True,
    ) -> dict[str, Any]:
        """Return original transcript as-is"""
        return {
            "original_text": original_text,
            "rewritten_text": original_text,  # No changes
            "segments": segments,
            "style": style,
        }

    async def generate_narration(
        self,
        topic: str,
        duration: int = 60,
        tone: str = "professional",
    ) -> str:
        """Generate simple narration from topic without AI"""
        logger.info(f"Generating simple narration for: {topic[:50]}...")
        
        # Create narration from topic using templates
        topic_clean = topic.strip()
        
        # Vietnamese narration templates based on tone
        templates = {
            "professional": f"""Xin chào các bạn! Hôm nay chúng ta sẽ cùng tìm hiểu về {topic_clean}. 
Đây là một chủ đề rất thú vị và có nhiều điều đáng để khám phá. 
Hãy cùng theo dõi video để hiểu rõ hơn nhé!
Cảm ơn các bạn đã quan tâm và theo dõi!""",
            
            "casual": f"""Hey các bạn ơi! Video này mình sẽ chia sẻ về {topic_clean}. 
Nghe hay không? Thì cùng xem nào!
Đừng quên like và subscribe nhé!""",
            
            "educational": f"""Chào mừng các bạn đến với video hôm nay! Chủ đề của chúng ta là: {topic_clean}. 
Đây là kiến thức bổ ích mà các bạn nên biết.
Hãy cùng học hỏi và khám phá thêm nhiều điều mới mẻ.
Cảm ơn các bạn đã theo dõi!""",
            
            "dramatic": f"""Bạn có bao giờ tự hỏi về {topic_clean}? 
Câu chuyện này sẽ khiến bạn ngạc nhiên! 
Hãy xem đến cuối để không bỏ lỡ điều bất ngờ nhé!""",
        }
        
        narration = templates.get(tone, templates["professional"])
        logger.info(f"Simple narration generated: {len(narration)} chars")
        return narration


class MockStoryGenerator(StoryGenerator):
    """Mock story generator for testing"""

    async def generate_story(
        self,
        prompt: str,
        max_length: int = 1000,
        style: str = "narrative",
        language: str = "vi",
    ) -> str:
        return f"Mock {style} story in {language}: {prompt[:100]}..."

    async def rewrite_transcript(
        self,
        original_text: str,
        segments: list[dict],
        style: str = "improved",
        preserve_meaning: bool = True,
    ) -> dict[str, Any]:
        return {
            "original_text": original_text,
            "rewritten_text": f"Mock rewritten in {style}: {original_text}",
            "segments": segments,
            "style": style,
        }

    async def generate_narration(
        self,
        topic: str,
        duration: int = 60,
        tone: str = "professional",
    ) -> str:
        return f"Mock {tone} narration about {topic} for {duration} seconds."


import asyncio

class CustomAIStoryGenerator(StoryGenerator):
    """
    Custom AI generator for OpenAI-compatible endpoints 
    (Useful for ngrok, local LLMs like Ollama/vLLM)
    """

    def __init__(self):
        if not settings.CUSTOM_AI_URL:
            raise ValueError("CUSTOM_AI_URL not set")
        
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key="sk-no-key-required", # Usually not needed for local
            base_url=settings.CUSTOM_AI_URL
        )
        self.model = settings.CUSTOM_AI_MODEL

    async def generate_story(self, prompt, max_length=1000, style="narrative", language="vi") -> str:
        try:
            logger.info(f"Generating story with Custom AI at {settings.CUSTOM_AI_URL}")
            system_prompt = VideoPrompts.get_conversational_narration_prompt(prompt, 60, style)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                max_tokens=max_length,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Custom AI story generation error: {e}")
            raise

    async def rewrite_transcript(self, original_text, segments, style="improved", preserve_meaning=True) -> dict:
        """Rewrite transcript using Custom AI"""
        try:
            logger.info(f"Rewriting transcript with Custom AI: {style}")
            prompt = VideoPrompts.get_transcript_rewrite_prompt(original_text, style)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"Rewrite: {original_text}"}],
                max_tokens=int(len(original_text) * 2),
                temperature=0.7
            )
            rewritten_text = response.choices[0].message.content.strip()
            return {
                "original_text": original_text,
                "rewritten_text": rewritten_text,
                "segments": segments, # Timing info can be added later if needed
                "style": style
            }
        except Exception as e:
            logger.error(f"Custom AI rewrite error: {e}")
            return {"original_text": original_text, "rewritten_text": original_text, "segments": segments, "style": style}

    async def generate_narration(self, topic, duration=60, tone="professional") -> str:
        try:
            logger.info(f"Generating narration with Custom AI for {duration}s")
            prompt = VideoPrompts.get_conversational_narration_prompt(topic, duration, tone)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"Topic: {topic}"}],
                max_tokens=int(duration * 5),
                temperature=0.8
            )
            narration = response.choices[0].message.content.strip()
            return narration.replace('"', '').replace("**", "").replace("__", "")
        except Exception as e:
            logger.error(f"Custom AI narration error: {e}")
            raise


import asyncio

async def get_story_generator(provider: str = None) -> StoryGenerator:
    """
    Get story generator with intelligent fallback:
    1. Try requested provider (if specified)
    2. Try Custom AI (if URL available)
    3. Try OpenAI (if API key available)
    4. Try Gemini (if API key available)
    5. Try Groq (if API key available) - FREE
    6. Fall back to SimpleStoryGenerator (no API needed)
    """
    provider = provider or settings.AI_PROVIDER
    
    # If specific provider requested
    if provider and provider != "auto":
        if provider == "custom" and settings.CUSTOM_AI_URL:
            try: return CustomAIStoryGenerator()
            except: pass
        elif provider == "openai" and settings.OPENAI_API_KEY:
            try: return OpenAIStoryGenerator()
            except: pass
        elif provider == "gemini" and settings.GOOGLE_API_KEY:
            try: return GeminiStoryGenerator()
            except: pass
        elif provider == "groq" and settings.GROQ_API_KEY:
            try: return GroqStoryGenerator()
            except: pass
        elif provider == "simple":
            return SimpleStoryGenerator()
    
    # Auto mode - try providers in order
    if settings.CUSTOM_AI_URL:
        try: return CustomAIStoryGenerator()
        except: pass
        
    if settings.OPENAI_API_KEY:
        try: return OpenAIStoryGenerator()
        except: pass
    
    if settings.GOOGLE_API_KEY:
        try: return GeminiStoryGenerator()
        except: pass
    
    if settings.GROQ_API_KEY:
        try: return GroqStoryGenerator()
        except: pass
    
    # Final fallback - simple generator (no API needed)
    logger.warning("No AI API keys configured, using SimpleStoryGenerator")
    return SimpleStoryGenerator()