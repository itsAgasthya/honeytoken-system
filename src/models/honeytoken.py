import uuid
import json
import logging
import os
import hashlib
import random
import string
from datetime import datetime
from ..db.database import get_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/honeytoken.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('honeytoken')

class Honeytoken:
    """Base class for all honeytoken types"""
    
    def __init__(self, name=None, token_type=None, value=None, location=None, description=None, sensitivity="medium"):
        self.name = name or f"honeytoken_{uuid.uuid4().hex[:8]}"
        self.token_type = token_type
        self.value = value
        self.location = location
        self.description = description
        self.sensitivity = sensitivity
        self.created_at = datetime.now()
        self.is_active = True
        self.token_id = None  # To be set after DB insertion
        
    def save(self):
        """Save the honeytoken to the database"""
        db = get_db()
        data = {
            'token_name': self.name,
            'token_type': self.token_type,
            'token_value': self.value,
            'token_location': self.location,
            'description': self.description,
            'sensitivity_level': self.sensitivity,
            'is_active': self.is_active
        }
        
        self.token_id = db.insert('honeytokens', data)
        logger.info(f"Honeytoken saved to database with ID: {self.token_id}")
        return self.token_id
        
    def update(self):
        """Update the honeytoken in the database"""
        if not self.token_id:
            logger.error("Cannot update honeytoken: no token_id")
            return False
            
        db = get_db()
        data = {
            'token_name': self.name,
            'token_type': self.token_type,
            'token_value': self.value,
            'token_location': self.location,
            'description': self.description,
            'sensitivity_level': self.sensitivity,
            'is_active': self.is_active
        }
        
        condition = {'token_id': self.token_id}
        affected_rows = db.update('honeytokens', data, condition)
        logger.info(f"Honeytoken updated in database, affected rows: {affected_rows}")
        return affected_rows > 0
        
    def delete(self):
        """Delete the honeytoken from the database"""
        if not self.token_id:
            logger.error("Cannot delete honeytoken: no token_id")
            return False
            
        db = get_db()
        condition = {'token_id': self.token_id}
        affected_rows = db.delete('honeytokens', condition)
        logger.info(f"Honeytoken deleted from database, affected rows: {affected_rows}")
        return affected_rows > 0
        
    def deactivate(self):
        """Deactivate the honeytoken instead of deleting it"""
        self.is_active = False
        return self.update()
        
    def activate(self):
        """Activate a previously deactivated honeytoken"""
        self.is_active = True
        return self.update()
        
    @staticmethod
    def get_by_id(token_id):
        """Retrieve a honeytoken by its ID"""
        db = get_db()
        query = "SELECT * FROM honeytokens WHERE token_id = %s"
        result = db.fetch_one(query, (token_id,))
        
        if result:
            token = Honeytoken()
            token.token_id = result['token_id']
            token.name = result['token_name']
            token.token_type = result['token_type']
            token.value = result['token_value']
            token.location = result['token_location']
            token.description = result['description']
            token.sensitivity = result['sensitivity_level']
            token.created_at = result['created_at']
            token.is_active = result['is_active']
            return token
        
        return None
        
    @staticmethod
    def get_all(active_only=True):
        """Retrieve all honeytokens"""
        db = get_db()
        query = "SELECT * FROM honeytokens"
        if active_only:
            query += " WHERE is_active = TRUE"
        results = db.fetch_all(query)
        
        tokens = []
        for result in results:
            token = Honeytoken()
            token.token_id = result['token_id']
            token.name = result['token_name']
            token.token_type = result['token_type']
            token.value = result['token_value']
            token.location = result['token_location']
            token.description = result['description']
            token.sensitivity = result['sensitivity_level']
            token.created_at = result['created_at']
            token.is_active = result['is_active']
            tokens.append(token)
        
        return tokens
        
    @staticmethod
    def log_access(token_id, user_id, ip_address, user_agent=None, method=None, context=None, is_authorized=False):
        """Log access to a honeytoken"""
        db = get_db()
        access_id = db.log_honeytoken_access(
            token_id, user_id, ip_address, user_agent, method, context, is_authorized
        )
        
        # Create forensic logs
        if access_id:
            forensic_data = {
                'timestamp': datetime.now().isoformat(),
                'token_id': token_id,
                'user_id': user_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'method': method,
                'context': context,
                'is_authorized': is_authorized
            }
            
            # Log the raw data for forensic analysis
            db.create_forensic_log(
                access_id=access_id,
                log_type='application',
                source='honeytoken_system',
                log_data=json.dumps(forensic_data, indent=2)
            )
            
            logger.warning(f"Honeytoken access detected - Token ID: {token_id}, User ID: {user_id}, IP: {ip_address}")
        
        return access_id

