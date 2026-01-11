"""
AI Story Generation Service
Generates creative stories, rewrites content, creates narration
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import json
from app.core.logger import logger
from app.core.config import settings


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
            
            system_prompt = f"""You are an expert content rewriter. 
            Rewrite the following transcript in {style} style. 
            IMPORTANT: The rewritten text must be compatible with the original timing.
            Original text length: {len(original_text)} characters
            Original duration: {total_duration:. 1f} seconds
            Target:  roughly {len(original_text)} characters to fit the same timing. 
            
            Preserve the core meaning:  {preserve_meaning}
            
            Return ONLY the rewritten text, nothing else."""

            response = await self.client.chat.completions. create(
                model=self. model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Rewrite this:\n\n{original_text}"},
                ],
                max_tokens=int(len(original_text) * 1.2),
                temperature=0.6,
            )

            rewritten_text = response.choices[0].message.content. strip()
            
            # Preserve original segments but with rewritten text
            # This is a simplified approach - in production, you'd want more sophisticated mapping
            words_original = original_text.split()
            words_rewritten = rewritten_text.split()
            
            rewritten_segments = []
            word_idx = 0
            
            for seg in segments:
                # Distribute rewritten words proportionally
                seg_duration = seg["end"] - seg["start"]
                total_seg_duration = segments[-1]["end"] - segments[0]["start"]
                proportion = seg_duration / total_seg_duration if total_seg_duration > 0 else 0
                
                seg_word_count = int(proportion * len(words_rewritten))
                seg_words = words_rewritten[word_idx:word_idx + seg_word_count]
                
                rewritten_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": " ".join(seg_words),
                    "original_text": seg. get("text"),
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
            logger.info(f"Generating {tone} narration for {duration}s")
            
            # Estimate:  ~150 words per minute = ~2.5 words per second
            estimated_words = int(duration * 2.5)
            
            system_prompt = f"""You are a professional video narrator. 
            Generate engaging {tone} narration for a video. 
            The narration should be approximately {estimated_words} words (for {duration} seconds of speaking).
            Make it compelling, clear, and suitable for video content in Vietnamese."""

            response = await self. client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate narration for topic: {topic}"},
                ],
                max_tokens=estimated_words,
                temperature=0.7,
            )

            narration = response.choices[0].message.content
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
        self.model = genai.GenerativeModel('gemini-pro')

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

            response = await asyncio.to_thread(self. model.generate_content, full_prompt)
            story = response.text
            logger. info(f"Story generated: {len(story)} chars")
            return story

        except Exception as e:
            logger.error(f"Gemini story generation error: {e}")
            raise

    async def rewrite_transcript(
        self,
        original_text: str,
        segments: list[dict],
        style: str = "improved",
        preserve_meaning:  bool = True,
    ) -> dict[str, Any]:
        """Rewrite transcript using Gemini"""
        try: 
            logger.info(f"Rewriting transcript with Gemini:  {style}")
            
            total_duration = segments[-1]["end"] if segments else 1
            
            prompt = f"""Rewrite this transcript in {style} style while preserving timing compatibility.
            Original duration: {total_duration:.1f} seconds
            Original text: {original_text}
            
            Requirements:
            - Keep roughly the same length (±10%)
            - Preserve meaning:  {preserve_meaning}
            - Return ONLY the rewritten text"""

            response = await asyncio. to_thread(self.model. generate_content, prompt)
            rewritten_text = response.text. strip()
            
            # Similar segment mapping as OpenAI version
            rewritten_segments = []
            words_rewritten = rewritten_text.split()
            word_idx = 0
            
            for seg in segments:
                seg_duration = seg["end"] - seg["start"]
                total_seg_duration = segments[-1]["end"] - segments[0]["start"]
                proportion = seg_duration / total_seg_duration if total_seg_duration > 0 else 0
                
                seg_word_count = int(proportion * len(words_rewritten))
                seg_words = words_rewritten[word_idx: word_idx + seg_word_count]
                
                rewritten_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": " ".join(seg_words),
                    "original_text": seg.get("text"),
                })
                
                word_idx += seg_word_count

            return {
                "original_text":  original_text,
                "rewritten_text": rewritten_text,
                "segments": rewritten_segments,
                "style":  style,
            }

        except Exception as e:
            logger. error(f"Gemini transcript rewriting error: {e}")
            raise

    async def generate_narration(
        self,
        topic: str,
        duration: int = 60,
        tone: str = "professional",
    ) -> str:
        """Generate narration using Gemini"""
        try: 
            estimated_words = int(duration * 2.5)
            
            prompt = f"""Generate {tone} video narration in Vietnamese.
            Topic: {topic}
            Duration:  {duration} seconds (~{estimated_words} words)
            Make it compelling and engaging."""

            response = await asyncio.to_thread(self.model.generate_content, prompt)
            narration = response.text
            logger.info(f"Narration generated: {len(narration)} chars")
            return narration

        except Exception as e: 
            logger.error(f"Gemini narration generation error:  {e}")
            raise


class MockStoryGenerator(StoryGenerator):
    """Mock story generator for testing"""

    async def generate_story(
        self,
        prompt: str,
        max_length: int = 1000,
        style: str = "narrative",
        language: str = "vi",
    ) -> str:
        return f"Mock {style} story in {language}:  {prompt[:100]}..."

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
        topic:  str,
        duration: int = 60,
        tone: str = "professional",
    ) -> str:
        return f"Mock {tone} narration about {topic} for {duration} seconds."


import asyncio

async def get_story_generator(provider: str = None) -> StoryGenerator:
    """Get story generator based on settings"""
    provider = provider or settings.AI_PROVIDER
    
    if provider == "openai": 
        return OpenAIStoryGenerator()
    elif provider == "gemini":
        return GeminiStoryGenerator()
    else:
        logger.warning(f"Unknown story generator: {provider}, using mock")
        return MockStoryGenerator()