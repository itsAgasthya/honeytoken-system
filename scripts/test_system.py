#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import json
import requests
from datetime import datetime
import time
import random
import mysql.connector
from dotenv import load_dotenv

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.honeytoken import Honeytoken, HoneytokenAccess, TokenType, AccessType

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

def test_honeytoken_generation():
    """Test the honeytoken generation system."""
    print("\n=== Testing Honeytoken Generation ===")
    
    try:
        # Run the generation script
        os.system('python scripts/generate_honeytokens.py')
        
        # Verify tokens were created
        app = create_app()
        with app.app_context():
            tokens = Honeytoken.query.all()
            print(f"Generated {len(tokens)} honeytokens:")
            
            for token in tokens:
                print(f"\nToken ID: {token.id}")
                print(f"Type: {token.token_type.value}")
                print(f"Description: {token.description}")
                print(f"Value Preview: {token.token_value[:100]}...")
                
                # Verify alert config
                alert_config = token.alert_configs[0]
                print(f"Alert Configuration: threshold={alert_config.alert_threshold}, "
                      f"channels={alert_config.alert_channels}")
        
        return True
    except Exception as e:
        print(f"Error testing honeytoken generation: {e}")
        return False

def test_access_logging():
    """Test the access logging system."""
    print("\n=== Testing Access Logging ===")
    
    try:
        app = create_app()
        with app.app_context():
            # Get a random token
            token = Honeytoken.query.order_by(db.func.random()).first()
            
            # Create test access logs
            access_types = [AccessType.READ, AccessType.WRITE]
            for i in range(3):
                log = HoneytokenAccess(
                    token_id=token.id,
                    access_time=datetime.utcnow(),
                    user_id=f"test_user_{i}",
                    ip_address=f"192.168.1.{random.randint(2, 254)}",
                    access_type=random.choice(access_types),
                    query_text="SELECT * FROM sensitive_data WHERE id = 1",
                    session_data={"browser": "Test Browser", "os": "Test OS"},
                    user_agent="Mozilla/5.0 (Test Browser)",
                    request_headers={"X-Test": "true"}
                )
                db.session.add(log)
            
            db.session.commit()
            
            # Verify logs were created
            logs = HoneytokenAccess.query.filter_by(token_id=token.id).all()
            print(f"\nCreated {len(logs)} test access logs for token {token.id}")
            for log in logs:
                print(f"Access Log: Time={log.access_time}, User={log.user_id}, "
                      f"IP={log.ip_address}, Type={log.access_type.value}")
        
        return True
    except Exception as e:
        print(f"Error testing access logging: {e}")
        return False

def test_monitoring_alerts():
    """Test the monitoring and alerting system."""
    print("\n=== Testing Monitoring & Alerts ===")
    
    try:
        # First, ensure the monitoring service is running
        service_status = os.system('systemctl is-active --quiet honeytoken-monitor')
        if service_status != 0:
            print("Starting monitoring service...")
            os.system('sudo systemctl start honeytoken-monitor')
        
        # Create some test access logs that should trigger alerts
        app = create_app()
        with app.app_context():
            token = Honeytoken.query.filter_by(is_active=1).first()
            
            print(f"\nCreating multiple access logs for token {token.id} to trigger alert...")
            for i in range(5):  # Create enough logs to exceed threshold
                log = HoneytokenAccess(
                    token_id=token.id,
                    access_time=datetime.utcnow(),
                    user_id="suspicious_user",
                    ip_address="10.0.0.100",
                    access_type=AccessType.READ,
                    query_text="SELECT * FROM sensitive_data",
                )
                db.session.add(log)
            
            db.session.commit()
        
        # Wait for the monitor to detect and process the access
        print("Waiting for alert processing (30 seconds)...")
        time.sleep(30)
        
        # Test the API endpoint that checks for alerts
        response = requests.post('http://localhost:5000/api/alerts/check')
        if response.status_code == 200:
            alerts = response.json().get('alerts', [])
            print(f"\nReceived {len(alerts)} alerts from the API")
            for alert in alerts:
                print(f"Alert for token {alert['token_id']}: "
                      f"{alert['access_count']} accesses detected")
        
        return True
    except Exception as e:
        print(f"Error testing monitoring alerts: {e}")
        return False

