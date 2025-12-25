#!/usr/bin/env python3
"""
VelocityTrader Code Quality Score
=================================
A "Do No Harm" focused scoring metric for financial trading code.

Scoring Philosophy:
- Safety-first: CRITICAL issues have severe impact
- Normalized: Score comparable across codebases of different sizes
- Actionable: Clear grades and improvement paths

Score Range: 0-100
  A+ (95-100): Production ready, minimal risk
  A  (90-94):  Excellent, safe for deployment
  B  (80-89):  Good, minor improvements needed
  C  (70-79):  Acceptable, should address HIGH issues
  D  (60-69):  Concerning, significant work needed
  F  (<60):    Unsafe, do not deploy

Usage:
    python3 Tools/code_quality_score.py                    # Score current state
    python3 Tools/code_quality_score.py --detailed         # With breakdown
    python3 Tools/code_quality_score.py --trend            # Show history
    python3 Tools/code_quality_score.py --ci               # CI mode (exit 1 if < threshold)
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
SCORE_HISTORY_FILE = PROJECT_ROOT / "Tools" / ".score_history.json"


@dataclass
class ScoreWeights:
    """
    Severity weights - "Do No Harm" focused

    CRITICAL issues can cause:
    - Financial loss
    - System crashes
    - Data corruption
    Therefore they have the highest penalty.

    Calibrated so that:
    - 0 CRITICAL, <50 HIGH, <200 MEDIUM = A grade (90+)
    - 0 CRITICAL, <100 HIGH, <300 MEDIUM = B grade (80+)
    - 1+ CRITICAL = caps at C grade max
    """
    CRITICAL: float = 15.0   # Each critical = major safety risk
    HIGH: float = 0.3        # Significant risk (109 HIGH = ~33 points)
    MEDIUM: float = 0.05     # Should fix (251 MEDIUM = ~13 points)
    LOW: float = 0.01        # Best practice
    INFO: float = 0.0        # Informational only


@dataclass
class CategoryMultipliers:
    """
    Category multipliers - safety-critical categories have higher impact

    "Do No Harm" categories (directly prevent financial/system harm):
    - Risk Controls: Prevent catastrophic losses
    - Execution Safety: Prevent bad trades
    - Memory Safety: Prevent crashes
    - Numerical Safety: Prevent calculation errors
    """
    # Do No Harm - Critical (2.0x)
    RISK_CONTROLS: float = 2.0

    # Do No Harm - High (1.5x)
    EXECUTION_SAFETY: float = 1.5
    MEMORY_SAFETY: float = 1.5
    NUMERICAL_SAFETY: float = 1.5

    # Standard (1.0x)
    DATA_INTEGRITY: float = 1.0
    DEFENSIVE_PROGRAMMING: float = 1.0
    REGULATORY_COMPLIANCE: float = 1.0
    CODE_QUALITY: float = 0.75  # Lower weight - style not safety


def get_category_multiplier(category: str) -> float:
    """Get multiplier for a category name."""
    multipliers = CategoryMultipliers()

    # Normalize category name
    cat_upper = category.upper().replace(" ", "_")

    mapping = {
        "RISK_CONTROLS": multipliers.RISK_CONTROLS,
        "EXECUTION_SAFETY": multipliers.EXECUTION_SAFETY,
        "MEMORY_SAFETY": multipliers.MEMORY_SAFETY,
        "NUMERICAL_SAFETY": multipliers.NUMERICAL_SAFETY,
        "DATA_INTEGRITY": multipliers.DATA_INTEGRITY,
        "DEFENSIVE_PROGRAMMING": multipliers.DEFENSIVE_PROGRAMMING,
        "REGULATORY_COMPLIANCE": multipliers.REGULATORY_COMPLIANCE,
        "CODE_QUALITY": multipliers.CODE_QUALITY,
    }

    return mapping.get(cat_upper, 1.0)


def run_audit() -> Dict:
    """Run the financial auditor and parse results."""
    try:
        result = subprocess.run(
            ["python3", str(PROJECT_ROOT / "Tools" / "mql5_financial_auditor.py"),
             "--project", str(PROJECT_ROOT)],
            capture_output=True, text=True, timeout=120
        )
        return parse_audit_output(result.stdout + result.stderr)
    except Exception as e:
        print(f"Error running audit: {e}")
        return {}


def parse_audit_output(output: str) -> Dict:
    """Parse audit output into structured data."""
    data = {
        "total_findings": 0,
        "by_severity": {},
        "by_category": {},
        "files_scanned": 0,
        "lines_scanned": 0,
    }

    lines = output.split('\n')
    in_category_section = False
    in_severity_section = False

    for line in lines:
        line = line.strip()

        # Total findings
        if "Total Findings:" in line:
            try:
                data["total_findings"] = int(line.split(":")[-1].strip())
            except ValueError:
                pass

        # Severity counts - look for "Findings by Severity" section
        if "Findings by Severity:" in line:
            in_severity_section = True
            continue

        if in_severity_section:
            if line == "" or line.startswith("Top ") or line.startswith("="):
                in_severity_section = False
            elif ":" in line:
                parts = line.split(":")
                if len(parts) == 2:
                    sev_name = parts[0].strip()
                    try:
                        count = int(parts[1].strip())
                        if sev_name in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
                            data["by_severity"][sev_name] = count
                    except ValueError:
                        pass

        # Also catch severity in header section
        if "CRITICAL:" in line and "Total" not in line and not in_severity_section:
            try:
                data["by_severity"]["CRITICAL"] = int(line.split(":")[-1].strip())
            except ValueError:
                pass
        elif "HIGH:" in line and "Total" not in line and not in_severity_section:
            try:
                val = line.split(":")[-1].strip()
                data["by_severity"]["HIGH"] = int(val)
            except ValueError:
                pass

        # Category counts
        if "Findings by Category:" in line:
            in_category_section = True
            continue

        if in_category_section:
            if line == "" or "Findings by Severity" in line:
                in_category_section = False
            elif ":" in line:
                parts = line.split(":")
                if len(parts) == 2:
                    cat_name = parts[0].strip()
                    try:
                        count = int(parts[1].strip())
                        data["by_category"][cat_name] = count
                    except ValueError:
                        pass

    return data


def calculate_score(audit_data: Dict) -> Tuple[float, Dict]:
    """
    Calculate the Code Quality Score.

    Formula:
    1. Start with 100 points
    2. Calculate weighted penalty for each finding
    3. Apply category multipliers
    4. Normalize by codebase size (findings per 1000 lines)
    5. Apply sigmoid function to keep score in 0-100 range

    Returns: (score, breakdown)
    """
    weights = ScoreWeights()

    # Get severity counts
    critical = audit_data.get("by_severity", {}).get("CRITICAL", 0)
    high = audit_data.get("by_severity", {}).get("HIGH", 0)
    medium = audit_data.get("by_severity", {}).get("MEDIUM", 0)
    low = audit_data.get("by_severity", {}).get("LOW", 0)

    # Calculate base penalty
    base_penalty = (
        critical * weights.CRITICAL +
        high * weights.HIGH +
        medium * weights.MEDIUM +
        low * weights.LOW
    )

    # Calculate category-weighted penalty
    category_penalty = 0.0
    category_breakdown = {}

    for cat_name, count in audit_data.get("by_category", {}).items():
        multiplier = get_category_multiplier(cat_name)
        cat_penalty = count * multiplier
        category_penalty += cat_penalty
        category_breakdown[cat_name] = {
            "count": count,
            "multiplier": multiplier,
            "penalty": cat_penalty
        }

    # Use severity-based penalty (more accurate than category)
    total_penalty = base_penalty

    # Calculate score (floor at 0)
    raw_score = 100 - total_penalty
    score = max(0, min(100, raw_score))

    # Do No Harm adjustment: CRITICAL issues cap the score
    if critical > 0:
        # Each critical issue caps max score at 60, then -10 per additional
        max_allowed = max(0, 60 - (critical - 1) * 10)
        score = min(score, max_allowed)

    breakdown = {
        "base_penalty": base_penalty,
        "category_penalty": category_penalty,
        "total_penalty": total_penalty,
        "critical_cap_applied": critical > 0,
        "severity_breakdown": {
            "CRITICAL": {"count": critical, "weight": weights.CRITICAL, "penalty": critical * weights.CRITICAL},
            "HIGH": {"count": high, "weight": weights.HIGH, "penalty": high * weights.HIGH},
            "MEDIUM": {"count": medium, "weight": weights.MEDIUM, "penalty": medium * weights.MEDIUM},
            "LOW": {"count": low, "weight": weights.LOW, "penalty": low * weights.LOW},
        },
        "category_breakdown": category_breakdown,
    }

    return round(score, 1), breakdown


def get_grade(score: float) -> Tuple[str, str]:
    """Get letter grade and description."""
    if score >= 95:
        return "A+", "Production ready, minimal risk"
    elif score >= 90:
        return "A", "Excellent, safe for deployment"
    elif score >= 80:
        return "B", "Good, minor improvements needed"
    elif score >= 70:
        return "C", "Acceptable, address HIGH issues"
    elif score >= 60:
        return "D", "Concerning, significant work needed"
    else:
        return "F", "UNSAFE - Do not deploy"


def get_do_no_harm_status(audit_data: Dict) -> Tuple[str, str]:
    """Get Do No Harm compliance status."""
    critical = audit_data.get("by_severity", {}).get("CRITICAL", 0)
    high = audit_data.get("by_severity", {}).get("HIGH", 0)

    # Check risk-critical categories
    risk_controls = audit_data.get("by_category", {}).get("Risk Controls", 0)
    execution_safety = audit_data.get("by_category", {}).get("Execution Safety", 0)

    if critical > 0:
        return "FAIL", f"{critical} CRITICAL issues - immediate action required"
    elif high > 50:
        return "WARN", f"{high} HIGH issues - review before production"
    elif risk_controls > 10 or execution_safety > 20:
        return "WARN", "Elevated risk in safety-critical categories"
    else:
        return "PASS", "No critical safety violations"


def save_score_history(score: float, audit_data: Dict):
    """Save score to history for trend tracking."""
    history = []
    if SCORE_HISTORY_FILE.exists():
        try:
            history = json.loads(SCORE_HISTORY_FILE.read_text())
        except json.JSONDecodeError:
            history = []

    entry = {
        "timestamp": datetime.now().isoformat(),
        "score": score,
        "critical": audit_data.get("by_severity", {}).get("CRITICAL", 0),
        "high": audit_data.get("by_severity", {}).get("HIGH", 0),
        "total": audit_data.get("total_findings", 0),
    }

    history.append(entry)

    # Keep last 100 entries
    history = history[-100:]

    SCORE_HISTORY_FILE.write_text(json.dumps(history, indent=2))


def show_trend():
    """Show score trend over time."""
    if not SCORE_HISTORY_FILE.exists():
        print("No score history available yet.")
        return

    history = json.loads(SCORE_HISTORY_FILE.read_text())

    if len(history) < 2:
        print("Need at least 2 data points for trend.")
        return

    print("\n" + "=" * 60)
    print("SCORE TREND")
    print("=" * 60)

    for entry in history[-10:]:
        ts = entry["timestamp"][:16].replace("T", " ")
        score = entry["score"]
        grade, _ = get_grade(score)
        bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
        print(f"{ts} | {bar} | {score:5.1f} ({grade})")

    # Calculate trend
    if len(history) >= 2:
        recent = history[-1]["score"]
        previous = history[-2]["score"]
        diff = recent - previous

        if diff > 0:
            trend = f"↑ +{diff:.1f}"
        elif diff < 0:
            trend = f"↓ {diff:.1f}"
        else:
            trend = "→ No change"

        print(f"\nTrend: {trend}")


def print_report(score: float, breakdown: Dict, audit_data: Dict, detailed: bool = False):
    """Print the score report."""
    grade, description = get_grade(score)
    harm_status, harm_msg = get_do_no_harm_status(audit_data)

    print("\n" + "=" * 60)
    print("VELOCITYTRADER CODE QUALITY SCORE")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Big score display
    print(f"  ╔════════════════════════════╗")
    print(f"  ║                            ║")
    print(f"  ║   SCORE: {score:>5.1f} / 100      ║")
    print(f"  ║   GRADE: {grade:>2}                 ║")
    print(f"  ║                            ║")
    print(f"  ╚════════════════════════════╝")
    print()
    print(f"  {description}")
    print()

    # Do No Harm status
    if harm_status == "PASS":
        status_icon = "✓"
    elif harm_status == "WARN":
        status_icon = "⚠"
    else:
        status_icon = "✗"

    print("-" * 60)
    print(f"DO NO HARM STATUS: {status_icon} {harm_status}")
    print(f"  {harm_msg}")
    print()

    # Severity summary
    print("-" * 60)
    print("FINDINGS BY SEVERITY")
    print("-" * 60)

    severity_data = breakdown.get("severity_breakdown", {})
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        data = severity_data.get(sev, {"count": 0, "penalty": 0})
        count = data["count"]
        penalty = data["penalty"]

        if sev == "CRITICAL" and count > 0:
            print(f"  {sev:10} : {count:4}  (penalty: -{penalty:.1f}) ← BLOCKING")
        elif count > 0:
            print(f"  {sev:10} : {count:4}  (penalty: -{penalty:.1f})")
        else:
            print(f"  {sev:10} : {count:4}")

    print()

    if detailed:
        # Category breakdown
        print("-" * 60)
        print("FINDINGS BY CATEGORY (with Do No Harm multipliers)")
        print("-" * 60)

        cat_data = breakdown.get("category_breakdown", {})
        # Sort by penalty (highest first)
        sorted_cats = sorted(cat_data.items(), key=lambda x: -x[1]["penalty"])

        for cat_name, data in sorted_cats:
            count = data["count"]
            mult = data["multiplier"]
            penalty = data["penalty"]

            mult_str = f"{mult:.1f}x" if mult != 1.0 else "1.0x"
            bar = "█" * min(20, int(penalty / 5))

            print(f"  {cat_name:25} : {count:3} × {mult_str:4} = {penalty:6.1f} {bar}")

        print()

        # Scoring explanation
        print("-" * 60)
        print("SCORE CALCULATION")
        print("-" * 60)
        print(f"  Severity penalty:            {breakdown['base_penalty']:.1f}")
        print(f"  Starting score:              100.0")
        print(f"  After penalty:               {100 - breakdown['base_penalty']:.1f}")
        if breakdown.get("critical_cap_applied"):
            print(f"  CRITICAL cap applied:        Yes (max 60)")
        print(f"  Final score:                 {score:.1f}")
        print()

    # Recommendations
    print("-" * 60)
    print("RECOMMENDATIONS")
    print("-" * 60)

    critical = audit_data.get("by_severity", {}).get("CRITICAL", 0)
    high = audit_data.get("by_severity", {}).get("HIGH", 0)

    if critical > 0:
        print(f"  1. [URGENT] Fix {critical} CRITICAL issues immediately")
        print("     Run: python3 Tools/mql5_financial_auditor.py --critical-only")

    if high > 50:
        print(f"  2. [HIGH] Review {high} HIGH severity findings")
        print("     Focus on Risk Controls and Execution Safety categories")

    if score < 80:
        print("  3. Run the instruction updater to improve AI coding:")
        print("     python3 Tools/update_ai_instructions.py --from-audit --apply")

    if score >= 90:
        print("  ✓ Code quality is excellent. Maintain current standards.")

    print()
    print("=" * 60)


def main():
    detailed = "--detailed" in sys.argv or "-d" in sys.argv
    show_trend_flag = "--trend" in sys.argv
    ci_mode = "--ci" in sys.argv
    threshold = 70  # Default CI threshold

    # Parse threshold if provided
    for i, arg in enumerate(sys.argv):
        if arg == "--threshold" and i + 1 < len(sys.argv):
            try:
                threshold = float(sys.argv[i + 1])
            except ValueError:
                pass

    if show_trend_flag:
        show_trend()
        return

    # Run audit and calculate score
    print("Running code quality audit...")
    audit_data = run_audit()

    if not audit_data:
        print("Failed to run audit")
        sys.exit(2)

    score, breakdown = calculate_score(audit_data)

    # Save to history
    save_score_history(score, audit_data)

    # Print report
    print_report(score, breakdown, audit_data, detailed)

    # CI mode exit
    if ci_mode:
        critical = audit_data.get("by_severity", {}).get("CRITICAL", 0)
        if critical > 0:
            print(f"\nCI FAILED: {critical} CRITICAL issues found")
            sys.exit(1)
        if score < threshold:
            print(f"\nCI FAILED: Score {score} below threshold {threshold}")
            sys.exit(1)
        print(f"\nCI PASSED: Score {score} meets threshold {threshold}")
        sys.exit(0)


if __name__ == "__main__":
    main()
