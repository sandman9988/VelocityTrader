#!/usr/bin/env python3
"""
ProjectQuantum Dependency Fixer
Uses intelligent agent to fix missing include dependencies
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set
from smart_mql5_assistant import SmartMQL5Assistant

class DependencyFixer:
    def __init__(self):
        self.assistant = SmartMQL5Assistant()
        self.project_root = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.include_dir = self.project_root / "Include/ProjectQuantum"
        self.fixes_applied = 0
        
    def analyze_missing_dependencies(self):
        """Analyze all files for missing dependencies"""
        print("🔍 Analyzing missing dependencies...")
        
        dependency_issues = {}
        
        # Get all .mqh files
        mqh_files = list(self.include_dir.rglob("*.mqh"))
        
        for file_path in mqh_files:
            relative_path = file_path.relative_to(self.include_dir)
            print(f"Checking: {relative_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                missing_includes = self._find_missing_includes(content, file_path)
                if missing_includes:
                    dependency_issues[str(relative_path)] = missing_includes
                    
            except Exception as e:
                print(f"⚠️  Error analyzing {relative_path}: {e}")
        
        return dependency_issues
    
    def _find_missing_includes(self, content: str, file_path: Path) -> List[Dict]:
        """Find missing include dependencies in a file"""
        missing = []
        
        # Extract current includes
        current_includes = set(re.findall(r'#include\s+["\<]([^">\s]+)[">]', content))
        
        # Check for missing dependencies based on usage patterns
        dependency_patterns = {
            # Core dependencies
            'SafeMath': ['SafeAdd', 'SafeMultiply', 'SafeDivide', 'IsValidPrice'],
            'ArrayUtils': ['ArrayUtils::', 'Mean(', 'Median(', 'Variance('],
            'CLogger': ['CLogger::', 'LOG_INFO', 'LOG_ERROR', 'LOG_DEBUG'],
            'CPersistence': ['CPersistence', 'SaveState', 'LoadState'],
            'CSystemOptimizer': ['CSystemOptimizer', 'OptimizeSystem'],
            'SymbolUtils': ['SymbolUtils::', 'GetPointValue', 'GetMinLot'],
            'Defensive': ['ValidateInput', 'CheckBounds', 'IsValidSymbol'],
            
            # Intelligence dependencies  
            'CRL_Agent': ['CRL_Agent', 'SelectAction', 'UpdateQ'],
            'CReplayBuffer': ['CReplayBuffer', 'AddExperience', 'Sample'],
            'CShadowManager': ['CShadowManager', 'GetBestShadow'],
            
            # Risk dependencies
            'CRiskManager': ['CRiskManager', 'CalculatePosition', 'CheckRisk'],
            'CCircuitBreaker': ['CCircuitBreaker', 'IsLocked', 'TriggerBreaker'],
            
            # Physics dependencies
            'CMarketPhysics': ['CMarketPhysics', 'CalculateForce', 'GetMomentum'],
            'CFractalAnalyzer': ['CFractalAnalyzer', 'CalculateDimension'],
            
            # Performance dependencies
            'CPerformanceMonitor': ['CPerformanceMonitor', 'UpdateMetrics'],
            'CLearningMetrics': ['CLearningMetrics', 'RecordReward'],
        }
        
        # Check each pattern
        for include_file, patterns in dependency_patterns.items():
            # Skip if already included
            include_variants = [
                include_file + '.mqh',
                f'Core/{include_file}.mqh',
                f'Intelligence/{include_file}.mqh',
                f'Risk/{include_file}.mqh',
                f'Physics/{include_file}.mqh',
                f'Performance/{include_file}.mqh'
            ]
            
            if any(variant in current_includes for variant in include_variants):
                continue
                
            # Check if any patterns are used
            for pattern in patterns:
                if pattern in content:
                    # Determine correct include path
                    correct_path = self._determine_include_path(include_file)
                    missing.append({
                        'file': include_file,
                        'path': correct_path,
                        'reason': f'Uses {pattern}',
                        'pattern': pattern
                    })
                    break
        
        return missing
    
    def _determine_include_path(self, include_file: str) -> str:
        """Determine the correct include path for a file"""
        # Map files to their correct directories
        file_locations = {
            # Core files
            'SafeMath': 'Core/SafeMath.mqh',
            'ArrayUtils': 'Core/ArrayUtils.mqh', 
            'CLogger': 'Core/CLogger.mqh',
            'CPersistence': 'Core/CPersistence.mqh',
            'CSystemOptimizer': 'Core/CSystemOptimizer.mqh',
            'SymbolUtils': 'Core/SymbolUtils.mqh',
            'Defensive': 'Core/Defensive.mqh',
            'Core': 'Core/Core.mqh',
            
            # Intelligence files
            'CRL_Agent': 'Intelligence/CRL_Agent.mqh',
            'CReplayBuffer': 'Intelligence/CReplayBuffer.mqh',
            'CShadowManager': 'Intelligence/CShadowManager.mqh',
            'CProbabilityPredictor': 'Intelligence/CProbabilityPredictor.mqh',
            'CMarketProbability': 'Intelligence/CMarketProbability.mqh',
            
            # Risk files
            'CRiskManager': 'Risk/CRiskManager.mqh',
            'CCircuitBreaker': 'Safety/CCircuitBreaker.mqh',
            'CPositionSizer': 'Risk/CPositionSizer.mqh',
            
            # Physics files
            'CMarketPhysics': 'Physics/CMarketPhysics.mqh',
            'CFractalAnalyzer': 'Physics/CFractalAnalyzer.mqh',
            'CMarketAgnostic': 'Physics/CMarketAgnostic.mqh',
            
            # Performance files
            'CPerformanceMonitor': 'Performance/CPerformanceMonitor.mqh',
            'CLearningMetrics': 'Performance/CLearningMetrics.mqh',
            'CInstrumentProfiler': 'Performance/CInstrumentProfiler.mqh',
        }
        
        return file_locations.get(include_file, f'Core/{include_file}.mqh')
    
    def fix_dependencies(self, dependency_issues: Dict) -> int:
        """Fix missing dependencies in files"""
        print(f"\n🔧 Fixing dependencies in {len(dependency_issues)} files...")
        
        fixes_count = 0
        
        for file_path, missing_deps in dependency_issues.items():
            if not missing_deps:
                continue
                
            print(f"Fixing: {file_path}")
            full_path = self.include_dir / file_path
            
            try:
                # Read current content
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add missing includes
                new_includes = []
                for dep in missing_deps:
                    include_line = f'#include "{dep["path"]}"'
                    if include_line not in content:
                        new_includes.append(include_line)
                        print(f"  + Adding: {dep['path']} (reason: {dep['reason']})")
                
                if new_includes:
                    # Find insertion point (after existing includes)
                    include_pattern = r'(#include\s+["\<][^">\s]+[">]\s*\n)*'
                    match = re.search(include_pattern, content)
                    
                    if match:
                        insertion_point = match.end()
                    else:
                        # Insert after property declarations
                        property_match = re.search(r'(#property\s+[^\n]+\s*\n)*', content)
                        insertion_point = property_match.end() if property_match else 0
                    
                    # Insert new includes
                    new_include_block = '\n'.join(new_includes) + '\n'
                    updated_content = (content[:insertion_point] + 
                                     new_include_block + 
                                     content[insertion_point:])
                    
                    # Write updated content
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    fixes_count += len(new_includes)
                    print(f"  ✅ Added {len(new_includes)} includes")
                
            except Exception as e:
                print(f"  ❌ Error fixing {file_path}: {e}")
        
        return fixes_count
    
    def validate_fixes(self, dependency_issues: Dict) -> Dict:
        """Validate that fixes were applied correctly"""
        print(f"\n✅ Validating fixes...")
        
        validation_results = {
            'fixed_files': 0,
            'remaining_issues': {},
            'new_issues': []
        }
        
        for file_path in dependency_issues.keys():
            full_path = self.include_dir / file_path
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Re-analyze for missing dependencies
                remaining = self._find_missing_includes(content, full_path)
                
                if not remaining:
                    validation_results['fixed_files'] += 1
                    print(f"  ✅ {file_path}: All dependencies resolved")
                else:
                    validation_results['remaining_issues'][file_path] = remaining
                    print(f"  ⚠️  {file_path}: {len(remaining)} issues remain")
                    
            except Exception as e:
                validation_results['new_issues'].append(f"{file_path}: {e}")
                print(f"  ❌ {file_path}: Validation error - {e}")
        
        return validation_results
    
    def generate_fix_report(self, initial_issues: Dict, validation: Dict) -> str:
        """Generate comprehensive fix report"""
        report = [
            "🔧 ProjectQuantum Dependency Fix Report",
            "=" * 60,
            ""
        ]
        
        # Summary
        initial_count = sum(len(issues) for issues in initial_issues.values())
        remaining_count = sum(len(issues) for issues in validation['remaining_issues'].values())
        fixed_count = initial_count - remaining_count
        
        report.extend([
            "📊 SUMMARY:",
            f"   Initial Issues: {initial_count}",
            f"   Fixed: {fixed_count}",
            f"   Remaining: {remaining_count}",
            f"   Success Rate: {(fixed_count/initial_count*100):.1f}%" if initial_count > 0 else "   Success Rate: 100%",
            f"   Files Fixed: {validation['fixed_files']}/{len(initial_issues)}",
            ""
        ])
        
        # Fixed files
        if validation['fixed_files'] > 0:
            report.extend([
                f"✅ SUCCESSFULLY FIXED ({validation['fixed_files']} files):",
            ])
            for file_path in initial_issues.keys():
                if file_path not in validation['remaining_issues']:
                    report.append(f"   • {file_path}")
            report.append("")
        
        # Remaining issues
        if validation['remaining_issues']:
            report.extend([
                f"⚠️  REMAINING ISSUES ({len(validation['remaining_issues'])} files):",
            ])
            for file_path, issues in validation['remaining_issues'].items():
                report.append(f"   • {file_path}: {len(issues)} dependencies")
                for issue in issues[:3]:  # Show first 3
                    report.append(f"     - {issue['path']} ({issue['reason']})")
            report.append("")
        
        # New issues
        if validation['new_issues']:
            report.extend([
                "❌ NEW ISSUES:",
            ])
            for issue in validation['new_issues']:
                report.append(f"   • {issue}")
            report.append("")
        
        return "\n".join(report)
    
    def close(self):
        """Clean up resources"""
        self.assistant.close()

def main():
    """Run dependency fixing process"""
    print("🔧 Starting ProjectQuantum Dependency Fixer...")
    
    fixer = DependencyFixer()
    
    try:
        # Analyze missing dependencies
        dependency_issues = fixer.analyze_missing_dependencies()
        
        if not dependency_issues:
            print("✅ No missing dependencies found!")
            return True
        
        print(f"\nFound missing dependencies in {len(dependency_issues)} files")
        
        # Fix dependencies
        fixes_applied = fixer.fix_dependencies(dependency_issues)
        print(f"\n✅ Applied {fixes_applied} dependency fixes")
        
        # Validate fixes
        validation = fixer.validate_fixes(dependency_issues)
        
        # Generate report
        report = fixer.generate_fix_report(dependency_issues, validation)
        
        # Save report
        report_path = "/home/renier/ProjectQuantum-Full/dependency_fix_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        # Display report
        print("\n" + report)
        print(f"📄 Full report saved: {report_path}")
        
        return validation['fixed_files'] > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        fixer.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)