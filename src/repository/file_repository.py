import os
import logging
from fastapi import HTTPException
from core.config import config

logger = logging.getLogger(__name__)

class FileRepository:
    def __init__(self):
        self.supabase_url = config.SUPABASE_URL
        self.supabase_key = config.SUPABASE_KEY
        self.bucket_name = "resumes"
        self.supabase_client = None
        self.use_local_fallback = True

        if self.supabase_url and self.supabase_key:
            try:
                from supabase import create_client
                self.supabase_client = create_client(self.supabase_url, self.supabase_key)
                self.use_local_fallback = False
                logger.info("Supabase storage client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}. Falling back to local storage.")
        else:
            logger.info("Supabase credentials not configured. Using local storage fallback.")

        if self.use_local_fallback:
            self.local_dir = os.path.join(os.getcwd(), "uploads")
            os.makedirs(self.local_dir, exist_ok=True)
            logger.info(f"Local storage fallback directory set to: {self.local_dir}")

    async def upload_file(self, filename: str, file_bytes: bytes, content_type: str) -> str:
        """
        Uploads a file to Supabase Storage, or falls back to local storage.
        Returns the public URL (or local retrieval path) of the file.
        """
        if not self.use_local_fallback and self.supabase_client:
            try:
                # We upload to the "resumes" bucket.
                # Since supabase-py has synchronous methods for storage, we run it in a thread executor or just call it directly.
                # For safety, let's check if the bucket exists or handle the upload directly.
                bucket = self.supabase_client.storage.from_(self.bucket_name)
                
                # Check/upload
                # supabase-py upload format: upload(path, file, file_options)
                # To prevent naming collisions, we can prefix or keep the name.
                res = bucket.upload(
                    path=filename,
                    file=file_bytes,
                    file_options={"content-type": content_type, "x-upsert": "true"}
                )
                
                # Get public URL
                public_url = bucket.get_public_url(filename)
                logger.info(f"Successfully uploaded file to Supabase Storage: {public_url}")
                return public_url
            except Exception as e:
                logger.error(f"Error uploading to Supabase: {e}. Attempting local fallback.")
                # fall back to local upload
                pass

        # Local fallback upload
        try:
            local_path = os.path.join(self.local_dir, filename)
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            # We return a path relative to the API server or just the filename for local serving
            # Let's build a path that our API v1 router will serve
            download_url = f"/api/v1/file/download/{filename}"
            logger.info(f"Successfully saved file to local storage: {local_path}")
            return download_url
        except Exception as e:
            logger.error(f"Failed to save file locally: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    async def download_file(self, filename: str) -> bytes:
        """
        Downloads/reads file bytes.
        """
        if not self.use_local_fallback and self.supabase_client:
            try:
                bucket = self.supabase_client.storage.from_(self.bucket_name)
                file_bytes = bucket.download(filename)
                return file_bytes
            except Exception as e:
                logger.error(f"Failed to download file from Supabase: {e}. Checking local storage.")

        # Local fallback download
        local_path = os.path.join(self.local_dir, filename)
        if not os.path.exists(local_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        try:
            with open(local_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file from local storage: {e}")
            raise HTTPException(status_code=500, detail="Failed to read file from local storage")