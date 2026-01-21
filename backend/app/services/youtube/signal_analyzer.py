"""
YouTube Video Analyzer - Stage 2: Signal Analyzer
=================================================
Metadata fetching and engagement signal calculation.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Any

import httpx
from app.core.logger import logger
from app.core.config import settings


@dataclass
class EngagementMetrics:
    """Calculated engagement metrics"""
    like_view_ratio: float
    comment_view_ratio: float
    views_per_day: float
    days_since_upload: int
    velocity_score: float  # 0-10


@dataclass
class SignalAnalysisResult:
    """Complete signal analysis result"""
    video_id: str
    metadata: dict
    engagement_metrics: EngagementMetrics
    engagement_score: float  # 0-10
    reasoning: str


class SignalAnalyzer:
    """
    Stage 2: Metadata & Engagement Signal Analysis
    - Fetch video metadata
    - Calculate engagement ratios
    - Compute velocity scores
    """
    
    # Benchmark thresholds for scoring
    BENCHMARKS = {
        "like_view_ratio": {
            "excellent": 0.05,  # 5%+
            "good": 0.03,       # 3-5%
            "average": 0.02,    # 2-3%
            "poor": 0.01        # 1-2%
        },
        "comment_view_ratio": {
            "excellent": 0.01,  # 1%+
            "good": 0.005,      # 0.5-1%
            "average": 0.002    # 0.2-0.5%
        },
        "views_per_day": {
            "viral": 100000,
            "excellent": 50000,
            "good": 10000,
            "average": 1000
        }
    }
    
    YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def analyze(self, video_id: str, metadata: dict = None) -> SignalAnalysisResult:
        """
        Perform complete signal analysis on a video.
        
        Args:
            video_id: YouTube video ID
            metadata: Pre-fetched metadata (optional)
        """
        # Fetch metadata if not provided
        if not metadata:
            metadata = await self._fetch_metadata(video_id)
        
        if not metadata:
            raise ValueError(f"Could not fetch metadata for {video_id}")
        
        # Calculate engagement metrics
        metrics = self._calculate_metrics(metadata)
        
        # Calculate overall engagement score
        score, reasoning = self._calculate_score(metrics, metadata)
        
        return SignalAnalysisResult(
            video_id=video_id,
            metadata=metadata,
            engagement_metrics=metrics,
            engagement_score=score,
            reasoning=reasoning
        )
    
    async def _fetch_metadata(self, video_id: str) -> Optional[dict]:
        """Fetch video metadata from YouTube API"""
        try:
            params = {
                "part": "snippet,contentDetails,statistics",
                "id": video_id,
                "key": self.api_key
            }
            
            response = await self.client.get(
                f"{self.YOUTUBE_API_BASE}/videos",
                params=params
            )
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}")
                return None
            
            data = response.json()
            
            if not data.get("items"):
                return None
            
            item = data["items"][0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            
            return {
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_id": snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId", "")
            }
            
        except Exception as e:
            logger.error(f"Error fetching metadata: {e}")
            return None
    
    def _calculate_metrics(self, metadata: dict) -> EngagementMetrics:
        """Calculate engagement metrics from metadata"""
        views = metadata.get("view_count", 0)
        likes = metadata.get("like_count", 0)
        comments = metadata.get("comment_count", 0)
        published_at = metadata.get("published_at", "")
        
        # Calculate ratios (avoid division by zero)
        like_view_ratio = likes / views if views > 0 else 0
        comment_view_ratio = comments / views if views > 0 else 0
        
        # Calculate days since upload
        days_since_upload = self._calculate_days_since(published_at)
        
        # Calculate views per day
        views_per_day = views / max(days_since_upload, 1)
        
        # Calculate velocity score (0-10)
        velocity_score = self._score_velocity(views_per_day)
        
        return EngagementMetrics(
            like_view_ratio=round(like_view_ratio, 6),
            comment_view_ratio=round(comment_view_ratio, 6),
            views_per_day=round(views_per_day, 2),
            days_since_upload=days_since_upload,
            velocity_score=velocity_score
        )
    
    def _calculate_days_since(self, published_at: str) -> int:
        """Calculate days since video was published"""
        if not published_at:
            return 0
        
        try:
            # Parse ISO 8601 format
            pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = now - pub_date
            return max(1, delta.days)
        except Exception:
            return 1
    
    def _score_velocity(self, views_per_day: float) -> float:
        """Score velocity on 0-10 scale"""
        benchmarks = self.BENCHMARKS["views_per_day"]
        
        if views_per_day >= benchmarks["viral"]:
            return 10.0
        elif views_per_day >= benchmarks["excellent"]:
            return 8.0 + (views_per_day - benchmarks["excellent"]) / (benchmarks["viral"] - benchmarks["excellent"]) * 2
        elif views_per_day >= benchmarks["good"]:
            return 6.0 + (views_per_day - benchmarks["good"]) / (benchmarks["excellent"] - benchmarks["good"]) * 2
        elif views_per_day >= benchmarks["average"]:
            return 4.0 + (views_per_day - benchmarks["average"]) / (benchmarks["good"] - benchmarks["average"]) * 2
        else:
            return max(0, views_per_day / benchmarks["average"] * 4)
    
    def _calculate_score(self, metrics: EngagementMetrics, metadata: dict) -> tuple[float, str]:
        """Calculate overall engagement score with reasoning"""
        scores = []
        reasons = []
        
        # Like/View Ratio Score (weight: 30%)
        like_score = self._score_ratio(
            metrics.like_view_ratio,
            self.BENCHMARKS["like_view_ratio"]
        )
        scores.append(("Like Ratio", like_score, 0.30))
        
        if like_score >= 8:
            reasons.append(f"✅ Excellent like ratio ({metrics.like_view_ratio:.2%})")
        elif like_score >= 6:
            reasons.append(f"👍 Good like ratio ({metrics.like_view_ratio:.2%})")
        else:
            reasons.append(f"⚠️ Low like ratio ({metrics.like_view_ratio:.2%})")
        
        # Comment/View Ratio Score (weight: 25%)
        comment_score = self._score_ratio(
            metrics.comment_view_ratio,
            self.BENCHMARKS["comment_view_ratio"]
        )
        scores.append(("Comment Ratio", comment_score, 0.25))
        
        if comment_score >= 8:
            reasons.append(f"✅ High engagement ({metrics.comment_view_ratio:.3%} comments)")
        elif comment_score < 5:
            reasons.append(f"⚠️ Low comments ({metrics.comment_view_ratio:.3%})")
        
        # Velocity Score (weight: 30%)
        scores.append(("Velocity", metrics.velocity_score, 0.30))
        
        if metrics.velocity_score >= 8:
            reasons.append(f"🔥 Viral velocity ({metrics.views_per_day:,.0f} views/day)")
        elif metrics.velocity_score >= 6:
            reasons.append(f"📈 Good growth ({metrics.views_per_day:,.0f} views/day)")
        
        # Recency Score (weight: 15%)
        recency_score = self._score_recency(metrics.days_since_upload)
        scores.append(("Recency", recency_score, 0.15))
        
        if metrics.days_since_upload <= 7:
            reasons.append(f"🆕 Fresh content ({metrics.days_since_upload} days old)")
        elif metrics.days_since_upload > 365:
            reasons.append(f"📅 Evergreen content ({metrics.days_since_upload} days old)")
        
        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in scores)
        total_score = round(min(10, max(0, total_score)), 1)
        
        reasoning = " | ".join(reasons)
        
        return total_score, reasoning
    
    def _score_ratio(self, value: float, benchmarks: dict) -> float:
        """Score a ratio based on benchmarks"""
        if value >= benchmarks.get("excellent", float("inf")):
            return 10.0
        elif value >= benchmarks.get("good", float("inf")):
            return 8.0
        elif value >= benchmarks.get("average", float("inf")):
            return 6.0
        elif value >= benchmarks.get("poor", 0):
            return 4.0
        else:
            return 2.0
    
    def _score_recency(self, days: int) -> float:
        """Score based on content recency"""
        if days <= 7:
            return 10.0  # Very fresh
        elif days <= 30:
            return 8.0   # Recent
        elif days <= 90:
            return 6.0   # Moderate
        elif days <= 365:
            return 5.0   # Older but may be evergreen
        else:
            return 4.0   # Old content
    
    async def close(self):
        await self.client.aclose()


# Singleton instance
signal_analyzer = SignalAnalyzer()
