#!/usr/bin/env python3
"""
Simple SharePoint Connection Test
"""

import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env')

def test_sharepoint_connection():
    """Test basic SharePoint connection."""
    
    print("🔍 TESTING SHAREPOINT CONNECTION")
    print("=" * 50)
    
    # Check environment variables
    tenant_id = os.getenv('TENANT_ID')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    site_url = os.getenv('SHAREPOINT_SITE_URL')
    
    print(f"Tenant ID: {'✅ Present' if tenant_id else '❌ Missing'}")
    print(f"Client ID: {'✅ Present' if client_id else '❌ Missing'}")
    print(f"Client Secret: {'✅ Present' if client_secret else '❌ Missing'}")
    print(f"Site URL: {'✅ Present' if site_url else '❌ Missing'}")
    
    if not all([tenant_id, client_id, client_secret, site_url]):
        print("\n❌ Missing required SharePoint credentials")
        return False
    
    print(f"\nSite URL: {site_url}")
    
    # Test imports
    print("\n📦 Testing imports...")
    try:
        from core.sharepoint_integration import get_access_token
        print("✅ SharePoint integration imported")
    except Exception as e:
        print(f"❌ SharePoint integration import failed: {e}")
        return False
    
    # Test token acquisition
    print("\n🔑 Testing token acquisition...")
    try:
        token = get_access_token()
        if token:
            print("✅ Access token acquired successfully")
            print(f"Token length: {len(token)} characters")
        else:
            print("❌ Failed to acquire access token")
            return False
    except Exception as e:
        print(f"❌ Token acquisition failed: {e}")
        return False
    
    # Test SharePoint API call
    print("\n🌐 Testing SharePoint API access...")
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Extract site info from URL
        # Format: https://yourdomain.sharepoint.com/sites/sitename
        if not site_url:
            print("❌ site_url is None, cannot parse site info.")
            return False
        site_parts = site_url.replace('https://', '').split('/')
        domain = site_parts[0]
        site_path = '/'.join(site_parts[1:])
        
        api_url = f"https://graph.microsoft.com/v1.0/sites/{domain}:/{site_path}:/drive/root/children"
        
        print(f"API URL: {api_url}")
        
        response = requests.get(api_url, headers=headers)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            file_count = len(data.get('value', []))
            print(f"✅ SharePoint accessible - found {file_count} items")
            return True
        else:
            print(f"❌ SharePoint API error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ SharePoint API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_sharepoint_connection()
    if success:
        print("\n✅ SharePoint connection test PASSED")
    else:
        print("\n❌ SharePoint connection test FAILED")
        sys.exit(1)
