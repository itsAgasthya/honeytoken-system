# Configuration Guide

## Environment Variables

The system uses environment variables for configuration. Copy `.env.example` to `.env` and configure the following settings:

### Flask Configuration
```ini
FLASK_ENV=development
PORT=5000
DEBUG=True
SECRET_KEY=your-secret-key-here
```

- `FLASK_ENV`: Set to `production` in production environment
- `PORT`: Application port (default: 5000)
- `DEBUG`: Enable/disable debug mode
- `SECRET_KEY`: Secret key for session management

### Database Configuration
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password-here
DB_NAME=honeytoken_db
SHADOW_DB_NAME=honeytoken_shadow_db
DB_SSL_CA=/path/to/ssl/cert.pem
```

- `DB_HOST`: MySQL server hostname
- `DB_PORT`: MySQL server port
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_NAME`: Main database name
- `SHADOW_DB_NAME`: Shadow database name for honeytokens
- `DB_SSL_CA`: Path to SSL certificate (if using SSL)

### ELK Stack Configuration
```ini
ELASTICSEARCH_URL=http://localhost:9200
KIBANA_URL=http://localhost:5601
```

- `ELASTICSEARCH_URL`: Elasticsearch endpoint
- `KIBANA_URL`: Kibana dashboard URL

### Alert Configuration
```ini
# Email Alerts
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_RECIPIENTS=admin@yourdomain.com

# Slack Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

- Configure email settings for alert notifications
- Set up Slack webhook for team notifications

### Honeytoken Configuration
```ini
HONEYTOKEN_CHECK_INTERVAL=60
MAX_ALERT_FREQUENCY=300
SUSPICIOUS_ACCESS_THRESHOLD=3
```

- `HONEYTOKEN_CHECK_INTERVAL`: Seconds between honeytoken checks
- `MAX_ALERT_FREQUENCY`: Minimum seconds between alerts
- `SUSPICIOUS_ACCESS_THRESHOLD`: Number of accesses before high-priority alert

## Docker Configuration

### docker-compose.yml

The ELK stack is configured in `docker-compose.yml`:

```yaml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.12.0
    volumes:
      - ./logstash/config:/usr/share/logstash/config
      - ./logstash/pipeline:/usr/share/logstash/pipeline
      - ./logs:/logs

  kibana:
    image: docker.elastic.co/kibana/kibana:8.12.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

### Logstash Configuration

#### logstash.yml
```yaml
http.host: "0.0.0.0"
xpack.monitoring.elasticsearch.hosts: [ "http://elasticsearch:9200" ]
```

#### Pipeline Configuration (honeytoken.conf)
```
input {
  file {
    path => "/logs/access.log"
    codec => json
    type => "honeytoken_access"
  }
  file {
    path => "/logs/alerts.log"
    codec => json
    type => "honeytoken_alert"
  }
}

filter {
  if [type] == "honeytoken_access" {
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    geoip {
      source => "[ip_info][geolocation][ip]"
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "honeytoken-%{type}-%{+YYYY.MM.dd}"
  }
}
```

## Logging Configuration

### Log Levels
```ini
LOG_LEVEL=INFO
LOG_FORMAT=json
```

Available log levels:
- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

### Log Formats
- json: Structured JSON logging
- text: Human-readable format

### Log Files
- `logs/access.log`: Honeytoken access attempts
- `logs/alerts.log`: Security alerts
- `logs/app.log`: Application logs

## Security Configuration

### Admin Authentication
```ini
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me_in_production
```

### SSL/TLS Configuration
For production, configure SSL certificates:
1. Generate certificates
2. Update Flask configuration
3. Configure reverse proxy (nginx/apache)

### Database Security
1. Use strong passwords
2. Enable SSL for database connections
3. Restrict database user permissions
4. Regular backup configuration

## Monitoring Configuration

### Process Monitoring
- Configure process name patterns to monitor
- Set up network connection tracking
- Configure file system monitoring paths

### Alert Thresholds
- Set access frequency thresholds
- Configure geographical restrictions
- Define suspicious user agent patterns

## Backup Configuration

### Database Backups
1. Configure backup schedule
2. Set retention period
3. Define backup location

### Log Rotation
1. Configure log rotation policy
2. Set maximum log size
3. Define retention period

## Production Deployment

### System Requirements
- 2+ CPU cores
- 4GB+ RAM
- 20GB+ storage
- Linux-based OS

### Performance Tuning
1. Adjust Elasticsearch heap size
2. Configure Logstash workers
3. Optimize MySQL configuration
4. Set up caching

### Monitoring
1. Configure resource monitoring
2. Set up alerting for system issues
3. Monitor disk space usage

### Security Hardening
1. Enable firewall rules
2. Configure rate limiting
3. Set up intrusion detection
4. Regular security updates 