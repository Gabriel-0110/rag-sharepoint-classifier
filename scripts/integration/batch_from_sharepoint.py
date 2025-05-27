#!/usr/bin/env python
"""
Batch-classify every file in the “Case-Management” library
and write Document Type / Category back to SharePoint.

Prereqs:
  • env vars: TENANT_ID, CLIENT_ID, CLIENT_SECRET, SITE_ID, LIST_ID
  • helper modules: extract_all.py, embed_test.py, update_sharepoint.py
"""

import os, uuid, requests, csv
from msal   import ConfidentialClientApplication
from dotenv import load_dotenv
from scripts.utils.extract_all import extract_text_from_file
from scripts.utils.embed_test import classify_with_llm
from core.sharepoint_integration import update_metadata  # (item_id, filename, doc_type, doc_category)

# ───────── 0. config ─────────
load_dotenv()
TENANT_ID  = os.getenv("TENANT_ID")
CLIENT_ID  = os.getenv("CLIENT_ID")
CLIENT_SEC = os.getenv("CLIENT_SECRET")
SITE_ID    = os.getenv("SITE_ID")
LIST_ID    = os.getenv("LIST_ID")

# ───────── 1. auth ───────────
app   = ConfidentialClientApplication(
           CLIENT_ID,
           authority=f"https://login.microsoftonline.com/{TENANT_ID}",
           client_credential=CLIENT_SEC)
tok   = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
if not tok or "access_token" not in tok:
    error_msg = tok.get('error_description', tok) if isinstance(tok, dict) else str(tok)
    raise RuntimeError(f"Failed to acquire token: {error_msg}")
HEADERS = {"Authorization": f"Bearer {tok['access_token']}"}

# ───────── 2. helpers ────────
LOG_CSV      = "classification_log.csv"
DOWNLOAD_DIR = "sp_batch_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def append_log(fname, doc_type, cat, item_id):
    with open(LOG_CSV, "a", newline="") as fh:
        csv.writer(fh).writerow([fname, doc_type, cat, item_id])

logged_files = set()
if os.path.exists(LOG_CSV):
    with open(LOG_CSV) as fh:
        logged_files = {row[0] for row in csv.reader(fh)}

# ---- LLM-prompt length guard ----
MAX_MODEL_TOKENS    = 2048
RESERVED_COMPLETION = 200
SAFE_PROMPT_TOKENS  = MAX_MODEL_TOKENS - RESERVED_COMPLETION - 48   # spare room

def trim_for_llm(raw_text: str,
                 max_tokens: int = SAFE_PROMPT_TOKENS) -> str:
    """Keep only the first max_tokens words (~tokens)."""
    words = raw_text.split()
    return " ".join(words[:max_tokens]) if len(words) > max_tokens else raw_text

def walk_folder(drive_id: str, item_id: str, depth: int = 0):
    """Yield every file (recursively) inside a folder (max 3 levels)."""
    if depth > 2:
        return
    url  = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/children"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print(f"❌  Graph error {resp.status_code} while reading children of {item_id}")
        return
    for child in resp.json().get("value", []):
        if "file" in child:
            yield child
        elif "folder" in child:
            yield from walk_folder(drive_id, child["id"], depth + 1)

# ───────── 3. fetch cases ─────
print("📋 Fetching Case-Management list …")
items_url = (f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
             f"/lists/{LIST_ID}/items?$expand=fields&$top=9999")
items = requests.get(items_url, headers=HEADERS).json().get("value", [])
items.sort(key=lambda it: it["fields"].get("FileLeafRef", "").lower())

# ───────── 4. main loop ───────
processed_files = 0
MAX_FILES = 5  # Limit for test run
for item in items:
    if processed_files >= MAX_FILES:
        break
    item_id   = item["id"]
    fields    = item["fields"]
    case_name = (fields.get("FileLeafRef") or
                 fields.get("Title") or f"Item {item_id}")

    # 4-A. locate drive/folder backing the Case
    di = requests.get(
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
        f"/lists/{LIST_ID}/items/{item_id}/driveItem",
        headers=HEADERS).json()
    drive_id, folder_id = di["parentReference"]["driveId"], di["parentReference"]["id"]

    # 4-B. collect files
    files_found = list(walk_folder(drive_id, folder_id))
    if not files_found:
        print(f"⚠️  Skipping {case_name} — no files found")
        continue

    print(f"📁 Processing folder {case_name} …")
    for child in files_found:
        filename     = child["name"]
        download_url = child.get("@microsoft.graph.downloadUrl")

        if not download_url:
            print(f"   • ⚠️  {filename} – no download URL")
            continue
        if filename in logged_files:
            print(f"   • ✅ Already processed {filename}")
            continue

        # download
        local_path = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}_{filename}")
        try:
            with open(local_path, "wb") as fh:
                fh.write(requests.get(download_url).content)
        except Exception as e:
            print(f"   • ❌ Download failed for {filename}: {e}")
            continue

        try:
            # extract & classify (with trim)
            raw_text          = extract_text_from_file(local_path)
            prompt_text       = trim_for_llm(raw_text)
            doc_type, doc_cat = classify_with_llm(prompt_text)
            print(f"   • {filename} → {doc_type} / {doc_cat}")

            # update SharePoint metadata
            status = update_metadata(item_id=item_id,
                                     filename=filename,
                                     doc_type=doc_type,
                                     doc_category=doc_cat)
            print(f"     ↳ SP update: {status}")

            append_log(filename, doc_type, doc_cat, item_id)
            logged_files.add(filename)
            processed_files += 1
            if processed_files >= MAX_FILES:
                break
        except Exception as exc:
            print(f"   • ❌ Failed on {filename}: {exc}")
    if processed_files >= MAX_FILES:
        break

print("\n🎉  Batch run complete")
