#!/usr/bin/env python3
"""
Seed Demo Data Script

This script seeds the database with sample data for demonstration purposes,
including users, honeytokens, activities, alerts, and anomaly scores.
"""

import os
import sys
import json
import random
import logging
import argparse
import mysql.connector
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('seed_demo_data')

# Database connection settings - match with .dbcredentials
DB_CONFIG = {
    'user': 'root',
    'password': '123',
    'host': 'localhost',
    'database': 'honeytoken_ueba'
}

# User profiles
USER_PROFILES = {
    1: {
        "name": "Admin User",
        "role": "administrator",
        "department": "IT",
        "email": "admin@example.com",
        "normal_actions": ["login", "system_config", "user_management", "audit_logs"],
        "work_hours": (8, 18)  # 8 AM to 6 PM
    },
    2: {
        "name": "John Smith",
        "role": "analyst",
        "department": "Finance",
        "email": "john.smith@example.com",
        "normal_actions": ["login", "report_access", "database_query", "file_download"],
        "work_hours": (9, 17)  # 9 AM to 5 PM
    },
    3: {
        "name": "Alice Johnson",
        "role": "hr_manager",
        "department": "HR",
        "email": "alice.johnson@example.com",
        "normal_actions": ["login", "employee_record", "payroll_access", "document_upload"],
        "work_hours": (8, 16)  # 8 AM to 4 PM
    },
    4: {
        "name": "Bob Williams",
        "role": "developer",
        "department": "Engineering",
        "email": "bob.williams@example.com",
        "normal_actions": ["login", "code_repository", "build_server", "deployment"],
        "work_hours": (10, 19)  # 10 AM to 7 PM
    }
}

# Sample honeytokens
HONEYTOKENS = [
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
        "name": "AWS Access Key",
        "type": "api_key",
        "value": "AKIA1234567890EXAMPLE",
        "location": "~/.aws/credentials",
        "sensitivity": "critical",
        "description": "Fake AWS credentials that would trigger alerts if used"
    },
    {
        "name": "Decoy Document",
        "type": "document",
        "value": "Confidential_Acquisition_Plan.docx",
        "location": "/shared/executive/",
        "sensitivity": "high",
        "description": "Fake merger and acquisition document with trackers"
    }
]

# Sample resources for each activity type
RESOURCES = {
    "login": ["workstation", "vpn", "cloud_dashboard", "admin_panel"],
    "system_config": ["/etc/config.json", "/etc/security/policies.xml", "/opt/apps/settings.ini"],
    "user_management": ["/admin/users", "/admin/roles", "/admin/permissions"],
    "audit_logs": ["/var/log/audit.log", "/var/log/security.log", "/opt/logging/events.log"],
    "report_access": ["/reports/q1_finance.pdf", "/reports/annual_summary.xlsx", "/dashboards/kpi"],
    "database_query": ["SELECT * FROM customers", "UPDATE inventory SET stock=0", "INSERT INTO orders"],
    "file_download": ["/documents/confidential.pdf", "/reports/salaries.xlsx", "/backups/database.sql"],
    "employee_record": ["/hr/employees/1001", "/hr/employees/1042", "/hr/employees/2076"],
    "payroll_access": ["/finance/payroll/march", "/finance/payroll/q1", "/finance/compensation"],
    "document_upload": ["/hr/policies/updated_handbook.docx", "/hr/contracts/new_template.pdf"],
    "code_repository": ["git://repo/main", "git://repo/feature/login", "git://repo/hotfix/security"],
    "build_server": ["/jenkins/jobs/main-build", "/jenkins/jobs/nightly", "/jenkins/jobs/release"],
    "deployment": ["/kubernetes/deploy/production", "/kubernetes/deploy/staging", "/docker/compose/up"]
}

# Sample IP addresses
IP_RANGES = {
    "internal": ["192.168.1.", "10.0.0.", "172.16.0."],
    "vpn": ["10.8.0.", "10.9.0."],
    "external": ["203.0.113.", "198.51.100.", "209.85.231."]
}

