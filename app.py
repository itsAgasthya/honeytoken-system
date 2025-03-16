from flask import Flask, jsonify, render_template, request, Response
import mysql.connector
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from functools import wraps
import hashlib
import secrets
from mysql.connector import Error
import html
import json
import logging
from logging.handlers import SocketHandler
from elasticsearch import Elasticsearch

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Configure logging
elk_logger = logging.getLogger('elk_logger')
elk_logger.setLevel(logging.INFO)
socket_handler = SocketHandler('localhost', 5000)
socket_handler.setFormatter(logging.Formatter('%(message)s'))
elk_logger.addHandler(socket_handler)

# Initialize Elasticsearch client
es = Elasticsearch(['http://localhost:9200'])

# Security Headers
@app.after_request
def add_security_headers(response):
    """Add security headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; img-src 'self' data:;"
    return response

def requires_auth(f):
    """Basic authentication decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def check_auth(username, password):
    """Check if username/password combination is valid."""
    expected_username = os.getenv('ADMIN_USERNAME', 'admin')
    expected_password = os.getenv('ADMIN_PASSWORD', 'change_me_in_production')
    
    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(username, expected_username) and \
           secrets.compare_digest(
               hashlib.sha256(password.encode()).hexdigest(),
               hashlib.sha256(expected_password.encode()).hexdigest()
           )

def authenticate():
    """Send 401 response that enables basic auth."""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def get_db_connection():
    """Create a database connection."""
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            use_pure=True  # Use pure Python implementation
        )
    except Error as e:
        app.logger.error(f"Database connection error: {e}")
        raise

def execute_safe_query(cursor, query, params=None):
    """Execute a query with parameters safely."""
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except Error as e:
        app.logger.error(f"Database query error: {e}")
        raise

