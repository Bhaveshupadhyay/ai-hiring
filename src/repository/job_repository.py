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
        from sqlalchemy import func
        from models.application import Application
        result = await db.execute(
            select(Job, func.count(Application.id).label("applicants_count"))
            .outerjoin(Application, Job.id == Application.job_id)
            .where(Job.id == job_id)
            .group_by(Job.id)
        )
        row = result.first()
        if row:
            job, count = row
            job.applicants_count = count
            return job
        return None

    async def get_all(self, db: AsyncSession) -> list[Job]:
        from sqlalchemy import func
        from models.application import Application
        result = await db.execute(
            select(Job, func.count(Application.id).label("applicants_count"))
            .outerjoin(Application, Job.id == Application.job_id)
            .group_by(Job.id)
            .order_by(Job.created_at.desc())
        )
        jobs_with_count = []
        for job, count in result.all():
            job.applicants_count = count
            jobs_with_count.append(job)
        return jobs_with_count

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
