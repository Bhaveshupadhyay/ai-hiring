from fastapi import APIRouter
# from api.v1.file import router as file_router
from api.v1.jobs import router as jobs_router
from api.v1.candidates import router as candidates_router
from api.v1.applications import router as applications_router
from api.v1.interviews import router as interviews_router

routers = APIRouter()

# routers.include_router(file_router)
routers.include_router(jobs_router)
routers.include_router(candidates_router)
routers.include_router(applications_router)
routers.include_router(interviews_router)