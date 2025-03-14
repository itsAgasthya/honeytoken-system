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

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

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
    """Create a secure database connection."""
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            ssl_ca=os.getenv('DB_SSL_CA'),  # SSL certificate for secure connection
            ssl_verify_cert=True,
            use_pure=True  # Use pure Python implementation for better security
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

@app.route('/api/access-logs')
def get_access_logs():
    """Get honeytoken access logs."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
        SELECT l.*, h.token_type 
        FROM honeytoken_access_logs l
        JOIN honeytokens h ON l.token_id = h.id
        ORDER BY l.access_time DESC
        LIMIT 100
        """
        cursor.execute(query)
        logs = cursor.fetchall()
        
        # Convert datetime objects to string
        for log in logs:
            log['access_time'] = log['access_time'].isoformat()
            log['created_at'] = log['created_at'].isoformat()
            log['updated_at'] = log['updated_at'].isoformat()
        
        return jsonify(logs)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/analytics/access-patterns')
def get_access_patterns():
    """Get analytics about honeytoken access patterns."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get token stats
        token_query = """
        SELECT 
            h.id as token_id,
            h.token_type,
            COUNT(l.id) as access_count,
            COUNT(DISTINCT l.user_id) as unique_users,
            COUNT(DISTINCT l.ip_address) as unique_ips
        FROM honeytokens h
        LEFT JOIN honeytoken_access_logs l ON h.id = l.token_id
        GROUP BY h.id
        """
        cursor.execute(token_query)
        token_stats = cursor.fetchall()
        
        # Get daily stats
        daily_query = """
        SELECT 
            DATE(access_time) as date,
            COUNT(*) as access_count
        FROM honeytoken_access_logs
        WHERE access_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(access_time)
        ORDER BY date
        """
        cursor.execute(daily_query)
        daily_stats = cursor.fetchall()
        
        # Convert date objects to string
        for stat in daily_stats:
            stat['date'] = stat['date'].isoformat()
        
        return jsonify({
            'token_stats': token_stats,
            'daily_stats': daily_stats
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/alerts/check', methods=['POST'])
def check_alerts():
    """Check for alert conditions and return triggered alerts."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get active tokens with recent access
        query = """
        SELECT 
            h.id as token_id,
            h.token_type,
            COUNT(l.id) as access_count,
            ac.alert_threshold,
            ac.alert_channels
        FROM honeytokens h
        JOIN alert_configs ac ON h.id = ac.token_id
        JOIN honeytoken_access_logs l ON h.id = l.token_id
        WHERE h.is_active = 1
        AND l.access_time >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
        GROUP BY h.id
        HAVING COUNT(l.id) >= ac.alert_threshold
        """
        cursor.execute(query)
        alerts = cursor.fetchall()
        
        return jsonify({
            'alerts': alerts,
            'timestamp': datetime.utcnow().isoformat()
        })
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    # Only enable debug mode in development
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Force HTTPS in production
    if os.getenv('FLASK_ENV') == 'production':
        from flask_talisman import Talisman
        Talisman(app, force_https=True)
    
    app.run(
        host='127.0.0.1',  # Only listen on localhost
        port=int(os.getenv('PORT', 5000)),
        debug=debug
    ) 