import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db, get_job_service
from service.job_service import JobService
from api.v1.schemas import JobGenerateRequest, JobCreateRequest, JobUpdateRequest, JobResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/generate", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def generate_job_description(
    request: JobGenerateRequest,
    db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """
    Generate a job description from a title using Gemini, save it as a draft, and return it.
    """
    try:
        job = await job_service.generate_job_description(db, request.title)
        return job
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate job description: {str(e)}"
        )

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """
    Manually create a new job description.
    """
    job = await job_service.create_job(db, request.model_dump())
    return job

@router.get("", response_model=list[JobResponse])
async def get_jobs(
    db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """
    Retrieve all job descriptions.
    """
    jobs = await job_service.get_all_jobs(db)
    return jobs

@router.get("/{id}", response_model=JobResponse)
async def get_job(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """
    Retrieve a specific job description by ID.
    """
    job = await job_service.get_job_by_id(db, id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job

@router.put("/{id}", response_model=JobResponse)
async def update_job(
    id: uuid.UUID,
    request: JobUpdateRequest,
    db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """
    Update an existing job description.
    """
    # Filter out None values to avoid overwriting fields that weren't supplied in patch/update
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    
    job = await job_service.update_job(db, id, update_data)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """
    Delete a job description.
    """
    success = await job_service.delete_job(db, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return None
