from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for
import logging
import json
import os
import io
import time
from datetime import datetime, timedelta
from functools import wraps
from ..db.database import get_db
from ..models.honeytoken import Honeytoken, create_honeytoken, FileHoneytoken, DatabaseHoneytoken, APIKeyHoneytoken, CredentialsHoneytoken
from ..models.ueba import get_ueba_engine
from ..models.alert import Alert, get_alert_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('api')

# Create Flask app
app = Flask(__name__, 
            static_folder='../web/static',
            template_folder='../web/templates')

# Simple API key authentication
API_KEY = "honeytoken_api_key_123"  # This should be securely stored in a real application

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key', '')
        if api_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Log requests middleware
@app.before_request
def log_request():
    # Don't log static file requests
    if not request.path.startswith('/static/'):
        logger.info(f"Request: {request.method} {request.path} - IP: {request.remote_addr}")

# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    logger.error(f"Error: {str(e)}")
    return jsonify({"error": str(e)}), 500

# Root redirect to dashboard
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

# Dashboard - Web UI
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Honeytoken management - Web UI
@app.route('/honeytokens')
def honeytokens_ui():
    return render_template('honeytokens.html')

# Alerts - Web UI
@app.route('/alerts')
def alerts_ui():
    return render_template('alerts.html')

# User management - Web UI
@app.route('/users')
def users_ui():
    return render_template('users.html')

# UEBA Analysis - Web UI
@app.route('/ueba')
def ueba_ui():
    return render_template('ueba.html')

# Settings - Web UI
@app.route('/settings')
def settings_ui():
    return render_template('settings.html')

#
# API Endpoints
#

# Honeytokens API

