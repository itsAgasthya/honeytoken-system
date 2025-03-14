#!/usr/bin/env python3
import os
import sys
import json
import mysql.connector
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

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

def analyze_access_patterns(hours=24):
    """Analyze access patterns for the last specified hours."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get access logs for the specified time period
        cursor.execute("""
            SELECT 
                l.*,
                h.token_type,
                h.description
            FROM honeytoken_access_logs l
            JOIN honeytokens h ON l.token_id = h.id
            WHERE l.access_time >= %s
            ORDER BY l.access_time ASC
        """, (datetime.utcnow() - timedelta(hours=hours),))
        
        logs = cursor.fetchall()
        
        # Analyze patterns
        patterns = {
            'by_token': defaultdict(list),
            'by_ip': defaultdict(list),
            'by_user': defaultdict(list),
            'time_based': defaultdict(int),
            'anomalies': []
        }
        
        for log in logs:
            # Group by token
            patterns['by_token'][log['token_id']].append(log)
            
            # Group by IP
            patterns['by_ip'][log['ip_address']].append(log)
            
            # Group by user
            patterns['by_user'][log['user_id']].append(log)
            
            # Time-based analysis
            hour = log['access_time'].hour
            patterns['time_based'][hour] += 1
        
        # Detect anomalies
        anomalies = []
        
        # Check for rapid access attempts
        for ip, ip_logs in patterns['by_ip'].items():
            if len(ip_logs) >= 5:  # More than 5 attempts
                time_diff = (ip_logs[-1]['access_time'] - ip_logs[0]['access_time']).total_seconds()
                if time_diff < 60:  # Within 1 minute
                    anomalies.append({
                        'type': 'rapid_access',
                        'ip_address': ip,
                        'attempts': len(ip_logs),
                        'time_span': time_diff,
                        'timestamp': datetime.utcnow().isoformat()
                    })
        
        # Check for access during unusual hours
        business_hours = range(9, 18)  # 9 AM to 6 PM
        for hour, count in patterns['time_based'].items():
            if hour not in business_hours and count > 5:
                anomalies.append({
                    'type': 'unusual_hours',
                    'hour': hour,
                    'access_count': count,
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        # Check for multiple token access
        for user, user_logs in patterns['by_user'].items():
            unique_tokens = len(set(log['token_id'] for log in user_logs))
            if unique_tokens > 3:  # Accessing more than 3 different tokens
                anomalies.append({
                    'type': 'multiple_tokens',
                    'user_id': user,
                    'token_count': unique_tokens,
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        # Save anomalies to file
        os.makedirs('logs', exist_ok=True)
        with open('logs/anomalies.json', 'w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'analysis_period_hours': hours,
                'anomalies': anomalies
            }, f, indent=2)
        
        return patterns, anomalies
        
    finally:
        cursor.close()
        conn.close()

def show_recent_patterns(hours=24):
    """Display recent access patterns."""
    patterns, anomalies = analyze_access_patterns(hours)
    
    print(f"\nAccess Pattern Analysis (Last {hours} hours)")
    print("=" * 80)
    
    # Token access summary
    print("\nToken Access Summary:")
    print("-" * 40)
    for token_id, logs in patterns['by_token'].items():
        print(f"Token {token_id}: {len(logs)} accesses")
    
    # IP address summary
    print("\nIP Address Summary:")
    print("-" * 40)
    for ip, logs in patterns['by_ip'].items():
        print(f"IP {ip}: {len(logs)} accesses")
    
    # User activity summary
    print("\nUser Activity Summary:")
    print("-" * 40)
    for user, logs in patterns['by_user'].items():
        print(f"User {user}: {len(logs)} accesses")
    
    # Time-based summary
    print("\nHourly Access Distribution:")
    print("-" * 40)
    for hour in range(24):
        count = patterns['time_based'][hour]
        if count > 0:
            print(f"{hour:02d}:00 - {hour:02d}:59: {'#' * count} ({count})")
    
    # Anomalies
    if anomalies:
        print("\nDetected Anomalies:")
        print("-" * 40)
        for anomaly in anomalies:
            if anomaly['type'] == 'rapid_access':
                print(f"Rapid access from IP {anomaly['ip_address']}: "
                      f"{anomaly['attempts']} attempts in {anomaly['time_span']:.1f} seconds")
            elif anomaly['type'] == 'unusual_hours':
                print(f"Unusual activity at hour {anomaly['hour']:02d}:00: "
                      f"{anomaly['access_count']} accesses")
            elif anomaly['type'] == 'multiple_tokens':
                print(f"User {anomaly['user_id']} accessed {anomaly['token_count']} different tokens")
    
    print("\nDetailed analysis has been saved to logs/anomalies.json")

def main():
    """Main function to handle command line arguments."""
    hours = 24
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--show-recent':
            if len(sys.argv) > 2:
                try:
                    hours = int(sys.argv[2])
                except ValueError:
                    print("Invalid hours value. Using default 24 hours.")
            show_recent_patterns(hours)
        else:
            print("Unknown command. Available commands:")
            print("  --show-recent [hours] : Show recent access patterns")
    else:
        show_recent_patterns(hours)

if __name__ == "__main__":
    main() 