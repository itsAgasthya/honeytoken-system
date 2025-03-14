# Honeytoken System Demo Guide

## Prerequisites
- Python 3.11 or higher
- MySQL Server
- Elasticsearch and Kibana
- All dependencies installed from `requirements.txt`

## 1. System Setup (5 minutes)
```bash
# Start Elasticsearch and Kibana
sudo systemctl start elasticsearch
sudo systemctl start kibana

# Verify services are running
curl http://localhost:9200/_cluster/health
curl http://localhost:5601/api/status

# Start the monitoring daemon
sudo systemctl start honeytoken-monitor
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
1. **Elasticsearch Not Responding**
   ```bash
   sudo systemctl restart elasticsearch
   ```

2. **Monitor Daemon Issues**
   ```bash
   sudo systemctl status honeytoken-monitor
   journalctl -u honeytoken-monitor
   ```

3. **Database Connection Issues**
   ```bash
   mysql -u root -p honeytoken_db -e "SELECT 1"
   ```

### Backup Demo Data
Keep these ready in case of demo issues:
- Sample access logs in `logs/access`
- Pre-generated alerts in `logs/alerts`
- Process analysis data in `logs/process_info.json`
- Performance metrics in `logs/performance_metrics.json`

## Post-Demo Cleanup
```bash
# Stop monitoring
sudo systemctl stop honeytoken-monitor

# Clear test data
python scripts/test_system.py cleanup

# Stop services
sudo systemctl stop elasticsearch
sudo systemctl stop kibana
``` 