"""
Stage 7: Recommendation Engine
Provides actionable optimization strategies for Title, SEO, and Audience Retention.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.logger import logger
from app.services.ai.story_generator import get_story_generator

class Recommender:
    """
    Generates strategic recommendations for video optimization.
    """

    async def generate_recommendations(
        self, 
        metadata: Dict[str, Any], 
        signals: Dict[str, Any], 
        quality_score: float
    ) -> Dict[str, Any]:
        """
        Produce a comprehensive recommendation package.
        """
        try:
            logger.info(f"Generating recommendations for: {metadata.get('title')}")
            
            # Use AI to generate qualitative recommendations
            recs = await self._generate_with_ai(metadata, signals, quality_score)
            
            return {
                "seo_optimizations": recs.get("seo", {}),
                "visual_strategies": recs.get("visuals", {}),
                "retention_tactics": recs.get("retention", []),
                "title_variants": recs.get("titles", []),
                "thumbnail_concepts": recs.get("thumbnails", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return {
                "error": str(e),
                "seo_optimizations": {"keywords": [], "description_tag": ""},
                "retention_tactics": ["Engagement hooks", "Clear structure"],
                "timestamp": datetime.now().isoformat()
            }

    async def _generate_with_ai(
        self, 
        metadata: Dict[str, Any], 
        signals: Dict[str, Any], 
        quality_score: float
    ) -> Dict[str, Any]:
        """Call AI to synthesize strategic recommendations"""
        try:
            generator = await get_story_generator()
            
            prompt = f"""
            ACT AS A WORLD-CLASS YOUTUBE GROWTH CONSULTANT.
            Video Info:
            - Title: {metadata.get('title')}
            - Description: {metadata.get('description', '')[:300]}
            - Quality Score: {quality_score}/100
            - Signals: {json.dumps(signals, indent=2)}
            
            TASK:
            1. Suggest 5 high-CTR Title Variants (Engaging, Curiosity-driven).
            2. Propose 3 Thumbnail Concepts (Visual elements, text overlays).
            3. Provide SEO Keywords and an Optimized Description Snippet.
            4. List 3 tactical ways to improve Audience Retention for this specific content.
            
            RETURN JSON ONLY:
            {{
                "titles": ["title 1", "title 2", "title 3", "title 4", "title 5"],
                "thumbnails": ["concept 1", "concept 2", "concept 3"],
                "seo": {{
                    "keywords": ["kw1", "kw2"],
                    "description_snippet": "..."
                }},
                "visuals": {{
                    "color_palette_advice": "...",
                    "overlay_priority": "..."
                }},
                "retention": ["tactic 1", "tactic 2", "tactic 3"]
            }}
            """
            
            response = await generator.generate_story(
                prompt=prompt,
                max_length=1200,
                style="json"
            )
            
            # Extract JSON
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
                
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"AI recommendation failed: {e}")
            return {
                "titles": [f"Optimized: {metadata.get('title')}"],
                "seo": {"keywords": [metadata.get('title', '')], "description_snippet": "Best video!"},
                "retention": ["Improve the first 10 seconds"]
            }

recommender = Recommender()
