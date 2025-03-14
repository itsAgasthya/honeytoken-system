#!/usr/bin/env python3
import os
import sys
import json
import psutil
from datetime import datetime
import networkx as nx
from pathlib import Path

def get_process_info(pid):
    """Get detailed information about a process."""
    try:
        proc = psutil.Process(pid)
        return {
            'pid': proc.pid,
            'name': proc.name(),
            'username': proc.username(),
            'cmdline': ' '.join(proc.cmdline()),
            'create_time': datetime.fromtimestamp(proc.create_time()).isoformat(),
            'status': proc.status(),
            'cpu_percent': proc.cpu_percent(),
            'memory_percent': proc.memory_percent(),
            'connections': [
                {
                    'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}",
                    'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    'status': conn.status
                }
                for conn in proc.connections()
            ],
            'open_files': [f.path for f in proc.open_files()],
            'num_threads': proc.num_threads(),
            'parent': proc.ppid()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

def build_process_tree():
    """Build a tree of all running processes."""
    processes = {}
    relationships = []
    
    for proc in psutil.process_iter(['pid', 'ppid', 'name']):
        try:
            proc_info = proc.info
            processes[proc_info['pid']] = proc_info
            if proc_info['ppid']:
                relationships.append((proc_info['ppid'], proc_info['pid']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return processes, relationships

def analyze_suspicious_processes():
    """Analyze processes for suspicious behavior."""
    suspicious = []
    
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
        try:
            # Get process details
            proc_info = get_process_info(proc.pid)
            if not proc_info:
                continue
            
            # Check for suspicious indicators
            indicators = []
            
            # Check for unusual network connections
            if proc_info['connections']:
                for conn in proc_info['connections']:
                    if conn['remote_addr'] and any(
                        port in conn['remote_addr'] 
                        for port in ['4444', '4445', '1337']  # Common exploit ports
                    ):
                        indicators.append(f"Suspicious port in connection: {conn['remote_addr']}")
            
            # Check for sensitive file access
            sensitive_paths = ['/etc/shadow', '/etc/passwd', '.ssh', 'id_rsa']
            for file in proc_info['open_files']:
                if any(path in file for path in sensitive_paths):
                    indicators.append(f"Accessing sensitive file: {file}")
            
            # Check for high resource usage
            if proc_info['cpu_percent'] > 80 or proc_info['memory_percent'] > 80:
                indicators.append("High resource usage")
            
            if indicators:
                proc_info['suspicious_indicators'] = indicators
                suspicious.append(proc_info)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return suspicious

def show_process_tree():
    """Display the process tree in a hierarchical format."""
    processes, relationships = build_process_tree()
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes and edges
    for pid, proc_info in processes.items():
        G.add_node(pid, name=proc_info['name'])
    for parent, child in relationships:
        if parent in processes and child in processes:
            G.add_edge(parent, child)
    
    # Find root processes (those without parents or with non-existent parents)
    roots = [pid for pid in processes if processes[pid]['ppid'] not in processes]
    
    def print_tree(pid, level=0):
        """Recursively print the process tree."""
        if pid not in processes:
            return
        
        proc = processes[pid]
        print("  " * level + f"├── {proc['pid']} - {proc['name']}")
        
        children = [child for parent, child in relationships if parent == pid]
        for child in children:
            print_tree(child, level + 1)
    
    print("\nProcess Tree:")
    print("=============")
    for root in roots:
        print_tree(root)

def save_process_data():
    """Save process information to JSON files."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Save process relationships
    processes, relationships = build_process_tree()
    with open('logs/process_relationships.json', 'w') as f:
        json.dump({
            'timestamp': datetime.utcnow().isoformat(),
            'processes': processes,
            'relationships': relationships
        }, f, indent=2)
    
    # Save process information
    process_info = {
        'timestamp': datetime.utcnow().isoformat(),
        'processes': [
            get_process_info(proc.pid)
            for proc in psutil.process_iter()
            if get_process_info(proc.pid)
        ]
    }
    with open('logs/process_info.json', 'w') as f:
        json.dump(process_info, f, indent=2)
    
    # Save suspicious processes
    suspicious = analyze_suspicious_processes()
    with open('logs/suspicious_processes.json', 'w') as f:
        json.dump({
            'timestamp': datetime.utcnow().isoformat(),
            'suspicious_processes': suspicious
        }, f, indent=2)

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--show-tree':
            show_process_tree()
        elif sys.argv[1] == '--analyze':
            suspicious = analyze_suspicious_processes()
            print(f"\nFound {len(suspicious)} suspicious processes:")
            for proc in suspicious:
                print(f"\nPID: {proc['pid']} - {proc['name']}")
                print(f"Command: {proc['cmdline']}")
                print("Suspicious indicators:")
                for indicator in proc['suspicious_indicators']:
                    print(f"  - {indicator}")
    else:
        # Default: save all data
        save_process_data()
        print("Process data has been saved to logs directory")

if __name__ == "__main__":
    main() 