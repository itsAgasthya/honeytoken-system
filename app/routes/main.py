from flask import Blueprint, render_template, jsonify
from app.models.honeytoken import Honeytoken, HoneytokenAccess
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the dashboard page."""
    return render_template('index.html')

@bp.route('/stats')
def stats():
    """Get basic statistics about honeytoken access."""
    total_tokens = Honeytoken.query.count()
    total_access = HoneytokenAccess.query.count()
    active_tokens = Honeytoken.query.filter_by(is_active=1).count()
    
    return jsonify({
        'total_tokens': total_tokens,
        'total_access': total_access,
        'active_tokens': active_tokens
    }) 