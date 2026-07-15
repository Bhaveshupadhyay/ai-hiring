import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.application import Application
from models.candidate import Candidate

class ApplicationRepository:
    async def create(self, db: AsyncSession, application: Application) -> Application:
        db.add(application)
        await db.flush()
        return application

    async def get_by_id(self, db: AsyncSession, app_id: uuid.UUID) -> Application | None:
        result = await db.execute(
            select(Application)
            .where(Application.id == app_id)
            .options(
                selectinload(Application.candidate).selectinload(Candidate.resume_analysis),
                selectinload(Application.job)
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, 
        db: AsyncSession, 
        status: str | None = None, 
        sort_by_score: bool = False,
        job_id: uuid.UUID | None = None
    ) -> list[Application]:
        if sort_by_score:
            stmt = select(Application).order_by(
                Application.match_score.desc().nulls_last(),
                Application.created_at.desc()
            )
        else:
            stmt = select(Application).order_by(Application.created_at.desc())

        if status is not None:
            stmt = stmt.where(Application.status == status)
        if job_id is not None:
            stmt = stmt.where(Application.job_id == job_id)
        result = await db.execute(
            stmt.options(
                selectinload(Application.candidate).selectinload(Candidate.resume_analysis),
                selectinload(Application.job)
            )
        )
        return list(result.scalars().all())

    async def get_by_job_and_candidate(self, db: AsyncSession, job_id: uuid.UUID, candidate_id: uuid.UUID) -> Application | None:
        result = await db.execute(
            select(Application)
            .where(Application.job_id == job_id, Application.candidate_id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def update(self, db: AsyncSession, application: Application) -> Application:
        await db.flush()
        return application

    async def get_count_by_job_id(self, db: AsyncSession, job_id: uuid.UUID) -> int:
        result = await db.execute(
            select(func.count()).select_from(Application).where(Application.job_id == job_id)
        )
        return result.scalar_one()
