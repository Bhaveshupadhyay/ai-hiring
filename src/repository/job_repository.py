import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.job import Job

class JobRepository:
    async def create(self, db: AsyncSession, job: Job) -> Job:
        db.add(job)
        await db.flush() # Flushes changes to populate ID, but does not commit
        return job

    async def get_by_id(self, db: AsyncSession, job_id: uuid.UUID) -> Job | None:
        result = await db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> list[Job]:
        result = await db.execute(select(Job).order_by(Job.created_at.desc()))
        return list(result.scalars().all())

    async def update(self, db: AsyncSession, job: Job) -> Job:
        # Since SQLAlchemy tracks changes on objects attached to session,
        # we flush or just return the job.
        await db.flush()
        return job

    async def delete(self, db: AsyncSession, job_id: uuid.UUID) -> bool:
        job = await self.get_by_id(db, job_id)
        if job:
            await db.delete(job)
            await db.flush()
            return True
        return False
