"""
YouTube Video Analyzer - 10-Stage Pipeline
==========================================
Stage 1: Video Ingestion
- URL validation
- Video/Playlist/Channel detection
- Download with yt-dlp
- Metadata caching
"""

import asyncio
import re
import json
import time
from pathlib import Path
from typing import Optional, Any, Literal
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse, parse_qs

import httpx
from app.core.logger import logger
from app.core.config import settings


class InputType(str, Enum):
    VIDEO = "video"
    PLAYLIST = "playlist"
    CHANNEL = "channel"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    is_valid: bool
    is_available: bool
    is_age_restricted: bool
    region_blocked: list[str]
    duration_valid: bool
    duration_seconds: int
    can_download: bool
    error_message: Optional[str] = None


@dataclass
class VideoMetadata:
    video_id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    duration_seconds: int
    view_count: int
    like_count: int
    comment_count: int
    published_at: str
    thumbnail_url: str
    tags: list[str]
    category_id: str


@dataclass
class IngestionResult:
    success: bool
    video_id: str
    local_path: Optional[Path]
    metadata: Optional[VideoMetadata]
    download_time: float
    error: Optional[str] = None


class VideoIngestionService:
    """
    Stage 1: Video Ingestion
    - Validates URLs
    - Downloads videos with yt-dlp
    - Caches metadata
    - Handles playlists and channels
    """
    
    MAX_DURATION = 3600  # 60 minutes
    YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
        self._metadata_cache: dict[str, VideoMetadata] = {}
    
    def detect_input_type(self, url: str) -> tuple[InputType, str]:
        """Detect if URL is video, playlist, or channel"""
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        
        # Video URL patterns
        if "watch" in parsed.path:
            video_id = query.get("v", [None])[0]
            if video_id:
                return InputType.VIDEO, video_id
        
        # Short URL (youtu.be)
        if parsed.netloc == "youtu.be":
            video_id = parsed.path.strip("/")
            if video_id:
                return InputType.VIDEO, video_id
        
        # Playlist
        if "playlist" in parsed.path or "list" in query:
            playlist_id = query.get("list", [None])[0]
            if playlist_id:
                return InputType.PLAYLIST, playlist_id
        
        # Channel URL patterns
        channel_patterns = [
            r"youtube\.com/@([^/]+)",           # @username
            r"youtube\.com/channel/([^/]+)",    # channel/ID
            r"youtube\.com/c/([^/]+)",          # /c/name
            r"youtube\.com/user/([^/]+)",       # /user/name
        ]
        
        for pattern in channel_patterns:
            match = re.search(pattern, url)
            if match:
                return InputType.CHANNEL, match.group(1)
        
        return InputType.UNKNOWN, ""
    
    async def validate_video(self, video_id: str) -> ValidationResult:
        """Validate video availability and restrictions"""
        try:
            # Debug: Log API key status
            if not self.api_key:
                logger.error(f"YOUTUBE_API_KEY is not set! settings.YOUTUBE_API_KEY = {settings.YOUTUBE_API_KEY}")
                return ValidationResult(
                    is_valid=False,
                    is_available=False,
                    is_age_restricted=False,
                    region_blocked=[],
                    duration_valid=False,
                    duration_seconds=0,
                    can_download=False,
                    error_message="YOUTUBE_API_KEY is not configured"
                )
            
            # Get video details from YouTube API
            params = {
                "part": "snippet,contentDetails,status,statistics",
                "id": video_id,
                "key": self.api_key
            }
            
            logger.info(f"Validating video {video_id} with API key: {self.api_key[:10]}...")
            
            response = await self.client.get(
                f"{self.YOUTUBE_API_BASE}/videos",
                params=params
            )
            
            logger.info(f"API response status: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text[:500] if response.text else "No details"
                logger.error(f"API error: {response.status_code} - {error_detail}")
                return ValidationResult(
                    is_valid=False,
                    is_available=False,
                    is_age_restricted=False,
                    region_blocked=[],
                    duration_valid=False,
                    duration_seconds=0,
                    can_download=False,
                    error_message=f"API error: {response.status_code} - {error_detail}"
                )
            
            data = response.json()
            
            if not data.get("items"):
                logger.warning(f"Video {video_id} not found in API response")
                return ValidationResult(
                    is_valid=False,
                    is_available=False,
                    is_age_restricted=False,
                    region_blocked=[],
                    duration_valid=False,
                    duration_seconds=0,
                    can_download=False,
                    error_message="Video not found or private"
                )
            
            item = data["items"][0]
            status = item.get("status", {})
            content_details = item.get("contentDetails", {})
            
            # Parse duration (PT1H30M45S format)
            duration_str = content_details.get("duration", "PT0S")
            duration_seconds = self._parse_duration(duration_str)
            
            # Check restrictions
            is_age_restricted = content_details.get("contentRating", {}).get("ytRating") == "ytAgeRestricted"
            
            region_restriction = content_details.get("regionRestriction", {})
            blocked_regions = region_restriction.get("blocked", [])
            
            # Check privacy
            is_available = status.get("privacyStatus") == "public"
            
            # Duration check
            duration_valid = duration_seconds <= self.MAX_DURATION
            
            can_download = (
                is_available and 
                not is_age_restricted and 
                duration_valid
            )
            
            return ValidationResult(
                is_valid=True,
                is_available=is_available,
                is_age_restricted=is_age_restricted,
                region_blocked=blocked_regions,
                duration_valid=duration_valid,
                duration_seconds=duration_seconds,
                can_download=can_download,
                error_message=None if can_download else self._get_validation_error(
                    is_available, is_age_restricted, duration_valid, duration_seconds
                )
            )
            
        except Exception as e:
            logger.error(f"Validation error for {video_id}: {e}")
            return ValidationResult(
                is_valid=False,
                is_available=False,
                is_age_restricted=False,
                region_blocked=[],
                duration_valid=False,
                duration_seconds=0,
                can_download=False,
                error_message=str(e)
            )
    
    async def get_video_metadata(self, video_id: str) -> Optional[VideoMetadata]:
        """Get video metadata, with caching"""
        # Check cache first
        if video_id in self._metadata_cache:
            logger.info(f"Using cached metadata for {video_id}")
            return self._metadata_cache[video_id]
        
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
                logger.error(f"Failed to get metadata: {response.status_code}")
                return None
            
            data = response.json()
            
            if not data.get("items"):
                return None
            
            item = data["items"][0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})
            
            metadata = VideoMetadata(
                video_id=video_id,
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                channel_id=snippet.get("channelId", ""),
                channel_title=snippet.get("channelTitle", ""),
                duration_seconds=self._parse_duration(content.get("duration", "PT0S")),
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(stats.get("likeCount", 0)),
                comment_count=int(stats.get("commentCount", 0)),
                published_at=snippet.get("publishedAt", ""),
                thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                tags=snippet.get("tags", []),
                category_id=snippet.get("categoryId", "")
            )
            
            # Cache metadata
            self._metadata_cache[video_id] = metadata
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting metadata for {video_id}: {e}")
            return None
    
    async def download_video(
        self,
        video_id: str,
        output_dir: Path
    ) -> IngestionResult:
        """Download video using yt-dlp"""
        import yt_dlp
        
        start_time = time.time()
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            # Validate first
            validation = await self.validate_video(video_id)
            if not validation.can_download:
                return IngestionResult(
                    success=False,
                    video_id=video_id,
                    local_path=None,
                    metadata=None,
                    download_time=0,
                    error=validation.error_message
                )
            
            # Get metadata
            metadata = await self.get_video_metadata(video_id)
            
            # Setup output path
            output_dir.mkdir(parents=True, exist_ok=True)
            output_template = str(output_dir / f"yt_{video_id}.%(ext)s")
            
            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
                "merge_output_format": "mp4",
                "postprocessors": [{
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }],
            }
            
            # Download in thread pool
            loop = asyncio.get_event_loop()
            
            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            await loop.run_in_executor(None, _download)
            
            # Find downloaded file
            output_path = output_dir / f"yt_{video_id}.mp4"
            
            if not output_path.exists():
                # Try to find with different extension
                for ext in ["mp4", "webm", "mkv"]:
                    p = output_dir / f"yt_{video_id}.{ext}"
                    if p.exists():
                        output_path = p
                        break
            
            download_time = time.time() - start_time
            
            if output_path.exists():
                logger.info(f"Downloaded {video_id} in {download_time:.2f}s")
                return IngestionResult(
                    success=True,
                    video_id=video_id,
                    local_path=output_path,
                    metadata=metadata,
                    download_time=download_time
                )
            else:
                return IngestionResult(
                    success=False,
                    video_id=video_id,
                    local_path=None,
                    metadata=metadata,
                    download_time=download_time,
                    error="Download completed but file not found"
                )
                
        except Exception as e:
            logger.error(f"Download error for {video_id}: {e}")
            return IngestionResult(
                success=False,
                video_id=video_id,
                local_path=None,
                metadata=None,
                download_time=time.time() - start_time,
                error=str(e)
            )
    
    async def get_playlist_videos(self, playlist_id: str, max_results: int = 50) -> list[str]:
        """Get all video IDs from a playlist"""
        video_ids = []
        next_page_token = None
        
        while len(video_ids) < max_results:
            params = {
                "part": "contentDetails",
                "playlistId": playlist_id,
                "maxResults": min(50, max_results - len(video_ids)),
                "key": self.api_key
            }
            
            if next_page_token:
                params["pageToken"] = next_page_token
            
            response = await self.client.get(
                f"{self.YOUTUBE_API_BASE}/playlistItems",
                params=params
            )
            
            if response.status_code != 200:
                break
            
            data = response.json()
            
            for item in data.get("items", []):
                vid = item.get("contentDetails", {}).get("videoId")
                if vid:
                    video_ids.append(vid)
            
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
        
        return video_ids
    
    async def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 50,
        order: str = "viewCount"  # date, viewCount, rating
    ) -> list[str]:
        """Get video IDs from a channel"""
        # First, get uploads playlist ID
        params = {
            "part": "contentDetails",
            "id": channel_id,
            "key": self.api_key
        }
        
        # Handle @username format
        if channel_id.startswith("@"):
            params = {
                "part": "contentDetails",
                "forHandle": channel_id,
                "key": self.api_key
            }
        
        response = await self.client.get(
            f"{self.YOUTUBE_API_BASE}/channels",
            params=params
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get channel: {response.status_code}")
            return []
        
        data = response.json()
        
        if not data.get("items"):
            return []
        
        uploads_playlist_id = (
            data["items"][0]
            .get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )
        
        if not uploads_playlist_id:
            return []
        
        return await self.get_playlist_videos(uploads_playlist_id, max_results)
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to seconds"""
        import re
        
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _get_validation_error(
        self,
        is_available: bool,
        is_age_restricted: bool,
        duration_valid: bool,
        duration_seconds: int
    ) -> str:
        if not is_available:
            return "Video is private or unavailable"
        if is_age_restricted:
            return "Video is age-restricted"
        if not duration_valid:
            return f"Video too long: {duration_seconds}s (max: {self.MAX_DURATION}s)"
        return "Unknown validation error"
    
    async def close(self):
        await self.client.aclose()


# Singleton instance
ingestion_service = VideoIngestionService()