# Sample user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
]

def connect_to_database():
    """Connect to the MySQL database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        logger.info(f"Connected to MySQL database '{DB_CONFIG['database']}'")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Failed to connect to MySQL database: {err}")
        sys.exit(1)

def seed_users(conn, clear_existing=False):
    """Seed user data into the database"""
    cursor = conn.cursor()
    
    if clear_existing:
        try:
            cursor.execute("DELETE FROM users")
            logger.info("Cleared existing user data")
        except mysql.connector.Error as err:
            logger.warning(f"Error clearing users table: {err}")
    
    # Check if users table has data
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info(f"Users table already has {count} rows")
        cursor.close()
        return
    
    for user_id, profile in USER_PROFILES.items():
        query = """
        INSERT INTO users (user_id, username, email, department, role, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        created_at = datetime.now() - timedelta(days=random.randint(30, 365))
        values = (
            user_id,
            profile["name"],
            profile["email"],
            profile["department"],
            profile["role"],
            created_at.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        try:
            cursor.execute(query, values)
            logger.info(f"Inserted user: {profile['name']}")
        except mysql.connector.Error as err:
            logger.error(f"Failed to insert user {profile['name']}: {err}")
    
    conn.commit()
    cursor.close()

def seed_honeytokens(conn, clear_existing=False):
    """Seed honeytoken data into the database"""
    cursor = conn.cursor()
    
    if clear_existing:
        try:
            cursor.execute("DELETE FROM honeytokens")
            logger.info("Cleared existing honeytoken data")
        except mysql.connector.Error as err:
            logger.warning(f"Error clearing honeytokens table: {err}")
    
    # Check if honeytokens table has data
    cursor.execute("SELECT COUNT(*) FROM honeytokens")
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info(f"Honeytokens table already has {count} rows")
        cursor.close()
        return
    
    for i, token in enumerate(HONEYTOKENS, start=1):
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
        
        try:
            cursor.execute(query, values)
            logger.info(f"Inserted honeytoken: {token['name']}")
        except mysql.connector.Error as err:
            logger.error(f"Failed to insert honeytoken {token['name']}: {err}")
    
    conn.commit()
    cursor.close()

def generate_random_ip(user_id):
    """Generate a random IP address for user activity"""
    
    # Admin users mostly use internal IPs
    if user_id == 1:
        ranges = random.choices(
            [IP_RANGES["internal"], IP_RANGES["vpn"], IP_RANGES["external"]],
            weights=[0.8, 0.15, 0.05], 
            k=1
        )[0]
    # Normal users have a mix of internal and VPN
    else:
        ranges = random.choices(
            [IP_RANGES["internal"], IP_RANGES["vpn"], IP_RANGES["external"]],
            weights=[0.6, 0.3, 0.1], 
            k=1
        )[0]
    
    base = random.choice(ranges)
    return f"{base}{random.randint(1, 254)}"

def seed_activities(conn, num_activities=1000, clear_existing=False):
    """Seed user activity data into the database"""
    cursor = conn.cursor()
    
    if clear_existing:
        try:
            cursor.execute("DELETE FROM user_activities")
            logger.info("Cleared existing user activity data")
        except mysql.connector.Error as err:
            logger.warning(f"Error clearing user_activities table: {err}")
    
    # Check if user_activities table has data
    cursor.execute("SELECT COUNT(*) FROM user_activities")
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info(f"User activities table already has {count} rows")
        cursor.close()
        return
    
    # Initialize activity counter
    activities_added = 0
    
    # Generate activities for the past 14 days
    for day in range(14, 0, -1):
        # Calculate date
        date = datetime.now() - timedelta(days=day)
        
        # Generate more activities for weekdays
        daily_activities = num_activities // 10
        if date.weekday() < 5:  # 0-4 are Monday to Friday
            daily_activities = int(daily_activities * 1.5)
        
        # For each user, generate activities
        for user_id, profile in USER_PROFILES.items():
            # Number of activities per user varies
            user_activities_count = random.randint(
                daily_activities // 8, 
                daily_activities // 4
            )
            
            for _ in range(user_activities_count):
                # Choose activity type from user's normal actions
                activity_type = random.choice(profile["normal_actions"])
                
                # Generate timestamp within the user's work hours for the current day
                work_start, work_end = profile["work_hours"]
                
                # Occasionally (10% chance) generate activity outside normal hours
                if random.random() < 0.1:
                    hour = random.choice(list(range(0, work_start)) + list(range(work_end, 24)))
                else:
                    hour = random.randint(work_start, work_end)
                
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                timestamp = date.replace(hour=hour, minute=minute, second=second)
                
                # Choose a resource based on activity type
                resource = random.choice(RESOURCES.get(activity_type, ["unknown"]))
                
                # Generate IP address
                ip_address = generate_random_ip(user_id)
                
                # Choose user agent
                user_agent = random.choice(USER_AGENTS)
                
                # Add activity to database
                query = """
                INSERT INTO user_activities 
                (user_id, activity_type, resource_accessed, ip_address, user_agent, timestamp) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    user_id, 
                    activity_type,
                    resource,
                    ip_address,
                    user_agent,
                    timestamp.strftime('%Y-%m-%d %H:%M:%S')
                )
                
                try:
                    cursor.execute(query, values)
                    activities_added += 1
                    
                    # Update last_login time for the user
                    update_query = """
                    UPDATE users SET last_login = %s WHERE user_id = %s
                    """
                    cursor.execute(update_query, (timestamp.strftime('%Y-%m-%d %H:%M:%S'), user_id))
                    
                    # Commit after every 100 inserts
                    if activities_added % 100 == 0:
                        conn.commit()
                        logger.info(f"Added {activities_added} activities")
                except mysql.connector.Error as err:
                    logger.error(f"Error adding activity: {err}")
    
    # Final commit
    conn.commit()
    logger.info(f"Added a total of {activities_added} user activities")
    cursor.close()

def seed_alerts(conn, alert_percentage=0.05, clear_existing=False):
    """Seed alert data into the database"""
    cursor = conn.cursor()
    
    if clear_existing:
        try:
            cursor.execute("DELETE FROM alerts")
            logger.info("Cleared existing alert data")
        except mysql.connector.Error as err:
            logger.warning(f"Error clearing alerts table: {err}")
    
    # Check if alerts table has data
    cursor.execute("SELECT COUNT(*) FROM alerts")
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info(f"Alerts table already has {count} rows")
        cursor.close()
        return
    
    # Get all activities
    cursor.execute("""
    SELECT activity_id, user_id, activity_type, resource_accessed, ip_address, timestamp 
    FROM user_activities
    """)
    
    activities = cursor.fetchall()
    alerts_added = 0
    
    # First create honeytoken access records, then use those to create alerts
    for activity in random.sample(activities, int(len(activities) * alert_percentage)):
        activity_id, user_id, activity_type, resource, ip_address, timestamp = activity
        
        # Choose alert type and severity - make sure to use only valid enum values
        alert_types = ["access", "unusual_behavior", "multiple_access", "unauthorized"]
        severity_levels = ["low", "medium", "high", "critical"]
        severity_weights = [0.4, 0.3, 0.2, 0.1]  # More low/medium than high/critical
        
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
        
        # Randomly select a honeytoken
        token_id = random.randint(1, len(HONEYTOKENS))
        
        # First create a honeytoken access record
        honeytoken_query = """
        INSERT INTO honeytoken_access 
        (token_id, user_id, ip_address, user_agent, access_time, access_method, is_authorized, access_duration, additional_context) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Choose a user agent
        user_agent = random.choice(USER_AGENTS)
        
        # Generate access method
        access_methods = ["web_browser", "api_call", "command_line", "application"]
        access_method = random.choice(access_methods)
        
        # Generate access duration (in seconds)
        access_duration = random.randint(10, 300)
        
        # Additional context as JSON
        additional_context = json.dumps({
            "activity_id": activity_id,
            "activity_type": activity_type,
            "resource": resource,
            "referrer": f"http://{random.choice(['internal', 'external'])}.example.com/{random.choice(['login', 'dashboard', 'reports'])}"
        })
        
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
        
        try:
            cursor.execute(honeytoken_query, honeytoken_values)
            access_id = cursor.lastrowid  # Get the auto-generated access_id
            
            # Now create an alert with this access_id
            # 30% of alerts are resolved
            is_resolved = random.random() < 0.3
            
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
            alerts_added += 1
            
            # Commit after every 20 inserts
            if alerts_added % 20 == 0:
                conn.commit()
                logger.info(f"Added {alerts_added} alerts")
        except mysql.connector.Error as err:
            logger.error(f"Error adding alert: {err}")
    
    # Final commit
    conn.commit()
    logger.info(f"Added a total of {alerts_added} alerts")
    cursor.close()

def seed_anomaly_scores(conn, anomaly_percentage=0.10, clear_existing=False):
    """Seed anomaly score data into the database"""
    cursor = conn.cursor()
    
    if clear_existing:
        try:
            cursor.execute("DELETE FROM anomaly_scores")
            logger.info("Cleared existing anomaly score data")
        except mysql.connector.Error as err:
            logger.warning(f"Error clearing anomaly_scores table: {err}")
    
    # Check if anomaly_scores table has data
    cursor.execute("SELECT COUNT(*) FROM anomaly_scores")
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info(f"Anomaly scores table already has {count} rows")
        cursor.close()
        return
    
    # Get all activities
    cursor.execute("""
    SELECT activity_id, user_id, activity_type, timestamp 
    FROM user_activities
    """)
    
    activities = cursor.fetchall()
    anomalies_added = 0
    
    # For a percentage of activities, generate anomaly scores
    for activity in random.sample(activities, int(len(activities) * anomaly_percentage)):
        activity_id, user_id, activity_type, timestamp = activity
        
        # Generate several anomaly records for different features
        features = {
            "login_time": {
                "expected": random.uniform(9.0, 17.0),  # Expected login during business hours
                "actual": random.uniform(0.0, 24.0)     # Actual login time
            },
            "access_frequency": {
                "expected": random.uniform(1.0, 10.0),  # Expected access frequency
                "actual": random.uniform(10.0, 50.0)    # Higher than expected
            },
            "resource_access_pattern": {
                "expected": random.uniform(0.1, 0.5),   # Expected resource access diversity
                "actual": random.uniform(0.6, 0.9)      # Higher diversity than expected
            },
            "ip_address_range": {
                "expected": random.uniform(0.7, 0.9),   # Expected IP address in normal range
                "actual": random.uniform(0.1, 0.5)      # Unusual IP address
            },
            "session_duration": {
                "expected": random.uniform(30.0, 120.0),  # Expected session duration
                "actual": random.uniform(150.0, 480.0)    # Longer session than expected
            }
        }
        
        for feature_name, values in features.items():
            # Skip some features randomly
            if random.random() > 0.7:
                continue
                
            query = """
            INSERT INTO anomaly_scores 
            (user_id, activity_id, feature_name, expected_value, actual_value, anomaly_score, timestamp) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            # Generate anomaly score based on difference between expected and actual
            diff = abs(values["actual"] - values["expected"])
            normalized_diff = min(diff / values["expected"], 1.0)  # Normalize to 0-1
            
            # Add some randomness
            anomaly_score = min(normalized_diff * random.uniform(0.8, 1.2), 1.0)
            
            values_tuple = (
                user_id,
                activity_id,
                feature_name,
                values["expected"],
                values["actual"],
                anomaly_score,
                timestamp.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            try:
                cursor.execute(query, values_tuple)
                anomalies_added += 1
                
                # Commit after every 50 inserts
                if anomalies_added % 50 == 0:
                    conn.commit()
                    logger.info(f"Added {anomalies_added} anomaly scores")
            except mysql.connector.Error as err:
                logger.error(f"Error adding anomaly score: {err}")
    
    # Final commit
    conn.commit()
    logger.info(f"Added a total of {anomalies_added} anomaly scores")
    cursor.close()

def seed_behavioral_baselines(conn, clear_existing=False):
    """Seed behavioral baseline data into the database"""
    cursor = conn.cursor()
    
    if clear_existing:
        try:
            cursor.execute("DELETE FROM behavioral_baselines")
            logger.info("Cleared existing behavioral baseline data")
        except mysql.connector.Error as err:
            logger.warning(f"Error clearing behavioral_baselines table: {err}")
    
    # Check if behavioral_baselines table has data
    cursor.execute("SELECT COUNT(*) FROM behavioral_baselines")
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info(f"Behavioral baselines table already has {count} rows")
        cursor.close()
        return
    
    # Define features to add for each user
    features = {
        "login_frequency": {"min": 1.0, "max": 10.0},
        "avg_session_duration": {"min": 30.0, "max": 240.0},
        "working_hours_start": {"min": 8.0, "max": 10.0},
        "working_hours_end": {"min": 16.0, "max": 19.0},
        "file_access_frequency": {"min": 5.0, "max": 50.0},
        "database_query_frequency": {"min": 2.0, "max": 20.0},
        "resource_access_diversity": {"min": 0.1, "max": 0.9},
        "authentication_failures": {"min": 0.0, "max": 2.0},
        "privilege_usage_score": {"min": 0.1, "max": 0.8},
        "peer_group_similarity": {"min": 0.5, "max": 0.95}
    }
    
    baselines_added = 0
    
    # For each user, add behavioral baselines
    for user_id in USER_PROFILES.keys():
        for feature_name, range_vals in features.items():
            # Generate feature value within range
            feature_value = random.uniform(range_vals["min"], range_vals["max"])
            
            # Add some variety based on user role
            if user_id == 1:  # Admin
                if feature_name == "privilege_usage_score":
                    feature_value *= 2  # Admins use more privileges
            elif user_id == 4:  # Developer
                if feature_name == "resource_access_diversity":
                    feature_value *= 1.5  # Developers access more diverse resources
            
            # Generate confidence score (higher for longer-established baselines)
            confidence_score = random.uniform(0.7, 0.95)
            
            # Generate timestamp for when the baseline was last updated
            last_updated = datetime.now() - timedelta(days=random.randint(1, 14))
            
            query = """
            INSERT INTO behavioral_baselines 
            (user_id, feature_name, feature_value, confidence_score, last_updated) 
            VALUES (%s, %s, %s, %s, %s)
            """
            
            values = (
                user_id,
                feature_name,
                feature_value,
                confidence_score,
                last_updated.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            try:
                cursor.execute(query, values)
                baselines_added += 1
            except mysql.connector.Error as err:
                logger.error(f"Error adding behavioral baseline: {err}")
    
    # Commit changes
    conn.commit()
    logger.info(f"Added a total of {baselines_added} behavioral baselines")
    cursor.close()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Seed demo data into the database')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')
    parser.add_argument('--activities', type=int, default=1000, help='Number of activities to generate')
    parser.add_argument('--alert-percentage', type=float, default=0.05, help='Percentage of activities that should generate alerts')
    parser.add_argument('--anomaly-percentage', type=float, default=0.10, help='Percentage of activities that should have anomaly scores')
    parser.add_argument('--anomaly-scores-only', action='store_true', help='Only generate anomaly scores for existing activities')
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    # Connect to database
    conn = connect_to_database()
    
    if args.anomaly_scores_only:
        seed_anomaly_scores(conn, args.anomaly_percentage, args.clear)
    else:
        # Seed all data
        seed_users(conn, args.clear)
        seed_honeytokens(conn, args.clear)
        seed_activities(conn, args.activities, args.clear)
        seed_alerts(conn, args.alert_percentage, args.clear)
        seed_anomaly_scores(conn, args.anomaly_percentage, args.clear)
        seed_behavioral_baselines(conn, args.clear)
    
    conn.close()
    logger.info("Done!")

if __name__ == "__main__":
    main() 