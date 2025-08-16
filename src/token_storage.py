import json
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class TokenStorage:
    """Simple file-based token storage for development.
    In production, use a database instead."""
    
    def __init__(self, storage_path: str = "tokens.json"):
        self.storage_path = storage_path
        
    def save_token(self, tenant_id: str, token_data: Dict[str, Any]) -> None:
        """Save token data for a specific tenant"""
        # Load existing tokens
        tokens = self._load_tokens()
        
        # Add expiry timestamp
        token_data['expires_at'] = (
            datetime.now() + timedelta(seconds=token_data.get('expires_in', 1800))
        ).isoformat()
        
        # Save token for this tenant
        tokens[tenant_id] = token_data
        
        # Write back to file
        with open(self.storage_path, 'w') as f:
            json.dump(tokens, f, indent=2)
    
    def get_token(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get token data for a specific tenant"""
        tokens = self._load_tokens()
        return tokens.get(tenant_id)
    
    def is_token_expired(self, tenant_id: str) -> bool:
        """Check if token is expired"""
        token_data = self.get_token(tenant_id)
        if not token_data or 'expires_at' not in token_data:
            return True
        
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        return datetime.now() >= expires_at
    
    def _load_tokens(self) -> Dict[str, Any]:
        """Load tokens from file"""
        if not os.path.exists(self.storage_path):
            return {}
        
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def clear_tokens(self) -> None:
        """Clear all stored tokens"""
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)

# Global instance
token_storage = TokenStorage()