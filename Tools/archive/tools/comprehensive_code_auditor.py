#!/usr/bin/env python3
"""
Comprehensive ProjectQuantum Code Auditor
Eliminates duplicates, static values, incomplete functions, and performance bottlenecks
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from smart_mql5_assistant import SmartMQL5Assistant

class ComprehensiveCodeAuditor:
    def __init__(self):
        self.assistant = SmartMQL5Assistant()
        self.project_root = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.include_dir = self.project_root / "Include/ProjectQuantum"
        
        self.audit_results = {
            'duplicates': [],
            'incomplete_functions': [],
            'static_values': [],
            'performance_bottlenecks': [],
            'missing_validations': [],
            'non_dynamic_components': [],
            'synchronous_operations': []
        }
        
    def audit_entire_codebase(self):
        """Comprehensive audit of entire ProjectQuantum codebase"""
        print("🔍 Starting comprehensive ProjectQuantum code audit...")
        
        # Get all files
        mqh_files = list(self.include_dir.rglob("*.mqh"))
        
        for file_path in mqh_files:
            relative_path = file_path.relative_to(self.include_dir)
            print(f"Auditing: {relative_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Run comprehensive audits
                self._audit_duplicates(content, str(relative_path))
                self._audit_incomplete_functions(content, str(relative_path))
                self._audit_static_values(content, str(relative_path))
                self._audit_performance_bottlenecks(content, str(relative_path))
                self._audit_validations(content, str(relative_path))
                self._audit_dynamic_components(content, str(relative_path))
                self._audit_async_operations(content, str(relative_path))
                
            except Exception as e:
                print(f"⚠️  Error auditing {relative_path}: {e}")
        
        return self.audit_results
    
    def _audit_duplicates(self, content: str, file_path: str):
        """Find duplicate code blocks and functions"""
        # Extract function definitions
        functions = re.findall(r'(\w+\s+\w+\s*\([^)]*\)\s*{[^}]*})', content, re.DOTALL)
        
        # Simple duplicate detection (could be enhanced)
        seen_functions = {}
        for func in functions:
            # Normalize function for comparison
            normalized = re.sub(r'\s+', ' ', func).strip()
            signature = normalized.split('{')[0] if '{' in normalized else normalized
            
            if signature in seen_functions:
                self.audit_results['duplicates'].append({
                    'file': file_path,
                    'type': 'function_duplicate',
                    'signature': signature[:100],
                    'issue': 'Duplicate function definition detected'
                })
            else:
                seen_functions[signature] = True
        
        # Check for duplicate include statements
        includes = re.findall(r'#include\s+["\<]([^">\s]+)[">]', content)
        seen_includes = set()
        for include in includes:
            if include in seen_includes:
                self.audit_results['duplicates'].append({
                    'file': file_path,
                    'type': 'include_duplicate',
                    'include': include,
                    'issue': f'Duplicate include: {include}'
                })
            else:
                seen_includes.add(include)
    
    def _audit_incomplete_functions(self, content: str, file_path: str):
        """Find incomplete or TODO functions"""
        # Look for functions with TODO, FIXME, or empty implementations
        todo_patterns = [
            r'//\s*TODO',
            r'//\s*FIXME', 
            r'//\s*HACK',
            r'//\s*NOTE:.*implement',
            r'throw\s+new\s+NotImplementedException',
            r'return\s+false;\s*//.*implement',
            r'{\s*//.*implement.*}',
            r'{\s*return\s+0;\s*}',
            r'{\s*}\s*//.*empty'
        ]
        
        for pattern in todo_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.audit_results['incomplete_functions'].append({
                    'file': file_path,
                    'line': line_num,
                    'pattern': pattern,
                    'issue': f'Incomplete implementation detected: {match.group(0)}'
                })
        
        # Check for functions with minimal implementation
        func_pattern = r'(\w+\s+\w+\s*\([^)]*\)\s*{\s*([^}]*)\s*})'
        functions = re.finditer(func_pattern, content, re.DOTALL)
        
        for match in functions:
            func_body = match.group(2).strip()
            if len(func_body) < 10 and 'return' in func_body:  # Suspiciously short
                line_num = content[:match.start()].count('\n') + 1
                self.audit_results['incomplete_functions'].append({
                    'file': file_path,
                    'line': line_num,
                    'function': match.group(1)[:50],
                    'issue': 'Suspiciously minimal function implementation'
                })
    
    def _audit_static_values(self, content: str, file_path: str):
        """Find hardcoded static values that should be dynamic"""
        static_patterns = [
            # Magic numbers that should be configurable
            (r'\b(100|50|30|20|10|5)\b(?!\s*[;}])', 'magic_number'),
            (r'0\.0[1-9]\d*', 'hardcoded_decimal'),
            (r'"[^"]{10,}"', 'hardcoded_string'),
            # Static array sizes
            (r'new\s+\w+\[\s*\d+\s*\]', 'static_array_size'),
            # Fixed timeframes
            (r'PERIOD_\w+(?!\s*=\s*input)', 'hardcoded_timeframe'),
            # Fixed symbols
            (r'"EUR[A-Z]{3}"|"GBP[A-Z]{3}"|"USD[A-Z]{3}"', 'hardcoded_symbol'),
        ]
        
        for pattern, issue_type in static_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.audit_results['static_values'].append({
                    'file': file_path,
                    'line': line_num,
                    'type': issue_type,
                    'value': match.group(0),
                    'issue': f'Static value should be dynamic: {match.group(0)}'
                })
    
    def _audit_performance_bottlenecks(self, content: str, file_path: str):
        """Identify performance bottlenecks"""
        bottleneck_patterns = [
            # Inefficient loops
            (r'for\s*\([^)]*ArraySize\([^)]+\)[^)]*\)', 'array_size_in_loop'),
            # String concatenation in loops
            (r'for\s*\([^{]*\{[^}]*\+\s*=\s*[^}]*}', 'string_concat_in_loop'),
            # Inefficient algorithms
            (r'for\s*\([^{]*\{[^}]*for\s*\([^{]*\{[^}]*for\s*\(', 'triple_nested_loop'),
            # Memory allocations in hot paths
            (r'new\s+\w+\[.*\](?=.*OnTick)', 'allocation_in_ontick'),
            # Synchronous file operations
            (r'FileOpen\(.*\)(?=.*OnTick)', 'file_io_in_ontick'),
            # Database operations in main thread
            (r'SELECT\s+.*FROM(?=.*OnTick)', 'db_query_in_ontick'),
        ]
        
        for pattern, issue_type in bottleneck_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.audit_results['performance_bottlenecks'].append({
                    'file': file_path,
                    'line': line_num,
                    'type': issue_type,
                    'code': match.group(0)[:100],
                    'issue': f'Performance bottleneck: {issue_type}'
                })
    
    def _audit_validations(self, content: str, file_path: str):
        """Check for missing input validations"""
        # Find public methods without validation
        public_methods = re.finditer(r'public:\s*\n\s*(\w+\s+\w+\s*\([^)]*\))', content, re.MULTILINE)
        
        for match in public_methods:
            method_start = match.end()
            # Look for method body
            body_match = re.search(r'\s*{([^}]*)}', content[method_start:], re.DOTALL)
            if body_match:
                method_body = body_match.group(1)
                
                # Check for common validation patterns
                has_validation = any(pattern in method_body for pattern in [
                    'if(', 'Validate', 'Check', 'IsValid', 'NULL', '<=', '>='
                ])
                
                if not has_validation and len(method_body.strip()) > 10:
                    line_num = content[:match.start()].count('\n') + 1
                    self.audit_results['missing_validations'].append({
                        'file': file_path,
                        'line': line_num,
                        'method': match.group(1)[:50],
                        'issue': 'Public method lacks input validation'
                    })
    
    def _audit_dynamic_components(self, content: str, file_path: str):
        """Check for components that should be dynamic but aren't"""
        # Look for hardcoded configurations
        non_dynamic_patterns = [
            (r'const\s+\w+\s+\w+\s*=\s*\d+', 'const_should_be_configurable'),
            (r'#define\s+\w+\s+\d+', 'define_should_be_dynamic'),
            (r'static\s+\w+\s+\w+\s*=', 'static_should_be_instance'),
        ]
        
        for pattern, issue_type in non_dynamic_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Skip if it's clearly meant to be constant
                if any(keyword in match.group(0).upper() for keyword in ['VERSION', 'COPYRIGHT', 'MAGIC']):
                    continue
                    
                line_num = content[:match.start()].count('\n') + 1
                self.audit_results['non_dynamic_components'].append({
                    'file': file_path,
                    'line': line_num,
                    'type': issue_type,
                    'declaration': match.group(0),
                    'issue': f'Should be dynamic: {issue_type}'
                })
    
    def _audit_async_operations(self, content: str, file_path: str):
        """Check for synchronous operations that should be async"""
        sync_patterns = [
            (r'Sleep\(\d+\)', 'blocking_sleep'),
            (r'while\s*\([^)]*\)\s*{[^}]*}', 'blocking_while_loop'),
            (r'FileRead\([^)]*\)(?!.*async)', 'sync_file_read'),
            (r'WebRequest\([^)]*\)(?!.*async)', 'sync_web_request'),
        ]
        
        for pattern, issue_type in sync_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.audit_results['synchronous_operations'].append({
                    'file': file_path,
                    'line': line_num,
                    'type': issue_type,
                    'code': match.group(0)[:50],
                    'issue': f'Synchronous operation should be async: {issue_type}'
                })
    
    def generate_enhancement_plan(self):
        """Generate comprehensive enhancement plan"""
        total_issues = sum(len(issues) for issues in self.audit_results.values())
        
        plan = {
            'priority_fixes': [],
            'performance_improvements': [],
            'architecture_enhancements': [],
            'dynamic_upgrades': []
        }
        
        # Categorize fixes by priority
        for bottleneck in self.audit_results['performance_bottlenecks']:
            plan['priority_fixes'].append({
                'type': 'performance',
                'file': bottleneck['file'],
                'issue': bottleneck['issue'],
                'priority': 'critical'
            })
        
        for duplicate in self.audit_results['duplicates']:
            plan['priority_fixes'].append({
                'type': 'duplicate',
                'file': duplicate['file'],
                'issue': duplicate['issue'],
                'priority': 'high'
            })
        
        for incomplete in self.audit_results['incomplete_functions']:
            plan['priority_fixes'].append({
                'type': 'incomplete',
                'file': incomplete['file'],
                'issue': incomplete['issue'],
                'priority': 'high'
            })
        
        for static_val in self.audit_results['static_values']:
            plan['dynamic_upgrades'].append({
                'type': 'static_to_dynamic',
                'file': static_val['file'],
                'value': static_val['value'],
                'suggestion': self._suggest_dynamic_replacement(static_val)
            })
        
        return plan, total_issues
    
    def _suggest_dynamic_replacement(self, static_issue):
        """Suggest dynamic replacement for static values"""
        suggestions = {
            'magic_number': 'Convert to input parameter or configuration setting',
            'hardcoded_decimal': 'Use calculated value based on volatility or market conditions',
            'hardcoded_string': 'Load from configuration file or user input',
            'static_array_size': 'Use dynamic array with ArrayResize()',
            'hardcoded_timeframe': 'Use input parameter for timeframe selection',
            'hardcoded_symbol': 'Use current symbol or symbol selection parameter'
        }
        
        return suggestions.get(static_issue['type'], 'Make configurable or calculate dynamically')
    
    def close(self):
        """Clean up resources"""
        self.assistant.close()

