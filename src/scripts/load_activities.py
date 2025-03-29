#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent.parent.parent
sys.path.append(str(src_dir))

from src.db.load_activities import load_offline_activities

if __name__ == '__main__':
    try:
        load_offline_activities()
        print("Successfully loaded offline activities into database")
    except Exception as e:
        print(f"Error loading activities: {str(e)}")
        sys.exit(1) 