#!/bin/bash

# UEBA Honeytoken System Demo Script
# For Vulnerability Assessment and Penetration Testing Course

echo "========================================================"
echo "  UEBA Honeytoken System - Demo Setup"
echo "========================================================"

# Step 1: Check and kill any existing processes
echo "[1/7] Cleaning up existing processes..."
pkill -f "python run.py" || true
pkill -f "python start_server.py" || true
pkill -f "python src/api/app.py" || true
sleep 2

# Step 2: Ensure the environment is set up
echo "[2/7] Setting up the environment..."
# Check if venv is available
if [ -d "venv" ]; then
    # Use bash-compatible activation for the script
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "WARNING: Could not find venv/bin/activate, continuing without virtual environment"
    fi
    
    # Check for required dependencies and install if missing
    if ! python -c "import flask" 2>/dev/null; then
        echo "Flask not found, installing required packages..."
        if command -v pip > /dev/null; then
            pip install -r requirements.txt
        else
            echo "WARNING: pip not found, attempting to install with system package manager"
            apt-get update && apt-get install -y python3-pip || echo "Could not install pip"
            pip install -r requirements.txt
        fi
    fi
else
    echo "Creating a new virtual environment..."
    python -m venv venv
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "WARNING: Could not find venv/bin/activate, continuing without virtual environment"
    fi
    
    if command -v pip > /dev/null; then
        pip install -r requirements.txt
    else
        echo "WARNING: pip not found, attempting to install with system package manager"
        apt-get update && apt-get install -y python3-pip || echo "Could not install pip"
        pip install -r requirements.txt
    fi
fi

# Step 3: Reset and initialize the database
echo "[3/7] Initializing the database..."
if [ -f "src/db/schema.sql" ]; then
    echo "Found database schema, initializing database..."
    # Use environment variables or defaults for database connection
    DB_USER=${DB_USER:-root}
    DB_PASS=${DB_PASS:-"123"}
    DB_NAME=${DB_NAME:-honeytoken_ueba}
    
    # Try to initialize the database
    if command -v mysql > /dev/null; then
        # If mysql command exists
        if [ -z "$DB_PASS" ]; then
            mysql -u $DB_USER -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;" || echo "WARNING: Could not create database"
            mysql -u $DB_USER $DB_NAME < src/db/schema.sql || echo "WARNING: Could not initialize schema"
        else
            mysql -u $DB_USER -p"$DB_PASS" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;" || echo "WARNING: Could not create database"
            mysql -u $DB_USER -p"$DB_PASS" $DB_NAME < src/db/schema.sql || echo "WARNING: Could not initialize schema"
        fi
        echo "Database initialized successfully"
    else
        echo "WARNING: MySQL client not found, skipping database initialization"
    fi
else
    echo "WARNING: Database setup script not found. Assuming database is already set up."
fi

# Create and set permissions for log directory
echo "Ensuring logs directory exists with proper permissions..."
mkdir -p logs
rm -f logs/app.log logs/api.log logs/alert.log logs/honeytoken.log logs/ueba.log
touch logs/app.log logs/api.log logs/alert.log logs/honeytoken.log logs/ueba.log
chmod 777 -R logs

# Step 4: Start the application using the standalone server script
echo "[4/7] Starting the UEBA Honeytoken System..."
echo "Starting application using start_server.py - logging to logs/app.log"

# Ensure the server script is executable
chmod +x start_server.py

# Start the server
python start_server.py > logs/app.log 2>&1 &
APP_PID=$!
echo "Application started with PID: $APP_PID"

# Display logs
echo "Displaying current logs:"
cat logs/app.log

# Step 5: Wait for the application to start
echo "[5/7] Waiting for the application to start..."
echo "Giving the server time to initialize..."
sleep 10

# Check if the API is running
echo "Checking if the API is running..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/dashboard | grep -q "200"; then
    echo "Dashboard is accessible!"
else
    echo "WARNING: Dashboard may not be accessible. Check logs/app.log for details."
    echo "Latest logs:"
    cat logs/app.log
    echo "Continuing with the script, but note that the server component may not be functioning correctly."
fi

# Step 6: Generate test data by simulating user behavior
echo "[6/7] Generating test data with different behavior patterns..."
# Use the --offline flag since we're not sure if the API is working
echo "  ↳ Simulating normal user behavior..."
python simulate_user_behavior.py --severity normal --offline

echo "  ↳ Simulating suspicious user behavior..."
python simulate_user_behavior.py --severity suspicious --offline

echo "  ↳ Simulating malicious user behavior..."
python simulate_user_behavior.py --severity malicious --offline

# Step 7: Open the web interface
echo "[7/7] Opening the web interface..."
echo "Dashboard URL: http://localhost:5000/dashboard"

if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:5000/dashboard
elif command -v open > /dev/null; then
    open http://localhost:5000/dashboard
else
    echo "Could not automatically open browser. Please open http://localhost:5000/dashboard manually."
fi

# Display summary of what to expect
echo ""
echo "========================================================"
echo "  UEBA Honeytoken System - Demo Ready"
echo "========================================================"
echo ""
echo "The system has been set up with different types of user behaviors:"
echo "  - Normal activities: Typical user actions during work hours"
echo "  - Suspicious activities: Unusual actions or access patterns"
echo "  - Malicious activities: Potential security threats and violations"
echo ""
echo "Key Features to Demonstrate:"
echo "  1. Dashboard - Overview of system activity and alerts"
echo "  2. Honeytokens - View, create, and manage honeytokens"
echo "  3. Alerts - Monitor and respond to security alerts"
echo "  4. User Management - Track user risk scores and activities"
echo "  5. UEBA Analytics - Analyze behavior patterns and anomalies"
echo ""
echo "To stop the application, run: pkill -f 'python start_server.py'"
echo "========================================================="