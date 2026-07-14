import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Config(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Hiring Automation Platform"
    
    POSTGRES_DB_HOST: str=''
    POSTGRES_DB_PASSWORD: str=''
    POSTGRES_DB_NAME: str = "postgres"
    POSTGRES_DB_USER: str = "postgres.hrqqjcnlkdnpfttxlmiu"
    
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

config: Config = Config()