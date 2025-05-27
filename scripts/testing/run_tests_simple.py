#!/usr/bin/env python3
"""
Simple test runner for RAG Document Classification System
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Set up environment
    project_root = Path(__file__).parent.absolute()
    env = os.environ.copy()
    
    # Set PYTHONPATH to include project root
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{project_root}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = str(project_root)
    
    print(f"🧪 RAG Document Classification System - Test Runner")
    print(f"📁 Project root: {project_root}")
    print(f"🐍 PYTHONPATH: {env['PYTHONPATH']}")
    print("="*60)
    
    # Get command line arguments
    if len(sys.argv) > 1:
        test_target = sys.argv[1]
    else:
        test_target = "tests/unit/test_enhanced_rag_classifier.py"
    
    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        test_target,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]
    
    print(f"🚀 Running: {' '.join(cmd)}")
    print("="*60)
    
    # Run the test
    try:
        result = subprocess.run(cmd, env=env, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
