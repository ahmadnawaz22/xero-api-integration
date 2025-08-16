from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
import logging

from src.config import settings
from src.auth import verify_api_key
from src.xero_oauth import xero_oauth_manager
from src.token_storage import token_storage
from xero_python.accounting import AccountingApi
from xero_python.identity import IdentityApi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info(f"Starting up in {settings.environment} mode")
    yield
    logger.info("Shutting down")

# Create FastAPI app
app = FastAPI(
    title="Xero API Integration",
    version=settings.api_version,
    lifespan=lifespan
)

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": settings.api_version,
        "configuration": "valid"
    }

# Protected test endpoint
@app.get("/api/v1/test-auth")
async def test_auth(api_key: str = Depends(verify_api_key)):
    """Test endpoint that requires authentication"""
    return {
        "message": "Authentication successful!",
        "authorized": True
    }

# Xero OAuth2 Flow Endpoints
@app.get("/xero/auth")
async def xero_auth():
    """Redirect to Xero for authorization"""
    auth_url = xero_oauth_manager.get_authorization_url()
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def xero_callback(code: Optional[str] = Query(None), state: Optional[str] = Query(None)):
    """Handle Xero OAuth2 callback"""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    try:
        # Exchange code for token
        token_data = await xero_oauth_manager.exchange_code_for_token(code)
        
        # For now, let's just store a default tenant
        # We'll get the actual tenant info in a separate call
        # Store the token with a temporary ID
        token_storage.save_token("temp_tenant", token_data)
        
        return {
            "message": "Authorization successful",
            "token_received": True,
            "access_token": token_data.get('access_token', '')[:20] + "...",  # Show first 20 chars
            "expires_in": token_data.get('expires_in', 0),
            "next_step": "Call /api/v1/xero/connections to get tenant information"
        }
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/api/v1/xero/connections")
async def get_connections(api_key: str = Depends(verify_api_key)):
    """Get Xero tenant connections after authorization"""
    # Get the temporary token
    token_data = token_storage.get_token("temp_tenant")
    if not token_data:
        raise HTTPException(status_code=401, detail="No authorization found. Please authorize first.")
    
    try:
        # Create API client and get connections
        api_client = xero_oauth_manager.create_api_client(token_data['access_token'])
        identity_api = IdentityApi(api_client)
        connections = identity_api.get_connections()
        
        # Now store the token properly for each tenant
        tenant_info = []
        for connection in connections:
            token_storage.save_token(connection.tenant_id, token_data)
            tenant_info.append({
                "tenant_id": connection.tenant_id,
                "tenant_name": connection.tenant_name,
                "tenant_type": connection.tenant_type
            })
        
        # Remove the temporary token
        tokens = token_storage._load_tokens()
        if "temp_tenant" in tokens:
            del tokens["temp_tenant"]
            with open(token_storage.storage_path, 'w') as f:
                json.dump(tokens, f, indent=2)
        
        return {
            "connections": tenant_info,
            "count": len(tenant_info)
        }
        
    except Exception as e:
        logger.error(f"Failed to get connections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Xero API Endpoints
@app.get("/api/v1/xero/organizations")
async def get_organizations(api_key: str = Depends(verify_api_key)):
    """Get all connected Xero organizations"""
    tokens = token_storage._load_tokens()
    if not tokens:
        raise HTTPException(status_code=401, detail="No Xero connections found. Please authorize first.")
    
    organizations = []
    for tenant_id, token_data in tokens.items():
        # Check if token is expired
        if token_storage.is_token_expired(tenant_id):
            # Try to refresh
            try:
                new_token = await xero_oauth_manager.refresh_token(token_data['refresh_token'])
                token_storage.save_token(tenant_id, new_token)
                token_data = new_token
            except Exception as e:
                logger.error(f"Failed to refresh token for tenant {tenant_id}: {str(e)}")
                continue
        
        # Get organization info
        try:
            api_client = xero_oauth_manager.create_api_client(token_data['access_token'])
            accounting_api = AccountingApi(api_client)
            org = accounting_api.get_organisations(tenant_id)
            organizations.append({
                "tenant_id": tenant_id,
                "name": org.organisations[0].name,
                "version": org.organisations[0].version,
                "tax_number": org.organisations[0].tax_number
            })
        except Exception as e:
            logger.error(f"Failed to get org info for tenant {tenant_id}: {str(e)}")
    
    return {"organizations": organizations}

@app.get("/api/v1/xero/invoices")
async def get_invoices(
    tenant_id: str,
    status: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get invoices from Xero"""
    # Get token for tenant
    token_data = token_storage.get_token(tenant_id)
    if not token_data:
        raise HTTPException(status_code=401, detail="Tenant not authorized")
    
    # Check if token is expired and refresh if needed
    if token_storage.is_token_expired(tenant_id):
        try:
            token_data = await xero_oauth_manager.refresh_token(token_data['refresh_token'])
            token_storage.save_token(tenant_id, token_data)
        except Exception as e:
            raise HTTPException(status_code=401, detail="Failed to refresh token")
    
    # Get invoices
    try:
        api_client = xero_oauth_manager.create_api_client(token_data['access_token'])
        accounting_api = AccountingApi(api_client)
        
        # Build where clause
        where = f"Status==\"{status}\"" if status else None
        
        invoices = accounting_api.get_invoices(
            xero_tenant_id=tenant_id,
            where=where,
            order="InvoiceNumber DESC",
            page=1
        )
        
        # Convert to simple dict
        invoice_data = []
        for invoice in invoices.invoices:
            invoice_data.append({
                "invoice_id": invoice.invoice_id,
                "invoice_number": invoice.invoice_number,
                "contact_name": invoice.contact.name if invoice.contact else None,
                "date": invoice.date.isoformat() if invoice.date else None,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "status": invoice.status,
                "total": float(invoice.total) if invoice.total else 0,
                "amount_due": float(invoice.amount_due) if invoice.amount_due else 0
            })
        
        return {
            "tenant_id": tenant_id,
            "count": len(invoice_data),
            "invoices": invoice_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)