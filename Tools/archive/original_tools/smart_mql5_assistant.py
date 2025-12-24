#!/usr/bin/env python3
"""
Smart MQL5 Code Assistant
Uses persistent knowledge database to provide intelligent code suggestions and error fixes
"""

import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class SmartMQL5Assistant:
    def __init__(self, knowledge_db_path: str = "/home/renier/ProjectQuantum-Full/mql5_knowledge.db"):
        self.db_path = knowledge_db_path
        self.conn = sqlite3.connect(knowledge_db_path)
        self.cursor = self.conn.cursor()
    
    def analyze_code_snippet(self, code: str, file_context: str = "") -> Dict:
        """Analyze code snippet and provide intelligent suggestions"""
        print(f"🔍 Analyzing code snippet...")
        
        suggestions = {
            'function_calls': [],
            'potential_issues': [],
            'improvements': [],
            'correct_usage': []
        }
        
        # Find function calls in the code
        function_pattern = r'([A-Za-z_][A-Za-z0-9_]*)\s*\('
        for match in re.finditer(function_pattern, code):
            func_name = match.group(1)
            line_start = code.rfind('\n', 0, match.start()) + 1
            line_end = code.find('\n', match.end())
            if line_end == -1:
                line_end = len(code)
            line_content = code[line_start:line_end].strip()
            
            # Get function signature and usage info
            usage_info = self.get_intelligent_function_info(func_name)
            if usage_info:
                suggestions['function_calls'].append({
                    'function': func_name,
                    'line': line_content,
                    'usage_info': usage_info,
                    'position': match.start()
                })
        
        # Check for common MQL5 issues
        suggestions['potential_issues'].extend(self._check_common_issues(code))
        
        # Check for correct includes
        suggestions['improvements'].extend(self._suggest_includes(code))
        
        return suggestions
    
    def get_intelligent_function_info(self, function_name: str) -> Optional[Dict]:
        """Get comprehensive function information from knowledge database"""
        
        # Check built-in functions
        self.cursor.execute("""
            SELECT signature, return_type, parameters, description, category 
            FROM mql5_builtin_functions 
            WHERE function_name = ?
        """, (function_name,))
        
        builtin_result = self.cursor.fetchone()
        if builtin_result:
            return {
                'type': 'builtin',
                'signature': builtin_result[0],
                'return_type': builtin_result[1],
                'parameters': builtin_result[2],
                'description': builtin_result[3],
                'category': builtin_result[4],
                'examples': self._get_usage_examples(function_name)
            }
        
        # Check project functions
        self.cursor.execute("""
            SELECT signature, return_type, file_path, is_public, is_static, class_name
            FROM project_functions 
            WHERE function_name = ? 
            ORDER BY last_modified DESC LIMIT 3
        """, (function_name,))
        
        project_results = self.cursor.fetchall()
        if project_results:
            return {
                'type': 'project',
                'definitions': [{
                    'signature': result[0],
                    'return_type': result[1],
                    'file_path': result[2],
                    'is_public': result[3],
                    'is_static': result[4],
                    'class_name': result[5]
                } for result in project_results],
                'examples': self._get_usage_examples(function_name)
            }
        
        return None
    
    def _get_usage_examples(self, function_name: str) -> List[Dict]:
        """Get usage examples from compilation history"""
        self.cursor.execute("""
            SELECT parameters_used, context, fixed_code
            FROM function_calls fc
            LEFT JOIN compilation_fixes cf ON fc.called_function LIKE '%' || ? || '%'
            WHERE fc.called_function = ? AND fc.is_correct = 1
            LIMIT 3
        """, (function_name, function_name))
        
        examples = self.cursor.fetchall()
        return [{'params': ex[0], 'context': ex[1], 'fix': ex[2]} for ex in examples]
    
    def _check_common_issues(self, code: str) -> List[Dict]:
        """Check for common MQL5 coding issues"""
        issues = []
        
        # Check for GetPointer on structs
        if 'GetPointer(' in code and 'struct' in code:
            issues.append({
                'type': 'GetPointer on struct',
                'severity': 'high',
                'message': 'GetPointer only works with classes, not structs',
                'fix': 'Change struct to class or remove GetPointer usage'
            })
        
        # Check for static const in classes
        if re.search(r'class.*{.*static\s+const', code, re.DOTALL):
            issues.append({
                'type': 'static const in class',
                'severity': 'high', 
                'message': 'MQL5 strict mode does not support static const initialization in classes',
                'fix': 'Use getter methods instead of static const'
            })
        
        # Check for missing #property strict
        if 'class ' in code and '#property strict' not in code:
            issues.append({
                'type': 'missing strict mode',
                'severity': 'medium',
                'message': 'Consider adding #property strict for better error checking',
                'fix': 'Add #property strict at the top of the file'
            })
        
        # Check for C++ template usage
        if re.search(r'<[A-Za-z_][A-Za-z0-9_]*>', code):
            issues.append({
                'type': 'C++ templates',
                'severity': 'high',
                'message': 'MQL5 does not support C++ templates',
                'fix': 'Remove template syntax and use specific types'
            })
        
        # Check for deprecated IsFinite
        if 'IsFinite(' in code:
            issues.append({
                'type': 'deprecated function',
                'severity': 'medium',
                'message': 'IsFinite is deprecated, use MathIsValidNumber instead',
                'fix': 'Replace IsFinite with MathIsValidNumber'
            })
        
        return issues
    
    def _suggest_includes(self, code: str) -> List[Dict]:
        """Suggest appropriate #include statements based on code analysis"""
        suggestions = []
        
        # Analyze function usage to suggest includes
        if 'CTestFramework' in code:
            suggestions.append({
                'type': 'include suggestion',
                'include': '#include "../../Include/ProjectQuantum/Core/TestFramework.mqh"',
                'reason': 'CTestFramework usage detected'
            })
        
        if any(func in code for func in ['CLogger', 'LOG_INFO', 'LOG_ERROR']):
            suggestions.append({
                'type': 'include suggestion', 
                'include': '#include "../../Include/ProjectQuantum/Core/CLogger.mqh"',
                'reason': 'Logging functionality detected'
            })
        
        if 'CryptEncode' in code:
            suggestions.append({
                'type': 'function signature reminder',
                'function': 'CryptEncode',
                'correct_signature': 'CryptEncode(ENUM_CRYPT_METHOD method, const uchar& data[], const uchar& key[], uchar& result[])',
                'reason': 'CryptEncode requires 4 parameters'
            })
        
        return suggestions
    
    def suggest_code_fix(self, error_message: str, problematic_code: str) -> Optional[Dict]:
        """Suggest code fixes based on compilation errors"""
        
        # Look for similar errors in knowledge base
        self.cursor.execute("""
            SELECT original_code, fixed_code, error_type
            FROM compilation_fixes 
            WHERE error_message LIKE ? OR error_type LIKE ?
            ORDER BY fix_applied_at DESC LIMIT 3
        """, (f'%{error_message}%', f'%{error_message}%'))
        
        similar_fixes = self.cursor.fetchall()
        
        if similar_fixes:
            return {
                'suggested_fixes': [{
                    'original': fix[0],
                    'fixed': fix[1],
                    'error_type': fix[2]
                } for fix in similar_fixes],
                'confidence': 'high' if len(similar_fixes) >= 2 else 'medium'
            }
        
        # Pattern-based suggestions for common errors
        if 'class type expected' in error_message:
            return {
                'suggested_fixes': [{
                    'issue': 'GetPointer used on struct',
                    'solution': 'Change struct to class or remove GetPointer',
                    'example': 'class MyClass { ... }; MyClass obj; MyClass* ptr = GetPointer(obj);'
                }],
                'confidence': 'high'
            }
        
        if 'illegal assignment use' in error_message:
            return {
                'suggested_fixes': [{
                    'issue': 'static const initialization in class',
                    'solution': 'Use getter method instead',
                    'example': 'int GetMaxSize() { return 100; } // instead of static const int MAX_SIZE = 100;'
                }],
                'confidence': 'high'
            }
        
        return None
    
    def learn_from_compilation(self, file_path: str, errors: List[str], fixed_code: str):
        """Learn from compilation errors and fixes"""
        for error in errors:
            # Extract error type
            error_type = 'unknown'
            if 'class type expected' in error:
                error_type = 'GetPointer struct issue'
            elif 'illegal assignment' in error:
                error_type = 'static const issue'
            elif 'undeclared identifier' in error:
                error_type = 'missing include'
            
            # Store the fix
            self.cursor.execute("""
                INSERT INTO compilation_fixes 
                (error_type, error_message, fixed_code, file_path)
                VALUES (?, ?, ?, ?)
            """, (error_type, error, fixed_code, file_path))
        
        self.conn.commit()
        print(f"📚 Learned from {len(errors)} compilation errors")
    
    def generate_smart_suggestions_report(self, code: str) -> str:
        """Generate comprehensive smart suggestions report"""
        analysis = self.analyze_code_snippet(code)
        
        report = ["🤖 Smart MQL5 Code Analysis Report", "=" * 80, ""]
        
        # Function calls analysis
        if analysis['function_calls']:
            report.append("🔧 Function Calls Analysis:")
            for func_call in analysis['function_calls']:
                func_info = func_call['usage_info']
                report.append(f"   📞 {func_call['function']}()")
                if func_info['type'] == 'builtin':
                    report.append(f"      Built-in {func_info['category']}: {func_info['signature']}")
                    report.append(f"      Description: {func_info['description']}")
                else:
                    report.append(f"      Project function with {len(func_info['definitions'])} definitions")
                    for defn in func_info['definitions'][:1]:  # Show first definition
                        report.append(f"      Signature: {defn['signature']}")
                        report.append(f"      File: {defn['file_path']}")
                report.append("")
        
        # Issues found
        if analysis['potential_issues']:
            report.append("⚠️  Potential Issues:")
            for issue in analysis['potential_issues']:
                report.append(f"   🔴 {issue['type']} ({issue['severity']})")
                report.append(f"      {issue['message']}")
                report.append(f"      Fix: {issue['fix']}")
                report.append("")
        
        # Improvements
        if analysis['improvements']:
            report.append("💡 Suggested Improvements:")
            for imp in analysis['improvements']:
                report.append(f"   ✨ {imp['type']}")
                if 'include' in imp:
                    report.append(f"      Add: {imp['include']}")
                if 'correct_signature' in imp:
                    report.append(f"      Correct: {imp['correct_signature']}")
                report.append(f"      Reason: {imp['reason']}")
                report.append("")
        
        if not any([analysis['function_calls'], analysis['potential_issues'], analysis['improvements']]):
            report.append("✅ No issues detected in code snippet!")
        
        return "\n".join(report)
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    """Demo the smart assistant capabilities"""
    print("🤖 Smart MQL5 Assistant Demo")
    print("=" * 50)
    
    assistant = SmartMQL5Assistant()
    
    # Example problematic code
    test_code = '''
#property strict

struct TestStruct {
    int value;
};

class TestClass {
    static const int MAX_SIZE = 100;  // Issue!
    
public:
    void DoSomething() {
        TestStruct s;
        TestStruct* ptr = GetPointer(s);  // Issue!
        
        StringFormat("Test %d", 123);
        ArrayResize(buffer, 100);
        IsFinite(3.14);  // Deprecated
    }
};
'''
    
    try:
        # Generate analysis report
        report = assistant.generate_smart_suggestions_report(test_code)
        print(report)
        
        # Demo function lookup
        print("\n" + "="*50)
        print("📖 Function Information Lookup:")
        func_info = assistant.get_intelligent_function_info("StringFormat")
        if func_info:
            print(f"StringFormat: {func_info['signature']}")
            print(f"Description: {func_info['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        assistant.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)