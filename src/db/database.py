import mysql.connector
import logging
import os
import time
from mysql.connector import Error, pooling
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/database.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('database')

class Database:
    def __init__(self, host=None, user=None, password=None, database=None):
        # Try to load credentials from .dbcredentials file if they exist
        if os.path.exists('.dbcredentials'):
            creds = {}
            with open('.dbcredentials', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        creds[key] = value

            self.host = host or creds.get('DB_HOST', 'localhost')
            self.user = user or creds.get('DB_USER', 'root')
            self.password = password or creds.get('DB_PASS', '123')
            self.database = database or creds.get('DB_NAME', 'honeytoken_ueba')
        else:
            self.host = host or 'localhost'
            self.user = user or 'root'
            self.password = password or '123'
            self.database = database or 'honeytoken_ueba'
        
        self.connection = None
        self.pool = None
        self._setup_connection_pool()
        self.connect()

    def _setup_connection_pool(self):
        """Setup a connection pool for better handling of concurrent requests"""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="honeytoken_pool",
                pool_size=5,
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            logger.info(f"Connection pool created for MySQL database '{self.database}'")
        except Error as e:
            logger.error(f"Error creating connection pool: {e}")
            self.pool = None

    def connect(self):
        """Connect to the MySQL database"""
        try:
            # Try to get a connection from the pool first
            if self.pool:
                try:
                    self.connection = self.pool.get_connection()
                    self.connection.autocommit = True
                    logger.info(f"Connected to MySQL database '{self.database}' from pool")
                    return True
                except:
                    logger.warning("Failed to get connection from pool, falling back to direct connection")
                    # Continue to direct connection if pool connection fails
            
            # Direct connection if pool is not available or failed
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    passwd=self.password,
                    database=self.database,
                    use_pure=True,  # Use pure Python implementation for better stability
                    connection_timeout=30
                )
                # Set autocommit to True to avoid transaction issues
                self.connection.autocommit = True
                logger.info(f"Connected to MySQL database '{self.database}'")
                return True
            elif not self.connection.is_connected():
                # Reconnect if connection was lost
                self.connection.reconnect(attempts=3, delay=1)
                logger.info(f"Reconnected to MySQL database '{self.database}'")
                return True
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            return False
            
        return self.connection.is_connected()

    def ensure_connection(self):
        """Ensure database connection is active, reconnect if needed"""
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                if self.connection is None:
                    return self.connect()
                
                if not self.connection.is_connected():
                    # Connection lost, try to reconnect
                    try:
                        self.connection.ping(reconnect=True, attempts=3, delay=1)
                        if self.connection.is_connected():
                            logger.info(f"Reconnected to MySQL database '{self.database}'")
                            return True
                    except:
                        # If ping with reconnect fails, try to establish a new connection
                        return self.connect()
                
                return True
            except Error as e:
                logger.error(f"Error ensuring database connection (attempt {attempt+1}/{max_attempts}): {e}")
                attempt += 1
                time.sleep(1)  # Wait before retry
                
        # Last attempt - try to establish a fresh connection
        return self.connect()

    def disconnect(self):
        """Disconnect from the database"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Disconnected from MySQL database")
            return True
        return False

    def execute_query(self, query, params=None):
        """Execute a query without returning a result"""
        cursor = None
        attempt = 0
        max_attempts = 3
        
        while attempt < max_attempts:
            try:
                if not self.ensure_connection():
                    attempt += 1
                    if attempt < max_attempts:
                        time.sleep(1)
                        continue
                    return False
                    
                cursor = self.connection.cursor()
                cursor.execute(query, params or ())
                self.connection.commit()
                return True
            except Error as e:
                logger.error(f"Error executing query (attempt {attempt+1}/{max_attempts}): {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                if self.connection and self.connection.is_connected():
                    self.connection.rollback()
                
                attempt += 1
                if attempt < max_attempts:
                    time.sleep(1)
                    # Reset the connection before retrying
                    self.connect()
                else:
                    return False
            finally:
                if cursor:
                    cursor.close()

    def fetch_all(self, query, params=None):
        """Execute a query and return all results"""
        cursor = None
        attempt = 0
        max_attempts = 3
        
        while attempt < max_attempts:
            try:
                if not self.ensure_connection():
                    attempt += 1
                    if attempt < max_attempts:
                        time.sleep(1)
                        continue
                    return []
                    
                # Create a new connection for this query to avoid "commands out of sync"
                connection = None
                try:
                    if self.pool:
                        connection = self.pool.get_connection()
                    else:
                        connection = mysql.connector.connect(
                            host=self.host,
                            user=self.user,
                            passwd=self.password,
                            database=self.database
                        )
                    
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute(query, params or ())
                    result = cursor.fetchall()
                    return result
                finally:
                    # Always close the cursor and specific connection
                    if cursor:
                        cursor.close()
                    if connection and connection.is_connected():
                        connection.close()
            except Error as e:
                logger.error(f"Error fetching data (attempt {attempt+1}/{max_attempts}): {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                
                attempt += 1
                if attempt < max_attempts:
                    time.sleep(1)
                else:
                    return []

    def fetch_one(self, query, params=None):
        """Execute a query and return one result"""
        cursor = None
        attempt = 0
        max_attempts = 3
        
        while attempt < max_attempts:
            try:
                if not self.ensure_connection():
                    attempt += 1
                    if attempt < max_attempts:
                        time.sleep(1)
                        continue
                    return None
                    
                # Create a new connection for this query to avoid "commands out of sync"
                connection = None
                try:
                    if self.pool:
                        connection = self.pool.get_connection()
                    else:
                        connection = mysql.connector.connect(
                            host=self.host,
                            user=self.user,
                            passwd=self.password,
                            database=self.database
                        )
                    
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute(query, params or ())
                    result = cursor.fetchone()
                    return result
                finally:
                    # Always close the cursor and specific connection
                    if cursor:
                        cursor.close()
                    if connection and connection.is_connected():
                        connection.close()
            except Error as e:
                logger.error(f"Error fetching data (attempt {attempt+1}/{max_attempts}): {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                
                attempt += 1
                if attempt < max_attempts:
                    time.sleep(1)
                else:
                    return None

    def insert(self, table, data):
        """Insert data into a table and return the ID"""
        cursor = None
        attempt = 0
        max_attempts = 3
        
        while attempt < max_attempts:
            try:
                if not self.ensure_connection():
                    attempt += 1
                    if attempt < max_attempts:
                        time.sleep(1)
                        continue
                    return None
                    
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                
                cursor = self.connection.cursor()
                cursor.execute(query, list(data.values()))
                self.connection.commit()
                
                last_id = cursor.lastrowid
                
                logger.info(f"Data inserted into {table}, ID: {last_id}")
                return last_id
            except Error as e:
                logger.error(f"Error inserting data (attempt {attempt+1}/{max_attempts}): {e}")
                logger.error(f"Table: {table}")
                logger.error(f"Data: {data}")
                if self.connection and self.connection.is_connected():
                    self.connection.rollback()
                
                attempt += 1
                if attempt < max_attempts:
                    time.sleep(1)
                    # Reset the connection before retrying
                    self.connect()
                else:
                    return None
            finally:
                if cursor:
                    cursor.close()

    def update(self, table, data, condition):
        """Update data in a table"""
        cursor = None
        try:
            if not self.ensure_connection():
                return False
                
            set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
            where_clause = " AND ".join([f"{key} = %s" for key in condition.keys()])
            
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            
            cursor = self.connection.cursor()
            cursor.execute(query, list(data.values()) + list(condition.values()))
            self.connection.commit()
            
            affected_rows = cursor.rowcount
            
            logger.info(f"Data updated in {table}, {affected_rows} rows affected")
            return affected_rows > 0
        except Error as e:
            logger.error(f"Error updating data: {e}")
            logger.error(f"Table: {table}")
            logger.error(f"Data: {data}")
            logger.error(f"Condition: {condition}")
            if self.connection and self.connection.is_connected():
                self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def delete(self, table, condition):
        """Delete data from a table"""
        cursor = None
        try:
            if not self.ensure_connection():
                return False
                
            where_clause = " AND ".join([f"{key} = %s" for key in condition.keys()])
            
            query = f"DELETE FROM {table} WHERE {where_clause}"
            
            cursor = self.connection.cursor()
            cursor.execute(query, list(condition.values()))
            self.connection.commit()
            
            affected_rows = cursor.rowcount
            
            logger.info(f"Data deleted from {table}, {affected_rows} rows affected")
            return affected_rows > 0
        except Error as e:
            logger.error(f"Error deleting data: {e}")
            logger.error(f"Table: {table}")
            logger.error(f"Condition: {condition}")
            if self.connection and self.connection.is_connected():
                self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def log_activity(self, user_id, activity_type, ip_address, resource=None, details=None, user_agent=None, session_id=None):
        """Log user activity"""
        data = {
            "user_id": user_id,
            "activity_type": activity_type,
            "ip_address": ip_address,
            "resource_accessed": resource,
            "action_details": details,
            "user_agent": user_agent,
            "session_id": session_id
        }
        
        return self.insert("user_activities", data)

    def log_honeytoken_access(self, token_id, user_id, ip_address, user_agent=None, method=None, context=None, is_authorized=False):
        """Log access to a honeytoken"""
        data = {
            "token_id": token_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "access_method": method,
            "additional_context": context,
            "is_authorized": is_authorized
        }
        
        access_id = self.insert("honeytoken_access", data)
        
        # If access was logged successfully, generate an alert
        if access_id and not is_authorized:
            from ..models.alert import Alert
            Alert.create_honeytoken_access_alert(token_id, user_id, access_id, ip_address)
            
        return access_id

    def create_forensic_log(self, access_id, log_type, source, log_data, alert_id=None):
        """Create a forensic log entry"""
        import hashlib
        
        # Generate hash of log data for integrity
        hash_value = hashlib.sha256(str(log_data).encode()).hexdigest()
        
        data = {
            "access_id": access_id,
            "alert_id": alert_id,
            "log_type": log_type,
            "source": source,
            "log_data": log_data,
            "hash_value": hash_value
        }
        
        return self.insert("forensic_logs", data)

    def audit_action(self, user_id, action, entity_type, entity_id, old_value=None, new_value=None, ip_address=None):
        """Audit an action performed in the system"""
        data = {
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_value": old_value,
            "new_value": new_value,
            "ip_address": ip_address
        }
        
        return self.insert("audit_trail", data)

# Singleton instance of the database
_db_instance = None

def get_db():
    """Get the database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    elif not _db_instance.connection or not _db_instance.connection.is_connected():
        # If connection is lost, reconnect
        _db_instance.connect()
    return _db_instance 