import uuid
import logging
from fastapi import UploadFile, HTTPException
from repository.file_repository import FileRepository

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, file_repository: FileRepository):
        self.file_repository = file_repository

    async def upload_file(self, file: UploadFile) -> str:
        """
        Uploads the file using file_repository.
        Generates a unique name for the file to prevent overwrite/collision.
        """
        content_type = file.content_type or "application/octet-stream"
        original_filename = file.filename or "file"
        
        # Extract extension
        ext = ""
        if "." in original_filename:
            ext = "." + original_filename.split(".")[-1]
            
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        try:
            file_bytes = await file.read()
            if not file_bytes:
                raise HTTPException(status_code=400, detail="Empty file uploaded")
            
            # Reset seek position just in case
            await file.seek(0)
            
            url = await self.file_repository.upload_file(
                filename=unique_filename,
                file_bytes=file_bytes,
                content_type=content_type
            )
            return url
        except Exception as e:
            logger.error(f"Error in FileService.upload_file: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"File upload service failed: {str(e)}")

    async def download_file(self, filename: str) -> bytes:
        """
        Downloads the file by filename.
        """
        return await self.file_repository.download_file(filename)