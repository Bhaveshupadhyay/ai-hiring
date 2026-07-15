import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db, get_matching_service
from service.matching_service import MatchingService
from api.v1.schemas import MatchRequest, ApplicationReviewRequest, ApplicationResponse, ApplicationStatusUpdateRequest
from models.application import ApplicationStatus

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("/match", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def match_candidate_to_job(
    request: MatchRequest,
    db: AsyncSession = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    """
    Run AI matching comparing a candidate's resume analysis against a job description.
    """
    try:
        application = await matching_service.match_candidate_to_job(db, request.job_id, request.candidate_id)
        return application
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing AI candidate match: {str(e)}"
        )

@router.get("", response_model=list[ApplicationResponse])
async def get_applications(
    job_id: uuid.UUID | None = None,
    status: ApplicationStatus | None = None,
    sort_by_score: bool = False,
    db: AsyncSession = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    """
    List all applications for the dashboard review, optionally filtered by job_id and status,
    and optionally sorted by match score (high to low).
    """
    apps = await matching_service.get_all_applications(db, status=status, sort_by_score=sort_by_score, job_id=job_id)
    return apps

@router.patch("/{id}", response_model=ApplicationResponse)
async def review_application(
    id: uuid.UUID,
    request: ApplicationReviewRequest,
    db: AsyncSession = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    """
    Hiring manager review endpoint to approve/reject an application.
    Updates hm_decision and status without overwriting the original AI decisions.
    """
    try:
        application = await matching_service.review_application(db, id, request.hm_decision)
        return application
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reviewing application: {str(e)}"
        )

@router.post("/{id}/status", response_model=ApplicationResponse)
async def update_application_status(
    id: uuid.UUID,
    request: ApplicationStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    """
    Update the status of an application.
    """
    try:
        application = await matching_service.update_application_status(db, id, request.status)
        return application
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating application status: {str(e)}"
        )
