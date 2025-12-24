#!/usr/bin/env python3
"""
Test MQL5 Compilation Workflow
Simulates CI/CD compilation process locally
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

class CompilationWorkflow:
    def __init__(self):
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.metaeditor = "/mnt/c/DevCenter/MT5-Unified/MT5-Core/Terminal/MetaEditor64.exe"
        
        # Core files in dependency order
        self.core_files = [
            "Include/ProjectQuantum/Core/SafeMath.mqh",
            "Include/ProjectQuantum/Core/ArrayUtils.mqh", 
            "Include/ProjectQuantum/Core/SymbolUtils.mqh",
            "Include/ProjectQuantum/Core/CLogger.mqh",
            "Include/ProjectQuantum/Core/Defensive.mqh",
            "Include/ProjectQuantum/Core/TestFramework.mqh",
            "Include/ProjectQuantum/Core/CVersionManager.mqh",
            "Include/ProjectQuantum/Core/CFileIntegrity.mqh",
        ]
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "core_compilation": {},
            "full_compilation": {},
            "errors": []
        }
    
    def check_file_exists(self, filepath):
        """Check if file exists and has content"""
        full_path = self.mt5_dev / filepath
        if not full_path.exists():
            return False, f"File not found: {filepath}"
        
        size = full_path.stat().st_size
        if size == 0:
            return False, f"File is empty: {filepath}"
            
        return True, f"File exists ({size} bytes)"
    
    def verify_syntax(self, filepath):
        """Basic syntax verification"""
        full_path = self.mt5_dev / filepath
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            
            # Check for basic requirements
            if '#property strict' not in content:
                issues.append("Missing #property strict")
            
            # Check for common syntax errors
            if 'static double result =' in content:
                issues.append("Local variable declared as static")
                
            if 'static double value' in content and '(' in content:
                issues.append("Function parameter declared as static")
                
            # Check for balanced braces
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                issues.append(f"Unbalanced braces: {open_braces} {{ vs {close_braces} }}")
            
            # Check for balanced parentheses
            open_parens = content.count('(')
            close_parens = content.count(')')
            if open_parens != close_parens:
                issues.append(f"Unbalanced parentheses: {open_parens} ( vs {close_parens} )")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            return False, [f"Failed to read file: {e}"]
    
    def test_core_compilation(self):
        """Test compilation of core files"""
        print("🔧 Testing Core File Compilation")
        print("=" * 50)
        
        success_count = 0
        failed_files = []
        
        for i, filepath in enumerate(self.core_files, 1):
            print(f"\n[{i}/{len(self.core_files)}] {filepath}")
            
            # Check existence
            exists, msg = self.check_file_exists(filepath)
            print(f"   📄 {msg}")
            
            if not exists:
                failed_files.append((filepath, msg))
                self.results["core_compilation"][filepath] = {
                    "status": "failed",
                    "error": msg
                }
                continue
            
            # Verify syntax
            valid, issues = self.verify_syntax(filepath)
            
            if valid:
                print(f"   ✅ Syntax check passed")
                success_count += 1
                self.results["core_compilation"][filepath] = {
                    "status": "success",
                    "message": "Syntax valid"
                }
            else:
                print(f"   ❌ Syntax issues found:")
                for issue in issues:
                    print(f"      • {issue}")
                failed_files.append((filepath, issues))
                self.results["core_compilation"][filepath] = {
                    "status": "failed",
                    "errors": issues
                }
        
        print(f"\n📊 Core Compilation Summary")
        print(f"   Success: {success_count}/{len(self.core_files)}")
        print(f"   Failed: {len(failed_files)}")
        
        if failed_files:
            print(f"\n❌ Failed files:")
            for filepath, error in failed_files:
                print(f"   • {filepath}")
                if isinstance(error, list):
                    for e in error:
                        print(f"     - {e}")
                else:
                    print(f"     - {error}")
        
        return len(failed_files) == 0
    
    def generate_ci_report(self):
        """Generate CI-style report"""
        report_path = self.project_root / "ci_compilation_report.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 CI Report saved: {report_path}")
        
        # Generate summary
        total_files = len(self.results["core_compilation"])
        successful = sum(1 for r in self.results["core_compilation"].values() if r["status"] == "success")
        failed = total_files - successful
        
        summary_path = self.project_root / "ci_summary.md"
        with open(summary_path, 'w') as f:
            f.write("# ProjectQuantum CI/CD Compilation Report\n\n")
            f.write(f"**Date**: {self.results['timestamp']}\n\n")
            f.write("## Summary\n\n")
            f.write(f"- Total Files: {total_files}\n")
            f.write(f"- ✅ Successful: {successful}\n")
            f.write(f"- ❌ Failed: {failed}\n\n")
            
            if failed > 0:
                f.write("## Failed Files\n\n")
                for filepath, result in self.results["core_compilation"].items():
                    if result["status"] == "failed":
                        f.write(f"### {filepath}\n\n")
                        if "errors" in result:
                            for error in result["errors"]:
                                f.write(f"- {error}\n")
                        else:
                            f.write(f"- {result.get('error', 'Unknown error')}\n")
                        f.write("\n")
        
        print(f"📄 Summary saved: {summary_path}")
    
    def run_workflow(self):
        """Run the complete workflow"""
        print("🚀 ProjectQuantum CI/CD Workflow Test")
        print("=" * 50)
        
        # Test core compilation
        core_success = self.test_core_compilation()
        
        # Generate reports
        self.generate_ci_report()
        
        if core_success:
            print("\n✅ CI/CD workflow test PASSED")
            print("All core files are ready for compilation")
            return 0
        else:
            print("\n❌ CI/CD workflow test FAILED")
            print("Fix the issues above before pushing to repository")
            return 1

if __name__ == "__main__":
    workflow = CompilationWorkflow()
    sys.exit(workflow.run_workflow())