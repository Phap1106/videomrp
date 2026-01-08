import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from postgrest import APIError

from config import Config

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Client for Supabase database and storage"""
    
    def __init__(self):
        self.url = Config.SUPABASE_URL
        self.key = Config.SUPABASE_KEY
        self.service_key = Config.SUPABASE_SERVICE_KEY
        self.storage_bucket = Config.SUPABASE_STORAGE_BUCKET
        
        # Initialize clients
        self.client: Optional[Client] = None
        self.storage_client = None
        
        self._initialize()
    
    def _initialize(self):
        """Initialize Supabase clients"""
        try:
            if not self.url or not self.key:
                logger.warning("Supabase URL or key not configured")
                return
            
            self.client = create_client(self.url, self.key)
            
            # Initialize storage
            self.storage_client = self.client.storage.from_(self.storage_bucket)
            
            logger.info("Supabase client initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {str(e)}")
    
    def check_connection(self) -> bool:
        """Check if connection to Supabase is working"""
        try:
            if not self.client:
                return False
            
            # Try a simple query
            response = self.client.from_('videos').select('count', count='exact').limit(1).execute()
            return True
            
        except Exception as e:
            logger.error(f"Supabase connection check failed: {str(e)}")
            return False
    
    def create_video(self, video_data: Dict) -> Optional[str]:
        """Create a new video record"""
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return None
            
            # Prepare data
            data = {
                'original_filename': video_data.get('original_filename'),
                'file_path': video_data.get('file_path'),
                'file_size': video_data.get('file_size'),
                'source_url': video_data.get('source_url'),
                'source_type': video_data.get('source_type', 'upload'),
                'platform': video_data.get('platform'),
                'thumbnail_url': video_data.get('thumbnail_url'),
                'status': video_data.get('status', 'uploaded'),
                'created_at': datetime.now().isoformat(),
                'metadata': video_data.get('metadata', {})
            }
            
            # Insert record
            response = self.client.from_('videos').insert(data).execute()
            
            if response.data and len(response.data) > 0:
                video_id = response.data[0]['id']
                logger.info(f"Video record created: {video_id}")
                return video_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating video record: {str(e)}")
            return None
    
    def get_video(self, video_id: str) -> Optional[Dict]:
        """Get video by ID"""
        try:
            if not self.client:
                return None
            
            response = self.client.from_('videos').select('*').eq('id', video_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting video: {str(e)}")
            return None
    
    def get_videos(self, limit: int = 50, offset: int = 0, 
                  user_id: Optional[str] = None) -> List[Dict]:
        """Get list of videos"""
        try:
            if not self.client:
                return []
            
            query = self.client.from_('videos').select('*')
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            query = query.order('created_at', desc=True).limit(limit).offset(offset)
            
            response = query.execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting videos: {str(e)}")
            return []
    
    def update_video(self, video_id: str, updates: Dict) -> bool:
        """Update video record"""
        try:
            if not self.client:
                return False
            
            # Add updated timestamp
            updates['updated_at'] = datetime.now().isoformat()
            
            response = self.client.from_('videos').update(updates).eq('id', video_id).execute()
            
            success = bool(response.data)
            if success:
                logger.info(f"Video updated: {video_id}")
            else:
                logger.warning(f"Video update failed: {video_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating video: {str(e)}")
            return False
    
    def delete_video(self, video_id: str) -> bool:
        """Delete video record"""
        try:
            if not self.client:
                return False
            
            # First get video info
            video = self.get_video(video_id)
            if not video:
                return False
            
            # Delete from storage if exists
            storage_url = video.get('storage_url')
            if storage_url:
                try:
                    # Extract file path from URL
                    file_path = storage_url.split(f'{self.storage_bucket}/')[-1]
                    self.storage_client.remove([file_path])
                except Exception as e:
                    logger.warning(f"Error deleting from storage: {str(e)}")
            
            # Delete from database
            response = self.client.from_('videos').delete().eq('id', video_id).execute()
            
            success = bool(response.data)
            if success:
                logger.info(f"Video deleted: {video_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting video: {str(e)}")
            return False
    
    def upload_to_storage(self, file_path: str, 
                         storage_path: Optional[str] = None) -> Optional[str]:
        """Upload file to Supabase Storage"""
        try:
            if not self.storage_client or not os.path.exists(file_path):
                return None
            
            if storage_path is None:
                # Generate storage path
                filename = os.path.basename(file_path)
                storage_path = f"videos/{datetime.now().strftime('%Y/%m/%d')}/{filename}"
            
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload to storage
            response = self.storage_client.upload(
                storage_path,
                file_data,
                file_options={'content-type': 'video/mp4'}
            )
            
            if response:
                # Get public URL
                url = self.storage_client.get_public_url(storage_path)
                logger.info(f"File uploaded to storage: {url}")
                return url
            
            return None
            
        except Exception as e:
            logger.error(f"Error uploading to storage: {str(e)}")
            return None
    
    def create_processing_job(self, video_id: str, task_id: str, 
                            options: Dict = None) -> bool:
        """Create a processing job record"""
        try:
            if not self.client:
                return False
            
            data = {
                'video_id': video_id,
                'task_id': task_id,
                'options': options or {},
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            response = self.client.from_('processing_jobs').insert(data).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error creating processing job: {str(e)}")
            return False
    
    def update_processing_job(self, task_id: str, updates: Dict) -> bool:
        """Update processing job status"""
        try:
            if not self.client:
                return False
            
            # Add completed timestamp if job is done
            if updates.get('status') in ['completed', 'failed', 'cancelled']:
                updates['completed_at'] = datetime.now().isoformat()
            
            updates['updated_at'] = datetime.now().isoformat()
            
            response = self.client.from_('processing_jobs') \
                .update(updates) \
                .eq('task_id', task_id) \
                .execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error updating processing job: {str(e)}")
            return False
    
    def get_processing_job(self, task_id: str) -> Optional[Dict]:
        """Get processing job by task ID"""
        try:
            if not self.client:
                return None
            
            response = self.client.from_('processing_jobs') \
                .select('*') \
                .eq('task_id', task_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting processing job: {str(e)}")
            return None
    
    def search_videos(self, query: str, limit: int = 20) -> List[Dict]:
        """Search videos by filename or metadata"""
        try:
            if not self.client:
                return []
            
            # Search in original_filename
            response = self.client.from_('videos') \
                .select('*') \
                .ilike('original_filename', f'%{query}%') \
                .limit(limit) \
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about videos"""
        try:
            if not self.client:
                return {}
            
            stats = {
                'total_videos': 0,
                'total_size': 0,
                'by_status': {},
                'by_platform': {},
                'recent_uploads': []
            }
            
            # Get total count
            count_resp = self.client.from_('videos') \
                .select('count', count='exact') \
                .execute()
            stats['total_videos'] = count_resp.count or 0
            
            # Get total file size
            size_resp = self.client.from_('videos') \
                .select('file_size') \
                .execute()
            
            if size_resp.data:
                stats['total_size'] = sum(v.get('file_size', 0) for v in size_resp.data)
            
            # Get videos by status
            status_resp = self.client.from_('videos') \
                .select('status', count='exact') \
                .execute()
            
            if status_resp.data:
                for item in status_resp.data:
                    stats['by_status'][item['status']] = item['count']
            
            # Get recent uploads
            recent_resp = self.client.from_('videos') \
                .select('*') \
                .order('created_at', desc=True) \
                .limit(10) \
                .execute()
            
            stats['recent_uploads'] = recent_resp.data or []
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}