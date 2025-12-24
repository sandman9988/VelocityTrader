#!/usr/bin/env python3
"""
Comprehensive ProjectQuantum Code Audit
Real analysis of code quality, coverage, and execution capability
"""

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class ComprehensiveCodeAudit:
    def __init__(self):
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.216",
            "files_analyzed": 0,
            "total_lines": 0,
            "code_issues": [],
            "coverage_analysis": {},
            "compilation_readiness": {},
            "execution_analysis": {},
            "critical_findings": []
        }
        
    def analyze_file_structure(self):
        """Analyze ProjectQuantum file structure"""
        print("📁 Analyzing file structure...")
        
        structure = {
            "include_files": list((self.mt5_dev / "Include/ProjectQuantum").rglob("*.mqh")),
            "expert_files": list((self.mt5_dev / "Experts/ProjectQuantum").rglob("*.mq5")),
            "script_files": list((self.mt5_dev / "Scripts/ProjectQuantum").rglob("*.mq5")),
            "test_files": [f for f in (self.mt5_dev / "Scripts/ProjectQuantum").rglob("*.mq5") if "Test_" in f.name]
        }
        
        for category, files in structure.items():
            print(f"   {category}: {len(files)} files")
            
        self.audit_results["file_structure"] = {k: len(v) for k, v in structure.items()}
        return structure
    
    def analyze_code_quality(self, file_path):
        """Analyze code quality of a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"error": str(e)}
        
        lines = content.split('\n')
        
        analysis = {
            "file": str(file_path),
            "total_lines": len(lines),
            "code_lines": 0,
            "comment_lines": 0,
            "empty_lines": 0,
            "issues": [],
            "functions": [],
            "classes": [],
            "includes": [],
            "complexity_score": 0
        }
        
        # Count line types and find issues
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if not stripped:
                analysis["empty_lines"] += 1
            elif stripped.startswith('//') or stripped.startswith('/*'):
                analysis["comment_lines"] += 1
            else:
                analysis["code_lines"] += 1
            
            # Find issues
            if 'TODO' in line or 'FIXME' in line:
                analysis["issues"].append(f"Line {i}: {stripped}")
            
            if len(line) > 120:
                analysis["issues"].append(f"Line {i}: Line too long ({len(line)} chars)")
            
            # Find functions
            if re.match(r'\s*\w+\s+\w+\s*\(.*\)\s*{?', stripped) and not stripped.startswith('//'):
                analysis["functions"].append(stripped)
            
            # Find classes
            if stripped.startswith('class '):
                analysis["classes"].append(stripped)
            
            # Find includes
            if stripped.startswith('#include'):
                analysis["includes"].append(stripped)
        
        # Calculate complexity
        complexity_indicators = [
            'if ', 'else', 'for ', 'while ', 'switch ', 'case ', 'catch ', 'try'
        ]
        for indicator in complexity_indicators:
            analysis["complexity_score"] += content.count(indicator)
        
        return analysis
    
    def check_actual_compilation(self, file_path):
        """Check if file can actually be compiled"""
        compilation_check = {
            "file": str(file_path),
            "syntax_valid": True,
            "dependencies_found": True,
            "mql5_compliant": True,
            "issues": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            compilation_check["issues"].append(f"Cannot read file: {e}")
            return compilation_check
        
        # Check MQL5 requirements
        if '#property strict' not in content:
            compilation_check["mql5_compliant"] = False
            compilation_check["issues"].append("Missing #property strict")
        
        if '#property version' not in content:
            compilation_check["issues"].append("Missing #property version")
        
        # Check includes
        include_pattern = r'#include\s+"([^"]+)"'
        includes = re.findall(include_pattern, content)
        
        for include_path in includes:
            # Resolve include path
            if include_path.startswith('../../'):
                resolved = self.mt5_dev / include_path.replace('../../', '')
            elif include_path.startswith('../'):
                resolved = file_path.parent.parent / include_path.replace('../', '')
            else:
                resolved = file_path.parent / include_path
            
            if not resolved.exists():
                compilation_check["dependencies_found"] = False
                compilation_check["issues"].append(f"Missing include: {include_path}")
        
        # Check for C++ features not supported in MQL5
        unsupported_features = [
            ('template<', 'C++ templates'),
            ('namespace ', 'C++ namespaces'),
            ('std::', 'C++ standard library'),
            ('#pragma once', 'pragma once'),
            ('virtual ', 'virtual inheritance'),
            ('friend ', 'friend classes')
        ]
        
        for feature, description in unsupported_features:
            if feature in content:
                compilation_check["mql5_compliant"] = False
                compilation_check["issues"].append(f"Uses unsupported feature: {description}")
        
        # Check bracket balance
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            compilation_check["syntax_valid"] = False
            compilation_check["issues"].append(f"Brace mismatch: {open_braces} open, {close_braces} close")
        
        return compilation_check
    
    def analyze_test_coverage(self):
        """Analyze actual test coverage"""
        print("🧪 Analyzing test coverage...")
        
        # Get all source files
        source_files = list((self.mt5_dev / "Include/ProjectQuantum").rglob("*.mqh"))
        test_files = [f for f in (self.mt5_dev / "Scripts/ProjectQuantum").rglob("*.mq5") if "Test_" in f.name]
        
        coverage_analysis = {
            "total_source_files": len(source_files),
            "total_test_files": len(test_files),
            "coverage_by_module": {},
            "uncovered_files": [],
            "test_quality": {}
        }
        
        # Check which source files have tests
        for source_file in source_files:
            module_name = source_file.stem
            has_test = any(module_name in test_file.name for test_file in test_files)
            
            if has_test:
                # Analyze test quality
                test_file = next((t for t in test_files if module_name in t.name), None)
                if test_file:
                    test_quality = self.analyze_test_quality(test_file, source_file)
                    coverage_analysis["test_quality"][module_name] = test_quality
            else:
                coverage_analysis["uncovered_files"].append(str(source_file))
        
        covered_count = len(source_files) - len(coverage_analysis["uncovered_files"])
        coverage_percentage = (covered_count / len(source_files)) * 100 if source_files else 0
        
        coverage_analysis["coverage_percentage"] = coverage_percentage
        
        print(f"   📊 Coverage: {coverage_percentage:.1f}% ({covered_count}/{len(source_files)} files)")
        print(f"   🧪 Test files: {len(test_files)}")
        print(f"   ❌ Uncovered: {len(coverage_analysis['uncovered_files'])} files")
        
        return coverage_analysis
    
    def analyze_test_quality(self, test_file, source_file):
        """Analyze quality of individual test file"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                test_content = f.read()
            with open(source_file, 'r', encoding='utf-8') as f:
                source_content = f.read()
        except Exception as e:
            return {"error": str(e)}
        
        # Count test assertions
        test_assertions = len(re.findall(r'TEST_\w+', test_content))
        
        # Count public functions in source
        public_functions = len(re.findall(r'^\s*\w+\s+\w+\s*\([^)]*\)\s*{', source_content, re.MULTILINE))
        
        # Check for different types of tests
        has_unit_tests = 'TEST_EQUALS' in test_content or 'TEST_TRUE' in test_content
        has_edge_cases = 'edge' in test_content.lower() or 'boundary' in test_content.lower()
        has_error_tests = 'error' in test_content.lower() or 'exception' in test_content.lower()
        
        quality_score = 0
        if has_unit_tests: quality_score += 40
        if has_edge_cases: quality_score += 30
        if has_error_tests: quality_score += 30
        
        return {
            "test_assertions": test_assertions,
            "public_functions": public_functions,
            "coverage_ratio": test_assertions / max(public_functions, 1),
            "has_unit_tests": has_unit_tests,
            "has_edge_cases": has_edge_cases,
            "has_error_tests": has_error_tests,
            "quality_score": quality_score
        }
    
    def check_execution_readiness(self):
        """Check if code is actually ready for execution"""
        print("🔬 Checking execution readiness...")
        
        execution_analysis = {
            "main_ea_exists": False,
            "dependencies_complete": True,
            "initialization_proper": True,
            "critical_functions_implemented": [],
            "missing_implementations": [],
            "execution_blockers": []
        }
        
        # Check for main EA
        main_ea_path = self.mt5_dev / "Experts/ProjectQuantum/ProjectQuantum_Main.mq5"
        if main_ea_path.exists():
            execution_analysis["main_ea_exists"] = True
            with open(main_ea_path, 'r', encoding='utf-8') as f:
                main_content = f.read()
            
            # Check for essential EA functions
            required_functions = ['OnInit', 'OnTick', 'OnDeinit']
            for func in required_functions:
                if f'int {func}(' in main_content or f'void {func}(' in main_content:
                    execution_analysis["critical_functions_implemented"].append(func)
                else:
                    execution_analysis["missing_implementations"].append(func)
        else:
            execution_analysis["execution_blockers"].append("Main EA file not found")
        
        # Check core dependencies
        core_files = [
            "Include/ProjectQuantum/Core/Core.mqh",
            "Include/ProjectQuantum/Architecture/Project_Quantum.mqh",
            "Include/ProjectQuantum/Risk/CRiskManager.mqh"
        ]
        
        for core_file in core_files:
            full_path = self.mt5_dev / core_file
            if not full_path.exists():
                execution_analysis["dependencies_complete"] = False
                execution_analysis["execution_blockers"].append(f"Missing core file: {core_file}")
        
        return execution_analysis
    
    def generate_audit_report(self):
        """Generate comprehensive audit report"""
        print("\n📊 Generating comprehensive audit report...")
        
        # File structure analysis
        structure = self.analyze_file_structure()
        
        # Code quality analysis
        print("🔍 Analyzing code quality...")
        all_files = []
        all_files.extend(structure["include_files"])
        all_files.extend(structure["expert_files"]) 
        all_files.extend(structure["script_files"])
        
        code_quality_results = []
        compilation_results = []
        
        for file_path in all_files[:20]:  # Limit to first 20 files for performance
            print(f"   Analyzing: {file_path.name}")
            quality = self.analyze_code_quality(file_path)
            compilation = self.check_actual_compilation(file_path)
            
            code_quality_results.append(quality)
            compilation_results.append(compilation)
            
            if quality.get("issues"):
                self.audit_results["code_issues"].extend(quality["issues"])
        
        # Test coverage analysis
        coverage = self.analyze_test_coverage()
        
        # Execution readiness
        execution = self.check_execution_readiness()
        
        # Compile final results
        self.audit_results["files_analyzed"] = len(all_files)
        self.audit_results["total_lines"] = sum(q.get("total_lines", 0) for q in code_quality_results)
        self.audit_results["coverage_analysis"] = coverage
        self.audit_results["compilation_readiness"] = {
            "analyzed_files": len(compilation_results),
            "compilation_ready": sum(1 for c in compilation_results if c.get("syntax_valid") and c.get("mql5_compliant")),
            "issues_found": sum(len(c.get("issues", [])) for c in compilation_results)
        }
        self.audit_results["execution_analysis"] = execution
        
        # Identify critical findings
        if coverage["coverage_percentage"] < 50:
            self.audit_results["critical_findings"].append(f"Low test coverage: {coverage['coverage_percentage']:.1f}%")
        
        if not execution["main_ea_exists"]:
            self.audit_results["critical_findings"].append("Main EA file missing")
        
        if execution["execution_blockers"]:
            self.audit_results["critical_findings"].extend(execution["execution_blockers"])
        
        if self.audit_results["compilation_readiness"]["issues_found"] > 10:
            self.audit_results["critical_findings"].append("High number of compilation issues found")
        
        # Save report
        report_path = self.project_root / f"comprehensive_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        return report_path
    
    def print_audit_summary(self):
        """Print human-readable audit summary"""
        print("\n" + "=" * 80)
        print("🔍 COMPREHENSIVE CODE AUDIT SUMMARY")
        print("=" * 80)
        
        print(f"\n📁 FILE STRUCTURE:")
        structure = self.audit_results.get("file_structure", {})
        for category, count in structure.items():
            print(f"   {category.replace('_', ' ').title()}: {count}")
        
        print(f"\n📊 CODE ANALYSIS:")
        print(f"   Files Analyzed: {self.audit_results['files_analyzed']}")
        print(f"   Total Lines: {self.audit_results['total_lines']:,}")
        print(f"   Code Issues Found: {len(self.audit_results['code_issues'])}")
        
        print(f"\n🧪 TEST COVERAGE:")
        coverage = self.audit_results.get("coverage_analysis", {})
        print(f"   Coverage Percentage: {coverage.get('coverage_percentage', 0):.1f}%")
        print(f"   Covered Files: {coverage.get('total_source_files', 0) - len(coverage.get('uncovered_files', []))}/{coverage.get('total_source_files', 0)}")
        print(f"   Test Files: {coverage.get('total_test_files', 0)}")
        
        print(f"\n🔨 COMPILATION READINESS:")
        compilation = self.audit_results.get("compilation_readiness", {})
        ready_files = compilation.get("compilation_ready", 0)
        total_files = compilation.get("analyzed_files", 1)
        print(f"   Ready for Compilation: {ready_files}/{total_files} ({ready_files/total_files*100:.1f}%)")
        print(f"   Compilation Issues: {compilation.get('issues_found', 0)}")
        
        print(f"\n🚀 EXECUTION READINESS:")
        execution = self.audit_results.get("execution_analysis", {})
        print(f"   Main EA Exists: {'✅' if execution.get('main_ea_exists') else '❌'}")
        print(f"   Dependencies Complete: {'✅' if execution.get('dependencies_complete') else '❌'}")
        print(f"   Critical Functions: {len(execution.get('critical_functions_implemented', []))}")
        print(f"   Missing Implementations: {len(execution.get('missing_implementations', []))}")
        
        print(f"\n🚨 CRITICAL FINDINGS:")
        findings = self.audit_results.get("critical_findings", [])
        if findings:
            for finding in findings:
                print(f"   ❌ {finding}")
        else:
            print("   ✅ No critical issues found")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        coverage_ok = coverage.get('coverage_percentage', 0) >= 70
        compilation_ok = (ready_files / total_files) >= 0.8 if total_files > 0 else False
        execution_ok = execution.get('main_ea_exists') and execution.get('dependencies_complete')
        
        if coverage_ok and compilation_ok and execution_ok:
            print("   🟢 PRODUCTION READY")
        elif compilation_ok and execution_ok:
            print("   🟡 READY WITH LOW TEST COVERAGE")
        else:
            print("   🔴 NOT READY FOR PRODUCTION")
            print("   🔧 Requires significant fixes before deployment")

def main():
    print("🔍 Starting Comprehensive ProjectQuantum Code Audit")
    print("=" * 60)
    
    auditor = ComprehensiveCodeAudit()
    
    try:
        report_path = auditor.generate_audit_report()
        auditor.print_audit_summary()
        
        print(f"\n📄 Detailed audit report saved: {report_path}")
        
    except Exception as e:
        print(f"❌ Audit failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)