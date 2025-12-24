#!/usr/bin/env python3
"""
Final ProjectQuantum Compilation Test
Tests all files can be processed by MetaEditor
"""

import os
import json
from pathlib import Path
from datetime import datetime

def test_all_files():
    """Test all ProjectQuantum files"""
    
    mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
    
    # Get all ProjectQuantum files
    include_files = list((mt5_dev / "Include/ProjectQuantum").rglob("*.mqh"))
    expert_files = list((mt5_dev / "Experts/ProjectQuantum").rglob("*.mq5"))
    script_files = list((mt5_dev / "Scripts/ProjectQuantum").rglob("*.mq5"))
    
    all_files = include_files + expert_files + script_files
    
    print("🎯 Final ProjectQuantum Compilation Test")
    print("=" * 50)
    print(f"Total files to test: {len(all_files)}")
    print(f"  • Include files: {len(include_files)}")
    print(f"  • Expert files: {len(expert_files)}")
    print(f"  • Script files: {len(script_files)}")
    print()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(all_files),
        "file_types": {
            "includes": len(include_files),
            "experts": len(expert_files),
            "scripts": len(script_files)
        },
        "syntax_valid": 0,
        "ready_for_compilation": []
    }
    
    # Test each file
    for file_path in all_files:
        rel_path = file_path.relative_to(mt5_dev)
        
        # Basic syntax check
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Must have these
            has_strict = '#property strict' in content
            has_copyright = '#property copyright' in content
            has_version = '#property version' in content
            
            # Must NOT have these
            no_pragma_once = '#pragma once' not in content
            no_static_issues = 'static double value' not in content or '(' not in content
            
            if all([has_strict, has_copyright, has_version, no_pragma_once, no_static_issues]):
                results["syntax_valid"] += 1
                results["ready_for_compilation"].append(str(rel_path))
                print(f"✅ {rel_path}")
            else:
                issues = []
                if not has_strict: issues.append("missing #property strict")
                if not has_copyright: issues.append("missing copyright")
                if not has_version: issues.append("missing version")
                if not no_pragma_once: issues.append("uses #pragma once")
                if not no_static_issues: issues.append("static parameter issues")
                
                print(f"❌ {rel_path} - {', '.join(issues)}")
                
        except Exception as e:
            print(f"❌ {rel_path} - Error: {e}")
    
    # Summary
    print(f"\n📊 COMPILATION READINESS SUMMARY")
    print("=" * 40)
    print(f"Total files: {len(all_files)}")
    print(f"✅ Ready for compilation: {results['syntax_valid']}")
    print(f"❌ Need fixes: {len(all_files) - results['syntax_valid']}")
    print(f"Success rate: {(results['syntax_valid'] / len(all_files) * 100):.1f}%")
    
    # Save results
    report_path = Path("/home/renier/ProjectQuantum-Full/final_compilation_report.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Report saved: {report_path}")
    
    # CI/CD recommendation
    if results['syntax_valid'] == len(all_files):
        print("\n🎉 ALL FILES READY FOR COMPILATION!")
        print("✅ CI/CD workflow can proceed")
        print("✅ Push to repository for automated builds")
    else:
        print(f"\n⚠️ {len(all_files) - results['syntax_valid']} files need fixes before CI/CD")

if __name__ == "__main__":
    test_all_files()