from flask import Blueprint, render_template, jsonify
from app.models.honeytoken import Honeytoken, HoneytokenAccess
from app import db
from .auth import login_required

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    """Render the dashboard page."""
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

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