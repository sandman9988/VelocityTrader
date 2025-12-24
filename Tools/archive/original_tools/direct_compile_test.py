#!/usr/bin/env python3
"""
Direct MQL5 Compilation Test
Tests compilation directly with MetaEditor
"""

import subprocess
import os
import time
from pathlib import Path

def test_direct_compile():
    """Test direct compilation of a single file"""
    
    # Paths
    metaeditor = r"C:\DevCenter\MT5-Unified\MT5-Core\Terminal\MetaEditor64.exe"
    test_file = r"C:\DevCenter\MT5-Unified\MQL5-Development\Include\ProjectQuantum\Core\SafeMath.mqh"
    
    print("🔧 Direct Compilation Test")
    print(f"MetaEditor: {metaeditor}")
    print(f"Test file: {test_file}")
    
    # Create a simple test script that uses MetaEditor directly
    batch_content = f"""@echo off
echo Starting compilation...
"{metaeditor}" /compile:"{test_file}" /log:"C:\\DevCenter\\MT5-Unified\\MQL5-Development\\compile_test.log"
echo Exit code: %errorlevel%
"""
    
    batch_file = Path("C:/DevCenter/MT5-Unified/MQL5-Development/compile_test.bat")
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    print("\n📝 Created batch file for Windows compilation")
    
    # Try running through cmd
    try:
        result = subprocess.run(
            ["cmd.exe", "/c", str(batch_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"\nReturn code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Check if log was created
    log_file = Path("C:/DevCenter/MT5-Unified/MQL5-Development/compile_test.log")
    if log_file.exists():
        print(f"\n📄 Log file created!")
        try:
            # Try different encodings
            for encoding in ['utf-16', 'utf-8', 'cp1252']:
                try:
                    with open(log_file, 'r', encoding=encoding) as f:
                        content = f.read()
                        print(f"\nLog content ({encoding}):\n{content[:500]}")
                        break
                except:
                    continue
        except:
            print("❌ Could not read log file")
    else:
        print("\n❌ No log file created")
    
    # Alternative: Try to read the file and check for basic syntax
    print("\n📄 Checking file syntax manually...")
    mqh_file = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development/Include/ProjectQuantum/Core/SafeMath.mqh")
    
    if mqh_file.exists():
        with open(mqh_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"File size: {len(content)} bytes")
        print(f"Lines: {len(content.splitlines())}")
        
        # Check for common issues
        issues = []
        if "#property strict" not in content:
            issues.append("Missing #property strict")
        if "static const" in content and "class" in content:
            issues.append("Contains static const in class (MQL5 doesn't support)")
        if "#pragma once" in content:
            issues.append("Uses #pragma once (use include guards instead)")
            
        if issues:
            print("\n⚠️  Potential issues found:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print("✅ No obvious syntax issues found")

if __name__ == "__main__":
    test_direct_compile()