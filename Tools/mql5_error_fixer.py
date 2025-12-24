#!/usr/bin/env python3
"""
ProjectQuantum MQL5 Error Fixer
===============================
Systematic compiler error parser and fixer with audit trail.

Workflow:
1. Parse MT5 compiler output
2. Categorize errors by type
3. Identify root cause files (dependency order)
4. Generate fix plan
5. Apply fixes with audit trail
6. Verify fixes

Author: ProjectQuantum Team
Version: 1.0.0
"""

import os
import re
import sys
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from enum import Enum
from collections import defaultdict
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categorized compiler error types"""
    UNDEFINED_TYPE = "undefined_type"
    UNDEFINED_SYMBOL = "undefined_symbol"
    SYNTAX_ERROR = "syntax_error"
    MISSING_SEMICOLON = "missing_semicolon"
    UNEXPECTED_TOKEN = "unexpected_token"
    TYPE_MISMATCH = "type_mismatch"
    DECLARATION_ERROR = "declaration_error"
    REFERENCE_ERROR = "reference_error"
    EXPRESSION_ERROR = "expression_error"
    MODIFIER_ERROR = "modifier_error"
    OTHER = "other"


@dataclass
class CompilerError:
    """Parsed compiler error"""
    file: str
    line: int
    column: int
    error_code: str
    message: str
    category: ErrorCategory
    context: str = ""

    # For tracking
    root_cause: Optional[str] = None  # The symbol/type causing the error
    depends_on: Optional[str] = None  # File that should define it


@dataclass
class FixAction:
    """A single fix action"""
    file: str
    line: int
    action_type: str  # 'add_include', 'add_definition', 'fix_syntax', etc.
    description: str
    old_content: str
    new_content: str
    applied: bool = False


@dataclass
class FixPlan:
    """Plan for fixing errors"""
    timestamp: str
    total_errors: int
    error_categories: Dict[str, int]
    affected_files: List[str]
    fix_order: List[str]  # Files in order they should be fixed
    actions: List[FixAction]
    audit_log: List[str] = field(default_factory=list)


class MT5ErrorParser:
    """
    Parses MetaTrader 5 compiler output
    """

    # Error message patterns
    ERROR_PATTERNS = {
        # 'symbol' - unexpected token, probably type is missing?
        'unexpected_token_type': re.compile(
            r"'(\w+)'\s*-\s*unexpected token,?\s*(?:probably\s+)?type\s+(?:is\s+)?missing"
        ),
        # 'symbol' - semicolon expected
        'missing_semicolon': re.compile(
            r"'(\w+)'\s*-\s*semicolon expected"
        ),
        # '<' - semicolon expected (template issues)
        'template_semicolon': re.compile(
            r"'<'\s*-\s*semicolon expected"
        ),
        # undeclared identifier
        'undeclared_identifier': re.compile(
            r"undeclared identifier"
        ),
        # declaration without type
        'declaration_no_type': re.compile(
            r"declaration without type"
        ),
        # reference cannot be initialized
        'reference_error': re.compile(
            r"reference cannot be initialized"
        ),
        # '&' - comma expected
        'ampersand_comma': re.compile(
            r"'&'\s*-\s*comma expected"
        ),
        # expression errors
        'expression_error': re.compile(
            r"expressions?\s+(?:are\s+)?not\s+(?:allowed|expected|boolean)"
        ),
        # modifier errors
        'modifier_error': re.compile(
            r"'const'\s+modifier\s+not\s+allowed"
        ),
        # operand expected
        'operand_expected': re.compile(
            r"operand expected"
        ),
        # object pointer expected
        'pointer_expected': re.compile(
            r"object pointer expected"
        ),
        # cannot convert
        'type_mismatch': re.compile(
            r"cannot convert"
        ),
    }

    # Line pattern: file.mqh line col
    LINE_PATTERN = re.compile(
        r"^(.+?\.mq[h5])\s+(\d+)\s+(\d+)\s*$"
    )

    # Error line pattern: 'message' or just message
    ERROR_LINE_PATTERN = re.compile(
        r"^(.+?\.mq[h5])\s+(\d+)\s+(\d+)\s*$|^'?(.+?)'?\s+-\s+(.+)$|^(.+)$"
    )

    def parse_errors(self, compiler_output: str) -> List[CompilerError]:
        """Parse MT5 compiler output into structured errors"""
        errors = []
        lines = compiler_output.strip().split('\n')

        current_file = ""
        current_line = 0
        current_col = 0

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and header info
            if not line or line.startswith('//') or '\t\t\t' in line:
                i += 1
                continue

            # Check if this is a file reference line
            parts = line.split('\t')
            if len(parts) >= 2:
                # Format: message \t file \t line \t col
                # or: file \t line \t col (from previous error context)

                # Try to parse as error with location
                try:
                    # Look for tab-separated file location at end
                    if parts[-1].isdigit() and len(parts) >= 3:
                        current_col = int(parts[-1])
                        current_line = int(parts[-2])
                        current_file = parts[-3].strip()
                        message = '\t'.join(parts[:-3]).strip() if len(parts) > 3 else ""

                        if message and current_file:
                            error = self._create_error(
                                current_file, current_line, current_col, message
                            )
                            if error:
                                errors.append(error)
                except (ValueError, IndexError):
                except (ValueError, IndexError) as e:
                    # Malformed compiler output line; skip but log at debug level for diagnostics.
                    logging.debug(
                        "Skipping unparsable compiler output line %r due to %s", line, e
                    )

            i += 1

        return errors

    def parse_errors_simple(self, text: str) -> List[CompilerError]:
        """
        Parse simplified error format:
        'message' \t file \t line \t col
        or
        message \t file \t line \t col

        Uses robust regex to handle file paths with spaces.
        """
        errors = []

        # Regex to capture message, file path (with possible spaces), line, and column
        # File path must end with .mq5 or .mqh
        pattern = re.compile(r"^(.*?)\t(.*?\.mq[h5])\t(\d+)\t(\d+)$")

        for line in text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            # Try regex match first (handles paths with spaces)
            match = pattern.match(line)
            if match:
                message, file, line_no_str, col_str = match.groups()
                message = message.strip().strip("'")
                try:
                    line_no = int(line_no_str)
                    col = int(col_str)
                    error = self._create_error(file, line_no, col, message)
                    if error:
                        errors.append(error)
                except ValueError:
                    continue
            elif '\t' in line:
                # Fallback for less structured errors
                parts = line.split('\t')
                if len(parts) >= 2:
                    message = parts[0].strip().strip("'")
                    file_candidate = parts[1].strip()
                    if '.mq' in file_candidate:
                        error = self._create_error(file_candidate, 0, 0, message)
                        if error:
                            errors.append(error)

        return errors

    def _create_error(self, file: str, line: int, col: int, message: str) -> Optional[CompilerError]:
        """Create a CompilerError from parsed components"""
        if not file or not message:
            return None

        # Categorize the error
        category = ErrorCategory.OTHER
        root_cause = None

        # Check patterns
        for pattern_name, pattern in self.ERROR_PATTERNS.items():
            match = pattern.search(message)
            if match:
                if pattern_name == 'unexpected_token_type':
                    category = ErrorCategory.UNDEFINED_TYPE
                    root_cause = match.group(1) if match.groups() else None
                elif pattern_name in ('missing_semicolon', 'template_semicolon'):
                    category = ErrorCategory.MISSING_SEMICOLON
                    root_cause = match.group(1) if match.groups() else None
                elif pattern_name == 'undeclared_identifier':
                    category = ErrorCategory.UNDEFINED_SYMBOL
                elif pattern_name in ('declaration_no_type', 'ampersand_comma'):
                    category = ErrorCategory.DECLARATION_ERROR
                elif pattern_name == 'reference_error':
                    category = ErrorCategory.REFERENCE_ERROR
                elif pattern_name in ('expression_error', 'operand_expected'):
                    category = ErrorCategory.EXPRESSION_ERROR
                elif pattern_name == 'modifier_error':
                    category = ErrorCategory.MODIFIER_ERROR
                elif pattern_name in ('pointer_expected', 'type_mismatch'):
                    category = ErrorCategory.TYPE_MISMATCH
                break

        return CompilerError(
            file=file,
            line=line,
            column=col,
            error_code="",
            message=message,
            category=category,
            root_cause=root_cause
        )


class ErrorAnalyzer:
    """
    Analyzes errors to find root causes and fix order
    """

    # Known type definitions and their source files
    TYPE_SOURCES = {
        # Enums
        'ENUM_REGIME': 'Architecture/Project_Quantum.mqh',
        'ENUM_TRADING_ACTION': 'Architecture/Project_Quantum.mqh',
        'ENUM_SYSTEM_STATE': 'Architecture/Project_Quantum.mqh',
        'ENUM_CIRCUIT_LEVEL': 'Architecture/Project_Quantum.mqh',
        'ENUM_INSTRUMENT_CLASS': 'Architecture/Project_Quantum.mqh',
        'ENUM_SESSION_TYPE': 'Architecture/Project_Quantum.mqh',

        # Structs
        'SStateVector': 'Architecture/Project_Quantum.mqh',
        'SProbabilityPrediction': 'Architecture/Project_Quantum.mqh',
        'SJourneyTrade': 'Architecture/Project_Quantum.mqh',
        'SProjectQuantumTrade': 'Architecture/ProjectQuantum_Architecture.mqh',
        'SSessionMetrics': 'Architecture/Project_Quantum.mqh',
        'SCumulativeMetrics': 'Architecture/Project_Quantum.mqh',
        'SSystemHealth': 'Architecture/Project_Quantum.mqh',
        'STradeMetrics': 'Intelligence/CJourneyReward.mqh',

        # Template classes
        'CHashTable': 'Core/Core.mqh',
        'CRingBuffer': 'Core/Core.mqh',
        'CObjectPool': 'Core/Core.mqh',
        'SHashEntry': 'Core/Core.mqh',

        # Core classes
        'CCore': 'Core/Core.mqh',
        'CLogger': 'Core/CLogger.mqh',
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.include_base = project_root / "MQL5" / "Include" / "ProjectQuantum"

    def analyze(self, errors: List[CompilerError]) -> Dict[str, Any]:
        """Analyze errors to determine root causes"""

        # Group errors by file
        by_file: Dict[str, List[CompilerError]] = defaultdict(list)
        for error in errors:
            by_file[error.file].append(error)

        # Group by category
        by_category: Dict[ErrorCategory, List[CompilerError]] = defaultdict(list)
        for error in errors:
            by_category[error.category].append(error)

        # Find undefined types/symbols
        undefined_types: Set[str] = set()
        for error in errors:
            if error.category == ErrorCategory.UNDEFINED_TYPE and error.root_cause:
                undefined_types.add(error.root_cause)

        # Map undefined types to their source files
        missing_includes: Dict[str, Set[str]] = defaultdict(set)  # file -> needed includes
        for error in errors:
            if error.root_cause and error.root_cause in self.TYPE_SOURCES:
                source_file = self.TYPE_SOURCES[error.root_cause]
                missing_includes[error.file].add(source_file)

        # Determine fix order (files with most dependents first)
        fix_order = self._calculate_fix_order(by_file, missing_includes)

        return {
            'total_errors': len(errors),
            'errors_by_file': {k: len(v) for k, v in by_file.items()},
            'errors_by_category': {k.value: len(v) for k, v in by_category.items()},
            'undefined_types': list(undefined_types),
            'missing_includes': {k: list(v) for k, v in missing_includes.items()},
            'fix_order': fix_order,
            'root_cause_files': self._identify_root_cause_files(by_category)
        }

    def _calculate_fix_order(self, by_file: Dict, missing_includes: Dict) -> List[str]:
        """Calculate optimal order to fix files"""

        # Architecture files first (define base types)
        architecture_files = []
        core_files = []
        other_files = []

        for file in by_file.keys():
            if 'Architecture' in file:
                architecture_files.append(file)
            elif 'Core' in file:
                core_files.append(file)
            else:
                other_files.append(file)

        # Sort each group by error count (fewer errors = likely root cause)
        architecture_files.sort(key=lambda f: len(by_file[f]))
        core_files.sort(key=lambda f: len(by_file[f]))
        other_files.sort(key=lambda f: len(by_file[f]))

        return architecture_files + core_files + other_files

    def _identify_root_cause_files(self, by_category: Dict) -> List[str]:
        """Identify files that are likely root causes"""

        root_files = set()

        # Undefined type errors point to missing definitions
        for error in by_category.get(ErrorCategory.UNDEFINED_TYPE, []):
            if error.root_cause and error.root_cause in self.TYPE_SOURCES:
                source = self.TYPE_SOURCES[error.root_cause]
                root_files.add(source)

        return list(root_files)


class FixGenerator:
    """
    Generates fix actions for errors
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.include_base = project_root / "MQL5" / "Include" / "ProjectQuantum"

    def generate_plan(self, errors: List[CompilerError], analysis: Dict) -> FixPlan:
        """Generate a fix plan from errors and analysis"""

        actions = []

        # Generate include fixes
        for file, includes in analysis.get('missing_includes', {}).items():
            for include in includes:
                action = FixAction(
                    file=file,
                    line=1,
                    action_type='add_include',
                    description=f"Add missing include: {include}",
                    old_content="",
                    new_content=f'#include "{include}"'
                )
                actions.append(action)

        # Generate type definition stubs for unknown types
        undefined = analysis.get('undefined_types', [])
        known_types = set(ErrorAnalyzer.TYPE_SOURCES.keys())
        unknown_types = [t for t in undefined if t not in known_types]

        if unknown_types:
            logger.warning(f"Unknown types (may need manual definition): {unknown_types}")

        plan = FixPlan(
            timestamp=datetime.now().isoformat(),
            total_errors=len(errors),
            error_categories=analysis.get('errors_by_category', {}),
            affected_files=list(analysis.get('errors_by_file', {}).keys()),
            fix_order=analysis.get('fix_order', []),
            actions=actions
        )

        return plan


