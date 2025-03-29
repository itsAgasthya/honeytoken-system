import logging
import json
import math
import statistics
from datetime import datetime, timedelta
from ..db.database import get_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ueba.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ueba')

class UserBehaviorProfile:
    """Model to track and analyze user behavior"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.db = get_db()
        self.baseline_data = self._load_baseline()
        
    def _load_baseline(self):
        """Load baseline data for this user from the database"""
        query = "SELECT feature_name, feature_value, confidence_score FROM behavioral_baselines WHERE user_id = %s"
        results = self.db.fetch_all(query, (self.user_id,))
        
        baseline = {}
        for result in results:
            baseline[result['feature_name']] = {
                'value': result['feature_value'],
                'confidence': result['confidence_score']
            }
            
        return baseline
        
    def update_baseline(self, feature_name, new_value, weight=0.3):
        """Update baseline with new observed value using weighted average"""
        if feature_name in self.baseline_data:
            # Get current value and confidence
            current = self.baseline_data[feature_name]['value']
            confidence = self.baseline_data[feature_name]['confidence']
            
            # Update with weighted average
            updated_value = (current * (1 - weight)) + (new_value * weight)
            
            # Increase confidence slightly with each update
            updated_confidence = min(0.99, confidence + 0.01)
            
            # Update in database
            data = {
                'feature_value': updated_value,
                'confidence_score': updated_confidence,
                'last_updated': datetime.now()
            }
            condition = {
                'user_id': self.user_id,
                'feature_name': feature_name
            }
            self.db.update('behavioral_baselines', data, condition)
            
            # Update local cache
            self.baseline_data[feature_name] = {
                'value': updated_value,
                'confidence': updated_confidence
            }
            
            logger.debug(f"Updated baseline for user {self.user_id}, feature {feature_name}: {current} -> {updated_value}")
            
        else:
            # Create new baseline
            data = {
                'user_id': self.user_id,
                'feature_name': feature_name,
                'feature_value': new_value,
                'confidence_score': 0.5  # Initial confidence is moderate
            }
            self.db.insert('behavioral_baselines', data)
            
            # Update local cache
            self.baseline_data[feature_name] = {
                'value': new_value,
                'confidence': 0.5
            }
            
            logger.debug(f"Created new baseline for user {self.user_id}, feature {feature_name}: {new_value}")
            
    def calculate_anomaly_score(self, feature_name, observed_value):
        """Calculate an anomaly score for an observed value compared to baseline"""
        if feature_name not in self.baseline_data:
            # If no baseline exists, return a moderate anomaly score
            logger.warning(f"No baseline found for user {self.user_id}, feature {feature_name}")
            return 0.5
            
        baseline = self.baseline_data[feature_name]['value']
        confidence = self.baseline_data[feature_name]['confidence']
        
        # Calculate normalized difference
        if baseline == 0:
            # Avoid division by zero
            normalized_diff = 1.0 if observed_value != 0 else 0.0
        else:
            normalized_diff = abs(observed_value - baseline) / max(1.0, abs(baseline))
            
        # Apply confidence factor - lower confidence means less certain about anomalies
        anomaly_score = normalized_diff * confidence
        
        # Cap at 1.0
        anomaly_score = min(1.0, anomaly_score)
        
        logger.debug(f"Anomaly score for user {self.user_id}, feature {feature_name}: {anomaly_score}")
        return anomaly_score
        
    def record_anomaly_score(self, activity_id, feature_name, observed_value):
        """Record an anomaly score for a specific activity"""
        # Get expected value from baseline
        expected_value = self.baseline_data.get(feature_name, {'value': None})['value']
        
        # Calculate anomaly score
        anomaly_score = self.calculate_anomaly_score(feature_name, observed_value)
        
        # Record in database
        data = {
            'user_id': self.user_id,
            'activity_id': activity_id,
            'feature_name': feature_name,
            'expected_value': expected_value,
            'actual_value': observed_value,
            'anomaly_score': anomaly_score
        }
        
        anomaly_id = self.db.insert('anomaly_scores', data)
        
        # If anomaly score is high, create an alert
        if anomaly_score > 0.7:
            severity = "high" if anomaly_score > 0.9 else "medium"
            
            alert_data = {
                'user_id': self.user_id,
                'alert_type': 'unusual_behavior',
                'severity': severity,
                'description': f"Unusual behavior detected for user {self.user_id}: {feature_name} (score: {anomaly_score:.2f})"
            }
            
            alert_id = self.db.insert('alerts', alert_data)
            logger.warning(f"Created alert for anomalous behavior - User ID: {self.user_id}, Feature: {feature_name}, Score: {anomaly_score:.2f}")
            
        return anomaly_id
        
    def get_user_activities(self, days=30, limit=100):
        """Get recent user activities for analysis"""
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT * FROM user_activities 
        WHERE user_id = %s AND timestamp > %s 
        ORDER BY timestamp DESC 
        LIMIT %s
        """
        
        return self.db.fetch_all(query, (self.user_id, start_date, limit))
        
    def analyze_recent_activity(self, activity_id, activity_type, timestamp, resource, details=None):
        """Analyze a new activity against the user's behavioral baseline"""
        # Extract features from the activity
        features = self._extract_features(activity_type, timestamp, resource, details)
        
        # Calculate and record anomaly scores for each feature
        anomaly_scores = {}
        for feature_name, value in features.items():
            anomaly_scores[feature_name] = self.calculate_anomaly_score(feature_name, value)
            self.record_anomaly_score(activity_id, feature_name, value)
            
            # Update baseline with new observation 
            # (only if not highly anomalous, to avoid poisoning the baseline)
            if anomaly_scores[feature_name] < 0.7:
                self.update_baseline(feature_name, value)
                
        # Calculate overall anomaly score as weighted average
        if anomaly_scores:
            overall_score = sum(anomaly_scores.values()) / len(anomaly_scores)
        else:
            overall_score = 0
            
        return {
            'overall_score': overall_score,
            'feature_scores': anomaly_scores
        }
        
    def _extract_features(self, activity_type, timestamp, resource, details=None):
        """Extract behavioral features from an activity"""
        features = {}
        
        # Time of day (0-23 hours)
        hour_of_day = timestamp.hour
        features['time_of_day'] = hour_of_day
        
        # Day of week (0-6, where 0 is Monday)
        day_of_week = timestamp.weekday()
        features['day_of_week'] = day_of_week
        
        # Resource access patterns
        features['resource_type'] = self._hash_categorical(resource.split('/')[0] if '/' in resource else resource)
        
        # Activity type features
        features['activity_type'] = self._hash_categorical(activity_type)
        
        # Parse details if available
        if details:
            try:
                if isinstance(details, str):
                    details_dict = json.loads(details)
                else:
                    details_dict = details
                    
                # Extract more features based on details
                if 'duration' in details_dict:
                    features['activity_duration'] = float(details_dict['duration'])
                    
                if 'bytes_transferred' in details_dict:
                    features['bytes_transferred'] = float(details_dict['bytes_transferred'])
                    
                if 'access_count' in details_dict:
                    features['access_count'] = float(details_dict['access_count'])
            except:
                # If details can't be parsed, just ignore
                pass
                
        return features
        
    def _hash_categorical(self, value):
        """Convert categorical values to numeric using a simple hash"""
        if value is None:
            return 0
            
        # Use hash function to convert string to numeric
        hash_val = hash(str(value)) % 1000
        return hash_val / 1000  # Normalize to 0-1 range

