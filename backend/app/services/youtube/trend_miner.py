"""
Stage 5: Trend & Similar Content Mining
Research current trends and high-performing content in the video's niche.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

from app.core.logger import logger
from app.core.config import settings
from app.services.ai.story_generator import get_story_generator

class TrendMiner:
    """
    Analyzes YouTube trends and finds similar high-performing content
    for context and competitive analysis.
    """

    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        
    async def mine_trends(self, metadata: Dict[str, Any], topics: List[str]) -> Dict[str, Any]:
        """
        Mine trends and similar content based on video metadata and topics.
        """
        try:
            logger.info(f"Mining trends for topics: {topics[:3]}")
            
            # 1. Search for similar high-performing videos
            similar_videos = await self._search_similar_content(topics)
            
            # 2. Analyze search results for trends using AI
            trend_analysis = await self._analyze_trends_with_ai(metadata, similar_videos, topics)
            
            return {
                "similar_content": similar_videos,
                "trend_insights": trend_analysis.get("insights", []),
                "viral_hooks_suggestions": trend_analysis.get("hooks", []),
                "competitive_edge": trend_analysis.get("competitive_edge", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Trend mining error: {e}")
            return {
                "error": str(e),
                "similar_content": [],
                "trend_insights": ["Could not fetch real-time trends"],
                "timestamp": datetime.now().isoformat()
            }

    async def _search_similar_content(self, topics: List[str]) -> List[Dict[str, Any]]:
        """Search for top performing videos in the same niche"""
        if not self.api_key:
            return []
            
        import httpx
        query = " ".join(topics[:3])
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "key": self.api_key,
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "viewCount", # Get popular ones
            "maxResults": 5,
            "relevanceLanguage": "vi",
            "publishedAfter": (datetime.utcnow() - timedelta(days=90)).isoformat() + "Z" # Recent 3 months
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("items", []):
                    results.append({
                        "id": item["id"]["videoId"],
                        "title": item["snippet"]["title"],
                        "channel": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"],
                        "thumbnail": item["snippet"]["thumbnails"]["default"]["url"]
                    })
                return results
            else:
                logger.error(f"YouTube search error: {response.status_code} - {response.text}")
                return []

    async def _analyze_trends_with_ai(
        self, 
        metadata: Dict[str, Any], 
        similar_videos: List[Dict[str, Any]],
        topics: List[str]
    ) -> Dict[str, Any]:
        """Synthesize trend data using AI"""
        try:
            generator = await get_story_generator()
            
            prompt = f"""
            ACT AS A YOUTUBE STRATEGIST & TREND ANALYST.
            Original Video Title: {metadata.get('title')}
            Topics: {', '.join(topics)}
            
            SIMILAR HIGH-PERFORMING CONTENT FOUND:
            {json.dumps(similar_videos, indent=2)}
            
            TASK:
            1. Identify current trends in this niche based on titles and topics.
            2. Suggest 3 viral "Trend Integration" ideas for the user's video.
            3. Provide 3 high-retention hook ideas.
            4. Explain what the "Competitive Edge" for this video could be.
            
            RETURN JSON ONLY:
            {{
                "insights": ["insight 1", "insight 2"],
                "hooks": ["hook 1", "hook 2"],
                "competitive_edge": "Detailed explanation"
            }}
            """
            
            response = await generator.generate_story(
                prompt=prompt,
                max_length=800,
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
            logger.warning(f"AI trend analysis failed: {e}")
            return {
                "insights": ["Trending topics include " + ", ".join(topics[:2])],
                "hooks": ["How to fix " + topics[0]],
                "competitive_edge": "Unique perspective on " + topics[0]
            }

trend_miner = TrendMiner()
