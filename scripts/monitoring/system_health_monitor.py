#!/usr/bin/env python3
"""
System Health Monitor for RAG Classification System
Monitors GPU memory, service status, and classification pipeline health
"""

import subprocess
import requests
import time
import logging
from datetime import datetime
import psutil
import json

class SystemHealthMonitor:
    def __init__(self):
        self.services = [
            'rag-fastapi.service',
            'rag-mistral.service', 
            'rag-sharepoint.service'
        ]
        self.api_endpoints = {
            'fastapi': 'http://localhost:8000/health',
            'mistral': 'http://localhost:8001/health'
        }
        self.gpu_memory_threshold = 90  # Alert if GPU memory usage > 90%
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            filename='/home/azureuser/rag_project/logs/application/system_health.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def check_gpu_memory(self):
        """Check GPU memory usage"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                memory_info = result.stdout.strip().split(', ')
                used_mb = int(memory_info[0])
                total_mb = int(memory_info[1])
                usage_percent = (used_mb / total_mb) * 100
                
                status = {
                    'used_mb': used_mb,
                    'total_mb': total_mb,
                    'usage_percent': round(usage_percent, 2),
                    'status': 'CRITICAL' if usage_percent > self.gpu_memory_threshold else 'OK'
                }
                
                if usage_percent > self.gpu_memory_threshold:
                    self.logger.warning(f"GPU memory usage critical: {usage_percent:.2f}% ({used_mb}/{total_mb} MB)")
                
                return status
        except Exception as e:
            self.logger.error(f"Error checking GPU memory: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def check_service_status(self, service_name):
        """Check systemd service status"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'is-active', service_name], 
                                  capture_output=True, text=True)
            is_active = result.stdout.strip() == 'active'
            
            # Get more detailed status
            result = subprocess.run(['sudo', 'systemctl', 'status', service_name, '--no-pager'], 
                                  capture_output=True, text=True)
            
            return {
                'service': service_name,
                'active': is_active,
                'status': 'OK' if is_active else 'ERROR'
            }
        except Exception as e:
            self.logger.error(f"Error checking service {service_name}: {e}")
            return {'service': service_name, 'status': 'ERROR', 'error': str(e)}
    
    def check_api_endpoints(self):
        """Check API endpoint health"""
        results = {}
        for name, url in self.api_endpoints.items():
            try:
                response = requests.get(url, timeout=5)
                results[name] = {
                    'status': 'OK' if response.status_code == 200 else 'ERROR',
                    'status_code': response.status_code,
                    'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2)
                }
            except requests.RequestException as e:
                results[name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                self.logger.error(f"API endpoint {name} ({url}) failed: {e}")
        
        return results
    
    def check_classification_pipeline(self):
        """Test the classification pipeline end-to-end"""
        try:
            test_data = {
                "text": "I-130 Petition for Alien Relative - Family-based immigration petition",
                "filename": "test_health_check.pdf"
            }
            
            response = requests.post('http://localhost:8000/classify_document', 
                                   json=test_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'status': 'OK',
                    'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2),
                    'classification': {
                        'doc_type': result.get('doc_type', 'Unknown'),
                        'doc_category': result.get('doc_category', 'Unknown'),
                        'confidence': result.get('confidence', 'Unknown')
                    }
                }
            else:
                return {
                    'status': 'ERROR',
                    'status_code': response.status_code,
                    'error': response.text
                }
        except Exception as e:
            self.logger.error(f"Classification pipeline test failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def check_recent_classifications(self):
        """Check if recent classifications have been processed"""
        try:
            with open('/home/azureuser/rag_project/classification_log.csv', 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    last_line = lines[-1].strip()
                    timestamp_str = last_line.split(',')[0]
                    last_classification = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    time_since_last = datetime.now() - last_classification.replace(tzinfo=None)
                    
                    return {
                        'last_classification': timestamp_str,
                        'minutes_since_last': round(time_since_last.total_seconds() / 60, 2),
                        'status': 'OK' if time_since_last.total_seconds() < 3600 else 'WARNING'  # Warning if > 1 hour
                    }
        except Exception as e:
            self.logger.error(f"Error checking recent classifications: {e}")
            return {'status': 'ERROR', 'error': str(e)}
        
        return {'status': 'ERROR', 'error': 'No classification log found'}
    
    def generate_health_report(self):
        """Generate comprehensive health report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'gpu_memory': self.check_gpu_memory(),
            'services': {},
            'api_endpoints': self.check_api_endpoints(),
            'classification_pipeline': self.check_classification_pipeline(),
            'recent_classifications': self.check_recent_classifications()
        }
        
        # Check all services
        for service in self.services:
            report['services'][service] = self.check_service_status(service)
        
        # Determine overall system health
        all_statuses = []
        all_statuses.append(report['gpu_memory']['status'])
        all_statuses.extend([s['status'] for s in report['services'].values()])
        all_statuses.extend([e['status'] for e in report['api_endpoints'].values()])
        all_statuses.append(report['classification_pipeline']['status'])
        all_statuses.append(report['recent_classifications']['status'])
        
        if 'ERROR' in all_statuses:
            report['overall_status'] = 'ERROR'
        elif 'CRITICAL' in all_statuses or 'WARNING' in all_statuses:
            report['overall_status'] = 'WARNING'
        else:
            report['overall_status'] = 'HEALTHY'
        
        return report
    
    def print_status_summary(self, report):
        """Print a human-readable status summary"""
        print(f"\n🔍 RAG System Health Check - {report['timestamp']}")
        print(f"Overall Status: {report['overall_status']}")
        print("=" * 50)
        
        # GPU Memory
        gpu = report['gpu_memory']
        if 'usage_percent' in gpu:
            print(f"🖥️  GPU Memory: {gpu['usage_percent']}% ({gpu['used_mb']}/{gpu['total_mb']} MB) - {gpu['status']}")
        else:
            print(f"🖥️  GPU Memory: {gpu['status']}")
        
        # Services
        print("\n📋 Services:")
        for service, status in report['services'].items():
            status_emoji = "✅" if status['status'] == 'OK' else "❌"
            print(f"   {status_emoji} {service}: {status['status']}")
        
        # API Endpoints
        print("\n🌐 API Endpoints:")
        for endpoint, status in report['api_endpoints'].items():
            status_emoji = "✅" if status['status'] == 'OK' else "❌"
            if 'response_time_ms' in status:
                print(f"   {status_emoji} {endpoint}: {status['status']} ({status['response_time_ms']}ms)")
            else:
                print(f"   {status_emoji} {endpoint}: {status['status']}")
        
        # Classification Pipeline
        pipeline = report['classification_pipeline']
        status_emoji = "✅" if pipeline['status'] == 'OK' else "❌"
        print(f"\n🔄 Classification Pipeline: {status_emoji} {pipeline['status']}")
        if 'response_time_ms' in pipeline:
            print(f"   Response time: {pipeline['response_time_ms']}ms")
        
        # Recent Classifications
        recent = report['recent_classifications']
        status_emoji = "✅" if recent['status'] == 'OK' else "⚠️" if recent['status'] == 'WARNING' else "❌"
        print(f"\n📊 Recent Classifications: {status_emoji} {recent['status']}")
        if 'minutes_since_last' in recent:
            print(f"   Last classification: {recent['minutes_since_last']} minutes ago")
    
    def run_health_check(self, print_summary=True):
        """Run complete health check"""
        report = self.generate_health_report()
        
        if print_summary:
            self.print_status_summary(report)
        
        # Log the report
        self.logger.info(f"Health check completed - Status: {report['overall_status']}")
        
        return report

def main():
    """Main function for command-line usage"""
    monitor = SystemHealthMonitor()
    report = monitor.run_health_check()
    
    # Save detailed report
    report_file = f"/home/azureuser/rag_project/logs/application/health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    main()
