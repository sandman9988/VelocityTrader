#!/usr/bin/env python3
"""
AI Instruction Updater for VelocityTrader

Analyzes audit findings and suggests/applies updates to AI coding instructions.
This creates a feedback loop: audit findings -> instruction updates -> better code.

Usage:
    python3 Tools/update_ai_instructions.py                    # Analyze and suggest
    python3 Tools/update_ai_instructions.py --apply            # Apply suggestions
    python3 Tools/update_ai_instructions.py --from-audit       # Run audit first
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

PROJECT_ROOT = Path(__file__).parent.parent
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"
COPILOT_MD = PROJECT_ROOT / ".github" / "copilot-instructions.md"
FINDINGS_CACHE = PROJECT_ROOT / "Tools" / ".audit_findings_cache.json"

# Map audit rule codes to instruction patterns
RULE_TO_INSTRUCTION = {
    "NUM001": {
        "title": "Division Operations",
        "bad": "double rate = value / count;",
        "good": "double rate = SafeDivide(value, count, 0.0);",
        "rule": "ALWAYS use SafeDivide() or explicit zero-check before division"
    },
    "MEM001": {
        "title": "Array Bounds",
        "bad": "arr[i] = value;",
        "good": "if(i >= 0 && i < ArraySize(arr)) arr[i] = value;",
        "rule": "ALWAYS check index against ArraySize() before array access"
    },
    "MEM002": {
        "title": "ArrayResize Validation",
        "bad": "ArrayResize(buffer, size);",
        "good": "if(ArrayResize(buffer, size) != size) return false;",
        "rule": "ALWAYS check ArrayResize() return value equals requested size"
    },
    "FILE001": {
        "title": "File Handle Validation",
        "bad": "int h = FileOpen(path, mode); FileRead...(h);",
        "good": "int h = FileOpen(path, mode); if(h == INVALID_HANDLE) return false;",
        "rule": "ALWAYS validate file handle against INVALID_HANDLE before use"
    },
    "EXEC001": {
        "title": "Trade Error Handling",
        "bad": "OrderSend(...);",
        "good": "if(!OrderSend(...)) { int err = GetLastError(); Log(LOG_ERROR, err); }",
        "rule": "ALWAYS check OrderSend return and GetLastError() on failure"
    },
    "DATA001": {
        "title": "Numeric Validation",
        "bad": "double price = FileReadDouble(h); OrderSend(..., price, ...);",
        "good": "double price = FileReadDouble(h); if(!MathIsValidNumber(price)) return false;",
        "rule": "ALWAYS validate external numeric data with MathIsValidNumber()"
    },
}


def run_audit() -> Dict:
    """Run the financial auditor and capture findings."""
    print("Running financial audit...")
    try:
        result = subprocess.run(
            ["python3", str(PROJECT_ROOT / "Tools" / "mql5_financial_auditor.py"),
             "--project", str(PROJECT_ROOT), "--json"],
            capture_output=True, text=True, timeout=120
        )
        # Try to parse JSON from output
        for line in result.stdout.split('\n'):
            if line.strip().startswith('{'):
                return json.loads(line)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Audit failed: {e}")
    return {}


def extract_findings_from_output() -> List[Dict]:
    """Run audit and extract findings."""
    result = subprocess.run(
        ["python3", str(PROJECT_ROOT / "Tools" / "mql5_financial_auditor.py"),
         "--project", str(PROJECT_ROOT)],
        capture_output=True, text=True, timeout=120
    )

    findings = []
    # Parse the text output for rule codes
    for line in result.stdout.split('\n'):
        match = re.search(r'\[([A-Z]+\d+)\]', line)
        if match:
            findings.append({
                "rule": match.group(1),
                "line": line.strip()
            })
    return findings


def analyze_findings(findings: List[Dict]) -> Dict[str, int]:
    """Count findings by rule code."""
    counts = {}
    for f in findings:
        rule = f.get("rule", "UNKNOWN")
        counts[rule] = counts.get(rule, 0) + 1
    return counts


def get_current_rules(filepath: Path) -> Set[str]:
    """Extract rule codes already documented in an instruction file."""
    if not filepath.exists():
        return set()

    content = filepath.read_text()
    # Find all rule codes mentioned
    return set(re.findall(r'[A-Z]{2,}0\d{2}', content))


def suggest_updates(finding_counts: Dict[str, int]) -> List[Dict]:
    """Generate suggested instruction updates based on findings."""
    suggestions = []

    claude_rules = get_current_rules(CLAUDE_MD)

    for rule_code, count in sorted(finding_counts.items(), key=lambda x: -x[1]):
        if rule_code in RULE_TO_INSTRUCTION:
            info = RULE_TO_INSTRUCTION[rule_code]
            # Check if rule is already well-documented
            is_new = rule_code not in claude_rules

            suggestions.append({
                "rule": rule_code,
                "count": count,
                "is_new": is_new,
                "title": info["title"],
                "instruction": info["rule"],
                "bad_example": info["bad"],
                "good_example": info["good"]
            })

    return suggestions


def format_instruction_block(suggestion: Dict) -> str:
    """Format a suggestion as a markdown instruction block."""
    return f"""
