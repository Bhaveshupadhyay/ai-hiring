import urllib.parse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from core.config import config

Base = declarative_base()

_async_engine = None
_async_session_maker = None

def get_async_db_url() -> str:
    raw_password = config.POSTGRES_DB_PASSWORD
    encoded_password = urllib.parse.quote_plus(raw_password)
    db_host = config.POSTGRES_DB_HOST
    db_user = config.POSTGRES_DB_USER
    db_name = config.POSTGRES_DB_NAME
    
    return f"postgresql+asyncpg://{db_user}:{encoded_password}@{db_host}:5432/{db_name}?ssl=require"

def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    global _async_engine, _async_session_maker
    if _async_session_maker is None:
        url = get_async_db_url()
        _async_engine = create_async_engine(
            url, 
            echo=False, 
            future=True,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "ssl": "require",
                "statement_cache_size": 0
            }
        )
        _async_session_maker = async_sessionmaker(
            bind=_async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return _async_session_maker

def open_connection() -> None:
    get_async_session_maker()

async def create_tables() -> None:
    get_async_session_maker()
    
    # Import all models to register on Base
    import models.job
    import models.candidate
    import models.application
    import models.interview
    
    global _async_engine
    if _async_engine is not None:
        async with _async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

async def close_connection() -> None:
    global _async_engine, _async_session_maker
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
    _async_session_maker = None