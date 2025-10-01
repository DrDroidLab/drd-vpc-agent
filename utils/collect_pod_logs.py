#!/usr/bin/env python3
"""
Smart script to collect logs from all pods in the drdroid namespace.

This script:
1. Lists all pods in the drdroid namespace
2. Collects logs for each pod for a specified time period
3. Saves logs with standardized filenames for easy sharing

Usage:
    python collect_pod_logs.py [--minutes MINUTES] [--namespace NAMESPACE] [--output-dir OUTPUT_DIR]
"""

import argparse
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json


class PodLogCollector:
    """A smart pod log collector for Kubernetes clusters."""
    
    def __init__(self, namespace: str = "drdroid", output_dir: str = "pod_logs"):
        self.namespace = namespace
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
    
    def run_kubectl_command(self, command: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a kubectl command and return the result."""
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error running kubectl command: {' '.join(command)}")
            print(f"Error: {e.stderr}")
            sys.exit(1)
        except FileNotFoundError:
            print("Error: kubectl command not found. Please ensure kubectl is installed and in your PATH.")
            sys.exit(1)
    
    def get_pods(self) -> List[dict]:
        """Get list of all pods in the specified namespace."""
        print(f"Fetching pods from namespace: {self.namespace}")
        
        command = [
            "kubectl", "get", "pods",
            "-n", self.namespace,
            "-o", "json"
        ]
        
        result = self.run_kubectl_command(command)
        
        try:
            pods_data = json.loads(result.stdout)
            pods = []
            
            for pod in pods_data.get("items", []):
                pod_info = {
                    "name": pod["metadata"]["name"],
                    "status": pod["status"]["phase"],
                    "creation_timestamp": pod["metadata"]["creationTimestamp"]
                }
                pods.append(pod_info)
            
            return pods
        except json.JSONDecodeError as e:
            print(f"Error parsing kubectl output: {e}")
            sys.exit(1)
    
    def collect_pod_logs(self, pod_name: str, minutes: int) -> str:
        """Collect logs for a specific pod."""
        print(f"Collecting logs for pod: {pod_name} (last {minutes} minutes)")
        
        # Create standardized filename
        filename = f"logs_{self.namespace}_{pod_name}_{self.timestamp}_past_{minutes}min.txt"
        filepath = self.output_dir / filename
        
        command = [
            "kubectl", "logs",
            pod_name,
            "-n", self.namespace,
            f"--since={minutes}m"
        ]
        
        try:
            with open(filepath, 'w') as f:
                result = subprocess.run(
                    command,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
            
            # Check if file has content
            if filepath.stat().st_size == 0:
                print(f"  Warning: No logs found for pod {pod_name}")
                return str(filepath)
            
            print(f"  Logs saved to: {filepath}")
            return str(filepath)
            
        except subprocess.CalledProcessError as e:
            print(f"  Error collecting logs for {pod_name}: {e.stderr}")
            return ""
    
    def collect_all_logs(self, minutes: int = 15) -> List[str]:
        """Collect logs from all pods in the namespace."""
        print(f"Starting log collection for namespace: {self.namespace}")
        print(f"Time range: last {minutes} minutes")
        print(f"Output directory: {self.output_dir.absolute()}")
        print("-" * 60)
        
        # Get list of pods
        pods = self.get_pods()
        
        if not pods:
            print(f"No pods found in namespace: {self.namespace}")
            return []
        
        print(f"Found {len(pods)} pods:")
        for pod in pods:
            print(f"  - {pod['name']} (status: {pod['status']})")
        print("-" * 60)
        
        # Collect logs for each pod
        collected_files = []
        successful_collections = 0
        
        for pod in pods:
            pod_name = pod['name']
            filepath = self.collect_pod_logs(pod_name, minutes)
            
            if filepath:
                collected_files.append(filepath)
                successful_collections += 1
        
        print("-" * 60)
        print(f"Log collection completed!")
        print(f"Successfully collected logs from {successful_collections}/{len(pods)} pods")
        print(f"Files saved in: {self.output_dir.absolute()}")
        
        return collected_files
    
    def create_summary_report(self, collected_files: List[str], minutes: int):
        """Create a summary report of the log collection."""
        summary_file = self.output_dir / f"collection_summary_{self.timestamp}.txt"
        
        with open(summary_file, 'w') as f:
            f.write("POD LOG COLLECTION SUMMARY\n")
            f.write("=" * 50 + "\n")
            f.write(f"Collection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Namespace: {self.namespace}\n")
            f.write(f"Time Range: Last {minutes} minutes\n")
            f.write(f"Total Files Collected: {len(collected_files)}\n")
            f.write("\nCollected Files:\n")
            f.write("-" * 30 + "\n")
            
            for filepath in collected_files:
                filename = Path(filepath).name
                file_size = Path(filepath).stat().st_size
                f.write(f"{filename} ({file_size} bytes)\n")
        
        print(f"Summary report created: {summary_file}")


def main():
    """Main function to handle CLI arguments and run the log collector."""
    parser = argparse.ArgumentParser(
        description="Collect logs from all pods in a Kubernetes namespace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python collect_pod_logs.py                    # Collect last 15 minutes of logs
  python collect_pod_logs.py --minutes 30      # Collect last 30 minutes of logs
  python collect_pod_logs.py --namespace myns  # Collect from different namespace
  python collect_pod_logs.py --output-dir logs # Save to custom directory
        """
    )
    
    parser.add_argument(
        "--minutes", "-m",
        type=int,
        default=15,
        help="Number of minutes of logs to collect (default: 15)"
    )
    
    parser.add_argument(
        "--namespace", "-n",
        type=str,
        default="drdroid",
        help="Kubernetes namespace to collect logs from (default: drdroid)"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="pod_logs",
        help="Output directory for log files (default: pod_logs)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.minutes <= 0:
        print("Error: Minutes must be a positive integer")
        sys.exit(1)
    
    # Create and run the log collector
    collector = PodLogCollector(
        namespace=args.namespace,
        output_dir=args.output_dir
    )
    
    try:
        collected_files = collector.collect_all_logs(minutes=args.minutes)
        collector.create_summary_report(collected_files, args.minutes)
        
        if collected_files:
            print(f"\n🎉 Successfully collected {len(collected_files)} log files!")
            print("You can now share these files for analysis.")
        else:
            print("\n⚠️  No log files were collected.")
            
    except KeyboardInterrupt:
        print("\n\nLog collection interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()