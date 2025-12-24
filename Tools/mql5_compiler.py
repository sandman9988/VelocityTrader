#!/usr/bin/env python3
"""
ProjectQuantum Unified MQL5 Compiler
Consolidated compilation and validation functionality

Combines:
- mql5_dependency_compiler.py
- compilation_validator.py
- compile_all_mqh.py
- fix_mql5_compilation.py

Author: Renier De Jager
Version: 1.216
"""

import os
import sys
import re
import json
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class DependencyResolver:
    """Resolves compilation dependencies for MQL5 files"""
    
    def __init__(self, mt5_dev: Path):
        self.mt5_dev = mt5_dev
        self.dependency_cache = {}
        
        # Define compilation order based on dependencies
        self.compilation_order = [
            # Level 0: Core utilities (no dependencies)
            "Include/ProjectQuantum/Core/SafeMath.mqh",
            "Include/ProjectQuantum/Core/ArrayUtils.mqh",
            "Include/ProjectQuantum/Core/SymbolUtils.mqh",
            
            # Level 1: Basic components
            "Include/ProjectQuantum/Core/CLogger.mqh",
            "Include/ProjectQuantum/Core/Defensive.mqh",
            "Include/ProjectQuantum/Core/TestFramework.mqh",
            
            # Level 2: Advanced core
            "Include/ProjectQuantum/Core/CVersionManager.mqh",
            "Include/ProjectQuantum/Core/CFileIntegrity.mqh",
            "Include/ProjectQuantum/Core/CSymbolNormalizer.mqh",
            "Include/ProjectQuantum/Core/CAdaptiveNormalizer.mqh",
            "Include/ProjectQuantum/Core/CDominantCycle.mqh",
            "Include/ProjectQuantum/Core/CSystemOptimizer.mqh",
            "Include/ProjectQuantum/Core/CPersistence.mqh",
            
            # Level 3: Architecture
            "Include/ProjectQuantum/Architecture/ProjectQuantum_Architecture.mqh",
            "Include/ProjectQuantum/Architecture/Journey_Architecture.mqh",
            
            # Level 4: Core aggregation
            "Include/ProjectQuantum/Core/Core.mqh",
            
            # Level 5: Domain components
            "Include/ProjectQuantum/Intelligence/CRL_Agent.mqh",
            "Include/ProjectQuantum/Physics/CMarketPhysics.mqh",
            "Include/ProjectQuantum/Risk/CAdversarialRisk.mqh",
            
            # Level 6: Main systems
            "Include/ProjectQuantum/Intelligence/Intelligence.mqh",
            "Include/ProjectQuantum/Physics/Physics.mqh",
            "Include/ProjectQuantum/Risk/Risk.mqh",
            
            # Level 7: Full integration
            "Include/ProjectQuantum/ProjectQuantum.mqh",
            
            # Level 8: Expert Advisors
            "Experts/ProjectQuantum_EA.mq5"
        ]
    
    def get_file_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from file includes"""
        if str(file_path) in self.dependency_cache:
            return self.dependency_cache[str(file_path)]
        
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find include statements
            include_pattern = r'#include\s+"([^"]+)"'
            includes = re.findall(include_pattern, content)
            
            for include_path in includes:
                # Convert relative paths to absolute
                if include_path.startswith('../'):
                    # Resolve relative path
                    resolved_path = str((file_path.parent / include_path).resolve().relative_to(self.mt5_dev))
                    dependencies.append(resolved_path)
                else:
                    dependencies.append(include_path)
            
            self.dependency_cache[str(file_path)] = dependencies
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to parse dependencies for {file_path}: {e}")
        
        return dependencies
    
    def sort_by_dependencies(self, files: List[Path]) -> List[Path]:
        """Sort files by dependency order"""
        # Use predefined order if available
        ordered_files = []
        remaining_files = list(files)
        
        for ordered_path in self.compilation_order:
            ordered_file = self.mt5_dev / ordered_path
            if ordered_file in remaining_files:
                ordered_files.append(ordered_file)
                remaining_files.remove(ordered_file)
        
        # Add remaining files that aren't in the predefined order
        ordered_files.extend(remaining_files)
        
        return ordered_files


class MQL5SyntaxValidator:
    """Validates MQL5 syntax and common issues"""
    
    @staticmethod
    def validate_file_syntax(file_path: Path) -> Tuple[bool, List[str]]:
        """Validate basic MQL5 syntax"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            
            # Check bracket balance
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                issues.append(f"Brace mismatch: {open_braces} open, {close_braces} close")
            
            open_parens = content.count('(')
            close_parens = content.count(')')
            if open_parens != close_parens:
                issues.append(f"Parentheses mismatch: {open_parens} open, {close_parens} close")
            
            # Check for required properties in .mq5 files
            if file_path.suffix == '.mq5':
                if '#property strict' not in content:
                    issues.append("Missing #property strict")
                
                if '#property version' not in content:
                    issues.append("Missing #property version")
            
            # Check for common MQL5 issues
            if 'namespace ' in content:
                issues.append("MQL5 doesn't support namespaces - use static classes")
            
            if 'template<' in content:
                issues.append("MQL5 doesn't support C++ templates")
            
            # Check for missing semicolons (basic check)
            lines = content.split('\n')
            for i, line in enumerate(lines[:100]):  # Check first 100 lines only
                line = line.strip()
                if (line and 
                    not line.startswith('//') and 
                    not line.startswith('/*') and
                    not line.endswith(';') and
                    not line.endswith('{') and
                    not line.endswith('}') and
                    not line.startswith('#') and
                    not line.startswith('class') and
                    not line.startswith('struct') and
                    not line.startswith('enum') and
                    '(' not in line and
                    len(line) > 5):
                    # This might be missing a semicolon
                    # But this is a very basic check - many false positives possible
                    pass  # Skip this check for now
            
            return len(issues) == 0, issues
            
        except Exception as e:
            return False, [f"Error reading file: {e}"]


