#!/usr/bin/env python3
"""
ProjectQuantum Unified Sync Manager
Consolidated synchronization functionality for MT5 terminals

Combines:
- sync_to_mql5_terminal.py
- reverse_sync_from_terminal.py
- verify_sync_integrity.py
- branch_sync_checker.py

Author: Renier De Jager
Version: 1.216
"""

import os
import shutil
import hashlib
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class FileHashManager:
    """Manages file hashing for sync verification"""
    
    @staticmethod
    def compute_hash(file_path: Path) -> Optional[str]:
        """Compute SHA256 hash for file comparison.

        Args:
            file_path: Path to the file to hash

        Returns:
            Hex string of SHA256 hash, or None if file doesn't exist or cannot be read
        """
        if not file_path.exists():
            return None

        if not file_path.is_file():
            print(f"⚠️  Cannot hash non-file: {file_path}")
            return None

        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except PermissionError:
            print(f"⚠️  Permission denied reading file for hash: {file_path}")
            return None
        except IOError as e:
            print(f"⚠️  I/O error computing hash for {file_path}: {e}")
            return None
        except Exception as e:
            print(f"⚠️  Unexpected error computing hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def files_are_identical(file1: Path, file2: Path) -> bool:
        """Check if two files are identical using hash comparison.

        Args:
            file1: Path to the first file
            file2: Path to the second file

        Returns:
            True if both files exist, are readable, and have identical content.
            False if files differ, don't exist, or cannot be read.
        """
        if not file1.exists():
            return False
        if not file2.exists():
            return False

        hash1 = FileHashManager.compute_hash(file1)
        hash2 = FileHashManager.compute_hash(file2)

        # If either hash computation failed, files are not identical
        if hash1 is None or hash2 is None:
            return False

        return hash1 == hash2


class MT5SyncEngine:
    """Core synchronization engine for MT5 files"""
    
    def __init__(self, dev_dir: Path, mt5_terminals: List[Path]):
        self.dev_dir = dev_dir
        self.mt5_terminals = mt5_terminals
        self.sync_manifest = {}
    
    def sync_file(self, src_path: Path, dst_path: Path, create_backup: bool = True) -> Dict[str, Any]:
        """Sync a single file with hash comparison.

        Args:
            src_path: Source file path
            dst_path: Destination file path
            create_backup: Whether to create a backup of existing destination file

        Returns:
            Dictionary with sync result containing success, action, error, and backup_created fields
        """
        result = {
            "success": False,
            "action": "none",
            "error": None,
            "backup_created": False
        }

        # Validate source file exists and is readable
        if not src_path.exists():
            result["error"] = f"Source file does not exist: {src_path}"
            print(f"  ❌ Error: Source not found - {src_path.name}")
            return result

        if not src_path.is_file():
            result["error"] = f"Source is not a file: {src_path}"
            print(f"  ❌ Error: Source is not a file - {src_path.name}")
            return result

        try:
            # Create destination directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            result["error"] = f"Permission denied creating directory: {dst_path.parent}"
            print(f"  ❌ Error: Permission denied for directory - {dst_path.parent}")
            return result
        except OSError as e:
            result["error"] = f"Cannot create directory {dst_path.parent}: {e}"
            print(f"  ❌ Error: Cannot create directory - {e}")
            return result

        try:
            # Check if files are different
            if FileHashManager.files_are_identical(src_path, dst_path):
                result["action"] = "unchanged"
                result["success"] = True
                print(f"  ✓ Unchanged: {src_path.name}")
                return result

            # Create backup if destination exists and backup is requested
            if create_backup and dst_path.exists():
                backup_path = dst_path.with_suffix(dst_path.suffix + '.backup')
                try:
                    shutil.copy2(dst_path, backup_path)
                    result["backup_created"] = True
                    print(f"  📋 Backup: {dst_path.name} -> {backup_path.name}")
                except PermissionError:
                    print(f"  ⚠️  Warning: Cannot create backup (permission denied): {backup_path}")
                except shutil.Error as e:
                    print(f"  ⚠️  Warning: Backup failed: {e}")

            # Copy file
            shutil.copy2(src_path, dst_path)
            result["action"] = "synced"
            result["success"] = True
            print(f"  ✅ Synced: {src_path.name}")

        except PermissionError:
            result["error"] = f"Permission denied copying file: {src_path} -> {dst_path}"
            print(f"  ❌ Error: Permission denied - {src_path.name}")
        except shutil.Error as e:
            result["error"] = f"Copy error: {e}"
            print(f"  ❌ Error: Copy failed - {src_path.name}: {e}")
        except IOError as e:
            result["error"] = f"I/O error: {e}"
            print(f"  ❌ Error: I/O error - {src_path.name}: {e}")
        except Exception as e:
            result["error"] = f"Unexpected error: {e}"
            print(f"  ❌ Error: {src_path.name} - {e}")

        return result
    
    def sync_directory_batch(self, sync_mappings: List[Tuple[str, str]], 
                           source_base: Path, target_base: Path, 
                           description: str = "Sync") -> Dict[str, Any]:
        """Sync multiple files based on mapping list"""
        
        print(f"🔄 {description}")
        print(f"Source: {source_base}")
        print(f"Target: {target_base}")
        print()
        
        results = {
            "total_files": len(sync_mappings),
            "synced": 0,
            "unchanged": 0,
            "errors": 0,
            "file_results": []
        }
        
        for src_rel, dst_rel in sync_mappings:
            src_path = source_base / src_rel
            dst_path = target_base / dst_rel
            
            if not src_path.exists():
                error_result = {
                    "file": src_rel,
                    "success": False,
                    "action": "error",
                    "error": "Source file not found"
                }
                results["file_results"].append(error_result)
                results["errors"] += 1
                print(f"  ❌ Not found: {src_rel}")
                continue
            
            sync_result = self.sync_file(src_path, dst_path)
            sync_result["file"] = src_rel
            results["file_results"].append(sync_result)
            
            if sync_result["success"]:
                if sync_result["action"] == "synced":
                    results["synced"] += 1
                elif sync_result["action"] == "unchanged":
                    results["unchanged"] += 1
            else:
                results["errors"] += 1
        
        # Print summary
        print(f"\n📊 {description} Summary:")
        print(f"   Total files: {results['total_files']}")
        print(f"   ✅ Synced: {results['synced']}")
        print(f"   ✓ Unchanged: {results['unchanged']}")
        print(f"   ❌ Errors: {results['errors']}")
        
        return results


class ProjectQuantumSyncManager:
    """Main sync manager for ProjectQuantum files"""
    
    def __init__(self):
        self.dev_dir = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        
        # MT5 Terminal directories
        self.mt5_terminals = [
            Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/8A503E260F28D3DD9CC9A37AA3CE29BC/MQL5"),
            Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/29BC03B6BB995A90C75D3603F5C8A659/MQL5"),
            Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/95E092767220F643BF1B1CCEEF7AD317/MQL5"),
            Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5")
        ]
        
        # Primary terminal (first in list)
        self.primary_terminal = self.mt5_terminals[0] if self.mt5_terminals else None
        
        # Initialize sync engine
        self.sync_engine = MT5SyncEngine(self.dev_dir, self.mt5_terminals)
        
        # Define sync mappings
        self.core_files = [
            # Main EA
            ("Experts/ProjectQuantum_Main.mq5", "Experts/ProjectQuantum_Main.mq5"),
            
            # Core Architecture
            ("Include/ProjectQuantum/Architecture/ProjectQuantum_Architecture.mqh", "Include/ProjectQuantum/Architecture/ProjectQuantum_Architecture.mqh"),
            ("Include/ProjectQuantum/Architecture/Journey_Architecture.mqh", "Include/ProjectQuantum/Architecture/Journey_Architecture.mqh"),
            
            # Security System
            ("Include/ProjectQuantum/Core/CVersionManager.mqh", "Include/ProjectQuantum/Core/CVersionManager.mqh"),
            ("Include/ProjectQuantum/Core/CFileIntegrity.mqh", "Include/ProjectQuantum/Core/CFileIntegrity.mqh"),
            
            # Core Components
            ("Include/ProjectQuantum/Core/Core.mqh", "Include/ProjectQuantum/Core/Core.mqh"),
            ("Include/ProjectQuantum/Core/CLogger.mqh", "Include/ProjectQuantum/Core/CLogger.mqh"),
            ("Include/ProjectQuantum/Core/CPersistence.mqh", "Include/ProjectQuantum/Core/CPersistence.mqh"),
            ("Include/ProjectQuantum/Core/ArrayUtils.mqh", "Include/ProjectQuantum/Core/ArrayUtils.mqh"),
            ("Include/ProjectQuantum/Core/SafeMath.mqh", "Include/ProjectQuantum/Core/SafeMath.mqh"),
            ("Include/ProjectQuantum/Core/SymbolUtils.mqh", "Include/ProjectQuantum/Core/SymbolUtils.mqh"),
            ("Include/ProjectQuantum/Core/Defensive.mqh", "Include/ProjectQuantum/Core/Defensive.mqh"),
            ("Include/ProjectQuantum/Core/TestFramework.mqh", "Include/ProjectQuantum/Core/TestFramework.mqh"),
            
            # Intelligence
            ("Include/ProjectQuantum/Intelligence/CRL_Agent.mqh", "Include/ProjectQuantum/Intelligence/CRL_Agent.mqh"),
            ("Include/ProjectQuantum/Intelligence/Intelligence.mqh", "Include/ProjectQuantum/Intelligence/Intelligence.mqh"),
            
            # Physics
            ("Include/ProjectQuantum/Physics/CMarketPhysics.mqh", "Include/ProjectQuantum/Physics/CMarketPhysics.mqh"),
            ("Include/ProjectQuantum/Physics/Physics.mqh", "Include/ProjectQuantum/Physics/Physics.mqh"),
            
            # Risk Management
            ("Include/ProjectQuantum/Risk/CAdversarialRisk.mqh", "Include/ProjectQuantum/Risk/CAdversarialRisk.mqh"),
            ("Include/ProjectQuantum/Risk/Risk.mqh", "Include/ProjectQuantum/Risk/Risk.mqh"),
            
            # Main Integration
            ("Include/ProjectQuantum/ProjectQuantum.mqh", "Include/ProjectQuantum/ProjectQuantum.mqh"),
            
            # Test Scripts
            ("Scripts/ProjectQuantum/Test_SafeMath.mq5", "Scripts/ProjectQuantum/Test_SafeMath.mq5"),
            ("Scripts/ProjectQuantum/Test_ArrayUtils.mq5", "Scripts/ProjectQuantum/Test_ArrayUtils.mq5"),
            ("Scripts/ProjectQuantum/Test_Defensive.mq5", "Scripts/ProjectQuantum/Test_Defensive.mq5"),
        ]
    
    def verify_terminal_access(self) -> Dict[str, Any]:
        """Verify access to MT5 terminals"""
        print("🔍 Verifying MT5 terminal access...")
        
        verification = {
            "accessible_terminals": [],
            "inaccessible_terminals": [],
            "primary_terminal_ok": False
        }
        
        for i, terminal in enumerate(self.mt5_terminals):
            if terminal.exists():
                verification["accessible_terminals"].append(str(terminal))
                print(f"   ✅ Terminal {i+1}: {terminal}")
                
                if i == 0:  # Primary terminal
                    verification["primary_terminal_ok"] = True
            else:
                verification["inaccessible_terminals"].append(str(terminal))
                print(f"   ❌ Terminal {i+1}: {terminal} (not found)")
        
        print(f"\n📊 Terminal Status: {len(verification['accessible_terminals'])}/{len(self.mt5_terminals)} accessible")
        
        return verification
    
    def sync_to_terminals(self, sync_all_terminals: bool = False) -> Dict[str, Any]:
        """Sync files from development directory to MT5 terminals"""
        
        print("🚀 ProjectQuantum → MT5 Terminals Sync")
        print("=" * 60)
        
        # Verify terminal access
        verification = self.verify_terminal_access()
        
        if not verification["primary_terminal_ok"] and not sync_all_terminals:
            print("❌ Primary terminal not accessible and sync_all_terminals=False")
            return {"error": "Primary terminal not accessible"}
        
        # Determine target terminals
        if sync_all_terminals:
            target_terminals = [Path(t) for t in verification["accessible_terminals"]]
        else:
            target_terminals = [self.primary_terminal] if verification["primary_terminal_ok"] else []
        
        if not target_terminals:
            print("❌ No accessible terminals found")
            return {"error": "No accessible terminals"}
        
        # Sync to each terminal
        all_results = {}
        
        for i, terminal in enumerate(target_terminals, 1):
            print(f"\n📁 Syncing to Terminal {i}: {terminal.name}")
            print("-" * 50)
            
            terminal_results = self.sync_engine.sync_directory_batch(
                self.core_files,
                self.dev_dir,
                terminal,
                f"Dev → Terminal {i}"
            )
            
            all_results[f"terminal_{i}"] = terminal_results
        
        # Generate overall summary
        total_terminals = len(target_terminals)
        successful_terminals = sum(1 for r in all_results.values() if r["errors"] == 0)
        
        overall_results = {
            "timestamp": datetime.now().isoformat(),
            "terminals_synced": total_terminals,
            "successful_terminals": successful_terminals,
            "terminal_results": all_results,
            "success_rate": (successful_terminals / total_terminals) * 100 if total_terminals > 0 else 0
        }
        
        print(f"\n🎯 OVERALL SYNC SUMMARY")
        print("=" * 30)
        print(f"Terminals synced: {successful_terminals}/{total_terminals}")
        print(f"Success rate: {overall_results['success_rate']:.1f}%")
        
        return overall_results
    
    def reverse_sync_from_primary(self, file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Reverse sync from primary terminal back to development directory"""
        
        print("🔄 MT5 Primary Terminal → Development Reverse Sync")
        print("=" * 60)
        
        if not self.primary_terminal or not self.primary_terminal.exists():
            print("❌ Primary terminal not accessible")
            return {"error": "Primary terminal not accessible"}
        
        # Use provided patterns or default core files
        if file_patterns:
            # Create custom mappings from patterns
            reverse_mappings = []
            for pattern in file_patterns:
                # Simple pattern matching - can be enhanced
                if pattern.endswith('.mq5') or pattern.endswith('.mqh'):
                    reverse_mappings.append((pattern, pattern))
        else:
            # Use core files in reverse
            reverse_mappings = [(dst, src) for src, dst in self.core_files]
        
        print(f"Source: {self.primary_terminal}")
        print(f"Target: {self.dev_dir}")
        print()
        
        results = self.sync_engine.sync_directory_batch(
            reverse_mappings,
            self.primary_terminal,
            self.dev_dir,
            "Terminal → Dev (Reverse Sync)"
        )
        
        # Add timestamp
        results["timestamp"] = datetime.now().isoformat()
        results["source_terminal"] = str(self.primary_terminal)
        
        return results
    
    def verify_sync_integrity(self) -> Dict[str, Any]:
        """Verify integrity of sync across terminals"""
        
        print("🔍 Verifying sync integrity across terminals...")
        
        verification = {
            "timestamp": datetime.now().isoformat(),
            "files_checked": 0,
            "files_in_sync": 0,
            "files_out_of_sync": 0,
            "missing_files": 0,
            "integrity_issues": []
        }
        
        accessible_terminals = [t for t in self.mt5_terminals if t.exists()]
        
        if len(accessible_terminals) < 2:
            print("⚠️  Need at least 2 terminals for integrity verification")
            return verification
        
        print(f"Checking integrity across {len(accessible_terminals)} terminals...")
        
        # Check each core file
        for src_rel, _ in self.core_files:
            verification["files_checked"] += 1
            
            # Get file from development directory as reference
            dev_file = self.dev_dir / src_rel
            if not dev_file.exists():
                verification["missing_files"] += 1
                verification["integrity_issues"].append(f"Missing in dev: {src_rel}")
                continue
            
            dev_hash = FileHashManager.compute_hash(dev_file)
            
            # Check against all terminals
            terminal_hashes = {}
            for terminal in accessible_terminals:
                terminal_file = terminal / src_rel
                if terminal_file.exists():
                    terminal_hashes[str(terminal)] = FileHashManager.compute_hash(terminal_file)
                else:
                    terminal_hashes[str(terminal)] = None
                    verification["missing_files"] += 1
                    verification["integrity_issues"].append(f"Missing in {terminal.name}: {src_rel}")
            
            # Check if all hashes match dev hash
            all_match = all(h == dev_hash for h in terminal_hashes.values() if h is not None)
            
            if all_match and all(h is not None for h in terminal_hashes.values()):
                verification["files_in_sync"] += 1
                print(f"   ✅ {src_rel}")
            else:
                verification["files_out_of_sync"] += 1
                verification["integrity_issues"].append(f"Hash mismatch: {src_rel}")
                print(f"   ❌ {src_rel} (hash mismatch)")
        
        # Print summary
        print(f"\n📊 Integrity Verification Summary:")
        print(f"   Files checked: {verification['files_checked']}")
        print(f"   ✅ In sync: {verification['files_in_sync']}")
        print(f"   ❌ Out of sync: {verification['files_out_of_sync']}")
        print(f"   📂 Missing: {verification['missing_files']}")
        
        integrity_percentage = (verification['files_in_sync'] / verification['files_checked']) * 100 if verification['files_checked'] > 0 else 0
        verification["integrity_percentage"] = integrity_percentage
        
        print(f"   🎯 Integrity: {integrity_percentage:.1f}%")
        
        return verification
    
    def check_branch_sync_status(self) -> Dict[str, Any]:
        """Check git branch sync status.

        Returns:
            Dictionary with branch status including current_branch, uncommitted changes,
            unpushed commits, and sync recommendation. Contains 'error' key on failure.
        """
        print("🌿 Checking git branch sync status...")

        # Check if project root exists and is a git repository
        if not self.project_root.exists():
            print(f"   ❌ Project root does not exist: {self.project_root}")
            return {"error": f"Project root does not exist: {self.project_root}"}

        git_dir = self.project_root / ".git"
        if not git_dir.exists():
            print(f"   ❌ Not a git repository: {self.project_root}")
            return {"error": f"Not a git repository: {self.project_root}"}

        try:
            # Get current branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True, cwd=self.project_root,
                timeout=30  # Add timeout to prevent hanging
            )
            if branch_result.returncode != 0:
                error_msg = branch_result.stderr.strip() or "Unknown git error"
                print(f"   ❌ Error getting current branch: {error_msg}")
                return {"error": f"Git branch command failed: {error_msg}"}

            current_branch = branch_result.stdout.strip()

            # Get git status
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True, text=True, cwd=self.project_root,
                timeout=30
            )
            if status_result.returncode != 0:
                error_msg = status_result.stderr.strip() or "Unknown git error"
                print(f"   ⚠️  Warning: Could not get git status: {error_msg}")
                git_status = ""
            else:
                git_status = status_result.stdout.strip()

            # Check for unpushed commits (may fail if no upstream is set)
            try:
                unpushed_result = subprocess.run(
                    ['git', 'log', '@{u}..HEAD', '--oneline'],
                    capture_output=True, text=True, cwd=self.project_root,
                    timeout=30
                )
                if unpushed_result.returncode == 0:
                    unpushed_commits = unpushed_result.stdout.strip()
                else:
                    # No upstream set, or other error - not a fatal condition
                    unpushed_commits = ""
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Warning: Timeout checking unpushed commits")
                unpushed_commits = ""

            branch_status = {
                "current_branch": current_branch,
                "has_uncommitted_changes": bool(git_status),
                "uncommitted_files": git_status.split('\n') if git_status else [],
                "has_unpushed_commits": bool(unpushed_commits),
                "unpushed_commits": unpushed_commits.split('\n') if unpushed_commits else [],
                "sync_recommended": False
            }

            # Determine if sync is recommended
            if not branch_status["has_uncommitted_changes"] and not branch_status["has_unpushed_commits"]:
                branch_status["sync_recommended"] = True

            print(f"   Current branch: {current_branch}")
            print(f"   Uncommitted changes: {'Yes' if branch_status['has_uncommitted_changes'] else 'No'}")
            print(f"   Unpushed commits: {'Yes' if branch_status['has_unpushed_commits'] else 'No'}")
            print(f"   Sync recommended: {'Yes' if branch_status['sync_recommended'] else 'No'}")

            return branch_status

        except subprocess.TimeoutExpired:
            print(f"   ❌ Git command timed out")
            return {"error": "Git command timed out"}
        except FileNotFoundError:
            print(f"   ❌ Git is not installed or not in PATH")
            return {"error": "Git is not installed or not in PATH"}
        except Exception as e:
            print(f"   ❌ Error checking git status: {e}")
            return {"error": str(e)}
    
    def generate_sync_manifest(self) -> Path:
        """Generate comprehensive sync manifest"""
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.216",
            "sync_mappings": {
                "core_files": self.core_files
            },
            "terminal_info": {
                "development_directory": str(self.dev_dir),
                "mt5_terminals": [str(t) for t in self.mt5_terminals],
                "primary_terminal": str(self.primary_terminal) if self.primary_terminal else None
            }
        }
        
        manifest_path = self.project_root / "sync_manifest.json"
        try:
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            print(f"📄 Sync manifest saved: {manifest_path}")
        except PermissionError:
            print(f"❌ Cannot save manifest (permission denied): {manifest_path}")
            raise
        except IOError as e:
            print(f"❌ Error saving manifest: {manifest_path} - {e}")
            raise

        return manifest_path


def main():
    """Main entry point for sync manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ProjectQuantum Unified Sync Manager')
    parser.add_argument('--to-terminals', action='store_true', help='Sync from dev to terminals')
    parser.add_argument('--from-terminal', action='store_true', help='Reverse sync from primary terminal')
    parser.add_argument('--verify-integrity', action='store_true', help='Verify sync integrity')
    parser.add_argument('--check-git', action='store_true', help='Check git branch status')
    parser.add_argument('--all-terminals', action='store_true', help='Sync to all accessible terminals')
    parser.add_argument('--generate-manifest', action='store_true', help='Generate sync manifest')
    
    args = parser.parse_args()
    
    sync_manager = ProjectQuantumSyncManager()
    
    success = True
    
    if args.to_terminals:
        results = sync_manager.sync_to_terminals(sync_all_terminals=args.all_terminals)
        if "error" in results or results.get("success_rate", 0) < 80:
            success = False
    
    elif args.from_terminal:
        results = sync_manager.reverse_sync_from_primary()
        if "error" in results or results.get("errors", 0) > 0:
            success = False
    
    elif args.verify_integrity:
        results = sync_manager.verify_sync_integrity()
        if results.get("integrity_percentage", 0) < 90:
            success = False
    
    elif args.check_git:
        results = sync_manager.check_branch_sync_status()
        if "error" in results:
            success = False
    
    elif args.generate_manifest:
        manifest_path = sync_manager.generate_sync_manifest()
        print(f"Manifest generated: {manifest_path}")
    
    else:
        # Default: comprehensive sync check
        print("🔍 Running comprehensive sync status check...")
        
        # Check git status
        git_status = sync_manager.check_branch_sync_status()
        
        # Verify terminal access
        terminal_status = sync_manager.verify_terminal_access()
        
        # Check integrity if terminals are accessible
        if terminal_status["primary_terminal_ok"]:
            integrity_status = sync_manager.verify_sync_integrity()
            
            if integrity_status.get("integrity_percentage", 0) < 90:
                print("\n⚠️  Integrity issues detected - consider running sync")
                success = False
            else:
                print("\n✅ Sync integrity verified")
        
        print("\nUse --help for specific sync operations")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())