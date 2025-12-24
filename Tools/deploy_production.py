#!/usr/bin/env python3
"""
ProjectQuantum Production Deployment Script
Automates deployment to MT5 terminals with validation
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

class ProductionDeployer:
    def __init__(self):
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        
        # Production terminals
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
        
        self.deployment_log = []
        
    def calculate_checksum(self, filepath):
        """Calculate SHA256 checksum of a file

        Args:
            filepath: Path to the file to checksum

        Returns:
            Hex string of SHA256 hash, or None on error

        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be read
            IOError: If there is a problem reading the file
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except PermissionError as e:
            raise PermissionError(f"Cannot read file (permission denied): {filepath}") from e
        except IOError as e:
            raise IOError(f"Error reading file for checksum: {filepath} - {e}") from e
    
    def validate_files(self):
        """Validate all files before deployment"""
        print("🔍 Validating files for deployment...")
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "files_validated": 0,
            "files_failed": 0,
            "errors": []
        }
        
        # Check all ProjectQuantum files
        files_to_validate = []
        files_to_validate.extend((self.mt5_dev / "Include/ProjectQuantum").rglob("*.mqh"))
        files_to_validate.extend((self.mt5_dev / "Experts/ProjectQuantum").rglob("*.mq5"))
        files_to_validate.extend((self.mt5_dev / "Scripts/ProjectQuantum").rglob("*.mq5"))
        
        for file_path in files_to_validate:
            try:
                # Check file exists and not empty
                if not file_path.exists() or file_path.stat().st_size == 0:
                    validation_results["errors"].append(f"Invalid file: {file_path}")
                    validation_results["files_failed"] += 1
                    continue
                
                # Check required properties
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Try with latin-1 encoding as fallback
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            content = f.read()
                    except Exception as encoding_err:
                        validation_results["errors"].append(f"Encoding error for {file_path}: {encoding_err}")
                        validation_results["files_failed"] += 1
                        continue
                
                if '#property strict' not in content:
                    validation_results["errors"].append(f"Missing #property strict: {file_path}")
                    validation_results["files_failed"] += 1
                    continue
                
                validation_results["files_validated"] += 1
                
            except Exception as e:
                validation_results["errors"].append(f"Error validating {file_path}: {e}")
                validation_results["files_failed"] += 1
        
        print(f"✅ Validated: {validation_results['files_validated']} files")
        if validation_results["files_failed"] > 0:
            print(f"❌ Failed: {validation_results['files_failed']} files")
            for error in validation_results["errors"]:
                print(f"   • {error}")
            return False
        
        return True
    
    def create_backup(self, terminal_path):
        """Create backup of current terminal files

        Args:
            terminal_path: Path to the terminal directory

        Returns:
            Path to the backup directory

        Raises:
            OSError: If backup directory cannot be created
            PermissionError: If files cannot be copied
        """
        backup_dir = self.project_root / f"backups/{terminal_path.parent.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Failed to create backup directory {backup_dir}: {e}") from e

        print(f"📦 Creating backup: {backup_dir}")

        # Backup existing ProjectQuantum files
        items_backed_up = 0
        backup_errors = []

        for folder in ["Include/ProjectQuantum", "Experts", "Scripts"]:
            source_folder = terminal_path / folder
            if source_folder.exists():
                for item in source_folder.rglob("ProjectQuantum*"):
                    if item.is_file():
                        rel_path = item.relative_to(terminal_path)
                        backup_path = backup_dir / rel_path
                        try:
                            backup_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, backup_path)
                            items_backed_up += 1
                        except PermissionError as e:
                            backup_errors.append(f"Permission denied: {item}")
                        except shutil.Error as e:
                            backup_errors.append(f"Copy failed for {item}: {e}")
                        except OSError as e:
                            backup_errors.append(f"OS error for {item}: {e}")

        print(f"   📄 Backed up {items_backed_up} files")
        if backup_errors:
            print(f"   ⚠️  {len(backup_errors)} backup errors:")
            for err in backup_errors[:5]:  # Show first 5 errors
                print(f"      • {err}")
            if len(backup_errors) > 5:
                print(f"      ... and {len(backup_errors) - 5} more")

        self.deployment_log.append(f"Created backup with {items_backed_up} files ({len(backup_errors)} errors)")

        return backup_dir
    
    def deploy_to_terminal(self, terminal_info):
        """Deploy ProjectQuantum to a specific terminal"""
        terminal_path = terminal_info["path"]
        terminal_name = terminal_info["name"]
        
        print(f"\n🚀 Deploying to: {terminal_name}")
        print(f"   Path: {terminal_path}")
        
        if not terminal_path.exists():
            print(f"   ❌ Terminal directory not found")
            return False
        
        try:
            # Create backup first
            backup_dir = self.create_backup(terminal_path)
            
            # Deploy files
            deployed_files = 0
            
            # Deploy Include files
            source_includes = self.mt5_dev / "Include/ProjectQuantum"
            target_includes = terminal_path / "Include/ProjectQuantum"

            if source_includes.exists():
                print(f"   📁 Deploying Include files...")
                try:
                    if target_includes.exists():
                        shutil.rmtree(target_includes)
                    shutil.copytree(source_includes, target_includes)
                    deployed_files += len(list(source_includes.rglob("*.mqh")))
                except PermissionError as e:
                    raise PermissionError(f"Cannot deploy include files (permission denied): {e}") from e
                except shutil.Error as e:
                    raise IOError(f"Failed to copy include files: {e}") from e
            
            # Deploy Expert files
            source_experts = self.mt5_dev / "Experts/ProjectQuantum"
            target_experts = terminal_path / "Experts/ProjectQuantum"

            if source_experts.exists():
                print(f"   📁 Deploying Expert files...")
                try:
                    target_experts.mkdir(parents=True, exist_ok=True)
                    for ea_file in source_experts.glob("*.mq5"):
                        shutil.copy2(ea_file, target_experts / ea_file.name)
                        deployed_files += 1
                except PermissionError as e:
                    raise PermissionError(f"Cannot deploy expert files (permission denied): {e}") from e
                except shutil.Error as e:
                    raise IOError(f"Failed to copy expert files: {e}") from e
            
            # Deploy Script files
            source_scripts = self.mt5_dev / "Scripts/ProjectQuantum"
            target_scripts = terminal_path / "Scripts/ProjectQuantum"

            if source_scripts.exists():
                print(f"   📁 Deploying Script files...")
                try:
                    target_scripts.mkdir(parents=True, exist_ok=True)
                    for script_file in source_scripts.glob("*.mq5"):
                        shutil.copy2(script_file, target_scripts / script_file.name)
                        deployed_files += 1
                except PermissionError as e:
                    raise PermissionError(f"Cannot deploy script files (permission denied): {e}") from e
                except shutil.Error as e:
                    raise IOError(f"Failed to copy script files: {e}") from e
            
            # Deploy master include
            master_include = self.mt5_dev / "Include/ProjectQuantum.mqh"
            if master_include.exists():
                try:
                    shutil.copy2(master_include, terminal_path / "Include/ProjectQuantum.mqh")
                    deployed_files += 1
                except PermissionError as e:
                    raise PermissionError(f"Cannot deploy master include (permission denied): {e}") from e
                except shutil.Error as e:
                    raise IOError(f"Failed to copy master include: {e}") from e
            
            print(f"   ✅ Deployed {deployed_files} files successfully")
            self.deployment_log.append(f"{terminal_name}: Deployed {deployed_files} files")
            
            # Create deployment manifest
            self.create_deployment_manifest(terminal_path)
            
            return True
            
        except Exception as e:
            print(f"   ❌ Deployment failed: {e}")
            self.deployment_log.append(f"{terminal_name}: Failed - {e}")
            return False
    
    def create_deployment_manifest(self, terminal_path):
        """Create deployment manifest with checksums"""
        manifest = {
            "deployment_timestamp": datetime.now().isoformat(),
            "version": "1.216",
            "terminal_path": str(terminal_path),
            "files": {}
        }
        
        # Calculate checksums for all deployed files
        for pattern in ["Include/ProjectQuantum/**/*.mqh", "Experts/ProjectQuantum/*.mq5", "Scripts/ProjectQuantum/*.mq5"]:
            for file_path in terminal_path.glob(pattern):
                if file_path.is_file():
                    rel_path = file_path.relative_to(terminal_path)
                    manifest["files"][str(rel_path)] = {
                        "size": file_path.stat().st_size,
                        "checksum": self.calculate_checksum(file_path),
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    }
        
        manifest_path = terminal_path / "ProjectQuantum_Deployment.json"
        try:
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            print(f"   📄 Created deployment manifest")
        except PermissionError as e:
            print(f"   ⚠️  Cannot write deployment manifest (permission denied): {e}")
        except IOError as e:
            print(f"   ⚠️  Error writing deployment manifest: {e}")
    
    def verify_deployment(self, terminal_path):
        """Verify deployment integrity"""
        manifest_path = terminal_path / "ProjectQuantum_Deployment.json"
        
        if not manifest_path.exists():
            print(f"   ❌ No deployment manifest found")
            return False

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON in deployment manifest: {e}")
            return False
        except PermissionError as e:
            print(f"   ❌ Cannot read deployment manifest (permission denied): {e}")
            return False
        except IOError as e:
            print(f"   ❌ Error reading deployment manifest: {e}")
            return False
        
        print(f"   🔍 Verifying {len(manifest['files'])} files...")
        
        verified = 0
        failed = 0
        
        for rel_path, file_info in manifest["files"].items():
            file_path = terminal_path / rel_path
            
            if not file_path.exists():
                print(f"      ❌ Missing: {rel_path}")
                failed += 1
                continue
            
            try:
                current_checksum = self.calculate_checksum(file_path)
            except (FileNotFoundError, PermissionError, IOError) as e:
                print(f"      ❌ Cannot verify {rel_path}: {e}")
                failed += 1
                continue

            if current_checksum != file_info["checksum"]:
                print(f"      ❌ Modified: {rel_path}")
                failed += 1
            else:
                verified += 1
        
        if failed == 0:
            print(f"   ✅ All {verified} files verified")
            return True
        else:
            print(f"   ❌ Verification failed: {failed} issues")
            return False
    
    def deploy_all(self):
        """Deploy to all configured terminals"""
        print("🚀 ProjectQuantum Production Deployment")
        print("=" * 50)
        print(f"Version: 1.216")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Validate files first
        if not self.validate_files():
            print("\n❌ Validation failed - aborting deployment")
            return False
        
        # Deploy to each terminal
        success_count = 0
        for terminal in self.production_terminals:
            if terminal["active"]:
                if self.deploy_to_terminal(terminal):
                    # Verify deployment
                    if self.verify_deployment(terminal["path"]):
                        success_count += 1
                    else:
                        print(f"   ⚠️  Deployment verification failed")
            else:
                print(f"\n⏭️  Skipping inactive terminal: {terminal['name']}")
        
        # Generate deployment report
        self.generate_deployment_report(success_count)
        
        return success_count > 0
    
    def generate_deployment_report(self, success_count):
        """Generate deployment report"""
        report_path = self.project_root / f"deployment_reports/deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            report_path.parent.mkdir(exist_ok=True)
        except OSError as e:
            print(f"   ⚠️  Cannot create report directory: {e}")
            return

        report = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.216",
            "terminals_total": len([t for t in self.production_terminals if t["active"]]),
            "terminals_success": success_count,
            "deployment_log": self.deployment_log
        }

        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
        except PermissionError as e:
            print(f"   ⚠️  Cannot write deployment report (permission denied): {e}")
            return
        except IOError as e:
            print(f"   ⚠️  Error writing deployment report: {e}")
            return
        
        print(f"\n📊 DEPLOYMENT SUMMARY")
        print("=" * 30)
        print(f"Terminals deployed: {success_count}/{len([t for t in self.production_terminals if t['active']])}")
        print(f"Report saved: {report_path}")
        
        if success_count == len([t for t in self.production_terminals if t["active"]]):
            print("\n🎉 DEPLOYMENT SUCCESSFUL!")
            print("✅ ProjectQuantum v1.216 deployed to all active terminals")
        else:
            print("\n⚠️  PARTIAL DEPLOYMENT")
            print("Some terminals failed - check logs above")

if __name__ == "__main__":
    deployer = ProductionDeployer()
    success = deployer.deploy_all()
    sys.exit(0 if success else 1)