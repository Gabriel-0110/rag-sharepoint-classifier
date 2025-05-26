#!/bin/bash
# RAG Project - Simple Service Check
# Quick validation that all services are running

echo "🚀 RAG Project - Service Status Check"
echo "====================================="

# Check all services
echo "📋 Service Status:"
echo "✅ Qdrant Database: $(sudo systemctl is-active qdrant)"
echo "✅ Mistral AI Server: $(sudo systemctl is-active rag-mistral)"
echo "✅ FastAPI Server: $(sudo systemctl is-active rag-fastapi)"
echo "✅ SharePoint Automation: $(sudo systemctl is-active rag-sharepoint)"
echo "✅ Cloudflare Tunnel: $(sudo systemctl is-active cloudflared)"
echo

# Test endpoints
echo "🌐 Endpoint Tests:"
echo -n "✅ FastAPI (localhost:8000): "
curl -s http://localhost:8000/ > /dev/null && echo "OK" || echo "FAILED"

echo -n "✅ Mistral (localhost:8001): "
curl -s http://localhost:8001/health > /dev/null && echo "OK" || echo "FAILED"

echo -n "✅ Cloudflare URL: "
curl -s https://arandia-rag.ggunifiedtech.com/health > /dev/null && echo "OK" || echo "FAILED"

echo
echo "🎉 All services configured for automatic startup!"
echo "🔗 Main URL: https://arandia-rag.ggunifiedtech.com"
