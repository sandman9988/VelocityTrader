#!/usr/bin/env python3
"""
MQL5 Strict Compiler Wrapper for Claude Code Integration
Project Quantum v1.098

This script wraps MetaEditor compilation and provides clean feedback
for the Claude Code feedback loop.
"""

import sys
import os
import subprocess
import time
import glob

# --- CONFIGURATION ---
# Adjust this path to your MetaEditor executable
METAEDITOR_PATH = r"/mnt/c/DevCenter/MT5-Unified/MT5-Core/Terminal/MetaEditor64.exe"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(PROJECT_ROOT, "compile_temp.log")

def compile_file(target_file):
    """Compile a single MQL5 file and return (success, errors, warnings)"""

    # Ensure absolute path
    if not os.path.isabs(target_file):
        target_file = os.path.join(PROJECT_ROOT, target_file)

    if not os.path.exists(target_file):
        return False, [f"File not found: {target_file}"], []

    # Clean previous log
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    print(f"Compiling: {os.path.basename(target_file)}...")

    # Run MetaEditor (Headless)
    cmd = [METAEDITOR_PATH, f'/compile:{target_file}', f'/log:{LOG_FILE}']

    try:
        process = subprocess.run(cmd, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return False, ["Compilation timeout (60s)"], []
    except FileNotFoundError:
        return False, [f"MetaEditor not found at: {METAEDITOR_PATH}"], []

    # MetaEditor is async in writing logs sometimes
    time.sleep(0.5)

    # Read and Parse Log
    if not os.path.exists(LOG_FILE):
        return False, ["No log file generated - check MetaEditor path"], []

    try:
        # MetaEditor logs are UTF-16
        with open(LOG_FILE, 'r', encoding='utf-16') as f:
            log_content = f.read()
    except Exception:
        # Fallback
        with open(LOG_FILE, 'r', errors='ignore') as f:
            log_content = f.read()

    # Filter for Errors and Warnings
    lines = log_content.split('\n')
    errors = []
    warnings = []

    for line in lines:
        line_lower = line.lower()
        if "error" in line_lower and "0 error" not in line_lower:
            errors.append(line.strip())
        elif "warning" in line_lower and "0 warning" not in line_lower:
            warnings.append(line.strip())

    success = len(errors) == 0 and len(warnings) == 0
    return success, errors, warnings


def compile_and_report(target_file):
    """Compile a file and print formatted report"""

    success, errors, warnings = compile_file(target_file)

    if not success:
        print("\n🚫 COMPILATION FAILED (STRICT MODE)")
        print("-" * 60)
        for err in errors:
            print(f"🔴 ERROR: {err}")
        for warn in warnings:
            print(f"🟠 WARNING: {warn}")
        print("-" * 60)
        print("\nFix the errors above and re-run compilation.")
        sys.exit(1)
    else:
        print("\n✅ STRICT COMPILATION SUCCESS")
        print("0 Errors, 0 Warnings.")
        sys.exit(0)


def compile_all():
    """Compile all .mq5 files in the project"""

    print("=" * 60)
    print("PROJECT QUANTUM - FULL BUILD (STRICT MODE)")
    print("=" * 60)

    # Find all .mq5 files (main executables)
    mq5_files = glob.glob(os.path.join(PROJECT_ROOT, "**/*.mq5"), recursive=True)

    # Exclude test files if desired
    mq5_files = [f for f in mq5_files if "Tests" not in f]

    if not mq5_files:
        print("No .mq5 files found!")
        sys.exit(1)

    total_errors = []
    total_warnings = []
    failed_files = []

    for mq5_file in mq5_files:
        rel_path = os.path.relpath(mq5_file, PROJECT_ROOT)
        print(f"\n[BUILD] {rel_path}")

        success, errors, warnings = compile_file(mq5_file)

        if not success:
            failed_files.append(rel_path)
            total_errors.extend(errors)
            total_warnings.extend(warnings)
            print(f"  ❌ FAILED ({len(errors)} errors, {len(warnings)} warnings)")
        else:
            print(f"  ✅ OK")

    # Summary
    print("\n" + "=" * 60)
    print("BUILD SUMMARY")
    print("=" * 60)
    print(f"Files compiled: {len(mq5_files)}")
    print(f"Failures: {len(failed_files)}")
    print(f"Total Errors: {len(total_errors)}")
    print(f"Total Warnings: {len(total_warnings)}")

    if failed_files:
        print("\n🚫 BUILD FAILED")
        print("\nFailed files:")
        for f in failed_files:
            print(f"  - {f}")
        print(f"\nTotal: {len(total_errors)} errors, {len(total_warnings)} warnings")

        # Write ALL errors to file for Claude Code feedback loop
        error_file = os.path.join(PROJECT_ROOT, "build_errors.txt")
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"BUILD FAILED: {len(total_errors)} errors, {len(total_warnings)} warnings\n")
            f.write("=" * 60 + "\n\n")
            for err in total_errors:
                f.write(f"{err}\n")
            if total_warnings:
                f.write("\nWARNINGS:\n")
                for warn in total_warnings:
                    f.write(f"{warn}\n")

        print(f"\n📄 Full error list written to: build_errors.txt")
        print("   Share this file with Claude Code for fixes.")
        sys.exit(1)
    else:
        print("\n✅ ALL FILES COMPILED SUCCESSFULLY")
        sys.exit(0)


def print_usage():
    print("""
MQL5 Strict Compiler - Project Quantum v1.098

Usage:
  python mql5_build.py <filename.mq5>   - Compile single file
  python mql5_build.py --all            - Compile all .mq5 files
  python mql5_build.py --help           - Show this help

Examples:
  python mql5_build.py Main/ProjectQuantum_Main.mq5
  python mql5_build.py --all
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--help" or arg == "-h":
        print_usage()
        sys.exit(0)
    elif arg == "--all":
        compile_all()
    else:
        compile_and_report(arg)
