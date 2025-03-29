#!/usr/bin/env python3

"""
Sample Honeytoken Creation Script

This script creates sample honeytokens of various types for testing the system.
"""

import os
import sys
import json
import logging
import argparse
from src.models.honeytoken import create_honeytoken
from src.db.database import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sample_tokens')

def create_sample_file_honeytoken():
    """Create a sample file honeytoken"""
    content = """CONFIDENTIAL - INTERNAL USE ONLY
QUARTERLY FINANCIAL REPORT
Q4 2024

Revenue: $12,500,000
Expenses: $9,200,000
Profit: $3,300,000

New Product Launch: Project Phoenix
Budget Allocation: $2,500,000
Expected Release: Q2 2025

NOTES:
- Increase marketing budget by 15%
- Explore acquisition opportunities in Asia-Pacific region
- Board review scheduled for January 15, 2025

DO NOT SHARE WITH UNAUTHORIZED PERSONNEL
"""
    
    file_token = create_honeytoken(
        token_type="file",
        name="quarterly_financial_report",
        description="Fake quarterly financial report with sensitive information",
        sensitivity="high",
        file_path="/tmp/honeyfiles/quarterly_financial_report.txt",
        content=content
    )
    
    file_token.deploy()
    logger.info(f"Created file honeytoken: {file_token.name} (ID: {file_token.token_id})")
    return file_token

def create_sample_database_honeytoken():
    """Create a sample database honeytoken"""
    record_data = {
        "customer_id": "CUS1298754",
        "email": "johndoe@example.com",
        "name": "John Doe",
        "credit_card": "4111111111111111",
        "address": "123 Main St, Anytown, USA",
        "loyalty_points": 15000,
        "vip_status": True
    }
    
    db_token = create_honeytoken(
        token_type="database",
        name="premium_customer_record",
        description="Fake high-value customer data with credit card information",
        sensitivity="critical",
        table_name="customer_data",
        record_data=record_data
    )
    
    db_token.deploy()
    logger.info(f"Created database honeytoken: {db_token.name} (ID: {db_token.token_id})")
    return db_token

def create_sample_api_key_honeytoken():
    """Create a sample API key honeytoken"""
    api_token = create_honeytoken(
        token_type="api_key",
        name="payment_gateway_api_key",
        description="Fake API key for payment processing system",
        sensitivity="high",
        service_name="payment-gateway",
        key_prefix="pg-live-"
    )
    
    api_token.deploy()
    logger.info(f"Created API key honeytoken: {api_token.name} (ID: {api_token.token_id})")
    logger.info(f"API key value: {api_token.value}")
    return api_token

def create_sample_credentials_honeytoken():
    """Create a sample credentials honeytoken"""
    creds_token = create_honeytoken(
        token_type="credentials",
        name="admin_portal_credentials",
        description="Fake administrator credentials for internal portal",
        sensitivity="critical",
        username="admin_supervisor",
        service="admin-portal"
    )
    
    creds_token.deploy()
    logger.info(f"Created credentials honeytoken: {creds_token.name} (ID: {creds_token.token_id})")
    
    # Get the credential values from the stored token
    creds = json.loads(creds_token.value)
    username = creds.get('username')
    password = creds.get('password')
    logger.info(f"Username: {username}")
    logger.info(f"Password: {password}")
    
    return creds_token

def simulate_token_access(token_id, user_id=2):
    """Simulate access to a honeytoken"""
    from src.models.honeytoken import Honeytoken
    
    access_id = Honeytoken.log_access(
        token_id=token_id,
        user_id=user_id,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        method="file_open",
        context="Document viewed for 45 seconds",
        is_authorized=False
    )
    
    logger.info(f"Simulated unauthorized access to token {token_id} by user {user_id} - Access ID: {access_id}")
    return access_id

def main():
    """Main function to create sample honeytokens"""
    parser = argparse.ArgumentParser(description="Create sample honeytokens for testing")
    parser.add_argument('--access', action='store_true', help="Simulate access to the honeytokens")
    args = parser.parse_args()
    
    # Test database connection
    db = get_db()
    if not db.connection or not db.connection.is_connected():
        logger.error("Database connection failed")
        sys.exit(1)
        
    logger.info("Creating sample honeytokens...")
    
    # Create honeytokens
    file_token = create_sample_file_honeytoken()
    db_token = create_sample_database_honeytoken()
    api_token = create_sample_api_key_honeytoken()
    creds_token = create_sample_credentials_honeytoken()
    
    # Simulate access if requested
    if args.access:
        logger.info("Simulating access to honeytokens...")
        
        # Simulate access to the file token
        simulate_token_access(file_token.token_id, user_id=2)  # Analyst user
        
        # Simulate access to the API key token
        simulate_token_access(api_token.token_id, user_id=3)  # HR Manager
        
        # Simulate multiple accesses to the credentials token by different users
        simulate_token_access(creds_token.token_id, user_id=4)  # Developer
        simulate_token_access(creds_token.token_id, user_id=2)  # Analyst
        
    logger.info("Sample honeytokens created successfully")

if __name__ == "__main__":
    main() 