#!/usr/bin/env python3
"""
SharePoint Automation Monitoring Dashboard
Real-time monitoring of document classification status
"""

import os
import pandas as pd
from datetime import datetime, timedelta
import json

def load_classification_log():
    """Load and analyze classification log"""
    log_file = "classification_log.csv"
    if not os.path.exists(log_file):
        print("❌ No classification log found")
        return None
    
    try:
        df = pd.read_csv(log_file)
        if df.empty:
            print("❌ Classification log is empty")
            return None
        return df
    except Exception as e:
        print(f"❌ Error reading classification log: {e}")
        return None

def analyze_performance():
    """Analyze automation performance"""
    df = load_classification_log()
    if df is None:
        return
    
    try:
        # Convert timestamp to datetime
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        
        # Remove rows with invalid timestamps
        df = df.dropna(subset=['Timestamp'])
        
        if df.empty:
            print("📊 No valid data found in classification log")
            return
    except Exception as e:
        print(f"❌ Error processing timestamps: {e}")
        return
    
    # Recent activity (last 24 hours)
    recent = df[df['Timestamp'] > datetime.now() - timedelta(hours=24)]
    
    print("📊 SharePoint Automation Dashboard")
    print("=" * 50)
    print(f"📄 Total documents processed: {len(df)}")
    print(f"🕒 Last 24 hours: {len(recent)} documents")
    print(f"📅 Date range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
    
    # Document type distribution
    print("\n📋 Document Types:")
    type_counts = df['DocumentType'].value_counts()
    for doc_type, count in type_counts.head(10).items():
        print(f"  • {doc_type}: {count}")
    
    # Category distribution
    print("\n🏷️  Categories:")
    cat_counts = df['DocumentCategory'].value_counts()
    for category, count in cat_counts.head(10).items():
        print(f"  • {category}: {count}")
    
    # Recent activity
    if len(recent) > 0:
        print(f"\n🕒 Recent Activity (Last 24h):")
        for _, row in recent.tail(5).iterrows():
            timestamp = row['Timestamp'].strftime('%Y-%m-%d %H:%M')
            print(f"  • {timestamp}: {row['FileName']} → {row['DocumentType']}")

def check_service_status():
    """Check if automation services are running"""
    print("\n🔧 Service Status:")
    
    # Check if automation script is running
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'sharepoint_automation.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ SharePoint automation: RUNNING")
        else:
            print("  ❌ SharePoint automation: STOPPED")
    except:
        print("  ❓ Cannot check automation status")
    
    # Check Mistral API server
    try:
        result = subprocess.run(['pgrep', '-f', 'mistral_api_server'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ Mistral API server: RUNNING")
        else:
            print("  ❌ Mistral API server: STOPPED")
    except:
        print("  ❓ Cannot check Mistral status")
    
    # Check Qdrant
    try:
        import requests
        response = requests.get("http://localhost:6333/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ Qdrant vector DB: RUNNING")
        else:
            print("  ❌ Qdrant vector DB: ERROR")
    except:
        print("  ❌ Qdrant vector DB: NOT ACCESSIBLE")

def check_errors():
    """Check for recent errors in logs"""
    print("\n🚨 Recent Errors:")
    
    # Check system logs for errors
    import subprocess
    try:
        result = subprocess.run(['journalctl', '-u', 'sharepoint-automation', '--since', '1 hour ago', '--no-pager'], 
                              capture_output=True, text=True)
        
        error_lines = [line for line in result.stdout.split('\n') 
                      if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception'])]
        
        if error_lines:
            print("  Recent service errors found:")
            for line in error_lines[-5:]:  # Last 5 errors
                print(f"    {line}")
        else:
            print("  ✅ No recent errors in service logs")
            
    except Exception as e:
        print(f"  ❓ Cannot check service logs: {e}")

def main():
    """Main dashboard function"""
    print(f"🕒 Dashboard updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    analyze_performance()
    check_service_status()
    check_errors()
    
    print("\n" + "=" * 50)
    print("💡 Commands:")
    print("  • python monitor_automation.py - Refresh dashboard")
    print("  • sudo systemctl status sharepoint-automation - Check service")
    print("  • sudo systemctl restart sharepoint-automation - Restart service")
    print("  • tail -f classification_log.csv - Watch live activity")

if __name__ == "__main__":
    main()
