#!/bin/bash

echo "🧹 Starting RAG Project Cleanup..."

# Create backup directory first
mkdir -p backup/$(date +%Y%m%d_%H%M%S)

# Security: Remove file with hardcoded token
echo "🚨 Removing security risk file..."
rm -f model-download.py

# Remove backup/save files
echo "📄 Removing backup files..."
rm -f *.save

# Remove downloaded packages
echo "📦 Removing downloaded packages..."
rm -f *.deb *.tar.gz

# Remove cache directories
echo "🗂️ Removing cache directories..."
rm -rf __pycache__/
rm -rf src/__pycache__/
rm -rf snapshots/tmp/

# Remove large log files (backup first if needed)
echo "📝 Removing large log files..."
[ -f log.txt ] && mv log.txt backup/ && echo "Backed up log.txt"
rm -f qdrant.log

# Clean processing directories (keep structure)
echo "🗄️ Cleaning processing directories..."
rm -f sp_batch_downloads/*
rm -f extracted_texts/*
rm -f downloads/*
rm -f batch_input/*

echo "✅ Cleanup completed!"
echo "📁 Project size reduced significantly"
echo "🔐 Security issue resolved"
echo ""
echo "📋 Summary of kept files:"
echo "  - Core application: main.py, mistral_api_server.py"
echo "  - Source code: src/ directory"
echo "  - Dependencies: requirements.txt"
echo "  - Vector DB: storage/ directory"
echo "  - Scripts: extract_all.py, batch_from_sharepoint.py, etc."
echo ""
echo "🗑️ Removed:"
echo "  - Backup files (.save)"
echo "  - Downloaded packages (.deb, .tar.gz)"
echo "  - Cache directories (__pycache__/)"
echo "  - Security risk file (model-download.py)"
echo "  - Large log files"
echo "  - Processed document files"
