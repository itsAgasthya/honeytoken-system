# API Documentation

## Authentication

All API endpoints require authentication using JWT tokens. To obtain a token:

```
POST /api/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "your-password"
}
```

Include the token in subsequent requests:
```
Authorization: Bearer <your-token>
```

## Honeytoken Management

### List Honeytokens

```
GET /api/honeytokens
```

Response:
```json
{
    "honeytokens": [
        {
            "id": 1,
            "type": "database_credentials",
            "created_at": "2025-03-14T18:00:00Z",
            "last_accessed": "2025-03-14T18:30:00Z",
            "access_count": 5
        }
    ]
}
```

### Create Honeytoken

```
POST /api/honeytokens
Content-Type: application/json

{
    "type": "database_credentials",
    "data": {
        "username": "user123",
        "password": "pass123"
    }
}
```

### Delete Honeytoken

```
DELETE /api/honeytokens/{id}
```

## Access Logs

### Get Access Logs

```
GET /api/logs/access
```

Query parameters:
- `start_date`: ISO date
- `end_date`: ISO date
- `type`: Log type (access, alert)
- `limit`: Number of records (default 100)

Response:
```json
{
    "logs": [
        {
            "timestamp": "2025-03-14T18:44:15Z",
            "token_id": 1,
            "ip_address": "192.168.1.1",
            "user_agent": "curl/7.64.1",
            "geolocation": {
                "country": "US",
                "city": "New York"
            }
        }
    ]
}
```

### Get Alert Logs

```
GET /api/logs/alerts
```

Response:
```json
{
    "alerts": [
        {
            "timestamp": "2025-03-14T18:44:15Z",
            "severity": "high",
            "message": "Multiple access attempts detected",
            "token_id": 1,
            "details": {
                "access_count": 5,
                "time_window": "5m"
            }
        }
    ]
}
```

## Forensics

### Get Process Information

```
GET /api/forensics/processes
```

Response:
```json
{
    "processes": [
        {
            "pid": 1234,
            "name": "python",
            "username": "user",
            "cmdline": ["python", "script.py"],
            "connections": [
                {
                    "local_addr": "127.0.0.1:8080",
                    "remote_addr": "192.168.1.1:443",
                    "status": "ESTABLISHED"
                }
            ]
        }
    ]
}
```

### Get File Activity

```
GET /api/forensics/files
```

Response:
```json
{
    "file_activity": [
        {
            "timestamp": "2025-03-14T18:44:15Z",
            "path": "/path/to/file",
            "operation": "read",
            "process_id": 1234
        }
    ]
}
```

## Statistics

### Get Access Statistics

```
GET /api/stats/access
```

Response:
```json
{
    "total_access": 100,
    "unique_ips": 25,
    "top_tokens": [
        {
            "id": 1,
            "access_count": 30
        }
    ],
    "top_user_agents": [
        {
            "user_agent": "curl/7.64.1",
            "count": 45
        }
    ]
}
```

### Get Alert Statistics

```
GET /api/stats/alerts
```

Response:
```json
{
    "total_alerts": 50,
    "by_severity": {
        "high": 10,
        "medium": 20,
        "low": 20
    },
    "top_tokens": [
        {
            "id": 1,
            "alert_count": 15
        }
    ]
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
    "error": "Invalid request parameters",
    "details": "Specific error message"
}
```

### 401 Unauthorized
```json
{
    "error": "Authentication required",
    "details": "Invalid or missing token"
}
```

### 403 Forbidden
```json
{
    "error": "Permission denied",
    "details": "Insufficient privileges"
}
```

### 404 Not Found
```json
{
    "error": "Resource not found",
    "details": "Specific resource details"
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal server error",
    "details": "Error details"
}
``` 