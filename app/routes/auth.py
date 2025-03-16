from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import os
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Get credentials from environment variables
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_password = os.getenv('ADMIN_PASSWORD')
        
        if username == admin_username and password == admin_password:
            session['user_id'] = username
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login')) 