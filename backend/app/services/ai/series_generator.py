
"""
Series Story Generator - AI logic for multi-part video series
"""

import json
from typing import Optional, List, Dict, Any
from app.core.logger import logger
from app.core.config import settings
from app.services.ai.story_generator import StoryGenerator, get_story_generator

class SeriesStoryGenerator:
    """
    Specialized generator for multi-part video series.
    Orchestrates the creation of outline, hooks, scripts, and cliffhangers.
    """

    def __init__(self, provider: str = "auto"):
        self.provider = provider

    async def _get_generator(self) -> StoryGenerator:
        return await get_story_generator(self.provider)

    async def generate_series_outline(
        self,
        topic: str,
        num_parts: int,
        total_duration: int,
        style: str = "viral"
    ) -> Dict[str, Any]:
        """
        Generate a master plan for the series to ensure continuity.
        Returns a JSON structure with hooks, main plot points, and endings for each part.
        """
        try:
            generator = await self._get_generator()
            part_duration = total_duration // num_parts
            
            prompt = f"""
            ACT AS A MASTER STORYTELLER & SERIES PLANNER.
            Create a detailed outline for a {num_parts}-part video series about: "{topic}".
            Total duration: {total_duration}s (~{part_duration}s per part).
            Style: {style} (Engaging, Viral, Emotional).

            STRICT STRUCTURE REQUIRED:
            - The story must be CONTINUOUS (Part 2 starts where Part 1 ended).
            - Part 1: High-stakes Introduction -> Setting the Scene -> First Conflict -> Cliffhanger.
            - Middle Parts: Escalating tension -> New revelations -> Cliffhanger.
            - Final Part: Climax -> Resolution -> Reflective/Twist Ending.

            OUTPUT FORMAT (JSON ONLY):
            {{
                "title": "A catchy title for the whole series",
                "overall_theme": "The core theme/emotion",
                "parts": [
                    {{
                        "part_number": 1,
                        "hook": "Under 10 words, extremely catchy opening line",
                        "main_event": "Key event happening in this part",
                        "cliffhanger": "The suspenseful moment this part ends on"
                    }},
                    ... (for all {num_parts} parts)
                ]
            }}
            
            RETURN ONLY VALID JSON. NO MARKDOWN.
            """

            # Use the raw generate method from the underlying provider/client if possible
            # But StoryGenerator abstraction doesn't have a generic "generate_json" method.
            # We will use generate_story and parse it, or rely on the provider's text output being JSON-like.
            
            # For now, we ask for text and try to parse/clean it.
            response_text = await generator.generate_story(
                prompt=prompt,
                max_length=1500,
                style="json_structure" 
            )
            
            # Clean up response to get JSON
            json_str = response_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif json_str.startswith("```"):
                json_str = json_str.split("```")[1].split("```")[0].strip()
                
            outline = json.loads(json_str)
            return outline

        except Exception as e:
            logger.error(f"Series outline generation error: {e}")
            # Fallback outline
            return {
                "title": f"Series: {topic}",
                "overall_theme": "General",
                "parts": [
                    {
                        "part_number": i+1, 
                        "hook": f"Part {i+1} of {topic}", 
                        "main_event": "Content", 
                        "cliffhanger": "Watch next part!"
                    } for i in range(num_parts)
                ]
            }

    async def generate_part_script(
        self,
        part_index: int,
        total_parts: int,
        outline: Dict[str, Any],
        duration: int,
        prev_context: str = ""
    ) -> str:
        """
        Generate the actual narration script for a specific part.
        """
        try:
            generator = await self._get_generator()
            part_info = outline["parts"][part_index]
            is_first = (part_index == 0)
            is_last = (part_index == total_parts - 1)
            
            style_prompt = """
            TONE & VOICE INSTRUCTIONS:
            - Persona: 'The Cynical Observer' (Detailed, slightly skeptical, engaging) OR 'The Warm Storyteller' (if emotional).
            - Format: Vietnamese Spoken Language (Văn nói), natural breathing rhythm.
            - NO: "Hello friends", "Welcome back". Start immediately!
            """

            structure_prompt = ""
            if is_first:
                structure_prompt = f"""
                STRUCTURE (Part 1/{total_parts}):
                1. HOOK: "{part_info['hook']}" (Use this exact hook or improve it).
                2. BODY: Introduce the world/problem. Focus on {part_info['main_event']}.
                3. CLIFFHANGER: End abruptly on: "{part_info['cliffhanger']}".
                """
            elif is_last:
                structure_prompt = f"""
                STRUCTURE (Part {part_index+1}/{total_parts} - LAST PART):
                1. RECAP: "Ở phần trước..." (Quick 1-sentence recap).
                2. BODY: The Climax! Resolve {part_info['main_event']}.
                3. ENDING: A powerful, lingering conclusion. No "Like and Subscribe".
                """
            else:
                 structure_prompt = f"""
                STRUCTURE (Part {part_index+1}/{total_parts}):
                1. RECAP: "Ở phần trước..." (Quick 1-sentence recap).
                2. BODY: Develop the story. Focus on {part_info['main_event']}.
                3. CLIFFHANGER: drive suspense to: "{part_info['cliffhanger']}".
                """

            full_prompt = f"""
            WRITE SCRIPT FOR PART {part_index+1} OF VIDEO SERIES: "{outline['title']}".
            Target Duration: {duration} seconds (~{int(duration*2.5)} words).
            
            {style_prompt}
            
            {structure_prompt}
            
            CONTEXT FROM OUTLINE:
            Theme: {outline['overall_theme']}
            
            OUTPUT ONLY THE RAW VIETNAMESE SCRIPT.
            """
            
            script = await generator.generate_story(
                prompt=full_prompt,
                max_length=int(duration * 4), # ample token limit
                style="script"
            )
            
            return script.replace('"', '').strip()

        except Exception as e:
            logger.error(f"Part script generation error: {e}")
            return f"Nội dung phần {part_index+1}. {outline.get('title', 'Video')} là một chủ đề thú vị."

series_generator = SeriesStoryGenerator()
