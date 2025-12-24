#!/usr/bin/env python3
"""
ProjectQuantum Monitoring and Alerting System
Real-time monitoring for deployed MT5 instances
"""

import os
import sys
import json
import time
import smtplib
import sqlite3
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MonitoringSystem:
    def __init__(self):
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        
        # Production terminals from deployment script
        self.production_terminals = [
            {
                "name": "Primary Trading Terminal",
                "path": Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/8A503E260F28D3DD9CC9A37AA3CE29BC/MQL5"),
                "active": True
            },
            {
                "name": "Backup Terminal", 
                "path": Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5"),
                "active": False
            }
        ]
        
        # Initialize SQLite database for monitoring data
        self.db_path = self.project_root / "monitoring/monitoring.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
        
        # Alert configuration
        self.alert_config = {
            "email_enabled": True,
            "email_smtp": "smtp.gmail.com",
            "email_port": 587,
            "email_user": "renierdejager@gmail.com",
            "email_password": "",  # Set via environment variable
            "alert_recipients": ["renierdejager@gmail.com"],
            "alert_cooldown": 300,  # 5 minutes between same alerts
            "performance_threshold_cpu": 80.0,
            "performance_threshold_memory": 85.0,
            "file_integrity_check_interval": 3600,  # 1 hour
            "health_check_interval": 60  # 1 minute
        }
        
        self.last_alerts = {}  # Track alert cooldowns
        
    def init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # System metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                timestamp TEXT PRIMARY KEY,
                terminal_name TEXT,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                mt5_process_count INTEGER,
                trading_active BOOLEAN
            )
        ''')
        
        # File integrity table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_integrity (
                timestamp TEXT,
                terminal_name TEXT,
                file_path TEXT,
                checksum TEXT,
                status TEXT,
                PRIMARY KEY (timestamp, terminal_name, file_path)
            )
        ''')
        
        # Alert log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                timestamp TEXT PRIMARY KEY,
                alert_type TEXT,
                severity TEXT,
                terminal_name TEXT,
                message TEXT,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Performance benchmarks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_benchmarks (
                timestamp TEXT,
                terminal_name TEXT,
                ea_name TEXT,
                compilation_time REAL,
                execution_time REAL,
                memory_footprint REAL,
                PRIMARY KEY (timestamp, terminal_name, ea_name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def collect_system_metrics(self, terminal_info):
        """Collect system metrics for a terminal"""
        terminal_name = terminal_info["name"]
        terminal_path = terminal_info["path"]
        
        print(f"📊 Collecting metrics for: {terminal_name}")
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "terminal_name": terminal_name,
            "cpu_usage": self.get_cpu_usage(),
            "memory_usage": self.get_memory_usage(),
            "disk_usage": self.get_disk_usage(terminal_path),
            "mt5_process_count": self.count_mt5_processes(),
            "trading_active": self.is_trading_active(terminal_path)
        }
        
        # Store metrics
        self.store_system_metrics(metrics)
        
        # Check for alerts
        self.check_performance_alerts(metrics)
        
        return metrics
    
    def get_cpu_usage(self):
        """Get current CPU usage percentage"""
        try:
            result = subprocess.run(['wmic', 'cpu', 'get', 'loadpercentage', '/value'],
                                  capture_output=True, text=True, timeout=10)
            for line in result.stdout.split('\n'):
                if 'LoadPercentage=' in line:
                    return float(line.split('=')[1])
        except:
            pass
        return 0.0
    
    def get_memory_usage(self):
        """Get current memory usage percentage"""
        try:
            # Get total and available memory
            total_result = subprocess.run(['wmic', 'OS', 'get', 'TotalVisibleMemorySize', '/value'],
                                        capture_output=True, text=True, timeout=10)
            available_result = subprocess.run(['wmic', 'OS', 'get', 'FreePhysicalMemory', '/value'],
                                            capture_output=True, text=True, timeout=10)
            
            total_memory = 0
            available_memory = 0
            
            for line in total_result.stdout.split('\n'):
                if 'TotalVisibleMemorySize=' in line:
                    total_memory = float(line.split('=')[1])
            
            for line in available_result.stdout.split('\n'):
                if 'FreePhysicalMemory=' in line:
                    available_memory = float(line.split('=')[1])
            
            if total_memory > 0:
                used_memory = total_memory - available_memory
                return (used_memory / total_memory) * 100.0
                
        except:
            pass
        return 0.0
    
    def get_disk_usage(self, path):
        """Get disk usage for given path"""
        try:
            # Get disk usage for the drive containing the path
            drive = str(path).split(':')[0] + ':'
            result = subprocess.run(['wmic', 'logicaldisk', 'where', f'size>0', 'get', 'size,freespace,caption', '/value'],
                                  capture_output=True, text=True, timeout=10)
            
            for section in result.stdout.split('\n\n'):
                if f'Caption={drive}' in section:
                    size = 0
                    freespace = 0
                    for line in section.split('\n'):
                        if 'Size=' in line:
                            size = float(line.split('=')[1])
                        elif 'FreeSpace=' in line:
                            freespace = float(line.split('=')[1])
                    
                    if size > 0:
                        used = size - freespace
                        return (used / size) * 100.0
                        
        except:
            pass
        return 0.0
    
    def count_mt5_processes(self):
        """Count running MT5 processes"""
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe', '/FO', 'CSV'],
                                  capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split('\n')
            return max(0, len(lines) - 1)  # Subtract header line
        except:
            return 0
    
    def is_trading_active(self, terminal_path):
        """Check if trading is active by looking for recent log entries"""
        try:
            logs_path = terminal_path.parent / "Logs"
            if not logs_path.exists():
                return False
            
            # Look for today's log file
            today = datetime.now().strftime("%Y%m%d")
            log_files = list(logs_path.glob(f"*{today}*.log"))
            
            if not log_files:
                return False
            
            # Check most recent log for trading activity
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            mod_time = datetime.fromtimestamp(latest_log.stat().st_mtime)
            
            # Consider trading active if log was modified in last 10 minutes
            return (datetime.now() - mod_time).total_seconds() < 600
            
        except:
            return False
    
    def check_file_integrity(self, terminal_info):
        """Check file integrity for deployed ProjectQuantum files"""
        terminal_name = terminal_info["name"]
        terminal_path = terminal_info["path"]
        
        print(f"🔍 Checking file integrity for: {terminal_name}")
        
        integrity_results = []
        
        # Check ProjectQuantum files
        patterns = [
            "Include/ProjectQuantum/**/*.mqh",
            "Experts/ProjectQuantum/*.mq5", 
            "Scripts/ProjectQuantum/*.mq5",
            "Include/ProjectQuantum.mqh"
        ]
        
        for pattern in patterns:
            for file_path in terminal_path.glob(pattern):
                if file_path.is_file():
                    result = self.verify_file_integrity(terminal_name, file_path)
                    integrity_results.append(result)
        
        return integrity_results
    
    def verify_file_integrity(self, terminal_name, file_path):
        """Verify integrity of a single file"""
        try:
            # Calculate current checksum
            current_checksum = self.calculate_checksum(file_path)
            
            # Get expected checksum from deployment manifest
            manifest_path = file_path.parent.parent / "ProjectQuantum_Deployment.json"
            expected_checksum = None
            
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                rel_path = str(file_path.relative_to(file_path.parent.parent))
                if rel_path in manifest.get("files", {}):
                    expected_checksum = manifest["files"][rel_path]["checksum"]
            
            # Determine status
            if expected_checksum is None:
                status = "NO_MANIFEST"
            elif current_checksum == expected_checksum:
                status = "OK"
            else:
                status = "MODIFIED"
                self.send_alert("FILE_INTEGRITY", "HIGH", terminal_name, 
                              f"File integrity violation: {file_path}")
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "terminal_name": terminal_name,
                "file_path": str(file_path),
                "checksum": current_checksum,
                "status": status
            }
            
            # Store result
            self.store_file_integrity(result)
            
            return result
            
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "terminal_name": terminal_name,
                "file_path": str(file_path),
                "checksum": "",
                "status": f"ERROR: {e}"
            }
    
    def calculate_checksum(self, filepath):
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def check_performance_alerts(self, metrics):
        """Check metrics against alert thresholds"""
        terminal_name = metrics["terminal_name"]
        
        # CPU usage alert
        if metrics["cpu_usage"] > self.alert_config["performance_threshold_cpu"]:
            self.send_alert("PERFORMANCE", "MEDIUM", terminal_name,
                          f"High CPU usage: {metrics['cpu_usage']:.1f}%")
        
        # Memory usage alert  
        if metrics["memory_usage"] > self.alert_config["performance_threshold_memory"]:
            self.send_alert("PERFORMANCE", "MEDIUM", terminal_name,
                          f"High memory usage: {metrics['memory_usage']:.1f}%")
        
        # Disk usage alert
        if metrics["disk_usage"] > 90.0:
            self.send_alert("PERFORMANCE", "HIGH", terminal_name,
                          f"Critical disk usage: {metrics['disk_usage']:.1f}%")
        
        # Trading inactive alert
        if not metrics["trading_active"]:
            self.send_alert("TRADING", "LOW", terminal_name,
                          "Trading appears inactive - no recent activity")
        
        # MT5 process count alert
        if metrics["mt5_process_count"] == 0:
            self.send_alert("SYSTEM", "HIGH", terminal_name,
                          "No MT5 processes detected")
    
    def send_alert(self, alert_type, severity, terminal_name, message):
        """Send alert via configured channels"""
        # Check cooldown
        alert_key = f"{alert_type}_{terminal_name}_{message[:50]}"
        now = datetime.now()
        
        if alert_key in self.last_alerts:
            time_since_last = (now - self.last_alerts[alert_key]).total_seconds()
            if time_since_last < self.alert_config["alert_cooldown"]:
                return  # Skip duplicate alert
        
        self.last_alerts[alert_key] = now
        
        # Log alert
        alert_record = {
            "timestamp": now.isoformat(),
            "alert_type": alert_type,
            "severity": severity,
            "terminal_name": terminal_name,
            "message": message
        }
        
        self.store_alert(alert_record)
        
        print(f"🚨 ALERT [{severity}] {alert_type} - {terminal_name}: {message}")
        
        # Send email alert if configured
        if self.alert_config["email_enabled"]:
            self.send_email_alert(alert_record)
    
    def send_email_alert(self, alert_record):
        """Send email alert"""
        try:
            password = os.getenv('MONITORING_EMAIL_PASSWORD')
            if not password:
                print("   📧 Email alert skipped - no password configured")
                return
            
            subject = f"ProjectQuantum Alert: {alert_record['alert_type']} [{alert_record['severity']}]"
            
            body = f"""
ProjectQuantum Monitoring Alert

Terminal: {alert_record['terminal_name']}
Type: {alert_record['alert_type']}  
Severity: {alert_record['severity']}
Time: {alert_record['timestamp']}

Message:
{alert_record['message']}

This is an automated alert from the ProjectQuantum monitoring system.
"""
            
            msg = MIMEMultipart()
            msg['From'] = self.alert_config["email_user"]
            msg['To'] = ', '.join(self.alert_config["alert_recipients"])
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.alert_config["email_smtp"], self.alert_config["email_port"]) as server:
                server.starttls()
                server.login(self.alert_config["email_user"], password)
                server.send_message(msg)
            
            print(f"   📧 Email alert sent to {len(self.alert_config['alert_recipients'])} recipients")
            
        except Exception as e:
            print(f"   ❌ Failed to send email alert: {e}")
    
    def store_system_metrics(self, metrics):
        """Store system metrics in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO system_metrics 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics["timestamp"],
            metrics["terminal_name"], 
            metrics["cpu_usage"],
            metrics["memory_usage"],
            metrics["disk_usage"],
            metrics["mt5_process_count"],
            metrics["trading_active"]
        ))
        
        conn.commit()
        conn.close()
    
    def store_file_integrity(self, result):
        """Store file integrity result in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO file_integrity 
            VALUES (?, ?, ?, ?, ?)
        ''', (
            result["timestamp"],
            result["terminal_name"],
            result["file_path"],
            result["checksum"], 
            result["status"]
        ))
        
        conn.commit()
        conn.close()
    
    def store_alert(self, alert):
        """Store alert in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            alert["timestamp"],
            alert["alert_type"],
            alert["severity"],
            alert["terminal_name"],
            alert["message"],
            False
        ))
        
        conn.commit()
        conn.close()
    
    def generate_monitoring_dashboard(self):
        """Generate monitoring dashboard"""
        print("📊 Generating monitoring dashboard...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Get recent metrics
        metrics_query = '''
            SELECT * FROM system_metrics 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
        '''
        metrics_df = conn.execute(metrics_query).fetchall()
        
        # Get recent alerts
        alerts_query = '''
            SELECT * FROM alerts 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
        '''
        alerts_df = conn.execute(alerts_query).fetchall()
        
        # Get file integrity status
        integrity_query = '''
            SELECT terminal_name, status, COUNT(*) as count
            FROM file_integrity 
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY terminal_name, status
        '''
        integrity_df = conn.execute(integrity_query).fetchall()
        
        conn.close()
        
        # Generate dashboard HTML
        dashboard_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ProjectQuantum Monitoring Dashboard</title>
    <meta http-equiv="refresh" content="60">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
        .dashboard {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .panel {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: flex; justify-content: space-between; margin: 10px 0; }}
        .alert {{ padding: 10px; margin: 5px 0; border-radius: 4px; }}
        .alert.HIGH {{ background: #ffebee; border-left: 4px solid #f44336; }}
        .alert.MEDIUM {{ background: #fff3e0; border-left: 4px solid #ff9800; }}
        .alert.LOW {{ background: #e8f5e8; border-left: 4px solid #4caf50; }}
        .status.OK {{ color: #4caf50; }}
        .status.MODIFIED {{ color: #ff9800; }}
        .status.ERROR {{ color: #f44336; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ProjectQuantum Monitoring Dashboard</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Auto-refresh: 60 seconds</p>
    </div>
    
    <div class="dashboard">
        <div class="panel">
            <h2>System Metrics (Last 24h)</h2>
        """
        
        if metrics_df:
            for row in metrics_df[:10]:  # Show last 10 entries
                timestamp, terminal, cpu, memory, disk, processes, trading = row
                dashboard_html += f"""
            <div class="metric">
                <strong>{terminal}</strong>
                <span>CPU: {cpu:.1f}% | RAM: {memory:.1f}% | Disk: {disk:.1f}%</span>
            </div>
            <div class="timestamp">{timestamp}</div>
                """
        else:
            dashboard_html += "<p>No metrics available</p>"
        
        dashboard_html += """
        </div>
        
        <div class="panel">
            <h2>Recent Alerts (Last 24h)</h2>
        """
        
        if alerts_df:
            for row in alerts_df[:10]:  # Show last 10 alerts
                timestamp, alert_type, severity, terminal, message, resolved = row
                dashboard_html += f"""
            <div class="alert {severity}">
                <strong>{alert_type}</strong> [{severity}] - {terminal}
                <div>{message}</div>
                <div class="timestamp">{timestamp}</div>
            </div>
                """
        else:
            dashboard_html += "<p>No alerts in last 24 hours</p>"
        
        dashboard_html += """
        </div>
        
        <div class="panel">
            <h2>File Integrity Status</h2>
        """
        
        if integrity_df:
            for row in integrity_df:
                terminal, status, count = row
                dashboard_html += f"""
            <div class="metric">
                <span>{terminal}</span>
                <span class="status {status}">{status}: {count} files</span>
            </div>
                """
        else:
            dashboard_html += "<p>No integrity checks completed recently</p>"
        
        dashboard_html += """
        </div>
        
        <div class="panel">
            <h2>System Health Summary</h2>
            <div class="metric">
                <span>Total Active Terminals</span>
                <span>{}</span>
            </div>
            <div class="metric">
                <span>Monitoring Database</span>
                <span class="status OK">Connected</span>
            </div>
            <div class="metric">
                <span>Last Health Check</span>
                <span>{}</span>
            </div>
        </div>
    </div>
</body>
</html>
        """.format(
            len([t for t in self.production_terminals if t["active"]]),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Save dashboard
        dashboard_path = self.project_root / "monitoring/dashboard.html"
        with open(dashboard_path, 'w') as f:
            f.write(dashboard_html)
        
        print(f"   📄 Dashboard saved: {dashboard_path}")
        return dashboard_path
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        print(f"\n🔄 Running monitoring cycle: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        cycle_results = {
            "timestamp": datetime.now().isoformat(),
            "terminals_checked": 0,
            "alerts_generated": 0,
            "files_verified": 0
        }
        
        for terminal in self.production_terminals:
            if terminal["active"]:
                cycle_results["terminals_checked"] += 1
                
                # Collect system metrics
                metrics = self.collect_system_metrics(terminal)
                
                # Check file integrity
                integrity_results = self.check_file_integrity(terminal)
                cycle_results["files_verified"] += len(integrity_results)
        
        # Generate dashboard
        dashboard_path = self.generate_monitoring_dashboard()
        
        print(f"\n📈 Cycle complete:")
        print(f"   Terminals: {cycle_results['terminals_checked']}")
        print(f"   Files verified: {cycle_results['files_verified']}")
        print(f"   Dashboard: {dashboard_path}")
        
        return cycle_results
    
    def start_continuous_monitoring(self, interval_seconds=60):
        """Start continuous monitoring loop"""
        print("🚀 Starting ProjectQuantum Monitoring System")
        print(f"Monitoring interval: {interval_seconds} seconds")
        print(f"Alert cooldown: {self.alert_config['alert_cooldown']} seconds")
        print(f"Database: {self.db_path}")
        
        try:
            while True:
                self.run_monitoring_cycle()
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
            self.send_alert("SYSTEM", "HIGH", "MONITOR", f"Monitoring system error: {e}")

if __name__ == "__main__":
    monitor = MonitoringSystem()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run single monitoring cycle
        monitor.run_monitoring_cycle()
    else:
        # Start continuous monitoring
        monitor.start_continuous_monitoring()