import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from repository.application_repository import ApplicationRepository
from repository.job_repository import JobRepository
from repository.candidate_repository import CandidateRepository
from service.llm_provider import LLmProvider
from models.application import Application

logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(
        self,
        application_repository: ApplicationRepository,
        job_repository: JobRepository,
        candidate_repository: CandidateRepository,
        llm_provider: LLmProvider
    ):
        self.application_repository = application_repository
        self.job_repository = job_repository
        self.candidate_repository = candidate_repository
        self.llm_provider = llm_provider

    async def match_candidate_to_job(
        self,
        db: AsyncSession,
        job_id: uuid.UUID,
        candidate_id: uuid.UUID
    ) -> Application:
        """
        Loads Job and ResumeAnalysis, compares them using Gemini, and saves/updates the Application record.
        """
        # Load Job
        job = await self.job_repository.get_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Load Resume Analysis
        resume_analysis = await self.candidate_repository.get_resume_analysis_by_candidate_id(db, candidate_id)
        if not resume_analysis:
            raise HTTPException(status_code=404, detail="Resume analysis not found for candidate. Please parse resume first.")

        job_data = {
            "title": job.title,
            "summary": job.summary,
            "requirements": job.requirements,
            "nice_to_have": job.nice_to_have,
            "experience_required": job.experience_required,
            "education": job.education
        }

        resume_data = {
            "skills": resume_analysis.skills,
            "experience": resume_analysis.experience,
            "education": resume_analysis.education,
            "projects": resume_analysis.projects,
            "summary": resume_analysis.summary
        }

        logger.info(f"Comparing Candidate {candidate_id} against Job {job_id} using Gemini")
        
        # Call Gemini matching
        match_result = await self.llm_provider.match_resume(job_data, resume_data)

        # Check if application already exists
        existing_app = await self.application_repository.get_by_job_and_candidate(db, job_id=job_id, candidate_id=candidate_id)
        
        if existing_app:
            existing_app.match_score = match_result.score
            existing_app.reason = match_result.reason
            existing_app.strengths = match_result.strengths
            existing_app.weaknesses = match_result.weaknesses
            existing_app.ai_decision = match_result.decision
            existing_app.status = "pending" # Reset status for human review
            # We preserve hm_decision as per requirements (do not overwrite)
            application = await self.application_repository.update(db, existing_app)
            logger.info(f"Updated existing application ID: {application.id}")
        else:
            application = Application(
                candidate_id=candidate_id,
                job_id=job_id,
                match_score=match_result.score,
                reason=match_result.reason,
                strengths=match_result.strengths,
                weaknesses=match_result.weaknesses,
                ai_decision=match_result.decision,
                hm_decision=None,
                status="pending"
            )
            application = await self.application_repository.create(db, application)
            logger.info(f"Created new application ID: {application.id}")

        await db.flush()
        # Eager load candidate, job, and resume_analysis to prevent serialization issues
        eager_loaded_app = await self.get_application_by_id(db, application.id)
        if not eager_loaded_app:
            return application
        return eager_loaded_app

    async def get_application_by_id(self, db: AsyncSession, app_id: uuid.UUID) -> Application | None:
        return await self.application_repository.get_by_id(db, app_id)

    async def get_all_applications(self, db: AsyncSession) -> list[Application]:
        return await self.application_repository.get_all(db)

    async def review_application(
        self,
        db: AsyncSession,
        app_id: uuid.UUID,
        hm_decision: str # "approved" or "rejected"
    ) -> Application:
        """
        Human review override decision.
        Updates hm_decision and status without deleting/overwriting AI decisions.
        """
        application = await self.application_repository.get_by_id(db, app_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        if hm_decision not in ["approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid human decision. Must be 'approved' or 'rejected'.")

        application.hm_decision = hm_decision
        # Update the application status to reflect the human decision
        application.status = hm_decision
        
        updated_app = await self.application_repository.update(db, application)
        await db.flush()
        
        logger.info(f"Hiring manager reviewed application {app_id}: {hm_decision}")
        return updated_app
