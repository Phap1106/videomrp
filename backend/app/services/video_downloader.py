import httpx
import yt_dlp
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import re
import time
from loguru import logger
from urllib.parse import urlparse, parse_qs

from app.services.platform_detector import PlatformDetector
from app.core.config import settings


class VideoDownloader:
    """Download videos from various platforms"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        self.detector = PlatformDetector()
        
    async def download(self, url: str, output_dir: Path) -> Dict[str, Any]:
        """Download video from URL"""
        platform = self.detector.detect(url)
        logger.info(f"Downloading from {platform}: {url}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        
        try:
            if platform == "tiktok":
                result = await self._download_tiktok(url, output_dir, timestamp)
            elif platform == "douyin":
                result = await self._download_douyin(url, output_dir, timestamp)
            elif platform == "youtube":
                result = await self._download_youtube(url, output_dir, timestamp)
            elif platform == "instagram":
                result = await self._download_instagram(url, output_dir, timestamp)
            else:
                result = await self._download_generic(url, output_dir, timestamp)
            
            result["platform"] = platform.value
            return result
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise
    
    async def _download_tiktok(self, url: str, output_dir: Path, timestamp: int) -> Dict[str, Any]:
        """Download TikTok video without watermark"""
        video_info = {}
        
        try:
            # Try TikTok API
            api_url = f"https://www.tikwm.com/api/?url={url}"
            async with self.client as client:
                response = await client.get(api_url)
                data = response.json()
                
                if data.get("code") == 1:
                    video_data = data["data"]
                    video_url = video_data.get("play") or video_data.get("hdplay")
                    
                    if video_url:
                        # Download video
                        output_path = output_dir / f"tiktok_{timestamp}.mp4"
                        await self._download_file(video_url, output_path)
                        
                        video_info = {
                            "path": str(output_path),
                            "title": video_data.get("title", ""),
                            "author": video_data.get("author", {}).get("nickname", ""),
                            "duration": video_data.get("duration", 0),
                            "resolution": "720p",
                            "no_watermark": True,
                            "method": "tikwm_api"
                        }
                        return video_info
        except Exception as e:
            logger.warning(f"TikTok API failed: {e}")
        
        # Fallback to yt-dlp
        try:
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': str(output_dir / 'tiktok_%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = output_dir / f"tiktok_{info['id']}.mp4"
                
                video_info = {
                    "path": str(video_path),
                    "title": info.get('title', ''),
                    "author": info.get('uploader', ''),
                    "duration": info.get('duration', 0),
                    "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
                    "no_watermark": False,
                    "method": "yt_dlp"
                }
                return video_info
                
        except Exception as e:
            logger.error(f"TikTok download failed: {e}")
            raise Exception(f"Failed to download TikTok video: {str(e)}")
    
    async def _download_douyin(self, url: str, output_dir: Path, timestamp: int) -> Dict[str, Any]:
        """Download Douyin video"""
        try:
            api_url = f"https://douyin.wtf/api?url={url}"
            async with self.client as client:
                response = await client.get(api_url)
                data = response.json()
                
                if data.get("status") == "success":
                    video_data = data["video_data"]
                    video_url = video_data.get("nwm_video_url") or video_data.get("video_url")
                    
                    if video_url:
                        output_path = output_dir / f"douyin_{timestamp}.mp4"
                        await self._download_file(video_url, output_path)
                        
                        return {
                            "path": str(output_path),
                            "title": video_data.get("desc", ""),
                            "author": video_data.get("author", {}).get("nickname", ""),
                            "duration": video_data.get("duration", 0),
                            "resolution": "720p",
                            "no_watermark": True,
                            "method": "douyin_api"
                        }
        except Exception as e:
            logger.warning(f"Douyin API failed: {e}")
        
        # Fallback to generic download
        return await self._download_generic(url, output_dir, timestamp)
    
    async def _download_youtube(self, url: str, output_dir: Path, timestamp: int) -> Dict[str, Any]:
        """Download YouTube video"""
        try:
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': str(output_dir / 'youtube_%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writeinfojson': True,
                'writethumbnail': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en', 'vi'],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = output_dir / f"youtube_{info['id']}.mp4"
                
                # Get thumbnail if available
                thumbnail_path = None
                if info.get('thumbnail'):
                    thumbnail_path = output_dir / f"youtube_{info['id']}.jpg"
                    await self._download_file(info['thumbnail'], thumbnail_path)
                
                return {
                    "path": str(video_path),
                    "title": info.get('title', ''),
                    "author": info.get('uploader', ''),
                    "duration": info.get('duration', 0),
                    "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
                    "description": info.get('description', ''),
                    "thumbnail": str(thumbnail_path) if thumbnail_path else None,
                    "subtitles": info.get('subtitles', {}),
                    "method": "yt_dlp"
                }
                
        except Exception as e:
            logger.error(f"YouTube download failed: {e}")
            raise Exception(f"Failed to download YouTube video: {str(e)}")
    
    async def _download_instagram(self, url: str, output_dir: Path, timestamp: int) -> Dict[str, Any]:
        """Download Instagram video"""
        try:
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': str(output_dir / 'instagram_%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = output_dir / f"instagram_{info.get('id', timestamp)}.mp4"
                
                return {
                    "path": str(video_path),
                    "title": info.get('title', ''),
                    "author": info.get('uploader', ''),
                    "duration": info.get('duration', 0),
                    "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
                    "method": "yt_dlp"
                }
                
        except Exception as e:
            logger.error(f"Instagram download failed: {e}")
            raise Exception(f"Failed to download Instagram video: {str(e)}")
    
    async def _download_generic(self, url: str, output_dir: Path, timestamp: int) -> Dict[str, Any]:
        """Download generic video"""
        try:
            # Extract filename from URL
            parsed = urlparse(url)
            filename = parsed.path.split('/')[-1] or f"video_{timestamp}"
            if not filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
                filename = f"{filename}.mp4"
            
            output_path = output_dir / filename
            
            # Download file
            await self._download_file(url, output_path)
            
            return {
                "path": str(output_path),
                "title": filename,
                "author": "",
                "duration": 0,
                "resolution": "unknown",
                "method": "direct_download"
            }
            
        except Exception as e:
            logger.error(f"Generic download failed: {e}")
            raise Exception(f"Failed to download video: {str(e)}")
    
    async def _download_file(self, url: str, output_path: Path):
        """Download file from URL"""
        async with self.client.stream('GET', url) as response:
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if int(progress) % 10 == 0:
                            logger.debug(f"Download progress: {progress:.1f}%")
            
            logger.info(f"Downloaded {downloaded} bytes to {output_path}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()