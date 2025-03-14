#!/usr/bin/env python3
import os
import sys
import json
import time
import psutil
import requests
from datetime import datetime, timedelta
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create a database connection."""
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'honeytoken_db')
    )

def get_system_metrics():
    """Get current system performance metrics."""
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'cpu': {
            'percent': psutil.cpu_percent(interval=1, percpu=True),
            'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'count': psutil.cpu_count()
        },
        'memory': psutil.virtual_memory()._asdict(),
        'disk': {
            'usage': psutil.disk_usage('/')._asdict(),
            'io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None
        },
        'network': psutil.net_io_counters()._asdict()
    }

def get_elasticsearch_metrics():
    """Get Elasticsearch performance metrics."""
    try:
        # Get cluster health
        health = requests.get('http://localhost:9200/_cluster/health').json()
        
        # Get nodes stats
        stats = requests.get('http://localhost:9200/_nodes/stats').json()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'cluster_health': health,
            'nodes_stats': stats
        }
    except Exception as e:
        print(f"Error getting Elasticsearch metrics: {e}")
        return None

def get_detection_metrics():
    """Get honeytoken detection performance metrics."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get detection latency
        cursor.execute("""
            SELECT 
                AVG(TIMESTAMPDIFF(MICROSECOND, access_time, detection_time)) as avg_latency,
                MIN(TIMESTAMPDIFF(MICROSECOND, access_time, detection_time)) as min_latency,
                MAX(TIMESTAMPDIFF(MICROSECOND, access_time, detection_time)) as max_latency
            FROM honeytoken_access_logs
            WHERE detection_time IS NOT NULL
            AND access_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        latency = cursor.fetchone()
        
        # Get detection accuracy
        cursor.execute("""
            SELECT 
                COUNT(*) as total_alerts,
                SUM(CASE WHEN is_false_positive = 1 THEN 1 ELSE 0 END) as false_positives
            FROM honeytoken_alerts
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        accuracy = cursor.fetchone()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'detection_latency': {
                'average_us': latency['avg_latency'] if latency['avg_latency'] else 0,
                'min_us': latency['min_latency'] if latency['min_latency'] else 0,
                'max_us': latency['max_latency'] if latency['max_latency'] else 0
            },
            'accuracy': {
                'total_alerts': accuracy['total_alerts'],
                'false_positives': accuracy['false_positives'],
                'accuracy_rate': (
                    1 - (accuracy['false_positives'] / accuracy['total_alerts'])
                    if accuracy['total_alerts'] > 0 else 1
                )
            }
        }
    finally:
        cursor.close()
        conn.close()

def monitor_live_performance(interval=5):
    """Monitor and display live performance metrics."""
    try:
        while True:
            # Get metrics
            system = get_system_metrics()
            es = get_elasticsearch_metrics()
            detection = get_detection_metrics()
            
            # Clear screen
            os.system('clear' if os.name == 'posix' else 'cls')
            
            # Display system metrics
            print("\nSystem Performance:")
            print("=" * 80)
            print(f"CPU Usage: {system['cpu']['percent']}%")
            print(f"Memory Usage: {system['memory']['percent']}%")
            print(f"Disk Usage: {system['disk']['usage']['percent']}%")
            
            # Display Elasticsearch metrics
            if es:
                print("\nElasticsearch Status:")
                print("=" * 80)
                print(f"Cluster Status: {es['cluster_health']['status']}")
                print(f"Active Shards: {es['cluster_health']['active_shards']}")
                print(f"Relocating Shards: {es['cluster_health']['relocating_shards']}")
            
            # Display detection metrics
            print("\nDetection Performance:")
            print("=" * 80)
            print(f"Average Detection Latency: {detection['detection_latency']['average_us']/1000:.2f} ms")
            print(f"Detection Accuracy: {detection['accuracy']['accuracy_rate']*100:.2f}%")
            print(f"False Positives: {detection['accuracy']['false_positives']}")
            
            # Save metrics to file
            os.makedirs('logs', exist_ok=True)
            with open('logs/performance_metrics.json', 'w') as f:
                json.dump({
                    'timestamp': datetime.utcnow().isoformat(),
                    'system': system,
                    'elasticsearch': es,
                    'detection': detection
                }, f, indent=2)
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--live':
            interval = 5
            if len(sys.argv) > 2:
                try:
                    interval = int(sys.argv[2])
                except ValueError:
                    print("Invalid interval value. Using default 5 seconds.")
            monitor_live_performance(interval)
        else:
            print("Unknown command. Available commands:")
            print("  --live [interval] : Show live performance metrics")
    else:
        # Default: save current metrics
        system = get_system_metrics()
        es = get_elasticsearch_metrics()
        detection = get_detection_metrics()
        
        os.makedirs('logs', exist_ok=True)
        with open('logs/performance_metrics.json', 'w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'system': system,
                'elasticsearch': es,
                'detection': detection
            }, f, indent=2)
        print("Performance metrics have been saved to logs/performance_metrics.json")

if __name__ == "__main__":
    main() 