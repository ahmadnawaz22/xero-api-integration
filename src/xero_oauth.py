import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from xero_python.api_client import ApiClient
from xero_python.accounting import AccountingApi
from xero_python.identity import IdentityApi
import httpx
from src.config import settings

class XeroOAuth2Manager:
    def __init__(self):
        self.client_id = settings.xero_client_id
        self.client_secret = settings.xero_client_secret
        self.redirect_uri = settings.xero_redirect_uri
        self.scope = "offline_access accounting.transactions accounting.contacts accounting.settings"
        self.state = "xero-api-state"
        
    def get_authorization_url(self) -> str:
        """Generate the URL to redirect users to Xero for authorization"""
        auth_url = (
            "https://login.xero.com/identity/connect/authorize?"
            f"response_type=code&"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={self.scope}&"
            f"state={self.state}"
        )
        return auth_url
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        token_url = "https://identity.xero.com/connect/token"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token"""
        token_url = "https://identity.xero.com/connect/token"
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
    
    def create_api_client(self, access_token: str) -> ApiClient:
        """Create an API client with the given access token"""
        # Create a simple API client
        api_client = ApiClient()
        
        # Set the access token directly in the configuration
        api_client.configuration.access_token = access_token
        
        # Add the authorization header
        api_client.set_default_header(
            'Authorization',
            f'Bearer {access_token}'
        )
        
        return api_client

# Global instance
xero_oauth_manager = XeroOAuth2Manager()