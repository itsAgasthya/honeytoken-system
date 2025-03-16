-- Create main database
CREATE DATABASE IF NOT EXISTS honeytoken_db;

-- Create shadow database
CREATE DATABASE IF NOT EXISTS honeytoken_shadow_db;

-- Use main database
USE honeytoken_db;

-- Create tables (these will be managed by Flask-Migrate, but this is for reference)
CREATE TABLE IF NOT EXISTS honeytokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    token_type ENUM('credential', 'customer_record', 'financial_data', 'system_config') NOT NULL,
    token_value TEXT NOT NULL,
    description VARCHAR(255),
    is_active INT DEFAULT 1,
    token_metadata JSON
);

CREATE TABLE IF NOT EXISTS honeytoken_access_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    token_id INT NOT NULL,
    access_time DATETIME NOT NULL,
    user_id VARCHAR(255),
    ip_address VARCHAR(45),
    access_type ENUM('read', 'write', 'delete', 'execute') NOT NULL,
    query_text TEXT,
    session_data JSON,
    user_agent VARCHAR(255),
    request_headers JSON,
    FOREIGN KEY (token_id) REFERENCES honeytokens(id)
);

CREATE TABLE IF NOT EXISTS alert_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    token_id INT NOT NULL,
    alert_threshold INT DEFAULT 1,
    cooldown_period INT DEFAULT 300,
    alert_channels JSON,
    alert_message_template TEXT,
    is_active INT DEFAULT 1,
    FOREIGN KEY (token_id) REFERENCES honeytokens(id)
); 