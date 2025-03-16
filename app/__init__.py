from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask-SQLAlchemy and Flask-Migrate
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure the Flask application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost/{os.getenv('DB_NAME')}?auth_plugin=mysql_native_password"
    app.config['SQLALCHEMY_BINDS'] = {
        'shadow': f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost/{os.getenv('SHADOW_DB_NAME')}?auth_plugin=mysql_native_password"
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from .routes import main, admin, api, auth
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(auth.bp, url_prefix='/auth')
    
    return app 