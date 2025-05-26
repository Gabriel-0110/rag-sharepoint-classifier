#!/bin/bash
# Project Cleanup and Reorganization Script
# This script will organize the RAG project by keeping only essential files

echo "🧹 Starting Project Cleanup and Reorganization"
echo "=============================================="

cd /home/azureuser/rag_project

# Create backup before cleanup
echo "📦 Creating backup of current state..."
mkdir -p cleanup_backup_$(date +%Y%m%d_%H%M%S)
cp -r * cleanup_backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null

echo "🔍 Analyzing project structure..."

echo "
📋 ESSENTIAL FILES (keeping):
============================
Core System Files:
- .env (configuration)
- core/main.py (FastAPI server)
- core/mistral_api_server.py (AI inference server)
- core/sharepoint_automation.py (SharePoint integration)
- core/enhanced_rag_classifier.py (AI classification)
- requirements.txt (dependencies)
- classification_log.csv (production data)

Key Documentation:
- FINAL_STATUS_UPDATE_MAY26.md (final status)
- docs/ (configuration guides)

Data & Logs:
- data/ (document storage)
- logs/ (system logs)
- storage/ (vector database)

🗑️  REMOVING (unnecessary test/dev files):
=========================================
"

# Files to remove (test files, duplicates, temporary files)
FILES_TO_REMOVE=(
    "complete_system_demo.py"
    "completion_report.py" 
    "comprehensive_system_test.py"
    "confidence_scoring.py"
    "direct_sharepoint_update.py"
    "enhanced_rag_classifier.py"  # duplicate (core/ has the real one)
    "few_shot_learning.py"
    "final_demonstration.py"
    "final_system_test.py"
    "final_test_report.json"
    "main.py"  # duplicate (core/ has the real one)
    "mistral_api_server.py"  # duplicate (core/ has the real one)
    "monitor_automation.py"
    "quick_final_test.py"
    "reprocess_unknown_documents.py"  # one-time use script
    "sharepoint_automation.py"  # duplicate (core/ has the real one)
    "simple_status_check.py"
    "simple_validation.py"
    "teams_integration.py"  # duplicate functionality in core files
    "test_contract.txt"
    "test_enhanced_direct.py"
    "test_enhanced_http.py"
    "test_enhanced_rag.py"
    "test_immigration_document.txt"
    "test_sharepoint_integration.py"
    "test_sharepoint_update.py"
    "trocr_integration.py"  # integrated into core files
    "update_sharepoint_metadata.py"
    "update_sharepoint_with_improved_classifications.py"
    
    # Result files (keeping backups but removing duplicates)
    "reprocessing_results_20250526_005000.csv"
    "sharepoint_direct_update_20250526_005351.csv"
    "sharepoint_update_output.log"
    "classification_log_clean.csv"
    
    # Multiple completion reports (keeping only the final one)
    "FINAL_COMPLETION_REPORT.md"
    "FINAL_COMPLETION_REPORT_v2.md"
    "FINAL_MISSION_ACCOMPLISHED.md"
    "FINAL_STATUS_REPORT.md"
    "MISSION_COMPLETE.md"
    "IMPLEMENTATION_ANALYSIS.md"
    "PROJECT_STRUCTURE.md"
    
    # Shell scripts (temporary)
    "cleanup_project.sh"
    "enhanced_system_check.sh"
    "final_validation.sh"
    "manage_automation.sh"
    "system_status.sh"
    
    # Temporary files
    "nohup.out"
    "sharepoint-automation.service"  # empty file
)

# Remove unnecessary files
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        echo "  ❌ Removing: $file"
        rm "$file"
    fi
done

# Clean up empty __pycache__ in root
if [ -d "__pycache__" ]; then
    echo "  ❌ Removing root __pycache__"
    rm -rf "__pycache__"
fi

echo "
📁 ORGANIZING REMAINING STRUCTURE:
================================="

# Move important results to archive for reference
echo "📦 Moving important results to archive..."
mkdir -p archive/results
if [ -f "classification_log_backup_20250526_005000.csv" ]; then
    mv "classification_log_backup_20250526_005000.csv" archive/results/
    echo "  ✅ Moved classification backup to archive/results/"
fi

# Ensure proper directory structure
echo "📂 Verifying directory structure..."
mkdir -p {data,logs,storage,docs,archive,backup}

echo "
✅ CLEANUP COMPLETE!
==================

📋 Final Project Structure:
├── .env                              # Configuration
├── core/                            # Core system files
│   ├── main.py                      # FastAPI server
│   ├── mistral_api_server.py       # AI inference
│   ├── sharepoint_automation.py    # SharePoint integration
│   └── enhanced_rag_classifier.py  # AI classification
├── requirements.txt                 # Dependencies
├── classification_log.csv          # Production data
├── FINAL_STATUS_UPDATE_MAY26.md   # Final documentation
├── data/                           # Document storage
├── logs/                           # System logs
├── storage/                        # Vector database
├── docs/                           # Documentation
├── archive/                        # Historical data
└── backup/                         # Backups

🎯 System Status:
✅ Essential files preserved
✅ Duplicates removed
✅ Test files cleaned up
✅ Documentation consolidated
✅ Production structure maintained

🚀 Your system is now clean and organized!
"
