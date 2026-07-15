import uuid
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from repository.interview_repository import InterviewRepository
from repository.application_repository import ApplicationRepository
from models.interview import Interview, InterviewStatus

logger = logging.getLogger(__name__)

class InterviewService:
    def __init__(
        self,
        interview_repository: InterviewRepository,
        application_repository: ApplicationRepository
    ):
        self.interview_repository = interview_repository
        self.application_repository = application_repository

    async def schedule_interview(
        self,
        db: AsyncSession,
        application_id: uuid.UUID,
        scheduled_at: datetime,
        meeting_link: str | None = None,
        notes: str | None = None
    ) -> Interview:
        """
        Schedules a new interview for a given application.
        Only allows scheduling if the application exists.
        """
        # Verify application exists
        application = await self.application_repository.get_by_id(db, application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        interview = Interview(
            application_id=application_id,
            scheduled_at=scheduled_at,
            meeting_link=meeting_link,
            notes=notes,
            status=InterviewStatus.SCHEDULED
        )
        
        saved_interview = await self.interview_repository.create(db, interview)
        await db.flush()
        logger.info(f"Scheduled interview for application {application_id} at {scheduled_at}")
        
        # Eager load application and nested objects to prevent serialization issues
        eager_loaded_interview = await self.get_interview_by_id(db, saved_interview.id)
        if not eager_loaded_interview:
            return saved_interview
        return eager_loaded_interview

    async def update_interview(
        self,
        db: AsyncSession,
        interview_id: uuid.UUID,
        update_data: dict
    ) -> Interview | None:
        """
        Updates interview details like time, link, notes or status.
        """
        interview = await self.interview_repository.get_by_id(db, interview_id)
        if not interview:
            return None

        for key, val in update_data.items():
            if hasattr(interview, key):
                setattr(interview, key, val)

        updated_interview = await self.interview_repository.update(db, interview)
        await db.flush()
        logger.info(f"Updated interview ID: {interview_id}")
        return updated_interview

    async def get_interview_by_id(self, db: AsyncSession, interview_id: uuid.UUID) -> Interview | None:
        return await self.interview_repository.get_by_id(db, interview_id)

    async def get_all_interviews(self, db: AsyncSession) -> list[Interview]:
        return await self.interview_repository.get_all(db)
