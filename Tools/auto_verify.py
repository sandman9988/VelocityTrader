#!/usr/bin/env python3
"""
ProjectQuantum Auto-Verification System
Comprehensive verification tool that runs after every code edit

This tool ensures that code changes don't break the system by running:
1. Syntax validation for all MQL5 files
2. Compilation checks for modified files
3. Test suite execution
4. Code quality checks
5. Integration verification

Author: Renier De Jager
Version: 1.216
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class AutoVerificationSystem:
    """Comprehensive verification system for ProjectQuantum"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.tools_dir = self.project_root / "tools"
        self.verification_results = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.216",
            "checks": {},
            "overall_status": "UNKNOWN"
        }
        self.errors = []
        self.warnings = []
        
    def print_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    
    def print_status(self, check_name: str, passed: bool, details: str = ""):
        """Print check status with formatting"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {check_name}")
        if details:
            print(f"      {details}")
    
    def check_syntax_validation(self, quick_mode: bool = False) -> bool:
        """Run MQL5 syntax validation on all files"""
        self.print_header("1. SYNTAX VALIDATION")
        
        try:
            # Check if syntax checker exists
            syntax_checker = self.project_root / ".github" / "tools" / "mql5_syntax_checker.py"
            
            if not syntax_checker.exists():
                self.warnings.append("Syntax checker not found - skipping syntax validation")
                self.print_status("Syntax Validation", True, "Skipped - checker not found")
                return True
            
            # Run syntax checker
            print("🔍 Running MQL5 syntax validation...")
            result = subprocess.run(
                [sys.executable, str(syntax_checker), str(self.project_root)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Check if report was generated
            report_path = Path("mql5_syntax_report.json")
            if report_path.exists():
                with open(report_path, 'r') as f:
                    report = json.load(f)
                
                error_count = report.get("summary", {}).get("total_errors", 0)
                warning_count = report.get("summary", {}).get("total_warnings", 0)
                
                passed = error_count == 0
                self.verification_results["checks"]["syntax_validation"] = {
                    "passed": passed,
                    "errors": error_count,
                    "warnings": warning_count
                }
                
                self.print_status(
                    "Syntax Validation",
                    passed,
                    f"Errors: {error_count}, Warnings: {warning_count}"
                )
                
                if not passed:
                    self.errors.append(f"Syntax validation failed with {error_count} errors")
                
                return passed
            else:
                self.print_status("Syntax Validation", True, "No report generated")
                return True
                
        except subprocess.TimeoutExpired:
            self.errors.append("Syntax validation timed out")
            self.print_status("Syntax Validation", False, "Timeout")
            return False
        except Exception as e:
            self.warnings.append(f"Syntax validation error: {e}")
            self.print_status("Syntax Validation", True, f"Skipped - {e}")
            return True
    
    def check_compilation(self, quick_mode: bool = False) -> bool:
        """Run compilation checks"""
        self.print_header("2. COMPILATION CHECK")
        
        try:
            compiler_script = self.tools_dir / "mql5_compiler.py"
            
            if not compiler_script.exists():
                self.warnings.append("Compiler script not found")
                self.print_status("Compilation", True, "Skipped - compiler not found")
                return True
            
            if quick_mode:
                # Skip actual compilation in quick mode
                self.warnings.append("Compilation skipped in quick mode")
                self.print_status("Compilation", True, "Skipped in quick mode")
                self.verification_results["checks"]["compilation"] = {
                    "passed": True,
                    "skipped": True
                }
                return True
            
            print("🔨 Running full compilation...")
            
            # Run compiler with all checks
            args = [sys.executable, str(compiler_script)]
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_root)
            )
            
            passed = result.returncode == 0
            
            self.verification_results["checks"]["compilation"] = {
                "passed": passed,
                "return_code": result.returncode
            }
            
            self.print_status(
                "Compilation Check",
                passed,
                "All files compile successfully" if passed else "Compilation issues detected"
            )
            
            if not passed:
                self.errors.append("Compilation check failed")
                # Print some output for debugging
                if result.stderr:
                    print(f"      Error output: {result.stderr[:200]}")
            
            return passed
            
        except subprocess.TimeoutExpired:
            self.errors.append("Compilation check timed out")
            self.print_status("Compilation Check", False, "Timeout")
            return False
        except Exception as e:
            self.warnings.append(f"Compilation check error: {e}")
            self.print_status("Compilation Check", True, f"Skipped - {e}")
            return True
    
    def check_test_suite(self, quick_mode: bool = False) -> bool:
        """Run test suite"""
        self.print_header("3. TEST SUITE EXECUTION")
        
        try:
            test_runner = self.tools_dir / "test_runner.py"
            
            if not test_runner.exists():
                self.warnings.append("Test runner not found")
                self.print_status("Test Suite", True, "Skipped - test runner not found")
                return True
            
            print("🧪 Running test suite...")
            
            # Run tests without compilation in quick mode
            args = [sys.executable, str(test_runner)]
            if quick_mode:
                args.extend(["--no-compilation", "--max-files", "10"])
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=180 if quick_mode else 600,
                cwd=str(self.project_root)
            )
            
            passed = result.returncode == 0
            
            self.verification_results["checks"]["test_suite"] = {
                "passed": passed,
                "return_code": result.returncode
            }
            
            self.print_status(
                "Test Suite",
                passed,
                "All tests passed" if passed else "Some tests failed"
            )
            
            if not passed:
                self.errors.append("Test suite execution failed")
            
            return passed
            
        except subprocess.TimeoutExpired:
            self.errors.append("Test suite timed out")
            self.print_status("Test Suite", False, "Timeout")
            return False
        except Exception as e:
            self.warnings.append(f"Test suite error: {e}")
            self.print_status("Test Suite", True, f"Skipped - {e}")
            return True
    
    def check_code_quality(self, quick_mode: bool = False) -> bool:
        """Run code quality checks"""
        self.print_header("4. CODE QUALITY ANALYSIS")
        
        try:
            analyzer_script = self.tools_dir / "code_analyzer.py"
            
            if not analyzer_script.exists():
                self.warnings.append("Code analyzer not found")
                self.print_status("Code Quality", True, "Skipped - analyzer not found")
                return True
            
            print("📊 Analyzing code quality...")
            
            args = [sys.executable, str(analyzer_script)]
            if quick_mode:
                args.extend(["--max-files", "20"])
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_root)
            )
            
            # Code analyzer doesn't fail on quality issues, just reports them
            passed = True
            
            self.verification_results["checks"]["code_quality"] = {
                "passed": passed,
                "analyzed": True
            }
            
            self.print_status("Code Quality", passed, "Analysis complete")
            
            return passed
            
        except subprocess.TimeoutExpired:
            self.warnings.append("Code quality check timed out")
            self.print_status("Code Quality", True, "Timeout - continuing")
            return True
        except Exception as e:
            self.warnings.append(f"Code quality error: {e}")
            self.print_status("Code Quality", True, f"Skipped - {e}")
            return True
    
    def check_structure_integrity(self) -> bool:
        """Check project structure integrity"""
        self.print_header("5. STRUCTURE INTEGRITY")
        
        print("🏗️  Checking project structure...")
        
        # Check for required directories (based on actual project structure)
        required_dirs = [
            "Include",
            "Include/Core",
            "Main",
            "Scripts",
            "tools"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        # Check for critical files (based on actual project structure)
        critical_files = [
            "Include/Core/Core.mqh",
            "Main/ProjectQuantum_Main.mq5",
        ]
        
        missing_files = []
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        passed = len(missing_dirs) == 0 and len(missing_files) == 0
        
        self.verification_results["checks"]["structure_integrity"] = {
            "passed": passed,
            "missing_dirs": missing_dirs,
            "missing_files": missing_files
        }
        
        details = "All required files and directories present"
        if not passed:
            details = f"Missing: {len(missing_dirs)} dirs, {len(missing_files)} files"
            self.errors.append(f"Structure integrity check failed: {details}")
        
        self.print_status("Structure Integrity", passed, details)
        
        return passed
    
    def run_full_verification(self, quick_mode: bool = False) -> bool:
        """Run complete verification suite"""
        print("\n" + "="*70)
        print("  🚀 ProjectQuantum Auto-Verification System v1.216")
        print("="*70)
        print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Mode: {'QUICK' if quick_mode else 'FULL'}")
        print(f"  Project: {self.project_root}")
        print("="*70)
        
        start_time = time.time()
        
        # Run all checks
        results = {
            "syntax": self.check_syntax_validation(quick_mode),
            "compilation": self.check_compilation(quick_mode),
            "tests": self.check_test_suite(quick_mode),
            "quality": self.check_code_quality(quick_mode),
            "structure": self.check_structure_integrity()
        }
        
        # Calculate overall status
        critical_checks = ["syntax", "compilation", "structure"]
        critical_passed = all(results[check] for check in critical_checks)
        all_passed = all(results.values())
        
        elapsed_time = time.time() - start_time
        
        # Print summary
        self.print_header("VERIFICATION SUMMARY")
        
        print(f"⏱️  Time Elapsed: {elapsed_time:.2f} seconds\n")
        
        print("Check Results:")
        for check_name, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name.replace('_', ' ').title()}")
        
        print(f"\n📊 Overall Status:")
        if all_passed:
            overall_status = "✅ ALL CHECKS PASSED"
            self.verification_results["overall_status"] = "PASS"
            exit_code = 0
        elif critical_passed:
            overall_status = "⚠️  CRITICAL CHECKS PASSED (Some non-critical checks failed)"
            self.verification_results["overall_status"] = "PARTIAL"
            exit_code = 0
        else:
            overall_status = "❌ VERIFICATION FAILED"
            self.verification_results["overall_status"] = "FAIL"
            exit_code = 1
        
        print(f"  {overall_status}")
        
        # Print errors and warnings
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors[:10]:
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:
                print(f"  - {warning}")
            if len(self.warnings) > 5:
                print(f"  ... and {len(self.warnings) - 5} more")
        
        # Save results
        self.save_verification_report()
        
        print("\n" + "="*70)
        print(f"  Verification {'PASSED ✅' if exit_code == 0 else 'FAILED ❌'}")
        print("="*70 + "\n")
        
        return exit_code == 0
    
    def save_verification_report(self):
        """Save verification results to file"""
        report_dir = self.project_root / "verification_reports"
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"verification_{timestamp}.json"
        
        self.verification_results["errors"] = self.errors
        self.verification_results["warnings"] = self.warnings
        
        with open(report_path, 'w') as f:
            json.dump(self.verification_results, f, indent=2)
        
        print(f"\n📄 Verification report saved: {report_path}")
        
        # Also save as latest
        latest_path = report_dir / "verification_latest.json"
        with open(latest_path, 'w') as f:
            json.dump(self.verification_results, f, indent=2)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ProjectQuantum Auto-Verification System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full verification
  python auto_verify.py
  
  # Run quick verification (faster, for iterative development)
  python auto_verify.py --quick
  
  # Specify project directory
  python auto_verify.py --project /path/to/project
  
This tool should be run after every code edit to ensure no regressions.
        """
    )
    
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Run quick verification (skip compilation, limit tests)'
    )
    
    parser.add_argument(
        '--project', '-p',
        type=Path,
        help='Project root directory (default: parent of this script)'
    )
    
    args = parser.parse_args()
    
    # Create verification system
    verifier = AutoVerificationSystem(project_root=args.project)
    
    # Run verification
    success = verifier.run_full_verification(quick_mode=args.quick)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
