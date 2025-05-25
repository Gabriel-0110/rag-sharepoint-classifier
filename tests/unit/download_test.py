import os
import requests
from msal import ConfidentialClientApplication

# 1. Load credentials from env
tenant_id = os.environ["AZURE_TENANT_ID"]
client_id = os.environ["AZURE_CLIENT_ID"]
client_secret = os.environ["AZURE_CLIENT_SECRET"]

# 2. Acquire token
app = ConfidentialClientApplication(
    client_id=client_id,
    authority=f"https://login.microsoftonline.com/{tenant_id}",
    client_credential=client_secret,
)
token_response = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
access_token = token_response.get("access_token")
if not access_token:
    raise RuntimeError(f"No token: {token_response}")
headers = {"Authorization": f"Bearer {access_token}"}

# 3a. Get site metadata by path
site_domain = "arandialaw.sharepoint.com"
server_rel_path = "/sites/LegalServices"
site_url = f"https://graph.microsoft.com/v1.0/sites/{site_domain}:{server_rel_path}"
site_resp = requests.get(site_url, headers=headers)
site_resp.raise_for_status()
site_id = site_resp.json().get("id")
print(f"Site ID: {site_id}")

# 3b. List items in the site root
endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root/children"
resp = requests.get(endpoint, headers=headers)
resp.raise_for_status()
items = resp.json().get("value", [])
print(f"Found {len(items)} items (folders and files):")
for i, item in enumerate(items[:10], 1):
    typ = "File" if "file" in item else "Folder"
    print(f" {i}. {item['name']} ({typ})")

# 4. Find first file: try root, then scan folders
# 4a. Check root files
file_items = [item for item in items if "file" in item]
if file_items:
    target = file_items[0]
    print(f"Downloading root file: {target['name']} (id={target['id']})")
else:
    # 4b. Scan each folder for files
    folder_items = [item for item in items if "folder" in item]
    target = None
    for folder in folder_items:
        folder_id = folder["id"]
        print(f"Checking folder: {folder['name']} (id={folder_id})")
        ep2 = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{folder_id}/children"
        r2 = requests.get(ep2, headers=headers)
        r2.raise_for_status()
        items2 = r2.json().get("value", [])
        file_items2 = [itm for itm in items2 if "file" in itm]
        if file_items2:
            target = file_items2[0]
            print(f"Found file in folder '{folder['name']}': {target['name']} (id={target['id']})")
            break
    if not target:
        print("No files found in any folders.")
        exit()

# 5. Download the target file
dl_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{target['id']}/content"
r = requests.get(dl_url, headers=headers)
r.raise_for_status()

os.makedirs("downloads", exist_ok=True)
local_path = os.path.join("downloads", target["name"])
with open(local_path, "wb") as f:
    f.write(r.content)
print(f"✅ Saved file: {local_path}")
