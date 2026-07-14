import io
import logging
import httpx
import pypdf
from fastapi import HTTPException
from service.llm_provider import LLmProvider
from models.llm import ResumeParserLLMResponse

logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self, llm_provider: LLmProvider):
        self.llm_provider = llm_provider

    async def download_pdf(self, url: str) -> bytes:
        """
        Downloads a PDF from a URL.
        """
        # If the URL is relative (e.g. starting with /api/v1/file/download/), 
        # we can't easily fetch it via standard HTTP unless we know the base URL.
        # But wait! If it's a local file path or we are running locally, 
        # let's check if we can read it directly from the local disk if it's relative!
        if url.startswith("/api/v1/file/download/"):
            # It's a local fallback file
            filename = url.split("/")[-1]
            import os
            local_path = os.path.join(os.getcwd(), "uploads", filename)
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    return f.read()
            else:
                raise HTTPException(status_code=404, detail=f"Local file not found for URL: {url}")
        
        # Otherwise download via httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {e}")
            raise HTTPException(status_code=400, detail=f"Could not download resume PDF: {str(e)}")

    def extract_text(self, pdf_bytes: bytes) -> str:
        """
        Extracts raw text from PDF bytes using pypdf.
        """
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            
            clean_text = text.strip()
            if not clean_text:
                raise ValueError("No text could be extracted from the PDF")
            return clean_text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise HTTPException(status_code=400, detail=f"Could not extract text from PDF: {str(e)}")

    async def parse(self, resume_url: str) -> ResumeParserLLMResponse:
        """
        Downloads the PDF, extracts text, calls Gemini to parse, and returns structured data.
        """
        logger.info(f"Downloading resume from {resume_url}")
        pdf_bytes = await self.download_pdf(resume_url)
        
        logger.info("Extracting text from PDF")
        extracted_text = self.extract_text(pdf_bytes)
        
        logger.info("Calling Gemini LLM to parse resume text")
        parsed_data = await self.llm_provider.parse_resume(extracted_text)
        return parsed_data
