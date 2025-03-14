# Honeytoken System for Insider Threat Detection - Presentation Guide

## Project Overview

The Honeytoken System is a sophisticated security solution designed to detect and monitor potential insider threats within an organization. It uses deceptive data (honeytokens) strategically placed in databases and systems to track unauthorized access attempts and identify potential data breaches.

### Key Components

1. **Honeytoken Management**
   - Shadow database containing honeytoken data
   - Multiple types of honeytokens (credentials, API keys, tokens)
   - Automated honeytoken generation and distribution

2. **Monitoring System**
   - Real-time access tracking
   - IP geolocation and user agent analysis
   - Behavioral pattern detection
   - Integration with ELK Stack for log analysis

3. **Alert System**
   - Multi-channel notifications (Email, Slack)
   - Configurable alert thresholds
   - Severity-based alert classification

4. **Forensics Capabilities**
   - Detailed access logs
   - Process monitoring
   - Network connection tracking
   - File system activity monitoring

## Demo Steps

### 1. Initial Setup (5 minutes)
```bash
# Start the ELK stack
docker-compose up -d

# Verify services are running
docker ps

# Check Elasticsearch status
curl http://localhost:9200
```

### 2. Database Setup (5 minutes)
```bash
# Initialize the databases
python scripts/init_db.py

# Verify the shadow database
mysql -u root -p honeytoken_shadow_db
```

### 3. Application Demo (10 minutes)

a. Start the Flask application:
```bash
python app.py
```

b. Show the admin interface:
- Navigate to http://localhost:5000/admin
- Login with admin credentials
- Demonstrate honeytoken management

c. Generate test data:
```bash
python test_logs.py
```

### 4. Monitoring Demo (10 minutes)

a. Access Kibana:
- Open http://localhost:5601
- Show the Discover page
- Demonstrate index patterns:
  - honeytoken-access-*
  - honeytoken-alerts-*
  - honeytoken-logs-*

b. Show visualizations:
- Access patterns over time
- Geolocation of access attempts
- User agent distribution
- Alert frequency

### 5. Forensics Demo (5 minutes)
- Show detailed log analysis
- Demonstrate process monitoring
- Display network connection tracking
- Present file system activity logs

## Common Questions and Answers

### Technical Questions

1. **Q: How do you prevent false positives?**
   A: The system uses multiple validation layers:
   - Access pattern analysis
   - IP reputation checking
   - User agent verification
   - Threshold-based alerting

2. **Q: How do you handle legitimate accidental access?**
   A: The system:
   - Maintains detailed context for each access
   - Uses severity classification
   - Allows manual verification
   - Supports alert suppression for known patterns

3. **Q: What makes this solution better than traditional monitoring?**
   A: Key advantages:
   - Proactive threat detection
   - Low false-positive rate
   - Rich context collection
   - Real-time alerting
   - Forensic data preservation

### Security Questions

1. **Q: How do you protect the honeytoken system itself?**
   A: Multiple security layers:
   - Separate shadow database
   - Encrypted communications
   - Access control for admin interface
   - Audit logging of system actions

2. **Q: What happens if an attacker discovers it's a honeytoken?**
   A: The system:
   - Still provides valuable intelligence
   - Tracks attacker behavior
   - Collects forensic data
   - May serve as a deterrent

### Implementation Questions

1. **Q: How scalable is the solution?**
   A: The system is designed for scalability:
   - ELK Stack can handle large volumes
   - Distributed architecture
   - Configurable retention policies
   - Optimized log processing

2. **Q: How do you maintain the honeytokens?**
   A: Through automated processes:
   - Regular rotation
   - Validity checking
   - Access pattern analysis
   - Automated cleanup

## Key Points to Emphasize

1. **Security Benefits**
   - Early threat detection
   - Insider threat monitoring
   - Attack pattern analysis
   - Forensic evidence collection

2. **Technical Innovation**
   - ELK Stack integration
   - Real-time monitoring
   - Multi-layer detection
   - Comprehensive logging

3. **Practical Application**
   - Easy deployment
   - Low maintenance
   - Actionable alerts
   - Valuable intelligence

## Backup Demo Data

Keep these ready in case of demo issues:
- Snapshot of ELK indices
- Sample log files
- Pre-configured visualizations
- Test account credentials 