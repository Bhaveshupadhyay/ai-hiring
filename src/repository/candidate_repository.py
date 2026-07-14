import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.candidate import Candidate, ResumeAnalysis

class CandidateRepository:
    async def create(self, db: AsyncSession, candidate: Candidate) -> Candidate:
        db.add(candidate)
        await db.flush()
        return candidate

    async def get_by_id(self, db: AsyncSession, candidate_id: uuid.UUID) -> Candidate | None:
        result = await db.execute(
            select(Candidate)
            .where(Candidate.id == candidate_id)
            .options(selectinload(Candidate.resume_analysis))
        )
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> list[Candidate]:
        result = await db.execute(
            select(Candidate)
            .order_by(Candidate.created_at.desc())
            .options(selectinload(Candidate.resume_analysis))
        )
        return list(result.scalars().all())

    async def create_resume_analysis(self, db: AsyncSession, analysis: ResumeAnalysis) -> ResumeAnalysis:
        db.add(analysis)
        await db.flush()
        return analysis

    async def get_resume_analysis_by_candidate_id(self, db: AsyncSession, candidate_id: uuid.UUID) -> ResumeAnalysis | None:
        result = await db.execute(select(ResumeAnalysis).where(ResumeAnalysis.candidate_id == candidate_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Candidate | None:
        if not email or email.strip().lower() == "unknown":
            return None
        result = await db.execute(select(Candidate).where(Candidate.email == email))
        return result.scalar_one_or_none()

    async def check_application_exists(self, db: AsyncSession, candidate_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        from models.application import Application
        result = await db.execute(
            select(Application).where(
                Application.candidate_id == candidate_id,
                Application.job_id == job_id
            )
        )
        return result.scalar_one_or_none() is not None