@app.route('/api/ping', methods=['GET'])
def ping():
    """Simple endpoint for connection testing"""
    logger.info(f"Ping request received - IP: {request.remote_addr}")
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/api/honeytokens', methods=['GET'])
@require_api_key
def get_honeytokens():
    try:
        logger.info(f"Request: GET /api/honeytokens - IP: {request.remote_addr}")
        
        db = get_db()
        honeytokens = db.fetch_all("""
            SELECT 
                token_id as id, token_name as name, token_type as type, description, 
                token_location as location, is_active, created_at
            FROM honeytokens
            ORDER BY created_at DESC
        """)
        
        return jsonify(honeytokens)
    except Exception as e:
        logger.error(f"Error in get_honeytokens: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/honeytokens/<int:token_id>', methods=['GET'])
@require_api_key
def get_honeytoken(token_id):
    """Get a specific honeytoken"""
    token = Honeytoken.get_by_id(token_id)
    
    if not token:
        return jsonify({"error": f"Honeytoken with ID {token_id} not found"}), 404
        
    result = {
        'token_id': token.token_id,
        'name': token.name,
        'token_type': token.token_type,
        'value': token.value,
        'location': token.location,
        'description': token.description,
        'sensitivity': token.sensitivity,
        'created_at': token.created_at.isoformat() if hasattr(token.created_at, 'isoformat') else token.created_at,
        'is_active': token.is_active
    }
    
    return jsonify(result)

@app.route('/api/honeytokens', methods=['POST'])
@require_api_key
def create_honeytoken_api():
    """Create a new honeytoken"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    required_fields = ['token_type']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
            
    try:
        token = create_honeytoken(
            token_type=data['token_type'],
            name=data.get('name'),
            description=data.get('description'),
            sensitivity=data.get('sensitivity', 'medium')
        )
        
        # For specific token types, set additional properties
        if data['token_type'] == 'file':
            token.file_path = data.get('file_path')
            token.content = data.get('content')
            
        elif data['token_type'] == 'database':
            token.table_name = data.get('table_name')
            token.record_data = data.get('record_data')
            
        elif data['token_type'] == 'api_key':
            token.service_name = data.get('service_name')
            token.key_prefix = data.get('key_prefix')
            
        elif data['token_type'] == 'credentials':
            token.username = data.get('username')
            token.service = data.get('service')
            
        # Deploy the honeytoken
        token.deploy()
        
        return jsonify({
            "message": "Honeytoken created successfully",
            "token_id": token.token_id,
            "token_value": token.value
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating honeytoken: {str(e)}")
        return jsonify({"error": f"Error creating honeytoken: {str(e)}"}), 500

@app.route('/api/honeytokens/<int:token_id>', methods=['PUT'])
@require_api_key
def update_honeytoken(token_id):
    """Update a honeytoken"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    token = Honeytoken.get_by_id(token_id)
    
    if not token:
        return jsonify({"error": f"Honeytoken with ID {token_id} not found"}), 404
        
    # Update fields
    if 'name' in data:
        token.name = data['name']
    if 'description' in data:
        token.description = data['description']
    if 'sensitivity' in data:
        token.sensitivity = data['sensitivity']
    if 'is_active' in data:
        token.is_active = data['is_active']
        
    # Save changes
    token.update()
    
    return jsonify({"message": "Honeytoken updated successfully"})

@app.route('/api/honeytokens/<int:token_id>', methods=['DELETE'])
@require_api_key
def delete_honeytoken(token_id):
    """Delete a honeytoken"""
    token = Honeytoken.get_by_id(token_id)
    
    if not token:
        return jsonify({"error": f"Honeytoken with ID {token_id} not found"}), 404
        
    # Deactivate instead of deleting to preserve audit trail
    token.deactivate()
    
    return jsonify({"message": "Honeytoken deactivated successfully"})

@app.route('/api/honeytokens/<int:token_id>/access', methods=['POST'])
@require_api_key
def log_honeytoken_access(token_id):
    """Log access to a honeytoken (for testing)"""
    data = request.get_json() or {}
    
    user_id = data.get('user_id')
    ip_address = data.get('ip_address', request.remote_addr)
    user_agent = data.get('user_agent', request.headers.get('User-Agent'))
    method = data.get('method', 'api')
    context = data.get('context')
    is_authorized = data.get('is_authorized', False)
    
    access_id = Honeytoken.log_access(
        token_id=token_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        method=method,
        context=context,
        is_authorized=is_authorized
    )
    
    if not access_id:
        return jsonify({"error": "Failed to log access"}), 500
        
    return jsonify({
        "message": "Access logged successfully",
        "access_id": access_id
    })

# Alerts API

@app.route('/api/alerts', methods=['GET'])
@require_api_key
def get_alerts():
    """Get alerts with optional filtering"""
    resolved = request.args.get('resolved')
    if resolved is not None:
        resolved = resolved.lower() == 'true'
        
    severity = request.args.get('severity')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    alerts = Alert.get_all(
        resolved=resolved,
        severity=severity,
        limit=limit,
        offset=offset
    )
    
    # Convert to JSON serializable format
    result = []
    for alert in alerts:
        result.append({
            'alert_id': alert.alert_id,
            'token_id': alert.token_id,
            'user_id': alert.user_id,
            'access_id': alert.access_id,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'timestamp': alert.timestamp.isoformat() if hasattr(alert.timestamp, 'isoformat') else alert.timestamp,
            'description': alert.description,
            'is_resolved': alert.is_resolved,
            'resolved_by': alert.resolved_by,
            'resolution_notes': alert.resolution_notes
        })
    
    return jsonify(result)

@app.route('/api/alerts/recent', methods=['GET'])
@require_api_key
def get_recent_alerts():
    """Get recent alerts"""
    try:
        logger.info(f"Request: GET /api/alerts/recent - IP: {request.remote_addr}")
        
        hours = request.args.get('hours', 24, type=int)
        from_time = datetime.now() - timedelta(hours=hours)
        
        db = get_db()
        recent_alerts = db.fetch_all("""
            SELECT 
                a.alert_id as id, a.description as title, a.description, a.severity, 
                a.timestamp, a.is_resolved as status, a.user_id, u.username
            FROM alerts a
            LEFT JOIN users u ON a.user_id = u.user_id
            WHERE a.timestamp > %s
            ORDER BY a.timestamp DESC
            LIMIT 50
        """, (from_time,))
        
        for alert in recent_alerts:
            # Format timestamp for display
            if 'timestamp' in alert and alert['timestamp']:
                alert['timestamp'] = alert['timestamp'].isoformat()
        
        return jsonify(recent_alerts)
    except Exception as e:
        logger.error(f"Error in get_recent_alerts: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/alerts/summary', methods=['GET'])
@require_api_key
def get_alert_summary():
    """Get summary of alerts by severity"""
    try:
        logger.info(f"Request: GET /api/alerts/summary - IP: {request.remote_addr}")
        
        # Get alerts from the past week by default
        days = request.args.get('days', 7, type=int)
        from_date = datetime.now() - timedelta(days=days)
        
        db = get_db()
        summary = db.fetch_all("""
            SELECT severity, COUNT(*) as count 
            FROM alerts 
            WHERE timestamp > %s 
            GROUP BY severity
        """, (from_date,))
        
        # Transform to a more usable format
        result = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for item in summary:
            result[item['severity']] = item['count']
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_alert_summary: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['GET'])
@require_api_key
def get_alert(alert_id):
    """Get a specific alert"""
    alert = Alert.get_by_id(alert_id)
    
    if not alert or not alert.alert_id:
        return jsonify({"error": f"Alert with ID {alert_id} not found"}), 404
        
    result = {
        'alert_id': alert.alert_id,
        'token_id': alert.token_id,
        'user_id': alert.user_id,
        'access_id': alert.access_id,
        'alert_type': alert.alert_type,
        'severity': alert.severity,
        'timestamp': alert.timestamp.isoformat() if hasattr(alert.timestamp, 'isoformat') else alert.timestamp,
        'description': alert.description,
        'is_resolved': alert.is_resolved,
        'resolved_by': alert.resolved_by,
        'resolution_notes': alert.resolution_notes
    }
    
    return jsonify(result)

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
@require_api_key
def resolve_alert(alert_id):
    """Resolve an alert"""
    data = request.get_json() or {}
    
    user_id = data.get('user_id', 1)  # Default to admin user
    notes = data.get('notes', '')
    
    alert = Alert.get_by_id(alert_id)
    
    if not alert or not alert.alert_id:
        return jsonify({"error": f"Alert with ID {alert_id} not found"}), 404
        
    alert.resolve(user_id, notes)
    
    return jsonify({"message": "Alert resolved successfully"})

@app.route('/api/alerts/<int:alert_id>/evidence', methods=['GET'])
@require_api_key
def get_alert_evidence(alert_id):
    """Get forensic evidence for an alert"""
    alert = Alert.get_by_id(alert_id)
    
    if not alert or not alert.alert_id:
        return jsonify({"error": f"Alert with ID {alert_id} not found"}), 404
        
    # Collect evidence if not already collected
    if not alert.forensic_evidence:
        evidence = alert.collect_forensic_evidence()
    else:
        try:
            evidence = json.loads(alert.forensic_evidence)
        except:
            evidence = {"raw": alert.forensic_evidence}
    
    return jsonify(evidence)

@app.route('/api/alerts/<int:alert_id>/export', methods=['GET'])
@require_api_key
def export_alert(alert_id):
    """Export alert data for investigation"""
    alert_manager = get_alert_manager()
    export_data = alert_manager.export_alert_data(alert_id)
    
    if not export_data:
        return jsonify({"error": f"Alert with ID {alert_id} not found or cannot be exported"}), 404
        
    # Format for download as JSON file
    export_json = json.dumps(export_data, indent=2)
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f"alert-{alert_id}-export-{timestamp}.json"
    
    return send_file(
        io.BytesIO(export_json.encode()),
        mimetype='application/json',
        as_attachment=True,
        attachment_filename=filename
    )

# Users API

@app.route('/api/users', methods=['GET'])
@require_api_key
def get_users():
    """Get all users"""
    try:
        logger.info(f"Request: GET /api/users - IP: {request.remote_addr}")
        
        db = get_db()
        users = db.fetch_all("""
            SELECT user_id, username, email, department, role, created_at, last_login, is_active 
            FROM users
        """)
        
        return jsonify(users)
    except Exception as e:
        logger.error(f"Error in get_users: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
@require_api_key
def get_user(user_id):
    """Get a specific user"""
    db = get_db()
    query = "SELECT user_id, username, email, department, role, created_at, last_login, is_active FROM users WHERE user_id = %s"
    user = db.fetch_one(query, (user_id,))
    
    if not user:
        return jsonify({"error": f"User with ID {user_id} not found"}), 404
        
    # Convert datetime objects to strings
    for key, value in user.items():
        if isinstance(value, datetime):
            user[key] = value.isoformat()
    
    return jsonify(user)

@app.route('/api/users/<int:user_id>/risk', methods=['GET'])
@require_api_key
def get_user_risk(user_id):
    """Get risk score for a user"""
    ueba_engine = get_ueba_engine()
    risk_info = ueba_engine.get_user_risk_score(user_id)
    
    return jsonify(risk_info)

@app.route('/api/users/risky', methods=['GET'])
@require_api_key
def get_risky_users():
    """Get users with high risk scores"""
    try:
        logger.info(f"Request: GET /api/users/risky - IP: {request.remote_addr}")
        
        db = get_db()
        risky_users = db.fetch_all("""
            SELECT u.user_id, u.username, u.department, u.role, 
                   MAX(a.severity) as highest_severity,
                   COUNT(a.alert_id) as alert_count
            FROM users u
            JOIN alerts a ON u.user_id = a.user_id
            WHERE a.is_resolved = FALSE
            GROUP BY u.user_id, u.username, u.department, u.role
            ORDER BY 
                CASE 
                    WHEN MAX(a.severity) = 'critical' THEN 1
                    WHEN MAX(a.severity) = 'high' THEN 2
                    WHEN MAX(a.severity) = 'medium' THEN 3
                    ELSE 4
                END, 
                COUNT(a.alert_id) DESC
            LIMIT 5
        """)
        
        return jsonify(risky_users)
    except Exception as e:
        logger.error(f"Error in get_risky_users: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/stats', methods=['GET'])
@require_api_key
def get_user_stats():
    """Get user statistics for the dashboard"""
    try:
        logger.info(f"Request: GET /api/users/stats - IP: {request.remote_addr}")
        
        db = get_db()
        
        # Get total users count
        total_users = db.fetch_one("SELECT COUNT(*) as count FROM users")
        
        # Get active users (active in last 7 days)
        active_users = db.fetch_one("""
            SELECT COUNT(DISTINCT user_id) as count 
            FROM user_activities 
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        # Get admin users count
        admin_users = db.fetch_one("""
            SELECT COUNT(*) as count 
            FROM users 
            WHERE role = 'admin'
        """)
        
        # Get users with open alerts
        risky_users = db.fetch_one("""
            SELECT COUNT(DISTINCT user_id) as count 
            FROM alerts 
            WHERE is_resolved = FALSE
        """)
        
        return jsonify({
            'total': total_users.get('count', 0),
            'active': active_users.get('count', 0),
            'admin': admin_users.get('count', 0),
            'risky': risky_users.get('count', 0)
        })
    except Exception as e:
        logger.error(f"Error in get_user_stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# UEBA API

@app.route('/api/ueba/activity', methods=['POST'])
@require_api_key
def log_user_activity():
    """Log a user activity for UEBA analysis"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    required_fields = ['user_id', 'activity_type']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
            
    ueba_engine = get_ueba_engine()
    
    result = ueba_engine.process_activity(
        user_id=data['user_id'],
        activity_type=data['activity_type'],
        ip_address=data.get('ip_address', request.remote_addr),
        resource=data.get('resource'),
        details=data.get('details'),
        user_agent=data.get('user_agent', request.headers.get('User-Agent')),
        session_id=data.get('session_id')
    )
    
    if not result:
        return jsonify({"error": "Failed to process activity"}), 500
        
    return jsonify({
        "message": "Activity processed successfully",
        "activity_id": result['activity_id'],
        "anomaly_score": result['analysis']['overall_score']
    })

@app.route('/api/ueba/activities/<int:user_id>', methods=['GET'])
@require_api_key
def get_user_activities(user_id):
    """Get recent activities for a user"""
    db = get_db()
    days = int(request.args.get('days', 30))
    limit = int(request.args.get('limit', 100))
    
    query = """
    SELECT * FROM user_activities
    WHERE user_id = %s AND timestamp > DATE_SUB(NOW(), INTERVAL %s DAY)
    ORDER BY timestamp DESC
    LIMIT %s
    """
    
    activities = db.fetch_all(query, (user_id, days, limit))
    
    # Convert datetime objects to strings
    for activity in activities:
        for key, value in activity.items():
            if isinstance(value, datetime):
                activity[key] = value.isoformat()
    
    return jsonify(activities)

# Utility functions for the API

def init_logs_dir():
    """Ensure logs directory exists"""
    os.makedirs('logs', exist_ok=True)

def run_api(host='0.0.0.0', port=5000, debug=True):
    """Run the API server"""
    init_logs_dir()
    app.run(host=host, port=port, debug=debug)

@app.route('/api/activities', methods=['GET'])
@require_api_key
def get_activities():
    """Get activities for all users in the specified time range"""
    try:
        logger.info(f"Request: GET /api/activities - IP: {request.remote_addr}")
        
        hours = request.args.get('hours', 240000, type=int)  # Use a large default value to get all activities
        limit = request.args.get('limit', 500, type=int)     # Increase default limit to 500
        db = get_db()
        
        # Update query to use resource_accessed instead of resource and action_details instead of details
        activities = db.fetch_all("""
            SELECT ua.activity_id as id, ua.user_id, u.username, ua.activity_type, 
                   ua.resource_accessed as resource, ua.ip_address, ua.timestamp, 
                   COALESCE(anoms.anomaly_score, 0) as anomaly_score,
                   ua.action_details as details
            FROM user_activities ua
            LEFT JOIN users u ON ua.user_id = u.user_id
            LEFT JOIN (
                SELECT activity_id, AVG(anomaly_score) as anomaly_score
                FROM anomaly_scores
                GROUP BY activity_id
            ) anoms ON ua.activity_id = anoms.activity_id
            WHERE ua.timestamp > DATE_SUB(NOW(), INTERVAL %s HOUR)
            ORDER BY ua.timestamp DESC
            LIMIT %s
        """, (hours, limit))
        
        # Convert datetime objects to strings
        for activity in activities:
            for key, value in activity.items():
                if isinstance(value, datetime):
                    activity[key] = value.isoformat()
                elif key == 'details' and value is not None:
                    # Parse JSON string to dict if it's a string
                    if isinstance(value, str):
                        try:
                            activity[key] = json.loads(value)
                        except:
                            pass
        
        return jsonify(activities)
    except Exception as e:
        logger.error(f"Error in get_activities: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/activities/stats', methods=['GET'])
@require_api_key
def get_activity_stats():
    """Get activity statistics for the specified time range"""
    try:
        logger.info(f"Request: GET /api/activities/stats - IP: {request.remote_addr}")
        
        hours = request.args.get('hours', 24, type=int)
        db = get_db()
        
        # Get total activities
        total_activities = db.fetch_one("""
            SELECT COUNT(*) as count
            FROM user_activities
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL %s HOUR)
        """, (hours,))
        
        # Get anomalous activities (score > 0.5)
        anomalous_activities = db.fetch_one("""
            SELECT COUNT(*) as count
            FROM user_activities ua
            JOIN anomaly_scores ans ON ua.activity_id = ans.activity_id
            WHERE ua.timestamp > DATE_SUB(NOW(), INTERVAL %s HOUR)
            AND ans.anomaly_score > 0.5
        """, (hours,))
        
        # Get average anomaly score
        avg_score = db.fetch_one("""
            SELECT AVG(ans.anomaly_score) as avg_score
            FROM user_activities ua
            JOIN anomaly_scores ans ON ua.activity_id = ans.activity_id
            WHERE ua.timestamp > DATE_SUB(NOW(), INTERVAL %s HOUR)
        """, (hours,))
        
        total = total_activities.get('count', 0)
        anomalous = anomalous_activities.get('count', 0)
        
        return jsonify({
            'total_activities': total,
            'anomalous_activities': anomalous,
            'anomaly_rate': anomalous / total if total > 0 else 0,
            'avg_anomaly_score': avg_score.get('avg_score', 0) or 0
        })
    except Exception as e:
        logger.error(f"Error in get_activity_stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/anomalies/distribution', methods=['GET'])
@require_api_key
def get_anomaly_distribution():
    """Get the distribution of anomaly scores"""
    try:
        logger.info(f"Request: GET /api/anomalies/distribution - IP: {request.remote_addr}")
        
        hours = request.args.get('hours', 24, type=int)
        db = get_db()
        
        # Get anomaly score distribution
        scores = db.fetch_all("""
            SELECT ROUND(anomaly_score, 1) as score_range, COUNT(*) as count
            FROM user_activities ua
            JOIN anomaly_scores ans ON ua.activity_id = ans.activity_id
            WHERE ua.timestamp > DATE_SUB(NOW(), INTERVAL %s HOUR)
            GROUP BY ROUND(anomaly_score, 1)
            ORDER BY ROUND(anomaly_score, 1)
        """, (hours,))
        
        # Convert to dictionary with score range as key
        distribution = {}
        for item in scores:
            distribution[str(item['score_range'])] = item['count']
        
        return jsonify(distribution)
    except Exception as e:
        logger.error(f"Error in get_anomaly_distribution: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    run_api() 