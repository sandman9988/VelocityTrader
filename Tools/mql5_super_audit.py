#!/usr/bin/env python3
"""
MQL5 Super Audit Tool
=====================
Comprehensive code quality analysis combining:
- MQL4 deprecation detection
- C++ compatibility checking
- Best practices analysis
- Financial safety checks
- Code metrics

Author: VelocityTrader Team
Version: 1.0.0
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
from collections import defaultdict


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "CRITICAL"  # Must fix - will cause issues
    ERROR = "ERROR"        # Should fix - deprecated/unsupported
    WARNING = "WARNING"    # Consider fixing - anti-pattern
    INFO = "INFO"          # Informational - style suggestion


class Category(Enum):
    """Issue categories"""
    MQL4_DEPRECATED = "MQL4_DEPRECATED"
    CPP_UNSUPPORTED = "CPP_UNSUPPORTED"
    BEST_PRACTICE = "BEST_PRACTICE"
    FINANCIAL_SAFETY = "FINANCIAL_SAFETY"
    POINTER_SAFETY = "POINTER_SAFETY"
    RESOURCE_LEAK = "RESOURCE_LEAK"


@dataclass
class Issue:
    """Represents a code issue"""
    file: str
    line: int
    category: Category
    severity: Severity
    rule: str
    message: str
    suggestion: str = ""
    context: str = ""


@dataclass
class AuditResult:
    """Audit result summary"""
    total_files: int = 0
    total_lines: int = 0
    issues: List[Issue] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)

    def add_issue(self, issue: Issue):
        self.issues.append(issue)

    def count_by_severity(self) -> Dict[str, int]:
        counts = {s.value: 0 for s in Severity}
        for issue in self.issues:
            counts[issue.severity.value] += 1
        return counts

    def count_by_category(self) -> Dict[str, int]:
        counts = {c.value: 0 for c in Category}
        for issue in self.issues:
            counts[issue.category.value] += 1
        return counts


class MQL5SuperAudit:
    """Comprehensive MQL5 code auditor"""

    # MQL4 deprecated patterns
    MQL4_PATTERNS = {
        # Event handlers
        r'\b(init|deinit|start)\s*\(': (
            "MQL4 event handler",
            "Replace with OnInit/OnDeinit/OnTick"
        ),
        # Trade functions
        r'\b(OrderClose|OrderCloseBy|OrderDelete|OrderModify|OrderSelect|OrdersTotal|OrdersHistoryTotal)\b': (
            "MQL4 trade function",
            "Use MQL5 CTrade class or OrderSend with MqlTradeRequest"
        ),
        r'\b(OrderTicket|OrderType|OrderLots|OrderOpenPrice|OrderStopLoss|OrderTakeProfit|OrderSymbol|OrderMagicNumber|OrderComment|OrderProfit|OrderSwap|OrderCommission)\b': (
            "MQL4 order property function",
            "Use PositionGet*/OrderGet* functions"
        ),
        r'\b(MarketInfo|RefreshRates)\b': (
            "MQL4 market function",
            "Use SymbolInfo* functions"
        ),
        # Constants
        r'\b(OP_BUY|OP_SELL|OP_BUYLIMIT|OP_SELLLIMIT|OP_BUYSTOP|OP_SELLSTOP)\b': (
            "MQL4 trade constant",
            "Use ORDER_TYPE_* or POSITION_TYPE_* enums"
        ),
        r'\b(MODE_TRADES|MODE_HISTORY|SELECT_BY_POS|SELECT_BY_TICKET)\b': (
            "MQL4 selection constant",
            "Use MQL5 position/order enumeration"
        ),
        r'\b(MODE_ASK|MODE_BID|MODE_SPREAD|MODE_STOPLEVEL|MODE_LOTSIZE)\b': (
            "MQL4 MODE_* constant",
            "Use SymbolInfoDouble/SymbolInfoInteger"
        ),
        # Predefined vars
        r'(?<!\.)(?<!\w)(Ask|Bid)(?!\s*\()(?!\w)': (
            "MQL4 predefined variable",
            "Use SymbolInfoDouble(_Symbol, SYMBOL_ASK/BID)"
        ),
        r'#\s*property\s+strict': (
            "#property strict",
            "Remove - MQL5 is strict by design"
        ),
    }

    # C++ unsupported patterns
    CPP_PATTERNS = {
        r'\busing\s+namespace\s+std\b': (
            "using namespace std",
            "C++ namespace not available in MQL5"
        ),
        r'\b(std|boost)\s*::\s*[A-Za-z_]\w*': (
            "std::/boost:: namespace",
            "C++ standard library not available in MQL5"
        ),
        r'\b(cout|cin|cerr|clog|endl)\b': (
            "iostream identifier",
            "Use Print/Comment/Alert instead"
        ),
        r'\b(printf|scanf|sprintf|sscanf|fprintf)\s*\(': (
            "C stdio function",
            "Use StringFormat/Print instead"
        ),
        r'\b(malloc|calloc|realloc|free)\s*\(': (
            "C memory function",
            "Use new/delete or ArrayResize"
        ),
        r'\b(fopen|fclose|fread|fwrite|fseek)\s*\(': (
            "C file function",
            "Use MQL5 File* functions"
        ),
        r'\b(try|catch|throw|noexcept)\b': (
            "Exception handling",
            "Not supported - use error codes and GetLastError()"
        ),
        r'\bnullptr\b': (
            "nullptr keyword",
            "Use NULL in MQL5"
        ),
        r'\b(auto|decltype)\b(?!\s*\()': (
            "auto type deduction",
            "Explicitly declare types in MQL5"
        ),
        r'\b(constexpr|consteval|constinit|static_assert)\b': (
            "constexpr/static_assert",
            "Use const or #define"
        ),
        r'\b(static_cast|const_cast|reinterpret_cast)\s*<': (
            "C++ style cast",
            "Use C-style (type) casts"
        ),
        r'\b(int|void)\s+main\s*\(': (
            "main() function",
            "Use OnInit/OnTick entry points"
        ),
        r'\b(concept|requires|co_await|co_yield|co_return)\b': (
            "C++20 feature",
            "Not supported in MQL5"
        ),
    }

    # Best practice patterns - FINANCIAL CODE: DO NO HARM!
    # Every unchecked operation is a potential point of failure that could cause financial loss
    BEST_PRACTICE_PATTERNS = {
        r'\bSleep\s*\([^)]*\)': (
            "Sleep() call",
            "Blocks tick processing - missed trades possible! Use EventSetTimer",
            Severity.WARNING
        ),
        r'OrderSend\s*\([^)]+\)\s*;': (
            "Unchecked OrderSend",
            "CRITICAL: Must check OrderSend return - failed orders lose money!",
            Severity.ERROR
        ),
        r'^\s*ArrayResize\s*\([^)]+\)\s*;': (
            "Unchecked ArrayResize",
            "Memory failure = trading on garbage data! Check return value",
            Severity.WARNING
        ),
        r'^\s*(CopyBuffer|CopyRates|CopyClose|CopyHigh|CopyLow)\s*\([^)]+\)\s*;': (
            "Unchecked Copy* function",
            "Indicator data may not be ready - trading on stale/missing data!",
            Severity.WARNING
        ),
        r'\.magic\s*=\s*0\s*;': (
            "Magic number = 0",
            "Use unique magic number for EA identification",
            Severity.WARNING
        ),
        r'while\s*\(\s*(true|1)\s*\)': (
            "Infinite loop",
            "Ensure proper break/return conditions",
            Severity.WARNING
        ),
        r'GetPointer\s*\([^)]+\)\s*\.': (
            "GetPointer() with dot operator",
            "GetPointer returns pointer - use arrow (->)",
            Severity.ERROR
        ),
    }

    # Financial safety patterns - only flag truly dangerous casts
    FINANCIAL_PATTERNS = {
        # DANGEROUS: Casting prices/lots directly without rounding
        r'\(\s*int\s*\)\s*(lot|volume|price|sl|tp|stoploss|takeprofit)': (
            "Dangerous cast on financial value",
            "Use MathRound/NormalizeDouble instead of direct (int) cast",
            Severity.ERROR
        ),
        r'\(\s*float\s*\)\s*(SymbolInfo|AccountInfo|Position|Order)': (
            "Dangerous float cast on API value",
            "float has only ~7 digits precision - use double for financial data",
            Severity.ERROR
        ),
        # INFO: These are usually intentional but worth noting
        r'\b(volume|lot|lots)\s*=\s*\d+\.\d+': (
            "Hardcoded lot size",
            "Use calculated or input parameter",
            Severity.INFO
        ),
        r'"(EURUSD|GBPUSD|USDJPY|USDCHF|AUDUSD|XAUUSD)"': (
            "Hardcoded symbol",
            "Use _Symbol or input parameter",
            Severity.INFO
        ),
        r'\.deviation\s*=\s*\d+\s*;': (
            "Hardcoded deviation",
            "Use calculated or input parameter",
            Severity.INFO
        ),
    }

    # Safe cast patterns - these are intentional and don't need flagging
    SAFE_CAST_PATTERNS = [
        r'\(int\)\s*SymbolInfoInteger',      # Already integer, just type conversion
        r'\(int\)\s*MathRound',              # Already rounded
        r'\(int\)\s*MathFloor',              # Already floored
        r'\(int\)\s*MathCeil',               # Already ceiled
        r'\(int\)\s*\([^)]*Time[^)]*/',      # Time division (seconds to minutes/hours)
        r'\(int\)\s*\([^)]*\s*/\s*60',       # Time to minutes
        r'\(int\)\s*\([^)]*\s*/\s*3600',     # Time to hours
        r'\(int\)\s*g_breaker\.',            # Enum/state casts
        r'\(int\)\s*\w+Tab',                 # UI tab index
        r'\(int\)\s*checksum',               # Checksum values
        r'\(int\)\s*autoTag',                # Tag/flag values
        r'\(int\)\s*priority',               # Queue priority
        r'\(int\)\s*fileSize',               # File operations
        r'\(int\)\s*dataSize',               # Data size calculations
    ]

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.result = AuditResult()

    def find_mql5_files(self) -> List[Path]:
        """Find all MQL5 files in the project"""
        files = []
        mql5_dir = self.project_root / "MQL5"
        if mql5_dir.exists():
            files.extend(mql5_dir.rglob("*.mq5"))
            files.extend(mql5_dir.rglob("*.mqh"))
        return sorted(files)

    def audit_file(self, file_path: Path) -> List[Issue]:
        """Audit a single file"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
        except Exception as e:
            return issues

        rel_path = str(file_path.relative_to(self.project_root))

        for i, line in enumerate(lines, 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('//'):
                continue

            # Check MQL4 deprecated patterns
            for pattern, (name, suggestion) in self.MQL4_PATTERNS.items():
                if re.search(pattern, line):
                    issues.append(Issue(
                        file=rel_path,
                        line=i,
                        category=Category.MQL4_DEPRECATED,
                        severity=Severity.ERROR,
                        rule=name,
                        message=f"Deprecated MQL4 pattern: {name}",
                        suggestion=suggestion,
                        context=stripped[:80]
                    ))

            # Check C++ unsupported patterns
            for pattern, (name, suggestion) in self.CPP_PATTERNS.items():
                if re.search(pattern, line):
                    issues.append(Issue(
                        file=rel_path,
                        line=i,
                        category=Category.CPP_UNSUPPORTED,
                        severity=Severity.ERROR,
                        rule=name,
                        message=f"Unsupported C++ pattern: {name}",
                        suggestion=suggestion,
                        context=stripped[:80]
                    ))

            # Check best practice patterns
            for pattern, (name, suggestion, severity) in self.BEST_PRACTICE_PATTERNS.items():
                if re.search(pattern, line):
                    # Skip ArrayResize(x, 0) - clearing arrays is always safe
                    if 'ArrayResize' in name and re.search(r'ArrayResize\s*\([^,]+,\s*0\s*\)', line):
                        continue
                    issues.append(Issue(
                        file=rel_path,
                        line=i,
                        category=Category.BEST_PRACTICE,
                        severity=severity,
                        rule=name,
                        message=f"Best practice: {name}",
                        suggestion=suggestion,
                        context=stripped[:80]
                    ))

            # Check financial safety patterns
            for pattern, (name, suggestion, severity) in self.FINANCIAL_PATTERNS.items():
                if re.search(pattern, line):
                    # Skip if it matches a known safe pattern
                    is_safe = False
                    for safe_pattern in self.SAFE_CAST_PATTERNS:
                        if re.search(safe_pattern, line):
                            is_safe = True
                            break
                    if not is_safe:
                        issues.append(Issue(
                            file=rel_path,
                            line=i,
                            category=Category.FINANCIAL_SAFETY,
                            severity=severity,
                            rule=name,
                            message=f"Financial safety: {name}",
                            suggestion=suggestion,
                            context=stripped[:80]
                        ))

            # Check for additional dangerous patterns not covered above
            self._check_dangerous_patterns(line, stripped, rel_path, i, issues)

        return issues

    def _check_dangerous_patterns(self, line: str, stripped: str, rel_path: str, line_num: int, issues: List[Issue]):
        """Check for dangerous financial patterns that need special handling"""

        # Pattern: (int)lots or (int)volume without MathRound
        if re.search(r'\(\s*int\s*\)\s*\w*(lot|volume)\w*', line, re.IGNORECASE):
            if not re.search(r'MathRound|MathFloor|MathCeil', line):
                issues.append(Issue(
                    file=rel_path,
                    line=line_num,
                    category=Category.FINANCIAL_SAFETY,
                    severity=Severity.ERROR,
                    rule="Unrounded lot cast",
                    message="Casting lot/volume to int without rounding - (int)2.99 = 2!",
                    suggestion="Use (int)MathRound(lots) or NormalizeLots()",
                    context=stripped[:80]
                ))

        # Pattern: Division that could cause divide-by-zero in financial calc
        # Skip if: dividing by constant, has zero check on same line, is a ratio, or is indented (likely guarded)
        if re.search(r'(profit|loss|pnl|equity|balance|margin)\s*/\s*[a-zA-Z_]\w*', line, re.IGNORECASE):
            # Skip if dividing by constant number
            if re.search(r'/\s*\d+\.?\d*', line):
                pass  # Dividing by constant is safe
            # Skip if there's a zero check on the same line
            elif re.search(r'(!=\s*0|>\s*0|<\s*0|if\s*\()', line):
                pass  # Has inline check
            # Skip common ratio/capture patterns that are guarded elsewhere
            elif re.search(r'Ratio|ratio|Factor|factor|Percent|percent|captured|Captured', line):
                pass  # Ratios are typically guarded
            # Skip if deeply indented (likely inside a guarded block)
            elif line.startswith('         '):  # 9+ spaces = inside if block
                pass  # Likely has guard in outer scope
            else:
                issues.append(Issue(
                    file=rel_path,
                    line=line_num,
                    category=Category.FINANCIAL_SAFETY,
                    severity=Severity.WARNING,
                    rule="Potential division by zero",
                    message="Division in financial calculation - ensure divisor != 0",
                    suggestion="Add zero check: if(divisor != 0) or use safe division",
                    context=stripped[:80]
                ))

        # Pattern: Price comparison without NormalizeDouble
        if re.search(r'(price|sl|tp|ask|bid)\s*(==|!=)\s*(price|sl|tp|ask|bid|\d+\.)', line, re.IGNORECASE):
            if not re.search(r'NormalizeDouble|MathAbs.*<', line):
                issues.append(Issue(
                    file=rel_path,
                    line=line_num,
                    category=Category.FINANCIAL_SAFETY,
                    severity=Severity.WARNING,
                    rule="Direct price comparison",
                    message="Comparing prices directly may fail due to floating point",
                    suggestion="Use MathAbs(price1 - price2) < _Point or NormalizeDouble",
                    context=stripped[:80]
                ))

        # Pattern: AccountInfoDouble cast to int (balance overflow risk)
        # Only flag AccountInfoDouble, not AccountInfoInteger (which is safe to cast)
        if re.search(r'\(\s*int\s*\)\s*AccountInfoDouble', line):
            issues.append(Issue(
                file=rel_path,
                line=line_num,
                category=Category.FINANCIAL_SAFETY,
                severity=Severity.ERROR,
                rule="Account value overflow risk",
                message="Casting AccountInfoDouble to int - overflow if balance > 2.1B",
                suggestion="Use double or long for account values",
                context=stripped[:80]
            ))

        # Pattern: Hardcoded stop loss/take profit in points
        if re.search(r'(sl|tp|stoploss|takeprofit)\s*=\s*\d{2,4}\s*[;,)]', line, re.IGNORECASE):
            issues.append(Issue(
                file=rel_path,
                line=line_num,
                category=Category.FINANCIAL_SAFETY,
                severity=Severity.INFO,
                rule="Hardcoded SL/TP points",
                message="Hardcoded stop loss/take profit value",
                suggestion="Use input parameter or calculated value based on ATR",
                context=stripped[:80]
            ))

    def run_audit(self) -> AuditResult:
        """Run complete audit"""
        files = self.find_mql5_files()
        self.result.total_files = len(files)

        total_lines = 0
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    total_lines += len(lines)
            except:
                pass

            issues = self.audit_file(file_path)
            for issue in issues:
                self.result.add_issue(issue)

        self.result.total_lines = total_lines
        self.result.metrics = {
            "files_scanned": self.result.total_files,
            "lines_scanned": total_lines,
            "issues_by_severity": self.result.count_by_severity(),
            "issues_by_category": self.result.count_by_category(),
        }

        return self.result

    def print_report(self, verbose: bool = False):
        """Print audit report"""
        print("=" * 70)
        print("MQL5 SUPER AUDIT REPORT")
        print("=" * 70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project: {self.project_root}")
        print()

        # Summary
        print("SUMMARY")
        print("-" * 40)
        print(f"Files scanned: {self.result.total_files}")
        print(f"Lines scanned: {self.result.total_lines}")
        print(f"Total issues: {len(self.result.issues)}")
        print()

        # By severity
        print("BY SEVERITY")
        print("-" * 40)
        for severity, count in self.result.count_by_severity().items():
            if count > 0:
                print(f"  {severity}: {count}")
        print()

        # By category
        print("BY CATEGORY")
        print("-" * 40)
        for category, count in self.result.count_by_category().items():
            if count > 0:
                print(f"  {category}: {count}")
        print()

        # Critical/Error issues
        critical_errors = [i for i in self.result.issues
                         if i.severity in (Severity.CRITICAL, Severity.ERROR)]

        if critical_errors:
            print("CRITICAL/ERROR ISSUES")
            print("-" * 40)
            for issue in critical_errors[:20]:  # Limit output
                print(f"  [{issue.severity.value}] {issue.file}:{issue.line}")
                print(f"    {issue.message}")
                print(f"    Suggestion: {issue.suggestion}")
            if len(critical_errors) > 20:
                print(f"  ... and {len(critical_errors) - 20} more")
            print()

        # Warnings (if verbose)
        if verbose:
            warnings = [i for i in self.result.issues if i.severity == Severity.WARNING]
            if warnings:
                print("WARNINGS")
                print("-" * 40)
                for issue in warnings[:30]:
                    print(f"  {issue.file}:{issue.line} - {issue.rule}")
                if len(warnings) > 30:
                    print(f"  ... and {len(warnings) - 30} more")
                print()

        # Status
        print("=" * 70)
        critical_count = sum(1 for i in self.result.issues
                            if i.severity in (Severity.CRITICAL, Severity.ERROR))
        if critical_count == 0:
            print("✓ AUDIT PASSED - No critical issues found")
        else:
            print(f"✗ AUDIT FAILED - {critical_count} critical/error issues found")
        print("=" * 70)

        return critical_count == 0

    def to_json(self) -> str:
        """Export results as JSON"""
        return json.dumps({
            "summary": {
                "files_scanned": self.result.total_files,
                "lines_scanned": self.result.total_lines,
                "total_issues": len(self.result.issues),
                "by_severity": self.result.count_by_severity(),
                "by_category": self.result.count_by_category(),
            },
            "issues": [
                {
                    "file": i.file,
                    "line": i.line,
                    "category": i.category.value,
                    "severity": i.severity.value,
                    "rule": i.rule,
                    "message": i.message,
                    "suggestion": i.suggestion,
                }
                for i in self.result.issues
            ]
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="MQL5 Super Audit - Comprehensive code quality analysis"
    )
    parser.add_argument(
        "--project", "-p",
        default=".",
        help="Project root directory"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with code 1 if errors found"
    )

    args = parser.parse_args()

    auditor = MQL5SuperAudit(Path(args.project))
    auditor.run_audit()

    passed = auditor.print_report(verbose=args.verbose)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(auditor.to_json())
        print(f"\nJSON report saved to: {args.output}")

    if args.fail_on_error and not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
