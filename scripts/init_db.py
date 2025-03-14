#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from dotenv import load_dotenv

from app.models.base import Base
from app.models.honeytoken import Honeytoken, HoneytokenAccess, AlertConfig

def init_db():
    """Initialize the database and create all tables."""
    load_dotenv()

    # Database connection parameters
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    SHADOW_DB_NAME = os.getenv('SHADOW_DB_NAME')

    # Create database URLs
    main_db_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    shadow_db_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{SHADOW_DB_NAME}"

    # Create databases if they don't exist
    for db_url in [main_db_url, shadow_db_url]:
        engine = create_engine(db_url)
        if not database_exists(engine.url):
            create_database(engine.url)
            print(f"Created database: {engine.url}")
        
        # Create all tables
        Base.metadata.create_all(engine)
        print(f"Created tables in database: {engine.url}")

if __name__ == "__main__":
    try:
        init_db()
        print("Database initialization completed successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1) 