# Honeytoken UEBA System

A comprehensive User and Entity Behavior Analytics (UEBA) system for detecting insider threats through honeytoken monitoring.

## Overview

The Honeytoken UEBA System is a specialized security solution designed to detect and alert on unauthorized access to sensitive data or resources within an organization. By deploying deliberately enticing but fake resources (honeytokens) and monitoring their access, security teams can identify potential insider threats, unauthorized access, or compromised credentials.

This system combines traditional honeytoken techniques with advanced User and Entity Behavior Analytics (UEBA) to provide context-aware detection, reduce false positives, and enable forensic investigation of security incidents.

## Honeytoken Trap Setup

The system implements a sophisticated trap deployment methodology:

### Deployment Strategies
- **Strategic Placement**: Honeytokens are deployed in locations that legitimate users should never access, but would be attractive to potential attackers
- **Realistic Content**: Generated with plausible but fake data to appear as legitimate sensitive information
- **Access Controls**: Configured with appropriate permissions to make them discoverable while monitoring access
- **Diversity**: Multiple types of traps are used to detect different attack vectors and methodologies

### Monitoring Mechanisms
- **Continuous Monitoring**: Real-time monitoring of all honeytoken access events
- **Contextual Analysis**: Each access is analyzed within the context of user behavior patterns
- **Non-Interference**: Monitoring is designed to be invisible to avoid alerting attackers
- **Tamper Detection**: Any attempts to modify or remove honeytokens are logged and generate high-priority alerts

### Trap Types Implementation
1. **File Honeytokens**:
   - Deployed as documents in shared drives, servers, or user directories
   - Types include: spreadsheets, PDFs, text files, config files, and backup files
   - Each file contains unique markers for identifying which specific token was accessed

2. **Database Honeytokens**:
   - Implemented as records in legitimate databases with enticing column names
   - Types include: test accounts, fake customer records, and sensitive-looking test data
   - Embedded tracking identifiers allow pinpointing exact record access

3. **API Key Honeytokens**:
   - Inactive but realistic-looking API keys placed in configuration files
   - Implementation logs any attempt to authenticate with these keys
   - Different keys deployed with varying access level appearance (admin, user, etc.)

4. **Credential Honeytokens**:
   - Fake user accounts that no legitimate process should ever use
   - Distributed in credential stores or configuration files
   - Login attempts trigger immediate notifications

## User Behavior Analysis

The system implements a multi-layered approach to user behavior analysis:

### Behavioral Baseline Establishment
- **Initial Learning Period**: The system observes users for 2-4 weeks to establish normal patterns
- **Feature Extraction**: Extracts over 20 behavioral features including:
  - Temporal patterns (time of day, day of week activity)
  - Resource access patterns (files, systems, applications)
  - Action types and frequencies (read, write, delete, etc.)
  - Session characteristics (duration, idle times, command sequences)
- **Dynamic Updates**: Baselines are continuously and gradually updated to adapt to legitimate changes in behavior

### Anomaly Detection Methods
- **Statistical Analysis**: Z-score calculations for numerical features
- **Pattern Deviation**: Identification of unusual sequences or frequencies
- **Time-Series Analysis**: Detection of temporal anomalies in activity patterns
- **Peer Group Comparison**: Behavior compared to similar role/department users
- **Weighted Scoring**: Different features weighted by reliability and security significance

### Risk Scoring
- **Cumulative Scoring**: Multiple small anomalies can accumulate into significant risk scores
- **Decay Functions**: Risk scores naturally decrease over time without continued anomalies
- **Contextual Adjustment**: Scores adjusted based on resource sensitivity and user role
- **Alert Threshold Customization**: Configurable thresholds by department or role

## Enhanced Features

### Multiple Honeytoken Types
- **File Honeytokens**: 
  - Support for various file types (.docx, .xlsx, .pdf, .txt, .config)
  - Customizable content templates with embedded tracking identifiers
  - Access tracking through specialized hooks in file system monitors
  - Location flexibility - can be deployed anywhere in the filesystem

