import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from core.dependencies import get_file_service
from service.file_service import FileService

router = APIRouter(prefix='/file', tags=['File'])

# @router.post("/upload")
# async def upload_file(
#     file: UploadFile = File(...),
#     file_service: FileService = Depends(get_file_service)
# ):
#     """
#     General file upload. Returns the access URL.
#     """
#     url = await file_service.upload_file(file)
#     return {"url": url}
#
# @router.get("/download/{filename}")
# async def download_file(
#     filename: str,
#     file_service: FileService = Depends(get_file_service)
# ):
#     """
#     Serves files from local storage if using local fallback.
#     """
#     # Verify file existence using the file service
#     # Since download_file returns bytes, we can write a simple path verification
#     # or return the FileResponse directly.
#     import os
#     local_path = os.path.join(os.getcwd(), "uploads", filename)
#     if not os.path.exists(local_path):
#         raise HTTPException(status_code=404, detail="File not found")
#
#     # Return file response
#     media_type = "application/pdf" if filename.lower().endswith(".pdf") else "application/octet-stream"
#     return FileResponse(local_path, media_type=media_type, filename=filename)