class AuditTrail:
    """
    Maintains audit trail for all changes
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.audit_dir = project_root / "Tools" / "audit_logs"
        self.audit_dir.mkdir(exist_ok=True)
        self.current_log: List[Dict] = []

    def log_file_state(self, file_path: Path, action: str) -> Dict:
        """Log current state of a file"""

        with open(file_path, 'rb') as f:
            content = f.read()

        entry = {
            'timestamp': datetime.now().isoformat(),
            'file': str(file_path),
            'action': action,
            'sha256': hashlib.sha256(content).hexdigest(),
            'size': len(content),
            'lines': content.count(b'\n')
        }

        self.current_log.append(entry)
        return entry

    def create_backup(self, file_path: Path) -> Path:
        """Create timestamped backup of file"""

        backup_dir = self.audit_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_name

        shutil.copy2(file_path, backup_path)

        logger.info(f"Backup created: {backup_path}")
        return backup_path

    def save_log(self, name: str = "audit") -> Path:
        """Save current audit log"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = self.audit_dir / f"{name}_{timestamp}.json"

        with open(log_path, 'w') as f:
            json.dump(self.current_log, f, indent=2)

        logger.info(f"Audit log saved: {log_path}")
        return log_path


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='MQL5 Error Fixer - Systematic error fixing with audit trail'
    )

    parser.add_argument('--project', type=Path, default=Path('.'),
                        help='Project root directory')
    parser.add_argument('--errors', type=Path,
                        help='File containing compiler errors')
    parser.add_argument('--analyze-only', action='store_true',
                        help='Only analyze, do not fix')
    parser.add_argument('--output', type=Path,
                        help='Output fix plan to JSON')

    args = parser.parse_args()

    project_root = args.project.resolve()

    # Read errors
    if args.errors:
        with open(args.errors, 'r', encoding='utf-8') as f:
            error_text = f.read()
    else:
        print("Paste compiler errors (Ctrl+D when done):")
        error_text = sys.stdin.read()

    # Parse errors
    error_parser = MT5ErrorParser()
    errors = error_parser.parse_errors_simple(error_text)

    if not errors:
        # Try alternative parsing
        errors = error_parser.parse_errors(error_text)

    print(f"\nParsed {len(errors)} errors")

    # Analyze
    analyzer = ErrorAnalyzer(project_root)
    analysis = analyzer.analyze(errors)

    print("\n" + "=" * 60)
    print("ERROR ANALYSIS")
    print("=" * 60)
    print(f"Total errors: {analysis['total_errors']}")
    print(f"\nBy category:")
    for cat, count in sorted(analysis['errors_by_category'].items(),
                            key=lambda x: x[1], reverse=True):
        print(f"  {cat:25} : {count}")

    print(f"\nUndefined types ({len(analysis['undefined_types'])}):")
    for t in sorted(analysis['undefined_types']):
        source = ErrorAnalyzer.TYPE_SOURCES.get(t, "UNKNOWN")
        print(f"  {t:30} -> {source}")

    print(f"\nRoot cause files:")
    for f in analysis['root_cause_files']:
        print(f"  {f}")

    print(f"\nRecommended fix order:")
    for i, f in enumerate(analysis['fix_order'][:10], 1):
        print(f"  {i}. {f}")

    if args.analyze_only:
        return 0

    # Generate fix plan
    fixer = FixGenerator(project_root)
    plan = fixer.generate_plan(errors, analysis)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                'analysis': analysis,
                'plan': {
                    'timestamp': plan.timestamp,
                    'total_errors': plan.total_errors,
                    'fix_order': plan.fix_order,
                    'actions': [vars(a) for a in plan.actions]
                }
            }, f, indent=2)
        print(f"\nFix plan saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
