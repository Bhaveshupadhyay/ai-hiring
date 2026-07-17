import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from api.router import routers as v1_router
from api.v1.health import router as health_router
from core.config import config
from core.lifecycle import app_lifespan

logging.basicConfig(level=logging.INFO)
app = FastAPI(title=config.PROJECT_NAME, version="1.0.0",lifespan=app_lifespan)

app.include_router(v1_router, prefix=config.API_V1_STR)
app.include_router(health_router)

@app.get("/ping", tags=["Liveness"])
@app.head("/ping", tags=["Liveness"])
@app.get("/", tags=["Liveness"])
@app.head("/", tags=["Liveness"])
async def ping():
    """
    Lightweight liveness check (ping) to keep the container active.
    Does not touch the database.
    """
    return {"status": "ok"}

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