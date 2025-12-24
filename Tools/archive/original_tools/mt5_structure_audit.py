#!/usr/bin/env python3
"""
Complete MT5 Structure Audit
Reviews all MT5 directories for correct layout and identifies issues
"""

import os
from pathlib import Path
import json

class MT5StructureAuditor:
    def __init__(self):
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.terminal_paths = [
            Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/8A503E260F28D3DD9CC9A37AA3CE29BC/MQL5"),
            Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/29BC03B6BB995A90C75D3603F5C8A659/MQL5"),
            Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/95E092767220F643BF1B1CCEEF7AD317/MQL5"),
            Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5")
        ]
        
        self.standard_folders = {
            "Experts": "Expert Advisors (.mq5)",
            "Include": "Header files (.mqh)",
            "Indicators": "Custom indicators (.mq5)",  
            "Scripts": "Scripts (.mq5)",
            "Libraries": "Libraries (.mq5/.ex5)",
            "Files": "Data files",
            "Images": "Image resources"
        }
        
        self.issues = []
        self.report = {}
    
    def audit_directory(self, path, name):
        """Audit a single MT5 directory"""
        print(f"\n🔍 Auditing: {name}")
        print(f"   Path: {path}")
        
        if not path.exists():
            print(f"   ❌ Directory not found")
            self.issues.append(f"{name}: Directory not found")
            return {"exists": False}
        
        audit_result = {
            "exists": True,
            "standard_folders": {},
            "unexpected_folders": [],
            "file_counts": {},
            "duplicates": [],
            "wrong_level_items": []
        }
        
        # Check for standard folders
        for folder, description in self.standard_folders.items():
            folder_path = path / folder
            if folder_path.exists():
                file_count = len(list(folder_path.rglob("*.*")))
                audit_result["standard_folders"][folder] = {
                    "exists": True,
                    "file_count": file_count,
                    "description": description
                }
                print(f"   ✅ {folder}/ ({file_count} files) - {description}")
            else:
                audit_result["standard_folders"][folder] = {"exists": False}
                print(f"   ⚪ {folder}/ - Missing")
        
        # Check for unexpected items
        for item in path.iterdir():
            if item.is_dir():
                folder_name = item.name
                if folder_name not in self.standard_folders:
                    audit_result["unexpected_folders"].append(folder_name)
                    
                    # Check for common issues
                    if "ProjectQuantum" in folder_name and folder_name != "ProjectQuantum":
                        print(f"   ⚠️  Unexpected: {folder_name}/ (potential duplicate)")
                        self.issues.append(f"{name}: Duplicate ProjectQuantum folder - {folder_name}")
                    elif folder_name in ["Main", "Tests", "Documentation"]:
                        print(f"   ❌ Wrong level: {folder_name}/ (should be inside Experts or Scripts)")
                        self.issues.append(f"{name}: Wrong level folder - {folder_name}")
                        audit_result["wrong_level_items"].append(folder_name)
                    elif folder_name.startswith("."):
                        print(f"   ⚪ Hidden: {folder_name}/")
                    else:
                        print(f"   ❓ Unexpected: {folder_name}/")
            elif item.is_file():
                # Files directly in MQL5 root
                if item.suffix in [".mq5", ".mqh"]:
                    print(f"   ❌ Wrong level: {item.name} (should be in appropriate subfolder)")
                    audit_result["wrong_level_items"].append(item.name)
                    self.issues.append(f"{name}: File in wrong location - {item.name}")
                else:
                    print(f"   ℹ️  Root file: {item.name}")
        
        return audit_result
    
    def check_duplicates_across_terminals(self):
        """Check for duplicate structures across different terminals"""
        print(f"\n🔍 Checking for duplicate structures across terminals...")
        
        terminal_structures = {}
        for terminal_path in self.terminal_paths:
            if terminal_path.exists():
                experts_path = terminal_path / "Experts"
                if experts_path.exists():
                    experts = [f.name for f in experts_path.rglob("*.mq5")]
                    terminal_structures[terminal_path.name] = experts
        
        # Compare structures
        all_terminals = list(terminal_structures.keys())
        for i, terminal1 in enumerate(all_terminals):
            for terminal2 in all_terminals[i+1:]:
                common_files = set(terminal_structures[terminal1]) & set(terminal_structures[terminal2])
                if common_files:
                    print(f"   ⚠️  Duplicates between {terminal1} and {terminal2}: {len(common_files)} files")
                    self.issues.append(f"Duplicate files between terminals {terminal1} and {terminal2}")
    
    def analyze_project_specific_structure(self):
        """Analyze ProjectQuantum specific folder organization"""
        print(f"\n🎯 Analyzing ProjectQuantum Structure...")
        
        # Check development structure
        dev_experts = self.mt5_dev / "Experts" / "ProjectQuantum"
        dev_includes = self.mt5_dev / "Include" / "ProjectQuantum"
        dev_master_include = self.mt5_dev / "Include" / "ProjectQuantum.mqh"
        
        if dev_experts.exists():
            ea_count = len(list(dev_experts.glob("*.mq5")))
            print(f"   ✅ Dev Experts/ProjectQuantum/ ({ea_count} EAs)")
        else:
            print(f"   ❌ Dev Experts/ProjectQuantum/ missing")
            self.issues.append("ProjectQuantum: Missing Experts folder in development")
        
        if dev_includes.exists():
            include_count = len(list(dev_includes.rglob("*.mqh")))
            subdirs = [d.name for d in dev_includes.iterdir() if d.is_dir()]
            print(f"   ✅ Dev Include/ProjectQuantum/ ({include_count} files in {len(subdirs)} subdirs)")
            print(f"      Subdirs: {', '.join(subdirs)}")
        else:
            print(f"   ❌ Dev Include/ProjectQuantum/ missing")
            self.issues.append("ProjectQuantum: Missing Include folder in development")
        
        if dev_master_include.exists():
            print(f"   ✅ Dev Include/ProjectQuantum.mqh (master include)")
        else:
            print(f"   ❌ Dev Include/ProjectQuantum.mqh missing")
            self.issues.append("ProjectQuantum: Missing master include file")
    
    def generate_cleanup_recommendations(self):
        """Generate specific cleanup recommendations"""
        print(f"\n💡 CLEANUP RECOMMENDATIONS")
        print("=" * 50)
        
        recommendations = []
        
        # Check for wrong-level folders
        wrong_level_folders = []
        for path in [self.mt5_dev] + [p for p in self.terminal_paths if p.exists()]:
            for item in path.iterdir():
                if item.is_dir() and item.name in ["Main", "Tests", "Documentation", "Scripts"]:
                    if item.name not in ["Scripts", "Libraries", "Files"]:  # Scripts is valid at root
                        wrong_level_folders.append((path, item.name))
        
        if wrong_level_folders:
            recommendations.append("MOVE WRONG-LEVEL FOLDERS:")
            for path, folder in wrong_level_folders:
                if folder == "Main":
                    recommendations.append(f"   Move {path}/{folder}/*.mq5 → {path}/Experts/ProjectQuantum/")
                elif folder == "Tests":
                    recommendations.append(f"   Move {path}/{folder}/*.mq5 → {path}/Scripts/ProjectQuantum/")
                elif folder == "Documentation":
                    recommendations.append(f"   Move {path}/{folder} → {path}/Files/Documentation/")
        
        # Check for duplicate project folders
        duplicate_project_folders = []
        for path in [self.mt5_dev] + [p for p in self.terminal_paths if p.exists()]:
            for item in path.rglob("*"):
                if item.is_dir() and "ProjectQuantum" in item.name and item.name != "ProjectQuantum":
                    duplicate_project_folders.append(item)
        
        if duplicate_project_folders:
            recommendations.append("\nREMOVE DUPLICATE PROJECT FOLDERS:")
            for folder in duplicate_project_folders:
                recommendations.append(f"   Remove: {folder}")
        
        # Check for orphaned files
        orphaned_files = []
        for path in [self.mt5_dev] + [p for p in self.terminal_paths if p.exists()]:
            for item in path.glob("*"):
                if item.is_file() and item.suffix in [".mq5", ".mqh"]:
                    orphaned_files.append(item)
        
        if orphaned_files:
            recommendations.append("\nMOVE ORPHANED FILES:")
            for file in orphaned_files:
                if file.suffix == ".mq5":
                    recommendations.append(f"   Move {file.name} → Experts/ or Scripts/")
                elif file.suffix == ".mqh":
                    recommendations.append(f"   Move {file.name} → Include/")
        
        for rec in recommendations:
            print(rec)
        
        return recommendations
    
    def run_full_audit(self):
        """Run complete MT5 structure audit"""
        print("🔍 Complete MT5 Structure Audit")
        print("=" * 50)
        
        # Audit development directory
        self.report["development"] = self.audit_directory(self.mt5_dev, "Development")
        
        # Audit terminal directories
        self.report["terminals"] = {}
        for terminal_path in self.terminal_paths:
            terminal_id = terminal_path.parent.name
            self.report["terminals"][terminal_id] = self.audit_directory(terminal_path, f"Terminal-{terminal_id}")
        
        # Check for cross-terminal duplicates
        self.check_duplicates_across_terminals()
        
        # Analyze project structure
        self.analyze_project_specific_structure()
        
        # Generate recommendations
        recommendations = self.generate_cleanup_recommendations()
        
        # Summary
        print(f"\n📊 AUDIT SUMMARY")
        print("=" * 30)
        print(f"Issues found: {len(self.issues)}")
        print(f"Recommendations: {len(recommendations)}")
        
        if self.issues:
            print(f"\n❌ ISSUES FOUND:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        # Save report
        report_file = "/home/renier/ProjectQuantum-Full/mt5_structure_audit_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                "audit_results": self.report,
                "issues": self.issues,
                "recommendations": recommendations
            }, f, indent=2, default=str)
        
        print(f"\n📄 Full report saved: {report_file}")
        
        return len(self.issues) == 0

if __name__ == "__main__":
    auditor = MT5StructureAuditor()
    success = auditor.run_full_audit()
    
    if success:
        print("\n🎉 MT5 structure audit PASSED - No issues found!")
    else:
        print(f"\n⚠️  MT5 structure audit found {len(auditor.issues)} issues")
        print("Review recommendations above for cleanup steps")