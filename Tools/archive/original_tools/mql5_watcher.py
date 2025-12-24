#!/usr/bin/env python3
"""
MQL5 File Watcher for Real-Time Compilation
Project Quantum v1.098

Watches for file changes and automatically triggers compilation.
Run this in a separate terminal alongside Claude Code.

Usage:
    pip install watchdog
    python mql5_watcher.py
"""

import sys
import os
import subprocess
import time
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: watchdog not installed")
    print("Run: pip install watchdog")
    sys.exit(1)

# --- CONFIGURATION ---
METAEDITOR_PATH = r"C:\Program Files\MetaTrader 5\metaeditor64.exe"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(PROJECT_ROOT, "compile_watch.log")

# Debounce to prevent multiple triggers on single save
DEBOUNCE_SECONDS = 1.0
last_compile_time = {}


class MQL5Handler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = event.src_path

        # Only process MQL5 files
        if not file_path.endswith((".mq5", ".mqh")):
            return

        # Skip test files
        if "Tests" in file_path:
            return

        # Debounce
        current_time = time.time()
        if file_path in last_compile_time:
            if current_time - last_compile_time[file_path] < DEBOUNCE_SECONDS:
                return
        last_compile_time[file_path] = current_time

        # Compile
        self.compile_file(file_path)

    def compile_file(self, file_path):
        filename = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, PROJECT_ROOT)

        print(f"\n{'='*60}")
        print(f"[CHANGE DETECTED] {rel_path}")
        print(f"{'='*60}")

        # Clean log
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)

        cmd = [METAEDITOR_PATH, f'/compile:{file_path}', f'/log:{LOG_FILE}']

        try:
            subprocess.run(cmd, capture_output=True, timeout=60)
            time.sleep(0.5)
            self.read_and_report_log(rel_path)
        except subprocess.TimeoutExpired:
            print("❌ TIMEOUT: Compilation took too long")
        except FileNotFoundError:
            print(f"❌ ERROR: MetaEditor not found at {METAEDITOR_PATH}")
            print("Update METAEDITOR_PATH in this script.")
        except Exception as e:
            print(f"❌ ERROR: {e}")

    def read_and_report_log(self, filename):
        if not os.path.exists(LOG_FILE):
            print("⚠️  No log file generated")
            return

        try:
            with open(LOG_FILE, 'r', encoding='utf-16') as f:
                content = f.read()
        except UnicodeError:
            with open(LOG_FILE, 'r', errors='ignore') as f:
                content = f.read()

        # Parse errors and warnings
        lines = content.split('\n')
        errors = []
        warnings = []

        for line in lines:
            line_lower = line.lower()
            if "error" in line_lower and "0 error" not in line_lower:
                errors.append(line.strip())
            elif "warning" in line_lower and "0 warning" not in line_lower:
                warnings.append(line.strip())

        # Report
        if errors or warnings:
            print(f"\n🚫 STRICT COMPILATION FAILED: {filename}")
            print("-" * 50)

            for err in errors:
                print(f"🔴 {err}")
            for warn in warnings:
                print(f"🟠 {warn}")

            print("-" * 50)
            print("Fix the errors above and save again.")
        else:
            print(f"\n✅ STRICT COMPILATION SUCCESS: {filename}")
            print("0 Errors, 0 Warnings - Ready for commit!")


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         MQL5 STRICT WATCHER - Project Quantum v1.098         ║
╠══════════════════════════════════════════════════════════════╣
║  Watching for file changes...                                ║
║  Press Ctrl+C to stop                                        ║
╚══════════════════════════════════════════════════════════════╝
    """)

    print(f"Project Root: {PROJECT_ROOT}")
    print(f"MetaEditor: {METAEDITOR_PATH}")
    print(f"\nWatching .mq5 and .mqh files for changes...\n")

    event_handler = MQL5Handler()
    observer = Observer()
    observer.schedule(event_handler, path=PROJECT_ROOT, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping watcher...")
        observer.stop()

    observer.join()
    print("Watcher stopped.")


if __name__ == "__main__":
    main()
