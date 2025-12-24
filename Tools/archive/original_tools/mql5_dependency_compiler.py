#!/usr/bin/env python3
"""
MQL5 Dependency-Aware Compilation System
Compiles ProjectQuantum files in correct dependency order
"""

import os
import sys
import re
import subprocess
import json
from pathlib import Path
from datetime import datetime
import time

class MQL5DependencyCompiler:
    def __init__(self):
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.metaeditor = "/mnt/c/DevCenter/MT5-Unified/MT5-Core/Terminal/MetaEditor64.exe"
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        
        # Compilation order based on dependencies
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
            "Include/ProjectQuantum/Risk/CRiskManager.mqh",
            "Include/ProjectQuantum/Risk/CPortfolioRisk.mqh",
            "Include/ProjectQuantum/Risk/CAssetClassRisk.mqh",
            "Include/ProjectQuantum/Risk/CCompositeValidator.mqh",
            "Include/ProjectQuantum/Risk/CPositionSizer.mqh",
            "Include/ProjectQuantum/Risk/CThreeLevelRisk.mqh",
            
            "Include/ProjectQuantum/Physics/CMarketPhysics.mqh",
            "Include/ProjectQuantum/Physics/CPhysicsMonitor.mqh",
            "Include/ProjectQuantum/Physics/CMarketAgnostic.mqh",
            "Include/ProjectQuantum/Physics/CFractalAnalyzer.mqh",
            "Include/ProjectQuantum/Physics/CPortfolioPhysics.mqh",
            
            "Include/ProjectQuantum/Performance/CPerformanceMonitor.mqh",
            "Include/ProjectQuantum/Performance/CInstrumentProfiler.mqh",
            "Include/ProjectQuantum/Performance/CRegimeJudge.mqh",
            "Include/ProjectQuantum/Performance/CAdaptiveCycle.mqh",
            "Include/ProjectQuantum/Performance/CAgnosticClock.mqh",
            "Include/ProjectQuantum/Performance/CLearningMetrics.mqh",
            "Include/ProjectQuantum/Performance/CPositionRegistry.mqh",
            "Include/ProjectQuantum/Performance/CRiskIntelligence.mqh",
            
            "Include/ProjectQuantum/Intelligence/CRL_Agent.mqh",
            "Include/ProjectQuantum/Intelligence/CReplayBuffer.mqh",
            "Include/ProjectQuantum/Intelligence/CProbabilityPredictor.mqh",
            "Include/ProjectQuantum/Intelligence/CJourneyReward.mqh",
            "Include/ProjectQuantum/Intelligence/CMarketProbability.mqh",
            "Include/ProjectQuantum/Intelligence/CErrorLearningAgent.mqh",
            "Include/ProjectQuantum/Intelligence/CRLExitAgent.mqh",
            "Include/ProjectQuantum/Intelligence/CGenetics.mqh",
            "Include/ProjectQuantum/Intelligence/CRiskAdversary.mqh",
            "Include/ProjectQuantum/Intelligence/CShadowManager.mqh",
            
            "Include/ProjectQuantum/Safety/CCircuitBreaker.mqh",
            "Include/ProjectQuantum/Monitoring/CRealTimeLogMonitor.mqh",
            
            # Level 6: Architecture aggregation
            "Include/ProjectQuantum/Architecture/Project_Quantum.mqh",
            
            # Level 7: Master include
            "Include/ProjectQuantum.mqh",
            
            # Level 8: Test files
            "Scripts/ProjectQuantum/Test_SafeMath.mq5",
            "Scripts/ProjectQuantum/Test_ArrayUtils.mq5",
            "Scripts/ProjectQuantum/Test_SymbolUtils.mq5",
            "Scripts/ProjectQuantum/Test_Defensive.mq5",
            "Scripts/ProjectQuantum/Test_CPersistence.mq5",
            "Scripts/ProjectQuantum/Test_CRL_Agent.mq5",
            "Scripts/ProjectQuantum/Test_Security.mq5",
            "Scripts/ProjectQuantum/Test_ArchitecturalPrinciples.mq5",
            "Scripts/ProjectQuantum/Test_CRiskIntelligence.mq5",
            "Scripts/ProjectQuantum/Test_Lifecycle.mq5",
            "Scripts/ProjectQuantum/Test_CFractalAnalyzer.mq5",
            "Scripts/ProjectQuantum/Test_CLearningMetrics.mq5",
            
            # Level 9: Main files
            "Experts/ProjectQuantum/ProjectQuantum_UnitTests.mq5",
            "Experts/ProjectQuantum/ProjectQuantum_Main.mq5",
        ]
        
        self.compilation_results = {}
        self.error_patterns = {}
        
    def analyze_dependencies(self, filepath):
        """Analyze #include dependencies in a file"""
        dependencies = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find all #include statements
            include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
            matches = re.findall(include_pattern, content)
            
            for match in matches:
                dependencies.append(match)
                
        except Exception as e:
            print(f"❌ Failed to analyze {filepath}: {e}")
            
        return dependencies
    
    def compile_single_file(self, filepath):
        """Compile a single MQL5 file and return detailed results"""
        full_path = self.mt5_dev / filepath
        
        if not full_path.exists():
            return {
                "success": False,
                "errors": [f"File not found: {filepath}"],
                "warnings": [],
                "error_count": 1
            }
        
        # Create log file for this compilation
        log_file = self.project_root / f"compile_logs/{Path(filepath).stem}.log"
        log_file.parent.mkdir(exist_ok=True)
        
        print(f"   🔨 Compiling: {filepath}")
        
        # Run MetaEditor compilation
        cmd = [
            self.metaeditor,
            f"/compile:{full_path}",
            f"/log:{log_file}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            time.sleep(0.5)  # Give MetaEditor time to write log
            
            # Parse compilation log
            errors = []
            warnings = []
            
            if log_file.exists():
                try:
                    # Try UTF-16 first
                    with open(log_file, 'r', encoding='utf-16') as f:
                        log_content = f.read()
                except:
                    # Fallback to UTF-8
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                
                # Extract errors and warnings
                lines = log_content.split('\n')
                for line in lines:
                    if 'error' in line.lower() and 'errors' not in line.lower():
                        errors.append(line.strip())
                    elif 'warning' in line.lower() and 'warnings' not in line.lower():
                        warnings.append(line.strip())
                
                # Check for compilation success
                success = len(errors) == 0
                
                # For .mqh files, warnings are acceptable
                if filepath.endswith('.mqh') and len(errors) == 0:
                    success = True
                    
            else:
                errors = ["No log file generated"]
                success = False
                
            return {
                "success": success,
                "errors": errors,
                "warnings": warnings,
                "error_count": len(errors),
                "warning_count": len(warnings)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "errors": ["Compilation timeout"],
                "warnings": [],
                "error_count": 1
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [f"Compilation failed: {e}"],
                "warnings": [],
                "error_count": 1
            }
    
    def fix_common_errors(self, filepath, errors):
        """Attempt to fix common compilation errors"""
        fixes_applied = []
        
        # Common error patterns and fixes
        error_fixes = {
            "static const": self.fix_static_const,
            "GetPointer": self.fix_getpointer,
            "template": self.fix_templates,
            "pragma once": self.fix_pragma_once,
            "implicit conversion": self.fix_implicit_conversion
        }
        
        for error in errors:
            for pattern, fix_func in error_fixes.items():
                if pattern in error:
                    fix_result = fix_func(filepath, error)
                    if fix_result:
                        fixes_applied.append(fix_result)
                        
        return fixes_applied
    
    def fix_static_const(self, filepath, error):
        """Fix static const member initialization"""
        # Implementation would go here
        return None
        
    def fix_getpointer(self, filepath, error):
        """Fix GetPointer usage on structs"""
        # Implementation would go here
        return None
        
    def fix_templates(self, filepath, error):
        """Fix template syntax"""
        # Implementation would go here
        return None
        
    def fix_pragma_once(self, filepath, error):
        """Replace #pragma once with include guards"""
        # Implementation would go here
        return None
        
    def fix_implicit_conversion(self, filepath, error):
        """Add explicit type casts"""
        # Implementation would go here
        return None
    
    def compile_all(self):
        """Compile all files in dependency order"""
        print("🔧 ProjectQuantum Dependency-Aware Compilation")
        print("=" * 50)
        print(f"Files to compile: {len(self.compilation_order)}")
        print(f"MetaEditor: {self.metaeditor}")
        print()
        
        successful = 0
        failed = 0
        warnings_total = 0
        
        # Create results directory
        results_dir = self.project_root / "compilation_results"
        results_dir.mkdir(exist_ok=True)
        
        # Compile in order
        for i, filepath in enumerate(self.compilation_order, 1):
            print(f"\n[{i}/{len(self.compilation_order)}] {filepath}")
            
            result = self.compile_single_file(filepath)
            self.compilation_results[filepath] = result
            
            if result["success"]:
                successful += 1
                warnings_total += result["warning_count"]
                print(f"   ✅ Success ({result['warning_count']} warnings)")
            else:
                failed += 1
                print(f"   ❌ Failed ({result['error_count']} errors)")
                
                # Show first 3 errors
                for j, error in enumerate(result["errors"][:3]):
                    print(f"      • {error}")
                if len(result["errors"]) > 3:
                    print(f"      • ... and {len(result['errors']) - 3} more errors")
                
                # Stop if core file fails
                if "Core/" in filepath and i < 20:
                    print("\n⚠️  Core file failed - stopping to prevent cascade")
                    break
        
        # Generate report
        self.generate_report(successful, failed, warnings_total)
        
        # Generate CI workflow if all core files compile
        if failed == 0 or (failed > 0 and successful > 10):
            self.generate_ci_workflow()
            
        return failed == 0
    
    def generate_report(self, successful, failed, warnings_total):
        """Generate detailed compilation report"""
        report_file = self.project_root / "compilation_results/compilation_report.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(self.compilation_order),
            "successful": successful,
            "failed": failed,
            "warnings_total": warnings_total,
            "results": self.compilation_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📊 COMPILATION SUMMARY")
        print("=" * 30)
        print(f"Total files: {len(self.compilation_order)}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings_total}")
        
        if failed > 0:
            print(f"\n❌ Failed files:")
            for filepath, result in self.compilation_results.items():
                if not result["success"]:
                    print(f"   • {filepath} ({result['error_count']} errors)")
                    
        print(f"\n📄 Detailed report: {report_file}")
    
    def generate_ci_workflow(self):
        """Generate GitHub Actions CI workflow"""
        workflow = """name: MQL5 Compilation CI

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

jobs:
  compile:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup MT5
      run: |
        # Download and install MT5 if needed
        # This would need to be customized based on your CI environment
        
    - name: Compile Core Files
      run: |
        python mql5_dependency_compiler.py --core-only
        
    - name: Compile All Files
      if: success()
      run: |
        python mql5_dependency_compiler.py --all
        
    - name: Upload Compilation Report
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: compilation-report
        path: compilation_results/
        
    - name: Check Compilation Status
      run: |
        python -c "import json; r=json.load(open('compilation_results/compilation_report.json')); exit(0 if r['failed']==0 else 1)"
"""
        
        workflow_file = self.project_root / ".github/workflows/mql5_compile.yml"
        workflow_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(workflow_file, 'w') as f:
            f.write(workflow)
            
        print(f"\n🔧 Generated CI workflow: {workflow_file}")

if __name__ == "__main__":
    compiler = MQL5DependencyCompiler()
    success = compiler.compile_all()
    
    if success:
        print("\n🎉 All files compiled successfully!")
    else:
        print("\n❌ Compilation failed - review errors above")
        print("Fix the errors in order, starting with core files")
        sys.exit(1)