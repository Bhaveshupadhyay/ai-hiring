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
        1. Upload PDF using FileService (returns URL)
        2. Create Candidate (initial)
        3. Parse Resume via ResumeParser (Gemini)
        4. Save structured ResumeAnalysis
        5. Update Candidate name, email, phone from parsed details
        """
        logger.info(f"Uploading file: {file.filename}")
        # Upload PDF
        resume_url = await self.file_service.upload_file(file)
        
        # Create initial candidate record
        candidate = Candidate(
            name="Parsing...",
            email="Parsing...",
            phone=None,
            resume_url=resume_url
        )
        candidate = await self.candidate_repository.create(db, candidate)
        
        # Parse resume via ResumeParser
        try:
            parsed_data = await self.resume_parser.parse(resume_url)
        except Exception as e:
            logger.error(f"Error parsing resume via Gemini: {e}")
            # Even if parsing fails, we keep the candidate with the uploaded URL
            # but raise an error or set defaults. Let's raise an HTTP exception or save placeholder analysis
            # We want to make sure it's robust. Let's create an empty analysis to avoid breaking the DB constraints.
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
            candidate.name = file.filename or "Unknown"
            candidate.email = "Unknown"
            await db.flush()
            raise HTTPException(
                status_code=422,
                detail=f"Successfully uploaded, but failed to parse resume text: {str(e)}"
            )

        # Update candidate with parsed data
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
                # Check if email already exists in candidate db
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists in the candidate database."
                )

        candidate.name = parsed_data.name or file.filename or "Unknown"
        candidate.email = email
        candidate.phone = parsed_data.phone
        
        # Save structured resume analysis
        # raw_response is the dict representation of ResumeParserLLMResponse
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
