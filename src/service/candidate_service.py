import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException
from repository.candidate_repository import CandidateRepository
from service.file_service import FileService
from service.resume_parser import ResumeParser
from models.candidate import Candidate, ResumeAnalysis

logger = logging.getLogger(__name__)

class CandidateService:
    def __init__(
        self,
        candidate_repository: CandidateRepository,
        file_service: FileService,
        resume_parser: ResumeParser
    ):
        self.candidate_repository = candidate_repository
        self.file_service = file_service
        self.resume_parser = resume_parser

    async def upload_resume(self, db: AsyncSession, file: UploadFile, job_id: uuid.UUID) -> Candidate:
        """
        Flow:
        1. Read file bytes.
        2. Concurrently upload PDF using FileService and Parse Resume via ResumeParser (Gemini) using the read bytes.
        3. Save structured ResumeAnalysis and Candidate.
        """
        logger.info(f"Uploading and parsing file: {file.filename}")
        
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
            
        # Reset seek position for file service
        await file.seek(0)
        
        # Concurrently upload file and parse PDF text using Gemini
        upload_task = self.file_service.upload_file(file)
        parse_task = self.resume_parser.parse(resume_url="", pdf_bytes=file_bytes)
        
        results = await asyncio.gather(upload_task, parse_task, return_exceptions=True)
        
        # 1. Handle upload result
        if isinstance(results[0], Exception):
            logger.error(f"File upload failed: {results[0]}")
            if isinstance(results[0], HTTPException):
                raise results[0]
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(results[0])}")
            
        resume_url = results[0]
        
        # 2. Handle parse result
        if isinstance(results[1], Exception):
            e = results[1]
            logger.error(f"Error parsing resume via Gemini: {e}")
            candidate = Candidate(
                name=file.filename or "Unknown",
                email="Unknown",
                phone=None,
                resume_url=resume_url
            )
            candidate = await self.candidate_repository.create(db, candidate)
            
            empty_analysis = ResumeAnalysis(
                candidate_id=candidate.id,
                skills=[],
                experience=0,
                education="Extraction failed",
                projects=[],
                summary="Resume uploaded but extraction failed.",
                raw_response={"error": str(e)}
            )
            await self.candidate_repository.create_resume_analysis(db, empty_analysis)
            await db.flush()
            raise HTTPException(
                status_code=422,
                detail=f"Successfully uploaded, but failed to parse resume text: {str(e)}"
            )

        parsed_data = results[1]
        
        # Update/Create candidate with parsed data
        email = parsed_data.email or "Unknown"
        
        if email and email.lower() != "unknown":
            existing_candidate = await self.candidate_repository.get_by_email(db, email)
            if existing_candidate:
                # Check for duplicate resume for the same job id
                app_exists = await self.candidate_repository.check_application_exists(
                    db, candidate_id=existing_candidate.id, job_id=job_id
                )
                if app_exists:
                    raise HTTPException(
                        status_code=400,
                        detail="Duplicate resume upload for the same job id."
                    )
                
                # Update the existing candidate instead of raising an error
                existing_candidate.name = parsed_data.name or file.filename or "Unknown"
                existing_candidate.phone = parsed_data.phone
                existing_candidate.resume_url = resume_url
                
                # Check if there is an existing analysis for this candidate
                existing_analysis = await self.candidate_repository.get_resume_analysis_by_candidate_id(db, existing_candidate.id)
                raw_dict = parsed_data.model_dump()
                if existing_analysis:
                    existing_analysis.skills = parsed_data.skills
                    existing_analysis.experience = parsed_data.experience
                    existing_analysis.education = parsed_data.education
                    existing_analysis.projects = parsed_data.projects
                    existing_analysis.summary = parsed_data.summary
                    existing_analysis.raw_response = raw_dict
                else:
                    analysis = ResumeAnalysis(
                        candidate_id=existing_candidate.id,
                        skills=parsed_data.skills,
                        experience=parsed_data.experience,
                        education=parsed_data.education,
                        projects=parsed_data.projects,
                        summary=parsed_data.summary,
                        raw_response=raw_dict
                    )
                    await self.candidate_repository.create_resume_analysis(db, analysis)
                
                await db.flush()
                logger.info(f"Successfully updated candidate and analysis for: {existing_candidate.name}")
                return existing_candidate

        # Create new candidate if email is unknown or candidate does not exist yet
        candidate = Candidate(
            name=parsed_data.name or file.filename or "Unknown",
            email=email,
            phone=parsed_data.phone,
            resume_url=resume_url
        )
        candidate = await self.candidate_repository.create(db, candidate)
        
        # Save structured resume analysis
        raw_dict = parsed_data.model_dump()
        
        analysis = ResumeAnalysis(
            candidate_id=candidate.id,
            skills=parsed_data.skills,
            experience=parsed_data.experience,
            education=parsed_data.education,
            projects=parsed_data.projects,
            summary=parsed_data.summary,
            raw_response=raw_dict
        )
        
        await self.candidate_repository.create_resume_analysis(db, analysis)
        await db.flush()
        
        logger.info(f"Successfully created candidate and analysis for: {candidate.name}")
        return candidate


    async def create_candidate(self, db: AsyncSession, candidate_data: dict) -> Candidate:
        candidate = Candidate(
            name=candidate_data.get("name"),
            email=candidate_data.get("email"),
            phone=candidate_data.get("phone"),
            resume_url=candidate_data.get("resume_url")
        )
        return await self.candidate_repository.create(db, candidate)

    async def get_candidate_by_id(self, db: AsyncSession, candidate_id: uuid.UUID) -> Candidate | None:
        return await self.candidate_repository.get_by_id(db, candidate_id)

    async def get_all_candidates(self, db: AsyncSession) -> list[Candidate]:
        return await self.candidate_repository.get_all(db)

    async def get_resume_analysis(self, db: AsyncSession, candidate_id: uuid.UUID) -> ResumeAnalysis | None:
        return await self.candidate_repository.get_resume_analysis_by_candidate_id(db, candidate_id)
