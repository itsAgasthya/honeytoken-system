import logging
import json
from datetime import datetime
import os
import hashlib
import ipaddress
from typing import Dict, Any, List
import requests
from logging.handlers import RotatingFileHandler
from elasticsearch import Elasticsearch
import pyshark
import yara
import psutil
from pathlib import Path

class ForensicsLogger:
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger('forensics')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Initialize Elasticsearch client if configured
        self.es_client = None
        if os.getenv('ELASTICSEARCH_URL'):
            self.es_client = Elasticsearch([os.getenv('ELASTICSEARCH_URL')])
        
        # Initialize YARA rules
        self.yara_rules = None
        self._load_yara_rules()
        
        # Rotating file handler for access logs
        access_handler = RotatingFileHandler(
            'logs/access.log',
            maxBytes=10485760,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        access_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(access_handler)
        
        # Separate handler for alerts
        alert_handler = RotatingFileHandler(
            'logs/alerts.log',
            maxBytes=10485760,
            backupCount=10,
            encoding='utf-8'
        )
        alert_handler.setFormatter(
            logging.Formatter('%(asctime)s - ALERT - %(message)s')
        )
        self.logger.addHandler(alert_handler)

    def _load_yara_rules(self):
        """Load YARA rules for threat detection."""
        rules_dir = Path('forensics/yara_rules')
        if rules_dir.exists():
            rules = []
            for rule_file in rules_dir.glob('*.yar'):
                with open(rule_file) as f:
                    rules.append(f.read())
            if rules:
                self.yara_rules = yara.compile(source='\n'.join(rules))

    def capture_network_traffic(self, interface: str, duration: int = 60) -> str:
        """Capture network traffic related to honeytoken access."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        capture_file = f'logs/network/capture_{timestamp}.pcap'
        
        # Ensure network logs directory exists
        os.makedirs('logs/network', exist_ok=True)
        
        # Capture packets using pyshark (wrapper for tshark/wireshark)
        capture = pyshark.LiveCapture(interface=interface, output_file=capture_file)
        capture.sniff(timeout=duration)
        
        return capture_file

    def analyze_process_activity(self, pid: int = None) -> Dict[str, Any]:
        """Analyze process activity during honeytoken access."""
        process_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'processes': []
        }
        
        # Get all processes or specific process
        processes = [psutil.Process(pid)] if pid else psutil.process_iter(['pid', 'name', 'username', 'cmdline'])
        
        for proc in processes:
            try:
                proc_info = {
                    'pid': proc.pid,
                    'name': proc.name(),
                    'username': proc.username(),
                    'cmdline': proc.cmdline(),
                    'connections': [],
                    'open_files': []
                }
                
                # Get network connections
                for conn in proc.connections():
                    proc_info['connections'].append({
                        'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'status': conn.status
                    })
                
                # Get open files
                for file in proc.open_files():
                    proc_info['open_files'].append(file.path)
                
                process_data['processes'].append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return process_data

    def log_access_attempt(self, token_id: int, user_id: str, ip_address: str,
                          user_agent: str, request_headers: Dict[str, str]) -> None:
        """Log detailed information about a honeytoken access attempt."""
        try:
            # Enrich IP information
            ip_info = self._get_ip_info(ip_address)
            
            # Create forensic record
            forensic_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'token_id': token_id,
                'user_id': user_id,
                'ip_address': ip_address,
                'ip_info': ip_info,
                'user_agent': user_agent,
                'headers': request_headers,
                'request_hash': self._generate_request_hash(token_id, user_id, ip_address),
                'process_activity': self.analyze_process_activity(),
                'yara_matches': self._check_yara_rules(request_headers)
            }
            
            # Log to file
            self.logger.info(json.dumps(forensic_data))
            
            # Log to Elasticsearch if configured
            if self.es_client:
                self.es_client.index(
                    index=f'honeytoken-logs-{datetime.utcnow():%Y-%m}',
                    document=forensic_data
                )
            
            # If suspicious, trigger additional forensics
            if self._is_suspicious_access(forensic_data):
                self.logger.warning(f"Suspicious access detected: {json.dumps(forensic_data)}")
                self._collect_additional_forensics(forensic_data)
        
        except Exception as e:
            self.logger.error(f"Error logging access attempt: {str(e)}")

    def _collect_additional_forensics(self, forensic_data: Dict[str, Any]) -> None:
        """Collect additional forensics data for suspicious access."""
        try:
            # Capture network traffic
            capture_file = self.capture_network_traffic('eth0', duration=30)
            
            # Collect system state
            system_state = {
                'timestamp': datetime.utcnow().isoformat(),
                'memory_usage': psutil.virtual_memory()._asdict(),
                'cpu_usage': psutil.cpu_percent(interval=1, percpu=True),
                'network_connections': [conn._asdict() for conn in psutil.net_connections()],
                'capture_file': capture_file
            }
            
            # Log additional data
            self.logger.warning(f"Additional forensics collected: {json.dumps(system_state)}")
            
            if self.es_client:
                self.es_client.index(
                    index=f'honeytoken-forensics-{datetime.utcnow():%Y-%m}',
                    document={
                        'forensic_data': forensic_data,
                        'system_state': system_state
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Error collecting additional forensics: {str(e)}")

    def _check_yara_rules(self, data: Dict[str, Any]) -> List[str]:
        """Check data against YARA rules."""
        if not self.yara_rules:
            return []
        
        matches = []
        try:
            # Convert data to string for YARA scanning
            data_str = json.dumps(data)
            # Scan with YARA rules
            yara_matches = self.yara_rules.match(data=data_str)
            matches = [match.rule for match in yara_matches]
        except Exception as e:
            self.logger.error(f"Error checking YARA rules: {str(e)}")
        
        return matches

    def _get_ip_info(self, ip_address: str) -> Dict[str, Any]:
        """Gather information about an IP address."""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Basic IP information
            ip_info = {
                'version': ip.version,
                'is_private': ip.is_private,
                'is_global': ip.is_global,
                'reverse_pointer': None,
                'geolocation': None
            }
            
            # Try to get reverse DNS
            try:
                import socket
                ip_info['reverse_pointer'] = socket.gethostbyaddr(ip_address)[0]
            except:
                pass
            
            # Get geolocation data if it's a public IP
            if ip_info['is_global']:
                try:
                    response = requests.get(f'https://ipapi.co/{ip_address}/json/')
                    if response.status_code == 200:
                        ip_info['geolocation'] = response.json()
                except:
                    pass
            
            return ip_info
        except:
            return {'error': 'Invalid IP address'}

    def _generate_request_hash(self, token_id: int, user_id: str, ip_address: str) -> str:
        """Generate a unique hash for the request for correlation."""
        data = f"{token_id}{user_id}{ip_address}{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _is_suspicious_access(self, forensic_data: Dict[str, Any]) -> bool:
        """Determine if an access attempt is suspicious."""
        # Check for known suspicious patterns
        suspicious_indicators = [
            self._check_tor_exit_node(forensic_data['ip_address']),
            self._check_suspicious_user_agent(forensic_data['user_agent']),
            self._check_suspicious_headers(forensic_data['headers']),
            self._check_geolocation_anomaly(forensic_data.get('ip_info', {}).get('geolocation'))
        ]
        
        return any(suspicious_indicators)

    def _check_tor_exit_node(self, ip_address: str) -> bool:
        """Check if IP is a known Tor exit node."""
        try:
            response = requests.get('https://check.torproject.org/exit-addresses')
            return ip_address in response.text
        except:
            return False

    def _check_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check for suspicious user agents."""
        suspicious_patterns = [
            'curl', 'wget', 'python-requests', 'go-http-client',
            'burp', 'nikto', 'sqlmap', 'nmap', 'masscan'
        ]
        return any(pattern.lower() in user_agent.lower() for pattern in suspicious_patterns)

    def _check_suspicious_headers(self, headers: Dict[str, str]) -> bool:
        """Check for suspicious or missing headers."""
        required_headers = {'user-agent', 'host', 'accept'}
        return not all(header.lower() in map(str.lower, headers) for header in required_headers)

    def _check_geolocation_anomaly(self, geolocation: Dict[str, Any]) -> bool:
        """Check for geolocation anomalies."""
        if not geolocation:
            return False
            
        # Example: Check if access is from a high-risk country
        high_risk_countries = {'NK', 'IR', 'CU'}  # Example list
        return geolocation.get('country_code') in high_risk_countries

    def log_alert(self, alert_type: str, details: Dict[str, Any]) -> None:
        """Log security alerts."""
        alert_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': alert_type,
            'details': details
        }
        self.logger.warning(f"SECURITY ALERT: {json.dumps(alert_data)}")

# Initialize the forensics logger
forensics_logger = ForensicsLogger() 