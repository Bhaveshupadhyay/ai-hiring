import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db, get_candidate_service, get_matching_service
from service.candidate_service import CandidateService
from service.matching_service import MatchingService
from api.v1.schemas import CandidateResponse

router = APIRouter(tags=["Candidates"])

@router.post("/resume/upload", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    job_id: uuid.UUID,
    file: UploadFile = File(..., description="PDF file of the candidate's resume"),
    db: AsyncSession = Depends(get_db),
    candidate_service: CandidateService = Depends(get_candidate_service),
    matching_service: MatchingService = Depends(get_matching_service)
):
    """
    Upload resume PDF for a specific job. Stored in Supabase/local storage,
    parsed by Gemini, matched to the job description, and saved to database.
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload request."
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported for resume upload."
        )

    # 1. Upload resume and parse details
    candidate = await candidate_service.upload_resume(db, file, job_id)

    # 2. Run AI matching automatically for this job
    await matching_service.match_candidate_to_job(db, job_id=job_id, candidate_id=candidate.id)
    
    # 3. Retrieve analysis to include in response
    analysis = await candidate_service.get_resume_analysis(db, candidate.id)
    candidate.resume_analysis = analysis
    
    return candidate

@router.get("/candidates", response_model=list[CandidateResponse])
async def get_candidates(
    db: AsyncSession = Depends(get_db),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    """
    Retrieve list of all candidates.
    """
    candidates = await candidate_service.get_all_candidates(db)
    return candidates

@router.get("/candidate/{id}", response_model=CandidateResponse)
async def get_candidate(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    """
    Retrieve candidate details including resume analysis.
    """
    candidate = await candidate_service.get_candidate_by_id(db, id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        
    # Also load the analysis
    analysis = await candidate_service.get_resume_analysis(db, id)
    candidate.resume_analysis = analysis
    return candidate