- **Database Honeytokens**: 
  - Dedicated tables or embedded records in legitimate tables
  - SQL trigger-based access monitoring
  - Supports multiple database types (MySQL, PostgreSQL)
  - Record-level access tracking for precise detection

- **API Key Honeytokens**: 
  - Format-appropriate keys for various services (AWS, GitHub, internal systems)
  - Monitoring at authentication gateways
  - Key rotation and usage tracking
  - Severity classification by apparent permission level

- **Credential Honeytokens**: 
  - Directory integration (LDAP/Active Directory capable)
  - Multi-factor authentication monitoring
  - Login attempt correlation with source IP and user agent
  - Geolocation-based access analysis

### UEBA Capabilities
- **User Behavior Profiling**:
  - Multi-dimensional profiling including temporal, spatial, and resource dimensions
  - Role-based behavior expectations and deviations
  - Machine learning models for pattern recognition (when sufficient data exists)
  - Hierarchical profiling (individual, team, department, organization-wide)

- **Anomaly Detection**:
  - Real-time processing of activities against established baselines
  - Multi-algorithm approach combining statistical and pattern-based methods
  - Confidence scoring for detected anomalies
  - False positive reduction through contextual analysis

- **Risk Scoring**:
  - Compound risk metrics combining multiple behavioral factors
  - Time-weighted scoring with configurable decay functions
  - Differential scoring based on resource sensitivity
  - Trend analysis for gradual behavior changes

- **Baseline Establishment**:
  - Automated baseline computation from historical data
  - Continuous refinement with weighted new observations
  - Seasonal and cyclical pattern recognition
  - Peer group comparison for new users

### Alert Management
- **Real-time Detection**:
  - Sub-second processing of security events
  - Immediate notification for critical alerts
  - Correlation engine to link related events
  - Prioritization based on risk scores and resource sensitivity

- **Multi-channel Notifications**:
  - Email, SMS, webhook support
  - Integration with communication platforms (Slack, Teams)
  - Customizable notification templates
  - Escalation paths for unacknowledged alerts

- **Triage Workflows**:
  - Customizable investigation checklists
  - Evidence collection automation
  - Case management with status tracking
  - Collaboration tools for security team coordination

- **Resolution Tracking**:
  - Audit trail of investigation actions
  - Resolution categorization for trend analysis
  - Post-incident reporting
  - Feedback loop for system improvement

### Forensic Logging
- **Comprehensive Activity Recording**:
  - Full event details including user, resource, action, time, and context
  - Raw data preservation with checksums
  - Immutable logging with cryptographic verification
  - High-resolution timestamps for accurate timeline reconstruction

- **Chain of Custody**:
  - Tamper-evident logging mechanisms
  - Digital signatures for log integrity
  - Access control for forensic data
  - Exportable in court-admissible formats

- **Forensic Reports**:
  - Customizable report templates for different stakeholders
  - Timeline visualization for incident analysis
  - Evidence correlation and linking
  - Expert-friendly data exports for external analysis

- **Incident Reconstruction**:
  - Session replay capabilities
  - Command-by-command analysis
  - Visual activity maps
  - Relationship modeling between actions

### Visualization Dashboard
- **Interactive Monitoring**:
  - Real-time updating metrics and alerts
  - Drill-down capabilities from summary to detail views
  - Customizable dashboard layouts
  - Role-based access to different visualization components

- **Trend Analysis**:
  - Historical comparisons with configurable time ranges
  - Anomaly highlighting with statistical confidence indicators
  - Predictive trend modeling where applicable
  - Seasonal pattern recognition

- **User Risk Overview**:
  - Heat maps of user risk by department/role
  - Individual user risk scorecards
  - Behavior change tracking over time
  - Peer comparison visualizations

- **Alert Management Interface**:
  - Unified alert queue with filtering and sorting
  - Visual alert triage with priority indicators
  - One-click access to related evidence
  - Investigation status tracking

### Offline Mode Capabilities
- **Resilient Data Collection**:
  - Local caching of events during API unavailability
  - Encrypted storage of offline data
  - Bandwidth-efficient synchronization
  - Priority-based processing when connectivity restored

