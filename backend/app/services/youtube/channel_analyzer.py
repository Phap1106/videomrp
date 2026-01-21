"""
YouTube Channel Analyzer
========================
Fetches channel-level metrics to assess authority and brand quality.
"""

from typing import Dict, Any, Optional
import httpx
from app.core.logger import logger
from app.core.config import settings
from pydantic import BaseModel

class ChannelVideoInfo(BaseModel):
    id: str
    title: str
    published_at: str
    view_count: int

class ChannelInfo(BaseModel):
    title: str
    id: str
    view_count: int
    subscriber_count: int
    video_count: int

class ChannelAnalysis(BaseModel):
    channel_score: float
    metrics: Dict[str, Any]
    branding: Dict[str, Any]
    reasoning: str

class ChannelAnalyzer:
    """
    Analyzes YouTube channel metrics to determine authority and trust.
    """
    
    YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)

    async def analyze(self, channel_id: str) -> Dict[str, Any]:
        """
        Fetch channel statistics and calculate authority score.
        """
        try:
            if not self.api_key:
                return {"error": "API Key missing", "channel_score": 5.0}

            params = {
                "part": "statistics,snippet,brandingSettings",
                "id": channel_id,
                "key": self.api_key
            }
            
            response = await self.client.get(
                f"{self.YOUTUBE_API_BASE}/channels",
                params=params
            )
            
            if response.status_code != 200:
                logger.error(f"Channel API error: {response.status_code}")
                return {"channel_score": 5.0, "reasoning": "Could not fetch channel data"}
                
            data = response.json()
            if not data.get("items"):
                return {"channel_score": 5.0, "reasoning": "Channel not found"}
                
            item = data["items"][0]
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            
            subs = int(stats.get("subscriberCount", 0))
            views = int(stats.get("viewCount", 0))
            vids = int(stats.get("videoCount", 0))
            
            # Simple authority calculation (1-10)
            # Logarithmic scale for subscribers
            import math
            if subs > 0:
                sub_score = min(10, math.log10(subs) * 1.5) # 1k=4.5, 10k=6, 100k=7.5, 1M=9
            else:
                sub_score = 1.0
                
            # Content consistency
            vid_score = min(10, vids / 50) # 500+ vids = 10
            
            # Total view authority
            view_score = min(10, math.log10(views) / 8 * 10) if views > 0 else 1 # 100M views = 10
            
            final_authority = (sub_score * 0.5) + (vid_score * 0.2) + (view_score * 0.3)
            
            return {
                "channel_score": round(final_authority, 1),
                "metrics": {
                    "subscribers": subs,
                    "total_views": views,
                    "video_count": vids,
                    "hidden_subscriber_count": stats.get("hiddenSubscriberCount", False)
                },
                "branding": {
                    "title": snippet.get("title"),
                    "published_at": snippet.get("publishedAt")
                },
                "reasoning": f"Authority based on {subs:,} subscribers and {views:,} lifetime views."
            }
            
        except Exception as e:
            logger.error(f"Channel analysis error: {e}")
            return {"channel_score": 5.0, "reasoning": f"Analysis failed: {str(e)}"}
            
    async def close(self):
        await self.client.aclose()

channel_analyzer = ChannelAnalyzer()