def main():
    """Run comprehensive code audit"""
    print("🔍 Starting Comprehensive ProjectQuantum Code Audit...")
    
    auditor = ComprehensiveCodeAuditor()
    
    try:
        # Run comprehensive audit
        audit_results = auditor.audit_entire_codebase()
        
        # Generate enhancement plan
        enhancement_plan, total_issues = auditor.generate_enhancement_plan()
        
        # Summary statistics
        print(f"\n📊 AUDIT SUMMARY:")
        print(f"   Total Issues Found: {total_issues}")
        print(f"   Duplicates: {len(audit_results['duplicates'])}")
        print(f"   Incomplete Functions: {len(audit_results['incomplete_functions'])}")
        print(f"   Static Values: {len(audit_results['static_values'])}")
        print(f"   Performance Bottlenecks: {len(audit_results['performance_bottlenecks'])}")
        print(f"   Missing Validations: {len(audit_results['missing_validations'])}")
        print(f"   Non-Dynamic Components: {len(audit_results['non_dynamic_components'])}")
        print(f"   Synchronous Operations: {len(audit_results['synchronous_operations'])}")
        
        # Save detailed results
        import json
        results_path = "/home/renier/ProjectQuantum-Full/comprehensive_audit_results.json"
        with open(results_path, 'w') as f:
            json.dump({
                'audit_results': audit_results,
                'enhancement_plan': enhancement_plan,
                'total_issues': total_issues
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved: {results_path}")
        
        return total_issues < 50  # Success if manageable number of issues
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        auditor.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)