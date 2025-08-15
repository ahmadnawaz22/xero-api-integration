#!/usr/bin/env python
"""
Setup script to create .env file from .env.example
"""
import os
import shutil
import secrets

def setup_environment():
    """Create .env file with secure defaults"""
    
    # Check if .env already exists
    if os.path.exists('.env'):
        response = input('.env file already exists. Overwrite? (y/N): ')
        if response.lower() != 'y':
            print('Setup cancelled.')
            return
    
    # Copy .env.example to .env
    shutil.copy('.env.example', '.env')
    
    # Generate secure keys
    api_key = secrets.token_urlsafe(32)
    secret_key = secrets.token_urlsafe(64)
    
    # Read and update .env
    with open('.env', 'r') as f:
        content = f.read()
    
    content = content.replace('your-secret-api-key-here', api_key)
    content = content.replace('your-jwt-secret-key-here-make-it-long-and-random', secret_key)
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print('✅ Created .env file with secure keys')
    print('⚠️  Remember to update your Xero credentials in .env')

if __name__ == '__main__':
    setup_environment()