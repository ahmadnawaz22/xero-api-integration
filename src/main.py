"""
Main FastAPI application for Xero Integration
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging

from .config import settings, validate_settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Xero Integration API",
    description="Secure API for Xero data integration with Google Sheets",
    version=settings.api_version,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for API key validation
async def verify_api_key(x_api_key: str = Header(...)):
    """Validate API key from header"""
    if x_api_key != settings.api_key:
        logger.warning(f"Invalid API key attempt: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    return True

# Root endpoint
@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "message": "Xero Integration API",
        "version": settings.api_version,
        "environment": settings.environment,
        "docs": "/docs" if settings.environment == "development" else "Disabled in production"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    # Check configuration
    config_valid = validate_settings()
    
    return {
        "status": "healthy" if config_valid else "unhealthy",
        "environment": settings.environment,
        "version": settings.api_version,
        "configuration": "valid" if config_valid else "invalid"
    }

# Protected test endpoint
@app.get("/api/test")
async def test_endpoint(authorized: bool = Depends(verify_api_key)):
    """Test endpoint with authentication"""
    return {
        "message": "Authentication successful!",
        "authorized": authorized
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting Xero Integration API {settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Validate configuration
    if not validate_settings():
        logger.error("Invalid configuration. Please check your .env file")
    else:
        logger.info("Configuration validated successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down Xero Integration API")