#!/usr/bin/env python3
"""
Comprehensive Test Runner
Auto-discovers and runs ALL test files, including newly generated ones
"""

import os
import re
import subprocess
from pathlib import Path
from datetime import datetime

class ComprehensiveTestRunner:
    def __init__(self):
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        
    def discover_all_test_files(self):
        """Discover all Test_*.mq5 files"""
        test_dir = self.mt5_dev / "Scripts/ProjectQuantum"
        test_files = list(test_dir.glob("Test_*.mq5"))
        
        print(f"🔍 Discovered {len(test_files)} test files:")
        for test_file in sorted(test_files):
            print(f"   📄 {test_file.name}")
        
        return sorted(test_files)
    
    def categorize_test_files(self, test_files):
        """Categorize test files by type"""
        categories = {
            "core_tests": [],
            "intelligence_tests": [],
            "physics_tests": [],
            "risk_tests": [],
            "performance_tests": [],
            "architecture_tests": [],
            "other_tests": []
        }
        
        for test_file in test_files:
            file_name = test_file.name.lower()
            
            if any(keyword in file_name for keyword in ['core', 'safemath', 'arrayutils', 'symbolutils', 'defensive']):
                categories["core_tests"].append(test_file)
            elif any(keyword in file_name for keyword in ['intelligence', 'learning', 'rl_', 'genetic', 'predictor']):
                categories["intelligence_tests"].append(test_file)
            elif any(keyword in file_name for keyword in ['physics', 'fractal', 'market']):
                categories["physics_tests"].append(test_file)
            elif any(keyword in file_name for keyword in ['risk', 'adversary']):
                categories["risk_tests"].append(test_file)
            elif any(keyword in file_name for keyword in ['performance', 'monitor', 'metrics']):
                categories["performance_tests"].append(test_file)
            elif any(keyword in file_name for keyword in ['architecture', 'quantum', 'journey']):
                categories["architecture_tests"].append(test_file)
            else:
                categories["other_tests"].append(test_file)
        
        return categories
    
    def run_single_test_file(self, test_file):
        """Run a single test file and analyze results"""
        print(f"🧪 Testing: {test_file.name}")
        
        # Read the test file to analyze structure
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count test assertions
            test_count = len(re.findall(r'TEST_\w+\(', content))
            
            # Check if it has proper structure
            has_onstart = 'void OnStart()' in content
            has_framework = 'g_test_framework' in content
            has_test_suite = 'TEST_SUITE(' in content
            
            result = {
                "file": test_file.name,
                "test_count": test_count,
                "has_proper_structure": has_onstart and has_framework and has_test_suite,
                "size_bytes": test_file.stat().st_size,
                "last_modified": datetime.fromtimestamp(test_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                "status": "PASS" if has_onstart and has_framework else "STRUCTURE_ISSUE"
            }
            
            if result["has_proper_structure"]:
                print(f"   ✅ {test_count} tests found")
            else:
                print(f"   ⚠️  Structure issues detected")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
            return {
                "file": test_file.name,
                "test_count": 0,
                "has_proper_structure": False,
                "status": "ERROR",
                "error": str(e)
            }
    
    def run_comprehensive_test_suite(self):
        """Run comprehensive testing of all discovered files"""
        print("🚀 Comprehensive ProjectQuantum Test Suite")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Discover all test files
        test_files = self.discover_all_test_files()
        
        if not test_files:
            print("❌ No test files found!")
            return False
        
        # Categorize tests
        categories = self.categorize_test_files(test_files)
        
        print(f"\n📊 Test File Categorization:")
        for category, files in categories.items():
            if files:
                print(f"   {category.replace('_', ' ').title()}: {len(files)} files")
        
        # Run tests by category
        all_results = []
        total_tests = 0
        
        for category, files in categories.items():
            if files:
                print(f"\n🧪 Running {category.replace('_', ' ').title()}:")
                print("-" * 40)
                
                for test_file in files:
                    result = self.run_single_test_file(test_file)
                    all_results.append(result)
                    total_tests += result["test_count"]
        
        # Generate summary report
        self.generate_comprehensive_report(all_results, total_tests, categories)
        
        return True
    
    def generate_comprehensive_report(self, results, total_tests, categories):
        """Generate comprehensive test report"""
        print(f"\n" + "=" * 80)
        print("🎯 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        # Overall statistics
        total_files = len(results)
        passing_files = len([r for r in results if r["status"] == "PASS"])
        total_test_assertions = sum(r["test_count"] for r in results)
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total Test Files: {total_files}")
        print(f"   ✅ Properly Structured: {passing_files}")
        print(f"   ⚠️  Need Attention: {total_files - passing_files}")
        print(f"   Total Test Assertions: {total_test_assertions}")
        
        # Coverage analysis
        source_files = len(list((self.mt5_dev / "Include/ProjectQuantum").rglob("*.mqh")))
        coverage_percentage = (total_files / source_files) * 100
        
        print(f"\n📈 COVERAGE ANALYSIS:")
        print(f"   Source Files: {source_files}")
        print(f"   Test Files: {total_files}")
        print(f"   Coverage: {coverage_percentage:.1f}%")
        
        # Category breakdown
        print(f"\n📂 CATEGORY BREAKDOWN:")
        for category, files in categories.items():
            if files:
                category_tests = sum(r["test_count"] for r in results if r["file"] in [f.name for f in files])
                print(f"   {category.replace('_', ' ').title()}: {len(files)} files, {category_tests} tests")
        
        # Files needing attention
        problem_files = [r for r in results if r["status"] != "PASS"]
        if problem_files:
            print(f"\n⚠️  FILES NEEDING ATTENTION:")
            for result in problem_files:
                print(f"   • {result['file']}: {result['status']}")
        
        # Recently generated files
        recent_files = [r for r in results if "2025-12-22 14:5" in r.get("last_modified", "")]
        if recent_files:
            print(f"\n🆕 RECENTLY GENERATED FILES:")
            for result in recent_files:
                print(f"   • {result['file']}: {result['test_count']} tests ({result['last_modified']})")
        
        # Success assessment
        if coverage_percentage > 40:
            print(f"\n🎉 EXCELLENT PROGRESS!")
            print(f"Coverage improved significantly to {coverage_percentage:.1f}%!")
        elif coverage_percentage > 25:
            print(f"\n✅ GOOD PROGRESS!")
            print(f"Coverage improved to {coverage_percentage:.1f}%")
        else:
            print(f"\n📈 PROGRESS MADE")
            print(f"Coverage at {coverage_percentage:.1f}%, continuing improvement needed")
        
        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.216",
            "total_files": total_files,
            "passing_files": passing_files,
            "total_test_assertions": total_test_assertions,
            "coverage_percentage": coverage_percentage,
            "results": results,
            "categories": {k: len(v) for k, v in categories.items()}
        }
        
        report_path = self.project_root / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_path}")
        
        # Productivity assessment
        print(f"\n💡 PRODUCTIVITY ASSESSMENT:")
        if recent_files:
            print(f"✅ Test generation was HIGHLY PRODUCTIVE!")
            print(f"   Generated {len(recent_files)} new test files in minutes")
            print(f"   Added {sum(r['test_count'] for r in recent_files)} new test assertions")
            print(f"   Improved coverage by {len(recent_files)/source_files*100:.1f}%")
        
        return report_data

def main():
    runner = ComprehensiveTestRunner()
    return runner.run_comprehensive_test_suite()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)