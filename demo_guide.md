# Honeytoken System Demo Guide

## Prerequisites
- Python 3.11
- MariaDB/MySQL
- Required Python packages (see requirements.txt)
- Web browser (Chrome/Firefox recommended)

## Initial Setup
1. Ensure MariaDB service is running
2. Verify database connection:
```bash
mariadb -u root -p123 -e "SELECT VERSION();"
```
3. Check the honeytoken database:
```bash
mariadb -u root -p123 honeytoken_db -e "SHOW TABLES;"
```

## Running the Application
1. Start the Flask application:
```bash
python app.py
```
2. The application will run on http://localhost:5000
3. Default admin credentials:
   - Username: admin
   - Password: admin

## Presentation Script

### Introduction (2-3 minutes)
"Today, I'll demonstrate a honeytoken system designed to detect and monitor insider threats in enterprise environments. What makes our approach unique is how we've integrated honeytokens into a legitimate enterprise portal, making them indistinguishable from real functionality."

### System Overview (3-4 minutes)
1. Show the enterprise portal interface
   - "This is our enterprise portal, which looks and functions like any standard corporate system"
   - "Employees use it daily for legitimate work activities"
   - "The interface is modern, responsive, and follows standard UX patterns"

2. Demonstrate legitimate features
   - Project progress tracking with visual charts
   - Task management system
   - Team collaboration tools
   - Document management
   - HR and IT support functions

### Honeytoken Integration (5-6 minutes)
1. Explain the concept
   - "Honeytokens are strategically placed within normal workflows"
   - "They appear as natural parts of the system"
   - "Each honeytoken is designed to attract specific types of insider behavior"

2. Show example scenarios
   - Sensitive project data access
   - Employee information queries
   - Financial document searches
   - System configuration attempts

### Detection & Monitoring (4-5 minutes)
1. Demonstrate the monitoring system
   - Real-time access logging
   - Pattern analysis
   - Alert generation
   - Incident response workflow

2. Show example alerts
   - Multiple access attempts
   - Unusual search patterns
   - Unauthorized data access

### Security Features (3-4 minutes)
1. Highlight key security measures
   - Access control
   - Activity logging
   - Pattern detection
   - Alert mechanisms

2. Explain response capabilities
   - Immediate notifications
   - Detailed audit trails
   - Incident investigation tools

## Frontend Testing Tutorial

### 1. Legitimate Functionality Testing

#### Dashboard Features
1. Project Progress Chart
   - View project completion percentages
   - Hover over bars to see detailed stats
   - Verify chart responsiveness

2. Task Management
   - View current tasks
   - Update task status
   - Check priority levels
   - View task details

3. Team Activity
   - Check team member status
   - View current activities
   - Monitor real-time updates

4. Quick Actions
   - Create new tasks
   - Schedule meetings
   - Access documents

#### Work Section
1. Performance Metrics
   - Active tasks count
   - Project statistics
   - Completion rates
   - Team size

2. Project Management
   - View active projects
   - Check project details
   - Monitor team assignments

### 2. Honeytoken Testing Scenarios

#### Scenario 1: Curious Employee
1. Access Team Directory
   - Search for specific employees
   - Attempt to view detailed profiles
   - Monitor access logs:
```bash
curl -u admin:admin http://localhost:5000/api/access-logs | grep "employee"
```

#### Scenario 2: Financial Data Access
1. Navigate to HR Portal
   - Access payroll section
   - Attempt to view salary information
   - Check alert triggers:
```bash
curl -u admin:admin http://localhost:5000/api/alerts/check
```

#### Scenario 3: System Access
1. IT Support Section
   - Request system access
   - Attempt database credential access
   - Monitor alerts:
```bash
curl -u admin:admin http://localhost:5000/api/alerts/history
```

#### Scenario 4: Document Snooping
1. Document Center
   - Search for confidential documents
   - Attempt to access technical documentation
   - Check access patterns:
```bash
curl -u admin:admin http://localhost:5000/api/analytics/access-patterns
```

### 3. Monitoring and Analysis

#### Real-time Monitoring
1. Keep monitoring terminal open:
```bash
watch -n 1 'curl -u admin:admin http://localhost:5000/api/alerts'
```

2. Monitor access patterns:
```bash
watch -n 5 'curl -u admin:admin http://localhost:5000/api/analytics/access-patterns'
```

#### Analysis Tools
1. View detailed logs:
```bash
curl -u admin:admin http://localhost:5000/api/access-logs
```

2. Check alert history:
```bash
curl -u admin:admin http://localhost:5000/api/alerts/history
```

3. Analyze patterns:
```bash
curl -u admin:admin http://localhost:5000/api/analytics/access-patterns
```

## Best Practices
1. Regular System Monitoring
   - Check access logs daily
   - Review alert patterns weekly
   - Analyze user behavior patterns monthly

2. Honeytoken Management
   - Rotate honeytokens periodically
   - Update trigger conditions
   - Maintain realistic appearance

