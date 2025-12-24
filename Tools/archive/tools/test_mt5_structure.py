#!/usr/bin/env python3
"""
Test MT5 Structure Compilation
Tests the new organized MT5 folder structure
"""

import subprocess
import os
from pathlib import Path

def test_compilation():
    """Test compilation of ProjectQuantum with new structure"""
    
    # Paths
    metaeditor = "/mnt/c/DevCenter/MT5-Unified/MT5-Core/Terminal/MetaEditor64.exe"
    main_ea = "/mnt/c/DevCenter/MT5-Unified/MQL5-Development/Experts/ProjectQuantum/ProjectQuantum_Main.mq5"
    
    print("🔧 Testing MT5 Structure Compilation")
    print("=" * 50)
    print(f"EA File: {main_ea}")
    print(f"MetaEditor: {metaeditor}")
    
    # Check if files exist
    if not Path(main_ea).exists():
        print(f"❌ EA file not found: {main_ea}")
        return False
        
    if not Path(metaeditor).exists():
        print(f"❌ MetaEditor not found: {metaeditor}")
        return False
    
    # Attempt compilation
    print(f"\n🔨 Compiling ProjectQuantum_Main.mq5...")
    
    try:
        result = subprocess.run([
            metaeditor,
            f"/compile:{main_ea}",
            "/log:compile_test.log"
        ], capture_output=True, text=True, timeout=60)
        
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
            
        # Check if .ex5 was generated
        ex5_file = main_ea.replace('.mq5', '.ex5')
        if Path(ex5_file).exists():
            print("✅ Compilation successful - .ex5 file generated")
            return True
        else:
            print("❌ Compilation failed - no .ex5 file generated")
            
            # Try to read log file
            log_file = Path("compile_test.log")
            if log_file.exists():
                print(f"\nCompilation log:")
                with open(log_file, 'r') as f:
                    print(f.read())
            
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Compilation timeout")
        return False
    except Exception as e:
        print(f"❌ Compilation error: {e}")
        return False

def verify_structure():
    """Verify the MT5 folder structure"""
    print("\n📁 Verifying MT5 Structure")
    print("=" * 30)
    
    base_path = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
    
    required_paths = [
        "Experts/ProjectQuantum/ProjectQuantum_Main.mq5",
        "Include/ProjectQuantum.mqh",
        "Include/ProjectQuantum/Core/Core.mqh",
        "Include/ProjectQuantum/Core/CLogger.mqh",
        "Include/ProjectQuantum/Intelligence/CRL_Agent.mqh",
        "Include/ProjectQuantum/Risk/CRiskManager.mqh",
        "Include/ProjectQuantum/Performance/CPerformanceMonitor.mqh",
        "Include/ProjectQuantum/Physics/CMarketAgnostic.mqh",
        "Include/ProjectQuantum/Safety/CCircuitBreaker.mqh"
    ]
    
    all_good = True
    for path_str in required_paths:
        full_path = base_path / path_str
        if full_path.exists():
            print(f"✅ {path_str}")
        else:
            print(f"❌ {path_str}")
            all_good = False
    
    return all_good

if __name__ == "__main__":
    print("🧪 ProjectQuantum MT5 Structure Test")
    print("=" * 50)
    
    # Verify structure first
    structure_ok = verify_structure()
    
    if structure_ok:
        print("\n✅ Structure verification passed")
        
        # Test compilation
        compilation_ok = test_compilation()
        
        if compilation_ok:
            print("\n🎉 MT5 structure test PASSED!")
            print("✅ All files organized correctly")
            print("✅ Compilation successful")
        else:
            print("\n⚠️ MT5 structure test PARTIAL")
            print("✅ Files organized correctly")
            print("❌ Compilation needs fixes")
    else:
        print("\n❌ MT5 structure test FAILED")
        print("❌ Missing required files")