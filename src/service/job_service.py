import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from repository.job_repository import JobRepository
from models.job import Job, JobStatus
from service.llm_provider import LLmProvider

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self, job_repository: JobRepository, llm_provider: LLmProvider):
        self.job_repository = job_repository
        self.llm_provider = llm_provider

    async def generate_job_description(self, db: AsyncSession, title: str) -> Job:
        """
        Calls Gemini to generate a job description, then saves it to the database with a 'draft' status.
        """
        logger.info(f"Generating job description for title: {title}")
        llm_response = await self.llm_provider.generate_job_description(title)
        
        # Convert lists to newline-separated strings for the DB text fields
        responsibilities_str = "\n".join(llm_response.responsibilities)
        requirements_str = "\n".join(llm_response.requirements)
        nice_to_have_str = "\n".join(llm_response.nice_to_have)

        job = Job(
            title=title,
            summary=llm_response.summary,
            responsibilities=responsibilities_str,
            requirements=requirements_str,
            nice_to_have=nice_to_have_str,
            experience_required=llm_response.experience_required,
            education=llm_response.education,
            status=JobStatus.DRAFT
        )
        
        # saved_job = await self.job_repository.create(db, job)
        return job

    async def create_job(self, db: AsyncSession, job_data: dict) -> Job:
        """
        Manually creates a new job description in the database.
        """
        job = Job(
            title=job_data["title"],
            summary=job_data.get("summary"),
            responsibilities=job_data.get("responsibilities"),
            requirements=job_data.get("requirements"),
            nice_to_have=job_data.get("nice_to_have"),
            experience_required=job_data.get("experience_required"),
            education=job_data.get("education"),
            status=job_data.get("status", JobStatus.DRAFT)
        )
        return await self.job_repository.create(db, job)

    async def update_job(self, db: AsyncSession, job_id: uuid.UUID, update_data: dict) -> Job | None:
        """
        Updates an existing job description in the database.
        """
        job = await self.job_repository.get_by_id(db, job_id)
        if not job:
            return None
        
        for key, val in update_data.items():
            if hasattr(job, key):
                setattr(job, key, val)
                
        return await self.job_repository.update(db, job)

    async def get_job_by_id(self, db: AsyncSession, job_id: uuid.UUID) -> Job | None:
        return await self.job_repository.get_by_id(db, job_id)

    async def get_all_jobs(self, db: AsyncSession) -> list[Job]:
        return await self.job_repository.get_all(db)

    async def delete_job(self, db: AsyncSession, job_id: uuid.UUID) -> bool:
        return await self.job_repository.delete(db, job_id)
