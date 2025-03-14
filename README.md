# Honeytoken System for Insider Threat Detection

A sophisticated honeytoken-based system for detecting and monitoring insider threats in database systems. This project implements multiple layers of deception and monitoring to track unauthorized access attempts and potential data breaches.

## Features

- **Honeytoken Management**
  - Shadow database with honeytoken data
  - Multiple honeytoken types (credentials, API keys, tokens)
  - Automated honeytoken generation and distribution

- **Real-time Monitoring**
  - ELK Stack integration for log analysis
  - IP geolocation tracking
  - User agent analysis
  - Process and network monitoring

- **Alert System**
  - Multi-channel notifications (Email, Slack)
  - Configurable alert thresholds
  - Severity-based classification

- **Forensics**
  - Comprehensive access logging
  - Process monitoring
  - Network connection tracking
  - File system activity monitoring

## Prerequisites

- Python 3.11 or 3.12 (Note: Not compatible with Python 3.13)
- Docker and Docker Compose
- MySQL Server
- Git

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd honeytoken-system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
.\venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and configuration
```

5. Start the ELK Stack:
```bash
docker-compose up -d
```

6. Initialize the databases:
```bash
python scripts/init_db.py
```

7. Start the Flask application:
```bash
python app.py
```

8. Access the services:
- Web Interface: http://localhost:5000
- Kibana: http://localhost:5601
- Elasticsearch: http://localhost:9200

## Project Structure

```
honeytoken_system/
├── app/                    # Main application directory
│   ├── __init__.py        # Application initialization
│   ├── models/            # Database models
│   ├── routes/            # API routes and views
│   ├── templates/         # HTML templates
│   └── static/            # Static files (CSS, JS)
├── scripts/               # Utility scripts
├── config/               # Configuration files
├── logs/                 # Log files
├── docker-compose.yml    # Docker services configuration
├── logstash/            # Logstash configuration
│   ├── config/          # Logstash main config
│   └── pipeline/        # Logstash pipeline definitions
└── tests/               # Test files
```

## Testing

1. Generate test data:
```bash
python test_logs.py
```

2. View logs in Kibana:
- Go to http://localhost:5601
- Create index patterns:
  - honeytoken-access-*
  - honeytoken-alerts-*
  - honeytoken-logs-*
- Use Discover to view logs
- Create visualizations and dashboards

## Security Considerations

- All honeytokens are clearly marked in the shadow database
- Logging is compliant with privacy regulations
- No actual sensitive data is used in the system
- Regular cleanup of old honeytoken data
- Encrypted communications
- Access control for admin interface
- Audit logging of system actions

## Troubleshooting

1. **ELK Stack Issues**
   - Ensure Docker is running
   - Check container logs: `docker-compose logs`
   - Verify Elasticsearch is running: `curl http://localhost:9200`
   - Check Logstash pipeline: `docker-compose logs logstash`

2. **Database Issues**
   - Verify MySQL is running
   - Check database connections in .env
   - Ensure proper permissions are set

3. **Application Issues**
   - Check app logs in logs/
   - Verify all required services are running
   - Ensure Python version compatibility

## Documentation

- [Presentation Guide](PRESENTATION_GUIDE.md) - Detailed guide for project demonstration
- [API Documentation](docs/API.md) - API endpoints and usage
- [Configuration Guide](docs/CONFIGURATION.md) - Detailed configuration options

## Contributing

This is a college project for educational purposes. Please ensure all contributions follow secure coding practices and include appropriate documentation.

## License

MIT License - See LICENSE file for details 