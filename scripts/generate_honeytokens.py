#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import random
from datetime import datetime, timedelta
from faker import Faker
import json

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.honeytoken import Honeytoken, TokenType, AlertConfig

# Initialize Faker
fake = Faker()

def generate_credential_token():
    """Generate a realistic looking credential honeytoken."""
    username = random.choice([
        fake.user_name(),
        fake.email(),
        f"admin_{fake.user_name()}",
        f"svc_{fake.domain_word()}"
    ])
    
    password = random.choice([
        fake.password(length=12),
        f"{fake.word().capitalize()}{fake.year()}{fake.special_char()}{fake.word()}",
        fake.md5()[:12]
    ])
    
    metadata = {
        "access_level": random.choice(["admin", "superuser", "system", "service"]),
        "department": fake.department(),
        "last_rotation": fake.date_time_this_year().isoformat()
    }
    
    return {
        "token_type": TokenType.CREDENTIAL,
        "token_value": json.dumps({"username": username, "password": password}),
        "description": f"High-privilege {metadata['access_level']} account credentials",
        "metadata": metadata
    }

def generate_customer_record():
    """Generate a realistic looking customer record honeytoken."""
    customer = {
        "id": fake.uuid4(),
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "ssn": fake.ssn(),
        "address": fake.address(),
        "credit_card": {
            "number": fake.credit_card_number(),
            "expiry": fake.credit_card_expire(),
            "cvv": fake.credit_card_security_code()
        },
        "account_balance": round(random.uniform(50000, 1000000), 2)
    }
    
    metadata = {
        "vip_status": "platinum",
        "risk_score": random.uniform(0.8, 0.95),
        "last_transaction": fake.date_time_this_month().isoformat()
    }
    
    return {
        "token_type": TokenType.CUSTOMER_RECORD,
        "token_value": json.dumps(customer),
        "description": "High-value customer record with sensitive information",
        "metadata": metadata
    }

def generate_financial_data():
    """Generate a realistic looking financial data honeytoken."""
    data = {
        "transaction_id": fake.uuid4(),
        "amount": round(random.uniform(1000000, 10000000), 2),
        "currency": "USD",
        "transaction_type": random.choice(["merger", "acquisition", "investment"]),
        "parties": [
            {"name": fake.company(), "role": "buyer"},
            {"name": fake.company(), "role": "seller"}
        ],
        "bank_details": {
            "account": fake.bban(),
            "routing": fake.aba(),
            "swift": fake.swift()
        }
    }
    
    metadata = {
        "confidentiality": "top_secret",
        "deal_stage": "pre_announcement",
        "sector": fake.industry()
    }
    
    return {
        "token_type": TokenType.FINANCIAL_DATA,
        "token_value": json.dumps(data),
        "description": f"Confidential {data['transaction_type']} transaction details",
        "metadata": metadata
    }

def generate_system_config():
    """Generate a realistic looking system configuration honeytoken."""
    config = {
        "api_keys": {
            "aws": fake.uuid4(),
            "gcp": fake.uuid4(),
            "azure": fake.uuid4()
        },
        "database": {
            "host": fake.ipv4(),
            "port": random.choice([3306, 5432, 27017]),
            "username": "root",
            "password": fake.password(length=16)
        },
        "encryption_keys": {
            "primary": fake.sha256(),
            "secondary": fake.sha256()
        }
    }
    
    metadata = {
        "environment": "production",
        "criticality": "high",
        "last_updated": fake.date_time_this_month().isoformat()
    }
    
    return {
        "token_type": TokenType.SYSTEM_CONFIG,
        "token_value": json.dumps(config),
        "description": "Critical system configuration and access credentials",
        "metadata": metadata
    }

def create_honeytoken(token_data):
    """Create a honeytoken and its alert configuration in the database."""
    token = Honeytoken(
        token_type=token_data["token_type"],
        token_value=token_data["token_value"],
        description=token_data["description"],
        metadata=token_data["metadata"]
    )
    
    db.session.add(token)
    db.session.flush()  # Get the token ID
    
    alert_config = AlertConfig(
        token_id=token.id,
        alert_threshold=1,
        cooldown_period=300,
        alert_channels=["email", "slack"],
        alert_message_template=(
            "ALERT: {token_type} honeytoken (ID: {token_id}) was accessed by {user_id} "
            "from {ip_address} at {access_time}. This may indicate a potential data breach."
        )
    )
    
    db.session.add(alert_config)
    return token

def main():
    """Generate and insert honeytokens into the database."""
    app = create_app()
    
    with app.app_context():
        # Generate different types of honeytokens
        generators = {
            "credentials": (generate_credential_token, 3),
            "customer_records": (generate_customer_record, 2),
            "financial_data": (generate_financial_data, 2),
            "system_configs": (generate_system_config, 2)
        }
        
        created_tokens = []
        
        try:
            for token_type, (generator, count) in generators.items():
                print(f"Generating {count} {token_type} honeytokens...")
                for _ in range(count):
                    token_data = generator()
                    token = create_honeytoken(token_data)
                    created_tokens.append(token)
            
            db.session.commit()
            print(f"Successfully created {len(created_tokens)} honeytokens")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error generating honeytokens: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main() 