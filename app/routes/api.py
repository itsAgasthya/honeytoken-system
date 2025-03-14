from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models.honeytoken import HoneytokenAccess, Honeytoken, AlertConfig
from app import db

bp = Blueprint('api', __name__)

@bp.route('/access-logs', methods=['GET'])
def get_access_logs():
    """Get honeytoken access logs with filtering options."""
    # Get query parameters
    days = request.args.get('days', 7, type=int)
    token_id = request.args.get('token_id', type=int)
    
    query = HoneytokenAccess.query
    
    # Apply filters
    if token_id:
        query = query.filter_by(token_id=token_id)
    
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(HoneytokenAccess.access_time >= cutoff_date)
    
    # Execute query
    logs = query.order_by(HoneytokenAccess.access_time.desc()).all()
    
    return jsonify([{
        'id': log.id,
        'token_id': log.token_id,
        'access_time': log.access_time.isoformat(),
        'user_id': log.user_id,
        'ip_address': log.ip_address,
        'access_type': log.access_type.value,
        'query_text': log.query_text
    } for log in logs])

@bp.route('/analytics/access-patterns', methods=['GET'])
def get_access_patterns():
    """Get analytics about honeytoken access patterns."""
    days = request.args.get('days', 30, type=int)
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get access counts by token
    token_stats = db.session.query(
        HoneytokenAccess.token_id,
        func.count(HoneytokenAccess.id).label('access_count'),
        func.count(func.distinct(HoneytokenAccess.user_id)).label('unique_users'),
        func.count(func.distinct(HoneytokenAccess.ip_address)).label('unique_ips')
    ).filter(
        HoneytokenAccess.access_time >= cutoff_date
    ).group_by(
        HoneytokenAccess.token_id
    ).all()
    
    # Get access counts by day
    daily_stats = db.session.query(
        func.date(HoneytokenAccess.access_time).label('date'),
        func.count(HoneytokenAccess.id).label('access_count')
    ).filter(
        HoneytokenAccess.access_time >= cutoff_date
    ).group_by(
        func.date(HoneytokenAccess.access_time)
    ).all()
    
    return jsonify({
        'token_stats': [{
            'token_id': stat.token_id,
            'access_count': stat.access_count,
            'unique_users': stat.unique_users,
            'unique_ips': stat.unique_ips
        } for stat in token_stats],
        'daily_stats': [{
            'date': str(stat.date),
            'access_count': stat.access_count
        } for stat in daily_stats]
    })

@bp.route('/alerts/check', methods=['POST'])
def check_alerts():
    """Check for alert conditions and return triggered alerts."""
    # Get all active honeytokens with their alert configs
    active_tokens = db.session.query(
        Honeytoken, AlertConfig
    ).join(
        AlertConfig
    ).filter(
        Honeytoken.is_active == 1
    ).all()
    
    alerts = []
    
    for token, config in active_tokens:
        # Get recent access count
        recent_access_count = HoneytokenAccess.query.filter(
            HoneytokenAccess.token_id == token.id,
            HoneytokenAccess.access_time >= datetime.utcnow() - timedelta(seconds=config.cooldown_period)
        ).count()
        
        # Check if threshold is exceeded
        if recent_access_count >= config.alert_threshold:
            alerts.append({
                'token_id': token.id,
                'token_type': token.token_type.value,
                'access_count': recent_access_count,
                'threshold': config.alert_threshold,
                'channels': config.alert_channels
            })
    
    return jsonify({
        'alerts': alerts,
        'timestamp': datetime.utcnow().isoformat()
    }) 