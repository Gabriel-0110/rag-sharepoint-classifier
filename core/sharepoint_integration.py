#!/usr/bin/env python3
"""
SharePoint metadata update utilities
"""
import requests
import json
import os
from msal import ConfidentialClientApplication
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_access_token():
    """Get Microsoft Graph API access token"""
    try:
        app = ConfidentialClientApplication(
            os.getenv("CLIENT_ID"),
            authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
            client_credential=os.getenv("CLIENT_SECRET")
        )
        
        result = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
        
        if result and "access_token" in result:
            return result["access_token"]
        else:
            error_msg = "Unknown error"
            if result and "error_description" in result:
                error_msg = result["error_description"]
            logger.error(f"Token acquisition failed: {error_msg}")
            return None
            
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return None

def update_metadata(item_id: str, filename: str, doc_type: str, doc_category: str) -> bool:
    """
    Update SharePoint document metadata
    
    Args:
        item_id: SharePoint list item ID
        filename: Document filename
        doc_type: Classified document type
        doc_category: Classified document category
        
    Returns:
        bool: Success status
    """
    try:
        token = get_access_token()
        if not token:
            logger.error("Failed to get access token")
            return False
        
        site_id = os.getenv("SITE_ID")
        list_id = os.getenv("LIST_ID")
        
        if not all([site_id, list_id]):
            logger.error("Missing SharePoint configuration (SITE_ID, LIST_ID)")
            return False
        
        # Update metadata via Graph API
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items/{item_id}/fields"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "Document_x0020_Type": doc_type,
            "Document_x0020_Category": doc_category
        }
        
        response = requests.patch(url, json=data, headers=headers)
        
        if response.status_code in [200, 204]:
            logger.info(f"Successfully updated metadata for {filename}: {doc_type} -> {doc_category}")
            return True
        else:
            logger.error(f"Failed to update metadata: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Metadata update failed: {e}")
        return False

def batch_update_metadata(updates: list) -> dict:
    """
    Batch update multiple documents
    
    Args:
        updates: List of update dictionaries with keys: item_id, filename, doc_type, doc_category
        
    Returns:
        dict: Summary of results
    """
    results = {"success": 0, "failed": 0, "errors": []}
    
    for update in updates:
        try:
            success = update_metadata(
                update["item_id"],
                update["filename"], 
                update["doc_type"],
                update["doc_category"]
            )
            
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Failed to update {update['filename']}")
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Error updating {update['filename']}: {e}")
    
    return results

if __name__ == "__main__":
    # Test metadata update
    test_result = update_metadata("123", "test_document.pdf", "Legal Brief", "Immigration Appeals")
    print(f"Update result: {test_result}")
