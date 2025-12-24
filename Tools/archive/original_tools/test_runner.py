#!/usr/bin/env python3
"""
ProjectQuantum Unified Test Runner
Consolidated test execution and validation functionality

Combines:
- comprehensive_test_runner.py
- test_actual_compilation.py
- test_compilation_workflow.py
- test_mql5_compilation.py
- test_terminal_compile.py

Author: Renier De Jager
Version: 1.216
"""

import os
import re
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional


class MQL5CompilationValidator:
    """Validates MQL5 file compilation and syntax"""
    
    def __init__(self, mt5_dev: Path, metaeditor: str):
        self.mt5_dev = mt5_dev
        self.metaeditor = metaeditor
    
    def test_include_resolution(self, file_path: Path) -> bool:
        """Test if all includes can be resolved"""
        print(f"🔍 Testing includes for: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        include_pattern = r'#include\s+"([^"]+)"'
        includes = re.findall(include_pattern, content)
        
        all_found = True
        for include_path in includes:
            # Convert relative path to absolute
            if include_path.startswith('../../'):
                # From Scripts/ProjectQuantum to Include
                full_include_path = self.mt5_dev / include_path.replace('../../', '')
            elif include_path.startswith('../'):
                # From Scripts to parent
                script_dir = file_path.parent
                full_include_path = script_dir.parent / include_path.replace('../', '')
            else:
                # Relative to current file
                full_include_path = file_path.parent / include_path
            
            if full_include_path.exists():
                print(f"   ✅ Found: {include_path}")
            else:
                print(f"   ❌ Missing: {include_path} (looked at: {full_include_path})")
                all_found = False
        
        return all_found
    
    def check_test_framework_integration(self, file_path: Path) -> bool:
        """Check if test framework is properly integrated"""
        print(f"🧪 Checking test framework integration: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = {
            "TestFramework include": "TestFramework.mqh" in content,
            "Global framework variable": "g_test_framework" in content,
            "Framework initialization": "new CTestFramework" in content,
            "TEST macros used": "TEST_" in content,
            "OnStart function": "void OnStart()" in content
        }
        
        all_passed = True
        for check_name, passed in checks.items():
            if passed:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
                all_passed = False
        
        return all_passed
    
    def simulate_basic_compilation(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Simulate basic compilation checks"""
        print(f"🔨 Simulating compilation: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        
        # Check for required properties
        if '#property strict' not in content:
            issues.append("Missing #property strict")
        
        if '#property version' not in content:
            issues.append("Missing #property version")
        
        # Check bracket balance (simplified)
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            issues.append(f"Brace mismatch: {open_braces} open, {close_braces} close")
        
        # Check for common MQL5 issues
        if 'namespace ' in content:
            issues.append("MQL5 doesn't support namespaces - use static classes")
        
        if 'template<' in content:
            issues.append("MQL5 doesn't support C++ templates")
        
        success = len(issues) == 0
        
        if success:
            print("   ✅ Basic syntax checks passed")
        else:
            print(f"   ❌ Found {len(issues)} issues:")
            for issue in issues:
                print(f"      • {issue}")
        
        return success, issues
    
    def compile_with_metaeditor(self, file_path: Path, timeout: int = 30) -> Dict[str, Any]:
        """Compile file using MetaEditor"""
        print(f"🔨 Compiling with MetaEditor: {file_path.name}")
        
        if not file_path.exists():
            return {
                "success": False,
                "error": "File not found",
                "compilation_time": 0
            }
        
        start_time = time.time()
        
        try:
            result = subprocess.run([
                self.metaeditor,
                "/compile",
                str(file_path),
                "/log"
            ], capture_output=True, text=True, timeout=timeout)
            
            compilation_time = time.time() - start_time
            
            if result.returncode == 0:
                print(f"   ✅ Compilation successful ({compilation_time:.2f}s)")
                return {
                    "success": True,
                    "compilation_time": compilation_time,
                    "output": result.stdout
                }
            else:
                print(f"   ❌ Compilation failed ({compilation_time:.2f}s)")
                return {
                    "success": False,
                    "compilation_time": compilation_time,
                    "error": result.stderr,
                    "output": result.stdout
                }
        
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Compilation timeout after {timeout}s")
            return {
                "success": False,
                "error": f"Compilation timeout after {timeout}s",
                "compilation_time": timeout
            }
        except Exception as e:
            print(f"   ❌ Compilation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "compilation_time": time.time() - start_time
            }


class TestFileCategorizer:
    """Categorizes test files for organized execution"""
    
    @staticmethod
    def categorize_test_files(test_files: List[Path]) -> Dict[str, List[Path]]:
        """Categorize test files by type and priority"""
        categories = {
            "critical_tests": [],      # Core functionality - run first
            "component_tests": [],     # Component integration
            "intelligence_tests": [],  # AI/ML components
            "physics_tests": [],       # Market physics
            "risk_tests": [],          # Risk management
            "performance_tests": [],   # Performance monitoring
            "architecture_tests": [],  # System architecture
            "other_tests": []          # Miscellaneous
        }
        
        for test_file in test_files:
            file_name = test_file.name.lower()
            
            # Critical core tests - highest priority
            if any(keyword in file_name for keyword in ['core', 'safemath', 'arrayutils', 'symbolutils', 'defensive', 'logger']):
                categories["critical_tests"].append(test_file)
            # Component integration tests
            elif any(keyword in file_name for keyword in ['persistence', 'fileintegrity', 'versionmanager']):
                categories["component_tests"].append(test_file)
            # Intelligence/AI tests
            elif any(keyword in file_name for keyword in ['intelligence', 'learning', 'rl_', 'genetic', 'predictor', 'neural']):
                categories["intelligence_tests"].append(test_file)
            # Physics tests
            elif any(keyword in file_name for keyword in ['physics', 'fractal', 'market', 'cycle', 'normalizer']):
                categories["physics_tests"].append(test_file)
            # Risk management tests
            elif any(keyword in file_name for keyword in ['risk', 'adversary', 'protection', 'guard']):
                categories["risk_tests"].append(test_file)
            # Performance tests
            elif any(keyword in file_name for keyword in ['performance', 'monitor', 'metrics', 'optimizer']):
                categories["performance_tests"].append(test_file)
            # Architecture tests
            elif any(keyword in file_name for keyword in ['architecture', 'quantum', 'journey', 'system']):
                categories["architecture_tests"].append(test_file)
            else:
                categories["other_tests"].append(test_file)
        
        return categories


class ComprehensiveTestRunner:
    """Main test runner with comprehensive validation and execution"""
    
    def __init__(self):
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.metaeditor = "/mnt/c/DevCenter/MT5-Unified/MT5-Core/Terminal/MetaEditor64.exe"
        
        # Initialize components
        self.validator = MQL5CompilationValidator(self.mt5_dev, self.metaeditor)
        
    def discover_all_test_files(self) -> List[Path]:
        """Discover all Test_*.mq5 files"""
        test_dir = self.mt5_dev / "Scripts/ProjectQuantum"
        if not test_dir.exists():
            print(f"❌ Test directory not found: {test_dir}")
            return []
        
        test_files = list(test_dir.glob("Test_*.mq5"))
        
        print(f"🔍 Discovered {len(test_files)} test files:")
        for test_file in sorted(test_files):
            print(f"   📄 {test_file.name}")
        
        return sorted(test_files)
    
    def analyze_test_file_structure(self, test_file: Path) -> Dict[str, Any]:
        """Analyze test file structure and content"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count test assertions
            test_count = len(re.findall(r'TEST_\w+\(', content))
            
            # Check structure components
            has_onstart = 'void OnStart()' in content
            has_framework = 'g_test_framework' in content
            has_test_suite = 'TEST_SUITE(' in content
            has_proper_includes = 'TestFramework.mqh' in content
            
            # Analyze test functions
            test_functions = re.findall(r'void\s+(Test_\w+)\s*\(', content)
            
            result = {
                "file": test_file.name,
                "file_path": str(test_file),
                "test_count": test_count,
                "test_functions": test_functions,
                "has_onstart": has_onstart,
                "has_framework": has_framework,
                "has_test_suite": has_test_suite,
                "has_proper_includes": has_proper_includes,
                "has_proper_structure": has_onstart and has_framework and has_test_suite,
                "size_bytes": test_file.stat().st_size,
                "last_modified": datetime.fromtimestamp(test_file.stat().st_mtime).isoformat(),
                "status": "unknown"
            }
            
            return result
            
        except Exception as e:
            return {
                "file": test_file.name,
                "file_path": str(test_file),
                "test_count": 0,
                "test_functions": [],
                "has_proper_structure": False,
                "status": "ERROR",
                "error": str(e)
            }
    
    def run_single_test_comprehensive(self, test_file: Path, run_compilation: bool = True) -> Dict[str, Any]:
        """Run comprehensive testing on a single file"""
        print(f"\n🧪 Comprehensive Test: {test_file.name}")
        print("-" * 50)
        
        start_time = time.time()
        
        # Step 1: Analyze file structure
        analysis = self.analyze_test_file_structure(test_file)
        
        # Step 2: Validate includes
        includes_valid = self.validator.test_include_resolution(test_file)
        analysis["includes_valid"] = includes_valid
        
        # Step 3: Check test framework integration
        framework_integration = self.validator.check_test_framework_integration(test_file)
        analysis["framework_integration"] = framework_integration
        
        # Step 4: Simulate compilation
        syntax_valid, syntax_issues = self.validator.simulate_basic_compilation(test_file)
        analysis["syntax_valid"] = syntax_valid
        analysis["syntax_issues"] = syntax_issues
        
        # Step 5: Actual compilation (if requested)
        if run_compilation:
            compilation_result = self.validator.compile_with_metaeditor(test_file)
            analysis["compilation"] = compilation_result
        else:
            analysis["compilation"] = {"skipped": True}
        
        # Determine overall status
        if analysis["has_proper_structure"] and includes_valid and framework_integration and syntax_valid:
            if not run_compilation or (run_compilation and analysis["compilation"].get("success", False)):
                analysis["status"] = "PASS"
            else:
                analysis["status"] = "COMPILATION_FAILED"
        else:
            analysis["status"] = "STRUCTURE_ISSUES"
        
        analysis["total_test_time"] = time.time() - start_time
        
        # Print summary
        status_emoji = "✅" if analysis["status"] == "PASS" else "❌"
        print(f"   {status_emoji} Status: {analysis['status']}")
        print(f"   🔢 Test Count: {analysis['test_count']}")
        print(f"   ⏱️  Test Time: {analysis['total_test_time']:.2f}s")
        
        return analysis
    
    def run_test_suite_by_category(self, category: str, test_files: List[Path], run_compilation: bool = True) -> Dict[str, Any]:
        """Run all tests in a specific category"""
        print(f"\n🗂️  Running {category.replace('_', ' ').title()}:")
        print("=" * 60)
        
        category_results = {
            "category": category,
            "total_files": len(test_files),
            "results": [],
            "summary": {
                "passed": 0,
                "failed": 0,
                "total_tests": 0,
                "total_time": 0
            }
        }
        
        for test_file in test_files:
            result = self.run_single_test_comprehensive(test_file, run_compilation)
            category_results["results"].append(result)
            
            # Update summary
            if result["status"] == "PASS":
                category_results["summary"]["passed"] += 1
            else:
                category_results["summary"]["failed"] += 1
            
            category_results["summary"]["total_tests"] += result["test_count"]
            category_results["summary"]["total_time"] += result["total_test_time"]
        
        # Print category summary
        summary = category_results["summary"]
        success_rate = (summary["passed"] / len(test_files)) * 100 if test_files else 0
        
        print(f"\n📊 {category.replace('_', ' ').title()} Summary:")
        print(f"   Files: {summary['passed']}/{len(test_files)} passed ({success_rate:.1f}%)")
        print(f"   Tests: {summary['total_tests']} total test assertions")
        print(f"   Time: {summary['total_time']:.2f}s")
        
        return category_results
    
    def generate_comprehensive_report(self, all_results: List[Dict[str, Any]], categories: Dict[str, List[Path]]) -> Dict[str, Any]:
        """Generate comprehensive test execution report"""
        print(f"\n" + "=" * 80)
        print("🎯 COMPREHENSIVE TEST EXECUTION REPORT")
        print("=" * 80)
        
        # Calculate overall statistics
        total_files = sum(len(category_result["results"]) for category_result in all_results)
        total_passed = sum(category_result["summary"]["passed"] for category_result in all_results)
        total_tests = sum(category_result["summary"]["total_tests"] for category_result in all_results)
        total_time = sum(category_result["summary"]["total_time"] for category_result in all_results)
        
        overall_success_rate = (total_passed / total_files) * 100 if total_files > 0 else 0
        
        # Coverage analysis
        source_files = len(list((self.mt5_dev / "Include/ProjectQuantum").rglob("*.mqh")))
        coverage_percentage = (total_files / source_files) * 100 if source_files > 0 else 0
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total Test Files: {total_files}")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ❌ Failed: {total_files - total_passed}")
        print(f"   📈 Success Rate: {overall_success_rate:.1f}%")
        print(f"   🔢 Total Test Assertions: {total_tests}")
        print(f"   ⏱️  Total Execution Time: {total_time:.2f}s")
        
        print(f"\n📈 COVERAGE ANALYSIS:")
        print(f"   Source Files: {source_files}")
        print(f"   Test Files: {total_files}")
        print(f"   Coverage: {coverage_percentage:.1f}%")
        
        # Category breakdown
        print(f"\n📂 CATEGORY BREAKDOWN:")
        for category_result in all_results:
            category = category_result["category"]
            summary = category_result["summary"]
            success_rate = (summary["passed"] / category_result["total_files"]) * 100 if category_result["total_files"] > 0 else 0
            
            print(f"   {category.replace('_', ' ').title()}: {summary['passed']}/{category_result['total_files']} files ({success_rate:.1f}%), {summary['total_tests']} tests")
        
        # Files with issues
        failed_files = []
        for category_result in all_results:
            for result in category_result["results"]:
                if result["status"] != "PASS":
                    failed_files.append(result)
        
        if failed_files:
            print(f"\n⚠️  FILES WITH ISSUES ({len(failed_files)}):")
            for result in failed_files:
                print(f"   • {result['file']}: {result['status']}")
                if "syntax_issues" in result and result["syntax_issues"]:
                    for issue in result["syntax_issues"][:3]:  # Show first 3 issues
                        print(f"     - {issue}")
        
        # Success assessment
        if overall_success_rate >= 90:
            print(f"\n🎉 EXCELLENT! Test suite is in great shape!")
        elif overall_success_rate >= 75:
            print(f"\n✅ GOOD! Most tests are working properly.")
        elif overall_success_rate >= 50:
            print(f"\n⚠️  NEEDS ATTENTION: Several tests require fixes.")
        else:
            print(f"\n❌ CRITICAL: Many tests need immediate attention.")
        
        # Prepare final report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.216",
            "execution_summary": {
                "total_files": total_files,
                "passed_files": total_passed,
                "failed_files": total_files - total_passed,
                "success_rate": overall_success_rate,
                "total_test_assertions": total_tests,
                "total_execution_time": total_time,
                "coverage_percentage": coverage_percentage
            },
            "category_results": all_results,
            "failed_files": failed_files
        }
        
        return report_data
    
    def run_comprehensive_test_suite(self, run_compilation: bool = True, max_files_per_category: Optional[int] = None) -> bool:
        """Run the complete comprehensive test suite"""
        print("🚀 ProjectQuantum Comprehensive Test Suite")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Compilation: {'Enabled' if run_compilation else 'Disabled (Validation Only)'}")
        if max_files_per_category:
            print(f"Max files per category: {max_files_per_category}")
        print()
        
        # Step 1: Discover all test files
        test_files = self.discover_all_test_files()
        
        if not test_files:
            print("❌ No test files found!")
            return False
        
        # Step 2: Categorize tests
        categories = TestFileCategorizer.categorize_test_files(test_files)
        
        print(f"\n📊 Test File Categorization:")
        for category, files in categories.items():
            if files:
                limited_files = files[:max_files_per_category] if max_files_per_category else files
                print(f"   {category.replace('_', ' ').title()}: {len(limited_files)}/{len(files)} files")
        
        # Step 3: Run tests by category (critical first)
        execution_order = [
            "critical_tests", "component_tests", "intelligence_tests", 
            "physics_tests", "risk_tests", "performance_tests", 
            "architecture_tests", "other_tests"
        ]
        
        all_results = []
        
        for category in execution_order:
            if categories[category]:
                limited_files = categories[category][:max_files_per_category] if max_files_per_category else categories[category]
                category_result = self.run_test_suite_by_category(category, limited_files, run_compilation)
                all_results.append(category_result)
        
        # Step 4: Generate comprehensive report
        report_data = self.generate_comprehensive_report(all_results, categories)
        
        # Step 5: Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.project_root / "test_reports" / f"comprehensive_test_report_{timestamp}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_path}")
        
        # Determine success
        success_threshold = 80.0  # 80% success rate required
        success = report_data["execution_summary"]["success_rate"] >= success_threshold
        
        print(f"\n🎯 FINAL RESULT: {'✅ SUCCESS' if success else '❌ NEEDS IMPROVEMENT'}")
        print(f"Success Rate: {report_data['execution_summary']['success_rate']:.1f}% (threshold: {success_threshold}%)")
        
        return success


def main():
    """Main entry point for the test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ProjectQuantum Comprehensive Test Runner')
    parser.add_argument('--no-compilation', action='store_true', help='Skip actual compilation (validation only)')
    parser.add_argument('--max-files', type=int, help='Maximum files per category to test')
    parser.add_argument('--category', help='Run only specific category')
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    if args.category:
        # Run specific category only
        test_files = runner.discover_all_test_files()
        categories = TestFileCategorizer.categorize_test_files(test_files)
        
        if args.category in categories and categories[args.category]:
            category_files = categories[args.category][:args.max_files] if args.max_files else categories[args.category]
            result = runner.run_test_suite_by_category(args.category, category_files, not args.no_compilation)
            return 0 if result["summary"]["passed"] == len(category_files) else 1
        else:
            print(f"❌ Category '{args.category}' not found or empty")
            return 1
    else:
        # Run comprehensive suite
        success = runner.run_comprehensive_test_suite(
            run_compilation=not args.no_compilation,
            max_files_per_category=args.max_files
        )
        return 0 if success else 1


if __name__ == "__main__":
    exit(main())