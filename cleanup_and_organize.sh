#!/bin/bash
# Enhanced Project Cleanup and Reorganization Script
# This script will organize the RAG project by removing duplicates and organizing files properly

echo "🧹 Enhanced Project Cleanup and Reorganization"
echo "=============================================="

cd /home/azureuser/rag_project

# Create backup before cleanup
echo "📦 Creating backup of current state..."
BACKUP_DIR="cleanup_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r .env core/ enhanced/ src/ scripts/ tests/ docs/ data/ logs/ storage/ archive/ requirements.txt *.md "$BACKUP_DIR"/ 2>/dev/null
echo "✅ Backup created in: $BACKUP_DIR"

echo ""
echo "🔍 Current project analysis..."
echo "Total files in root: $(find . -maxdepth 1 -type f | wc -l)"
echo ""

echo "🗑️  REMOVING DUPLICATE AND UNNECESSARY FILES:"
echo "=============================================="

# Remove duplicate core files (real ones are in core/)
if [ -f "main.py" ]; then
    echo "  ❌ Removing duplicate: main.py"
    rm "main.py"
fi

if [ -f "mistral_api_server.py" ]; then
    echo "  ❌ Removing duplicate: mistral_api_server.py"
    rm "mistral_api_server.py"
fi

if [ -f "sharepoint_automation.py" ]; then
    echo "  ❌ Removing duplicate: sharepoint_automation.py"
    rm "sharepoint_automation.py"
fi

if [ -f "enhanced_rag_classifier.py" ]; then
    echo "  ❌ Removing duplicate: enhanced_rag_classifier.py"
    rm "enhanced_rag_classifier.py"
fi

# Remove duplicate enhanced files
if [ -f "confidence_scoring.py" ]; then
    echo "  ❌ Removing: confidence_scoring.py"
    rm "confidence_scoring.py"
fi

if [ -f "few_shot_learning.py" ]; then
    echo "  ❌ Removing: few_shot_learning.py"
    rm "few_shot_learning.py"
fi

if [ -f "teams_integration.py" ]; then
    echo "  ❌ Removing: teams_integration.py"
    rm "teams_integration.py"
fi

if [ -f "trocr_integration.py" ]; then
    echo "  ❌ Removing: trocr_integration.py"
    rm "trocr_integration.py"
fi

# Remove test files
test_files=(
    "complete_system_demo.py"
    "completion_report.py"
    "comprehensive_system_test.py"
    "direct_classification_test.py"
    "direct_sharepoint_update.py"
    "final_demonstration.py"
    "final_system_test.py"
    "monitor_automation.py"
    "quick_final_test.py"
    "reprocess_unknown_documents.py"
    "simple_status_check.py"
    "simple_test.py"
    "simple_validation.py"
    "test_classification.py"
    "test_enhanced_direct.py"
    "test_enhanced_http.py"
    "test_enhanced_rag.py"
    "test_sharepoint_classification.py"
    "test_sharepoint_integration.py"
    "test_sharepoint_update.py"
    "update_sharepoint_metadata.py"
    "update_sharepoint_with_improved_classifications.py"
    "verify_sharepoint_update.py"
    "test_contract.txt"
    "test_immigration_document.txt"
)

for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ❌ Removing test/dev file: $file"
        rm "$file"
    fi
done

# Remove shell scripts (these are now in scripts/)
shell_scripts=(
    "cleanup_project.sh"
    "enhanced_system_check.sh"
    "final_validation.sh"
    "manage_automation.sh"
    "organize_project.sh"
    "system_status.sh"
)

for script in "${shell_scripts[@]}"; do
    if [ -f "$script" ]; then
        echo "  ❌ Removing shell script: $script"
        rm "$script"
    fi
done

# Remove duplicate documentation (keeping only essential)
duplicate_docs=(
    "FINAL_COMPLETION_REPORT.md"
    "FINAL_COMPLETION_REPORT_v2.md"
    "FINAL_MISSION_ACCOMPLISHED.md"
    "FINAL_STATUS_REPORT.md"
    "MISSION_COMPLETE.md"
    "IMPLEMENTATION_ANALYSIS.md"
    "PROJECT_STRUCTURE.md"
)

for doc in "${duplicate_docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ❌ Removing duplicate doc: $doc"
        rm "$doc"
    fi
done

# Remove other files
other_files=(
    "classification_log_clean.csv"
    "sharepoint-automation.service"
)

for file in "${other_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ❌ Removing: $file"
        rm "$file"
    fi
done

echo ""
echo "📁 ORGANIZING STRUCTURE:"
echo "========================"

# Move important files to appropriate locations
if [ -f "classification_log.csv" ] && [ ! -f "core/classification_log.csv" ]; then
    echo "  📊 Moving classification_log.csv to core/"
    mv "classification_log.csv" "core/"
fi

# Clean up __pycache__ directories
echo "  🧹 Cleaning up __pycache__ directories..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo ""
echo "📂 VERIFYING DIRECTORY STRUCTURE:"
echo "================================="

# Check required directories
required_dirs=("core" "enhanced" "src" "scripts" "tests" "docs" "data" "logs" "storage" "archive")

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/ - exists"
    else
        echo "  ⚠️  $dir/ - missing"
    fi
done

echo ""
echo "📋 FINAL FILE COUNT:"
echo "==================="
echo "Root directory files: $(find . -maxdepth 1 -type f | wc -l)"
echo "Core files: $(find core/ -name "*.py" 2>/dev/null | wc -l)"
echo "Enhanced files: $(find enhanced/ -name "*.py" 2>/dev/null | wc -l)"
echo "Script files: $(find scripts/ -name "*.py" -o -name "*.sh" 2>/dev/null | wc -l)"

echo ""
echo "✅ CLEANUP COMPLETE!"
echo "===================="
