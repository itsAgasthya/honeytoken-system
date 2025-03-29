import logging
import json
import hashlib
import time
from datetime import datetime, timedelta
from ..db.database import get_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/alert.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('alert')

class Alert:
    """Model for handling alerts and forensic evidence collection"""
    
    def __init__(self, alert_id=None):
        self.db = get_db()
        self.alert_id = alert_id
        self.token_id = None
        self.user_id = None
        self.access_id = None
        self.alert_type = None
        self.severity = None
        self.timestamp = None
        self.description = None
        self.is_resolved = False
        self.resolved_by = None
        self.resolution_notes = None
        self.forensic_evidence = None
        
        if alert_id:
            self._load_alert()
            
    def _load_alert(self):
        """Load alert data from database"""
        query = "SELECT * FROM alerts WHERE alert_id = %s"
        result = self.db.fetch_one(query, (self.alert_id,))
        
        if result:
            self.token_id = result['token_id']
            self.user_id = result['user_id']
            self.access_id = result['access_id']
            self.alert_type = result['alert_type']
            self.severity = result['severity']
            self.timestamp = result['timestamp']
            self.description = result['description']
            self.is_resolved = result['is_resolved']
            self.resolved_by = result['resolved_by']
            self.resolution_notes = result['resolution_notes']
            self.forensic_evidence = result['forensic_evidence']
            
    def save(self):
        """Save or update alert in database"""
        data = {
            'token_id': self.token_id,
            'user_id': self.user_id,
            'access_id': self.access_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'description': self.description
        }
        
        if self.alert_id:
            # Update existing alert
            data['is_resolved'] = self.is_resolved
            data['resolved_by'] = self.resolved_by
            data['resolution_notes'] = self.resolution_notes
            data['forensic_evidence'] = self.forensic_evidence
            
            condition = {'alert_id': self.alert_id}
            self.db.update('alerts', data, condition)
            logger.info(f"Updated alert {self.alert_id}")
        else:
            # Create new alert
            self.alert_id = self.db.insert('alerts', data)
            logger.info(f"Created new alert {self.alert_id}")
            
        return self.alert_id
        
    def resolve(self, user_id, notes=None):
        """Mark an alert as resolved"""
        self.is_resolved = True
        self.resolved_by = user_id
        self.resolution_notes = notes
        
        data = {
            'is_resolved': True,
            'resolved_by': user_id,
            'resolution_notes': notes
        }
        
        condition = {'alert_id': self.alert_id}
        self.db.update('alerts', data, condition)
        
        # Log the resolution
        self.db.audit_action(
            user_id=user_id,
            action='resolve_alert',
            entity_type='alert',
            entity_id=self.alert_id,
            new_value=f"Resolved by user {user_id}: {notes}"
        )
        
        logger.info(f"Alert {self.alert_id} resolved by user {user_id}")
        return True
        
    def collect_forensic_evidence(self):
        """Collect detailed forensic evidence for this alert"""
        evidence = {}
        
        # If this is a honeytoken access alert, gather access details
        if self.alert_type == 'access' and self.access_id:
            # Get access details
            query = """
            SELECT ha.*, h.token_name, h.token_type, h.token_value, h.token_location, 
                   u.username, u.email, u.department, u.role
            FROM honeytoken_access ha
            JOIN honeytokens h ON ha.token_id = h.token_id
            LEFT JOIN users u ON ha.user_id = u.user_id
            WHERE ha.access_id = %s
            """
            
            access_details = self.db.fetch_one(query, (self.access_id,))
            if access_details:
                evidence['access_details'] = {
                    'access_id': access_details['access_id'],
                    'token_id': access_details['token_id'],
                    'token_name': access_details['token_name'],
                    'token_type': access_details['token_type'],
                    'token_location': access_details['token_location'],
                    'access_time': access_details['access_time'].isoformat() if access_details['access_time'] else None,
                    'ip_address': access_details['ip_address'],
                    'user_agent': access_details['user_agent'],
                    'access_method': access_details['access_method'],
                    'is_authorized': access_details['is_authorized'],
                    'username': access_details['username'],
                    'user_department': access_details['department'],
                    'user_role': access_details['role']
                }
                
                # Get related forensic logs
                query = "SELECT * FROM forensic_logs WHERE access_id = %s ORDER BY timestamp"
                forensic_logs = self.db.fetch_all(query, (self.access_id,))
                
                if forensic_logs:
                    evidence['forensic_logs'] = []
                    for log in forensic_logs:
                        evidence['forensic_logs'].append({
                            'log_id': log['log_id'],
                            'log_type': log['log_type'],
                            'timestamp': log['timestamp'].isoformat() if log['timestamp'] else None,
                            'source': log['source'],
                            'log_data': log['log_data'],
                            'hash_value': log['hash_value']
                        })
                        
        # If this is a behavioral alert, gather anomaly details
        elif self.alert_type == 'unusual_behavior' and self.user_id:
            # Get recent anomaly scores for this user
            query = """
            SELECT ans.*, ua.activity_type, ua.resource_accessed, ua.ip_address
            FROM anomaly_scores ans
            JOIN user_activities ua ON ans.activity_id = ua.activity_id
            WHERE ans.user_id = %s AND ans.timestamp > %s
            ORDER BY ans.anomaly_score DESC
            LIMIT 10
            """
            
            one_day_ago = datetime.now() - timedelta(days=1)
            anomalies = self.db.fetch_all(query, (self.user_id, one_day_ago))
            
            if anomalies:
                evidence['anomaly_details'] = []
                for anomaly in anomalies:
                    evidence['anomaly_details'].append({
                        'anomaly_id': anomaly['anomaly_id'],
                        'feature_name': anomaly['feature_name'],
                        'expected_value': anomaly['expected_value'],
                        'actual_value': anomaly['actual_value'],
                        'anomaly_score': anomaly['anomaly_score'],
                        'timestamp': anomaly['timestamp'].isoformat() if anomaly['timestamp'] else None,
                        'activity_type': anomaly['activity_type'],
                        'resource_accessed': anomaly['resource_accessed'],
                        'ip_address': anomaly['ip_address']
                    })
                    
            # Get user activity pattern
            query = """
            SELECT activity_type, COUNT(*) as count, 
                   MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
            FROM user_activities
            WHERE user_id = %s
            GROUP BY activity_type
            ORDER BY count DESC
            """
            
            activity_patterns = self.db.fetch_all(query, (self.user_id,))
            
            if activity_patterns:
                evidence['user_activity_patterns'] = []
                for pattern in activity_patterns:
                    evidence['user_activity_patterns'].append({
                        'activity_type': pattern['activity_type'],
                        'count': pattern['count'],
                        'first_seen': pattern['first_seen'].isoformat() if pattern['first_seen'] else None,
                        'last_seen': pattern['last_seen'].isoformat() if pattern['last_seen'] else None
                    })
                    
        # Add timestamp and hash for evidence integrity
        evidence['collected_at'] = datetime.now().isoformat()
        evidence_json = json.dumps(evidence, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
        evidence['evidence_hash'] = evidence_hash
        
        # Store the evidence
        self.forensic_evidence = json.dumps(evidence, indent=2)
        
        # Update the alert
        data = {'forensic_evidence': self.forensic_evidence}
        condition = {'alert_id': self.alert_id}
        self.db.update('alerts', data, condition)
        
        # Add a forensic log entry for the evidence collection
        if self.access_id:
            self.db.create_forensic_log(
                access_id=self.access_id,
                alert_id=self.alert_id,
                log_type='application',
                source='alert_system',
                log_data=json.dumps({
                    'action': 'evidence_collection',
                    'alert_id': self.alert_id,
                    'timestamp': datetime.now().isoformat(),
                    'evidence_hash': evidence_hash
                })
            )
            
        logger.info(f"Collected forensic evidence for alert {self.alert_id}")
        return evidence
        
    @staticmethod
    def get_by_id(alert_id):
        """Get an alert by ID"""
        return Alert(alert_id)
        
    @staticmethod
    def get_all(resolved=None, severity=None, limit=100, offset=0):
        """Get all alerts with optional filtering"""
        db = get_db()
        
        # Build query
        query = "SELECT * FROM alerts"
        conditions = []
        params = []
        
        if resolved is not None:
            conditions.append("is_resolved = %s")
            params.append(resolved)
            
        if severity:
            conditions.append("severity = %s")
            params.append(severity)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Execute query
        results = db.fetch_all(query, params)
        
        # Convert to Alert objects
        alerts = []
        for result in results:
            alert = Alert()
            alert.alert_id = result['alert_id']
            alert.token_id = result['token_id']
            alert.user_id = result['user_id']
            alert.access_id = result['access_id']
            alert.alert_type = result['alert_type']
            alert.severity = result['severity']
            alert.timestamp = result['timestamp']
            alert.description = result['description']
            alert.is_resolved = result['is_resolved']
            alert.resolved_by = result['resolved_by']
            alert.resolution_notes = result['resolution_notes']
            alert.forensic_evidence = result['forensic_evidence']
            alerts.append(alert)
            
        return alerts
        
    @staticmethod
    def create_honeytoken_access_alert(token_id, user_id, access_id, ip_address):
        """Create an alert for honeytoken access"""
        db = get_db()
        
        # Get token details
        query = "SELECT * FROM honeytokens WHERE token_id = %s"
        token = db.fetch_one(query, (token_id,))
        
        if not token:
            logger.error(f"Cannot create alert: token {token_id} not found")
            return None
            
        # Create alert
        alert = Alert()
        alert.token_id = token_id
        alert.user_id = user_id
        alert.access_id = access_id
        alert.alert_type = 'access'
        alert.severity = 'high'  # Honeytoken access is always high severity
        alert.description = (
            f"Honeytoken access detected!\n"
            f"Token: {token['token_name']} (Type: {token['token_type']})\n"
            f"Location: {token['token_location']}\n"
            f"User ID: {user_id}\n"
            f"IP Address: {ip_address}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        alert_id = alert.save()
        
        # Collect forensic evidence
        alert.collect_forensic_evidence()
        
        logger.warning(f"Created honeytoken access alert {alert_id}")
        return alert
        
    @staticmethod
    def create_behavior_alert(user_id, anomaly_details, severity="medium"):
        """Create an alert for anomalous user behavior"""
        # Create alert
        alert = Alert()
        alert.user_id = user_id
        alert.alert_type = 'unusual_behavior'
        alert.severity = severity
        
        # Generate description
        description = f"Unusual behavior detected for user {user_id}:\n"
        
        if isinstance(anomaly_details, dict):
            for feature, score in anomaly_details.items():
                description += f"- {feature}: {score:.2f}\n"
        else:
            description += anomaly_details
            
        alert.description = description
        
        alert_id = alert.save()
        
        # Collect forensic evidence
        alert.collect_forensic_evidence()
        
        logger.warning(f"Created behavioral alert {alert_id}")
        return alert

class AlertManager:
    """Manager class for handling alerts"""
    
    def __init__(self):
        self.db = get_db()
        
    def get_recent_alerts(self, hours=24, include_resolved=False):
        """Get recent alerts from the last N hours"""
        start_time = datetime.now() - timedelta(hours=hours)
        
        query = "SELECT * FROM alerts WHERE timestamp > %s"
        params = [start_time]
        
        if not include_resolved:
            query += " AND is_resolved = FALSE"
            
        query += " ORDER BY timestamp DESC"
        results = self.db.fetch_all(query, params)
        
        # Enrich with token and user data
        enriched_alerts = []
        for result in results:
            alert_data = dict(result)
            
            # Add token info if available
            if result['token_id']:
                token_query = "SELECT token_name, token_type FROM honeytokens WHERE token_id = %s"
                token = self.db.fetch_one(token_query, (result['token_id'],))
                if token:
                    alert_data['token_name'] = token['token_name']
                    alert_data['token_type'] = token['token_type']
                    
            # Add user info if available
            if result['user_id']:
                user_query = "SELECT username, email, department FROM users WHERE user_id = %s"
                user = self.db.fetch_one(user_query, (result['user_id'],))
                if user:
                    alert_data['username'] = user['username']
                    alert_data['user_email'] = user['email']
                    alert_data['user_department'] = user['department']
                    
            enriched_alerts.append(alert_data)
            
        return enriched_alerts
        
    def get_summary(self, days=7):
        """Get summary statistics of alerts"""
        start_time = datetime.now() - timedelta(days=days)
        
        # Count alerts by severity
        severity_query = """
        SELECT severity, COUNT(*) as count 
        FROM alerts 
        WHERE timestamp > %s 
        GROUP BY severity
        """
        severity_counts = self.db.fetch_all(severity_query, (start_time,))
        
        # Count alerts by type
        type_query = """
        SELECT alert_type, COUNT(*) as count 
        FROM alerts 
        WHERE timestamp > %s 
        GROUP BY alert_type
        """
        type_counts = self.db.fetch_all(type_query, (start_time,))
        
        # Count by day
        day_query = """
        SELECT DATE(timestamp) as day, COUNT(*) as count 
        FROM alerts 
        WHERE timestamp > %s 
        GROUP BY DATE(timestamp)
        ORDER BY day
        """
        day_counts = self.db.fetch_all(day_query, (start_time,))
        
        # Get top accessed honeytokens
        token_query = """
        SELECT h.token_id, h.token_name, h.token_type, COUNT(a.alert_id) as alert_count
        FROM alerts a
        JOIN honeytokens h ON a.token_id = h.token_id
        WHERE a.timestamp > %s
        GROUP BY h.token_id, h.token_name, h.token_type
        ORDER BY alert_count DESC
        LIMIT 5
        """
        top_tokens = self.db.fetch_all(token_query, (start_time,))
        
        # Get top users with alerts
        user_query = """
        SELECT u.user_id, u.username, u.department, COUNT(a.alert_id) as alert_count
        FROM alerts a
        JOIN users u ON a.user_id = u.user_id
        WHERE a.timestamp > %s
        GROUP BY u.user_id, u.username, u.department
        ORDER BY alert_count DESC
        LIMIT 5
        """
        top_users = self.db.fetch_all(user_query, (start_time,))
        
        return {
            'total_alerts': sum(item['count'] for item in severity_counts),
            'by_severity': severity_counts,
            'by_type': type_counts,
            'by_day': day_counts,
            'top_tokens': top_tokens,
            'top_users': top_users,
            'period_days': days
        }
        
    def export_alert_data(self, alert_id):
        """Export all data related to an alert for investigation"""
        alert = Alert.get_by_id(alert_id)
        if not alert or not alert.alert_id:
            logger.error(f"Cannot export data: alert {alert_id} not found")
            return None
            
        # Ensure we have the latest forensic evidence
        alert.collect_forensic_evidence()
        
        # Get all related data
        export_data = {
            'alert': {
                'alert_id': alert.alert_id,
                'type': alert.alert_type,
                'severity': alert.severity,
                'timestamp': alert.timestamp.isoformat() if alert.timestamp else None,
                'description': alert.description,
                'is_resolved': alert.is_resolved,
                'resolved_by': alert.resolved_by,
                'resolution_notes': alert.resolution_notes
            }
        }
        
        # Include forensic evidence if available
        if alert.forensic_evidence:
            try:
                export_data['forensic_evidence'] = json.loads(alert.forensic_evidence)
            except:
                export_data['forensic_evidence'] = alert.forensic_evidence
                
        # Include user data if available
        if alert.user_id:
            user_query = "SELECT * FROM users WHERE user_id = %s"
            user = self.db.fetch_one(user_query, (alert.user_id,))
            if user:
                export_data['user'] = {k: v for k, v in user.items() if k != 'password'}
                
        # Include token data if available
        if alert.token_id:
            token_query = "SELECT * FROM honeytokens WHERE token_id = %s"
            token = self.db.fetch_one(token_query, (alert.token_id,))
            if token:
                export_data['honeytoken'] = {k: v for k, v in token.items()}
                
        # Include access data if available
        if alert.access_id:
            access_query = "SELECT * FROM honeytoken_access WHERE access_id = %s"
            access = self.db.fetch_one(access_query, (alert.access_id,))
            if access:
                export_data['access'] = {k: v.isoformat() if isinstance(v, datetime) else v for k, v in access.items()}
                
                # Include related forensic logs
                logs_query = "SELECT * FROM forensic_logs WHERE access_id = %s"
                logs = self.db.fetch_all(logs_query, (alert.access_id,))
                if logs:
                    export_data['forensic_logs'] = []
                    for log in logs:
                        log_data = {k: v.isoformat() if isinstance(v, datetime) else v for k, v in log.items()}
                        export_data['forensic_logs'].append(log_data)
                        
        # Add export metadata
        export_data['export_metadata'] = {
            'exported_at': datetime.now().isoformat(),
            'exported_by': 'system',
            'format_version': '1.0'
        }
        
        # Create a hash of the export data for integrity verification
        export_json = json.dumps(export_data, sort_keys=True)
        export_hash = hashlib.sha256(export_json.encode()).hexdigest()
        export_data['export_metadata']['data_hash'] = export_hash
        
        return export_data

# Create a singleton instance
alert_manager = AlertManager()

# Function to get the alert manager
def get_alert_manager():
    return alert_manager 