class FileHeaderManager:
    """Manages standardized headers for MQL5 files"""
    
    def __init__(self, version: str = "1.216", author: str = "Renier De Jager"):
        self.version = version
        self.author = author
        self.copyright_year = "2024"
        self.company = "Quantum Trading Systems"
        self.link = "https://www.quantum-trading.ai"
    
    def generate_standard_header(self, file_type: str = "mqh") -> str:
        """Generate standard header for MQL5 files"""
        if file_type == "mq5":
            return f'''//+------------------------------------------------------------------+
//|                                             Project Quantum v{self.version} |
//|                          Copyright {self.copyright_year}, {self.company} |
//|                                   {self.link} |
//|                                        Author: {self.author} |
//+------------------------------------------------------------------+
#property copyright "{self.author}"
#property link      "{self.link}"
#property version   "{self.version}"
#property strict
'''
        else:  # mqh
            return f'''//+------------------------------------------------------------------+
//|                                             Project Quantum v{self.version} |
//|                          Copyright {self.copyright_year}, {self.company} |
//|                                   {self.link} |
//|                                        Author: {self.author} |
//+------------------------------------------------------------------+
#property copyright "{self.author}"
#property link      "{self.link}"
#property version   "{self.version}"
#property strict
'''
    
    def update_file_header(self, file_path: Path) -> bool:
        """Update header in a single MQL5 file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find first significant line (after header)
            lines = content.split('\n')
            content_start = 0
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if (stripped.startswith('#include') or 
                    stripped.startswith('class ') or 
                    stripped.startswith('enum ') or
                    stripped.startswith('struct ') or
                    stripped.startswith('template') or
                    stripped.startswith('//---') or
                    (stripped.startswith('//') and any(keyword in stripped.lower() for keyword in ['function', 'class', 'implementation']))):
                    content_start = i
                    break
            
            # Generate new content with standard header
            file_type = file_path.suffix[1:]  # Remove the dot
            new_content = self.generate_standard_header(file_type) + '\n'
            
            if content_start < len(lines):
                new_content += '\n'.join(lines[content_start:])
            
            # Write updated file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update header in {file_path}: {e}")
            return False


class MetaEditorCompiler:
    """Handles compilation using MetaEditor"""
    
    def __init__(self, metaeditor_path: str, timeout: int = 60):
        self.metaeditor_path = metaeditor_path
        self.timeout = timeout
    
    def compile_file(self, file_path: Path, log_file: Optional[Path] = None) -> Dict[str, Any]:
        """Compile a single file using MetaEditor"""
        start_time = time.time()
        
        try:
            # Prepare command
            cmd = [self.metaeditor_path, "/compile", str(file_path)]
            
            if log_file:
                cmd.extend(["/log", str(log_file)])
            
            # Run compilation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            compilation_time = time.time() - start_time
            
            # Parse result
            success = result.returncode == 0
            
            compilation_result = {
                "success": success,
                "return_code": result.returncode,
                "compilation_time": compilation_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
            
            # Try to read log file if provided
            if log_file and log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        compilation_result["log"] = f.read()
                except:
                    pass
            
            return compilation_result
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "return_code": -1,
                "compilation_time": self.timeout,
                "error": f"Compilation timeout after {self.timeout}s",
                "command": " ".join(cmd) if 'cmd' in locals() else "Command not set"
            }
        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "compilation_time": time.time() - start_time,
                "error": str(e),
                "command": " ".join(cmd) if 'cmd' in locals() else "Command not set"
            }
    
    def compile_batch(self, files: List[Path], stop_on_error: bool = False) -> Dict[str, Any]:
        """Compile multiple files in order"""
        results = {
            "files": {},
            "summary": {
                "total": len(files),
                "successful": 0,
                "failed": 0,
                "total_time": 0
            }
        }
        
        start_time = time.time()
        
        for file_path in files:
            print(f"🔨 Compiling {file_path.name}...")
            
            compilation_result = self.compile_file(file_path)
            results["files"][str(file_path)] = compilation_result
            results["summary"]["total_time"] += compilation_result["compilation_time"]
            
            if compilation_result["success"]:
                results["summary"]["successful"] += 1
                print(f"   ✅ Success ({compilation_result['compilation_time']:.2f}s)")
            else:
                results["summary"]["failed"] += 1
                print(f"   ❌ Failed ({compilation_result['compilation_time']:.2f}s)")
                if compilation_result.get("error"):
                    print(f"      Error: {compilation_result['error']}")
                
                if stop_on_error:
                    print(f"❌ Stopping compilation due to error in {file_path.name}")
                    break
        
        results["summary"]["total_time"] = time.time() - start_time
        results["summary"]["success_rate"] = (
            results["summary"]["successful"] / results["summary"]["total"]
            if results["summary"]["total"] > 0 else 0
        )
        
        return results


class UnifiedMQL5Compiler:
    """Main compiler class combining all functionality"""
    
    def __init__(self):
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.metaeditor = "/mnt/c/DevCenter/MT5-Unified/MT5-Core/Terminal/MetaEditor64.exe"
        
        # Initialize components
        self.dependency_resolver = DependencyResolver(self.mt5_dev)
        self.syntax_validator = MQL5SyntaxValidator()
        self.header_manager = FileHeaderManager()
        self.compiler = MetaEditorCompiler(self.metaeditor)
        
        # Ensure compilation logs directory
        self.logs_dir = self.project_root / "compilation_logs"
        self.logs_dir.mkdir(exist_ok=True)
    
    def discover_files(self, file_types: List[str] = ["*.mqh", "*.mq5"]) -> Dict[str, List[Path]]:
        """Discover all MQL5 files in the project"""
        discovered_files = {}
        
        for file_type in file_types:
            if file_type == "*.mqh":
                files = list((self.mt5_dev / "Include/ProjectQuantum").rglob("*.mqh"))
                discovered_files["mqh_files"] = files
            elif file_type == "*.mq5":
                files = list((self.mt5_dev / "Scripts/ProjectQuantum").rglob("*.mq5"))
                files.extend(list((self.mt5_dev / "Experts").rglob("*ProjectQuantum*.mq5")))
                discovered_files["mq5_files"] = files
        
        return discovered_files
    
    def validate_syntax_batch(self, files: List[Path]) -> Dict[str, Any]:
        """Validate syntax for multiple files"""
        results = {
            "files": {},
            "summary": {
                "total": len(files),
                "valid": 0,
                "invalid": 0
            }
        }
        
        for file_path in files:
            is_valid, issues = self.syntax_validator.validate_file_syntax(file_path)
            
            results["files"][str(file_path)] = {
                "valid": is_valid,
                "issues": issues
            }
            
            if is_valid:
                results["summary"]["valid"] += 1
            else:
                results["summary"]["invalid"] += 1
        
        return results
    
    def update_headers_batch(self, files: List[Path]) -> Dict[str, Any]:
        """Update headers for multiple files"""
        results = {
            "files": {},
            "summary": {
                "total": len(files),
                "updated": 0,
                "failed": 0
            }
        }
        
        for file_path in files:
            success = self.header_manager.update_file_header(file_path)
            
            results["files"][str(file_path)] = {"updated": success}
            
            if success:
                results["summary"]["updated"] += 1
            else:
                results["summary"]["failed"] += 1
        
        return results
    
    def compile_project(self, 
                       compile_mqh: bool = True, 
                       compile_mq5: bool = True,
                       update_headers: bool = True,
                       validate_syntax: bool = True,
                       dependency_order: bool = True,
                       stop_on_error: bool = False) -> Dict[str, Any]:
        """Compile entire project with options"""
        
        print("🚀 ProjectQuantum Unified MQL5 Compiler")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Options: Headers={update_headers}, Syntax={validate_syntax}, Dependencies={dependency_order}")
        print()
        
        # Discover all files
        print("🔍 Discovering MQL5 files...")
        all_files = self.discover_files()
        mqh_files = all_files.get("mqh_files", [])
        mq5_files = all_files.get("mq5_files", [])
        
        print(f"   Found {len(mqh_files)} .mqh files")
        print(f"   Found {len(mq5_files)} .mq5 files")
        
        compilation_results = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.216",
            "options": {
                "compile_mqh": compile_mqh,
                "compile_mq5": compile_mq5,
                "update_headers": update_headers,
                "validate_syntax": validate_syntax,
                "dependency_order": dependency_order,
                "stop_on_error": stop_on_error
            },
            "discovered_files": {
                "mqh_count": len(mqh_files),
                "mq5_count": len(mq5_files)
            }
        }
        
        # Step 1: Update headers if requested
        if update_headers:
            print("\n📝 Updating file headers...")
            all_source_files = mqh_files + mq5_files
            header_results = self.update_headers_batch(all_source_files)
            compilation_results["header_updates"] = header_results
            print(f"   ✅ Updated {header_results['summary']['updated']}/{header_results['summary']['total']} files")
        
        # Step 2: Validate syntax if requested
        if validate_syntax:
            print("\n🔍 Validating syntax...")
            all_source_files = mqh_files + mq5_files
            syntax_results = self.validate_syntax_batch(all_source_files)
            compilation_results["syntax_validation"] = syntax_results
            print(f"   ✅ Valid: {syntax_results['summary']['valid']}/{syntax_results['summary']['total']} files")
            
            if syntax_results['summary']['invalid'] > 0:
                print("   ⚠️  Files with syntax issues:")
                for file_path, result in syntax_results["files"].items():
                    if not result["valid"]:
                        file_name = Path(file_path).name
                        print(f"      • {file_name}: {', '.join(result['issues'][:3])}")  # Show first 3 issues
        
        # Step 3: Compile .mqh files if requested
        if compile_mqh and mqh_files:
            print("\n🔨 Compiling .mqh files...")
            
            # Sort by dependencies if requested
            if dependency_order:
                mqh_files = self.dependency_resolver.sort_by_dependencies(mqh_files)
                print("   📊 Files sorted by dependency order")
            
            mqh_compilation = self.compiler.compile_batch(mqh_files, stop_on_error)
            compilation_results["mqh_compilation"] = mqh_compilation
            
            print(f"   📊 MQH Results: {mqh_compilation['summary']['successful']}/{mqh_compilation['summary']['total']} successful")
        
        # Step 4: Compile .mq5 files if requested
        if compile_mq5 and mq5_files:
            print("\n🔨 Compiling .mq5 files...")
            
            mq5_compilation = self.compiler.compile_batch(mq5_files, stop_on_error)
            compilation_results["mq5_compilation"] = mq5_compilation
            
            print(f"   📊 MQ5 Results: {mq5_compilation['summary']['successful']}/{mq5_compilation['summary']['total']} successful")
        
        # Step 5: Generate comprehensive report
        self._generate_compilation_report(compilation_results)
        
        # Save detailed results
        report_path = self._save_compilation_results(compilation_results)
        compilation_results["report_path"] = str(report_path)
        
        # Print final summary
        self._print_final_summary(compilation_results)
        
        return compilation_results
    
    def _generate_compilation_report(self, results: Dict[str, Any]):
        """Generate human-readable compilation report"""
        print(f"\n" + "=" * 80)
        print("📊 COMPILATION SUMMARY REPORT")
        print("=" * 80)
        
        # Header updates
        if "header_updates" in results:
            header_summary = results["header_updates"]["summary"]
            print(f"\n📝 Header Updates:")
            print(f"   Updated: {header_summary['updated']}/{header_summary['total']} files")
        
        # Syntax validation
        if "syntax_validation" in results:
            syntax_summary = results["syntax_validation"]["summary"]
            print(f"\n🔍 Syntax Validation:")
            print(f"   Valid: {syntax_summary['valid']}/{syntax_summary['total']} files")
            if syntax_summary['invalid'] > 0:
                print(f"   Issues: {syntax_summary['invalid']} files need attention")
        
        # MQH compilation
        if "mqh_compilation" in results:
            mqh_summary = results["mqh_compilation"]["summary"]
            print(f"\n🔨 MQH Compilation:")
            print(f"   Successful: {mqh_summary['successful']}/{mqh_summary['total']} files")
            print(f"   Success Rate: {mqh_summary['success_rate']:.1%}")
            print(f"   Total Time: {mqh_summary['total_time']:.2f}s")
        
        # MQ5 compilation
        if "mq5_compilation" in results:
            mq5_summary = results["mq5_compilation"]["summary"]
            print(f"\n🔨 MQ5 Compilation:")
            print(f"   Successful: {mq5_summary['successful']}/{mq5_summary['total']} files")
            print(f"   Success Rate: {mq5_summary['success_rate']:.1%}")
            print(f"   Total Time: {mq5_summary['total_time']:.2f}s")
        
        # Overall assessment
        overall_success = True
        
        if "syntax_validation" in results and results["syntax_validation"]["summary"]["invalid"] > 0:
            overall_success = False
        
        if "mqh_compilation" in results and results["mqh_compilation"]["summary"]["success_rate"] < 0.9:
            overall_success = False
        
        if "mq5_compilation" in results and results["mq5_compilation"]["summary"]["success_rate"] < 0.9:
            overall_success = False
        
        print(f"\n🎯 OVERALL STATUS: {'✅ SUCCESS' if overall_success else '⚠️  NEEDS ATTENTION'}")
    
    def _save_compilation_results(self, results: Dict[str, Any]) -> Path:
        """Save detailed compilation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.logs_dir / f"compilation_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return report_path
    
    def _print_final_summary(self, results: Dict[str, Any]):
        """Print final summary"""
        print(f"\n💾 Detailed report saved: {results.get('report_path', 'Not saved')}")
        
        # Quick stats
        total_files = results["discovered_files"]["mqh_count"] + results["discovered_files"]["mq5_count"]
        print(f"\n📈 Quick Stats:")
        print(f"   Total files processed: {total_files}")
        
        if "mqh_compilation" in results:
            mqh_success_rate = results["mqh_compilation"]["summary"]["success_rate"]
            print(f"   MQH compilation success: {mqh_success_rate:.1%}")
        
        if "mq5_compilation" in results:
            mq5_success_rate = results["mq5_compilation"]["summary"]["success_rate"]
            print(f"   MQ5 compilation success: {mq5_success_rate:.1%}")


