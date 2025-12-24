#!/usr/bin/env python3
"""
Comprehensive ProjectQuantum Code Reviewer
Uses intelligent agent to analyze all .mqh files and main EA files
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from smart_mql5_assistant import SmartMQL5Assistant

class ProjectQuantumReviewer:
    def __init__(self):
        self.assistant = SmartMQL5Assistant()
        self.project_root = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.include_dir = self.project_root / "Include/ProjectQuantum"
        self.scripts_dir = self.project_root / "Scripts/ProjectQuantum"
        
        self.review_results = {
            'include_files': {},
            'ea_files': {},
            'dependencies': {},
            'issues': [],
            'statistics': {}
        }
    
    def review_all_includes(self):
        """Review all .mqh include files"""
        print("🔍 Reviewing all ProjectQuantum .mqh files...")
        
        include_files = list(self.include_dir.rglob("*.mqh"))
        
        for file_path in include_files:
            relative_path = file_path.relative_to(self.include_dir)
            print(f"Analyzing: {relative_path}")
            
            try:
                analysis = self._analyze_mqh_file(file_path)
                self.review_results['include_files'][str(relative_path)] = analysis
            except Exception as e:
                print(f"⚠️  Error analyzing {relative_path}: {e}")
                self.review_results['issues'].append({
                    'file': str(relative_path),
                    'type': 'analysis_error',
                    'message': str(e)
                })
        
        print(f"✅ Reviewed {len(include_files)} include files")
    
    def review_main_ea_files(self):
        """Review main EA files"""
        print("\n🔍 Reviewing main EA files...")
        
        # Look for main EA files
        ea_patterns = ["**/Main/*", "**/*Main*", "**/*EA*", "**/ProjectQuantum_Main*"]
        ea_files = []
        
        for pattern in ea_patterns:
            ea_files.extend(self.project_root.rglob(pattern))
        
        # Also check Scripts directory
        script_files = list(self.scripts_dir.rglob("*.mq5"))
        ea_files.extend([f for f in script_files if 'Test_' not in f.name])
        
        # Remove duplicates
        ea_files = list(set(ea_files))
        
        for file_path in ea_files:
            if file_path.suffix in ['.mq5', '.mq4', '.mqh']:
                print(f"Analyzing EA: {file_path.name}")
                
                try:
                    analysis = self._analyze_ea_file(file_path)
                    self.review_results['ea_files'][file_path.name] = analysis
                except Exception as e:
                    print(f"⚠️  Error analyzing {file_path.name}: {e}")
        
        print(f"✅ Reviewed {len(ea_files)} EA files")
    
    def _analyze_mqh_file(self, file_path: Path) -> Dict:
        """Analyze a single .mqh include file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Use intelligent agent analysis
        smart_analysis = self.assistant.analyze_code_snippet(content, str(file_path))
        
        # Additional structural analysis
        analysis = {
            'file_size': len(content),
            'line_count': len(content.split('\n')),
            'has_strict_mode': '#property strict' in content,
            'has_version': '#property version' in content,
            'has_copyright': '#property copyright' in content or '//|' in content,
            'include_count': len(re.findall(r'#include\s+["\<]', content)),
            'class_count': len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE)),
            'function_count': len(re.findall(r'^\s*\w+\s+\w+\s*\([^)]*\)\s*{', content, re.MULTILINE)),
            'enum_count': len(re.findall(r'^\s*enum\s+', content, re.MULTILINE)),
            'struct_count': len(re.findall(r'^\s*struct\s+', content, re.MULTILINE)),
            'smart_analysis': smart_analysis,
            'complexity_score': self._calculate_complexity(content)
        }
        
        # Extract dependencies
        includes = re.findall(r'#include\s+["\<]([^">\s]+)[">]', content)
        analysis['dependencies'] = includes
        
        # Check for common patterns
        analysis['has_singleton_pattern'] = 'static ' in content and 'GetInstance' in content
        analysis['has_error_handling'] = 'try' in content or 'catch' in content or 'GetLastError' in content
        analysis['has_logging'] = 'Print(' in content or 'LOG_' in content or 'CLogger' in content
        analysis['has_comments'] = content.count('//') > 10 or content.count('/*') > 2
        
        return analysis
    
    def _analyze_ea_file(self, file_path: Path) -> Dict:
        """Analyze a main EA file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        analysis = {
            'file_size': len(content),
            'line_count': len(content.split('\n')),
            'has_strict_mode': '#property strict' in content,
            'has_version': '#property version' in content,
            'has_ontick': 'void OnTick()' in content,
            'has_oninit': 'int OnInit()' in content or 'void OnInit()' in content,
            'has_ondeinit': 'void OnDeinit(' in content,
            'has_onstart': 'void OnStart()' in content,
            'is_script': '#property script' in content or 'void OnStart()' in content,
            'is_indicator': '#property indicator' in content,
            'is_expert': not ('#property script' in content) and not ('#property indicator' in content),
            'include_count': len(re.findall(r'#include\s+["\<]', content)),
            'input_parameters': len(re.findall(r'^\s*input\s+', content, re.MULTILINE)),
            'global_variables': len(re.findall(r'^\s*\w+\s+g_\w+', content, re.MULTILINE)),
        }
        
        # Extract includes
        includes = re.findall(r'#include\s+["\<]([^">\s]+)[">]', content)
        analysis['dependencies'] = includes
        
        # Check for trading functionality
        trading_functions = ['OrderSend', 'PositionOpen', 'Trade.', 'CTrade']
        analysis['has_trading'] = any(func in content for func in trading_functions)
        
        # Check for ProjectQuantum integration
        pq_patterns = ['ProjectQuantum', 'CQuantum', 'CRL_Agent', 'CLogger', 'CRiskManager']
        analysis['uses_project_quantum'] = any(pattern in content for pattern in pq_patterns)
        
        return analysis
    
    def _calculate_complexity(self, content: str) -> int:
        """Calculate rough complexity score based on various factors"""
        score = 0
        
        # Base complexity from control structures
        score += content.count('if(') * 1
        score += content.count('for(') * 2
        score += content.count('while(') * 2
        score += content.count('switch(') * 3
        score += content.count('try') * 2
        
        # Function complexity
        functions = re.findall(r'^\s*\w+\s+\w+\s*\([^)]*\)\s*{', content, re.MULTILINE)
        score += len(functions) * 5
        
        # Class complexity
        classes = re.findall(r'^\s*class\s+\w+', content, re.MULTILINE)
        score += len(classes) * 10
        
        # Template/generic complexity
        score += content.count('<T>') * 15
        score += content.count('template') * 20
        
        return score
    
    def analyze_dependencies(self):
        """Analyze inter-file dependencies"""
        print("\n🔍 Analyzing project dependencies...")
        
        dependency_graph = {}
        circular_deps = []
        missing_includes = []
        
        # Build dependency graph
        all_files = {**self.review_results['include_files'], **self.review_results['ea_files']}
        
        for file_name, analysis in all_files.items():
            deps = analysis.get('dependencies', [])
            dependency_graph[file_name] = deps
            
            # Check for missing includes
            for dep in deps:
                dep_path = self._resolve_include_path(dep)
                if not dep_path.exists():
                    missing_includes.append({
                        'file': file_name,
                        'missing_include': dep,
                        'resolved_path': str(dep_path)
                    })
        
        # Simple circular dependency detection
        for file_name, deps in dependency_graph.items():
            for dep in deps:
                if dep in dependency_graph and file_name in dependency_graph[dep]:
                    circular_deps.append((file_name, dep))
        
        self.review_results['dependencies'] = {
            'dependency_graph': dependency_graph,
            'circular_dependencies': circular_deps,
            'missing_includes': missing_includes
        }
        
        print(f"Found {len(circular_deps)} circular dependencies")
        print(f"Found {len(missing_includes)} missing includes")
    
    def _resolve_include_path(self, include: str) -> Path:
        """Resolve include path to actual file location"""
        if include.startswith('ProjectQuantum/'):
            return self.include_dir / include.replace('ProjectQuantum/', '')
        elif include.startswith('../../Include/ProjectQuantum/'):
            return self.include_dir / include.replace('../../Include/ProjectQuantum/', '')
        else:
            # Try various locations
            possible_paths = [
                self.include_dir / include,
                self.project_root / "Include" / include,
                Path(include)  # Absolute path
            ]
            
            for path in possible_paths:
                if path.exists():
                    return path
            
            return self.include_dir / include  # Default fallback
    
    def generate_statistics(self):
        """Generate comprehensive statistics"""
        print("\n📊 Generating project statistics...")
        
        stats = {
            'file_counts': {
                'include_files': len(self.review_results['include_files']),
                'ea_files': len(self.review_results['ea_files']),
                'total_files': len(self.review_results['include_files']) + len(self.review_results['ea_files'])
            },
            'code_metrics': {
                'total_lines': 0,
                'total_classes': 0,
                'total_functions': 0,
                'total_includes': 0,
                'avg_complexity': 0
            },
            'quality_metrics': {
                'files_with_strict_mode': 0,
                'files_with_version': 0,
                'files_with_copyright': 0,
                'files_with_error_handling': 0,
                'files_with_logging': 0
            },
            'category_breakdown': {
                'Core': 0,
                'Intelligence': 0,
                'Physics': 0,
                'Risk': 0,
                'Performance': 0,
                'Safety': 0,
                'Architecture': 0,
                'Monitoring': 0
            }
        }
        
        complexities = []
        
        # Aggregate metrics from include files
        for file_path, analysis in self.review_results['include_files'].items():
            stats['code_metrics']['total_lines'] += analysis.get('line_count', 0)
            stats['code_metrics']['total_classes'] += analysis.get('class_count', 0)
            stats['code_metrics']['total_functions'] += analysis.get('function_count', 0)
            stats['code_metrics']['total_includes'] += analysis.get('include_count', 0)
            
            complexity = analysis.get('complexity_score', 0)
            complexities.append(complexity)
            
            # Quality metrics
            if analysis.get('has_strict_mode'): stats['quality_metrics']['files_with_strict_mode'] += 1
            if analysis.get('has_version'): stats['quality_metrics']['files_with_version'] += 1
            if analysis.get('has_copyright'): stats['quality_metrics']['files_with_copyright'] += 1
            if analysis.get('has_error_handling'): stats['quality_metrics']['files_with_error_handling'] += 1
            if analysis.get('has_logging'): stats['quality_metrics']['files_with_logging'] += 1
            
            # Category breakdown
            for category in stats['category_breakdown']:
                if category in file_path:
                    stats['category_breakdown'][category] += 1
                    break
        
        # Calculate averages
        if complexities:
            stats['code_metrics']['avg_complexity'] = sum(complexities) / len(complexities)
        
        self.review_results['statistics'] = stats
    
    def generate_report(self) -> str:
        """Generate comprehensive review report"""
        stats = self.review_results['statistics']
        deps = self.review_results['dependencies']
        
        report = [
            "🚀 ProjectQuantum Comprehensive Code Review Report",
            "=" * 80,
            ""
        ]
        
        # Overview
        report.extend([
            "📊 PROJECT OVERVIEW:",
            f"   Total Files: {stats['file_counts']['total_files']}",
            f"   Include Files (.mqh): {stats['file_counts']['include_files']}",
            f"   EA/Script Files: {stats['file_counts']['ea_files']}",
            f"   Total Lines of Code: {stats['code_metrics']['total_lines']:,}",
            ""
        ])
        
        # Code Metrics
        report.extend([
            "📈 CODE METRICS:",
            f"   Classes: {stats['code_metrics']['total_classes']}",
            f"   Functions: {stats['code_metrics']['total_functions']}",
            f"   Include Statements: {stats['code_metrics']['total_includes']}",
            f"   Average Complexity Score: {stats['code_metrics']['avg_complexity']:.1f}",
            ""
        ])
        
        # Quality Assessment
        total_files = stats['file_counts']['total_files']
        report.extend([
            "✅ QUALITY ASSESSMENT:",
            f"   Strict Mode Compliance: {stats['quality_metrics']['files_with_strict_mode']}/{total_files} ({stats['quality_metrics']['files_with_strict_mode']/total_files*100:.1f}%)",
            f"   Version Information: {stats['quality_metrics']['files_with_version']}/{total_files} ({stats['quality_metrics']['files_with_version']/total_files*100:.1f}%)",
            f"   Copyright Headers: {stats['quality_metrics']['files_with_copyright']}/{total_files} ({stats['quality_metrics']['files_with_copyright']/total_files*100:.1f}%)",
            f"   Error Handling: {stats['quality_metrics']['files_with_error_handling']}/{total_files} ({stats['quality_metrics']['files_with_error_handling']/total_files*100:.1f}%)",
            f"   Logging Integration: {stats['quality_metrics']['files_with_logging']}/{total_files} ({stats['quality_metrics']['files_with_logging']/total_files*100:.1f}%)",
            ""
        ])
        
        # Category Breakdown
        report.extend([
            "🏗️  ARCHITECTURE BREAKDOWN:"
        ])
        for category, count in stats['category_breakdown'].items():
            if count > 0:
                report.append(f"   {category}: {count} files")
        report.append("")
        
        # Dependencies
        if deps.get('circular_dependencies'):
            report.extend([
                "⚠️  CIRCULAR DEPENDENCIES DETECTED:",
            ])
            for dep1, dep2 in deps['circular_dependencies']:
                report.append(f"   {dep1} ↔ {dep2}")
            report.append("")
        
        if deps.get('missing_includes'):
            report.extend([
                "❌ MISSING INCLUDES:",
            ])
            for missing in deps['missing_includes'][:10]:  # Show first 10
                report.append(f"   {missing['file']}: missing {missing['missing_include']}")
            if len(deps['missing_includes']) > 10:
                report.append(f"   ... and {len(deps['missing_includes']) - 10} more")
            report.append("")
        
        # Top Complex Files
        complex_files = []
        for file_path, analysis in self.review_results['include_files'].items():
            complexity = analysis.get('complexity_score', 0)
            complex_files.append((file_path, complexity))
        
        complex_files.sort(key=lambda x: x[1], reverse=True)
        
        if complex_files:
            report.extend([
                "🔥 MOST COMPLEX FILES:",
            ])
            for file_path, complexity in complex_files[:5]:
                report.append(f"   {file_path}: {complexity} complexity points")
            report.append("")
        
        # Issues Summary
        total_issues = len(self.review_results['issues'])
        for file_path, analysis in self.review_results['include_files'].items():
            total_issues += len(analysis.get('smart_analysis', {}).get('potential_issues', []))
        
        report.extend([
            "🎯 SUMMARY:",
            f"   Total Issues Found: {total_issues}",
            f"   Code Quality Score: {self._calculate_quality_score():.1f}/100",
            f"   Architecture Maturity: {self._assess_architecture_maturity()}",
            ""
        ])
        
        return "\n".join(report)
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall code quality score"""
        stats = self.review_results['statistics']
        total_files = stats['file_counts']['total_files']
        
        if total_files == 0:
            return 0.0
        
        # Quality factors (each worth up to 20 points)
        strict_mode_score = (stats['quality_metrics']['files_with_strict_mode'] / total_files) * 20
        version_score = (stats['quality_metrics']['files_with_version'] / total_files) * 20
        copyright_score = (stats['quality_metrics']['files_with_copyright'] / total_files) * 20
        error_handling_score = (stats['quality_metrics']['files_with_error_handling'] / total_files) * 20
        logging_score = (stats['quality_metrics']['files_with_logging'] / total_files) * 20
        
        total_score = strict_mode_score + version_score + copyright_score + error_handling_score + logging_score
        return min(100.0, total_score)
    
    def _assess_architecture_maturity(self) -> str:
        """Assess overall architecture maturity"""
        stats = self.review_results['statistics']
        quality_score = self._calculate_quality_score()
        
        if quality_score >= 90:
            return "Enterprise-Ready"
        elif quality_score >= 75:
            return "Production-Ready"
        elif quality_score >= 60:
            return "Development-Stable"
        elif quality_score >= 40:
            return "Alpha-Stage"
        else:
            return "Prototype-Stage"
    
    def close(self):
        """Clean up resources"""
        self.assistant.close()

def main():
    """Run comprehensive project review"""
    print("🚀 Starting Comprehensive ProjectQuantum Review...")
    
    reviewer = ProjectQuantumReviewer()
    
    try:
        # Perform comprehensive review
        reviewer.review_all_includes()
        reviewer.review_main_ea_files()
        reviewer.analyze_dependencies()
        reviewer.generate_statistics()
        
        # Generate and save report
        report = reviewer.generate_report()
        
        # Save report
        report_path = "/home/renier/ProjectQuantum-Full/comprehensive_project_review.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        # Display report
        print("\n" + report)
        print(f"\n📄 Full report saved: {report_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during review: {e}")
        return False
    finally:
        reviewer.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)