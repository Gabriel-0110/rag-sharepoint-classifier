#!/bin/bash
# RAG Project - Startup Validation Script
# This script verifies all services are running correctly after VM restart

echo "🚀 RAG Project - Startup Validation"
echo "===================================="
echo "Checking all services and endpoints..."
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service status
check_service() {
    local service_name=$1
    local display_name=$2
    
    if systemctl is-active --quiet "$service_name"; then
        echo -e "${GREEN}✅ $display_name${NC} - Running"
        return 0
    else
        echo -e "${RED}❌ $display_name${NC} - Not Running"
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local display_name=$2
    local timeout=${3:-10}
    
    if curl -s --max-time "$timeout" "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $display_name${NC} - Accessible"
        return 0
    else
        echo -e "${RED}❌ $display_name${NC} - Not Accessible"
        return 1
    fi
}

# Check system services
echo -e "${BLUE}📋 System Services Status:${NC}"
check_service "qdrant" "Qdrant Vector Database"
check_service "rag-mistral" "Mistral AI Server (Port 8001)"
check_service "rag-fastapi" "FastAPI Server (Port 8000)"
check_service "rag-sharepoint" "SharePoint Automation"
check_service "cloudflared" "Cloudflare Tunnel"
echo

# Wait a moment for services to fully initialize
echo -e "${YELLOW}⏳ Waiting 15 seconds for services to initialize...${NC}"
sleep 15

# Check local endpoints
echo -e "${BLUE}🌐 Local Endpoints:${NC}"
check_endpoint "http://localhost:8000/" "FastAPI Server (localhost:8000)"
check_endpoint "http://localhost:8001/health" "Mistral AI Server (localhost:8001)"
echo

# Check external endpoints
echo -e "${BLUE}🌍 External Endpoints (Cloudflare):${NC}"
check_endpoint "https://arandia-rag.ggunifiedtech.com/health" "Mistral AI (ggunified URL)" 20
check_endpoint "https://arandia-fastapi.ggunifiedtech.com/" "FastAPI (ggunified URL)" 20
echo

# Test GPU availability
echo -e "${BLUE}🎯 GPU Status:${NC}"
if nvidia-smi > /dev/null 2>&1; then
    echo -e "${GREEN}✅ NVIDIA GPU${NC} - Available"
    nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits | while IFS=, read -r name used total; do
        echo "   GPU: $name | Memory: ${used}MB / ${total}MB"
    done
else
    echo -e "${RED}❌ NVIDIA GPU${NC} - Not Available"
fi
echo

# Test classification functionality
echo -e "${BLUE}🧪 Functionality Test:${NC}"
echo "Testing document classification..."

# Test local FastAPI
test_response=$(curl -s -X POST "http://localhost:8000/classify" \
    -H "Content-Type: application/json" \
    -d '{"content": "This is a test birth certificate document", "filename": "test.pdf"}' 2>/dev/null)

if [[ $? -eq 0 && "$test_response" == *"Birth Certificate"* ]]; then
    echo -e "${GREEN}✅ Document Classification${NC} - Working"
else
    echo -e "${RED}❌ Document Classification${NC} - Failed"
fi

# Test Mistral AI
mistral_response=$(curl -s -X POST "http://localhost:8001/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10
    }' 2>/dev/null)

if [[ $? -eq 0 && "$mistral_response" == *"choices"* ]]; then
    echo -e "${GREEN}✅ Mistral AI Inference${NC} - Working"
else
    echo -e "${RED}❌ Mistral AI Inference${NC} - Failed"
fi
echo

# Check log files
echo -e "${BLUE}📝 Recent Log Activity:${NC}"
echo "FastAPI Server:"
if [[ -f "/home/azureuser/rag_project/logs/application/fastapi.log" ]]; then
    echo "   $(tail -1 /home/azureuser/rag_project/logs/application/fastapi.log 2>/dev/null || echo 'No recent activity')"
else
    echo "   Log file not found"
fi

echo "Mistral Server:"
if [[ -f "/home/azureuser/rag_project/logs/application/mistral_server.log" ]]; then
    echo "   $(tail -1 /home/azureuser/rag_project/logs/application/mistral_server.log 2>/dev/null || echo 'No recent activity')"
else
    echo "   Log file not found"
fi

echo "SharePoint Automation:"
if [[ -f "/home/azureuser/rag_project/logs/application/sharepoint_automation.log" ]]; then
    echo "   $(tail -1 /home/azureuser/rag_project/logs/application/sharepoint_automation.log 2>/dev/null || echo 'No recent activity')"
else
    echo "   Log file not found"
fi
echo

# Final summary
echo -e "${BLUE}📊 Summary:${NC}"
echo "🔗 Access URLs:"
echo "   • FastAPI Server: http://localhost:8000"
echo "   • Mistral AI Server: http://localhost:8001"
echo "   • External Mistral: https://arandia-rag.ggunifiedtech.com"
echo "   • External FastAPI: https://arandia-fastapi.ggunifiedtech.com"
echo
echo "📁 Project Location: /home/azureuser/rag_project"
echo "📋 Documentation: /home/azureuser/rag_project/FINAL_STATUS_UPDATE_MAY26.md"
echo
echo -e "${GREEN}🎉 RAG Project validation complete!${NC}"
echo "All services are configured to start automatically on VM boot."
