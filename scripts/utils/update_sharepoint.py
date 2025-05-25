from dotenv import load_dotenv
import os
import requests
from msal import ConfidentialClientApplication
from log_classification import log_classification_result

# Load environment variables
load_dotenv()

TENANT_ID     = os.getenv("TENANT_ID")
CLIENT_ID     = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SITE_ID       = os.getenv("SITE_ID")
LIST_ID       = os.getenv("LIST_ID")

def update_metadata(item_id: str, doc_type: str, doc_category: str, filename: str):
    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET, SITE_ID, LIST_ID]):
        raise ValueError("Missing required environment variables.")

    # Authenticate
    app = ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
    )
    token_result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

    if "access_token" not in token_result:
        raise RuntimeError("Failed to acquire access token.")

    access_token = token_result['access_token']

    # Compose request
    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{LIST_ID}/items/{item_id}/fields"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "Document_x0020_Type": doc_type,
        "Document_x0020_Category": doc_category,
    }

    # Send PATCH request
    response = requests.patch(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Metadata updated for {filename}")
        log_classification_result(filename, item_id, doc_type, doc_category)
    else:
        print(f"❌ Failed to update {filename}: {response.text}")

# Example usage (optional test call)
if __name__ == "__main__":
    update_metadata(
        item_id="4273",
        doc_type="Contract",
        doc_category="Corporate",
        filename="ABDENNOUR HARCHAOUI"
    )
