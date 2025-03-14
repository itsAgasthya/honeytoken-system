#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import time
import schedule
import smtplib
import json
import mysql.connector
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

def get_db_connection():
    """Create a database connection."""
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'honeytoken_db')
    )

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

def format_alert_message(template, token_data, access_log):
    """Format alert message using template and data."""
    return template.format(
        token_id=token_data['id'],
        token_type=token_data['token_type'],
        user_id=access_log['user_id'],
        ip_address=access_log['ip_address'],
        access_time=access_log['access_time'].strftime('%Y-%m-%d %H:%M:%S UTC'),
        query_text=access_log.get('query_text', 'N/A')
    )

def check_alerts():
    """Check for honeytoken access and send alerts."""
    print(f"Checking alerts at {datetime.utcnow()}")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all active honeytokens with their alert configs
        cursor.execute("""
            SELECT h.*, ac.*
            FROM honeytokens h
            JOIN alert_configs ac ON h.id = ac.token_id
            WHERE h.is_active = 1
        """)
        active_tokens = cursor.fetchall()
        
        for token in active_tokens:
            # Get recent access logs
            cursor.execute("""
                SELECT *
                FROM honeytoken_access_logs
                WHERE token_id = %s
                AND access_time >= %s
            """, (
                token['id'],
                datetime.utcnow() - timedelta(seconds=token['cooldown_period'])
            ))
            recent_logs = cursor.fetchall()
            
            if len(recent_logs) >= token['alert_threshold']:
                # Format and send alerts
                for access_log in recent_logs:
                    alert_message = format_alert_message(
                        token['alert_message_template'],
                        token,
                        access_log
                    )
                    
                    # Send alerts through configured channels
                    channels = json.loads(token['alert_channels'])
                    
                    if 'email' in channels:
                        send_email_alert(
                            subject=f"Honeytoken Alert - {token['token_type']} Access Detected",
                            body=alert_message,
                            recipients=[os.getenv('ALERT_RECIPIENTS')]
                        )
                    
                    if 'slack' in channels and os.getenv('SLACK_WEBHOOK_URL'):
                        send_slack_alert(
                            webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
                            message=alert_message
                        )
    finally:
        cursor.close()
        conn.close()

def cleanup_old_logs():
    """Clean up old access logs to prevent database bloat."""
    print("Cleaning up old access logs...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Delete logs older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        cursor.execute("""
            DELETE FROM honeytoken_access_logs
            WHERE access_time < %s
        """, (cutoff_date,))
        
        conn.commit()
        print(f"Deleted {cursor.rowcount} old access logs")
        
    except Exception as e:
        conn.rollback()
        print(f"Error cleaning up old logs: {e}")
    finally:
        cursor.close()
        conn.close()

def show_active_monitoring():
    """Display active monitoring status."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get active honeytokens
        cursor.execute("""
            SELECT h.id, h.token_type, h.is_active,
                   COUNT(l.id) as access_count,
                   MAX(l.access_time) as last_access
            FROM honeytokens h
            LEFT JOIN honeytoken_access_logs l ON h.id = l.token_id
            WHERE h.is_active = 1
            GROUP BY h.id
        """)
        active_tokens = cursor.fetchall()
        
        print("\nActive Honeytoken Monitoring Status:")
        print("=" * 80)
        print(f"{'ID':<5} {'Type':<15} {'Access Count':<15} {'Last Access':<25}")
        print("-" * 80)
        
        for token in active_tokens:
            last_access = token['last_access'].strftime('%Y-%m-%d %H:%M:%S') if token['last_access'] else 'Never'
            print(f"{token['id']:<5} {token['token_type']:<15} {token['access_count']:<15} {last_access:<25}")
        
        print("=" * 80)
        
    finally:
        cursor.close()
        conn.close()

def main():
    """Main daemon process."""
    print("Starting honeytoken monitoring daemon...")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--show-active':
        show_active_monitoring()
        return
    
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