def main():
    """Main entry point for the compiler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ProjectQuantum Unified MQL5 Compiler')
    parser.add_argument('--mqh-only', action='store_true', help='Compile only .mqh files')
    parser.add_argument('--mq5-only', action='store_true', help='Compile only .mq5 files')
    parser.add_argument('--no-headers', action='store_true', help='Skip header updates')
    parser.add_argument('--no-syntax', action='store_true', help='Skip syntax validation')
    parser.add_argument('--no-dependencies', action='store_true', help='Skip dependency ordering')
    parser.add_argument('--stop-on-error', action='store_true', help='Stop compilation on first error')
    
    args = parser.parse_args()
    
    compiler = UnifiedMQL5Compiler()
    
    # Determine compilation options
    compile_mqh = not args.mq5_only
    compile_mq5 = not args.mqh_only
    update_headers = not args.no_headers
    validate_syntax = not args.no_syntax
    dependency_order = not args.no_dependencies
    stop_on_error = args.stop_on_error
    
    # Run compilation
    results = compiler.compile_project(
        compile_mqh=compile_mqh,
        compile_mq5=compile_mq5,
        update_headers=update_headers,
        validate_syntax=validate_syntax,
        dependency_order=dependency_order,
        stop_on_error=stop_on_error
    )
    
    # Determine exit code
    success = True
    
    if "syntax_validation" in results:
        invalid_files = results["syntax_validation"]["summary"]["invalid"]
        if invalid_files > 0:
            success = False
    
    if "mqh_compilation" in results:
        mqh_success_rate = results["mqh_compilation"]["summary"]["success_rate"]
        if mqh_success_rate < 0.8:  # 80% threshold
            success = False
    
    if "mq5_compilation" in results:
        mq5_success_rate = results["mq5_compilation"]["summary"]["success_rate"]
        if mq5_success_rate < 0.8:  # 80% threshold
            success = False
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())