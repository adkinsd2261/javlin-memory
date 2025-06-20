
import os
import json
import requests
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger('MemoryOS.Alerts')

class AlertManager:
    """Simple alerting system for critical errors"""
    
    def __init__(self):
        self.webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        self.email_webhook = os.getenv('EMAIL_WEBHOOK_URL')  # Zapier, IFTTT, etc.
        self.alert_threshold = int(os.getenv('ALERT_THRESHOLD', '3'))  # errors before alert
        self.error_count = 0
        self.last_alert_time = None
        self.cooldown_minutes = 15  # Prevent spam
        
    def should_send_alert(self) -> bool:
        """Check if we should send an alert based on error count and cooldown"""
        if not (self.webhook_url or self.email_webhook):
            return False
            
        now = datetime.now(timezone.utc)
        
        # Check cooldown
        if self.last_alert_time:
            minutes_since_last = (now - self.last_alert_time).seconds / 60
            if minutes_since_last < self.cooldown_minutes:
                return False
                
        return self.error_count >= self.alert_threshold
    
    def record_error(self, error_message: str, error_type: str = "SYSTEM_ERROR"):
        """Record an error and potentially send alert"""
        self.error_count += 1
        logger.error(f"Alert Manager: {error_type} - {error_message}")
        
        if self.should_send_alert():
            self.send_alert(error_message, error_type)
            self.error_count = 0  # Reset counter after sending alert
            self.last_alert_time = datetime.now(timezone.utc)
    
    def record_recovery(self):
        """Reset error count on successful operations"""
        if self.error_count > 0:
            self.error_count = max(0, self.error_count - 1)
    
    def send_alert(self, message: str, alert_type: str = "CRITICAL_ERROR"):
        """Send alert via webhook"""
        alert_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "MemoryOS-Clean",
            "alert_type": alert_type,
            "message": message,
            "error_count": self.error_count,
            "severity": "HIGH" if self.error_count >= 5 else "MEDIUM"
        }
        
        # Try webhook first
        if self.webhook_url:
            try:
                response = requests.post(
                    self.webhook_url,
                    json=alert_data,
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )
                if response.status_code == 200:
                    logger.info(f"Alert sent successfully via webhook")
                    return
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")
        
        # Try email webhook (Zapier, IFTTT, etc.)
        if self.email_webhook:
            try:
                email_data = {
                    "subject": f"🚨 MemoryOS Alert: {alert_type}",
                    "body": f"""
MemoryOS Critical Alert

Service: MemoryOS-Clean
Alert Type: {alert_type}
Timestamp: {alert_data['timestamp']}
Error Count: {self.error_count}
Severity: {alert_data['severity']}

Message:
{message}

Please check the system logs and health endpoint:
https://your-repl-name.replit.app/health

Log file: memoryos.log
                    """.strip()
                }
                
                response = requests.post(
                    self.email_webhook,
                    json=email_data,
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(f"Alert sent successfully via email webhook")
                    return
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
    
    def test_alert(self) -> bool:
        """Test the alerting system"""
        try:
            self.send_alert("Test alert - MemoryOS alerting system is working", "TEST")
            return True
        except Exception as e:
            logger.error(f"Alert test failed: {e}")
            return False

# Global alert manager instance
alert_manager = AlertManager()

def setup_alerts():
    """Setup instructions for alerting"""
    instructions = """
🚨 ALERTING SETUP INSTRUCTIONS

To enable alerts for critical errors:

1. **Webhook Alerts (Recommended)**
   - Set environment variable: ALERT_WEBHOOK_URL
   - Use services like:
     * Discord webhook
     * Slack webhook
     * Microsoft Teams webhook
     * Custom webhook endpoint

2. **Email Alerts**
   - Set environment variable: EMAIL_WEBHOOK_URL
   - Use services like:
     * Zapier webhook → Email
     * IFTTT webhook → Email
     * Make.com webhook → Email

3. **Configuration**
   - ALERT_THRESHOLD (default: 3) - errors before alert
   - Cooldown: 15 minutes between alerts

4. **Test Alerts**
   - Call alert_manager.test_alert() to verify setup

Example webhook URLs:
- Discord: https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN
- Slack: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
    """
    
    print(instructions)
    return instructions

if __name__ == "__main__":
    setup_alerts()
