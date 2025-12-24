#!/usr/bin/env python3
"""
ProjectQuantum Unified Code Analyzer
Consolidated code analysis, auditing, and quality assessment functionality

Combines:
- comprehensive_code_audit.py
- mt5_structure_audit.py
- project_reviewer.py
- smart_mql5_assistant.py

Author: Renier De Jager
Version: 1.216
"""

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Any, Set


class FileStructureAnalyzer:
    """Analyzes file structure and organization"""
    
    def __init__(self, mt5_dev: Path):
        self.mt5_dev = mt5_dev
        self.standard_folders = {
            "Experts": "Expert Advisors (.mq5)",
            "Include": "Header files (.mqh)",
            "Indicators": "Custom indicators (.mq5)",  
            "Scripts": "Scripts (.mq5)",
            "Libraries": "Libraries (.mq5/.ex5)",
            "Files": "Data files",
            "Images": "Image resources"
        }
    
    def analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze ProjectQuantum file structure"""
        print("📁 Analyzing project structure...")
        
        structure = {
            "include_files": list((self.mt5_dev / "Include/ProjectQuantum").rglob("*.mqh")),
            "expert_files": list((self.mt5_dev / "Experts").rglob("*ProjectQuantum*.mq5")),
            "script_files": list((self.mt5_dev / "Scripts/ProjectQuantum").rglob("*.mq5")),
            "test_files": [f for f in (self.mt5_dev / "Scripts/ProjectQuantum").rglob("*.mq5") if "Test_" in f.name]
        }
        
        structure_analysis = {}
        
        for category, files in structure.items():
            print(f"   {category}: {len(files)} files")
            
            # Categorize by subdirectory
            subdirs = defaultdict(int)
            for file_path in files:
                try:
                    if "Include/ProjectQuantum" in str(file_path):
                        relative = file_path.relative_to(self.mt5_dev / "Include/ProjectQuantum")
                    else:
                        relative = file_path.relative_to(self.mt5_dev)
                    
                    if relative.parent != Path('.'):
                        subdirs[str(relative.parent)] += 1
                    else:
                        subdirs['root'] += 1
                except:
                    subdirs['unknown'] += 1
            
            structure_analysis[category] = {
                "total_files": len(files),
                "subdirectories": dict(subdirs),
                "files": [str(f) for f in files]
            }
        
        return structure_analysis
    
    def audit_mt5_directory(self, path: Path, name: str) -> Dict[str, Any]:
        """Audit a single MT5 directory"""
        print(f"🔍 Auditing MT5 directory: {name}")
        
        if not path.exists():
            print(f"   ❌ Directory not found")
            return {"exists": False, "issues": [f"{name}: Directory not found"]}
        
        audit_result = {
            "exists": True,
            "standard_folders": {},
            "unexpected_folders": [],
            "wrong_level_items": [],
            "issues": []
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
                print(f"   ✅ {folder}/ ({file_count} files)")
            else:
                audit_result["standard_folders"][folder] = {"exists": False}
        
        # Check for unexpected items
        for item in path.iterdir():
            if item.is_dir():
                folder_name = item.name
                if folder_name not in self.standard_folders:
                    audit_result["unexpected_folders"].append(folder_name)
                    
                    if "ProjectQuantum" in folder_name and folder_name != "ProjectQuantum":
                        issue = f"{name}: Duplicate ProjectQuantum folder - {folder_name}"
                        audit_result["issues"].append(issue)
                        print(f"   ⚠️  {issue}")
                    elif folder_name in ["Main", "Tests", "Documentation"]:
                        issue = f"{name}: Wrong level folder - {folder_name}"
                        audit_result["issues"].append(issue)
                        audit_result["wrong_level_items"].append(folder_name)
                        print(f"   ❌ {issue}")
            elif item.is_file():
                if item.suffix in [".mq5", ".mqh"]:
                    issue = f"{name}: File in wrong location - {item.name}"
                    audit_result["issues"].append(issue)
                    audit_result["wrong_level_items"].append(item.name)
                    print(f"   ❌ {issue}")
        
        return audit_result


class CodeQualityAnalyzer:
    """Analyzes code quality metrics"""
    
    def __init__(self):
        self.quality_thresholds = {
            "max_line_length": 120,
            "max_function_lines": 50,
            "min_comment_ratio": 0.15,
            "max_cyclomatic_complexity": 10
        }
    
    def analyze_file_quality(self, file_path: Path) -> Dict[str, Any]:
        """Analyze code quality of a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"error": f"Failed to read file: {e}"}
        
        lines = content.split('\n')
        
        analysis = {
            "file": str(file_path.name),
            "total_lines": len(lines),
            "code_lines": 0,
            "comment_lines": 0,
            "empty_lines": 0,
            "issues": [],
            "functions": [],
            "classes": [],
            "includes": [],
            "complexity_score": 0,
            "quality_metrics": {}
        }
        
        # Analyze each line
        function_lines = 0
        in_function = False
        brace_depth = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            original_line = line
            
            # Count line types
            if not stripped:
                analysis["empty_lines"] += 1
            elif stripped.startswith('//') or stripped.startswith('/*'):
                analysis["comment_lines"] += 1
            else:
                analysis["code_lines"] += 1
                
                # Count braces for complexity
                brace_depth += line.count('{') - line.count('}')
            
            # Find quality issues
            if len(original_line) > self.quality_thresholds["max_line_length"]:
                analysis["issues"].append(f"Line {i}: Line too long ({len(original_line)} chars)")
            
            if 'TODO' in line or 'FIXME' in line or 'HACK' in line:
                analysis["issues"].append(f"Line {i}: Contains TODO/FIXME/HACK")
            
            # Find functions
            func_match = re.match(r'\s*(\w+)\s+(\w+)\s*\([^)]*\)\s*{?', stripped)
            if func_match and not stripped.startswith('//'):
                return_type, func_name = func_match.groups()
                analysis["functions"].append({
                    "name": func_name,
                    "return_type": return_type,
                    "line": i
                })
                in_function = True
                function_lines = 0
            
            # Track function length
            if in_function:
                function_lines += 1
                if stripped == '}' and brace_depth == 0:
                    in_function = False
                    if function_lines > self.quality_thresholds["max_function_lines"]:
                        analysis["issues"].append(f"Line {i}: Function too long ({function_lines} lines)")
            
            # Find classes
            if stripped.startswith('class '):
                class_match = re.match(r'class\s+(\w+)', stripped)
                if class_match:
                    analysis["classes"].append(class_match.group(1))
            
            # Find includes
            if stripped.startswith('#include'):
                include_match = re.match(r'#include\s*[<"]([^>"]+)[>"]', stripped)
                if include_match:
                    analysis["includes"].append(include_match.group(1))
        
        # Calculate quality metrics
        total_non_empty = analysis["total_lines"] - analysis["empty_lines"]
        comment_ratio = analysis["comment_lines"] / max(total_non_empty, 1)
        
        analysis["quality_metrics"] = {
            "comment_ratio": comment_ratio,
            "code_to_comment_ratio": analysis["code_lines"] / max(analysis["comment_lines"], 1),
            "function_count": len(analysis["functions"]),
            "class_count": len(analysis["classes"]),
            "include_count": len(analysis["includes"]),
            "issues_count": len(analysis["issues"]),
            "quality_score": self._calculate_quality_score(analysis, comment_ratio)
        }
        
        return analysis
    
    def _calculate_quality_score(self, analysis: Dict[str, Any], comment_ratio: float) -> float:
        """Calculate overall quality score (0-100)"""
        score = 100.0
        
        # Deduct for issues
        score -= len(analysis["issues"]) * 2
        
        # Deduct for poor comment ratio
        if comment_ratio < self.quality_thresholds["min_comment_ratio"]:
            score -= 20
        
        # Deduct for excessive complexity
        if len(analysis["functions"]) > 20:
            score -= 10
        
        # Bonus for good structure
        if analysis["class_count"] > 0:
            score += 5
        
        if len(analysis["includes"]) > 0:
            score += 5
        
        return max(0.0, min(100.0, score))
    
    def analyze_batch_quality(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze quality of multiple files"""
        print("🔍 Analyzing code quality...")
        
        all_results = []
        quality_summary = {
            "total_files": len(files),
            "total_lines": 0,
            "total_code_lines": 0,
            "total_comment_lines": 0,
            "total_issues": 0,
            "average_quality_score": 0.0,
            "files_with_issues": 0,
            "distribution": {
                "excellent": 0,    # 90-100
                "good": 0,         # 70-89
                "fair": 0,         # 50-69
                "poor": 0          # 0-49
            }
        }
        
        for file_path in files:
            result = self.analyze_file_quality(file_path)
            if "error" not in result:
                all_results.append(result)
                
                # Update summary
                quality_summary["total_lines"] += result["total_lines"]
                quality_summary["total_code_lines"] += result["code_lines"]
                quality_summary["total_comment_lines"] += result["comment_lines"]
                quality_summary["total_issues"] += len(result["issues"])
                
                if len(result["issues"]) > 0:
                    quality_summary["files_with_issues"] += 1
                
                # Quality distribution
                quality_score = result["quality_metrics"]["quality_score"]
                if quality_score >= 90:
                    quality_summary["distribution"]["excellent"] += 1
                elif quality_score >= 70:
                    quality_summary["distribution"]["good"] += 1
                elif quality_score >= 50:
                    quality_summary["distribution"]["fair"] += 1
                else:
                    quality_summary["distribution"]["poor"] += 1
        
        # Calculate averages
        if all_results:
            quality_summary["average_quality_score"] = sum(
                r["quality_metrics"]["quality_score"] for r in all_results
            ) / len(all_results)
        
        return {
            "summary": quality_summary,
            "file_results": all_results
        }


class DependencyAnalyzer:
    """Analyzes file dependencies and relationships"""
    
    def __init__(self, mt5_dev: Path):
        self.mt5_dev = mt5_dev
        self.dependency_graph = {}
        self.circular_dependencies = []
    
    def analyze_dependencies(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze dependencies between files"""
        print("🔗 Analyzing file dependencies...")
        
        # Build dependency graph
        for file_path in files:
            self.dependency_graph[str(file_path)] = self._extract_dependencies(file_path)
        
        # Detect circular dependencies
        self._detect_circular_dependencies()
        
        # Calculate metrics
        dependency_metrics = self._calculate_dependency_metrics()
        
        return {
            "dependency_graph": self.dependency_graph,
            "circular_dependencies": self.circular_dependencies,
            "metrics": dependency_metrics
        }
    
    def _extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract include dependencies from a file"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find include statements
            include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
            includes = re.findall(include_pattern, content)
            
            for include_path in includes:
                # Resolve relative paths
                if include_path.startswith('../'):
                    resolved_path = (file_path.parent / include_path).resolve()
                    if resolved_path.exists():
                        dependencies.append(str(resolved_path))
                else:
                    # Look for file in include directories
                    potential_path = self.mt5_dev / "Include" / include_path
                    if potential_path.exists():
                        dependencies.append(str(potential_path))
                    else:
                        # Try ProjectQuantum subdirectory
                        potential_path = self.mt5_dev / "Include/ProjectQuantum" / include_path
                        if potential_path.exists():
                            dependencies.append(str(potential_path))
        
        except Exception as e:
            print(f"   ⚠️  Error reading dependencies from {file_path.name}: {e}")
        
        return dependencies
    
    def _detect_circular_dependencies(self):
        """Detect circular dependencies in the graph"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node, path):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                self.circular_dependencies.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                if has_cycle(neighbor, path):
                    return True
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        for node in self.dependency_graph:
            if node not in visited:
                has_cycle(node, [])
    
    def _calculate_dependency_metrics(self) -> Dict[str, Any]:
        """Calculate dependency-related metrics"""
        if not self.dependency_graph:
            return {}
        
        # Calculate in-degree and out-degree
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for node, dependencies in self.dependency_graph.items():
            out_degree[node] = len(dependencies)
            for dep in dependencies:
                in_degree[dep] += 1
        
        # Find highly coupled files
        max_in_degree = max(in_degree.values()) if in_degree else 0
        max_out_degree = max(out_degree.values()) if out_degree else 0
        
        highly_depended_files = [
            node for node, degree in in_degree.items() 
            if degree >= max_in_degree * 0.8 and degree > 3
        ]
        
        highly_dependent_files = [
            node for node, degree in out_degree.items() 
            if degree >= max_out_degree * 0.8 and degree > 5
        ]
        
        return {
            "total_files": len(self.dependency_graph),
            "total_dependencies": sum(len(deps) for deps in self.dependency_graph.values()),
            "circular_dependency_count": len(self.circular_dependencies),
            "max_in_degree": max_in_degree,
            "max_out_degree": max_out_degree,
            "highly_depended_files": highly_depended_files,
            "highly_dependent_files": highly_dependent_files,
            "average_dependencies_per_file": sum(len(deps) for deps in self.dependency_graph.values()) / len(self.dependency_graph)
        }


class CompilationReadinessAnalyzer:
    """Analyzes compilation readiness and potential issues"""
    
    def __init__(self):
        self.mql5_keywords = {
            'types': ['int', 'double', 'string', 'bool', 'datetime', 'color', 'long', 'short', 'char', 'uchar'],
            'functions': ['Print', 'Alert', 'Comment', 'GetLastError', 'ArraySize', 'MathMax', 'MathMin'],
            'constants': ['NULL', 'EMPTY', 'PERIOD_M1', 'PERIOD_H1', 'PERIOD_D1'],
            'properties': ['#property strict', '#property version', '#property copyright']
        }
    
    def analyze_compilation_readiness(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze compilation readiness of files"""
        print("🔨 Analyzing compilation readiness...")
        
        results = {
            "total_files": len(files),
            "compilation_ready": 0,
            "has_syntax_issues": 0,
            "missing_properties": 0,
            "file_results": []
        }
        
        for file_path in files:
            file_result = self._analyze_single_file_readiness(file_path)
            results["file_results"].append(file_result)
            
            if file_result["compilation_ready"]:
                results["compilation_ready"] += 1
            if file_result["syntax_issues"]:
                results["has_syntax_issues"] += 1
            if file_result["missing_properties"]:
                results["missing_properties"] += 1
        
        results["readiness_percentage"] = (results["compilation_ready"] / len(files)) * 100 if files else 0
        
        return results
    
    def _analyze_single_file_readiness(self, file_path: Path) -> Dict[str, Any]:
        """Analyze compilation readiness of a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                "file": file_path.name,
                "compilation_ready": False,
                "error": str(e)
            }
        
        result = {
            "file": file_path.name,
            "compilation_ready": True,
            "syntax_issues": [],
            "missing_properties": [],
            "warnings": []
        }
        
        # Check for required properties (for .mq5 files)
        if file_path.suffix == '.mq5':
            required_properties = ['#property strict', '#property version']
            for prop in required_properties:
                if prop not in content:
                    result["missing_properties"].append(prop)
                    result["compilation_ready"] = False
        
        # Check for syntax issues
        lines = content.split('\n')
        open_braces = 0
        open_parens = 0
        
        for i, line in enumerate(lines, 1):
            # Count braces and parentheses
            open_braces += line.count('{') - line.count('}')
            open_parens += line.count('(') - line.count(')')
            
            # Check for common syntax errors
            stripped = line.strip()
            
            if stripped.endswith('{') and not stripped.startswith('//'):
                # Function or control structure
                if not re.match(r'.*\w+.*\{$', stripped) and 'if' not in stripped and 'for' not in stripped:
                    result["syntax_issues"].append(f"Line {i}: Possible malformed function/structure")
            
            # Check for C++ specific features not supported in MQL5
            if 'namespace ' in line:
                result["syntax_issues"].append(f"Line {i}: Namespaces not supported in MQL5")
                result["compilation_ready"] = False
            
            if 'template<' in line:
                result["syntax_issues"].append(f"Line {i}: Templates not supported in MQL5")
                result["compilation_ready"] = False
            
            if 'std::' in line:
                result["syntax_issues"].append(f"Line {i}: STL not available in MQL5")
                result["compilation_ready"] = False
        
        # Check final brace/parentheses balance
        if open_braces != 0:
            result["syntax_issues"].append(f"Unbalanced braces: {open_braces}")
            result["compilation_ready"] = False
        
        if open_parens != 0:
            result["syntax_issues"].append(f"Unbalanced parentheses: {open_parens}")
            result["compilation_ready"] = False
        
        # Check for include paths
        includes = re.findall(r'#include\s*[<"]([^>"]+)[>"]', content)
        for include in includes:
            if '../' in include and include.count('../') > 3:
                result["warnings"].append(f"Deep relative path in include: {include}")
        
        return result


class UnifiedCodeAnalyzer:
    """Main code analyzer combining all analysis components"""
    
    def __init__(self):
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        
        # Initialize analyzers
        self.structure_analyzer = FileStructureAnalyzer(self.mt5_dev)
        self.quality_analyzer = CodeQualityAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer(self.mt5_dev)
        self.compilation_analyzer = CompilationReadinessAnalyzer()
    
    def run_comprehensive_analysis(self, 
                                 analyze_structure: bool = True,
                                 analyze_quality: bool = True,
                                 analyze_dependencies: bool = True,
                                 analyze_compilation: bool = True,
                                 max_files: Optional[int] = None) -> Dict[str, Any]:
        """Run comprehensive code analysis"""
        
        print("🔍 ProjectQuantum Comprehensive Code Analysis")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Options: Structure={analyze_structure}, Quality={analyze_quality}")
        print(f"         Dependencies={analyze_dependencies}, Compilation={analyze_compilation}")
        if max_files:
            print(f"         Max Files: {max_files}")
        print()
        
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.216",
            "analysis_options": {
                "structure": analyze_structure,
                "quality": analyze_quality,
                "dependencies": analyze_dependencies,
                "compilation": analyze_compilation
            }
        }
        
        # Discover files
        print("📂 Discovering project files...")
        include_files = list((self.mt5_dev / "Include/ProjectQuantum").rglob("*.mqh"))
        script_files = list((self.mt5_dev / "Scripts/ProjectQuantum").rglob("*.mq5"))
        expert_files = list((self.mt5_dev / "Experts").rglob("*ProjectQuantum*.mq5"))
        
        all_files = include_files + script_files + expert_files
        
        if max_files:
            all_files = all_files[:max_files]
        
        print(f"   Found {len(include_files)} include files")
        print(f"   Found {len(script_files)} script files") 
        print(f"   Found {len(expert_files)} expert advisor files")
        print(f"   Total: {len(all_files)} files to analyze")
        
        # Component 1: Structure Analysis
        if analyze_structure:
            print("\n📁 Running structure analysis...")
            structure_results = self.structure_analyzer.analyze_project_structure()
            analysis_results["structure_analysis"] = structure_results
            print("   ✅ Structure analysis completed")
        
        # Component 2: Quality Analysis
        if analyze_quality:
            print("\n🎯 Running quality analysis...")
            quality_results = self.quality_analyzer.analyze_batch_quality(all_files)
            analysis_results["quality_analysis"] = quality_results
            
            avg_score = quality_results["summary"]["average_quality_score"]
            print(f"   ✅ Quality analysis completed (avg score: {avg_score:.1f}/100)")
        
        # Component 3: Dependency Analysis
        if analyze_dependencies:
            print("\n🔗 Running dependency analysis...")
            dependency_results = self.dependency_analyzer.analyze_dependencies(all_files)
            analysis_results["dependency_analysis"] = dependency_results
            
            circular_deps = len(dependency_results["circular_dependencies"])
            print(f"   ✅ Dependency analysis completed ({circular_deps} circular dependencies)")
        
        # Component 4: Compilation Analysis
        if analyze_compilation:
            print("\n🔨 Running compilation readiness analysis...")
            compilation_results = self.compilation_analyzer.analyze_compilation_readiness(all_files)
            analysis_results["compilation_analysis"] = compilation_results
            
            readiness = compilation_results["readiness_percentage"]
            print(f"   ✅ Compilation analysis completed ({readiness:.1f}% ready)")
        
        # Generate insights
        insights = self._generate_analysis_insights(analysis_results)
        analysis_results["insights"] = insights
        
        # Generate summary report
        self._generate_analysis_report(analysis_results)
        
        # Save detailed results
        report_path = self._save_analysis_results(analysis_results)
        analysis_results["report_path"] = str(report_path)
        
        return analysis_results
    
    def _generate_analysis_insights(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from analysis results"""
        insights = []
        
        # Structure insights
        if "structure_analysis" in results:
            structure = results["structure_analysis"]
            include_count = structure.get("include_files", {}).get("total_files", 0)
            test_count = structure.get("test_files", {}).get("total_files", 0)
            
            if include_count > 50:
                insights.append(f"Large codebase with {include_count} include files - consider modularization")
            
            if test_count == 0:
                insights.append("No test files found - critical for code quality assurance")
            elif test_count < include_count * 0.5:
                insights.append(f"Low test coverage: {test_count} tests for {include_count} includes")
        
        # Quality insights
        if "quality_analysis" in results:
            quality = results["quality_analysis"]["summary"]
            avg_score = quality.get("average_quality_score", 0)
            
            if avg_score >= 90:
                insights.append("Excellent code quality - well maintained codebase")
            elif avg_score >= 70:
                insights.append("Good code quality with room for improvement")
            elif avg_score >= 50:
                insights.append("Moderate code quality - focus on refactoring needed")
            else:
                insights.append("Poor code quality - significant improvements required")
            
            if quality.get("files_with_issues", 0) > quality.get("total_files", 1) * 0.5:
                insights.append("Over 50% of files have quality issues")
        
        # Dependency insights
        if "dependency_analysis" in results:
            deps = results["dependency_analysis"]
            circular_count = len(deps.get("circular_dependencies", []))
            
            if circular_count > 0:
                insights.append(f"Found {circular_count} circular dependencies - refactoring needed")
            
            metrics = deps.get("metrics", {})
            if metrics.get("average_dependencies_per_file", 0) > 10:
                insights.append("High coupling detected - consider dependency injection")
        
        # Compilation insights
        if "compilation_analysis" in results:
            comp = results["compilation_analysis"]
            readiness = comp.get("readiness_percentage", 0)
            
            if readiness >= 90:
                insights.append("Excellent compilation readiness")
            elif readiness >= 70:
                insights.append("Good compilation readiness - minor fixes needed")
            else:
                insights.append("Poor compilation readiness - major fixes required")
        
        return insights
    
    def _generate_analysis_report(self, results: Dict[str, Any]):
        """Generate human-readable analysis report"""
        print(f"\n" + "=" * 80)
        print("🎯 COMPREHENSIVE CODE ANALYSIS REPORT")
        print("=" * 80)
        
        # Structure summary
        if "structure_analysis" in results:
            print(f"\n📁 PROJECT STRUCTURE:")
            structure = results["structure_analysis"]
            for category, info in structure.items():
                total = info.get("total_files", 0)
                print(f"   {category.replace('_', ' ').title()}: {total} files")
        
        # Quality summary
        if "quality_analysis" in results:
            print(f"\n🎯 CODE QUALITY:")
            quality = results["quality_analysis"]["summary"]
            print(f"   Average Quality Score: {quality['average_quality_score']:.1f}/100")
            print(f"   Total Lines of Code: {quality['total_code_lines']:,}")
            print(f"   Files with Issues: {quality['files_with_issues']}/{quality['total_files']}")
            
            dist = quality["distribution"]
            print(f"   Quality Distribution:")
            print(f"     Excellent (90-100): {dist['excellent']} files")
            print(f"     Good (70-89): {dist['good']} files") 
            print(f"     Fair (50-69): {dist['fair']} files")
            print(f"     Poor (0-49): {dist['poor']} files")
        
        # Dependency summary
        if "dependency_analysis" in results:
            print(f"\n🔗 DEPENDENCIES:")
            deps = results["dependency_analysis"]
            metrics = deps.get("metrics", {})
            
            print(f"   Total Dependencies: {metrics.get('total_dependencies', 0)}")
            print(f"   Circular Dependencies: {len(deps.get('circular_dependencies', []))}")
            print(f"   Average Deps per File: {metrics.get('average_dependencies_per_file', 0):.1f}")
        
        # Compilation summary
        if "compilation_analysis" in results:
            print(f"\n🔨 COMPILATION READINESS:")
            comp = results["compilation_analysis"]
            print(f"   Ready to Compile: {comp['compilation_ready']}/{comp['total_files']} files")
            print(f"   Readiness Percentage: {comp['readiness_percentage']:.1f}%")
            print(f"   Files with Syntax Issues: {comp['has_syntax_issues']}")
            print(f"   Files Missing Properties: {comp['missing_properties']}")
        
        # Insights
        if "insights" in results:
            print(f"\n💡 KEY INSIGHTS ({len(results['insights'])}):")
            for i, insight in enumerate(results["insights"], 1):
                print(f"   {i}. {insight}")
        
        # Overall assessment
        self._print_overall_assessment(results)
    
    def _print_overall_assessment(self, results: Dict[str, Any]):
        """Print overall system health assessment"""
        print(f"\n🏥 OVERALL SYSTEM HEALTH:")
        
        health_score = 100.0
        
        # Quality impact
        if "quality_analysis" in results:
            quality_score = results["quality_analysis"]["summary"]["average_quality_score"]
            health_score = health_score * (quality_score / 100.0)
        
        # Compilation impact
        if "compilation_analysis" in results:
            comp_readiness = results["compilation_analysis"]["readiness_percentage"]
            health_score = health_score * (comp_readiness / 100.0)
        
        # Dependency impact
        if "dependency_analysis" in results:
            circular_deps = len(results["dependency_analysis"].get("circular_dependencies", []))
            if circular_deps > 0:
                health_score *= 0.8  # 20% penalty for circular dependencies
        
        if health_score >= 90:
            print(f"   🎉 EXCELLENT (Health Score: {health_score:.1f}/100)")
            print("   System is in excellent condition with high quality code")
        elif health_score >= 75:
            print(f"   ✅ GOOD (Health Score: {health_score:.1f}/100)")
            print("   System is in good condition with minor issues")
        elif health_score >= 60:
            print(f"   ⚠️  FAIR (Health Score: {health_score:.1f}/100)")
            print("   System needs attention - moderate issues detected")
        else:
            print(f"   ❌ POOR (Health Score: {health_score:.1f}/100)")
            print("   System requires immediate attention - critical issues detected")
    
    def _save_analysis_results(self, results: Dict[str, Any]) -> Path:
        """Save comprehensive analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure reports directory exists
        reports_dir = self.project_root / "analysis_reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_path = reports_dir / f"code_analysis_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return report_path


def main():
    """Main entry point for code analyzer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ProjectQuantum Comprehensive Code Analyzer')
    parser.add_argument('--no-structure', action='store_true', help='Skip structure analysis')
    parser.add_argument('--no-quality', action='store_true', help='Skip quality analysis')
    parser.add_argument('--no-dependencies', action='store_true', help='Skip dependency analysis')
    parser.add_argument('--no-compilation', action='store_true', help='Skip compilation analysis')
    parser.add_argument('--max-files', type=int, help='Maximum number of files to analyze')
    
    args = parser.parse_args()
    
    analyzer = UnifiedCodeAnalyzer()
    
    results = analyzer.run_comprehensive_analysis(
        analyze_structure=not args.no_structure,
        analyze_quality=not args.no_quality,
        analyze_dependencies=not args.no_dependencies,
        analyze_compilation=not args.no_compilation,
        max_files=args.max_files
    )
    
    # Determine success based on overall health
    success = True
    
    if "quality_analysis" in results:
        avg_quality = results["quality_analysis"]["summary"]["average_quality_score"]
        if avg_quality < 60:
            success = False
    
    if "compilation_analysis" in results:
        compilation_readiness = results["compilation_analysis"]["readiness_percentage"]
        if compilation_readiness < 70:
            success = False
    
    if "dependency_analysis" in results:
        circular_deps = len(results["dependency_analysis"].get("circular_dependencies", []))
        if circular_deps > 5:
            success = False
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())