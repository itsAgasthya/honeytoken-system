#!/bin/bash

# Get the absolute path of the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Create the systemd service file
cat << EOF | sudo tee /etc/systemd/system/honeytoken-monitor.service
[Unit]
Description=Honeytoken Monitoring System
After=network.target mysql.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=${PROJECT_DIR}
Environment=PYTHONPATH=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python ${PROJECT_DIR}/scripts/monitor_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Make the monitor daemon executable
chmod +x "${PROJECT_DIR}/scripts/monitor_daemon.py"

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable honeytoken-monitor
sudo systemctl start honeytoken-monitor

# Check the status
sudo systemctl status honeytoken-monitor

echo "Honeytoken monitoring service has been installed and started."
echo "You can check the logs using: sudo journalctl -u honeytoken-monitor -f" 