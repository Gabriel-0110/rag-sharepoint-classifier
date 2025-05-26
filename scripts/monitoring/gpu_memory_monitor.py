#!/usr/bin/env python3
"""
GPU Memory Monitor for RAG System
Monitors GPU memory usage and automatically restarts services if memory conflicts occur.
"""

import subprocess
import json
import time
import logging
from datetime import datetime
import requests
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/azureuser/rag_project/logs/application/gpu_monitor.log'),
        logging.StreamHandler()
    ]
)

class GPUMemoryMonitor:
    def __init__(self):
        self.max_gpu_memory_mb = 4096  # Total GPU memory
        self.critical_threshold = 0.95  # 95% usage threshold
        self.warning_threshold = 0.85   # 85% usage threshold
        
    def get_gpu_memory_usage(self):
        """Get current GPU memory usage."""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    used, total = map(int, line.split(', '))
                    return used, total
            return None, None
        except Exception as e:
            logging.error(f"Error getting GPU memory usage: {e}")
            return None, None
    
    def get_gpu_processes(self):
        """Get list of processes using GPU memory."""
        try:
            result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                processes = []
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 3:
                            pid, name, memory = parts[0], parts[1], int(parts[2])
                            processes.append({'pid': pid, 'name': name, 'memory_mb': memory})
                return processes
            return []
        except Exception as e:
            logging.error(f"Error getting GPU processes: {e}")
            return []
    
    def check_service_health(self):
        """Check if all RAG services are running properly."""
        services = ['rag-fastapi.service', 'rag-mistral.service', 'rag-sharepoint.service']
        service_status = {}
        
        for service in services:
            try:
                result = subprocess.run(['systemctl', 'is-active', service], 
                                      capture_output=True, text=True)
                service_status[service] = result.stdout.strip() == 'active'
            except Exception as e:
                logging.error(f"Error checking {service}: {e}")
                service_status[service] = False
        
        return service_status
    
    def test_classification_endpoint(self):
        """Test if the classification endpoint is responding."""
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            return response.status_code == 200
        except Exception as e:
            logging.warning(f"Classification endpoint not responding: {e}")
            return False
    
    def restart_sharepoint_service(self):
        """Restart the SharePoint automation service."""
        try:
            logging.info("Restarting SharePoint automation service due to memory issues...")
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'rag-sharepoint.service'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logging.info("SharePoint service restarted successfully")
                return True
            else:
                logging.error(f"Failed to restart SharePoint service: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Error restarting SharePoint service: {e}")
            return False
    
    def generate_health_report(self):
        """Generate a comprehensive health report."""
        used_memory, total_memory = self.get_gpu_memory_usage()
        gpu_processes = self.get_gpu_processes()
        service_status = self.check_service_health()
        classification_healthy = self.test_classification_endpoint()
        
        memory_usage_percent = (used_memory / total_memory * 100) if used_memory and total_memory else 0
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'gpu_memory': {
                'used_mb': used_memory,
                'total_mb': total_memory,
                'usage_percent': memory_usage_percent,
                'status': 'critical' if memory_usage_percent > self.critical_threshold * 100 
                         else 'warning' if memory_usage_percent > self.warning_threshold * 100 
                         else 'normal'
            },
            'gpu_processes': gpu_processes,
            'services': service_status,
            'classification_endpoint': classification_healthy
        }
        
        return report
    
    def monitor_loop(self, interval_seconds=60):
        """Main monitoring loop."""
        logging.info("Starting GPU memory monitoring...")
        
        while True:
            try:
                report = self.generate_health_report()
                
                # Log current status
                memory_status = report['gpu_memory']['status']
                usage_percent = report['gpu_memory']['usage_percent']
                
                if memory_status == 'critical':
                    logging.warning(f"CRITICAL: GPU memory usage at {usage_percent:.1f}%")
                    
                    # Check if SharePoint service is having issues
                    if not report['services'].get('rag-sharepoint.service', False):
                        logging.error("SharePoint service is down, attempting restart...")
                        self.restart_sharepoint_service()
                    
                elif memory_status == 'warning':
                    logging.info(f"WARNING: GPU memory usage at {usage_percent:.1f}%")
                else:
                    logging.info(f"GPU memory usage normal: {usage_percent:.1f}%")
                
                # Save detailed report
                report_file = f"/home/azureuser/rag_project/logs/application/health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
                
                # Clean up old report files (keep only last 24 hours)
                self.cleanup_old_reports()
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
            
            time.sleep(interval_seconds)
    
    def cleanup_old_reports(self):
        """Remove health reports older than 24 hours."""
        try:
            reports_dir = "/home/azureuser/rag_project/logs/application"
            current_time = time.time()
            
            for filename in os.listdir(reports_dir):
                if filename.startswith('health_report_') and filename.endswith('.json'):
                    file_path = os.path.join(reports_dir, filename)
                    file_age = current_time - os.path.getctime(file_path)
                    
                    # Remove files older than 24 hours (86400 seconds)
                    if file_age > 86400:
                        os.remove(file_path)
                        logging.debug(f"Removed old health report: {filename}")
        except Exception as e:
            logging.error(f"Error cleaning up old reports: {e}")

def main():
    monitor = GPUMemoryMonitor()
    
    # Generate initial report
    initial_report = monitor.generate_health_report()
    print("🔍 Initial System Health Report:")
    print(f"   GPU Memory: {initial_report['gpu_memory']['used_mb']}MB / {initial_report['gpu_memory']['total_mb']}MB ({initial_report['gpu_memory']['usage_percent']:.1f}%)")
    print(f"   Status: {initial_report['gpu_memory']['status'].upper()}")
    print(f"   Services: {sum(initial_report['services'].values())}/{len(initial_report['services'])} running")
    print(f"   Classification Endpoint: {'✅' if initial_report['classification_endpoint'] else '❌'}")
    
    # Start monitoring
    monitor.monitor_loop(interval_seconds=120)  # Check every 2 minutes

if __name__ == "__main__":
    main()
