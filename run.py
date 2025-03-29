#!/usr/bin/env python3

import os
import sys
import json
import glob
import time
import logging
import argparse
import traceback
import shutil
from datetime import datetime
from src.api.app import run_api
from src.db.database import get_db

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('run')

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Honeytoken UEBA System")
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the API on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the API on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--setup', action='store_true', help='Run setup tasks')
    parser.add_argument('--load-offline', action='store_true', help='Load offline activities before starting')
    parser.add_argument('--test-db', action='store_true', help='Test database connection and exit')
    
    return parser.parse_args()

def ensure_directories():
    """Ensure required directories exist"""
    dirs = ['logs', 'tmp/honeyfiles', 'offline_activities', 'offline_activities/processed', 'offline_activities/failed']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.info(f"Ensured directory exists: {d}")

def test_database_connection():
    """Test database connection"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            db = get_db()
            
            # Test basic connection
            if not db.connection or not db.connection.is_connected():
                logger.error(f"Database connection failed - not connected (attempt {attempt+1}/{max_attempts})")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
                return False
                
            # Run a simple query to test the connection fully
            test_result = db.fetch_one("SELECT 1 as test")
            if test_result and test_result.get('test') == 1:
                logger.info("Database connection successful")
                return True
            else:
                logger.error(f"Database connection test query failed (attempt {attempt+1}/{max_attempts})")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
                return False
        except Exception as e:
            logger.error(f"Database connection failed with error (attempt {attempt+1}/{max_attempts}): {str(e)}")
            logger.error(traceback.format_exc())
            if attempt < max_attempts - 1:
                time.sleep(2)
                continue
            return False
    
    return False

def setup():
    """Run setup tasks"""
    logger.info("Running setup tasks...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Test database connection
    if not test_database_connection():
        logger.error("Setup failed: Database connection error")
        return False
        
    logger.info("Setup completed successfully")
    return True

def mark_file_as_failed(file_path, error_message):
    """Move a failed file to the failed directory with error information"""
    try:
        base_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        failed_dir = 'offline_activities/failed'
        
        # Ensure failed directory exists
        os.makedirs(failed_dir, exist_ok=True)
        
        # Create a failed filename with timestamp
        failed_filename = f"{timestamp}_{base_name}"
        failed_path = os.path.join(failed_dir, failed_filename)
        
        # Create an error info file
        error_file = f"{failed_path}.error"
        with open(error_file, 'w') as f:
            f.write(f"Error processing file: {error_message}\n")
            f.write(f"Original file: {file_path}\n")
            f.write(f"Timestamp: {timestamp}\n")
        
        # Move the file
        shutil.move(file_path, failed_path)
        logger.warning(f"Marked file as failed: {file_path} -> {failed_path}")
        return True
    except Exception as e:
        logger.error(f"Error marking file as failed: {str(e)}")
        return False

def process_activity_file(file_path, ueba_engine):
    """Process a single offline activity file"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Check if the file still exists (it might have been moved by another process)
            if not os.path.exists(file_path):
                logger.warning(f"File no longer exists, skipping: {file_path}")
                return False
                
            # Read and load the activity data
            with open(file_path, 'r') as f:
                activity = json.load(f)
                
            # Validate required fields
            required_fields = ['user_id', 'activity_type', 'ip_address']
            for field in required_fields:
                if field not in activity:
                    raise ValueError(f"Missing required field: {field}")
                
            # Process the activity
            user_id = activity.get('user_id')
            activity_type = activity.get('activity_type')
            ip_address = activity.get('ip_address')
            resource = activity.get('resource')
            details = activity.get('details')
            user_agent = activity.get('user_agent')
            
            # Enhanced error handling during processing
            if not test_database_connection():
                logger.error(f"Database connection lost before processing file: {file_path}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
                return False
                
            result = ueba_engine.process_activity(
                user_id=user_id,
                activity_type=activity_type,
                ip_address=ip_address,
                resource=resource,
                details=details,
                user_agent=user_agent
            )
            
            if result:
                logger.info(f"Loaded offline activity from {os.path.basename(file_path)}: {activity_type} - Anomaly score: {result['analysis']['overall_score']}")
                
                # Move the file to a processed folder
                processed_dir = 'offline_activities/processed'
                os.makedirs(processed_dir, exist_ok=True)
                
                # Create a processed filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                processed_filename = f"{timestamp}_{os.path.basename(file_path)}"
                processed_path = os.path.join(processed_dir, processed_filename)
                
                # Move the file
                shutil.move(file_path, processed_path)
                return True
            else:
                logger.error(f"Failed to process activity from {file_path}")
                if attempt < max_attempts - 1:
                    logger.warning(f"Retrying processing of {file_path} (attempt {attempt+1}/{max_attempts})")
                    time.sleep(2)
                    continue
                else:
                    mark_file_as_failed(file_path, "Processing returned no result")
                    return False
                    
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in file {file_path}: {str(e)}")
            mark_file_as_failed(file_path, f"Invalid JSON: {str(e)}")
            return False
        except ValueError as e:
            logger.error(f"Validation error in file {file_path}: {str(e)}")
            mark_file_as_failed(file_path, f"Validation error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error processing offline activity file {file_path} (attempt {attempt+1}/{max_attempts}): {str(e)}")
            logger.error(traceback.format_exc())
            
            if attempt < max_attempts - 1:
                logger.warning(f"Retrying processing of {file_path}")
                time.sleep(2)
                # After an exception, test the database connection before retrying
                if not test_database_connection():
                    logger.error("Database connection lost during processing")
                    time.sleep(5)  # Wait a bit longer before retry
                continue
            else:
                # After max retries, mark as failed
                mark_file_as_failed(file_path, f"Processing error: {str(e)}")
                return False

def load_offline_activities():
    """Load any offline activities into the database"""
    logger.info("Looking for offline activities to load...")
    
    try:
        from src.models.ueba import get_ueba_engine
        ueba_engine = get_ueba_engine()
        
        # Get all offline activity files
        activity_files = glob.glob('offline_activities/activity_*.json')
        if not activity_files:
            logger.info("No offline activities found.")
            return 0
            
        # Test database connection before processing
        if not test_database_connection():
            logger.error("Failed to connect to database. Cannot process offline activities.")
            return 0
            
        # Process files in batches to avoid overwhelming the database
        batch_size = 10
        count = 0
        total_files = len(activity_files)
        logger.info(f"Found {total_files} offline activities to process")
        
        for i, file_path in enumerate(activity_files):
            try:
                if process_activity_file(file_path, ueba_engine):
                    count += 1
                    # After each successful activity, log progress
                    if count % 5 == 0:
                        logger.info(f"Processed {count}/{total_files} activities")
                    
                    # After each batch, check database connection
                    if count % batch_size == 0:
                        logger.info(f"Completed batch of {batch_size} activities, checking database connection")
                        if not test_database_connection():
                            logger.error("Database connection lost during processing. Pausing...")
                            # Wait for a moment and retry
                            time.sleep(5)
                            if not test_database_connection():
                                logger.error("Failed to reconnect to database. Stopping processing.")
                                break
                            else:
                                logger.info("Successfully reconnected to database, continuing processing")
                        
                        # Small pause between batches to reduce database load
                        time.sleep(1)
            except Exception as e:
                logger.error(f"Error during offline activity processing loop: {str(e)}")
                logger.error(traceback.format_exc())
                # Continue with next file
                continue
        
        logger.info(f"Loaded {count} offline activities.")
        return count
    except Exception as e:
        logger.error(f"Fatal error in load_offline_activities: {str(e)}")
        logger.error(traceback.format_exc())
        return 0

def main():
    """Main entry point"""
    try:
        args = parse_args()
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Ensure all required directories exist
        ensure_directories()
        
        # Test database connection if requested
        if args.test_db:
            if test_database_connection():
                logger.info("Database connection test successful")
                sys.exit(0)
            else:
                logger.error("Database connection test failed")
                sys.exit(1)
        
        # Run setup if requested
        if args.setup:
            if not setup():
                sys.exit(1)
            sys.exit(0)
            
        # Test database connection
        if not test_database_connection():
            logger.error("Failed to connect to database. Exiting.")
            sys.exit(1)
            
        # Load offline activities if requested
        if args.load_offline:
            logger.info("Loading offline activities...")
            load_offline_activities()
        else:
            # Check if offline activities exist and load them automatically
            activity_files = glob.glob('offline_activities/activity_*.json')
            if activity_files:
                logger.info(f"Found {len(activity_files)} offline activities. Loading automatically...")
                load_offline_activities()
        
        # Run the API
        logger.info(f"Starting API on {args.host}:{args.port} (debug={args.debug})")
        run_api(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 