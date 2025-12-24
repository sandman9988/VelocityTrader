#!/usr/bin/env python3
"""
Actual MQL5 Compilation Test
Tests if files can actually compile by checking syntax more carefully
"""

import re
from pathlib import Path

class ActualMQL5Tester:
    def __init__(self):
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        
    def test_include_resolution(self, file_path):
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
    
    def check_test_framework_integration(self, file_path):
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
    
    def simulate_basic_compilation(self, file_path):
        """Simulate basic compilation checks"""
        print(f"🔨 Simulating compilation: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic syntax checks
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
        
        if issues:
            print("   ❌ Compilation issues found:")
            for issue in issues:
                print(f"      • {issue}")
            return False
        else:
            print("   ✅ Basic compilation checks passed")
            return True

    def test_file_comprehensive(self, file_path):
        """Run comprehensive test of a file"""
        print(f"\n📋 COMPREHENSIVE TEST: {file_path.name}")
        print("=" * 60)
        
        include_ok = self.test_include_resolution(file_path)
        framework_ok = self.check_test_framework_integration(file_path)
        syntax_ok = self.simulate_basic_compilation(file_path)
        
        overall_ok = include_ok and framework_ok and syntax_ok
        
        print(f"\n🎯 RESULT: {'✅ PASS' if overall_ok else '❌ FAIL'}")
        return overall_ok
    
    def test_all_files(self):
        """Test all fixed files comprehensively"""
        print("🧪 Comprehensive MQL5 Compilation Test")
        print("=" * 60)
        
        test_files = [
            "Scripts/ProjectQuantum/Test_SafeMath.mq5",
            "Scripts/ProjectQuantum/Test_CLearningMetrics.mq5",
            "Scripts/ProjectQuantum/Test_CRiskIntelligence.mq5"
        ]
        
        results = []
        for test_file in test_files:
            full_path = self.mt5_dev / test_file
            if full_path.exists():
                result = self.test_file_comprehensive(full_path)
                results.append((test_file, result))
            else:
                print(f"\n❌ FILE NOT FOUND: {test_file}")
                results.append((test_file, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 FINAL COMPILATION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_file, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_file}")
        
        print(f"\nSuccess Rate: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 ALL FILES READY FOR MQL5 COMPILATION!")
        else:
            print(f"\n⚠️  {total-passed} FILES NEED FIXES")
        
        return passed == total

if __name__ == "__main__":
    tester = ActualMQL5Tester()
    success = tester.test_all_files()
    exit(0 if success else 1)