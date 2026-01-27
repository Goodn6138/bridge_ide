from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/auth/github/callback"
    
    # Judge0
    JUDGE0_API_URL: str = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_HOST: str = "judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY: str
    
    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key"
    DEBUG: bool = True
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Bridge IDE"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
