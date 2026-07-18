import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from models.application import ApplicationStatus
from models.job import JobStatus
from models.interview import InterviewStatus

# --- Job Schemas ---
class JobGenerateRequest(BaseModel):
    title: str = Field(..., description="Job title for which Gemini should generate description")

class JobCreateRequest(BaseModel):
    title: str = Field(..., max_length=255)
    summary: str | None = None
    responsibilities: str | None = None
    requirements: str | None = None
    nice_to_have: str | None = None
    experience_required: str | None = None
    education: str | None = None
    status: JobStatus = JobStatus.DRAFT

class JobUpdateRequest(BaseModel):
    title: str | None = Field(None, max_length=255)
    summary: str | None = None
    responsibilities: str | None = None
    requirements: str | None = None
    nice_to_have: str | None = None
    experience_required: str | None = None
    education: str | None = None
    status: JobStatus | None = None

class JobStatusUpdateRequest(BaseModel):
    status: JobStatus = Field(..., description="The new status of the job post")

class JobResponse(BaseModel):
    id: uuid.UUID
    title: str
    summary: str | None
    responsibilities: str | None
    requirements: str | None
    nice_to_have: str | None
    experience_required: str | None
    education: str | None
    status: JobStatus
    created_at: datetime
    applicants_count: int = 0

    class Config:
        from_attributes = True

class JobApplicantsCountResponse(BaseModel):
    job_id: uuid.UUID
    count: int


# --- Resume Analysis / Candidate Schemas ---
class ResumeAnalysisResponse(BaseModel):
    id: uuid.UUID
    skills: list | dict | None
    experience: int | None
    education: str | None
    projects: list | dict | None
    summary: str | None
    raw_response: dict | list | None

    class Config:
        from_attributes = True

class CandidateResponse(BaseModel):
    id: uuid.UUID
    name: str | None
    email: str | None
    phone: str | None
    resume_url: str | None
    created_at: datetime
    resume_analysis: ResumeAnalysisResponse | None = None

    class Config:
        from_attributes = True


# --- Application Schemas ---
class MatchRequest(BaseModel):
    job_id: uuid.UUID
    candidate_id: uuid.UUID

class ApplicationReviewRequest(BaseModel):
    hm_decision: str = Field(..., description="Decision by hiring manager: 'approved' or 'rejected'")

class ApplicationStatusUpdateRequest(BaseModel):
    status: ApplicationStatus = Field(..., description="The new status of the application")

class ApplicationResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    match_score: int | None
    reason: str | None
    strengths: list | dict | None
    weaknesses: list | dict | None
    ai_decision: str | None
    hm_decision: str | None
    status: ApplicationStatus
    created_at: datetime
    candidate: CandidateResponse | None = None
    job: JobResponse | None = None

    class Config:
        from_attributes = True


# --- Interview Schemas ---
class InterviewCreateRequest(BaseModel):
    application_id: uuid.UUID
    scheduled_at: datetime
    meeting_link: str | None = None
    notes: str | None = None

class InterviewUpdateRequest(BaseModel):
    scheduled_at: datetime | None = None
    meeting_link: str | None = None
    notes: str | None = None
    status: InterviewStatus | None = None

class InterviewResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    scheduled_at: datetime
    meeting_link: str | None
    notes: str | None
    status: InterviewStatus
    application: ApplicationResponse | None = None

    class Config:
        from_attributes = True
