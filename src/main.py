import logging

from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from api.router import routers as v1_router
from api.v1.health import router as health_router, health_check, HealthCheckResponse
from core.config import config
from core.dependencies import get_db
from core.lifecycle import app_lifespan

logging.basicConfig(level=logging.INFO)
app = FastAPI(title=config.PROJECT_NAME, version="1.0.0",lifespan=app_lifespan)

app.include_router(v1_router, prefix=config.API_V1_STR)
app.include_router(health_router)

@app.get("/", response_model=HealthCheckResponse, tags=["Health"])
async def root(db: AsyncSession = Depends(get_db)):
    return await health_check(db)

origins = [
    "https://clientmanger.tech",
    "https://www.clientmanger.tech",
    "https://chat.clientmanger.tech",
    "https://bhaveshupadhyay.github.io",
    "https://www.bhaveshupadhyay.github.io",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://localhost:63342",
    "http://localhost:3000",
    "http://localhost:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)