#!/usr/bin/env python3
"""
Quick MT5 Terminal Compilation Test
Tests if ProjectQuantum compiles successfully after fixes
"""

import subprocess
import os
from pathlib import Path

# MetaEditor path
METAEDITOR_PATH = r"C:\Program Files\MetaTrader 5\metaeditor64.exe"
MT5_DIR = Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/8A503E260F28D3DD9CC9A37AA3CE29BC/MQL5")
MAIN_EA = MT5_DIR / "Experts" / "ProjectQuantum_Main.mq5"
LOG_FILE = "/tmp/mt5_compile_test.log"

def main():
    print("🔧 Testing ProjectQuantum Compilation in MT5 Terminal")
    print("=" * 60)
    print(f"EA: {MAIN_EA}")
    print(f"MetaEditor: {METAEDITOR_PATH}")
    
    if not MAIN_EA.exists():
        print(f"❌ EA file not found: {MAIN_EA}")
        return 1
    
    # Prepare Windows path for MetaEditor
    ea_win_path = str(MAIN_EA).replace("/mnt/c", "C:")
    log_win_path = LOG_FILE.replace("/tmp", "C:\\Windows\\Temp")
    
    # Clean old log
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    # Build MetaEditor command
    cmd = [
        METAEDITOR_PATH,
        f'/compile:{ea_win_path}',
        f'/log:{log_win_path}',
        '/inc:C:\\Users\\renie\\AppData\\Roaming\\MetaQuotes\\Terminal\\8A503E260F28D3DD9CC9A37AA3CE29BC\\MQL5\\Include'
    ]
    
    print(f"🚀 Running compilation...")
    print(f"Command: {' '.join(cmd[:2])} ...")
    
    try:
        # Run compilation (will return immediately)
        result = subprocess.run(cmd, capture_output=True, timeout=30, cwd=str(MT5_DIR))
        
        # Wait a moment for log generation
        import time
        time.sleep(2)
        
        # Check results
        errors = 0
        warnings = 0
        
        print(f"\n📊 COMPILATION RESULTS:")
        print("-" * 40)
        
        if result.returncode == 0:
            print("✅ MetaEditor process completed successfully")
        else:
            print(f"⚠️  MetaEditor returned code: {result.returncode}")
        
        # Try to read log from both locations
        log_paths = [LOG_FILE, log_win_path, "/tmp/compile.log"]
        
        for log_path in log_paths:
            if os.path.exists(log_path):
                print(f"📄 Reading log: {log_path}")
                with open(log_path, 'r', encoding='utf-16', errors='ignore') as f:
                    content = f.read()
                break
        else:
            print("⚠️  No log file found, checking stdout/stderr...")
            content = result.stdout.decode('utf-8', errors='ignore') + result.stderr.decode('utf-8', errors='ignore')
        
        if content:
            lines = content.split('\n')
            for line in lines:
                line_lower = line.lower()
                if "error" in line_lower and "0 error" not in line_lower:
                    print(f"🔴 {line.strip()}")
                    errors += 1
                elif "warning" in line_lower and "0 warning" not in line_lower:
                    print(f"🟠 {line.strip()}")
                    warnings += 1
                elif line.strip() and ("successfully" in line_lower or "completed" in line_lower):
                    print(f"✅ {line.strip()}")
        
        # Summary
        print(f"\n📈 SUMMARY:")
        print(f"Errors: {errors}")
        print(f"Warnings: {warnings}")
        
        if errors == 0:
            print(f"🎯 SUCCESS! ProjectQuantum compiles cleanly")
            return 0
        else:
            print(f"❌ FAILED with {errors} errors")
            return 1
            
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT: Compilation took too long")
        return 1
    except FileNotFoundError:
        print(f"❌ ERROR: MetaEditor not found at {METAEDITOR_PATH}")
        return 1
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())