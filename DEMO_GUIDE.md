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

# Verify pip and virtual environment
python -m pip --version
python -m venv --help
```

### 1.2 Initialize Python Environment
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools wheel

# Install core dependencies first
pip install Flask==3.0.2 mysql-connector-python==8.3.0 python-dotenv==1.0.1 requests==2.31.0

# Install database dependencies
pip install SQLAlchemy>=2.0.27 alembic==1.13.1 mysqlclient==2.2.4

# Install ELK stack dependencies
pip install elasticsearch==8.12.1 elasticsearch-dsl==8.17.1 python-logstash==0.4.8

# Install remaining dependencies
pip install -r requirements.txt

# Verify critical packages
python -c "
import sqlalchemy
import elasticsearch
import elasticsearch_dsl
import python_logstash
print(f'Python packages verified:\n\
- SQLAlchemy: {sqlalchemy.__version__}\n\
- Elasticsearch: {elasticsearch.__version__}\n\
- Elasticsearch-DSL: {elasticsearch_dsl.__version__}\n\
- Python-Logstash: {python_logstash.__version__}')"
```

### 1.3 Database Setup
```bash
# Create MySQL databases
mysql -u root -p <<EOF
CREATE DATABASE IF NOT EXISTS honeytoken_db;
CREATE DATABASE IF NOT EXISTS honeytoken_shadow_db;
GRANT ALL PRIVILEGES ON honeytoken_db.* TO 'honeytoken_user'@'localhost';
GRANT ALL PRIVILEGES ON honeytoken_shadow_db.* TO 'honeytoken_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Initialize SQLAlchemy migrations
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Verify database setup
python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine('mysql://honeytoken_user@localhost/honeytoken_db')
Session = sessionmaker(bind=engine)
session = Session()
print('Database connection successful')"
```

### 1.4 Configure Logging
```bash
# Create logging directory
mkdir -p logs/elk

# Test Logstash connection
python -c "
import logging
import python_logstash
test_logger = logging.getLogger('python-logstash-logger')
test_logger.setLevel(logging.INFO)
test_logger.addHandler(python_logstash.LogstashHandler('localhost', 5959, version=1))
test_logger.info('Test message from Honeytoken System')"
```

### 1.5 Start ELK Stack
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

### 1.6 Verify Services
```bash
# Test Elasticsearch health
curl -X GET "localhost:9200/_cluster/health?pretty"
# Expected output should show status: "green" or "yellow"

# Test Kibana status
curl -X GET "localhost:5601/api/status"
# Should return HTTP 200 OK
```

### 1.7 Initialize Application
```bash
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
1. **Package Installation Issues**
   ```bash
   # Clear pip cache and temporary files
   pip cache purge
   rm -rf ~/.cache/pip
   
   # Install packages in order with verbose output
   pip install --verbose Flask==3.0.2
   pip install --verbose SQLAlchemy>=2.0.27
   pip install --verbose elasticsearch==8.12.1
   pip install --verbose elasticsearch-dsl==8.17.1
   pip install --verbose python-logstash==0.4.8
   
   # For SQLAlchemy issues with Python 3.13
   pip install --upgrade SQLAlchemy>=2.0.27
   
   # For MySQL connection issues
   pip install mysqlclient==2.2.4
   
   # If specific packages fail, try alternatives
   # For Logstash issues:
   pip install python-logstash-async  # Alternative logging package
   # OR use direct TCP socket logging
   python -c "
   import socket
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   s.connect(('localhost', 5959))
   s.send(b'Test log message\n')
   s.close()"
   
   # Verify package compatibility
   pip check
   
   # List all installed packages
   pip freeze > installed_packages.txt
   ```

2. **Database Connection Issues**
   ```bash
   # Check MySQL service
   sudo systemctl status mysql
   
   # Verify MySQL connection
   mysql -u honeytoken_user -p -e "SELECT VERSION();"
   
   # Test SQLAlchemy connection
   python -c "
   from sqlalchemy import create_engine
   engine = create_engine('mysql://honeytoken_user@localhost/honeytoken_db')
   connection = engine.connect()
   print('Connection successful')
   connection.close()"
   
   # Reset MySQL password if needed
   sudo mysql -u root
   ALTER USER 'honeytoken_user'@'localhost' IDENTIFIED BY 'new_password';
   FLUSH PRIVILEGES;
   ```

3. **Elasticsearch Fails to Start**
   ```bash
   # 1. Check error details
   sudo systemctl status elasticsearch.service
   sudo journalctl -xeu elasticsearch.service
   
   # 2. Check system resources and limits
   free -h  # Verify available memory
   df -h    # Check disk space
   ulimit -a  # Check system limits
   
   # 3. Fix common permission issues
   sudo chown -R elasticsearch:elasticsearch /var/lib/elasticsearch
   sudo chown -R elasticsearch:elasticsearch /var/log/elasticsearch
   sudo chmod 2750 /var/lib/elasticsearch
   sudo chmod 2750 /var/log/elasticsearch
   
   # 4. Verify Elasticsearch configuration
   sudo nano /etc/elasticsearch/elasticsearch.yml
   # Required settings:
   # cluster.name: honeytoken-cluster
   # node.name: node-1
   # path.data: /var/lib/elasticsearch
   # path.logs: /var/log/elasticsearch
   # network.host: localhost
   # http.port: 9200
   # discovery.type: single-node
   
   # 5. Check JVM settings
   sudo nano /etc/elasticsearch/jvm.options
   # Ensure these settings:
   # -Xms512m
   # -Xmx512m
   
   # 6. Try running Elasticsearch manually to see detailed errors
   sudo -u elasticsearch /usr/share/elasticsearch/bin/elasticsearch
   
   # 7. If system service still fails, use Docker alternative
   docker pull docker.elastic.co/elasticsearch/elasticsearch:7.17.14
   docker run -d --name elasticsearch \
     -p 9200:9200 -p 9300:9300 \
     -e "discovery.type=single-node" \
     -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
     -v elasticsearch-data:/usr/share/elasticsearch/data \
     docker.elastic.co/elasticsearch/elasticsearch:7.17.14
   
   # 8. Verify Docker container is running
   docker ps | grep elasticsearch
   docker logs elasticsearch
   ```

4. **Monitor Daemon Issues**
   ```bash
   # Check if process is running
   ps aux | grep monitor_daemon
   
   # View logs
   tail -f logs/monitor.log
   
   # Check Elasticsearch connection from daemon
   curl -X GET "localhost:9200/_cluster/health?pretty"
   
   # Restart daemon with debug logging
   pkill -f monitor_daemon.py
   python scripts/monitor_daemon.py --debug &
   ```

5. **Port Conflicts**
   ```