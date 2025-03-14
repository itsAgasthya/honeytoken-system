from forensics import ForensicsLogger
import time
from faker import Faker
import random
import uuid

fake = Faker()
logger = ForensicsLogger()

def generate_test_logs(num_entries=10):
    """Generate test honeytoken access logs."""
    token_types = ['database_credentials', 'api_key', 'ssh_key', 'oauth_token']
    
    for _ in range(num_entries):
        # Generate random data
        token_id = random.randint(1, 100)
        user_id = str(uuid.uuid4())
        ip_address = fake.ipv4()
        user_agent = random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'curl/7.64.1',
            'python-requests/2.31.0',
            'Postman/7.36.5'
        ])
        
        # Generate headers
        headers = {
            'user-agent': user_agent,
            'host': 'example.com',
            'accept': '*/*',
            'x-forwarded-for': ip_address
        }
        
        # Log the access attempt
        logger.log_access_attempt(
            token_id=token_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_headers=headers
        )
        
        # Add some suspicious access attempts
        if random.random() < 0.2:  # 20% chance of suspicious activity
            suspicious_ip = fake.ipv4()
            suspicious_ua = 'sqlmap/1.4.7'
            suspicious_headers = {
                'user-agent': suspicious_ua,
                'host': 'example.com',
                'accept': '*/*',
                'x-forwarded-for': suspicious_ip
            }
            
            logger.log_access_attempt(
                token_id=token_id,
                user_id=str(uuid.uuid4()),
                ip_address=suspicious_ip,
                user_agent=suspicious_ua,
                request_headers=suspicious_headers
            )
        
        time.sleep(1)  # Wait 1 second between entries

if __name__ == '__main__':
    print("Generating test logs...")
    generate_test_logs(20)
    print("Done generating test logs.") 