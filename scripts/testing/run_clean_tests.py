#!/usr/bin/env python3
"""
Clean and organized test runner for RAG Document Classification System
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and capture output"""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()[:200]}...")
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()[:200]}...")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

# Configuration
PROJECT_ROOT = Path("/home/azureuser/rag_project")
PYTHON_PATH = PROJECT_ROOT
PYTEST_CONFIG = PROJECT_ROOT / "pytest.ini"

def main():
    parser = argparse.ArgumentParser(description="Clean Test Runner for RAG System")
    parser.add_argument("--category", choices=["working", "unit", "integration", "system", "all"], 
                       default="working", help="Test category to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run with coverage")
    
    args = parser.parse_args()
    
    print("🧪 RAG Document Classification System - Clean Test Runner")
    print("=" * 60)
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"🐍 Python path: {PYTHON_PATH}")
    print(f"📋 Test category: {args.category}")
    
    # Set environment
    os.environ["PYTHONPATH"] = str(PYTHON_PATH)
    
    # Build pytest command
    pytest_args = ["-x", "--tb=short", "--disable-warnings"]
    if args.verbose:
        pytest_args.append("-v")
    if args.coverage:
        pytest_args.extend(["--cov=core", "--cov-report=term-missing"])
    
    # Determine test directories
    test_dirs = {
        "working": "tests/working_tests/",
        "unit": "tests/unit_tests/", 
        "integration": "tests/integration_tests/",
        "system": "tests/system_tests/",
        "all": "tests/"
    }
    
    target_dir = test_dirs[args.category]
    
    if not (PROJECT_ROOT / target_dir).exists():
        print(f"❌ Test directory not found: {target_dir}")
        return 1
    
    # Run tests
    pytest_cmd = f"python -m pytest {target_dir} {' '.join(pytest_args)}"
    
    print(f"\n🚀 Running tests from: {target_dir}")
    print(f"Command: {pytest_cmd}")
    print("-" * 60)
    
    success = run_command(pytest_cmd, f"Running {args.category} tests")
    
    if success:
        print(f"\n🎉 {args.category.title()} tests completed successfully!")
    else:
        print(f"\n❌ {args.category.title()} tests failed!")
        
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
