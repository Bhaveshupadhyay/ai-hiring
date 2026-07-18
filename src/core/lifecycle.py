from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from core.client import open_connection, close_connection, create_tables

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    open_connection()
    # Run table creation in a background task to prevent blocking application startup/ping checks
    asyncio.create_task(create_tables())
    yield
    await close_connection()