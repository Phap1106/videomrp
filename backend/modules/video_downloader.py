import os
import re
import json
import logging
import tempfile
import yt_dlp
from urllib.parse import urlparse
from typing import Dict, Optional, Tuple
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)

class VideoDownloader:
    """Download videos from social media platforms"""
    
    def __init__(self):
        self.output_dir = Config.UPLOAD_FOLDER
        self.timeout = Config.DOWNLOAD_TIMEOUT
        self.max_retries = Config.MAX_RETRIES
        
        # Platform patterns
        self.platform_patterns = {
            'tiktok': r'(tiktok\.com|musical\.ly)',
            'douyin': r'douyin\.com',
            'youtube': r'(youtube\.com|youtu\.be)',
            'instagram': r'instagram\.com',
            'twitter': r'(twitter\.com|x\.com)'
        }
    
    def detect_platform(self, url: str) -> str:
        """Detect platform from URL"""
        for platform, pattern in self.platform_patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                return platform
        return 'unknown'
    
    def extract_video_id(self, url: str, platform: str) -> Optional[str]:
        """Extract video ID from URL"""
        try:
            if platform == 'tiktok':
                # Extract from TikTok URL
                match = re.search(r'/video/(\d+)', url)
                if match:
                    return match.group(1)
                
                # Alternative TikTok pattern
                match = re.search(r'@[\w\.]+/video/(\d+)', url)
                if match:
                    return match.group(1)
            
            elif platform == 'douyin':
                match = re.search(r'/video/(\d+)', url)
                if match:
                    return match.group(1)
            
            elif platform == 'youtube':
                # YouTube patterns
                patterns = [
                    r'(?:v=|/)([0-9A-Za-z_-]{11})',
                    r'youtu\.be/([0-9A-Za-z_-]{11})'
                ]
                for pattern in patterns:
                    match = re.search(pattern, url)
                    if match:
                        return match.group(1)
            
            return None
        except Exception as e:
            logger.error(f"Error extracting video ID: {str(e)}")
            return None
    
    def download_video(self, url: str) -> Dict:
        """Download video from URL"""
        try:
            platform = self.detect_platform(url)
            logger.info(f"Downloading from {platform}: {url}")
            
            # Create temp file for download
            with tempfile.NamedTemporaryFile(
                suffix='.mp4', 
                delete=False,
                dir=self.output_dir
            ) as temp_file:
                temp_path = temp_file.name
            
            # YouTube-DL options
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': temp_path,
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
                'force_generic_extractor': False,
                'postprocessors': [],
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'no_color': True,
                'socket_timeout': self.timeout,
                'http_chunk_size': 10485760,  # 10MB chunks
                'retries': self.max_retries,
                'fragment_retries': self.max_retries,
                'skip_unavailable_fragments': False,
                'keepvideo': False,
                'writethumbnail': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'consoletitle': False,
                'progress_hooks': [self._progress_hook],
                'user_agent': Config.USER_AGENT,
                
                # Platform specific options
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['hls', 'dash']
                    },
                    'tiktok': {
                        'app_version': '29.7.5',
                        'manifest_app_version': '29.7.5'
                    }
                }
            }
            
            # Platform-specific adjustments
            if platform == 'tiktok':
                ydl_opts.update({
                    'referer': 'https://www.tiktok.com/',
                    'headers': {
                        'User-Agent': Config.USER_AGENT,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Cache-Control': 'max-age=0'
                    }
                })
            
            # Download video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    raise Exception("Failed to extract video info")
                
                # Get downloaded file info
                downloaded_file = temp_path
                if not os.path.exists(downloaded_file):
                    # Try to find the actual downloaded file
                    if 'requested_downloads' in info and info['requested_downloads']:
                        downloaded_file = info['requested_downloads'][0]['filepath']
                
                # Generate final filename
                video_id = self.extract_video_id(url, platform) or info.get('id', 'unknown')
                safe_title = re.sub(r'[^\w\-_\. ]', '_', info.get('title', video_id))[:100]
                final_filename = f"{platform}_{video_id}_{safe_title}.mp4"
                final_filepath = os.path.join(self.output_dir, final_filename)
                
                # Rename temp file to final filename
                os.rename(downloaded_file, final_filepath)
                
                # Clean up temp thumbnail if exists
                thumbnail_path = downloaded_file + '.webp'
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                
                # Get thumbnail if available
                thumbnail = None
                if info.get('thumbnail'):
                    thumbnail = info['thumbnail']
                elif info.get('thumbnails'):
                    thumbnail = info['thumbnails'][-1]['url'] if info['thumbnails'] else None
                
                return {
                    'success': True,
                    'platform': platform,
                    'video_id': video_id,
                    'title': info.get('title', 'Unknown'),
                    'filename': final_filename,
                    'filepath': final_filepath,
                    'file_size': os.path.getsize(final_filepath),
                    'duration': info.get('duration', 0),
                    'thumbnail': thumbnail,
                    'url': url,
                    'info': {
                        'uploader': info.get('uploader'),
                        'upload_date': info.get('upload_date'),
                        'view_count': info.get('view_count'),
                        'like_count': info.get('like_count'),
                        'comment_count': info.get('comment_count')
                    }
                }
        
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Download error: {str(e)}")
            # Clean up temp file if exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            
            return {
                'success': False,
                'error': f"Download failed: {str(e)}",
                'platform': platform,
                'url': url
            }
        
        except Exception as e:
            logger.error(f"Unexpected download error: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'platform': platform,
                'url': url
            }
    
    def _progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            # Log progress
            if 'total_bytes' in d and d['total_bytes'] > 0:
                percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                logger.info(f"Download progress: {percent:.1f}%")
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                percent = d['downloaded_bytes'] / d['total_bytes_estimate'] * 100
                logger.info(f"Download progress: {percent:.1f}%")
        
        elif d['status'] == 'finished':
            logger.info("Download completed")
        
        elif d['status'] == 'error':
            logger.error(f"Download error in hook: {d}")
    
    def batch_download(self, urls: list) -> Dict:
        """Download multiple videos"""
        results = []
        for url in urls:
            result = self.download_video(url)
            results.append(result)
        
        success_count = sum(1 for r in results if r['success'])
        
        return {
            'total': len(urls),
            'success': success_count,
            'failed': len(urls) - success_count,
            'results': results
        }
    
    def get_video_info(self, url: str) -> Dict:
        """Get video information without downloading"""
        try:
            platform = self.detect_platform(url)
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'force_generic_extractor': False,
                'user_agent': Config.USER_AGENT
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise Exception("Failed to extract video info")
                
                video_id = self.extract_video_id(url, platform) or info.get('id', 'unknown')
                
                return {
                    'success': True,
                    'platform': platform,
                    'video_id': video_id,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail'),
                    'description': info.get('description'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'comment_count': info.get('comment_count'),
                    'is_live': info.get('is_live', False),
                    'formats': [
                        {
                            'format_id': f.get('format_id'),
                            'ext': f.get('ext'),
                            'resolution': f.get('resolution'),
                            'filesize': f.get('filesize')
                        }
                        for f in info.get('formats', [])[:5]  # First 5 formats
                    ]
                }
        
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }