import pandas as pd
from datetime import datetime
import os

def log_classification_result(filename, item_id, doc_type, doc_category, log_path="classification_log.csv"):
    """
    Appends a classification result to the audit log CSV file.
    Creates the file with headers if it doesn't exist.

    Parameters:
    - filename (str): The name of the file classified
    - item_id (str): SharePoint ListItem ID
    - doc_type (str): Document Type (e.g. Contract)
    - doc_category (str): Document Category (e.g. Corporate)
    - log_path (str): Path to the CSV log file
    """
    log_entry = {
        "Timestamp": datetime.utcnow().isoformat(),
        "FileName": filename,
        "SharePointID": item_id,
        "DocumentType": doc_type,
        "DocumentCategory": doc_category
    }

    df = pd.DataFrame([log_entry])
    file_exists = os.path.isfile(log_path)

    df.to_csv(log_path, mode='a', header=not file_exists, index=False)

    print(f"✅ Logged classification → {filename} | {doc_type} | {doc_category}")
