#!/usr/bin/env python3
"""
Final System Test and Validation
Comprehensive testing of the complete SharePoint metadata placement system.
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        
    def test_system_status(self) -> bool:
        """Test basic system status and capabilities."""
        logger.info("🧪 Testing System Status...")
        
        try:
            # Test root endpoint
            response = requests.get(f"{self.base_url}/")
            assert response.status_code == 200
            status_data = response.json()
            
            logger.info(f"✅ System Status: {status_data['status']}")
            logger.info("Enhanced Features Status:")
            for feature, available in status_data['enhanced_features'].items():
                status = "✅" if available else "⚠️"
                logger.info(f"  {status} {feature}: {available}")
            
            # Test system capabilities
            response = requests.get(f"{self.base_url}/system-capabilities")
            assert response.status_code == 200
            capabilities = response.json()
            
            logger.info(f"✅ System Completion: {capabilities['completion_status']}")
            logger.info(f"✅ PDF Compliance: {capabilities['pdf_requirements_compliance']}")
            
            self.test_results['system_status'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ System status test failed: {e}")
            self.test_results['system_status'] = False
            return False
    
    def test_basic_classification(self) -> bool:
        """Test basic document classification functionality."""
        logger.info("🧪 Testing Basic Classification...")
        
        try:
            test_payload = {
                "text": "This is a contract agreement between Company A and Company B for software development services. The contract includes payment terms, project deliverables, and confidentiality clauses.",
                "sharepoint_file_url": "https://test.sharepoint.com/test-contract.pdf"
            }
            
            response = requests.post(f"{self.base_url}/classify", json=test_payload)
            assert response.status_code == 200
            result = response.json()
            
            logger.info(f"✅ Classification Result:")
            logger.info(f"  Document Type: {result.get('document_type', 'Not classified')}")
            logger.info(f"  Category: {result.get('document_category', 'Not classified')}")
            logger.info(f"  Confidence: {result.get('confidence', 'N/A')}")
            
            self.test_results['basic_classification'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Basic classification test failed: {e}")
            self.test_results['basic_classification'] = False
            return False
    
    def test_enhanced_classification(self) -> bool:
        """Test enhanced classification with RAG and confidence scoring."""
        logger.info("🧪 Testing Enhanced Classification...")
        
        try:
            test_payload = {
                "text": "MEMORANDUM OF UNDERSTANDING between ABC Corporation and XYZ Ltd regarding the establishment of a joint venture for developing renewable energy solutions. This agreement outlines the roles, responsibilities, and profit-sharing arrangements.",
                "sharepoint_file_url": "https://test.sharepoint.com/test-mou.pdf",
                "use_enhanced_rag": True,
                "include_confidence_analysis": True
            }
            
            response = requests.post(f"{self.base_url}/classify-enhanced", json=test_payload)
            assert response.status_code == 200
            result = response.json()
            
            logger.info(f"✅ Enhanced Classification Result:")
            logger.info(f"  Document Type: {result.get('document_type', 'Not classified')}")
            logger.info(f"  Category: {result.get('document_category', 'Not classified')}")
            logger.info(f"  Confidence Level: {result.get('confidence_level', 'N/A')}")
            logger.info(f"  Confidence Score: {result.get('confidence_score', 'N/A')}")
            logger.info(f"  Review Required: {result.get('requires_review', 'N/A')}")
            
            if 'reasoning' in result:
                logger.info(f"  Reasoning: {result['reasoning'][:100]}...")
            
            self.test_results['enhanced_classification'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Enhanced classification test failed: {e}")
            self.test_results['enhanced_classification'] = False
            return False
    
    def test_advanced_classification(self) -> bool:
        """Test advanced classification with all features."""
        logger.info("🧪 Testing Advanced Classification...")
        
        try:
            test_payload = {
                "text": "CONFIDENTIAL - Board of Directors Meeting Minutes for Q4 2024. Discussion topics include budget approval, strategic partnerships, executive compensation, and merger considerations. Attendees: CEO, CFO, COO, and external board members.",
                "sharepoint_file_url": "https://test.sharepoint.com/board-minutes.pdf",
                "use_enhanced_rag": True,
                "use_few_shot_learning": True,
                "include_confidence_analysis": True,
                "enable_teams_notifications": False  # Disable since webhook not configured
            }
            
            response = requests.post(f"{self.base_url}/classify-advanced", json=test_payload)
            assert response.status_code == 200
            result = response.json()
            
            logger.info(f"✅ Advanced Classification Result:")
            logger.info(f"  Document Type: {result.get('document_type', 'Not classified')}")
            logger.info(f"  Category: {result.get('document_category', 'Not classified')}")
            logger.info(f"  Confidence Analysis: {result.get('confidence_analysis', {})}")
            logger.info(f"  Alternative Suggestions: {result.get('alternative_suggestions', [])}")
            logger.info(f"  Processing Features Used: {result.get('features_used', [])}")
            
            self.test_results['advanced_classification'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Advanced classification test failed: {e}")
            self.test_results['advanced_classification'] = False
            return False
    
    def test_system_performance(self) -> bool:
        """Test system performance and response times."""
        logger.info("🧪 Testing System Performance...")
        
        try:
            # Test multiple quick classifications
            test_texts = [
                "Software license agreement for enterprise applications",
                "Employee handbook and HR policies document", 
                "Financial audit report for fiscal year 2024",
                "Project management plan for construction project",
                "Marketing campaign strategy and budget proposal"
            ]
            
            start_time = time.time()
            successful_requests = 0
            
            for i, text in enumerate(test_texts):
                try:
                    payload = {
                        "text": text,
                        "sharepoint_file_url": f"https://test.sharepoint.com/test-doc-{i+1}.pdf"
                    }
                    
                    response = requests.post(f"{self.base_url}/classify", json=payload, timeout=30)
                    if response.status_code == 200:
                        successful_requests += 1
                        
                except Exception as e:
                    logger.warning(f"Request {i+1} failed: {e}")
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / len(test_texts)
            
            logger.info(f"✅ Performance Test Results:")
            logger.info(f"  Total Requests: {len(test_texts)}")
            logger.info(f"  Successful: {successful_requests}")
            logger.info(f"  Success Rate: {(successful_requests/len(test_texts)*100):.1f}%")
            logger.info(f"  Total Time: {total_time:.2f}s")
            logger.info(f"  Average Time per Request: {avg_time:.2f}s")
            
            # Performance criteria: >80% success rate, <10s average response time
            performance_good = successful_requests/len(test_texts) >= 0.8 and avg_time < 10.0
            
            if performance_good:
                logger.info("✅ Performance test PASSED")
                self.test_results['performance'] = True
                return True
            else:
                logger.warning("⚠️ Performance test shows degraded performance but system functional")
                self.test_results['performance'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            self.test_results['performance'] = False
            return False
    
    def test_error_handling(self) -> bool:
        """Test system error handling and edge cases."""
        logger.info("🧪 Testing Error Handling...")
        
        try:
            # Test empty text
            response = requests.post(f"{self.base_url}/classify", json={"text": "", "sharepoint_file_url": "test.pdf"})
            logger.info(f"Empty text response: {response.status_code}")
            
            # Test invalid JSON
            response = requests.post(f"{self.base_url}/classify", json={"invalid": "payload"})
            logger.info(f"Invalid payload response: {response.status_code}")
            
            # Test very long text
            long_text = "This is a test document. " * 1000  # ~25KB
            response = requests.post(f"{self.base_url}/classify", json={"text": long_text, "sharepoint_file_url": "test.pdf"})
            logger.info(f"Long text response: {response.status_code}")
            
            logger.info("✅ Error handling test completed")
            self.test_results['error_handling'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.test_results['error_handling'] = False
            return False
    
    def generate_final_report(self) -> Dict:
        """Generate final test report and system validation."""
        logger.info("📊 Generating Final Test Report...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Get final system status
        try:
            response = requests.get(f"{self.base_url}/system-capabilities")
            system_info = response.json() if response.status_code == 200 else {}
        except:
            system_info = {}
        
        report = {
            "test_execution_time": datetime.now().isoformat(),
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": f"{success_rate:.1f}%"
            },
            "detailed_results": self.test_results,
            "system_status": system_info.get("completion_status", "Unknown"),
            "pdf_compliance": system_info.get("pdf_requirements_compliance", "Unknown"),
            "ready_for_production": passed_tests >= 4,  # At least 4/5 core tests must pass
            "recommendations": []
        }
        
        # Add recommendations based on test results
        if not self.test_results.get('performance', True):
            report["recommendations"].append("Consider optimizing model inference for better performance")
        
        if success_rate == 100:
            report["recommendations"].append("System is fully operational and ready for production deployment")
            report["status"] = "✅ ALL TESTS PASSED - SYSTEM READY"
        elif success_rate >= 80:
            report["recommendations"].append("System is mostly functional with minor issues")
            report["status"] = "⚠️ MOSTLY FUNCTIONAL - PRODUCTION READY WITH MONITORING"
        else:
            report["recommendations"].append("System needs attention before production deployment")
            report["status"] = "❌ NEEDS ATTENTION"
        
        return report
    
    def run_all_tests(self) -> Dict:
        """Run all system tests and return comprehensive report."""
        logger.info("🚀 Starting Comprehensive System Test Suite...")
        logger.info("=" * 60)
        
        # Run all tests
        self.test_system_status()
        self.test_basic_classification()
        self.test_enhanced_classification()
        self.test_advanced_classification()
        self.test_system_performance()
        self.test_error_handling()
        
        # Generate final report
        report = self.generate_final_report()
        
        logger.info("=" * 60)
        logger.info("📋 FINAL TEST REPORT")
        logger.info("=" * 60)
        logger.info(f"Status: {report['status']}")
        logger.info(f"Success Rate: {report['test_summary']['success_rate']}")
        logger.info(f"Tests Passed: {report['test_summary']['passed_tests']}/{report['test_summary']['total_tests']}")
        logger.info(f"Production Ready: {report['ready_for_production']}")
        logger.info(f"System Completion: {report['system_status']}")
        logger.info(f"PDF Compliance: {report['pdf_compliance']}")
        
        if report['recommendations']:
            logger.info("\n📝 Recommendations:")
            for rec in report['recommendations']:
                logger.info(f"  • {rec}")
        
        return report

def main():
    """Run the comprehensive system test."""
    tester = SystemTester()
    report = tester.run_all_tests()
    
    # Save report to file
    with open('/home/azureuser/rag_project/final_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\n📄 Full report saved to: final_test_report.json")
    logger.info("🎯 Testing Complete!")
    
    return report

if __name__ == "__main__":
    main()