def log_access_attempt(token_id, user_id, ip_address, access_type, user_agent=None, query_text=None):
    """Log an access attempt to a honeytoken."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
        INSERT INTO honeytoken_access_logs (
            token_id, access_time, user_id, ip_address, access_type, 
            user_agent, query_text
        ) VALUES (%s, NOW(), %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (token_id, user_id, ip_address, access_type, user_agent, query_text))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def log_to_elk(log_type, data):
    """Send log data to ELK Stack"""
    log_entry = {
        'type': log_type,
        **data,
        'timestamp': datetime.utcnow().isoformat()
    }
    elk_logger.info(json.dumps(log_entry))
    
    # Also store directly in Elasticsearch for immediate access
    if log_type == 'honeytoken_access':
        es.index(index=f'honeytoken-access-{datetime.utcnow():%Y.%m.%d}', body=data)
    elif log_type == 'alert':
        es.index(index=f'honeytoken-alerts-{datetime.utcnow():%Y.%m.%d}', body=data)

@app.route('/')
@requires_auth
def index():
    """Render the dashboard page."""
    return render_template('index.html')

@app.route('/stats')
@requires_auth
def stats():
    """Get basic statistics about honeytoken access."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Use parameterized queries
        total_tokens = execute_safe_query(
            cursor,
            "SELECT COUNT(*) as count FROM honeytokens",
        )[0]['count']
        
        active_tokens = execute_safe_query(
            cursor,
            "SELECT COUNT(*) as count FROM honeytokens WHERE is_active = %s",
            (True,)
        )[0]['count']
        
        total_access = execute_safe_query(
            cursor,
            "SELECT COUNT(*) as count FROM honeytoken_access_logs"
        )[0]['count']
        
        return jsonify({
            'total_tokens': total_tokens,
            'active_tokens': active_tokens,
            'total_access': total_access
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/access-logs', methods=['GET'])
@requires_auth
def get_access_logs():
    try:
        # Query Elasticsearch for access logs
        result = es.search(
            index="honeytoken-access-*",
            body={
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": 100
            }
        )
        return jsonify([hit['_source'] for hit in result['hits']['hits']])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/access-patterns', methods=['GET'])
@requires_auth
def get_access_patterns():
    try:
        # Complex Elasticsearch aggregation for access patterns
        result = es.search(
            index="honeytoken-access-*",
            body={
                "size": 0,
                "aggs": {
                    "access_over_time": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": "hour"
                        }
                    },
                    "top_tokens": {
                        "terms": {
                            "field": "token_type.keyword",
                            "size": 10
                        }
                    },
                    "top_ips": {
                        "terms": {
                            "field": "ip_address.keyword",
                            "size": 10
                        }
                    },
                    "access_by_user": {
                        "terms": {
                            "field": "user_id.keyword",
                            "size": 10
                        }
                    }
                }
            }
        )
        return jsonify(result['aggregations'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get current alerts."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
        SELECT 
            a.id as alert_id,
            h.token_type,
            h.description,
            COUNT(l.id) as access_count,
            a.alert_threshold,
            a.alert_channels,
            MAX(l.access_time) as last_access
        FROM alert_configs a
        JOIN honeytokens h ON a.token_id = h.id
        JOIN honeytoken_access_logs l ON h.id = l.token_id
        WHERE a.is_active = 1
        GROUP BY a.id, h.token_type, h.description, a.alert_threshold, a.alert_channels
        HAVING COUNT(l.id) >= a.alert_threshold
        """
        cursor.execute(query)
        alerts = cursor.fetchall()
        return jsonify(alerts)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/alerts/check', methods=['POST'])
def check_alerts():
    """Check for new alerts and trigger notifications."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get active alerts that have exceeded their threshold
        query = """
        SELECT 
            a.id as alert_id,
            h.token_type,
            h.description,
            COUNT(l.id) as access_count,
            a.alert_threshold,
            a.alert_channels
        FROM alert_configs a
        JOIN honeytokens h ON a.token_id = h.id
        JOIN honeytoken_access_logs l ON h.id = l.token_id
        WHERE a.is_active = 1
        AND l.access_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        GROUP BY a.id, h.token_type, h.description, a.alert_threshold, a.alert_channels
        HAVING COUNT(l.id) >= a.alert_threshold
        """
        cursor.execute(query)
        alerts = cursor.fetchall()
        
        # Insert alerts into history
        if alerts:
            for alert in alerts:
                insert_query = """
                INSERT INTO alert_history (
                    alert_config_id, 
                    trigger_time,
                    access_count,
                    notification_sent
                ) VALUES (%s, NOW(), %s, 1)
                """
                cursor.execute(insert_query, (alert['alert_id'], alert['access_count']))
            conn.commit()
        
        return jsonify({
            'alerts_triggered': len(alerts),
            'alerts': alerts
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/alerts/history', methods=['GET'])
@requires_auth
def get_alert_history():
    try:
        # Query Elasticsearch for alerts
        result = es.search(
            index="honeytoken-alerts-*",
            body={
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": 100
            }
        )
        return jsonify([hit['_source'] for hit in result['hits']['hits']])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/employee-portal')
def employee_portal():
    """Render the employee portal page."""
    return render_template('employee_portal.html')

@app.route('/api/employee/<emp_id>', methods=['GET'])
def get_employee_details(emp_id):
    log_data = {
        'access_time': datetime.utcnow().isoformat(),
        'access_type': 'read',
        'ip_address': request.remote_addr,
        'user_id': request.authorization.username if request.authorization else 'unknown',
        'user_agent': request.headers.get('User-Agent'),
        'resource_type': 'employee',
        'resource_id': emp_id,
        'query_text': f'Attempted to access employee ID: {emp_id}'
    }
    log_to_elk('honeytoken_access', log_data)
    return jsonify({"error": "Access denied"}), 401

@app.route('/api/payroll/access', methods=['POST'])
def access_payroll():
    """Endpoint for accessing payroll data (honeytoken)."""
    user_id = request.authorization.username if request.authorization else 'unknown'
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    # This is a honeytoken - log the access
    log_access_attempt(
        token_id=2,  # ID of the payroll data honeytoken
        user_id=user_id,
        ip_address=ip,
        access_type='read',
        user_agent=user_agent,
        query_text="Attempted to access payroll data"
    )
    
    return jsonify({'error': 'Access denied'}), 401

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Endpoint for admin login attempts (honeytoken)."""
    data = request.get_json()
    user_id = data.get('username', 'unknown')
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    # This is a honeytoken - log the access
    log_access_attempt(
        token_id=3,  # ID of the admin credentials honeytoken
        user_id=user_id,
        ip_address=ip,
        access_type='execute',
        user_agent=user_agent,
        query_text=f"Admin login attempt with username: {user_id}"
    )
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/system/db-credentials')
def get_db_credentials():
    """Endpoint for accessing database credentials (honeytoken)."""
    user_id = request.authorization.username if request.authorization else 'unknown'
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    # This is a honeytoken - log the access
    log_access_attempt(
        token_id=4,  # ID of the system config honeytoken
        user_id=user_id,
        ip_address=ip,
        access_type='read',
        user_agent=user_agent,
        query_text="Attempted to access database credentials"
    )
    
    return jsonify({'error': 'Access denied'}), 401

# Add Kibana dashboard configuration endpoint
@app.route('/api/kibana/config', methods=['GET'])
@requires_auth
def get_kibana_config():
    return jsonify({
        "dashboards": [
            {
                "title": "Honeytoken Access Overview",
                "url": "http://localhost:5601/app/dashboards#/view/honeytoken-access-overview"
            },
            {
                "title": "Alert Analysis",
                "url": "http://localhost:5601/app/dashboards#/view/honeytoken-alert-analysis"
            },
            {
                "title": "User Behavior Analytics",
                "url": "http://localhost:5601/app/dashboards#/view/user-behavior-analytics"
            }
        ]
    })

if __name__ == '__main__':
    # Only enable debug mode in development
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Force HTTPS in production
    if os.getenv('FLASK_ENV') == 'production':
        from flask_talisman import Talisman
        Talisman(app, force_https=True)
    
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,
        debug=debug
    ) 