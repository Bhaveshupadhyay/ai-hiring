import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db, get_interview_service
from service.interview_service import InterviewService
from api.v1.schemas import InterviewCreateRequest, InterviewResponse

router = APIRouter(prefix="/interviews", tags=["Interviews"])

@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def schedule_interview(
    request: InterviewCreateRequest,
    db: AsyncSession = Depends(get_db),
    interview_service: InterviewService = Depends(get_interview_service)
):
    """
    Schedule a new interview for a candidate application.
    """
    try:
        interview = await interview_service.schedule_interview(
            db=db,
            application_id=request.application_id,
            scheduled_at=request.scheduled_at,
            meeting_link=request.meeting_link,
            notes=request.notes
        )
        return interview
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule interview: {str(e)}"
        )

@router.get("", response_model=list[InterviewResponse])
async def get_interviews(
    db: AsyncSession = Depends(get_db),
    interview_service: InterviewService = Depends(get_interview_service)
):
    """
    Retrieve all scheduled interviews.
    """
    interviews = await interview_service.get_all_interviews(db)
    return interviews
