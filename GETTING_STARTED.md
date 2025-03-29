# Getting Started with Honeytoken UEBA System

This guide will help you get started with the Honeytoken UEBA System, a comprehensive solution for detecting insider threats using honeytokens and User Entity Behavior Analytics.

## Quick Start

The easiest way to get started is to use the provided shell script:

```bash
# See available options
./run.sh --help

# Setup the environment and database
./run.sh --setup

# Generate sample data for testing
./run.sh --sample-data

# Start the application
./run.sh --run

# Do all of the above in one command
./run.sh --all
```

## Manual Setup

If you prefer to set things up manually, follow these steps:

1. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the database**:
   ```bash
   mysql -u root -p < src/db/schema.sql
   ```

3. **Set up the system**:
   ```bash
   python run.py --setup
   ```

4. **Run the application**:
   ```bash
   python run.py --debug
   ```

## Testing with Sample Data

To generate sample data for testing:

1. **Create sample honeytokens**:
   ```bash
   python create_sample_tokens.py --access
   ```

2. **Simulate user behavior for UEBA analysis**:
   ```bash
   python simulate_user_behavior.py --suspicious --sessions 2
   ```

## Accessing the System

- **Web Dashboard**: http://localhost:5000/
- **API**: Use the API key `honeytoken_api_key_123` in the `X-API-Key` header

Example API call:
```bash
curl -H "X-API-Key: honeytoken_api_key_123" http://localhost:5000/api/honeytokens
```

## Feature Overview

### Honeytoken Types

1. **File Honeytokens**
   - Fake sensitive documents that appear legitimate
   - Monitored for unauthorized access

2. **Database Honeytokens**
   - Fake records in database tables
   - Look like real customer data, but easily identifiable as fake

3. **API Key Honeytokens**
   - Fake API credentials that appear to be for sensitive services
   - Can detect if credentials are being harvested

4. **Credentials Honeytokens**
   - Username/password pairs for non-existent users
   - Useful for detecting password spraying attacks

### UEBA Capabilities

The system analyzes user behavior to detect anomalies:

- Establishes behavioral baselines for users
- Detects activities outside normal patterns
- Scores users based on risk factors
- Correlates honeytoken access with other behaviors

### Alert Management

Comprehensive alert system for security teams:

- Real-time notifications for suspicious activities
- Alert triage and investigation workflow
- Forensic evidence collection for incidents
- Resolution tracking and audit trail

## Customization

You can customize the system by:

1. **Changing the API key**:
   - Edit the `API_KEY` variable in `src/api/app.py`

2. **Adding new honeytoken types**:
   - Extend the base `Honeytoken` class in `src/models/honeytoken.py`

3. **Adjusting UEBA thresholds**:
   - Modify scoring parameters in `src/models/ueba.py`

4. **Creating custom alerts**:
   - Implement new alert types in `src/models/alert.py`

## Troubleshooting

If you encounter issues:

1. **Database Connection Problems**:
   - Check MySQL/MariaDB is running: `systemctl status mariadb`
   - Verify credentials in `.dbcredentials` or when prompted

2. **Application Errors**:
   - Check log files in the `logs/` directory
   - Run with `--debug` for verbose output

3. **Permission Issues**:
   - Ensure the application has write access to `logs/` and `tmp/` directories

## Next Steps

Once you're familiar with the basic functionality:

1. **Deploy in a test environment** to monitor real user behavior
2. **Integrate with your SIEM system** using the API
3. **Customize honeytokens** for your specific environment
4. **Set up automated alert handling** for efficient incident response 