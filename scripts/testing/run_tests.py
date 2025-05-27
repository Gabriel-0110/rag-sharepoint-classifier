#!/usr/bin/env python3
"""
Comprehensive test runner for RAG Document Classification System

This script runs all tests with proper reporting and handles different test categories.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"⏱️  Execution time: {end_time - start_time:.2f} seconds")
    print(f"📤 Return code: {result.returncode}")
    
    if result.stdout:
        print("\n📋 STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("\n⚠️  STDERR:")
        print(result.stderr)
    
    return result

def check_dependencies():
    """Check if all required dependencies are available"""
    print("\n🔍 Checking test dependencies...")
    
    required_packages = [
        'pytest',
        'requests', 
        'fastapi',
        'transformers',
        'torch',
        'qdrant-client',
        'sentence-transformers',
        'Pillow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install missing packages with: pip install <package_name>")
        return False
    
    print("\n✅ All dependencies are available")
    return True

def run_unit_tests():
    """Run unit tests"""
    cmd = [
        'python', '-m', 'pytest', 
        'tests/unit/',
        '-v',
        '--tb=short',
        '-m', 'not slow'
    ]
    
    return run_command(cmd, "Running Unit Tests")

def run_integration_tests():
    """Run integration tests"""
    cmd = [
        'python', '-m', 'pytest',
        'tests/integration/',
        '-v', 
        '--tb=short'
    ]
    
    return run_command(cmd, "Running Integration Tests")

def run_system_tests():
    """Run system tests"""
    cmd = [
        'python', '-m', 'pytest',
        'tests/system/',
        '-v',
        '--tb=short',
        '-s'  # Don't capture output for system tests
    ]
    
    return run_command(cmd, "Running System Tests")

def run_specific_test_category(category):
    """Run tests for a specific category"""
    category_mapping = {
        'api': 'tests/unit/test_fastapi_endpoints.py',
        'rag': 'tests/unit/test_enhanced_rag_classifier.py', 
        'confidence': 'tests/unit/test_confidence_scoring.py',
        'ocr': 'tests/unit/test_trocr_integration.py',
        'sharepoint': 'tests/unit/test_sharepoint_integration.py',
        'workflow': 'tests/integration/test_complete_workflow.py'
    }
    
    if category not in category_mapping:
        print(f"❌ Unknown test category: {category}")
        print(f"Available categories: {', '.join(category_mapping.keys())}")
        return None
    
    test_file = category_mapping[category]
    
    cmd = [
        'python', '-m', 'pytest',
        test_file,
        '-v',
        '--tb=short'
    ]
    
    return run_command(cmd, f"Running {category.upper()} Tests")

def run_all_tests():
    """Run all test suites"""
    results = []
    
    print("\n🧪 Starting Comprehensive Test Suite")
    print("=" * 60)
    
    # Run unit tests
    result = run_unit_tests()
    results.append(("Unit Tests", result.returncode))
    
    # Run integration tests
    result = run_integration_tests()
    results.append(("Integration Tests", result.returncode))
    
    # Run system tests (only if previous tests passed)
    if all(code == 0 for _, code in results):
        result = run_system_tests()
        results.append(("System Tests", result.returncode))
    else:
        print("\n⚠️  Skipping system tests due to previous failures")
        results.append(("System Tests", -1))
    
    return results

def generate_test_report(results):
    """Generate a summary test report"""
    print("\n" + "="*60)
    print("📊 TEST EXECUTION SUMMARY")
    print("="*60)
    
    total_suites = len(results)
    passed_suites = sum(1 for _, code in results if code == 0)
    failed_suites = total_suites - passed_suites
    
    for suite_name, return_code in results:
        status = "✅ PASSED" if return_code == 0 else "❌ FAILED"
        print(f"{suite_name:20} {status}")
    
    print("-" * 60)
    print(f"Total Test Suites: {total_suites}")
    print(f"Passed: {passed_suites}")
    print(f"Failed: {failed_suites}")
    print(f"Success Rate: {(passed_suites/total_suites)*100:.1f}%")
    
    if failed_suites == 0:
        print("\n🎉 All test suites PASSED!")
        return True
    else:
        print(f"\n💥 {failed_suites} test suite(s) FAILED!")
        return False

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="RAG Document Classification Test Runner")
    parser.add_argument(
        '--category', 
        choices=['unit', 'integration', 'system', 'all', 'api', 'rag', 'confidence', 'ocr', 'sharepoint', 'workflow'],
        default='all',
        help='Test category to run'
    )
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Only check dependencies'
    )
    parser.add_argument(
        '--fast',
        action='store_true', 
        help='Run only fast tests'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    print("🧪 RAG Document Classification System - Test Runner")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        if args.check_deps:
            return
        print("\n❌ Cannot proceed without required dependencies")
        sys.exit(1)
    
    if args.check_deps:
        print("\n✅ Dependency check completed successfully")
        return
    
    # Set environment variables for testing
    os.environ['TESTING'] = '1'
    os.environ['LOG_LEVEL'] = 'INFO'
    
    # Run tests based on category
    if args.category == 'all':
        results = run_all_tests()
        success = generate_test_report(results)
        sys.exit(0 if success else 1)
    
    elif args.category == 'unit':
        result = run_unit_tests()
        sys.exit(result.returncode)
    
    elif args.category == 'integration':
        result = run_integration_tests()
        sys.exit(result.returncode)
    
    elif args.category == 'system':
        result = run_system_tests()
        sys.exit(result.returncode)
    
    else:
        # Specific test category
        result = run_specific_test_category(args.category)
        if result:
            sys.exit(result.returncode)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()
