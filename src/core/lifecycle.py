from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.client import open_connection, close_connection, create_tables

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    open_connection()
    await create_tables()
    yield
    await close_connection()