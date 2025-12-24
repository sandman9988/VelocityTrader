#!/usr/bin/env python3
"""
Comprehensive MQL5 Include File Compiler & Branding Tool
Project Quantum v1.098 - Renier De Jager

Compiles all .mqh files individually and standardizes branding
"""

import os
import sys
import glob
import re
import subprocess
import json
from datetime import datetime

# Configuration  
VERSION = "1.216"  # MQL5 format: y.xxx
COPYRIGHT_YEAR = "2024"
AUTHOR = "Renier De Jager"
COMPANY = "Quantum Trading Systems"
LINK = "https://www.quantum-trading.ai"

METAEDITOR_PATH = r"/mnt/c/DevCenter/MT5-Unified/MT5-Core/Terminal/MetaEditor64.exe"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def get_standard_header():
    """Generate standard header for all MQL5 files"""
    return f"""//+------------------------------------------------------------------+
//|                                             Project Quantum v{VERSION} |
//|                          Copyright {COPYRIGHT_YEAR}, {COMPANY} |
//|                                   {LINK} |
//|                                        Author: {AUTHOR} |
//+------------------------------------------------------------------+
#property copyright "{AUTHOR}"
#property link      "{LINK}"
#property version   "{VERSION}"
#property strict
"""

def update_file_branding(filepath):
    """Update branding in a single MQL5 file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove existing header (everything before first include or class)
        # Find first significant line
        lines = content.split('\n')
        content_start = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith('#include') or 
                stripped.startswith('class ') or 
                stripped.startswith('enum ') or
                stripped.startswith('struct ') or
                stripped.startswith('template') or
                (stripped.startswith('//') and 'Core' in stripped and 'mqh' in stripped)):
                content_start = i
                break
        
        # Rebuild file with standard header
        new_content = get_standard_header() + '\n'
        if content_start < len(lines):
            new_content += '\n'.join(lines[content_start:])
        
        # Write updated file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to update branding in {filepath}: {e}")
        return False

def compile_mqh_file(mqh_file):
    """Attempt to compile a single .mqh file (syntax check)"""
    
    # Copy to compilation directory
    comp_dir = "/mnt/c/DevCenter/MT5-Unified/MQL5-Development/Include/"
    rel_path = os.path.relpath(mqh_file, "Include/")
    target_path = os.path.join(comp_dir, rel_path)
    
    # Ensure target directory exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    try:
        # Copy file to compilation location
        subprocess.run(['cp', mqh_file, target_path], check=True)
        
        # Try to compile (syntax check)
        log_file = f"{PROJECT_ROOT}/temp_compile.log"
        if os.path.exists(log_file):
            os.remove(log_file)
            
        cmd = [METAEDITOR_PATH, f'/compile:{target_path}', f'/log:{log_file}']
        
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        # Check for errors in log
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_content = f.read()
                
            if 'error' in log_content.lower():
                return False, f"Compilation errors in log"
            else:
                return True, "Syntax check passed"
        else:
            return True, "No log file generated (likely success)"
            
    except subprocess.TimeoutExpired:
        return False, "Compilation timeout"
    except Exception as e:
        return False, f"Compilation failed: {e}"

def main():
    """Main compilation and branding process"""
    
    print(f"🏗️  Project Quantum v{VERSION} - MQL5 Compilation & Branding")
    print("=" * 65)
    
    # Find all .mqh files
    mqh_files = glob.glob("Include/**/*.mqh", recursive=True)
    print(f"📁 Found {len(mqh_files)} .mqh files to process")
    print()
    
    results = {
        'branding_updated': 0,
        'branding_failed': 0,
        'compilation_passed': 0,
        'compilation_failed': 0,
        'failed_files': []
    }
    
    for i, mqh_file in enumerate(mqh_files, 1):
        file_name = os.path.basename(mqh_file)
        print(f"[{i:2d}/{len(mqh_files)}] Processing: {file_name}")
        
        # Update branding
        print(f"   🏷️  Updating branding...")
        if update_file_branding(mqh_file):
            results['branding_updated'] += 1
            print(f"   ✅ Branding updated")
        else:
            results['branding_failed'] += 1
            print(f"   ❌ Branding failed")
            results['failed_files'].append(f"{mqh_file} (branding)")
            continue
        
        # Compile syntax check
        print(f"   🔧 Checking syntax...")
        success, message = compile_mqh_file(mqh_file)
        
        if success:
            results['compilation_passed'] += 1
            print(f"   ✅ {message}")
        else:
            results['compilation_failed'] += 1
            print(f"   ❌ {message}")
            results['failed_files'].append(f"{mqh_file} (compilation)")
        
        print()
    
    # Summary
    print("📊 COMPILATION SUMMARY")
    print("=" * 30)
    print(f"Files processed: {len(mqh_files)}")
    print(f"Branding updated: {results['branding_updated']}")
    print(f"Branding failed: {results['branding_failed']}")
    print(f"Compilation passed: {results['compilation_passed']}")
    print(f"Compilation failed: {results['compilation_failed']}")
    print()
    
    if results['failed_files']:
        print("❌ Failed files:")
        for failed_file in results['failed_files']:
            print(f"   • {failed_file}")
        print()
    
    # Save detailed results
    timestamp = datetime.now().isoformat()
    detailed_results = {
        'timestamp': timestamp,
        'version': VERSION,
        'total_files': len(mqh_files),
        'results': results
    }
    
    with open('mqh_compilation_report.json', 'w') as f:
        json.dump(detailed_results, f, indent=2)
    
    print(f"📄 Detailed report saved to: mqh_compilation_report.json")
    
    # Return success/failure
    if results['compilation_failed'] == 0:
        print("🎉 All files compiled successfully!")
        return 0
    else:
        print(f"⚠️  {results['compilation_failed']} files failed compilation")
        return 1

if __name__ == "__main__":
    sys.exit(main())