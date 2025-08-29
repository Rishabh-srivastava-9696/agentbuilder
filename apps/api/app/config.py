"""
Application Configuration
"""

import os
from typing import List
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_LOG_LEVEL: str = "info"
    DEBUG: bool = False
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    # Qwen Configuration
    QWEN_API_KEY: str = ""
    QWEN_MODEL: str = "qwen-max"
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # Default LLM Provider
    DEFAULT_LLM_PROVIDER: str = "openai"
    
    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "agent-builder"
    MONGODB_COLLECTION: str = "documents"
    
    # Voyage AI Configuration
    VOYAGE_API_KEY: str = ""
    VOYAGE_MODEL: str = "voyage-large-2-instruct"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_SSL: bool = False
    
    # Server Configuration
    API_WORKERS: int = 1
    API_RELOAD: bool = True
    
    # CORS Configuration
    CORS_ALLOW_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Feature Flags
    ENABLE_WEBSOCKETS: bool = True
    ENABLE_SSE: bool = True
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = False
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "pdf,txt,md,docx,html"
    UPLOAD_DIR: str = "./uploads"
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @field_validator("REDIS_SSL", "API_RELOAD", "ENABLE_WEBSOCKETS", "ENABLE_SSE", "ENABLE_METRICS", "ENABLE_TRACING", mode="before")
    @classmethod
    def parse_bool_fields(cls, v):
        """Parse boolean fields from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v
    
    @field_validator("API_WORKERS", "RATE_LIMIT_REQUESTS_PER_MINUTE", "RATE_LIMIT_BURST", "MAX_FILE_SIZE_MB", "ACCESS_TOKEN_EXPIRE_MINUTES", mode="before")
    @classmethod
    def parse_int_fields(cls, v):
        """Parse integer fields from string."""
        if isinstance(v, str):
            return int(v)
        return v
    
    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        """Parse DEBUG from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
