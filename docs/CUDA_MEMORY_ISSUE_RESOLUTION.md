# CUDA Memory Issue Resolution and Prevention

## Issue Summary
**Date:** May 26, 2025  
**Problem:** Recently uploaded files were not being classified due to CUDA out of memory errors in the SharePoint automation service.

## Root Cause Analysis

### What Happened
1. **GPU Memory Exhaustion**: The system has a 4GB GPU (NVIDIA A10-4Q), which was nearly fully utilized:
   - Mistral AI Server: ~2.5GB
   - FastAPI Server: ~485MB
   - System/Display: ~180MB
   - **Total Usage**: ~3.2GB out of 4GB (79% utilization)

2. **Classification Service Failure**: When the SharePoint automation tried to initialize the `EnhancedRAGClassifier`, it attempted to load the SentenceTransformer model on GPU, causing a CUDA out of memory error.

3. **Silent Failure**: The service continued running but couldn't process new files due to the initialization failure.

## Immediate Fixes Applied

### 1. Force CPU Usage for Embedding Model
**File Modified:** `/home/azureuser/rag_project/core/enhanced_rag_classifier.py`
```python
# Changed from:
self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# To:
self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
```

### 2. Fixed String Formatting Issues
- Corrected escape sequences in the `_build_rag_prompt` method
- Ensured proper prompt formatting for the LLM

### 3. Service Restart
- Restarted the SharePoint automation service to apply the fixes
- Confirmed all services are now running properly

## Current System Status ✅

### GPU Memory Usage
- **Current**: 3.2GB / 4GB (79% - within safe limits)
- **Mistral Server**: 2.5GB (primary LLM processing)
- **FastAPI Server**: 485MB (API endpoints)
- **Embedding Model**: Now using CPU (prevents conflicts)

### Service Status
- ✅ **rag-fastapi.service**: Running (port 8000)
- ✅ **rag-mistral.service**: Running (port 8001)
- ✅ **rag-sharepoint.service**: Running (document processing)
- ✅ **Classification Endpoint**: Responding properly

### Recent Activity
- Last successful classification: 2025-05-26T01:09:44
- System is now processing files with updated categories and types
- Enhanced classification using modern Immigration & Criminal Law taxonomy

## Prevention Measures Implemented

### 1. Automated Health Monitoring
**Script:** `/home/azureuser/rag_project/scripts/monitoring/health_check.sh`

**Features:**
- Monitors GPU memory usage every 10 minutes
- Checks service status for all RAG components
- Tests classification endpoint responsiveness
- Automatically restarts services if issues detected
- Logs all activities to `/home/azureuser/rag_project/logs/application/system_health.log`

**Thresholds:**
- **Warning**: 85% GPU memory usage
- **Critical**: 95% GPU memory usage (triggers service restart)

### 2. Cron Job Automation
```bash
# Runs health check every 10 minutes
*/10 * * * * /home/azureuser/rag_project/scripts/monitoring/health_check.sh
```

### 3. Memory-Aware Architecture
- **GPU**: Reserved for Mistral LLM (primary inference)
- **CPU**: Used for embedding models and preprocessing
- **Separation of Concerns**: Prevents resource conflicts

## Updated Document Classification System

### New Categories (Immigration & Criminal Law Focus)
- **Immigration - Family & Individual**
- **Immigration - Employment & Business** 
- **Immigration - Citizenship & Naturalization**
- **Immigration - Removal Defense & Asylum**
- **Immigration - Waivers & Appeals**
- **Immigration - Consular Processing & Travel**
- **Immigration - USCIS & Agency Matters**
- **Criminal Defense - Federal Offenses**
- **Criminal Defense - State Felonies**
- **Criminal Defense - State Misdemeanors & Violations**
- **Criminal Defense - Post-Conviction Relief**
- **Criminal Defense - Immigration Consequences (Crimmigration)**
- **Criminal Defense - Investigations & Pre-Charge**
- **Client Communications**
- **Administrative & Case Management**

### Enhanced Document Types
- 60+ specialized document types covering USCIS forms, EOIR documents, criminal filings, evidence, correspondence, and administrative documents
- Modern terminology and professional descriptions
- Specific support for immigration/criminal law practice needs

## How to Monitor System Health

### Manual Check
```bash
# Run immediate health check
/home/azureuser/rag_project/scripts/monitoring/health_check.sh

# Check GPU memory
nvidia-smi

# Check service status
sudo systemctl status rag-fastapi.service rag-mistral.service rag-sharepoint.service
```

### Log Files
- **System Health**: `/home/azureuser/rag_project/logs/application/system_health.log`
- **SharePoint Automation**: `/home/azureuser/rag_project/logs/application/sharepoint_automation.log`
- **Classification Activity**: `/home/azureuser/rag_project/classification_log.csv`

### Service Logs
```bash
# Check recent SharePoint automation logs
sudo journalctl -u rag-sharepoint.service --since "1 hour ago"

# Check all RAG services
sudo systemctl status rag-*.service
```

## Expected Behavior Going Forward

1. **Automatic File Processing**: New files uploaded to SharePoint will be detected within 5 minutes
2. **Enhanced Classification**: Files will be classified using the new specialized categories and types
3. **Memory Management**: System will automatically prevent CUDA memory conflicts
4. **Self-Healing**: Services will automatically restart if issues are detected
5. **Comprehensive Logging**: All activities will be logged for troubleshooting

## Emergency Recovery Procedures

If the system stops processing files:

1. **Check GPU Memory**:
   ```bash
   nvidia-smi
   ```

2. **Restart SharePoint Service**:
   ```bash
   sudo systemctl restart rag-sharepoint.service
   ```

3. **Run Health Check**:
   ```bash
   /home/azureuser/rag_project/scripts/monitoring/health_check.sh
   ```

4. **Check Recent Logs**:
   ```bash
   tail -20 /home/azureuser/rag_project/logs/application/sharepoint_automation.log
   ```

The system is now more robust, self-monitoring, and specifically tailored for your immigration and criminal law practice needs.
