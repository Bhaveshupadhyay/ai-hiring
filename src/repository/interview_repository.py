import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.interview import Interview
from models.application import Application
from models.candidate import Candidate

class InterviewRepository:
    async def create(self, db: AsyncSession, interview: Interview) -> Interview:
        db.add(interview)
        await db.flush()
        return interview

    async def get_by_id(self, db: AsyncSession, interview_id: uuid.UUID) -> Interview | None:
        result = await db.execute(
            select(Interview)
            .where(Interview.id == interview_id)
            .options(
                selectinload(Interview.application).selectinload(Application.candidate).selectinload(Candidate.resume_analysis),
                selectinload(Interview.application).selectinload(Application.job)
            )
        )
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> list[Interview]:
        result = await db.execute(
            select(Interview)
            .order_by(Interview.scheduled_at.desc())
            .options(
                selectinload(Interview.application).selectinload(Application.candidate).selectinload(Candidate.resume_analysis),
                selectinload(Interview.application).selectinload(Application.job)
            )
        )
        return list(result.scalars().all())

    async def update(self, db: AsyncSession, interview: Interview) -> Interview:
        await db.flush()
        return interview
