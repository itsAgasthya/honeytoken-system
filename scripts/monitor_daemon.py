#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import time
import schedule
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.honeytoken import Honeytoken, HoneytokenAccess, AlertConfig

# Load environment variables
load_dotenv()

def send_email_alert(subject, body, recipients):
    """Send an email alert using configured SMTP server."""
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SMTP_USER')
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT'))) as server:
            server.starttls()
            server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
            server.send_message(msg)
            
        print(f"Email alert sent to {recipients}")
        return True
    except Exception as e:
        print(f"Error sending email alert: {e}")
        return False

def send_slack_alert(webhook_url, message):
    """Send an alert to Slack using webhook."""
    try:
        payload = {
            "text": message,
            "username": "Honeytoken Monitor",
            "icon_emoji": ":warning:"
        }
        
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        
        print("Slack alert sent successfully")
        return True
    except Exception as e:
        print(f"Error sending Slack alert: {e}")
        return False

def format_alert_message(template, token, access_log):
    """Format alert message using template and data."""
    return template.format(
        token_id=token.id,
        token_type=token.token_type.value,
        user_id=access_log.user_id,
        ip_address=access_log.ip_address,
        access_time=access_log.access_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        query_text=access_log.query_text
    )

def check_alerts():
    """Check for honeytoken access and send alerts."""
    print(f"Checking alerts at {datetime.utcnow()}")
    
    app = create_app()
    with app.app_context():
        # Get all active honeytokens with their alert configs
        active_tokens = db.session.query(
            Honeytoken, AlertConfig
        ).join(
            AlertConfig
        ).filter(
            Honeytoken.is_active == 1
        ).all()
        
        for token, config in active_tokens:
            # Get recent access logs
            recent_logs = HoneytokenAccess.query.filter(
                HoneytokenAccess.token_id == token.id,
                HoneytokenAccess.access_time >= datetime.utcnow() - timedelta(seconds=config.cooldown_period)
            ).all()
            
            if len(recent_logs) >= config.alert_threshold:
                # Format and send alerts
                for access_log in recent_logs:
                    alert_message = format_alert_message(
                        config.alert_message_template,
                        token,
                        access_log
                    )
                    
                    # Send alerts through configured channels
                    if 'email' in config.alert_channels:
                        send_email_alert(
                            subject=f"Honeytoken Alert - {token.token_type.value} Access Detected",
                            body=alert_message,
                            recipients=[os.getenv('ALERT_RECIPIENTS')]
                        )
                    
                    if 'slack' in config.alert_channels and os.getenv('SLACK_WEBHOOK_URL'):
                        send_slack_alert(
                            webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
                            message=alert_message
                        )

def cleanup_old_logs():
    """Clean up old access logs to prevent database bloat."""
    print("Cleaning up old access logs...")
    
    app = create_app()
    with app.app_context():
        # Delete logs older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        try:
            deleted = HoneytokenAccess.query.filter(
                HoneytokenAccess.access_time < cutoff_date
            ).delete()
            
            db.session.commit()
            print(f"Deleted {deleted} old access logs")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error cleaning up old logs: {e}")

def main():
    """Main daemon process."""
    print("Starting honeytoken monitoring daemon...")
    
    # Schedule tasks
    schedule.every(int(os.getenv('HONEYTOKEN_CHECK_INTERVAL', 60))).seconds.do(check_alerts)
    schedule.every().day.at("00:00").do(cleanup_old_logs)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down monitoring daemon...")
            break
        except Exception as e:
            print(f"Error in monitoring daemon: {e}")
            time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    main() 