- **Automatic Data Processing**:
  - Transparent integration of offline data upon reconnection
  - Chronological ordering of delayed events
  - Retroactive alert generation for offline periods
  - Conflict resolution for overlapping events

- **Enhanced Reliability**:
  - Heartbeat monitoring of API connectivity
  - Graceful degradation during outages
  - Performance optimization for intermittent connectivity
  - Status notifications for monitoring system health

## System Architecture

```
├── src/
│   ├── api/              # REST API implementation
│   ├── db/               # Database models and connectors
│   ├── models/           # Core system models
│   │   ├── honeytoken.py # Honeytoken implementation
│   │   ├── ueba.py       # UEBA engine
│   │   └── alert.py      # Alert management
│   └── web/              # Web interface
│       ├── static/       # Frontend assets
│       └── templates/    # HTML templates
├── run.py                # Main application runner
├── simulate_user_behavior.py # User activity simulation
└── requirements.txt      # Dependencies
```

## Getting Started

### Prerequisites

- Python 3.7+
- MySQL/MariaDB database
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/honeytoken-ueba-system.git
   cd honeytoken-ueba-system
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the database:
   ```
   mysql -u root -p < src/db/schema.sql
   ```

4. Initialize the system:
   ```
   python run.py --setup
   ```

5. Start the application:
   ```
   python run.py --debug
   ```

### Creating Sample Honeytokens

The system includes a utility script to create sample honeytokens for testing:

```
python create_sample_tokens.py --access
```

This will create various types of honeytokens and simulate accesses to them.

## Usage

### Accessing the Dashboard

The web dashboard is available at http://localhost:5000/ after starting the application.

### API Usage

The system provides a RESTful API for automation and integration. API calls require an API key specified in the X-API-Key header.

Example:
```
curl -H "X-API-Key: honeytoken_api_key_123" http://localhost:5000/api/honeytokens
```

Key API endpoints:
- `/api/honeytokens` - Manage honeytokens
- `/api/alerts` - View and manage alerts
- `/api/users` - User management
- `/api/ueba` - UEBA analysis

### Offline Mode

The system includes an offline mode capability for handling situations when the API service is unavailable:

1. **Automatic Detection**: When the API is unavailable, user behavior simulation automatically switches to offline mode.

2. **Local Storage**: Activity data is stored in JSON files in the `offline_activities/` directory.

3. **Data Processing at Startup**: When the API starts up, it automatically checks for offline activities and processes them.

4. **Manual Processing**: You can also manually process offline activities:
   ```
   python run.py --load-offline
   ```

5. **Simulating in Offline Mode**: Force offline mode in simulations:
   ```
   python simulate_user_behavior.py --offline --suspicious
   ```

This feature ensures continuous monitoring and data collection, even during API downtime or network issues.

## Security Considerations

- **API Key**: Change the default API key before deploying in production
- **Database Credentials**: Use strong, unique credentials for database access
- **Implementation**: Treat the system itself as sensitive and secure access to it
- **Monitoring**: Monitor the honeytoken system itself for unauthorized access

## Use Cases

1. **Detecting Insider Threats**: Identify employees accessing unauthorized data
2. **Finding Compromised Accounts**: Detect when legitimate credentials are misused
3. **Early Breach Detection**: Identify attackers during reconnaissance phase
4. **Security Awareness**: Measure effectiveness of security training

## Advanced Configuration

For production deployments, consider:

1. Using HTTPS for the web interface
2. Implementing stronger authentication
3. Setting up monitoring for the honeytoken system itself
4. Integrating with SIEM or ticketing systems

## Troubleshooting

Common issues:

- Database connection problems
  - Check DB credentials and network connectivity
  - Ensure MariaDB/MySQL service is running

- API authentication failures
  - Verify correct API key is being used
  - Check header format: `X-API-Key: your_key_here`

- Permissions issues
  - Ensure application has write access to logs/ and tmp/ directories

- Offline Activities Not Processing
  - Check that the `offline_activities/` directory exists and is writable
  - Verify that offline activity files follow the correct naming format
  - Run manually with `python run.py --load-offline --debug` to see detailed logs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 