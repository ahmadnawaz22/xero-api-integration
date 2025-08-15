"""
Configuration management for the Xero API
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    api_key: str = os.getenv("API_KEY", "")
    api_version: str = os.getenv("API_VERSION", "v1")
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Xero Settings
    xero_client_id: str = os.getenv("XERO_CLIENT_ID", "")
    xero_client_secret: str = os.getenv("XERO_CLIENT_SECRET", "")
    xero_redirect_uri: str = os.getenv("XERO_REDIRECT_URI", "http://localhost:8000/callback")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./xero_tokens.db")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate critical settings
def validate_settings():
    """Validate that all required settings are present"""
    errors = []
    
    if not settings.api_key:
        errors.append("API_KEY is not set")
    
    if not settings.xero_client_id:
        errors.append("XERO_CLIENT_ID is not set")
        
    if not settings.xero_client_secret:
        errors.append("XERO_CLIENT_SECRET is not set")
    
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\n📝 Please update your .env file")
        return False
    
    return True