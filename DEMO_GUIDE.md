# Honeytoken System Demo Guide

## Prerequisites
- Python 3.11 or higher
- MySQL Server
- Docker and Docker Compose (recommended) or Elasticsearch and Kibana installed locally
- All dependencies installed from `requirements.txt`

## 1. System Setup (10 minutes)

### 1.1 Verify Environment
```bash
# Check Python version
python --version  # Should be 3.11 or higher

# Verify MySQL is running
sudo systemctl status mysql
mysql -u root -p -e "SELECT VERSION();"

# Check Docker status (if using Docker)
docker --version
docker-compose --version
```

### 1.2 Start ELK Stack
Option 1 - Using Docker (Recommended):
```bash
# Start ELK stack using Docker
docker-compose up -d elasticsearch kibana

# Wait for services to be ready (usually takes 1-2 minutes)
docker-compose ps  # Check status
```

Option 2 - Using System Services:
```bash
# Start Elasticsearch
sudo systemctl start elasticsearch
# Verify Elasticsearch status
sudo systemctl status elasticsearch
# If failed, check logs
sudo journalctl -xeu elasticsearch.service

# Start Kibana after Elasticsearch is running
sudo systemctl start kibana
```

### 1.3 Verify Services
```bash
# Test Elasticsearch health
curl -X GET "localhost:9200/_cluster/health?pretty"
# Expected output should show status: "green" or "yellow"

# Test Kibana status
curl -X GET "localhost:5601/api/status"
# Should return HTTP 200 OK
```

### 1.4 Initialize Application
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Start the monitoring daemon
python scripts/monitor_daemon.py &
```

## 2. Shadow Database Demo (10 minutes)

### 2.1 Generate Honeytokens
```bash
python scripts/test_system.py monitoring
```
Expected output: Confirmation of active monitoring system components

### 2.2 View Active Honeytokens
- Access the web dashboard at http://localhost:5000
- Navigate to "Honeytokens" section
- Observe different token types and their configurations

## 3. Detection System Demo (15 minutes)

### 3.1 Simulate Unauthorized Access
```bash
python scripts/test_system.py unauthorized_access
```
Expected output: Multiple access logs and triggered alerts

### 3.2 Process Analysis
```bash
python scripts/process_analyzer.py --show-tree
```
Expected output: Hierarchical view of processes with potential suspicious activities

### 3.3 Access Pattern Analysis
```bash
python scripts/analyze_patterns.py --show-recent
```
Expected output:
- Token access summary
- IP address summary
- User activity patterns
- Hourly distribution
- Detected anomalies

## 4. Performance Monitoring (10 minutes)

### 4.1 Live System Metrics
```bash
python scripts/performance_monitor.py --live
```
Expected output:
- Real-time CPU, memory, and disk usage
- Elasticsearch cluster health
- Detection system performance

### 4.2 Accuracy Analysis
```bash
python scripts/analyze_accuracy.py --last-24h
```
Expected output:
- Overall detection accuracy
- False positive rates
- Detection timing by token type

## 5. Kibana Dashboards (10 minutes)

### 5.1 Access Overview Dashboard
- URL: http://localhost:5601
- Navigate to "Dashboards" → "Overview"
- Demonstrate:
  - Access patterns visualization
  - Geographic distribution of access
  - Token type distribution

### 5.2 Alert Investigation
- Navigate to "Dashboards" → "Alerts"
- Show:
  - Real-time alert feed
  - Alert severity distribution
  - Response time metrics

### 5.3 Forensics Dashboard
- Navigate to "Dashboards" → "Forensics"
- Demonstrate:
  - Process relationship graphs
  - Network connection analysis
  - File activity timeline

## Troubleshooting

### Common Issues
1. **Elasticsearch Fails to Start**
   ```bash
   # Check system resources
   free -h  # Verify available memory
   df -h    # Check disk space
   
   # Verify Elasticsearch configuration
   sudo nano /etc/elasticsearch/elasticsearch.yml
   # Ensure these settings:
   # - Xms512m
   # - Xmx512m
   # - network.host: localhost
   
   # Try Docker alternative if system service fails
   docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 \
     -e "discovery.type=single-node" \
     docker.elastic.co/elasticsearch/elasticsearch:7.17.14
   ```

2. **Monitor Daemon Issues**
   ```bash
   # Check if process is running
   ps aux | grep monitor_daemon
   
   # View logs
   tail -f logs/monitor.log
   
   # Restart daemon
   pkill -f monitor_daemon.py
   python scripts/monitor_daemon.py &
   ```

3. **Database Connection Issues**
   ```bash
   # Check MySQL service
   sudo systemctl status mysql
   
   # Verify credentials
   mysql -u root -p -e "SELECT 1;"
   
   # Check database exists
   mysql -u root -p -e "SHOW DATABASES;"
   ```

4. **Port Conflicts**
   ```bash
   # Check ports in use
   sudo lsof -i :9200  # Elasticsearch
   sudo lsof -i :5601  # Kibana
   sudo lsof -i :3306  # MySQL
   
   # Kill conflicting processes if needed
   sudo kill -9 <PID>
   ```

### Backup Demo Data
Keep these ready in case of demo issues:
- Sample access logs in `logs/access`
- Pre-generated alerts in `logs/alerts`
- Process analysis data in `logs/process_info.json`
- Performance metrics in `logs/performance_metrics.json`

### Quick Recovery Steps
```bash
# 1. Reset environment
./scripts/reset_environment.sh

# 2. Load backup data
./scripts/load_backup_data.sh

# 3. Restart core services
docker-compose restart  # If using Docker
# OR
sudo systemctl restart elasticsearch kibana  # If using system services
```

## Post-Demo Cleanup
```bash
# Stop monitoring daemon
pkill -f monitor_daemon.py

# Clear test data
python scripts/test_system.py cleanup

# Stop services (Docker)
docker-compose down

# OR Stop services (System)
sudo systemctl stop elasticsearch
sudo systemctl stop kibana

# Deactivate virtual environment
deactivate
``` 