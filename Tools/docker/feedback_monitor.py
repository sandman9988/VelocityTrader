#!/usr/bin/env python3
"""
ProjectQuantum Feedback Loop Monitor
Real-time compilation and testing feedback for Docker-based development

This script provides continuous feedback during development by:
1. Monitoring compilation results
2. Tracking test execution
3. Displaying real-time status updates
4. Providing actionable recommendations
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class FeedbackLoopMonitor:
    """Monitors Docker container compilation and test execution"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results_dir = project_root / "ci-results"
        self.logs_dir = project_root / "logs"
        self.last_check_time = None
        
        # Ensure directories exist
        self.results_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    def check_compilation_status(self) -> Optional[Dict[str, Any]]:
        """Check latest compilation results"""
        report_file = self.results_dir / "compilation-report.json"
        
        if not report_file.exists():
            return None
        
        try:
            with open(report_file, 'r') as f:
                data = json.load(f)
            
            # Check if file was updated since last check
            file_mtime = report_file.stat().st_mtime
            if self.last_check_time and file_mtime <= self.last_check_time:
                return None
            
            self.last_check_time = file_mtime
            return data
            
        except Exception as e:
            print(f"⚠️  Error reading compilation report: {e}")
            return None
    
    def check_test_status(self) -> Optional[Dict[str, Any]]:
        """Check latest test results"""
        report_file = self.results_dir / "test-report.json"
        
        if not report_file.exists():
            return None
        
        try:
            with open(report_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading test report: {e}")
            return None
    
    def print_compilation_feedback(self, data: Dict[str, Any]):
        """Print formatted compilation feedback"""
        timestamp = data.get('timestamp', 'Unknown')
        main_ea = data.get('main_ea', {})
        summary = data.get('summary', {})
        
        status = main_ea.get('status', 'unknown')
        errors = summary.get('total_errors', 0)
        warnings = summary.get('total_warnings', 0)
        comp_time = summary.get('compilation_time', 0)
        total_files = summary.get('total_files', 0)
        
        print("\n" + "=" * 60)
        print("📊 COMPILATION FEEDBACK")
        print("=" * 60)
        print(f"Timestamp: {timestamp}")
        print(f"Status:    {'✅ SUCCESS' if status == 'success' else '❌ FAILED'}")
        print(f"Files:     {total_files}")
        print(f"Errors:    {errors}")
        print(f"Warnings:  {warnings}")
        print(f"Time:      {comp_time}s")
        
        # Provide recommendations
        if errors > 0:
            print("\n💡 RECOMMENDATIONS:")
            print("   • Check compilation logs in ci-results/")
            print("   • Review error messages for syntax issues")
            print("   • Ensure all dependencies are properly included")
        elif warnings > 0:
            print("\n💡 RECOMMENDATIONS:")
            print("   • Review warnings for potential issues")
            print("   • Consider fixing warnings to improve code quality")
        else:
            print("\n✨ EXCELLENT! All files compiled successfully.")
        
        print("=" * 60)
    
    def print_test_feedback(self, data: Dict[str, Any]):
        """Print formatted test feedback"""
        summary = data.get('summary', {})
        
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        
        print("\n" + "=" * 60)
        print("🧪 TEST FEEDBACK")
        print("=" * 60)
        print(f"Total:   {total}")
        print(f"Passed:  {passed} {'✅' if passed == total else ''}")
        print(f"Failed:  {failed} {'❌' if failed > 0 else ''}")
        print(f"Skipped: {skipped}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"Success: {success_rate:.1f}%")
        
        # Provide recommendations
        if failed > 0:
            print("\n💡 RECOMMENDATIONS:")
            print("   • Review failed test logs")
            print("   • Check test-report.json for detailed results")
            print("   • Run specific tests: ./Tools/docker/mql5-docker.sh test <suite>")
        elif skipped > 0:
            print("\n💡 NOTE:")
            print("   • Some tests were skipped (need compilation)")
        else:
            print("\n✨ EXCELLENT! All tests passed.")
        
        print("=" * 60)
    
    def monitor_continuously(self, interval: int = 5):
        """Continuously monitor for updates"""
        print("🔍 Starting Feedback Loop Monitor")
        print("=" * 60)
        print("Monitoring for compilation and test updates...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Check for compilation updates
                comp_data = self.check_compilation_status()
                if comp_data:
                    self.print_compilation_feedback(comp_data)
                
                # Check for test updates
                test_data = self.check_test_status()
                if test_data and comp_data:  # Only show tests if we have compilation
                    self.print_test_feedback(test_data)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Feedback monitor stopped")
    
    def show_current_status(self):
        """Show current status (one-time check)"""
        comp_data = self.check_compilation_status()
        test_data = self.check_test_status()
        
        if not comp_data and not test_data:
            print("ℹ️  No compilation or test results found yet.")
            print("   Run: ./Tools/docker/mql5-docker.sh compile")
            return
        
        if comp_data:
            self.print_compilation_feedback(comp_data)
        
        if test_data:
            self.print_test_feedback(test_data)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ProjectQuantum Feedback Loop Monitor'
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Continuously monitor for updates'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Monitoring interval in seconds (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Get project root (2 levels up from script location)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    monitor = FeedbackLoopMonitor(project_root)
    
    if args.watch:
        monitor.monitor_continuously(args.interval)
    else:
        monitor.show_current_status()


if __name__ == '__main__':
    main()