class UEBAEngine:
    """Main engine for User Entity Behavior Analytics"""
    
    def __init__(self):
        self.db = get_db()
        
    def process_activity(self, user_id, activity_type, ip_address, resource=None, details=None, user_agent=None, session_id=None):
        """Process a new user activity"""
        # Log the activity
        data = {
            'user_id': user_id,
            'activity_type': activity_type,
            'ip_address': ip_address,
            'resource_accessed': resource,
            'action_details': json.dumps(details) if isinstance(details, dict) else details,
            'user_agent': user_agent,
            'session_id': session_id
        }
        
        activity_id = self.db.insert('user_activities', data)
        
        if not activity_id:
            logger.error(f"Failed to log activity for user {user_id}")
            return None
            
        # Create user profile if not exists
        user_profile = UserBehaviorProfile(user_id)
        
        # Analyze the activity
        timestamp = datetime.now()
        analysis_result = user_profile.analyze_recent_activity(
            activity_id,
            activity_type,
            timestamp,
            resource or '',
            details
        )
        
        # Check if multiple accesses from different IPs
        ip_anomaly = self._check_multiple_ip_access(user_id, ip_address)
        
        # Check for other anomalies
        resource_anomaly = self._check_resource_access_pattern(user_id, resource)
        
        # If high anomaly scores, create alert
        if analysis_result['overall_score'] > 0.8 or ip_anomaly or resource_anomaly:
            alert_data = {
                'user_id': user_id,
                'alert_type': 'unusual_behavior',
                'severity': 'high' if analysis_result['overall_score'] > 0.9 else 'medium',
                'description': self._generate_alert_description(
                    user_id, 
                    analysis_result, 
                    ip_anomaly, 
                    resource_anomaly
                )
            }
            
            alert_id = self.db.insert('alerts', alert_data)
            logger.warning(f"Created alert for user {user_id} - Score: {analysis_result['overall_score']:.2f}")
            
        return {
            'activity_id': activity_id,
            'analysis': analysis_result
        }
        
    def _check_multiple_ip_access(self, user_id, current_ip):
        """Check if user is accessing from multiple IPs in a short time window"""
        # Get recent IP addresses used by this user in the last hour
        query = """
        SELECT DISTINCT ip_address FROM user_activities 
        WHERE user_id = %s AND timestamp > %s 
        ORDER BY timestamp DESC
        """
        
        one_hour_ago = datetime.now() - timedelta(hours=1)
        results = self.db.fetch_all(query, (user_id, one_hour_ago))
        
        # Extract IP addresses
        recent_ips = [r['ip_address'] for r in results if r['ip_address'] != current_ip]
        
        # If multiple different IPs found, flag as anomaly
        if len(recent_ips) >= 2:
            logger.warning(f"Multiple IP access detected for user {user_id}: {current_ip}, {recent_ips}")
            return True
            
        return False
        
    def _check_resource_access_pattern(self, user_id, resource):
        """Check if resource access pattern is anomalous"""
        if not resource:
            return False
            
        # Get resources commonly accessed by this user
        query = """
        SELECT resource_accessed, COUNT(*) as count 
        FROM user_activities 
        WHERE user_id = %s AND timestamp > %s 
        GROUP BY resource_accessed 
        ORDER BY count DESC
        """
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        results = self.db.fetch_all(query, (user_id, thirty_days_ago))
        
        # Check if current resource has been accessed before
        common_resources = [r['resource_accessed'] for r in results]
        
        # If resource has never been accessed and we have enough data
        if resource not in common_resources and len(common_resources) > 5:
            logger.warning(f"Unusual resource access for user {user_id}: {resource}")
            return True
            
        return False
        
    def _generate_alert_description(self, user_id, analysis_result, ip_anomaly, resource_anomaly):
        """Generate a human-readable alert description"""
        description = f"Unusual behavior detected for user {user_id}:\n"
        
        # Add overall anomaly score
        description += f"Overall anomaly score: {analysis_result['overall_score']:.2f}\n"
        
        # Add specific anomalies
        if analysis_result['overall_score'] > 0.7:
            # Add details about which features were most anomalous
            high_scores = [
                (feature, score) 
                for feature, score in analysis_result['feature_scores'].items() 
                if score > 0.7
            ]
            
            if high_scores:
                description += "Anomalous features:\n"
                for feature, score in high_scores:
                    description += f"- {feature}: {score:.2f}\n"
                    
        if ip_anomaly:
            description += "Multiple IP addresses used in a short time window\n"
            
        if resource_anomaly:
            description += "Access to unusual resources detected\n"
            
        return description
        
    def get_user_risk_score(self, user_id):
        """Calculate overall risk score for a user based on alerts and anomalies"""
        # Get alert counts by severity for the user
        query = """
        SELECT severity, COUNT(*) as count 
        FROM alerts 
        WHERE user_id = %s AND timestamp > %s 
        GROUP BY severity
        """
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        results = self.db.fetch_all(query, (user_id, thirty_days_ago))
        
        # Calculate weighted score based on alert severity
        weights = {
            'low': 1,
            'medium': 3,
            'high': 5,
            'critical': 10
        }
        
        alert_score = 0
        for result in results:
            severity = result['severity']
            count = result['count']
            alert_score += weights.get(severity, 1) * count
            
        # Get average anomaly score for the user
        query = """
        SELECT AVG(anomaly_score) as avg_score 
        FROM anomaly_scores 
        WHERE user_id = %s AND timestamp > %s
        """
        
        result = self.db.fetch_one(query, (user_id, thirty_days_ago))
        avg_anomaly = result['avg_score'] if result and result['avg_score'] else 0
        
        # Combine scores
        risk_score = (alert_score * 0.7) + (avg_anomaly * 30)
        
        # Normalize to 0-100 scale with logarithmic scaling for alert_score
        if alert_score > 0:
            normalized_risk = min(100, 20 + (50 * math.log10(1 + alert_score)) + (30 * avg_anomaly))
        else:
            normalized_risk = min(100, 20 + (30 * avg_anomaly))
            
        # Categorize risk
        risk_category = 'low'
        if normalized_risk > 80:
            risk_category = 'critical'
        elif normalized_risk > 60:
            risk_category = 'high'
        elif normalized_risk > 40:
            risk_category = 'medium'
            
        return {
            'user_id': user_id,
            'raw_score': risk_score,
            'normalized_score': normalized_risk,
            'category': risk_category,
            'alert_count': sum(result['count'] for result in results),
            'avg_anomaly_score': avg_anomaly
        }
        
    def get_top_risky_users(self, limit=10):
        """Get the top risky users based on alerts and anomalies"""
        # Get all users
        query = "SELECT user_id FROM users"
        users = self.db.fetch_all(query)
        
        # Calculate risk score for each user
        risk_scores = []
        for user in users:
            user_id = user['user_id']
            risk_info = self.get_user_risk_score(user_id)
            risk_scores.append(risk_info)
            
        # Sort by normalized risk score
        risk_scores.sort(key=lambda x: x['normalized_score'], reverse=True)
        
        # Return top N
        return risk_scores[:limit]
        
# Create a singleton instance
ueba_engine = UEBAEngine()

# Function to get the UEBA engine
def get_ueba_engine():
    return ueba_engine 