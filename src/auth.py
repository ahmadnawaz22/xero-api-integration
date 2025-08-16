from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from src.config import settings

# Create API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify the API key from header"""
    if not api_key:
        raise HTTPException(
            status_code=403,
            detail="API Key required"
        )
    
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    
    return api_key