class FileHoneytoken(Honeytoken):
    """Honeytoken implemented as a file"""
    
    def __init__(self, name=None, content=None, file_path=None, file_type="txt", description=None, sensitivity="medium"):
        # Default content if none provided
        if content is None:
            content = f"CONFIDENTIAL INFORMATION - DO NOT SHARE\nDocument ID: {uuid.uuid4()}\nCreated: {datetime.now().isoformat()}"
            
        self.file_type = file_type
        self.file_path = file_path or f"/tmp/honeyfiles/{name or uuid.uuid4().hex}.{file_type}"
        
        super().__init__(
            name=name,
            token_type="file",
            value=content,
            location=self.file_path,
            description=description,
            sensitivity=sensitivity
        )
        
    def deploy(self):
        """Create the honey file on the system"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Write the file
            with open(self.file_path, 'w') as f:
                f.write(self.value)
                
            logger.info(f"Deployed file honeytoken at {self.file_path}")
            
            # Save to database if not already saved
            if not self.token_id:
                self.save()
                
            return True
        except Exception as e:
            logger.error(f"Error deploying file honeytoken: {e}")
            return False
            
    def remove(self):
        """Remove the honey file from the system"""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                logger.info(f"Removed file honeytoken at {self.file_path}")
                
            # Deactivate in database
            self.deactivate()
            return True
        except Exception as e:
            logger.error(f"Error removing file honeytoken: {e}")
            return False

class DatabaseHoneytoken(Honeytoken):
    """Honeytoken implemented as database entries"""
    
    def __init__(self, name=None, table_name=None, record_data=None, description=None, sensitivity="medium"):
        self.table_name = table_name or "customer_data"
        
        # Default record data if none provided
        if record_data is None:
            # Generate fake but realistic-looking data
            fake_id = ''.join(random.choices(string.digits, k=10))
            fake_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
            record_data = {
                "customer_id": fake_id,
                "email": fake_email,
                "credit_card": f"4{''.join(random.choices(string.digits, k=15))}",
                "notes": "High-value customer account"
            }
            
        super().__init__(
            name=name,
            token_type="database",
            value=json.dumps(record_data),
            location=f"table:{self.table_name}",
            description=description,
            sensitivity=sensitivity
        )
        
    def deploy(self):
        """Create a honeytoken record in a database table"""
        # This is a placeholder - in a real implementation,
        # you would create the actual table and insert the record
        logger.info(f"Deployed database honeytoken in table {self.table_name}")
        
        # Save to database if not already saved
        if not self.token_id:
            self.save()
            
        return True
            
    def remove(self):
        """Remove the honey record from the database"""
        # This is a placeholder - in a real implementation,
        # you would delete the actual record
        logger.info(f"Removed database honeytoken from table {self.table_name}")
        
        # Deactivate in database
        self.deactivate()
        return True

class APIKeyHoneytoken(Honeytoken):
    """Honeytoken implemented as fake API keys"""
    
    def __init__(self, name=None, service_name=None, key_prefix=None, description=None, sensitivity="high"):
        self.service_name = service_name or "internal-api"
        self.key_prefix = key_prefix or "api-"
        
        # Generate a realistic-looking API key
        api_key = self.generate_api_key()
        
        super().__init__(
            name=name,
            token_type="api_key",
            value=api_key,
            location=f"service:{self.service_name}",
            description=description,
            sensitivity=sensitivity
        )
        
    def generate_api_key(self):
        """Generate a realistic looking API key"""
        key_base = uuid.uuid4().hex
        key_hash = hashlib.sha256(key_base.encode()).hexdigest()[:24]
        return f"{self.key_prefix}{key_hash}"
        
    def deploy(self):
        """Deploy the API key honeytoken (simulated)"""
        # In a real implementation, you might add this to a config file
        # or a secrets management system monitored by your detection systems
        logger.info(f"Deployed API key honeytoken for service {self.service_name}")
        
        # Save to database if not already saved
        if not self.token_id:
            self.save()
            
        return True
            
    def remove(self):
        """Remove the API key honeytoken"""
        logger.info(f"Removed API key honeytoken for service {self.service_name}")
        
        # Deactivate in database
        self.deactivate()
        return True

class CredentialsHoneytoken(Honeytoken):
    """Honeytoken implemented as fake login credentials"""
    
    def __init__(self, name=None, username=None, service=None, description=None, sensitivity="high"):
        self.username = username or f"user_{uuid.uuid4().hex[:8]}"
        self.service = service or "internal-portal"
        self.password = self.generate_password()
        
        creds_value = json.dumps({
            "username": self.username,
            "password": self.password,
            "service": self.service
        })
        
        super().__init__(
            name=name,
            token_type="credentials",
            value=creds_value,
            location=f"service:{self.service}",
            description=description,
            sensitivity=sensitivity
        )
        
    def generate_password(self):
        """Generate a random password"""
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choices(chars, k=12))
        
    def deploy(self):
        """Deploy the credentials honeytoken (simulated)"""
        # In a real implementation, you might add this to a credentials file
        logger.info(f"Deployed credentials honeytoken for service {self.service}")
        
        # Save to database if not already saved
        if not self.token_id:
            self.save()
            
        return True
            
    def remove(self):
        """Remove the credentials honeytoken"""
        logger.info(f"Removed credentials honeytoken for service {self.service}")
        
        # Deactivate in database
        self.deactivate()
        return True

# Factory function to create honeytokens of different types
def create_honeytoken(token_type, **kwargs):
    """Factory function to create different types of honeytokens"""
    if token_type == "file":
        return FileHoneytoken(**kwargs)
    elif token_type == "database":
        return DatabaseHoneytoken(**kwargs)
    elif token_type == "api_key":
        return APIKeyHoneytoken(**kwargs)
    elif token_type == "credentials":
        return CredentialsHoneytoken(**kwargs)
    else:
        raise ValueError(f"Unknown honeytoken type: {token_type}") 