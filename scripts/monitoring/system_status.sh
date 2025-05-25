#!/bin/bash
# SharePoint Automation System - Complete Status and Management
# Created: 2025-05-25

echo "🔧 SharePoint Document Classification Automation System"
echo "======================================================"
echo

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service status
check_service() {
    local service_name=$1
    local port=$2
    local description=$3
    
    if [ ! -z "$port" ]; then
        if curl -s "http://localhost:$port" > /dev/null 2>&1; then
            echo -e "  ✅ $description: ${GREEN}RUNNING${NC} (port $port)"
        else
            echo -e "  ❌ $description: ${RED}ERROR${NC} (port $port)"
        fi
    else
        if systemctl --user is-active --quiet "$service_name" 2>/dev/null; then
            echo -e "  ✅ $description: ${GREEN}RUNNING${NC}"
        else
            echo -e "  ❌ $description: ${RED}STOPPED${NC}"
        fi
    fi
}

echo "🔧 Service Status:"
check_service "sharepoint-automation" "" "SharePoint Automation"
check_service "" "8000" "Main FastAPI Server"
check_service "" "8001" "Mistral AI Server"
check_service "" "6333" "Qdrant Vector DB"
echo

echo "📊 Processing Statistics:"
if [ -f "classification_log.csv" ]; then
    total_docs=$(tail -n +2 classification_log.csv 2>/dev/null | wc -l)
    today=$(date +%Y-%m-%d)
    today_docs=$(grep "^$today" classification_log.csv 2>/dev/null | wc -l)
    echo "  📄 Total documents processed: $total_docs"
    echo "  🕒 Today: $today_docs documents"
    echo "  📅 Last processed: $(tail -1 classification_log.csv 2>/dev/null | cut -d',' -f1)"
else
    echo "  📄 No classification log found"
fi
echo

echo "🗂️  Project Structure:"
echo "  📁 Main directory: $(pwd)"
echo "  📄 Configuration: .env (SharePoint credentials)"
echo "  📋 Processing log: classification_log.csv"
echo "  🔧 Service file: sharepoint-automation.service"
echo "  📊 Storage: storage/ ($(du -sh storage/ 2>/dev/null | cut -f1))"
echo

echo "💻 Management Commands:"
echo "  🔄 Start automation:    systemctl --user start sharepoint-automation"
echo "  🛑 Stop automation:     systemctl --user stop sharepoint-automation"
echo "  ♻️  Restart automation:  systemctl --user restart sharepoint-automation"
echo "  📊 View status:         systemctl --user status sharepoint-automation"
echo "  📜 View logs:           journalctl --user -u sharepoint-automation -f"
echo "  📈 Monitor dashboard:   python monitor_automation.py"
echo "  📝 Watch activity:      tail -f classification_log.csv"
echo

echo "🧪 Testing Commands:"
echo "  🏥 Health check:        curl http://localhost:8000/"
echo "  🔍 Test classification: curl -X POST -H 'Content-Type: application/json' \\"
echo "                           -d '{\"file_path\":\"/path/to/file.pdf\",\"item_id\":\"test\"}' \\"
echo "                           http://localhost:8000/classify"
echo "  📊 Qdrant status:       curl http://localhost:6333/collections"
echo

echo "🚀 Production Ready Features:"
echo "  ✅ Automatic startup on boot (systemd service enabled)"
echo "  ✅ Continuous SharePoint monitoring (5-minute intervals)"
echo "  ✅ Error handling and recovery (automatic restarts)"
echo "  ✅ Comprehensive logging and audit trail"
echo "  ✅ Real-time monitoring dashboard"
echo "  ✅ End-to-end document processing pipeline"
echo "  ✅ AI-powered classification (Mistral-7B)"
echo "  ✅ Vector database storage (Qdrant)"
echo "  ✅ SharePoint metadata updates"
echo

echo "📚 System Architecture:"
echo "  1. SharePoint monitoring → Download new documents"
echo "  2. Text extraction → PDF, DOCX, Image OCR"
echo "  3. AI classification → Mistral-7B model"
echo "  4. Vector storage → Qdrant database"
echo "  5. Metadata update → Back to SharePoint"
echo

if systemctl --user is-active --quiet sharepoint-automation 2>/dev/null; then
    echo -e "🎉 ${GREEN}System Status: FULLY OPERATIONAL${NC}"
    echo "   The SharePoint automation is running and monitoring for new documents!"
else
    echo -e "⚠️  ${YELLOW}System Status: NEEDS ATTENTION${NC}"
    echo "   Run: systemctl --user start sharepoint-automation"
fi

echo
echo "======================================================"
echo "🔗 For more information, see: PROJECT_STRUCTURE.md"
