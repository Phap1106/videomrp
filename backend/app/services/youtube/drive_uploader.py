"""
YouTube Video Analyzer - Stage 4: Google Drive Uploader
========================================================
Upload processed videos to Google Drive with folder organization.
"""

import asyncio
import os
import io
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any
from dataclasses import dataclass
import json
import httpx

from app.core.logger import logger
from app.core.config import settings


@dataclass
class DriveFolder:
    """Google Drive folder info"""
    folder_id: str
    name: str
    url: str
    parent_id: Optional[str] = None


@dataclass
class DriveFile:
    """Uploaded file info"""
    file_id: str
    name: str
    url: str
    size_bytes: int
    mime_type: str


@dataclass
class UploadResult:
    """Batch upload result"""
    success: bool
    folder: Optional[DriveFolder]
    files: list[DriveFile]
    total_size_bytes: int
    upload_time_seconds: float
    failed_files: list[str]
    error: Optional[str] = None


class GoogleDriveUploader:
    """
    Google Drive upload service.
    - OAuth2 authentication
    - Resumable uploads
    - Folder organization
    - Progress tracking
    """
    
    DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
    UPLOAD_API_BASE = "https://www.googleapis.com/upload/drive/v3"
    CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks
    MAX_RETRIES = 3
    
    def __init__(self):
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self.client = httpx.AsyncClient(timeout=60.0)
    
    def set_credentials(
        self,
        access_token: str,
        refresh_token: str = None,
        expiry: datetime = None
    ):
        """Set OAuth2 credentials"""
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expiry = expiry
    
    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        return self._access_token is not None
    
    async def create_folder(
        self,
        name: str,
        parent_id: str = None
    ) -> Optional[DriveFolder]:
        """Create a folder in Google Drive"""
        if not self._access_token:
            logger.error("Not authenticated")
            return None
        
        try:
            metadata = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder"
            }
            
            if parent_id:
                metadata["parents"] = [parent_id]
            
            response = await self.client.post(
                f"{self.DRIVE_API_BASE}/files",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json"
                },
                json=metadata
            )
            
            if response.status_code != 200:
                logger.error(f"Folder creation failed: {response.status_code}")
                return None
            
            data = response.json()
            
            return DriveFolder(
                folder_id=data["id"],
                name=data["name"],
                url=f"https://drive.google.com/drive/folders/{data['id']}",
                parent_id=parent_id
            )
            
        except Exception as e:
            logger.error(f"Folder creation error: {e}")
            return None
    
    async def get_or_create_folder(
        self,
        path: str,
        root_folder_id: str = None
    ) -> Optional[DriveFolder]:
        """
        Get or create folder path (e.g., "VideoFactory/ChannelName/2026-01")
        """
        parts = path.strip("/").split("/")
        parent_id = root_folder_id
        
        for part in parts:
            # Check if folder exists
            existing = await self._find_folder(part, parent_id)
            
            if existing:
                parent_id = existing
            else:
                # Create folder
                folder = await self.create_folder(part, parent_id)
                if not folder:
                    return None
                parent_id = folder.folder_id
        
        return DriveFolder(
            folder_id=parent_id,
            name=parts[-1],
            url=f"https://drive.google.com/drive/folders/{parent_id}",
            parent_id=root_folder_id
        )
    
    async def _find_folder(
        self,
        name: str,
        parent_id: str = None
    ) -> Optional[str]:
        """Find folder by name"""
        try:
            query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            response = await self.client.get(
                f"{self.DRIVE_API_BASE}/files",
                headers={"Authorization": f"Bearer {self._access_token}"},
                params={"q": query, "fields": "files(id,name)"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("files"):
                    return data["files"][0]["id"]
            
        except Exception as e:
            logger.error(f"Folder search error: {e}")
        
        return None
    
    async def upload_file(
        self,
        file_path: Path,
        folder_id: str = None,
        name: str = None,
        progress_callback: Callable = None
    ) -> Optional[DriveFile]:
        """
        Upload a file to Google Drive with resumable upload.
        """
        if not self._access_token:
            logger.error("Not authenticated")
            return None
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        file_name = name or file_path.name
        file_size = file_path.stat().st_size
        mime_type = self._get_mime_type(file_path)
        
        try:
            # Step 1: Initialize resumable upload
            metadata = {"name": file_name}
            if folder_id:
                metadata["parents"] = [folder_id]
            
            response = await self.client.post(
                f"{self.UPLOAD_API_BASE}/files?uploadType=resumable",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                    "X-Upload-Content-Type": mime_type,
                    "X-Upload-Content-Length": str(file_size)
                },
                json=metadata
            )
            
            if response.status_code != 200:
                logger.error(f"Upload init failed: {response.status_code}")
                return None
            
            upload_url = response.headers.get("Location")
            if not upload_url:
                logger.error("No upload URL received")
                return None
            
            # Step 2: Upload file in chunks
            uploaded = 0
            
            with open(file_path, "rb") as f:
                while uploaded < file_size:
                    chunk_size = min(self.CHUNK_SIZE, file_size - uploaded)
                    chunk = f.read(chunk_size)
                    
                    end_byte = uploaded + len(chunk) - 1
                    
                    for attempt in range(self.MAX_RETRIES):
                        try:
                            response = await self.client.put(
                                upload_url,
                                headers={
                                    "Content-Range": f"bytes {uploaded}-{end_byte}/{file_size}"
                                },
                                content=chunk
                            )
                            
                            if response.status_code in [200, 201]:
                                # Upload complete
                                data = response.json()
                                return DriveFile(
                                    file_id=data["id"],
                                    name=data["name"],
                                    url=f"https://drive.google.com/file/d/{data['id']}/view",
                                    size_bytes=file_size,
                                    mime_type=mime_type
                                )
                            
                            elif response.status_code == 308:
                                # Chunk uploaded, continue
                                uploaded += len(chunk)
                                
                                if progress_callback:
                                    progress = (uploaded / file_size) * 100
                                    if asyncio.iscoroutinefunction(progress_callback):
                                        await progress_callback(progress)
                                    else:
                                        progress_callback(progress)
                                break
                            
                            else:
                                logger.warning(f"Chunk upload failed: {response.status_code}")
                                if attempt == self.MAX_RETRIES - 1:
                                    return None
                                await asyncio.sleep(2 ** attempt)
                                
                        except Exception as e:
                            logger.warning(f"Upload error: {e}")
                            if attempt == self.MAX_RETRIES - 1:
                                raise
                            await asyncio.sleep(2 ** attempt)
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            return None
        
        return None
    
    async def upload_batch(
        self,
        files: list[Path],
        folder_path: str,
        progress_callback: Callable = None
    ) -> UploadResult:
        """
        Upload multiple files to a folder.
        
        Args:
            files: List of file paths
            folder_path: Folder path (e.g., "VideoFactory/ChannelName/2026-01")
            progress_callback: Progress callback
        """
        import time
        start_time = time.time()
        
        uploaded_files = []
        failed_files = []
        total_size = 0
        
        # Create folder structure
        folder = await self.get_or_create_folder(folder_path)
        if not folder:
            return UploadResult(
                success=False,
                folder=None,
                files=[],
                total_size_bytes=0,
                upload_time_seconds=0,
                failed_files=[str(f) for f in files],
                error="Failed to create folder"
            )
        
        # Upload each file
        for i, file_path in enumerate(files):
            try:
                logger.info(f"Uploading {i+1}/{len(files)}: {file_path.name}")
                
                result = await self.upload_file(
                    file_path,
                    folder_id=folder.folder_id
                )
                
                if result:
                    uploaded_files.append(result)
                    total_size += result.size_bytes
                else:
                    failed_files.append(str(file_path))
                
                if progress_callback:
                    progress = ((i + 1) / len(files)) * 100
                    if asyncio.iscoroutinefunction(progress_callback):
                        await progress_callback(progress)
                    else:
                        progress_callback(progress)
                
            except Exception as e:
                logger.error(f"Upload error for {file_path}: {e}")
                failed_files.append(str(file_path))
        
        upload_time = time.time() - start_time
        
        return UploadResult(
            success=len(failed_files) == 0,
            folder=folder,
            files=uploaded_files,
            total_size_bytes=total_size,
            upload_time_seconds=round(upload_time, 1),
            failed_files=failed_files
        )
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for file"""
        extension = file_path.suffix.lower()
        
        mime_types = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mkv": "video/x-matroska",
            ".mov": "video/quicktime",
            ".avi": "video/x-msvideo",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".json": "application/json",
            ".txt": "text/plain",
            ".srt": "text/plain",
        }
        
        return mime_types.get(extension, "application/octet-stream")
    
    def generate_folder_name(
        self,
        channel_name: str,
        date: datetime = None
    ) -> str:
        """Generate organized folder name"""
        date = date or datetime.utcnow()
        
        # Slugify channel name
        import re
        slug = re.sub(r'[^\w\s-]', '', channel_name)
        slug = re.sub(r'[-\s]+', '_', slug)[:30]
        
        return f"VideoFactory/{slug}/{date.strftime('%Y-%m')}"
    
    async def close(self):
        await self.client.aclose()


# Singleton instance
drive_uploader = GoogleDriveUploader()
