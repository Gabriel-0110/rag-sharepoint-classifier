#!/bin/bash
# RAG System Health Check and Recovery Script
# Run this script periodically to prevent CUDA memory issues

LOG_FILE="/home/azureuser/rag_project/logs/application/system_health.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting RAG System Health Check" >> "$LOG_FILE"

# Function to log with timestamp
log_message() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
    echo "$1"
}

# Check GPU memory usage
GPU_MEMORY=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | head -1)
if [ -n "$GPU_MEMORY" ]; then
    USED=$(echo $GPU_MEMORY | cut -d',' -f1 | tr -d ' ')
    TOTAL=$(echo $GPU_MEMORY | cut -d',' -f2 | tr -d ' ')
    USAGE_PERCENT=$((USED * 100 / TOTAL))
    
    log_message "GPU Memory: ${USED}MB / ${TOTAL}MB (${USAGE_PERCENT}%)"
    
    if [ $USAGE_PERCENT -gt 95 ]; then
        log_message "CRITICAL: GPU memory usage above 95%, restarting SharePoint service"
        sudo systemctl restart rag-sharepoint.service
        sleep 10
    elif [ $USAGE_PERCENT -gt 85 ]; then
        log_message "WARNING: GPU memory usage above 85%"
    fi
else
    log_message "ERROR: Could not get GPU memory information"
fi

# Check if all services are running
SERVICES=("rag-fastapi.service" "rag-mistral.service" "rag-sharepoint.service")
ALL_RUNNING=true

for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service"; then
        log_message "✅ $service is running"
    else
        log_message "❌ $service is NOT running"
        ALL_RUNNING=false
        
        # Try to restart the failed service
        log_message "Attempting to restart $service"
        sudo systemctl restart "$service"
        sleep 5
        
        if systemctl is-active --quiet "$service"; then
            log_message "✅ Successfully restarted $service"
        else
            log_message "❌ Failed to restart $service"
        fi
    fi
done

# Test classification endpoint
if curl -s --connect-timeout 5 http://localhost:8000/health > /dev/null; then
    log_message "✅ Classification endpoint is responding"
else
    log_message "❌ Classification endpoint is not responding"
    log_message "Restarting FastAPI service"
    sudo systemctl restart rag-fastapi.service
fi

# Check for recent classification activity
RECENT_CLASSIFICATIONS=$(tail -5 /home/azureuser/rag_project/classification_log.csv | wc -l)
if [ $RECENT_CLASSIFICATIONS -gt 0 ]; then
    LAST_CLASSIFICATION=$(tail -1 /home/azureuser/rag_project/classification_log.csv | cut -d',' -f1)
    log_message "Last classification: $LAST_CLASSIFICATION"
else
    log_message "No recent classifications found"
fi

log_message "Health check completed"
echo "[$TIMESTAMP] ===========================================" >> "$LOG_FILE"
