#!/usr/bin/env python3
"""
Load Offline Activities Script

This script reads all offline activity files from the ./offline_activities directory
and loads them into the database to ensure the dashboard and UEBA display have sufficient data.
"""

import os
import sys
import json
import glob
import logging
import random
import mysql.connector
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('load_offline_activities')

# Database connection settings - match with .dbcredentials
DB_CONFIG = {
    'user': 'root',
    'password': '123',
    'host': 'localhost',
    'database': 'honeytoken_ueba'
}

def connect_to_database():
    """Connect to the MySQL database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        logger.info(f"Connected to MySQL database '{DB_CONFIG['database']}'")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Failed to connect to MySQL database: {err}")
        sys.exit(1)

def process_activity(conn, activity_data):
    """Process an activity and save it to the database"""
    cursor = conn.cursor()
    
    try:
        # Map fields from activity file to database columns
        user_id = activity_data.get('user_id')
        activity_type = activity_data.get('activity_type')
        ip_address = activity_data.get('ip_address')
        user_agent = activity_data.get('user_agent')
        resource = activity_data.get('resource')
        details = activity_data.get('details', {})
        
        # Convert timestamp if it exists
        timestamp = None
        if 'timestamp' in details:
            try:
                timestamp = datetime.strptime(details['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                try:
                    timestamp = datetime.strptime(details['timestamp'], '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    logger.error(f"Invalid timestamp format: {details['timestamp']}")
        
        # If no timestamp, use a random time in the past 24 hours
        if not timestamp:
            timestamp = datetime.now() - timedelta(hours=random.uniform(0, 24))
        
        # Convert details to JSON if it's a dict
        if isinstance(details, dict):
            details_json = json.dumps(details)
        else:
            details_json = details
        
        # Insert activity into user_activities table
        query = """
        INSERT INTO user_activities 
        (user_id, activity_type, resource_accessed, ip_address, user_agent, timestamp, action_details) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            user_id,
            activity_type,
            resource,
            ip_address,
            user_agent,
            timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            details_json
        )
        
        cursor.execute(query, values)
        activity_id = cursor.lastrowid
        
        # Update the user's last_login time
        update_query = """
        UPDATE users SET last_login = %s WHERE user_id = %s
        """
        cursor.execute(update_query, (timestamp.strftime('%Y-%m-%d %H:%M:%S'), user_id))
        
        # Generate anomaly score for some activities (about 15%)
        if random.random() < 0.15:
            generate_anomaly_score(conn, user_id, activity_id, timestamp)
            
        # Generate alert for some anomalous activities (about 5%)
        if random.random() < 0.05:
            generate_alert(conn, user_id, activity_id, activity_type, resource, ip_address, timestamp)
            
        return activity_id
        
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        return None
    finally:
        cursor.close()

