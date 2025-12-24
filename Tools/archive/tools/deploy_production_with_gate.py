#!/usr/bin/env python3
"""
ProjectQuantum Production Deployment with Test Gate
Enhanced deployment script with comprehensive failure prevention
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Import the original deployment functionality
from deploy_production import ProductionDeployer

class GatedProductionDeployer(ProductionDeployer):
    def __init__(self):
        super().__init__()
        self.gate_checks_passed = False
        
    def run_pre_deployment_tests(self):
        """Run comprehensive pre-deployment test suite"""
        print("🧪 Running pre-deployment test gate...")
        
        # Run automated test framework
        result = subprocess.run([
            sys.executable, "automated_test_framework.py"
        ], capture_output=True, text=True, cwd=self.project_root)
        
        if result.returncode != 0:
            print("❌ PRE-DEPLOYMENT GATE FAILURE")
            print("=" * 50)
            print("Tests failed - deployment aborted for safety")
            print()
            print("Failure details:")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                # Parse test results for better error reporting
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'FAILED' in line or 'Failed:' in line or 'Success Rate:' in line:
                        print(f"  {line}")
            print()
            print("🔧 Required actions:")
            print("  1. Fix all failing tests")
            print("  2. Achieve 100% test pass rate") 
            print("  3. Retry deployment")
            print()
            print("⚠️  Production deployment BLOCKED for safety")
            return False
        
        print("✅ All tests passed - deployment gate cleared")
        return True
    
    def run_system_health_check(self):
        """Run system health verification"""
        print("\n🔍 Running system health check...")
        
        # Check monitoring system
        result = subprocess.run([
            sys.executable, "monitoring_system.py", "--once"
        ], capture_output=True, text=True, cwd=self.project_root)
        
        if result.returncode != 0:
            print("❌ System health check failed")
            print(f"Error: {result.stderr}")
            return False
        
        print("✅ System health check passed")
        return True
    
    def verify_backup_capability(self):
        """Verify backup and rollback capability"""
        print("\n📦 Verifying backup capability...")
        
        backup_dir = self.project_root / "backups"
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if we can create backups
        test_backup_name = f"test_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_backup_path = backup_dir / test_backup_name
        
        try:
            test_backup_path.mkdir()
            test_file = test_backup_path / "backup_test.txt"
            test_file.write_text("Backup capability verified")
            
            # Cleanup test backup
            test_file.unlink()
            test_backup_path.rmdir()
            
            print("✅ Backup capability verified")
            return True
            
        except Exception as e:
            print(f"❌ Backup capability failed: {e}")
            return False
    
    def deploy_with_gates(self):
        """Deploy with comprehensive safety gates"""
        print("🛡️  ProjectQuantum Gated Production Deployment")
        print("=" * 60)
        print(f"Version: 1.216")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Gate 1: Pre-deployment tests
        if not self.run_pre_deployment_tests():
            return False
        
        # Gate 2: System health check
        if not self.run_system_health_check():
            print("❌ System health check failed - aborting deployment")
            return False
        
        # Gate 3: Backup capability verification
        if not self.verify_backup_capability():
            print("❌ Backup verification failed - aborting deployment")
            return False
        
        print("\n🚀 All safety gates passed - proceeding with deployment")
        print("=" * 60)
        
        # Run the actual deployment
        success = self.deploy_all()
        
        if success:
            print("\n🎉 DEPLOYMENT COMPLETED SUCCESSFULLY")
            print("✅ All safety gates passed")
            print("✅ Files deployed and verified")
            print("✅ System monitoring active")
            print()
            print("🔄 Post-deployment verification:")
            
            # Run post-deployment monitoring check
            self.run_system_health_check()
            
        else:
            print("\n❌ DEPLOYMENT FAILED")
            print("🔧 Check deployment logs for details")
            print("📦 Backups available for rollback if needed")
        
        return success

def main():
    """Main deployment entry point with safety gates"""
    deployer = GatedProductionDeployer()
    
    # Check for force flag (bypasses some gates for emergency)
    force_deployment = "--force" in sys.argv
    
    if force_deployment:
        print("⚠️  FORCE DEPLOYMENT MODE ENABLED")
        print("This bypasses some safety checks - use with caution!")
        success = deployer.deploy_all()
    else:
        success = deployer.deploy_with_gates()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()