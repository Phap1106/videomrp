import os
from pathlib import Path
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.core.config import settings
from app.core.logger import logger

class GoogleDriveService:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive API using Service Account"""
        try:
            creds_path = settings.GOOGLE_APPLICATION_CREDENTIALS
            if not creds_path or not os.path.exists(creds_path):
                # Try finding it in backend dir if relative path
                backend_creds = settings.BACKEND_DIR / "credentials.json"
                if backend_creds.exists():
                    creds_path = str(backend_creds)
                else:
                    logger.warning(f"Google Drive credentials file not found: {creds_path}")
                    return

            self.creds = Credentials.from_service_account_file(
                 creds_path, scopes=self.SCOPES)
            self.service = build('drive', 'v3', credentials=self.creds)
            logger.info("✅ Google Drive Service authenticated")
        except Exception as e:
             logger.error(f"Google Drive authentication failed: {e}")

    def upload_file(self, file_path: str | Path, folder_id: str = None) -> str | None:
        """
        Upload a file to Google Drive.
        Returns the File ID if successful, None otherwise.
        """
        if not self.service:
            logger.warning("Google Drive service not initialized, skipping upload.")
            return None

        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File to upload not found: {file_path}")
            return None

        target_folder = folder_id or settings.GOOGLE_DRIVE_FOLDER_ID
        if not target_folder:
            logger.warning("No Google Drive folder ID configured.")
            return None

        try:
            file_metadata = {
                'name': file_path.name,
                'parents': [target_folder]
            }
            
            # Simple mimetype detection based on extension
            mimetype = 'video/mp4' if file_path.suffix.lower() == '.mp4' else 'application/octet-stream'
            if file_path.suffix.lower() == '.mp3': mimetype = 'audio/mpeg'
            
            media = MediaFileUpload(
                str(file_path), 
                mimetype=mimetype,
                resumable=True
            )

            logger.info(f"📤 Uploading {file_path.name} to Drive (Folder: {target_folder})...")
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            logger.info(f"✅ Uploaded to Drive: ID={file.get('id')}, Link={file.get('webViewLink')}")
            return file.get('webViewLink')

        except Exception as e:
            logger.error(f"❌ Google Drive upload error: {e}")
            return None

# Singleton instance
google_drive_service = GoogleDriveService()
