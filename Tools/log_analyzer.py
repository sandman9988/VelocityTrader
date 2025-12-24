#!/usr/bin/env python3
"""
Project Quantum - Log Analysis Tool
Parses JSONL logs and provides summary statistics for review.

Usage:
    python analyze_logs.py logs/*.jsonl
    python analyze_logs.py --level VERBOSE logs/quantum_*.jsonl
    python analyze_logs.py --category RISK logs/*.jsonl
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def parse_log_entry(line: str) -> dict | None:
    """Parse a single JSONL log entry."""
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None


def analyze_logs(files: list[Path], level_filter: str = None, category_filter: str = None):
    """Analyze log files and print summary."""
    entries = []
    errors = 0

    # Parse all files
    for filepath in files:
        if not filepath.exists():
            print(f"Warning: File not found: {filepath}")
            continue

        with open(filepath, 'r') as f:
            for line in f:
                entry = parse_log_entry(line)
                if entry:
                    entries.append(entry)
                else:
                    errors += 1

    if not entries:
        print("No log entries found.")
        return

    # Apply filters
    if level_filter:
        entries = [e for e in entries if e.get('level', '').upper() == level_filter.upper()]

    if category_filter:
        entries = [e for e in entries if f'[{category_filter.upper()}]' in e.get('message', '').upper()]

    print(f"\n{'='*60}")
    print(f" PROJECT QUANTUM LOG ANALYSIS")
    print(f"{'='*60}")
    print(f"Files analyzed: {len(files)}")
    print(f"Total entries:  {len(entries)}")
    print(f"Parse errors:   {errors}")

    if not entries:
        print("\nNo entries match the filters.")
        return

    # Level distribution
    levels = Counter(e.get('level', 'UNKNOWN') for e in entries)
    print(f"\n{'─'*40}")
    print("Level Distribution:")
    for level, count in sorted(levels.items(), key=lambda x: -x[1]):
        pct = count / len(entries) * 100
        bar = '█' * int(pct / 2)
        print(f"  {level:12} {count:6} ({pct:5.1f}%) {bar}")

    # Time range
    timestamps = []
    for e in entries:
        ts = e.get('ts')
        if ts:
            try:
                timestamps.append(datetime.strptime(ts, '%Y.%m.%d %H:%M:%S'))
            except:
                pass

    if timestamps:
        print(f"\n{'─'*40}")
        print("Time Range:")
        print(f"  First: {min(timestamps)}")
        print(f"  Last:  {max(timestamps)}")
        duration = max(timestamps) - min(timestamps)
        print(f"  Duration: {duration}")

    # Session info
    sessions = set(e.get('session', 'unknown') for e in entries)
    symbols = set(e.get('symbol', 'unknown') for e in entries)
    print(f"\n{'─'*40}")
    print(f"Sessions: {len(sessions)}")
    print(f"Symbols:  {', '.join(symbols)}")

    # Category breakdown (for VERBOSE logs)
    verbose_entries = [e for e in entries if e.get('level') == 'VERBOSE']
    if verbose_entries:
        categories = Counter()
        for e in verbose_entries:
            msg = e.get('message', '')
            if msg.startswith('[') and ']' in msg:
                cat = msg[1:msg.index(']')]
                categories[cat] += 1

        if categories:
            print(f"\n{'─'*40}")
            print("Verbose Categories:")
            for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                print(f"  {cat:15} {count:6}")

    # Trace analysis
    trace_entries = [e for e in entries if e.get('level') == 'TRACE']
    if trace_entries:
        funcs = Counter()
        for e in trace_entries:
            msg = e.get('message', '')
            if 'ENTER' in msg or 'EXIT' in msg:
                # Extract function name
                parts = msg.split()
                for p in parts:
                    if '()' in p:
                        funcs[p.replace('()', '')] += 1
                        break

        if funcs:
            print(f"\n{'─'*40}")
            print("Function Trace Counts:")
            for func, count in sorted(funcs.items(), key=lambda x: -x[1])[:10]:
                print(f"  {func:25} {count:6}")

    # Errors and warnings
    issues = [e for e in entries if e.get('level') in ('ERROR', 'CRITICAL', 'WARN')]
    if issues:
        print(f"\n{'─'*40}")
        print(f"Issues Found ({len(issues)}):")
        for e in issues[:20]:  # Show first 20
            level = e.get('level', 'UNKNOWN')
            msg = e.get('message', '')[:60]
            ts = e.get('ts', '')
            print(f"  [{level:8}] {ts} | {msg}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more")

    # Audit trail
    audits = [e for e in entries if e.get('level') == 'AUDIT']
    if audits:
        print(f"\n{'─'*40}")
        print(f"Audit Trail ({len(audits)} entries):")
        for e in audits[:10]:
            audit = e.get('audit', {})
            action = audit.get('action', 'unknown')
            outcome = audit.get('outcome', 'unknown')
            event = audit.get('event', 'unknown')
            print(f"  {event:15} | {action:15} | {outcome}")
        if len(audits) > 10:
            print(f"  ... and {len(audits) - 10} more")

    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Analyze Project Quantum logs")
    parser.add_argument("files", nargs="+", type=Path, help="Log files to analyze (JSONL format)")
    parser.add_argument("--level", "-l", help="Filter by log level (e.g., VERBOSE, DEBUG, TRACE)")
    parser.add_argument("--category", "-c", help="Filter by category (for VERBOSE logs)")
    args = parser.parse_args()

    analyze_logs(args.files, args.level, args.category)


if __name__ == "__main__":
    main()
