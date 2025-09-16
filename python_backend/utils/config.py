"""
Configuration management for the resume fraud detection service.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings."""
    
    # AWS Configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    
    # Supabase Configuration
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: Optional[str] = None
    
    # External API Keys
    numverify_api_key: Optional[str] = None
    abstract_api_key: Optional[str] = None
    serpapi_key: Optional[str] = None
    
    # Background Verification API Keys (Optional)
    opencorporates_api_token: Optional[str] = None
    companies_house_api_key: Optional[str] = None
    datagov_api_key: Optional[str] = None  # Legacy field for backward compatibility
    college_scorecard_key: Optional[str] = None
    github_token: Optional[str] = None
    sec_contact_email: str = "you@example.com"
    openalex_contact_email: str = "you@example.com"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # File Processing
    max_file_size_mb: int = 10
    allowed_file_types: list = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
