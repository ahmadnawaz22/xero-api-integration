from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    api_key: str
    api_version: str = "v1"
    environment: str = "development"
    
    # Xero OAuth2 Settings
    xero_client_id: str
    xero_client_secret: str
    xero_redirect_uri: str
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # This allows extra fields in .env without errors

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()