def test_web_dashboard():
    """Test the web dashboard functionality."""
    print("\n=== Testing Web Dashboard ===")
    
    try:
        # Test main dashboard page
        response = requests.get('http://localhost:5000/')
        if response.status_code == 200:
            print("Dashboard page loads successfully")
        
        # Test stats endpoint
        response = requests.get('http://localhost:5000/stats')
        if response.status_code == 200:
            stats = response.json()
            print("\nDashboard Statistics:")
            print(f"Total Tokens: {stats['total_tokens']}")
            print(f"Active Tokens: {stats['active_tokens']}")
            print(f"Total Access Events: {stats['total_access']}")
        
        # Test access logs endpoint
        response = requests.get('http://localhost:5000/api/access-logs')
        if response.status_code == 200:
            logs = response.json()
            print(f"\nRetrieved {len(logs)} access logs from API")
        
        # Test analytics endpoint
        response = requests.get('http://localhost:5000/api/analytics/access-patterns')
        if response.status_code == 200:
            analytics = response.json()
            print("\nAnalytics data retrieved successfully")
            print(f"Token stats: {len(analytics['token_stats'])} records")
            print(f"Daily stats: {len(analytics['daily_stats'])} days")
        
        return True
    except Exception as e:
        print(f"Error testing web dashboard: {e}")
        return False

def cleanup_test_data():
    """Clean up test data from the database."""
    print("\n=== Cleaning Up Test Data ===")
    
    try:
        app = create_app()
        with app.app_context():
            # Delete test access logs
            HoneytokenAccess.query.filter_by(user_id='test_user_0').delete()
            HoneytokenAccess.query.filter_by(user_id='suspicious_user').delete()
            db.session.commit()
            print("Test data cleaned up successfully")
        
        return True
    except Exception as e:
        print(f"Error cleaning up test data: {e}")
        return False

def simulate_unauthorized_access():
    """Simulate unauthorized access to honeytokens."""
    print("\n=== Simulating Unauthorized Access ===")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get an active honeytoken
        cursor.execute("""
            SELECT * FROM honeytokens 
            WHERE is_active = 1 
            LIMIT 1
        """)
        token = cursor.fetchone()
        
        if not token:
            print("No active honeytokens found")
            return False
        
        # Simulate multiple access attempts
        print(f"\nSimulating unauthorized access to token {token['id']}")
        
        for i in range(5):
            # Create access log
            cursor.execute("""
                INSERT INTO honeytoken_access_logs 
                (token_id, access_time, user_id, ip_address, access_type, query_text)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                token['id'],
                datetime.utcnow(),
                'suspicious_user',
                '192.168.1.100',
                'READ',
                'SELECT * FROM sensitive_data'
            ))
            
            print(f"Created access log {i+1}/5")
            time.sleep(1)  # Small delay between access attempts
        
        conn.commit()
        print("\nUnauthorized access simulation completed")
        return True
        
    except Exception as e:
        print(f"Error simulating unauthorized access: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def test_monitoring_system():
    """Test the monitoring system components."""
    print("\n=== Testing Monitoring System ===")
    
    try:
        # Test Elasticsearch connection
        es_response = requests.get('http://localhost:9200/_cluster/health')
        if es_response.status_code == 200:
            print("✅ Elasticsearch is running")
        else:
            print("❌ Elasticsearch is not responding")
            return False
        
        # Test Kibana connection
        kibana_response = requests.get('http://localhost:5601/api/status')
        if kibana_response.status_code == 200:
            print("✅ Kibana is running")
        else:
            print("❌ Kibana is not responding")
            return False
        
        # Test monitoring daemon
        daemon_status = os.system('systemctl is-active --quiet honeytoken-monitor')
        if daemon_status == 0:
            print("✅ Monitoring daemon is running")
        else:
            print("❌ Monitoring daemon is not running")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error testing monitoring system: {e}")
        return False

def main():
    """Run system tests based on command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python test_system.py [scenario]")
        print("Available scenarios:")
        print("  - unauthorized_access : Simulate unauthorized access")
        print("  - monitoring         : Test monitoring system")
        sys.exit(1)
    
    scenario = sys.argv[1]
    
    if scenario == "unauthorized_access":
        success = simulate_unauthorized_access()
    elif scenario == "monitoring":
        success = test_monitoring_system()
    else:
        print(f"Unknown scenario: {scenario}")
        sys.exit(1)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 