from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from pydantic import BaseModel
from core.dependencies import get_db

router = APIRouter(prefix="/health", tags=["Health"])

class HealthCheckResponse(BaseModel):
    status: str
    database: str

@router.get("", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Check the health of the application and its database connection.
    """
    try:
        # Perform a quick database execution to verify connectivity
        await db.execute(text("SELECT 1"))
        return HealthCheckResponse(status="healthy", database="connected")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
