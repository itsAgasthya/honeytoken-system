-- Honeytoken System Database Schema

-- Drop database if exists and create a new one
DROP DATABASE IF EXISTS honeytoken_ueba;
CREATE DATABASE honeytoken_ueba;
USE honeytoken_ueba;

-- Create Users table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    department VARCHAR(50) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create Honeytokens table
CREATE TABLE honeytokens (
    token_id INT AUTO_INCREMENT PRIMARY KEY,
    token_name VARCHAR(100) NOT NULL,
    token_type ENUM('file', 'database', 'api_key', 'credentials', 'document') NOT NULL,
    token_value TEXT NOT NULL,
    token_location TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    sensitivity_level ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    expected_access_pattern TEXT
);

-- Create UserActivity table for UEBA
CREATE TABLE user_activities (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    activity_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    resource_accessed VARCHAR(255),
    action_details TEXT,
    session_id VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create HoneytokenAccess table
CREATE TABLE honeytoken_access (
    access_id INT AUTO_INCREMENT PRIMARY KEY,
    token_id INT NOT NULL,
    user_id INT,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_method VARCHAR(50),
    additional_context TEXT,
    is_authorized BOOLEAN DEFAULT FALSE,
    access_duration INT DEFAULT 0,  -- Duration in seconds
    FOREIGN KEY (token_id) REFERENCES honeytokens(token_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create Alerts table
CREATE TABLE alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    token_id INT,
    user_id INT,
    access_id INT,
    alert_type ENUM('access', 'unusual_behavior', 'multiple_access', 'unauthorized') NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by INT,
    resolution_notes TEXT,
    forensic_evidence TEXT,
    FOREIGN KEY (token_id) REFERENCES honeytokens(token_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (access_id) REFERENCES honeytoken_access(access_id),
    FOREIGN KEY (resolved_by) REFERENCES users(user_id)
);

-- Create BehavioralBaselines table for UEBA
CREATE TABLE behavioral_baselines (
    baseline_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value FLOAT NOT NULL,
    confidence_score FLOAT DEFAULT 0.8,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE KEY user_feature (user_id, feature_name)
);

-- Create AnomalyScores table for UEBA
CREATE TABLE anomaly_scores (
    anomaly_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    activity_id INT NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    expected_value FLOAT,
    actual_value FLOAT,
    anomaly_score FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (activity_id) REFERENCES user_activities(activity_id)
);

-- Create ForensicLogs table for detailed forensic evidence
CREATE TABLE forensic_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    alert_id INT,
    access_id INT,
    log_type ENUM('system', 'network', 'file', 'database', 'application') NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(255) NOT NULL,
    log_data TEXT NOT NULL,
    hash_value VARCHAR(255),  -- For integrity verification
    FOREIGN KEY (alert_id) REFERENCES alerts(alert_id),
    FOREIGN KEY (access_id) REFERENCES honeytoken_access(access_id)
);

-- Create AuditTrail table for system auditing
CREATE TABLE audit_trail (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Insert some initial data for testing
INSERT INTO users (username, email, department, role) VALUES
('admin', 'admin@example.com', 'IT', 'Administrator'),
('jsmith', 'jsmith@example.com', 'Finance', 'Analyst'),
('apatil', 'apatil@example.com', 'HR', 'Manager'),
('rjones', 'rjones@example.com', 'Engineering', 'Developer');

-- Create views for easy querying
CREATE VIEW active_honeytokens AS
SELECT * FROM honeytokens WHERE is_active = TRUE;

CREATE VIEW unresolved_alerts AS
SELECT a.*, h.token_name, h.token_type, u.username
FROM alerts a
JOIN honeytokens h ON a.token_id = h.token_id
LEFT JOIN users u ON a.user_id = u.user_id
WHERE a.is_resolved = FALSE;

CREATE VIEW user_risk_scores AS
SELECT 
    u.user_id,
    u.username,
    COUNT(a.alert_id) AS total_alerts,
    SUM(CASE WHEN a.severity = 'critical' THEN 4
             WHEN a.severity = 'high' THEN 3
             WHEN a.severity = 'medium' THEN 2
             WHEN a.severity = 'low' THEN 1
             ELSE 0 END) AS risk_score
FROM users u
LEFT JOIN alerts a ON u.user_id = a.user_id
GROUP BY u.user_id, u.username;

-- Create indexes for performance
CREATE INDEX idx_user_activities_user ON user_activities(user_id);
CREATE INDEX idx_user_activities_timestamp ON user_activities(timestamp);
CREATE INDEX idx_honeytoken_access_token ON honeytoken_access(token_id);
CREATE INDEX idx_honeytoken_access_time ON honeytoken_access(access_time);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX idx_alerts_severity ON alerts(severity); 