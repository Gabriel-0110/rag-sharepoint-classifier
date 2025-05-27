#!/bin/bash
# Final comprehensive cleanup script
set -e

echo "🧹 Starting FINAL cleanup of rag_project directory..."

cd /home/azureuser/rag_project

# Create essential directories if they don't exist
mkdir -p core logs data docs tests

echo "📁 Moving core files to proper locations..."

# Move core application files
if [ -f "enhanced_rag_classifier.py" ]; then
    mv enhanced_rag_classifier.py core/ 2>/dev/null || true
fi

if [ -f "sharepoint_automation.py" ]; then
    echo "✅ sharepoint_automation.py already in root (keep as main service)"
fi

if [ -f "mistral_api_server.py" ]; then
    echo "✅ mistral_api_server.py already in root (keep as main service)"
fi

if [ -f "main.py" ]; then
    echo "✅ main.py already in root (keep as FastAPI service)"
fi

# Move test files to tests directory
echo "📁 Moving test files..."
mv test_*.py tests/ 2>/dev/null || true
mv *test*.py tests/ 2>/dev/null || true
mv simple_*.py tests/ 2>/dev/null || true
mv debug_*.py tests/ 2>/dev/null || true
mv direct_*.py tests/ 2>/dev/null || true

# Move logs
echo "📁 Moving log files..."
mv *.log logs/ 2>/dev/null || true
mv *.csv logs/ 2>/dev/null || true

# Move documentation
echo "📁 Moving documentation..."
mv *.md docs/ 2>/dev/null || true

# Remove duplicate and temporary files
echo "🗑️  Removing duplicate and temporary files..."

# Remove all the completion/status/mission files (keep only essential ones)
rm -f FINAL_*.md MISSION_*.md POST_*.md SHAREPOINT_*.md 2>/dev/null || true

# Remove duplicate classifier files
rm -f enhanced_rag_classifier.py fixed_rag_classifier.py 2>/dev/null || true

# Remove cleanup scripts (keep only this one)
rm -f cleanup_*.sh organize_*.sh permanent_*.sh manage_*.sh 2>/dev/null || true

# Remove duplicate integration files
rm -f teams_integration.py trocr_integration.py 2>/dev/null || true
rm -f few_shot_learning.py confidence_scoring.py 2>/dev/null || true

# Remove update scripts (we'll recreate when needed)
rm -f update_*.py reprocess_*.py verify_*.py 2>/dev/null || true
rm -f direct_sharepoint_update.py 2>/dev/null || true

# Remove system check scripts
rm -f system_status.sh enhanced_system_check.sh final_validation.sh 2>/dev/null || true

# Remove monitoring scripts
rm -f monitor_automation.py completion_report.py 2>/dev/null || true

# Remove comprehensive/complete test files
rm -f comprehensive_*.py complete_*.py final_*.py quick_*.py 2>/dev/null || true

# Clean up any remaining clutter
rm -f *.txt 2>/dev/null || true

echo "📋 Files remaining in root directory:"
ls -la | grep -v "^d" | wc -l
echo "Essential files kept:"
ls -1 *.py 2>/dev/null || echo "No Python files in root"
ls -1 *.md 2>/dev/null || echo "No markdown files in root"
ls -1 *.sh 2>/dev/null || echo "No shell scripts in root"

echo "📁 Directory structure after cleanup:"
echo "Root files:"
ls -1 *.py *.md *.sh *.txt *.service requirements.txt 2>/dev/null || echo "None"
echo ""
echo "Subdirectories:"
ls -d */ 2>/dev/null || echo "None"

echo "✅ Final cleanup completed!"
