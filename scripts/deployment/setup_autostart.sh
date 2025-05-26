#!/bin/bash
# Setup automatic startup for all RAG project services

echo "🚀 Setting up automatic startup for RAG project services..."

# Project directory
PROJECT_DIR="/home/azureuser/rag_project"
SCRIPTS_DIR="$PROJECT_DIR/scripts/deployment"

# Environment setup
CONDA_PATH="/home/azureuser/miniconda3"
RAG_ENV="rag"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📋 Creating systemd service files...${NC}"

# 1. FastAPI Server Service
sudo tee /etc/systemd/system/rag-fastapi.service > /dev/null << EOF
[Unit]
Description=RAG FastAPI Classification Server
After=network.target
Wants=qdrant.service
After=qdrant.service

[Service]
Type=simple
User=azureuser
Group=azureuser
WorkingDirectory=$PROJECT_DIR/core
Environment=PATH=$CONDA_PATH/envs/$RAG_ENV/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$CONDA_PATH/envs/$RAG_ENV/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
KillMode=mixed
KillSignal=SIGINT
TimeoutStopSec=30

# Logging
StandardOutput=append:$PROJECT_DIR/logs/application/fastapi.log
StandardError=append:$PROJECT_DIR/logs/application/fastapi.log

[Install]
WantedBy=multi-user.target
EOF

# 2. Mistral API Server Service
sudo tee /etc/systemd/system/rag-mistral.service > /dev/null << EOF
[Unit]
Description=RAG Mistral AI Server
After=network.target nvidia-persistenced.service
Wants=nvidia-persistenced.service

[Service]
Type=simple
User=azureuser
Group=azureuser
WorkingDirectory=$PROJECT_DIR/core
Environment=PATH=$CONDA_PATH/envs/$RAG_ENV/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=CUDA_VISIBLE_DEVICES=0
ExecStart=$CONDA_PATH/envs/$RAG_ENV/bin/python mistral_api_server.py
Restart=always
RestartSec=10
KillMode=mixed
KillSignal=SIGINT
TimeoutStopSec=60

# Logging
StandardOutput=append:$PROJECT_DIR/logs/application/mistral_server.log
StandardError=append:$PROJECT_DIR/logs/application/mistral_server.log

[Install]
WantedBy=multi-user.target
EOF

# 3. Updated SharePoint Automation Service (system-level)
sudo tee /etc/systemd/system/rag-sharepoint.service > /dev/null << EOF
[Unit]
Description=RAG SharePoint Document Automation
After=network.target rag-fastapi.service rag-mistral.service
Wants=rag-fastapi.service rag-mistral.service

[Service]
Type=simple
User=azureuser
Group=azureuser
WorkingDirectory=$PROJECT_DIR/core
Environment=PATH=$CONDA_PATH/envs/$RAG_ENV/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$CONDA_PATH/envs/$RAG_ENV/bin/python sharepoint_automation.py
Restart=always
RestartSec=5
KillMode=mixed
KillSignal=SIGINT
TimeoutStopSec=30

# Logging
StandardOutput=append:$PROJECT_DIR/logs/application/sharepoint_automation.log
StandardError=append:$PROJECT_DIR/logs/application/sharepoint_automation.log

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Service files created successfully${NC}"

# Stop any running processes first
echo -e "${YELLOW}🛑 Stopping current processes...${NC}"
sudo systemctl stop rag-classifier 2>/dev/null || true
sudo systemctl stop mistral-api 2>/dev/null || true
systemctl --user stop sharepoint-automation 2>/dev/null || true
sudo systemctl stop rag-sharepoint 2>/dev/null || true

# Kill any remaining processes
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "mistral_api_server.py" 2>/dev/null || true
pkill -f "sharepoint_automation.py" 2>/dev/null || true

echo -e "${YELLOW}🔄 Reloading systemd daemon...${NC}"
sudo systemctl daemon-reload

echo -e "${YELLOW}🟢 Enabling services for auto-start...${NC}"
sudo systemctl enable rag-fastapi.service
sudo systemctl enable rag-mistral.service
sudo systemctl enable rag-sharepoint.service
sudo systemctl enable qdrant.service
sudo systemctl enable cloudflared.service

echo -e "${YELLOW}🚀 Starting services...${NC}"
sudo systemctl start qdrant.service
sleep 2
sudo systemctl start rag-mistral.service
sleep 5
sudo systemctl start rag-fastapi.service
sleep 3
sudo systemctl start rag-sharepoint.service

echo -e "${GREEN}✅ All services configured for automatic startup!${NC}"

echo -e "${YELLOW}📊 Service Status:${NC}"
echo "FastAPI Server (Port 8000):"
sudo systemctl is-active rag-fastapi || echo "❌ Not running"
echo "Mistral Server (Port 8001):"
sudo systemctl is-active rag-mistral || echo "❌ Not running"
echo "SharePoint Automation:"
sudo systemctl is-active rag-sharepoint || echo "❌ Not running"
echo "Qdrant Vector DB:"
sudo systemctl is-active qdrant || echo "❌ Not running"
echo "Cloudflare Tunnel:"
sudo systemctl is-active cloudflared || echo "❌ Not running"

echo -e "${GREEN}🎉 Setup complete! All services will start automatically on boot.${NC}"
echo -e "${YELLOW}💡 Use 'sudo systemctl status <service-name>' to check individual service status${NC}"
echo -e "${YELLOW}🔧 Use 'sudo journalctl -u <service-name> -f' to view service logs${NC}"

# Test the services
echo -e "${YELLOW}🧪 Testing services in 10 seconds...${NC}"
sleep 10

echo "Testing FastAPI (Port 8000):"
curl -s http://localhost:8000/ | jq . 2>/dev/null || curl -s http://localhost:8000/

echo -e "\nTesting Mistral API (Port 8001):"
curl -s http://localhost:8001/health | jq . 2>/dev/null || curl -s http://localhost:8001/health

echo -e "\n${GREEN}🌐 Cloudflare URL: https://arandia-rag.ggunifiedtech.com${NC}"
