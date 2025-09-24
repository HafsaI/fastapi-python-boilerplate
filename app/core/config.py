"""
Core configuration module for the AI Agents platform.
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Agents Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/agents_db"
    DATABASE_URL_SYNC: str = "postgresql://user:password@localhost:5432/agents_db"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # AI Provider API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Agent Configuration
    DEFAULT_AGENT_TIMEOUT: int = 300
    MAX_CONCURRENT_AGENTS: int = 10
    AGENT_MEMORY_TTL: int = 3600
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # CORS - Updated to allow file:// protocol and localhost
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "file://"
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
