#!/usr/bin/env python3
"""
Teams Notifications Integration
Implements Teams webhook notifications as mentioned in PDF requirements.
"""

import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class NotificationConfig:
    """Configuration for Teams notifications."""
    webhook_url: str = ""
    enabled: bool = False
    notify_on_success: bool = True
    notify_on_error: bool = True
    notify_on_low_confidence: bool = True
    batch_notifications: bool = False
    batch_size: int = 10

class TeamsNotifier:
    """Teams webhook notification system."""
    
    def __init__(self, config: NotificationConfig = None):
        self.config = config or NotificationConfig()
        self.pending_notifications = []
    
    def send_notification(self, title: str, message: str, color: str = "good", facts: List[Dict] = None) -> bool:
        """Send a notification to Teams via webhook."""
        if not self.config.enabled or not self.config.webhook_url:
            logger.debug("Teams notifications disabled or no webhook URL configured")
            return False
        
        try:
            # Create Teams message card
            card = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": self._get_color_code(color),
                "summary": title,
                "sections": [{
                    "activityTitle": title,
                    "activitySubtitle": f"RAG Document Classification System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "text": message,
                    "facts": facts or []
                }]
            }
            
            # Send to Teams
            response = requests.post(
                self.config.webhook_url,
                json=card,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Teams notification sent successfully: {title}")
                return True
            else:
                logger.error(f"Failed to send Teams notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Teams notification: {e}")
            return False
    
    def _get_color_code(self, color: str) -> str:
        """Convert color name to hex code for Teams."""
        color_map = {
            "good": "00FF00",
            "warning": "FFA500", 
            "attention": "FF0000",
            "accent": "0078D4",
            "default": "808080"
        }
        return color_map.get(color, color_map["default"])
    
    def notify_classification_success(self, filename: str, doc_type: str, category: str, 
                                    confidence: str, processing_time: float = None):
        """Notify successful document classification."""
        if not self.config.notify_on_success:
            return
        
        facts = [
            {"name": "Document", "value": filename},
            {"name": "Type", "value": doc_type},
            {"name": "Category", "value": category},
            {"name": "Confidence", "value": confidence}
        ]
        
        if processing_time:
            facts.append({"name": "Processing Time", "value": f"{processing_time:.2f} seconds"})
        
        message = f"Document '{filename}' has been successfully classified and metadata updated in SharePoint."
        
        if self.config.batch_notifications:
            self._add_to_batch("✅ Document Classified", message, "good", facts)
        else:
            self.send_notification("✅ Document Classification Success", message, "good", facts)
    
    def notify_classification_error(self, filename: str, error: str, step: str = ""):
        """Notify classification error."""
        if not self.config.notify_on_error:
            return
        
        facts = [
            {"name": "Document", "value": filename},
            {"name": "Error", "value": error}
        ]
        
        if step:
            facts.append({"name": "Failed Step", "value": step})
        
        message = f"Failed to process document '{filename}'. Manual intervention may be required."
        
        if self.config.batch_notifications:
            self._add_to_batch("❌ Classification Error", message, "attention", facts)
        else:
            self.send_notification("❌ Document Classification Error", message, "attention", facts)
    
    def notify_low_confidence(self, filename: str, doc_type: str, category: str, 
                            confidence: str, issues: List[str]):
        """Notify low confidence classification requiring review."""
        if not self.config.notify_on_low_confidence:
            return
        
        facts = [
            {"name": "Document", "value": filename},
            {"name": "Type", "value": doc_type},
            {"name": "Category", "value": category},
            {"name": "Confidence", "value": confidence},
            {"name": "Issues", "value": "; ".join(issues)}
        ]
        
        message = f"Document '{filename}' was classified with low confidence. Human review recommended."
        
        if self.config.batch_notifications:
            self._add_to_batch("⚠️ Low Confidence Classification", message, "warning", facts)
        else:
            self.send_notification("⚠️ Low Confidence Classification", message, "warning", facts)
    
    def notify_batch_summary(self, processed_count: int, success_count: int, 
                           error_count: int, low_confidence_count: int):
        """Send batch processing summary."""
        color = "good" if error_count == 0 else "warning" if error_count < processed_count / 2 else "attention"
        
        facts = [
            {"name": "Total Processed", "value": str(processed_count)},
            {"name": "Successful", "value": str(success_count)},
            {"name": "Errors", "value": str(error_count)},
            {"name": "Low Confidence", "value": str(low_confidence_count)},
            {"name": "Success Rate", "value": f"{(success_count/processed_count)*100:.1f}%" if processed_count > 0 else "0%"}
        ]
        
        message = f"Batch processing completed. {success_count} documents processed successfully."
        if error_count > 0:
            message += f" {error_count} errors occurred."
        if low_confidence_count > 0:
            message += f" {low_confidence_count} documents need review."
        
        self.send_notification("📊 Batch Processing Summary", message, color, facts)
    
    def notify_system_status(self, status: str, details: Dict):
        """Send system status notification."""
        facts = []
        for key, value in details.items():
            facts.append({"name": key.replace("_", " ").title(), "value": str(value)})
        
        color = "good" if status == "healthy" else "warning" if status == "degraded" else "attention"
        
        message = f"RAG Document Classification System status: {status.upper()}"
        
        self.send_notification("🔧 System Status Update", message, color, facts)
    
    def _add_to_batch(self, title: str, message: str, color: str, facts: List[Dict]):
        """Add notification to batch queue."""
        self.pending_notifications.append({
            'title': title,
            'message': message,
            'color': color,
            'facts': facts,
            'timestamp': datetime.now()
        })
        
        if len(self.pending_notifications) >= self.config.batch_size:
            self._send_batch_notifications()
    
    def _send_batch_notifications(self):
        """Send all pending batch notifications."""
        if not self.pending_notifications:
            return
        
        # Group by type
        grouped = {}
        for notif in self.pending_notifications:
            key = notif['title']
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(notif)
        
        # Send summary for each type
        for notification_type, notifications in grouped.items():
            count = len(notifications)
            if count == 1:
                # Single notification
                n = notifications[0]
                self.send_notification(n['title'], n['message'], n['color'], n['facts'])
            else:
                # Multiple notifications summary
                message = f"{count} {notification_type.lower()} notifications"
                facts = [{"name": "Count", "value": str(count)}]
                
                # Add sample details from latest
                latest = max(notifications, key=lambda x: x['timestamp'])
                facts.extend(latest['facts'][:3])  # First 3 facts only
                
                self.send_notification(f"{notification_type} (Batch)", message, latest['color'], facts)
        
        # Clear pending notifications
        self.pending_notifications.clear()
    
    def flush_batch(self):
        """Force send any pending batch notifications."""
        if self.pending_notifications:
            self._send_batch_notifications()

def load_teams_config() -> NotificationConfig:
    """Load Teams configuration from environment or config file."""
    import os
    
    config = NotificationConfig()
    
    # Try to load from environment variables
    config.webhook_url = os.getenv('TEAMS_WEBHOOK_URL', '')
    config.enabled = os.getenv('TEAMS_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
    config.notify_on_success = os.getenv('TEAMS_NOTIFY_SUCCESS', 'true').lower() == 'true'
    config.notify_on_error = os.getenv('TEAMS_NOTIFY_ERROR', 'true').lower() == 'true'
    config.notify_on_low_confidence = os.getenv('TEAMS_NOTIFY_LOW_CONFIDENCE', 'true').lower() == 'true'
    config.batch_notifications = os.getenv('TEAMS_BATCH_NOTIFICATIONS', 'false').lower() == 'true'
    
    # Try to load from config file
    try:
        config_path = '/home/azureuser/rag_project/teams_config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                for key, value in file_config.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
    except Exception as e:
        logger.warning(f"Could not load Teams config file: {e}")
    
    return config

# Global notifier instance
teams_notifier = TeamsNotifier(load_teams_config())

def notify_classification_success(filename: str, doc_type: str, category: str, confidence: str, processing_time: float = None):
    """Send Teams notification for successful classification."""
    teams_notifier.notify_classification_success(filename, doc_type, category, confidence, processing_time)

def notify_classification_error(filename: str, error: str, step: str = ""):
    """Send Teams notification for classification error."""
    teams_notifier.notify_classification_error(filename, error, step)

def notify_low_confidence_classification(filename: str, doc_type: str, category: str, confidence: str, issues: List[str]):
    """Send Teams notification for low confidence classification."""
    teams_notifier.notify_low_confidence(filename, doc_type, category, confidence, issues)

def notify_batch_summary(processed_count: int, success_count: int, error_count: int, low_confidence_count: int):
    """Send Teams notification for batch processing summary."""
    teams_notifier.notify_batch_summary(processed_count, success_count, error_count, low_confidence_count)

if __name__ == "__main__":
    # Test Teams integration (requires webhook URL)
    test_config = NotificationConfig(
        webhook_url="YOUR_TEAMS_WEBHOOK_URL_HERE",
        enabled=False  # Set to True and add real webhook URL to test
    )
    
    test_notifier = TeamsNotifier(test_config)
    
    # Test notification
    test_notifier.notify_classification_success(
        "test_document.pdf", 
        "Contract", 
        "Corporate", 
        "High",
        2.5
    )
    
    print("Teams integration ready. Configure webhook URL to enable notifications.")
