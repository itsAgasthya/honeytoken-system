#!/usr/bin/env python3
import os
import sys
import json
import mysql.connector
from datetime import datetime, timedelta
from collections import defaultdict
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

def analyze_accuracy(hours=24):
    """Analyze detection accuracy for the specified time period."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get alert statistics
        cursor.execute("""
            SELECT 
                token_type,
                COUNT(*) as total_alerts,
                SUM(CASE WHEN is_false_positive = 1 THEN 1 ELSE 0 END) as false_positives,
                SUM(CASE WHEN is_false_positive = 0 THEN 1 ELSE 0 END) as true_positives
            FROM honeytoken_alerts a
            JOIN honeytokens h ON a.token_id = h.id
            WHERE a.created_at >= %s
            GROUP BY token_type
        """, (datetime.utcnow() - timedelta(hours=hours),))
        
        alert_stats = cursor.fetchall()
        
        # Get detection timing statistics
        cursor.execute("""
            SELECT 
                h.token_type,
                AVG(TIMESTAMPDIFF(MICROSECOND, l.access_time, l.detection_time)) as avg_detection_time,
                MIN(TIMESTAMPDIFF(MICROSECOND, l.access_time, l.detection_time)) as min_detection_time,
                MAX(TIMESTAMPDIFF(MICROSECOND, l.access_time, l.detection_time)) as max_detection_time
            FROM honeytoken_access_logs l
            JOIN honeytokens h ON l.token_id = h.id
            WHERE l.access_time >= %s
            AND l.detection_time IS NOT NULL
            GROUP BY h.token_type
        """, (datetime.utcnow() - timedelta(hours=hours),))
        
        timing_stats = cursor.fetchall()
        
        # Calculate metrics
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_period_hours': hours,
            'overall': {
                'total_alerts': sum(stat['total_alerts'] for stat in alert_stats),
                'false_positives': sum(stat['false_positives'] for stat in alert_stats),
                'true_positives': sum(stat['true_positives'] for stat in alert_stats)
            },
            'by_token_type': {},
            'timing': {}
        }
        
        # Process alert statistics
        for stat in alert_stats:
            token_type = stat['token_type']
            total = stat['total_alerts']
            false_pos = stat['false_positives']
            true_pos = stat['true_positives']
            
            metrics['by_token_type'][token_type] = {
                'total_alerts': total,
                'false_positives': false_pos,
                'true_positives': true_pos,
                'precision': true_pos / total if total > 0 else 1.0,
                'false_positive_rate': false_pos / total if total > 0 else 0.0
            }
        
        # Process timing statistics
        for stat in timing_stats:
            token_type = stat['token_type']
            metrics['timing'][token_type] = {
                'average_ms': stat['avg_detection_time'] / 1000 if stat['avg_detection_time'] else 0,
                'min_ms': stat['min_detection_time'] / 1000 if stat['min_detection_time'] else 0,
                'max_ms': stat['max_detection_time'] / 1000 if stat['max_detection_time'] else 0
            }
        
        # Calculate overall metrics
        total = metrics['overall']['total_alerts']
        true_pos = metrics['overall']['true_positives']
        false_pos = metrics['overall']['false_positives']
        
        metrics['overall']['precision'] = true_pos / total if total > 0 else 1.0
        metrics['overall']['false_positive_rate'] = false_pos / total if total > 0 else 0.0
        
        # Save metrics to file
        os.makedirs('logs', exist_ok=True)
        with open('logs/accuracy_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        return metrics
        
    finally:
        cursor.close()
        conn.close()

def display_accuracy_analysis(metrics):
    """Display accuracy analysis results."""
    print(f"\nAccuracy Analysis (Last {metrics['analysis_period_hours']} hours)")
    print("=" * 80)
    
    # Overall metrics
    print("\nOverall Performance:")
    print("-" * 40)
    print(f"Total Alerts: {metrics['overall']['total_alerts']}")
    print(f"True Positives: {metrics['overall']['true_positives']}")
    print(f"False Positives: {metrics['overall']['false_positives']}")
    print(f"Precision: {metrics['overall']['precision']*100:.2f}%")
    print(f"False Positive Rate: {metrics['overall']['false_positive_rate']*100:.2f}%")
    
    # Performance by token type
    print("\nPerformance by Token Type:")
    print("-" * 40)
    for token_type, stats in metrics['by_token_type'].items():
        print(f"\n{token_type}:")
        print(f"  Total Alerts: {stats['total_alerts']}")
        print(f"  True Positives: {stats['true_positives']}")
        print(f"  False Positives: {stats['false_positives']}")
        print(f"  Precision: {stats['precision']*100:.2f}%")
        print(f"  False Positive Rate: {stats['false_positive_rate']*100:.2f}%")
    
    # Detection timing
    print("\nDetection Timing by Token Type:")
    print("-" * 40)
    for token_type, timing in metrics['timing'].items():
        print(f"\n{token_type}:")
        print(f"  Average Detection Time: {timing['average_ms']:.2f} ms")
        print(f"  Minimum Detection Time: {timing['min_ms']:.2f} ms")
        print(f"  Maximum Detection Time: {timing['max_ms']:.2f} ms")
    
    print("\nDetailed metrics have been saved to logs/accuracy_metrics.json")

def main():
    """Main function to handle command line arguments."""
    hours = 24
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--last-24h':
            metrics = analyze_accuracy(24)
            display_accuracy_analysis(metrics)
        elif sys.argv[1] == '--hours':
            try:
                hours = int(sys.argv[2])
                metrics = analyze_accuracy(hours)
                display_accuracy_analysis(metrics)
            except (IndexError, ValueError):
                print("Invalid hours value. Usage: --hours <number>")
        else:
            print("Unknown command. Available commands:")
            print("  --last-24h        : Analyze last 24 hours")
            print("  --hours <number>   : Analyze specified number of hours")
    else:
        metrics = analyze_accuracy(hours)
        display_accuracy_analysis(metrics)

if __name__ == "__main__":
    main() 