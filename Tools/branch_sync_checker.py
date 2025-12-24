#!/usr/bin/env python3
"""
Branch Synchronization Checker
Analyzes the 3-branch structure and synchronization status
"""

import os
import subprocess
from pathlib import Path
import json

class BranchSyncChecker:
    def __init__(self):
        self.mt5_root = Path("/mnt/c/DevCenter/MT5-Unified")
        self.branches = {
            'MQL5-Development': self.mt5_root / "MQL5-Development",
            'MT5-Core': self.mt5_root / "MT5-Core", 
            'Testing': self.mt5_root / "Testing"
        }
        
        self.sync_results = {
            'branch_status': {},
            'file_synchronization': {},
            'git_repositories': {},
            'overall_sync_status': 'unknown'
        }
    
    def check_branch_synchronization(self):
        """Check synchronization status across all 3 branches"""
        print("🔄 BRANCH SYNCHRONIZATION CHECKER")
        print("🔍 Analyzing 3-branch structure and sync status...")
        print("=" * 60)
        
        # Check branch existence and structure
        self._check_branch_structure()
        
        # Check for git repositories
        self._check_git_repositories()
        
        # Analyze file synchronization
        self._analyze_file_synchronization()
        
        # Check ProjectQuantum main files
        self._check_projectquantum_sync()
        
        # Generate sync report
        self._generate_sync_report()
        
        return self.sync_results
    
    def _check_branch_structure(self):
        """Check if all 3 branches exist and their structure"""
        print("🔧 Checking Branch Structure...")
        
        for branch_name, branch_path in self.branches.items():
            branch_info = {
                'exists': branch_path.exists(),
                'is_directory': branch_path.is_dir(),
                'contents': []
            }
            
            if branch_info['exists'] and branch_info['is_directory']:
                try:
                    contents = [item.name for item in branch_path.iterdir()]
                    branch_info['contents'] = sorted(contents)
                    branch_info['file_count'] = len([item for item in branch_path.rglob('*') if item.is_file()])
                    branch_info['dir_count'] = len([item for item in branch_path.rglob('*') if item.is_dir()])
                except Exception as e:
                    branch_info['error'] = str(e)
            
            self.sync_results['branch_status'][branch_name] = branch_info
            
            status = "✅ EXISTS" if branch_info['exists'] else "❌ MISSING"
            file_count = branch_info.get('file_count', 0)
            print(f"   {status} {branch_name}: {file_count} files")
            
            if branch_info['exists']:
                main_folders = [item for item in branch_info['contents'] 
                              if item in ['Experts', 'Include', 'Indicators', 'Scripts', 'Libraries']]
                if main_folders:
                    print(f"      📁 Main folders: {', '.join(main_folders)}")
    
    def _check_git_repositories(self):
        """Check for git repositories in each branch"""
        print("🔧 Checking Git Repositories...")
        
        for branch_name, branch_path in self.branches.items():
            git_info = {
                'has_git': False,
                'git_status': 'unknown',
                'current_branch': 'unknown',
                'remote_info': 'unknown'
            }
            
            if branch_path.exists():
                git_dir = branch_path / '.git'
                git_info['has_git'] = git_dir.exists()
                
                if git_info['has_git']:
                    try:
                        # Get git status
                        result = subprocess.run(['git', 'status', '--porcelain'], 
                                              cwd=branch_path, capture_output=True, text=True)
                        if result.returncode == 0:
                            modified_files = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                            git_info['git_status'] = f"{modified_files} modified files"
                        
                        # Get current branch
                        result = subprocess.run(['git', 'branch', '--show-current'], 
                                              cwd=branch_path, capture_output=True, text=True)
                        if result.returncode == 0:
                            git_info['current_branch'] = result.stdout.strip()
                        
                        # Get remote info
                        result = subprocess.run(['git', 'remote', '-v'], 
                                              cwd=branch_path, capture_output=True, text=True)
                        if result.returncode == 0:
                            remotes = result.stdout.strip().split('\n')
                            git_info['remote_info'] = f"{len(remotes)} remotes configured"
                            
                    except Exception as e:
                        git_info['error'] = str(e)
            
            self.sync_results['git_repositories'][branch_name] = git_info
            
            status = "✅ GIT REPO" if git_info['has_git'] else "❌ NO GIT"
            branch_info = git_info.get('current_branch', 'unknown')
            print(f"   {status} {branch_name}: branch '{branch_info}', {git_info.get('git_status', 'unknown')}")
    
    def _analyze_file_synchronization(self):
        """Analyze file synchronization between branches"""
        print("🔧 Analyzing File Synchronization...")
        
        # Key files to check for synchronization
        key_files = [
            'Experts/ProjectQuantum_Main.mq5',
            'Include/ProjectQuantum/Core/Core.mqh',
            'Include/ProjectQuantum/Architecture/ProjectQuantum_Architecture.mqh',
            'Include/ProjectQuantum/Intelligence/CRL_Agent.mqh',
            'Include/ProjectQuantum/Risk/CRiskManager.mqh'
        ]
        
        file_sync_status = {}
        
        for file_path in key_files:
            file_status = {}
            
            for branch_name, branch_root in self.branches.items():
                full_path = branch_root / file_path
                file_status[branch_name] = {
                    'exists': full_path.exists(),
                    'size': full_path.stat().st_size if full_path.exists() else 0,
                    'modified_time': full_path.stat().st_mtime if full_path.exists() else 0
                }
            
            # Check if files are synchronized
            existing_branches = [branch for branch, info in file_status.items() if info['exists']]
            
            if len(existing_branches) > 1:
                sizes = [file_status[branch]['size'] for branch in existing_branches]
                times = [file_status[branch]['modified_time'] for branch in existing_branches]
                
                size_synchronized = len(set(sizes)) == 1
                time_synchronized = max(times) - min(times) < 60  # Within 1 minute
                
                sync_status = 'synced' if size_synchronized and time_synchronized else 'out_of_sync'
            else:
                sync_status = 'missing_in_branches'
            
            file_sync_status[file_path] = {
                'branch_status': file_status,
                'sync_status': sync_status,
                'existing_branches': existing_branches
            }
            
            status_symbol = {
                'synced': '✅ SYNCED',
                'out_of_sync': '⚠️ OUT OF SYNC', 
                'missing_in_branches': '❌ MISSING'
            }.get(sync_status, '❓ UNKNOWN')
            
            print(f"   {status_symbol} {file_path}: in {len(existing_branches)} branches")
        
        self.sync_results['file_synchronization'] = file_sync_status
    
    def _check_projectquantum_sync(self):
        """Check ProjectQuantum specific synchronization"""
        print("🔧 Checking ProjectQuantum Synchronization...")
        
        # Check for ProjectQuantum main EA in each branch
        pq_main_files = {}
        
        for branch_name, branch_root in self.branches.items():
            pq_paths = [
                branch_root / "Experts/ProjectQuantum_Main.mq5",
                branch_root / "Experts/ProjectQuantum/ProjectQuantum_Main.mq5"
            ]
            
            found_paths = [path for path in pq_paths if path.exists()]
            
            pq_main_files[branch_name] = {
                'found': len(found_paths) > 0,
                'paths': [str(path) for path in found_paths],
                'primary_path': str(found_paths[0]) if found_paths else None
            }
        
        # Check Include directory structure
        include_structure = {}
        
        for branch_name, branch_root in self.branches.items():
            include_path = branch_root / "Include/ProjectQuantum"
            
            if include_path.exists():
                subdirs = [item.name for item in include_path.iterdir() if item.is_dir()]
                file_count = len(list(include_path.rglob('*.mqh')))
                
                include_structure[branch_name] = {
                    'exists': True,
                    'subdirectories': sorted(subdirs),
                    'mqh_file_count': file_count
                }
            else:
                include_structure[branch_name] = {
                    'exists': False,
                    'subdirectories': [],
                    'mqh_file_count': 0
                }
        
        # Report findings
        print("   📊 ProjectQuantum Main EA:")
        for branch_name, info in pq_main_files.items():
            status = "✅ FOUND" if info['found'] else "❌ MISSING"
            print(f"      {status} {branch_name}: {info.get('primary_path', 'N/A')}")
        
        print("   📊 Include Structure:")
        for branch_name, info in include_structure.items():
            status = "✅ EXISTS" if info['exists'] else "❌ MISSING"
            print(f"      {status} {branch_name}: {info['mqh_file_count']} .mqh files")
        
        self.sync_results['projectquantum_sync'] = {
            'main_ea_files': pq_main_files,
            'include_structure': include_structure
        }
    
    def _generate_sync_report(self):
        """Generate comprehensive synchronization report"""
        print("\n🎯 SYNCHRONIZATION STATUS REPORT")
        print("=" * 50)
        
        # Branch availability
        existing_branches = [name for name, info in self.sync_results['branch_status'].items() 
                           if info['exists']]
        
        print(f"📊 Branch Availability: {len(existing_branches)}/3 branches exist")
        for branch_name in existing_branches:
            file_count = self.sync_results['branch_status'][branch_name].get('file_count', 0)
            print(f"   ✅ {branch_name}: {file_count} files")
        
        missing_branches = [name for name, info in self.sync_results['branch_status'].items() 
                          if not info['exists']]
        if missing_branches:
            print(f"   ❌ Missing: {', '.join(missing_branches)}")
        
        # Git repository status
        git_branches = [name for name, info in self.sync_results['git_repositories'].items() 
                       if info['has_git']]
        
        print(f"\n📊 Git Repository Status: {len(git_branches)}/3 branches have git")
        for branch_name in git_branches:
            git_info = self.sync_results['git_repositories'][branch_name]
            print(f"   ✅ {branch_name}: {git_info.get('current_branch', 'unknown')} branch")
        
        # File synchronization status
        sync_status = self.sync_results['file_synchronization']
        synced_files = [file for file, info in sync_status.items() 
                       if info['sync_status'] == 'synced']
        out_of_sync_files = [file for file, info in sync_status.items() 
                           if info['sync_status'] == 'out_of_sync']
        missing_files = [file for file, info in sync_status.items() 
                        if info['sync_status'] == 'missing_in_branches']
        
        print(f"\n📊 File Synchronization:")
        print(f"   ✅ Synced: {len(synced_files)} files")
        print(f"   ⚠️  Out of sync: {len(out_of_sync_files)} files")
        print(f"   ❌ Missing: {len(missing_files)} files")
        
        if out_of_sync_files:
            print(f"\n⚠️  Files needing synchronization:")
            for file_path in out_of_sync_files:
                file_info = sync_status[file_path]
                print(f"      • {file_path} (in {len(file_info['existing_branches'])} branches)")
        
        # ProjectQuantum specific status
        pq_sync = self.sync_results['projectquantum_sync']
        pq_main_branches = [name for name, info in pq_sync['main_ea_files'].items() 
                           if info['found']]
        pq_include_branches = [name for name, info in pq_sync['include_structure'].items() 
                             if info['exists']]
        
        print(f"\n📊 ProjectQuantum Status:")
        print(f"   💰 Main EA: Available in {len(pq_main_branches)}/3 branches")
        print(f"   🏗️  Include System: Available in {len(pq_include_branches)}/3 branches")
        
        # Overall assessment
        overall_score = 0.0
        
        # Branch existence (25%)
        branch_score = len(existing_branches) / 3 * 0.25
        overall_score += branch_score
        
        # File synchronization (50%)
        total_files = len(sync_status)
        if total_files > 0:
            sync_score = len(synced_files) / total_files * 0.5
            overall_score += sync_score
        
        # ProjectQuantum availability (25%)
        pq_score = (len(pq_main_branches) / 3 + len(pq_include_branches) / 3) / 2 * 0.25
        overall_score += pq_score
        
        self.sync_results['overall_sync_status'] = overall_score
        
        print(f"\n🎯 Overall Synchronization Score: {overall_score:.1%}")
        
        if overall_score >= 0.9:
            assessment = "EXCELLENT - All branches fully synchronized"
        elif overall_score >= 0.7:
            assessment = "GOOD - Minor synchronization needed"
        elif overall_score >= 0.5:
            assessment = "ACCEPTABLE - Some branches out of sync"
        else:
            assessment = "POOR - Major synchronization issues"
        
        print(f"📋 Assessment: {assessment}")
        
        # Recommendations
        recommendations = []
        
        if len(existing_branches) < 3:
            recommendations.append("Set up missing branch directories")
        
        if len(git_branches) < len(existing_branches):
            recommendations.append("Initialize git repositories in non-git branches")
        
        if out_of_sync_files:
            recommendations.append(f"Synchronize {len(out_of_sync_files)} out-of-sync files")
        
        if len(pq_main_branches) < 3:
            recommendations.append("Deploy ProjectQuantum Main EA to all branches")
        
        if recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print(f"\n✅ No synchronization issues found!")
        
        # Save detailed sync report
        with open('/home/renier/ProjectQuantum-Full/branch_sync_report.json', 'w') as f:
            json.dump({
                'sync_results': self.sync_results,
                'overall_assessment': assessment,
                'recommendations': recommendations
            }, f, indent=2, default=str)
        
        print(f"\n📄 Detailed sync report saved: branch_sync_report.json")

def main():
    """Check branch synchronization"""
    print("🚀 Starting Branch Synchronization Check...")
    
    checker = BranchSyncChecker()
    
    try:
        results = checker.check_branch_synchronization()
        print("\n✅ Branch synchronization check completed!")
        return True
        
    except Exception as e:
        print(f"❌ Synchronization check failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)