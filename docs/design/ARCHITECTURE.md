# System Architecture

## High-Level Architecture Diagram

```mermaid
graph TB
    subgraph Client Layer
        WUI[Web UI]
        API[API Endpoints]
    end

    subgraph Application Layer
        FM[Flask Middleware]
        AUTH[Authentication]
        HM[Honeytoken Manager]
        AM[Alert Manager]
        PM[Process Monitor]
    end

    subgraph Data Layer
        MD[(Main Database)]
        SD[(Shadow Database)]
        ELK[ELK Stack]
        subgraph ELK Stack
            ES[Elasticsearch]
            LS[Logstash]
            KB[Kibana]
        end
    end

    subgraph Monitoring Layer
        FSM[File System Monitor]
        NM[Network Monitor]
        PM[Process Monitor]
    end

    subgraph Alert Layer
        EMAIL[Email Alerts]
        SLACK[Slack Alerts]
        DASH[Dashboard Alerts]
    end

    %% Client Layer Connections
    WUI --> FM
    API --> FM
    
    %% Application Layer Connections
    FM --> AUTH
    FM --> HM
    FM --> AM
    
    %% Data Layer Connections
    HM --> MD
    HM --> SD
    AM --> ELK
    
    %% ELK Stack Internal
    LS --> ES
    ES --> KB
    
    %% Monitoring Layer Connections
    FSM --> LS
    NM --> LS
    PM --> LS
    
    %% Alert Layer Connections
    AM --> EMAIL
    AM --> SLACK
    AM --> DASH

    %% Data Flow Styles
    classDef primary fill:#4a154b,stroke:#333,stroke-width:2px,color:#ffffff
    classDef secondary fill:#1a73e8,stroke:#333,stroke-width:1px,color:#ffffff
    class WUI,API,FM primary
    class AUTH,HM,AM secondary
```

## Component Details

### 1. Client Layer
- **Web UI**: Administrative interface for honeytoken management
- **API Endpoints**: RESTful API for system integration

### 2. Application Layer
- **Flask Middleware**: Request handling and routing
- **Authentication**: JWT-based access control
- **Honeytoken Manager**: Honeytoken lifecycle management
- **Alert Manager**: Alert generation and distribution
- **Process Monitor**: System process monitoring

### 3. Data Layer
- **Main Database**: Production database
- **Shadow Database**: Honeytoken storage
- **ELK Stack**:
  - Elasticsearch: Log storage and search
  - Logstash: Log processing and enrichment
  - Kibana: Visualization and analysis

### 4. Monitoring Layer
- **File System Monitor**: File access tracking
- **Network Monitor**: Connection tracking
- **Process Monitor**: Process activity monitoring

### 5. Alert Layer
- **Email Alerts**: SMTP-based notifications
- **Slack Alerts**: Webhook integration
- **Dashboard Alerts**: Real-time web interface

## Data Flow

1. **Honeytoken Access**:
   ```mermaid
   sequenceDiagram
       participant User
       participant System
       participant Monitor
       participant Logger
       participant Alert
       
       User->>System: Access Data
       System->>Monitor: Check Access
       Monitor->>Logger: Log Access
       Logger->>Alert: Evaluate Threat
       Alert-->>System: Notification
   ```

2. **Alert Generation**:
   ```mermaid
   sequenceDiagram
       participant Monitor
       participant Analyzer
       participant Alert
       participant Notification
       
       Monitor->>Analyzer: Access Data
       Analyzer->>Alert: Evaluate Threat
       Alert->>Notification: Generate Alert
       Notification-->>Alert: Confirmation
   ```

## Security Architecture

### 1. Authentication Flow
```mermaid
sequenceDiagram
    participant User
    participant API
    participant Auth
    participant DB
    
    User->>API: Login Request
    API->>Auth: Validate Credentials
    Auth->>DB: Check User
    DB-->>Auth: User Data
    Auth-->>API: JWT Token
    API-->>User: Token Response
```

### 2. Monitoring Flow
```mermaid
sequenceDiagram
    participant System
    participant Monitor
    participant Logger
    participant Analyzer
    participant Alert
    
    System->>Monitor: Activity
    Monitor->>Logger: Raw Data
    Logger->>Analyzer: Structured Data
    Analyzer->>Alert: Threat Level
    Alert-->>System: Notification
```

## Network Architecture

```mermaid
graph LR
    subgraph Internal Network
        APP[Application Server]
        DB[(Databases)]
        ELK[ELK Stack]
    end
    
    subgraph DMZ
        LB[Load Balancer]
        WAF[Web Application Firewall]
    end
    
    subgraph External
        USER[Users]
        API[API Clients]
    end
    
    USER --> WAF
    API --> WAF
    WAF --> LB
    LB --> APP
    APP --> DB
    APP --> ELK
```

## Deployment Architecture

```mermaid
graph TB
    subgraph Production
        LB[Load Balancer]
        APP1[App Server 1]
        APP2[App Server 2]
        DB[(Database)]
        ELK[ELK Stack]
    end
    
    subgraph Monitoring
        MON[Monitoring Server]
        LOG[Log Server]
    end
    
    LB --> APP1
    LB --> APP2
    APP1 --> DB
    APP2 --> DB
    APP1 --> ELK
    APP2 --> ELK
    ELK --> MON
    ELK --> LOG
``` 