### {suggestion['rule']}: {suggestion['title']}
{suggestion['instruction']}

```mql5
// NEVER:
{suggestion['bad_example']}

// ALWAYS:
{suggestion['good_example']}
```
"""


def append_to_claude_md(suggestions: List[Dict]) -> int:
    """Append new rules to CLAUDE.md."""
    if not CLAUDE_MD.exists():
        print(f"CLAUDE.md not found at {CLAUDE_MD}")
        return 0

    content = CLAUDE_MD.read_text()
    new_rules = [s for s in suggestions if s["is_new"]]

    if not new_rules:
        print("No new rules to add.")
        return 0

    # Add new rules section
    additions = "\n## Recently Added Rules\n"
    additions += f"*Added: {datetime.now().strftime('%Y-%m-%d')} from audit findings*\n"

    for s in new_rules:
        additions += format_instruction_block(s)

    # Insert before the last section or at end
    if "---" in content:
        parts = content.rsplit("---", 1)
        new_content = parts[0] + additions + "\n---" + parts[1]
    else:
        new_content = content + additions

    CLAUDE_MD.write_text(new_content)
    return len(new_rules)


def print_report(suggestions: List[Dict]):
    """Print analysis report."""
    print("\n" + "=" * 60)
    print("AI INSTRUCTION UPDATE ANALYSIS")
    print("=" * 60)

    if not suggestions:
        print("No actionable findings.")
        return

    print(f"\nFindings by rule (top issues for AI to learn):\n")

    for s in suggestions:
        status = "[NEW]" if s["is_new"] else "[exists]"
        print(f"  {s['rule']:8} {status:10} {s['count']:3}x  {s['title']}")

    new_count = sum(1 for s in suggestions if s["is_new"])
    if new_count > 0:
        print(f"\n{new_count} new rules can be added to CLAUDE.md")
        print("Run with --apply to add them.")


def main():
    apply_mode = "--apply" in sys.argv
    from_audit = "--from-audit" in sys.argv or apply_mode

    if from_audit:
        findings = extract_findings_from_output()
    elif FINDINGS_CACHE.exists():
        findings = json.loads(FINDINGS_CACHE.read_text())
    else:
        print("No cached findings. Run with --from-audit to analyze.")
        findings = extract_findings_from_output()

    # Cache findings
    FINDINGS_CACHE.parent.mkdir(exist_ok=True)
    FINDINGS_CACHE.write_text(json.dumps(findings, indent=2))

    counts = analyze_findings(findings)
    suggestions = suggest_updates(counts)

    print_report(suggestions)

    if apply_mode:
        added = append_to_claude_md(suggestions)
        if added:
            print(f"\n✓ Added {added} new rules to CLAUDE.md")
            print("  AI agents will follow these rules in future sessions.")


if __name__ == "__main__":
    main()