def generate_anomaly_score(conn, user_id, activity_id, timestamp):
    """Generate anomaly scores for an activity"""
    cursor = conn.cursor()
    
    try:
        features = {
            "login_time": {
                "expected": random.uniform(9.0, 17.0),
                "actual": random.uniform(0.0, 24.0)
            },
            "access_frequency": {
                "expected": random.uniform(1.0, 10.0),
                "actual": random.uniform(10.0, 50.0)
            },
            "resource_access_pattern": {
                "expected": random.uniform(0.1, 0.5),
                "actual": random.uniform(0.6, 0.9)
            },
            "ip_address_range": {
                "expected": random.uniform(0.7, 0.9),
                "actual": random.uniform(0.1, 0.5)
            },
            "session_duration": {
                "expected": random.uniform(30.0, 120.0),
                "actual": random.uniform(150.0, 480.0)
            }
        }
        
        for feature_name, values in features.items():
            # Skip some features randomly
            if random.random() > 0.7:
                continue
                
            # Generate anomaly score based on difference between expected and actual
            diff = abs(values["actual"] - values["expected"])
            normalized_diff = min(diff / values["expected"], 1.0)
            
            # Add some randomness
            anomaly_score = min(normalized_diff * random.uniform(0.8, 1.2), 1.0)
            
            query = """
            INSERT INTO anomaly_scores 
            (user_id, activity_id, feature_name, expected_value, actual_value, anomaly_score, timestamp) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values_tuple = (
                user_id,
                activity_id,
                feature_name,
                values["expected"],
                values["actual"],
                anomaly_score,
                timestamp.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            cursor.execute(query, values_tuple)
            
    except mysql.connector.Error as err:
        logger.error(f"Error adding anomaly score: {err}")
    finally:
        cursor.close()

def generate_alert(conn, user_id, activity_id, activity_type, resource, ip_address, timestamp):
    """Generate an alert for an activity"""
    cursor = conn.cursor()
    
    try:
        # Choose alert type and severity
        alert_types = ["access", "unusual_behavior", "multiple_access", "unauthorized"]
        severity_levels = ["low", "medium", "high", "critical"]
        severity_weights = [0.4, 0.3, 0.2, 0.1]
        
        alert_type = random.choice(alert_types)
        severity = random.choices(severity_levels, weights=severity_weights, k=1)[0]
        
        # Generate description based on alert type
        if alert_type == "access":
            description = f"Suspicious access detected from IP {ip_address} at unusual time"
        elif alert_type == "unusual_behavior":
            description = f"User accessed {resource} outside normal working hours"
        elif alert_type == "multiple_access":
            description = f"Multiple access attempts from different locations"
        else:  # unauthorized
            description = f"Unauthorized access attempt to restricted resource: {resource}"
        
        # Randomly select a honeytoken (1-5)
        token_id = random.randint(1, 5)
        
        # First create a honeytoken access record
        access_methods = ["web_browser", "api_call", "command_line", "application"]
        access_method = random.choice(access_methods)
        access_duration = random.randint(10, 300)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        additional_context = json.dumps({
            "activity_id": activity_id,
            "activity_type": activity_type,
            "resource": resource,
            "referrer": f"http://{random.choice(['internal', 'external'])}.example.com/{random.choice(['login', 'dashboard', 'reports'])}"
        })
        
        honeytoken_query = """
        INSERT INTO honeytoken_access 
        (token_id, user_id, ip_address, user_agent, access_time, access_method, is_authorized, access_duration, additional_context) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        honeytoken_values = (
            token_id,
            user_id,
            ip_address,
            user_agent,
            timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            access_method,
            0,  # is_authorized (0 = false)
            access_duration,
            additional_context
        )
        
        cursor.execute(honeytoken_query, honeytoken_values)
        access_id = cursor.lastrowid
        
        # Now create an alert with this access_id
        is_resolved = random.random() < 0.3  # 30% of alerts are resolved
        
        alert_query = """
        INSERT INTO alerts 
        (user_id, alert_type, severity, timestamp, description, is_resolved, token_id, access_id) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        alert_values = (
            user_id,
            alert_type,
            severity,
            timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            description,
            is_resolved,
            token_id,
            access_id
        )
        
        cursor.execute(alert_query, alert_values)
        
    except mysql.connector.Error as err:
        logger.error(f"Error adding alert: {err}")
    finally:
        cursor.close()

def ensure_honeytokens_exist(conn):
    """Ensure honeytokens exist in the database"""
    cursor = conn.cursor()
    
    try:
        # Check if honeytokens exist
        cursor.execute("SELECT COUNT(*) FROM honeytokens")
        count = cursor.fetchone()[0]
        
        if count > 0:
            logger.info(f"Honeytokens table has {count} rows")
            return True
        
        # Define sample honeytokens
        honeytokens = [
            {
                "name": "Secret API Key",
                "type": "api_key",
                "value": "eXaMpLe_API_k3Y_12345",
                "location": "/config/api_keys.json",
                "sensitivity": "high",
                "description": "A fake API key that looks like it could access our payment processing system"
            },
            {
                "name": "Test User Account",
                "type": "credentials",
                "value": "test_user:test_password",
                "location": "/etc/passwd",
                "sensitivity": "medium",
                "description": "Fake administrator credentials"
            },
            {
                "name": "Database Backup",
                "type": "file",
                "value": "backup_20250327.sql",
                "location": "/backups/database/",
                "sensitivity": "critical",
                "description": "Honeypot database backup file that appears to contain customer data"
            },
            {
                "name": "Customer Database",
                "type": "database",
                "value": "customer_db_connection_string",
                "location": "/config/database/",
                "sensitivity": "critical",
                "description": "Fake database connection string"
            },
            {
                "name": "HR Document",
                "type": "document",
                "value": "employee_salaries.xlsx",
                "location": "/hr/confidential/",
                "sensitivity": "high",
                "description": "Fake HR document containing salary information"
            }
        ]
        
        # Insert honeytokens
        for i, token in enumerate(honeytokens, start=1):
            query = """
            INSERT INTO honeytokens (token_id, token_name, token_type, token_value, token_location, 
                                   description, sensitivity_level, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            created_at = datetime.now() - timedelta(days=random.randint(1, 30))
            values = (
                i,
                token["name"],
                token["type"],
                token["value"],
                token["location"],
                token["description"],
                token["sensitivity"],
                1,  # is_active
                created_at.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            cursor.execute(query, values)
            logger.info(f"Inserted honeytoken: {token['name']}")
        
        conn.commit()
        return True
        
    except mysql.connector.Error as err:
        logger.error(f"Error ensuring honeytokens exist: {err}")
        return False
    finally:
        cursor.close()

def load_offline_activities():
    """Load all offline activities from the ./offline_activities directory"""
    offline_dir = "./offline_activities"
    processed_dir = os.path.join(offline_dir, "processed")
    
    # Check if directories exist
    if not os.path.isdir(offline_dir):
        logger.error(f"Directory not found: {offline_dir}")
        return False
    
    if not os.path.isdir(processed_dir):
        logger.error(f"Processed directory not found: {processed_dir}")
        return False
    
    # Get all JSON files from both directories
    activity_files = glob.glob(os.path.join(offline_dir, "*.json"))
    processed_files = glob.glob(os.path.join(processed_dir, "*.json"))
    
    all_files = activity_files + processed_files
    logger.info(f"Found {len(all_files)} offline activity files")
    
    if not all_files:
        logger.warning("No offline activity files found")
        return False
    
    # Connect to database
    conn = connect_to_database()
    
    try:
        # Ensure honeytokens exist
        if not ensure_honeytokens_exist(conn):
            logger.error("Failed to ensure honeytokens exist")
            return False
        
        processed_count = 0
        
        for file_path in all_files:
            try:
                with open(file_path, 'r') as f:
                    activity_data = json.load(f)
                
                # Process the activity
                activity_id = process_activity(conn, activity_data)
                
                if activity_id:
                    processed_count += 1
                    
                    # Move processed file to processed directory if it's not already there
                    if not file_path.startswith(processed_dir):
                        processed_path = os.path.join(processed_dir, os.path.basename(file_path))
                        os.rename(file_path, processed_path)
                        logger.debug(f"Moved {file_path} to {processed_path}")
                
                # Commit after every 50 activities
                if processed_count % 50 == 0:
                    conn.commit()
                    logger.info(f"Processed {processed_count} activities")
                
            except (json.JSONDecodeError, IOError) as err:
                logger.error(f"Error reading activity file {file_path}: {err}")
        
        # Final commit
        conn.commit()
        logger.info(f"Successfully processed {processed_count} offline activities")
        return True
        
    except Exception as e:
        logger.error(f"Error processing offline activities: {str(e)}")
        return False
    finally:
        conn.close()
        logger.info("Database connection closed")

def main():
    """Main function"""
    logger.info("Starting offline activities loading")
    success = load_offline_activities()
    
    if success:
        logger.info("Offline activities loaded successfully")
    else:
        logger.error("Failed to load offline activities")

if __name__ == "__main__":
    main() 