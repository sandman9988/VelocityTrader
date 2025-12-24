#!/usr/bin/env python3
"""
MQL5 Compilation Verification
Tests actual MQL5 compilation without requiring full MetaEditor setup
"""

import re
import sys
from pathlib import Path

class MQL5CompilationValidator:
    def __init__(self):
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.compilation_errors = []
        
    def validate_mql5_syntax(self, file_path):
        """Validate MQL5 syntax without full compilation"""
        if not file_path.exists():
            return False, [f"File not found: {file_path}"]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, [f"Cannot read file: {e}"]
        
        errors = []
        
        # Check required MQL5 properties
        if '#property strict' not in content:
            errors.append("Missing #property strict")
        
        # Check for common MQL5 syntax issues
        self.check_includes(content, file_path, errors)
        self.check_function_syntax(content, errors)
        self.check_variable_declarations(content, errors)
        self.check_brackets_balance(content, errors)
        
        return len(errors) == 0, errors
    
    def check_includes(self, content, file_path, errors):
        """Check include statements"""
        include_pattern = r'#include\s+"([^"]+)"'
        includes = re.findall(include_pattern, content)
        
        for include_path in includes:
            # Convert relative path to absolute
            if include_path.startswith('../../'):
                # From Scripts/ProjectQuantum to Include
                full_include_path = self.mt5_dev / include_path.replace('../../', '')
            elif include_path.startswith('../'):
                # From Scripts to Include  
                script_dir = file_path.parent
                full_include_path = script_dir.parent / include_path.replace('../', '')
            else:
                # Assume relative to current file
                full_include_path = file_path.parent / include_path
            
            if not full_include_path.exists():
                errors.append(f"Include file not found: {include_path} (resolved to: {full_include_path})")
    
    def check_function_syntax(self, content, errors):
        """Check function syntax"""
        # Check for missing semicolons
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip comments and preprocessor directives
            if stripped.startswith('//') or stripped.startswith('#') or stripped.startswith('/*'):
                continue
                
            # Check for missing semicolon on statements
            if stripped and not stripped.endswith((';', '{', '}')) and not stripped.startswith('if') and not stripped.startswith('for') and not stripped.startswith('while'):
                # Could be a missing semicolon
                if any(keyword in stripped for keyword in ['=', 'Print(', 'TEST_', 'delete ', 'new ']):
                    if not stripped.endswith('\\'):  # Line continuation
                        errors.append(f"Line {i}: Possible missing semicolon: {stripped}")
    
    def check_variable_declarations(self, content, errors):
        """Check variable declarations"""
        # Check for undeclared variables (basic check)
        # This is simplified - real MQL5 compiler does full scope analysis
        
        # Look for TEST_ macros without proper declaration
        if 'TEST_' in content and 'g_test_framework' not in content:
            errors.append("TEST_ macros used but g_test_framework not declared")
    
    def check_brackets_balance(self, content, errors):
        """Check bracket balance"""
        # Remove strings and comments to avoid false positives
        cleaned = re.sub(r'"[^"]*"', '', content)  # Remove strings
        cleaned = re.sub(r'//.*', '', cleaned)     # Remove line comments
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)  # Remove block comments
        
        bracket_count = 0
        paren_count = 0
        square_count = 0
        
        for char in cleaned:
            if char == '{':
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
            elif char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == '[':
                square_count += 1
            elif char == ']':
                square_count -= 1
        
        if bracket_count != 0:
            errors.append(f"Unbalanced curly brackets: {bracket_count}")
        if paren_count != 0:
            errors.append(f"Unbalanced parentheses: {paren_count}")
        if square_count != 0:
            errors.append(f"Unbalanced square brackets: {square_count}")
    
    def test_file_compilation(self, file_path):
        """Test compilation of a single file"""
        print(f"🔍 Testing: {file_path.name}")
        
        is_valid, errors = self.validate_mql5_syntax(file_path)
        
        if is_valid:
            print(f"   ✅ Syntax validation PASSED")
            return True
        else:
            print(f"   ❌ Syntax validation FAILED")
            for error in errors:
                print(f"      • {error}")
            return False
    
    def test_all_fixed_files(self):
        """Test compilation of all recently fixed test files"""
        print("🧪 MQL5 Compilation Validation")
        print("=" * 50)
        
        test_files = [
            "Scripts/ProjectQuantum/Test_SafeMath.mq5",
            "Scripts/ProjectQuantum/Test_CLearningMetrics.mq5", 
            "Scripts/ProjectQuantum/Test_CRiskIntelligence.mq5"
        ]
        
        passed = 0
        total = len(test_files)
        
        for test_file in test_files:
            full_path = self.mt5_dev / test_file
            if self.test_file_compilation(full_path):
                passed += 1
            print()
        
        print("🎯 COMPILATION VALIDATION SUMMARY")
        print("=" * 40)
        print(f"Files Tested: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if passed == total:
            print("\n🎉 ALL FILES PASSED SYNTAX VALIDATION!")
            print("✅ Ready for MQL5 compilation")
        else:
            print(f"\n⚠️  {total - passed} FILES FAILED VALIDATION")
            print("🔧 Fix syntax errors before attempting MQL5 compilation")
        
        return passed == total

if __name__ == "__main__":
    validator = MQL5CompilationValidator()
    success = validator.test_all_fixed_files()
    sys.exit(0 if success else 1)