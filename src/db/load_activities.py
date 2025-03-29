import os
import json
from datetime import datetime
from pathlib import Path
import logging
from .database import get_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/load_activities.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('load_activities')

def load_offline_activities():
    """Load activities from offline_activities directory into the database."""
    try:
        # Get database connection
        db = get_db()
        
        # Get path to offline activities directory
        activities_dir = Path('offline_activities')
        if not activities_dir.exists():
            logger.error("offline_activities directory not found")
            return
            
        # Get list of activity files
        activity_files = list(activities_dir.glob('activity_*.json'))
        logger.info(f"Found {len(activity_files)} activity files to process")
        
        # Process each activity file
        for activity_file in activity_files:
            try:
                # Read activity data
                with open(activity_file, 'r') as f:
                    activity_data = json.load(f)
                
                # Extract fields
                user_id = activity_data['user_id']
                activity_type = activity_data['activity_type']
                ip_address = activity_data['ip_address']
                user_agent = activity_data['user_agent']
                resource = activity_data.get('resource', '')
                details = activity_data.get('details', {})
                
                # Convert timestamp string to datetime
                timestamp = datetime.fromisoformat(details.get('timestamp', datetime.now().isoformat()))
                
                # Insert into database
                db.execute_query("""
                    INSERT INTO user_activities 
                    (user_id, activity_type, timestamp, ip_address, user_agent, resource_accessed, action_details)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    activity_type,
                    timestamp,
                    ip_address,
                    user_agent,
                    resource,
                    json.dumps(details)
                ))
                
                # Move processed file to processed directory
                processed_dir = activities_dir / 'processed'
                processed_dir.mkdir(exist_ok=True)
                activity_file.rename(processed_dir / activity_file.name)
                
                logger.info(f"Processed activity file: {activity_file.name}")
                
            except Exception as e:
                logger.error(f"Error processing activity file {activity_file.name}: {str(e)}")
                continue
        
        logger.info("Finished processing all activity files")
        
    except Exception as e:
        logger.error(f"Error loading offline activities: {str(e)}")
        raise

if __name__ == '__main__':
    load_offline_activities() 