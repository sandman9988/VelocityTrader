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

        try:
            if not path.exists():
                print(f"   ❌ Directory not found")
                self.issues.append(f"{name}: Directory not found")
                return {"exists": False}
        except (OSError, PermissionError) as e:
            print(f"   ❌ Cannot access directory: {e}")
            self.issues.append(f"{name}: Cannot access directory - {e}")
            return {"exists": False, "error": str(e)}

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
            try:
                if folder_path.exists():
                    try:
                        file_count = len(list(folder_path.rglob("*.*")))
                    except (OSError, PermissionError) as e:
                        file_count = -1
                        print(f"   ⚠️  {folder}/ (error counting files: {e})")
                        continue
                    audit_result["standard_folders"][folder] = {
                        "exists": True,
                        "file_count": file_count,
                        "description": description
                    }
                    print(f"   ✅ {folder}/ ({file_count} files) - {description}")
                else:
                    audit_result["standard_folders"][folder] = {"exists": False}
                    print(f"   ⚪ {folder}/ - Missing")
            except (OSError, PermissionError) as e:
                audit_result["standard_folders"][folder] = {"exists": False, "error": str(e)}
                print(f"   ⚠️  {folder}/ - Cannot check: {e}")

        # Check for unexpected items
        try:
            items = list(path.iterdir())
        except (OSError, PermissionError) as e:
            print(f"   ⚠️  Cannot list directory contents: {e}")
            self.issues.append(f"{name}: Cannot list directory - {e}")
            return audit_result

        for item in items:
            try:
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
            except (OSError, PermissionError) as e:
                print(f"   ⚠️  Cannot access item: {e}")

        return audit_result
    
    def check_duplicates_across_terminals(self):
        """Check for duplicate structures across different terminals"""
        print(f"\n🔍 Checking for duplicate structures across terminals...")

        terminal_structures = {}
        for terminal_path in self.terminal_paths:
            try:
                if terminal_path.exists():
                    experts_path = terminal_path / "Experts"
                    try:
                        if experts_path.exists():
                            try:
                                experts = [f.name for f in experts_path.rglob("*.mq5")]
                                terminal_structures[terminal_path.name] = experts
                            except (OSError, PermissionError) as e:
                                print(f"   ⚠️  Cannot scan {terminal_path.name}/Experts: {e}")
                    except (OSError, PermissionError) as e:
                        print(f"   ⚠️  Cannot access Experts in {terminal_path.name}: {e}")
            except (OSError, PermissionError) as e:
                print(f"   ⚠️  Cannot check terminal {terminal_path}: {e}")

        if not terminal_structures:
            print("   ℹ️  No terminal structures found to compare")
            return

        # Compare structures
        all_terminals = list(terminal_structures.keys())
        for i, terminal1 in enumerate(all_terminals):
            for terminal2 in all_terminals[i+1:]:
                try:
                    common_files = set(terminal_structures[terminal1]) & set(terminal_structures[terminal2])
                    if common_files:
                        print(f"   ⚠️  Duplicates between {terminal1} and {terminal2}: {len(common_files)} files")
                        self.issues.append(f"Duplicate files between terminals {terminal1} and {terminal2}")
                except (KeyError, TypeError) as e:
                    print(f"   ⚠️  Error comparing terminals: {e}")
    
    def analyze_project_specific_structure(self):
        """Analyze ProjectQuantum specific folder organization"""
        print(f"\n🎯 Analyzing ProjectQuantum Structure...")

        # Check development structure
        dev_experts = self.mt5_dev / "Experts" / "ProjectQuantum"
        dev_includes = self.mt5_dev / "Include" / "ProjectQuantum"
        dev_master_include = self.mt5_dev / "Include" / "ProjectQuantum.mqh"

        try:
            if dev_experts.exists():
                try:
                    ea_count = len(list(dev_experts.glob("*.mq5")))
                    print(f"   ✅ Dev Experts/ProjectQuantum/ ({ea_count} EAs)")
                except (OSError, PermissionError) as e:
                    print(f"   ⚠️  Dev Experts/ProjectQuantum/ exists but cannot count files: {e}")
            else:
                print(f"   ❌ Dev Experts/ProjectQuantum/ missing")
                self.issues.append("ProjectQuantum: Missing Experts folder in development")
        except (OSError, PermissionError) as e:
            print(f"   ⚠️  Cannot check Experts/ProjectQuantum: {e}")

        try:
            if dev_includes.exists():
                try:
                    include_count = len(list(dev_includes.rglob("*.mqh")))
                    subdirs = [d.name for d in dev_includes.iterdir() if d.is_dir()]
                    print(f"   ✅ Dev Include/ProjectQuantum/ ({include_count} files in {len(subdirs)} subdirs)")
                    if subdirs:
                        print(f"      Subdirs: {', '.join(subdirs)}")
                except (OSError, PermissionError) as e:
                    print(f"   ⚠️  Dev Include/ProjectQuantum/ exists but cannot enumerate: {e}")
            else:
                print(f"   ❌ Dev Include/ProjectQuantum/ missing")
                self.issues.append("ProjectQuantum: Missing Include folder in development")
        except (OSError, PermissionError) as e:
            print(f"   ⚠️  Cannot check Include/ProjectQuantum: {e}")

        try:
            if dev_master_include.exists():
                print(f"   ✅ Dev Include/ProjectQuantum.mqh (master include)")
            else:
                print(f"   ❌ Dev Include/ProjectQuantum.mqh missing")
                self.issues.append("ProjectQuantum: Missing master include file")
        except (OSError, PermissionError) as e:
            print(f"   ⚠️  Cannot check ProjectQuantum.mqh: {e}")
    
    def generate_cleanup_recommendations(self):
        """Generate specific cleanup recommendations"""
        print(f"\n💡 CLEANUP RECOMMENDATIONS")
        print("=" * 50)

        recommendations = []

        # Build list of existing paths to check
        paths_to_check = [self.mt5_dev]
        for p in self.terminal_paths:
            try:
                if p.exists():
                    paths_to_check.append(p)
            except (OSError, PermissionError):
                continue

        # Check for wrong-level folders
        wrong_level_folders = []
        for path in paths_to_check:
            try:
                for item in path.iterdir():
                    try:
                        if item.is_dir() and item.name in ["Main", "Tests", "Documentation", "Scripts"]:
                            if item.name not in ["Scripts", "Libraries", "Files"]:  # Scripts is valid at root
                                wrong_level_folders.append((path, item.name))
                    except (OSError, PermissionError):
                        continue
            except (OSError, PermissionError) as e:
                print(f"   ⚠️  Cannot check {path}: {e}")

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
        for path in paths_to_check:
            try:
                for item in path.rglob("*"):
                    try:
                        if item.is_dir() and "ProjectQuantum" in item.name and item.name != "ProjectQuantum":
                            duplicate_project_folders.append(item)
                    except (OSError, PermissionError):
                        continue
            except (OSError, PermissionError) as e:
                print(f"   ⚠️  Cannot scan {path} for duplicates: {e}")

        if duplicate_project_folders:
            recommendations.append("\nREMOVE DUPLICATE PROJECT FOLDERS:")
            for folder in duplicate_project_folders:
                recommendations.append(f"   Remove: {folder}")

        # Check for orphaned files
        orphaned_files = []
        for path in paths_to_check:
            try:
                for item in path.glob("*"):
                    try:
                        if item.is_file() and item.suffix in [".mq5", ".mqh"]:
                            orphaned_files.append(item)
                    except (OSError, PermissionError):
                        continue
            except (OSError, PermissionError) as e:
                print(f"   ⚠️  Cannot scan {path} for orphaned files: {e}")

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

        try:
            # Audit development directory
            self.report["development"] = self.audit_directory(self.mt5_dev, "Development")
        except Exception as e:
            print(f"   ⚠️  Error auditing development directory: {e}")
            self.report["development"] = {"error": str(e)}

        # Audit terminal directories
        self.report["terminals"] = {}
        for terminal_path in self.terminal_paths:
            try:
                terminal_id = terminal_path.parent.name
                self.report["terminals"][terminal_id] = self.audit_directory(terminal_path, f"Terminal-{terminal_id}")
            except Exception as e:
                print(f"   ⚠️  Error auditing terminal {terminal_path}: {e}")

        # Check for cross-terminal duplicates
        try:
            self.check_duplicates_across_terminals()
        except Exception as e:
            print(f"   ⚠️  Error checking duplicates: {e}")

        # Analyze project structure
        try:
            self.analyze_project_specific_structure()
        except Exception as e:
            print(f"   ⚠️  Error analyzing project structure: {e}")

        # Generate recommendations
        try:
            recommendations = self.generate_cleanup_recommendations()
        except Exception as e:
            print(f"   ⚠️  Error generating recommendations: {e}")
            recommendations = []

        # Summary
        print(f"\n📊 AUDIT SUMMARY")
        print("=" * 30)
        print(f"Issues found: {len(self.issues)}")
        print(f"Recommendations: {len(recommendations)}")

        if self.issues:
            print(f"\n❌ ISSUES FOUND:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")

        # Save report - try multiple locations
        report_data = {
            "audit_results": self.report,
            "issues": self.issues,
            "recommendations": recommendations
        }

        # Try to find a writable location for the report
        report_locations = [
            Path("/home/renier/ProjectQuantum-Full/mt5_structure_audit_report.json"),
            Path.cwd() / "mt5_structure_audit_report.json",
            Path.home() / "mt5_structure_audit_report.json",
        ]

        report_saved = False
        for report_file in report_locations:
            try:
                report_file.parent.mkdir(parents=True, exist_ok=True)
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, default=str)
                print(f"\n📄 Full report saved: {report_file}")
                report_saved = True
                break
            except PermissionError:
                continue
            except (IOError, OSError) as e:
                continue
            except (TypeError, ValueError) as e:
                print(f"   ⚠️  Error serializing report: {e}")
                break

        if not report_saved:
            print(f"\n⚠️  Could not save report to any location")

        return len(self.issues) == 0

if __name__ == "__main__":
    import sys

    try:
        auditor = MT5StructureAuditor()
        success = auditor.run_full_audit()

        if success:
            print("\n🎉 MT5 structure audit PASSED - No issues found!")
            sys.exit(0)
        else:
            print(f"\n⚠️  MT5 structure audit found {len(auditor.issues)} issues")
            print("Review recommendations above for cleanup steps")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nAudit interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Audit failed with error: {e}")
        sys.exit(2)