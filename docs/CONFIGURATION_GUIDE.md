# 🔧 Configuration Guide: Required Information

## Overview
To make the RAG Document Classification System fully operational, you need to provide specific organizational information in several configuration files. This guide identifies exactly what information is needed and where to add it.

## 📋 Required Information Checklist

### ✅ Already Configured (Based on .env file)
- SharePoint Tenant ID: `59020e57-1a7b-463f-abbe-eed76e79d47c`
- SharePoint Client ID: `3dd6ba68-931f-4790-a5a3-e70832c0b218`
- SharePoint Client Secret: `wXt8Q~3x~mT3J8Aje1JYSju_8ZcXoyB3XFaX5cgd`
- SharePoint Site ID: `02775f06-aa10-449f-a372-73b5065bb0db,b8478269-3841-4295-aa4f-28b0b78d23b6`
- SharePoint List ID: `91838f52-4597-4599-afed-959b8510b41c`
- Teams Webhook URL: `https://arandialaw.webhook.office.com/webhookb2/...`

### 🔧 Need Your Input/Verification

## 1. SharePoint Configuration
**File**: `/home/azureuser/rag_project/.env`

### Questions for You:
1. **SharePoint Site URL**: What is your complete SharePoint site URL?
   - Format: `https://[your-tenant].sharepoint.com/sites/[site-name]`
   - Current guess: `https://arandialaw.sharepoint.com/sites/[SITE_NAME]`

2. **Document Library Name**: What is the name of the SharePoint document library where documents are stored?
   - Common names: "Documents", "Shared Documents", "Legal Documents", etc.

3. **Metadata Fields**: What are the exact column names in SharePoint for:
   - Document Type field (e.g., "Document_Type", "DocType", "Type")
   - Document Category field (e.g., "Category", "Document_Category", "Classification")

## 2. Microsoft Teams Configuration
**File**: `/home/azureuser/rag_project/.env`

### Questions for You:
1. **Teams Channel**: Which Teams channel should receive notifications?
2. **Notification Preferences**: Do you want notifications for:
   - ✅ Successful classifications? (Currently: disabled)
   - ✅ Classification errors? 
   - ✅ Low confidence classifications requiring review?
   - ✅ Batch processing summaries?

## 3. Business Categories Configuration
**File**: `/home/azureuser/rag_project/enhanced/enhanced_rag_classifier.py`

### Current Categories (lines 15-35):
```python
"Corporate": "Corporate governance, board resolutions, company policies",
"Real Estate": "Property transactions, leases, zoning, development",
"Employment": "HR policies, employment contracts, workplace procedures",
"Intellectual Property": "Patents, trademarks, copyrights, licensing",
"Litigation": "Court documents, legal proceedings, disputes",
"Regulatory": "Compliance documents, regulatory filings",
"Financial": "Financial agreements, banking, investment documents",
"Technology": "Software licenses, IT agreements, technical documentation",
"Healthcare": "Medical records, healthcare compliance, patient documents",
"Other": "Documents that don't fit standard categories"
```

### Questions for You:
1. **Are these categories appropriate for your law firm?**
2. **Do you need to add/remove/modify any categories?**
3. **Are there specific legal practice areas we should add?** (e.g., Immigration, Family Law, Criminal Law, Tax Law, etc.)

## 4. Document Types Configuration
**File**: `/home/azureuser/rag_project/enhanced/enhanced_rag_classifier.py`

### Current Document Types (lines 38-50):
```python
"Contract": "Legal agreements, terms of service, licensing agreements",
"Policy": "Company policies, procedures, guidelines, handbooks",
"Communication": "Emails, memos, letters, correspondence",
"Report": "Analysis reports, research documents, summaries",
"Legal Document": "Court filings, legal briefs, affidavits, depositions",
"Financial Document": "Invoices, receipts, financial statements, budgets",
"Technical Document": "Specifications, manuals, technical guides",
"Other": "Documents that don't fit standard types"
```

### Questions for You:
1. **Are these document types sufficient for your practice?**
2. **Should we add specific legal document types?** (e.g., Pleadings, Motions, Discovery, Briefs, etc.)

## 📝 Action Items for You

### Immediate Actions Required:

1. **Verify SharePoint Settings**:
   - Confirm the SharePoint site URL
   - Verify the document library name
   - Check the exact names of metadata columns

2. **Enable Teams Notifications** (Optional but Recommended):
   - Set `TEAMS_NOTIFICATIONS_ENABLED=true` in `.env`
   - Test the webhook URL is working

3. **Customize Categories** (Optional):
   - Review and modify the business categories to match your practice areas
   - Add any specialized legal categories you need

### Information I Need From You:

**Please provide the following information:**

```
1. SharePoint Site URL: https://arandialaw.sharepoint.com/sites/[WHAT_IS_YOUR_SITE_NAME]

2. SharePoint Document Library Name: [LIBRARY_NAME]

3. SharePoint Metadata Column Names:
   - Document Type Column: [COLUMN_NAME]
   - Document Category Column: [COLUMN_NAME]

4. Teams Notifications:
   - Enable notifications? [YES/NO]
   - Which types of notifications do you want?

5. Business Categories:
   - Are the current categories sufficient? [YES/NO]
   - What categories should be added/removed/modified?

6. Document Types:
   - Are the current types sufficient? [YES/NO]
   - What types should be added/removed/modified?
```

## 🚀 How to Update Configurations

### Once you provide the information, I will help you update:

1. **`.env` file** - SharePoint URLs and settings
2. **Enhanced RAG Classifier** - Business categories and document types  
3. **SharePoint Automation** - Column mappings and library settings
4. **Teams Integration** - Notification preferences

### Test Configuration:
After updating, we'll run:
```bash
# Test SharePoint connection
python scripts/utils/test_sharepoint_connection.py

# Test Teams notifications
python scripts/utils/test_teams_notifications.py

# Run full system validation
python tests/system/final_system_test.py
```

## 📞 Next Steps

**Please provide the requested information above, and I will:**
1. Update all configuration files with your specific details
2. Create test scripts to validate the connections
3. Run comprehensive tests to ensure everything works
4. Provide a final deployment checklist

The system is 100% complete - we just need your organizational details to make it fully operational for your environment!
