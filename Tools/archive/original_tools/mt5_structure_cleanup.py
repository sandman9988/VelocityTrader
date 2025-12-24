#!/usr/bin/env python3
"""
MT5 Structure Cleanup Script
Removes duplicates and organizes MT5 folders correctly
"""

import os
import shutil
import subprocess
from pathlib import Path

class MT5StructureCleanup:
    def __init__(self):
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.backup_dir = Path("/home/renier/ProjectQuantum-Full/mt5_cleanup_backup")
        self.issues_fixed = []
        
    def create_backup(self, path):
        """Create backup before making changes"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
            
        backup_name = f"backup_{path.name}_{Path.cwd().name}"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copytree(str(path), str(backup_path))
            print(f"   📋 Backup created: {backup_path}")
            return True
        except Exception as e:
            print(f"   ❌ Backup failed: {e}")
            return False
    
    def remove_duplicate_mql5_folder(self):
        """Remove the duplicate MQL5 folder inside MQL5-Development"""
        duplicate_path = self.mt5_dev / "MQL5"
        
        print(f"🗑️  Removing duplicate MQL5/ folder...")
        print(f"   Path: {duplicate_path}")
        
        if not duplicate_path.exists():
            print(f"   ✅ No duplicate MQL5 folder found")
            return True
            
        # Check if it contains important data
        experts_count = len(list((duplicate_path / "Experts").rglob("*.mq5"))) if (duplicate_path / "Experts").exists() else 0
        includes_count = len(list((duplicate_path / "Include").rglob("*.mqh"))) if (duplicate_path / "Include").exists() else 0
        
        print(f"   📊 Contains: {experts_count} EAs, {includes_count} includes")
        
        if experts_count > 0 or includes_count > 0:
            print(f"   📋 Creating backup first...")
            if not self.create_backup(duplicate_path):
                print(f"   ❌ Skipping removal - backup failed")
                return False
        
        try:
            subprocess.run(['rm', '-rf', str(duplicate_path)], check=True)
            print(f"   ✅ Duplicate MQL5 folder removed")
            self.issues_fixed.append("Removed duplicate MQL5 folder")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to remove: {e}")
            return False
    
    def cleanup_projects_folder(self):
        """Clean up the Projects folder structure"""
        projects_path = self.mt5_dev / "Projects"
        
        print(f"\n🗂️  Cleaning up Projects folder...")
        print(f"   Path: {projects_path}")
        
        if not projects_path.exists():
            print(f"   ✅ No Projects folder found")
            return True
        
        # Check what's inside
        subdirs = [d.name for d in projects_path.iterdir() if d.is_dir()]
        print(f"   📁 Contains subdirectories: {subdirs}")
        
        # These folders seem to be organizational - check if they contain actual code
        has_code = False
        for subdir in projects_path.rglob("*"):
            if subdir.suffix in [".mq5", ".mqh", ".ex5"]:
                has_code = True
                break
                
        if not has_code:
            print(f"   🗑️  Projects folder contains no code files")
            try:
                subprocess.run(['rm', '-rf', str(projects_path)], check=True)
                print(f"   ✅ Empty Projects folder removed")
                self.issues_fixed.append("Removed empty Projects folder")
                return True
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to remove: {e}")
                return False
        else:
            print(f"   ⚠️  Projects folder contains code - keeping it")
            return True
    
    def cleanup_shared_includes(self):
        """Clean up SharedIncludes folder"""
        shared_path = self.mt5_dev / "SharedIncludes"
        
        print(f"\n📚 Checking SharedIncludes folder...")
        print(f"   Path: {shared_path}")
        
        if not shared_path.exists():
            print(f"   ✅ No SharedIncludes folder found")
            return True
        
        # Check if it contains files that should be in Include/
        mqh_files = list(shared_path.rglob("*.mqh"))
        print(f"   📄 Contains {len(mqh_files)} .mqh files")
        
        if mqh_files:
            print(f"   🔄 Moving .mqh files to Include/")
            include_dir = self.mt5_dev / "Include"
            
            for mqh_file in mqh_files:
                rel_path = mqh_file.relative_to(shared_path)
                target_path = include_dir / rel_path
                
                # Create target directory if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.move(str(mqh_file), str(target_path))
                    print(f"      📦 Moved: {rel_path}")
                except Exception as e:
                    print(f"      ❌ Failed to move {rel_path}: {e}")
        
        # Remove SharedIncludes if now empty
        try:
            remaining_files = list(shared_path.rglob("*"))
            if len(remaining_files) <= 1:  # Only the folder itself
                subprocess.run(['rm', '-rf', str(shared_path)], check=True)
                print(f"   ✅ Empty SharedIncludes folder removed")
                self.issues_fixed.append("Moved SharedIncludes to Include/")
        except Exception as e:
            print(f"   ❌ Failed to remove SharedIncludes: {e}")
            
        return True
    
    def cleanup_templates_folder(self):
        """Clean up Templates folder"""
        templates_path = self.mt5_dev / "Templates"
        
        print(f"\n📄 Checking Templates folder...")
        print(f"   Path: {templates_path}")
        
        if not templates_path.exists():
            print(f"   ✅ No Templates folder found")
            return True
        
        # Templates might be useful, but check if they're standard MT5 templates
        template_files = list(templates_path.rglob("*.*"))
        print(f"   📄 Contains {len(template_files)} files")
        
        # If it contains only a few files and they're not critical, we can move them
        if len(template_files) < 5:
            try:
                # Move to Files/Templates instead
                files_templates = self.mt5_dev / "Files" / "Templates"
                files_templates.mkdir(parents=True, exist_ok=True)
                
                for template_file in template_files:
                    if template_file.is_file():
                        rel_path = template_file.relative_to(templates_path)
                        target_path = files_templates / rel_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(template_file), str(target_path))
                        print(f"      📦 Moved: {rel_path}")
                
                # Remove empty Templates folder
                subprocess.run(['rm', '-rf', str(templates_path)], check=True)
                print(f"   ✅ Templates moved to Files/Templates/")
                self.issues_fixed.append("Moved Templates to Files/Templates/")
                
            except Exception as e:
                print(f"   ❌ Failed to move templates: {e}")
        else:
            print(f"   ⚠️  Templates folder has many files - keeping it")
            
        return True
    
    def cleanup_log_files(self):
        """Clean up compilation log files in wrong location"""
        print(f"\n📝 Cleaning up log files...")
        
        log_files = list(self.mt5_dev.glob("*.log"))
        if log_files:
            logs_dir = self.mt5_dev / "Files" / "Logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            for log_file in log_files:
                target_path = logs_dir / log_file.name
                try:
                    shutil.move(str(log_file), str(target_path))
                    print(f"   📦 Moved: {log_file.name} → Files/Logs/")
                except Exception as e:
                    print(f"   ❌ Failed to move {log_file.name}: {e}")
                    
            self.issues_fixed.append(f"Moved {len(log_files)} log files to Files/Logs/")
        else:
            print(f"   ✅ No log files in wrong location")
            
        return True
    
    def verify_proper_structure(self):
        """Verify the MT5 structure is now correct"""
        print(f"\n✅ Verifying final structure...")
        
        required_folders = ["Experts", "Include", "Indicators", "Scripts", "Libraries"]
        all_good = True
        
        for folder in required_folders:
            path = self.mt5_dev / folder
            if path.exists():
                file_count = len(list(path.rglob("*.*")))
                print(f"   ✅ {folder}/ ({file_count} files)")
            else:
                print(f"   ❌ {folder}/ missing")
                all_good = False
        
        # Check ProjectQuantum organization
        pq_experts = self.mt5_dev / "Experts" / "ProjectQuantum"
        pq_includes = self.mt5_dev / "Include" / "ProjectQuantum"
        pq_master = self.mt5_dev / "Include" / "ProjectQuantum.mqh"
        
        if pq_experts.exists():
            ea_count = len(list(pq_experts.glob("*.mq5")))
            print(f"   ✅ ProjectQuantum Experts ({ea_count} EAs)")
        else:
            print(f"   ❌ ProjectQuantum Experts missing")
            all_good = False
            
        if pq_includes.exists():
            inc_count = len(list(pq_includes.rglob("*.mqh")))
            print(f"   ✅ ProjectQuantum Includes ({inc_count} files)")
        else:
            print(f"   ❌ ProjectQuantum Includes missing")
            all_good = False
            
        if pq_master.exists():
            print(f"   ✅ ProjectQuantum master include")
        else:
            print(f"   ❌ ProjectQuantum master include missing")
            all_good = False
            
        return all_good
    
    def run_cleanup(self):
        """Run the complete MT5 structure cleanup"""
        print("🧹 MT5 Structure Cleanup")
        print("=" * 50)
        
        cleanup_steps = [
            ("Remove duplicate MQL5 folder", self.remove_duplicate_mql5_folder),
            ("Clean up Projects folder", self.cleanup_projects_folder),
            ("Clean up SharedIncludes", self.cleanup_shared_includes),
            ("Clean up Templates", self.cleanup_templates_folder),
            ("Clean up log files", self.cleanup_log_files),
        ]
        
        success_count = 0
        for desc, func in cleanup_steps:
            print(f"\n🔧 {desc}...")
            try:
                if func():
                    success_count += 1
                    print(f"   ✅ Success")
                else:
                    print(f"   ❌ Failed")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n📊 Cleanup completed: {success_count}/{len(cleanup_steps)} steps successful")
        
        if self.issues_fixed:
            print(f"\n🎯 Issues Fixed:")
            for i, issue in enumerate(self.issues_fixed, 1):
                print(f"   {i}. {issue}")
        
        # Verify final structure
        structure_ok = self.verify_proper_structure()
        
        if structure_ok and success_count == len(cleanup_steps):
            print(f"\n🎉 MT5 structure cleanup COMPLETE!")
            print(f"✅ All duplicates removed")
            print(f"✅ Files properly organized")
            print(f"✅ ProjectQuantum structure intact")
        else:
            print(f"\n⚠️  Cleanup partially completed")
            print(f"Some manual intervention may be needed")
        
        return structure_ok and success_count == len(cleanup_steps)

if __name__ == "__main__":
    cleaner = MT5StructureCleanup()
    cleaner.run_cleanup()