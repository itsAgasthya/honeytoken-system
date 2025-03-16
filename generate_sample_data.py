import random
import datetime
import json
from elasticsearch import Elasticsearch
from datetime import timedelta

# Initialize Elasticsearch client
es = Elasticsearch("http://localhost:9200")

# Sample data configuration
USERS = ["john.doe", "jane.smith", "admin.user", "guest.user", "system.service"]
IP_ADDRESSES = ["192.168.1.100", "10.0.0.1", "172.16.0.50", "127.0.0.1"]
RESOURCE_TYPES = ["employee_data", "payroll_info", "admin_credentials", "system_config"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Python-requests/2.31.0",
    "curl/7.68.0"
]

def generate_access_log(timestamp):
    """Generate a single access log entry"""
    return {
        "timestamp": timestamp.isoformat(),
        "user_id": random.choice(USERS),
        "ip_address": random.choice(IP_ADDRESSES),
        "resource_type": random.choice(RESOURCE_TYPES),
        "access_type": "read",
        "user_agent": random.choice(USER_AGENTS),
        "session_id": f"sess_{random.randint(1000, 9999)}",
        "success": random.choice([True, False]),
        "metadata": {
            "endpoint": f"/api/{random.choice(['employee', 'admin', 'system'])}/{random.randint(1, 100)}",
            "request_method": "GET"
        }
    }

def generate_alert(timestamp, access_count):
    """Generate an alert based on access patterns"""
    return {
        "timestamp": timestamp.isoformat(),
        "alert_type": "excessive_access",
        "resource_type": random.choice(RESOURCE_TYPES),
        "access_count": access_count,
        "severity": random.choice(["low", "medium", "high"]),
        "status": "triggered",
        "metadata": {
            "threshold": random.choice([5, 10, 15]),
            "time_window": "1h"
        }
    }

def main():
    """Generate and index sample data"""
    # Create indices if they don't exist
    access_index = "honeytoken-access-logs"
    alert_index = "honeytoken-alerts"
    
    # Generate data for the last 7 days
    end_time = datetime.datetime.now()
    start_time = end_time - timedelta(days=7)
    current_time = start_time
    
    print("Generating sample data...")
    
    while current_time < end_time:
        # Generate 1-5 access logs per hour
        for _ in range(random.randint(1, 5)):
            access_time = current_time + timedelta(minutes=random.randint(0, 59))
            access_log = generate_access_log(access_time)
            
            # Index access log
            es.index(index=access_index, document=access_log)
            
            # Generate alert if access count is high
            if random.random() < 0.1:  # 10% chance of generating an alert
                alert = generate_alert(access_time, random.randint(5, 20))
                es.index(index=alert_index, document=alert)
        
        current_time += timedelta(hours=1)
    
    # Refresh indices
    es.indices.refresh(index=[access_index, alert_index])
    
    print("Sample data generation complete!")
    print(f"Generated data from {start_time} to {end_time}")

if __name__ == "__main__":
    main() 