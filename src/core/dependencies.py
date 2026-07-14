from functools import lru_cache
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from core.client import get_async_session_maker

# Repositories
from repository.file_repository import FileRepository
from repository.job_repository import JobRepository
from repository.candidate_repository import CandidateRepository
from repository.application_repository import ApplicationRepository
from repository.interview_repository import InterviewRepository

# Services
from service.llm_provider import LLmProvider, GeminiLLmProvider, GroqLLmProvider
from service.file_service import FileService
from service.resume_parser import ResumeParser
from service.job_service import JobService
from service.candidate_service import CandidateService
from service.matching_service import MatchingService
from service.interview_service import InterviewService

# Database Dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async_session = get_async_session_maker()
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# LLM Provider Dependency
@lru_cache
def get_llm_provider() -> LLmProvider:
    return GroqLLmProvider()

# Repository Dependencies
@lru_cache
def get_file_repository() -> FileRepository:
    return FileRepository()

@lru_cache
def get_job_repository() -> JobRepository:
    return JobRepository()

@lru_cache
def get_candidate_repository() -> CandidateRepository:
    return CandidateRepository()

@lru_cache
def get_application_repository() -> ApplicationRepository:
    return ApplicationRepository()

@lru_cache
def get_interview_repository() -> InterviewRepository:
    return InterviewRepository()

# Service Dependencies
@lru_cache
def get_file_service() -> FileService:
    return FileService(file_repository=get_file_repository())

@lru_cache
def get_resume_parser() -> ResumeParser:
    return ResumeParser(llm_provider=get_llm_provider())

def get_job_service() -> JobService:
    return JobService(
        job_repository=get_job_repository(),
        llm_provider=get_llm_provider()
    )

def get_candidate_service() -> CandidateService:
    return CandidateService(
        candidate_repository=get_candidate_repository(),
        file_service=get_file_service(),
        resume_parser=get_resume_parser()
    )

def get_matching_service() -> MatchingService:
    return MatchingService(
        application_repository=get_application_repository(),
        job_repository=get_job_repository(),
        candidate_repository=get_candidate_repository(),
        llm_provider=get_llm_provider()
    )

def get_interview_service() -> InterviewService:
    return InterviewService(
        interview_repository=get_interview_repository(),
        application_repository=get_application_repository()
    )