3. Incident Response
   - Document all alerts
   - Investigate patterns
   - Update security measures

4. System Maintenance
   - Keep dependencies updated
   - Monitor system performance
   - Backup logs regularly

## Troubleshooting
1. Database Connection Issues
   - Verify MariaDB service status
   - Check connection credentials
   - Validate database permissions

2. Alert System Issues
   - Verify email/Slack configurations
   - Check alert thresholds
   - Monitor notification delivery

3. Performance Issues
   - Check server resources
   - Monitor database queries
   - Review log sizes

## Security Notes
1. Access Control
   - Use strong passwords
   - Implement MFA where possible
   - Regular permission audits

2. Monitoring
   - Regular log review
   - Pattern analysis
   - Anomaly detection

3. Incident Response
   - Clear escalation procedures
   - Documentation requirements
   - Response timelines

## ELK Stack Integration

### Prerequisites
1. Install and configure Elasticsearch:
   ```bash
   # Download and install Elasticsearch
   wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.12.1-linux-x86_64.tar.gz
   tar -xzf elasticsearch-8.12.1-linux-x86_64.tar.gz
   cd elasticsearch-8.12.1/
   
   # Start Elasticsearch
   ./bin/elasticsearch
   ```

2. Install and configure Kibana:
   ```bash
   # Download and install Kibana
   wget https://artifacts.elastic.co/downloads/kibana/kibana-8.12.1-linux-x86_64.tar.gz
   tar -xzf kibana-8.12.1-linux-x86_64.tar.gz
   cd kibana-8.12.1/
   
   # Start Kibana
   ./bin/kibana
   ```

### Setting up Kibana Dashboards
1. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Kibana setup script:
   ```bash
   python setup_kibana.py
   ```

3. Access the Kibana dashboard:
   - Open your browser and navigate to `http://localhost:5601`
   - Click on "Dashboard" in the left sidebar
   - Select "Honeytoken Access Overview"

### Available Visualizations
1. Access Attempts Over Time
   - Line chart showing the frequency of honeytoken access attempts
   - Helps identify patterns and potential attack windows
   - Filter by time range to focus on specific periods

2. Top Accessed Resources
   - Pie chart displaying most frequently accessed honeytoken resources
   - Helps identify which sensitive resources are most targeted
   - Use to adjust security measures and monitoring

### Analyzing Access Patterns
1. Real-time Monitoring
   - Watch the dashboard during testing to see immediate results
   - Observe how different access attempts are logged and visualized
   - Note any patterns in access times or resource types

2. Historical Analysis
   - Review past access attempts to identify trends
   - Use time filters to focus on specific incidents
   - Export data for further analysis or reporting

3. Alert Correlation
   - Compare access patterns with triggered alerts
   - Identify potential false positives or missed detections
   - Use insights to fine-tune alert thresholds

### Best Practices
1. Regular Monitoring
   - Check the dashboard at least daily
   - Set up email alerts for unusual patterns
   - Document any significant findings

2. Dashboard Customization
   - Add new visualizations as needed
   - Adjust time ranges for your use case
   - Create filtered views for different teams

3. Data Retention
   - Configure appropriate retention periods
   - Archive important historical data
   - Clean up old indices regularly

## Testing with Sample Data

### Generating Sample Data
1. Ensure Elasticsearch and Kibana are running
2. Run the sample data generation script:
   ```bash
   python generate_sample_data.py
   ```
   This will create:
   - 7 days of simulated access logs
   - Random alerts based on access patterns
   - Realistic user and resource distributions

### Sample Data Overview
1. Access Logs
   - User IDs: Various employee and system accounts
   - IP Addresses: Internal and localhost
   - Resource Types: Employee data, payroll, admin credentials, system config
   - Access Types: Read operations
   - User Agents: Browser and API clients

2. Alerts
   - Types: Excessive access
   - Severity Levels: Low, medium, high
   - Thresholds: 5, 10, or 15 access attempts
   - Time Windows: 1 hour periods

### Analyzing Sample Data
1. Access Patterns
   - View the "Access Attempts Over Time" visualization
   - Note the distribution of access attempts throughout the day
   - Identify any suspicious patterns or spikes

2. Resource Usage
   - Check the "Top Accessed Resources" chart
   - Compare access frequencies across different resource types
   - Look for unexpected access patterns

3. Alert Analysis
   - Review generated alerts in the Kibana dashboard
   - Correlate alerts with access patterns
   - Evaluate alert threshold effectiveness

### Using Sample Data for Testing
1. Baseline Establishment
   - Use sample data as a baseline for normal behavior
   - Compare real access patterns against the baseline
   - Adjust alert thresholds based on findings

2. Pattern Recognition
   - Practice identifying suspicious patterns
   - Learn to differentiate between normal and anomalous access
   - Test alert configurations against known patterns

3. Dashboard Evaluation
   - Verify all visualizations work as expected
   - Test different time ranges and filters
   - Ensure alerts are properly displayed and categorized