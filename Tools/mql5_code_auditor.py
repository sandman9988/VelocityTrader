#!/usr/bin/env python3
"""
ProjectQuantum MQL5 Code Auditor
================================
Systematic, first-principles code auditing and refactoring tool.

Design Philosophy:
- Stanford/MIT-style rigorous engineering
- Cryptographic integrity verification (SHA256)
- Dependency-ordered processing
- Audit trail for every change
- Safe math validation
- Memory/array bounds checking

Author: ProjectQuantum Team
Version: 1.0.0
"""

import os
import re
import sys
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Optional
from enum import Enum, auto
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = auto()  # Compilation blocker
    ERROR = auto()     # Logic error, potential crash
    WARNING = auto()   # Bad practice, potential bug
    INFO = auto()      # Style, optimization opportunity


class IssueType(Enum):
    """Categorized issue types"""
    # Compilation Issues
    MISSING_INCLUDE = auto()
    UNDEFINED_TYPE = auto()
    UNDEFINED_SYMBOL = auto()
    SYNTAX_ERROR = auto()

    # Safety Issues
    DIVISION_BY_ZERO = auto()
    ARRAY_BOUNDS = auto()
    NULL_POINTER = auto()
    UNINITIALIZED_VAR = auto()
    MEMORY_LEAK = auto()

    # Math Issues
    UNSAFE_DIVISION = auto()
    OVERFLOW_RISK = auto()
    PRECISION_LOSS = auto()

    # MQL5 Specific
    MISSING_PROPERTY = auto()
    MISSING_BOM = auto()
    WRONG_ENCODING = auto()

    # Architecture
    CIRCULAR_DEPENDENCY = auto()
    MISSING_GUARD = auto()
    DUPLICATE_DEFINITION = auto()


@dataclass
class Issue:
    """Represents a single code issue"""
    file_path: str
    line: int
    column: int
    issue_type: IssueType
    severity: Severity
    message: str
    suggestion: str = ""
    context: str = ""  # Surrounding code

    def to_dict(self) -> dict:
        return {
            "file": self.file_path,
            "line": self.line,
            "column": self.column,
            "type": self.issue_type.name,
            "severity": self.severity.name,
            "message": self.message,
            "suggestion": self.suggestion,
            "context": self.context
        }


@dataclass
class FileAudit:
    """Audit record for a single file"""
    file_path: str
    sha256: str
    size_bytes: int
    line_count: int
    last_modified: str
    has_bom: bool
    encoding: str
    includes: List[str] = field(default_factory=list)
    defines: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    structs: List[str] = field(default_factory=list)
    enums: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d['issues'] = [i.to_dict() for i in self.issues]
        return d


@dataclass
class AuditReport:
    """Complete audit report"""
    timestamp: str
    project_root: str
    total_files: int
    total_lines: int
    files_with_issues: int
    issue_counts: Dict[str, int] = field(default_factory=dict)
    severity_counts: Dict[str, int] = field(default_factory=dict)
    file_audits: List[FileAudit] = field(default_factory=list)
    dependency_order: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d['file_audits'] = [f.to_dict() for f in self.file_audits]
        return d


class MQL5Parser:
    """
    MQL5 source code parser
    Extracts structure, dependencies, and potential issues
    """

    # MQL5 keywords for context
    KEYWORDS = {
        'void', 'int', 'double', 'float', 'string', 'bool', 'char',
        'short', 'long', 'uchar', 'ushort', 'uint', 'ulong', 'datetime',
        'color', 'class', 'struct', 'enum', 'interface', 'const',
        'static', 'virtual', 'override', 'public', 'private', 'protected',
        'input', 'sinput', 'template', 'typename', 'return', 'if', 'else',
        'for', 'while', 'do', 'switch', 'case', 'break', 'continue',
        'new', 'delete', 'true', 'false', 'NULL', 'EMPTY_VALUE'
    }

    # Built-in MQL5 types
    BUILTIN_TYPES = {
        'int', 'double', 'float', 'string', 'bool', 'char', 'short', 'long',
        'uchar', 'ushort', 'uint', 'ulong', 'datetime', 'color', 'void'
    }

    # Regex patterns
    PATTERNS = {
        'include': re.compile(r'#include\s*[<"]([^>"]+)[>"]'),
        'define': re.compile(r'#define\s+(\w+)'),
        'class': re.compile(r'class\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+(\w+))?'),
        'struct': re.compile(r'struct\s+(\w+)'),
        'enum': re.compile(r'enum\s+(\w+)'),
        'template_class': re.compile(r'template\s*<\s*typename\s+\w+\s*>\s*(?:class|struct)\s+(\w+)'),
        'function': re.compile(r'(?:^|\s)(\w+)\s+(\w+)\s*\([^)]*\)\s*(?:const\s*)?(?:\{|;)'),
        'division': re.compile(r'([^/])/([^/=*])'),  # Division operator (not // or /= or /*)
        'array_access': re.compile(r'(\w+)\s*\[([^\]]+)\]'),
        'property': re.compile(r'#property\s+(\w+)'),
        'ifndef_guard': re.compile(r'#ifndef\s+(\w+)'),
        'define_guard': re.compile(r'#define\s+(\w+)\s*$'),
    }

    def __init__(self):
        self.current_file = ""
        self.lines: List[str] = []

    def parse_file(self, file_path: Path) -> FileAudit:
        """Parse a single MQL5 file and extract metadata"""
        self.current_file = str(file_path)

        # Read file and compute hash
        try:
            with open(file_path, 'rb') as f:
                content_bytes = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied reading: {file_path}")
        except (IOError, OSError) as e:
            raise IOError(f"I/O error reading '{file_path}': {e}")

        sha256 = hashlib.sha256(content_bytes).hexdigest()
        size_bytes = len(content_bytes)

        # Check BOM
        has_bom = content_bytes.startswith(b'\xef\xbb\xbf')

        # Detect encoding with fallback chain
        content = None
        encoding = 'unknown'
        encodings_to_try = [
            ('utf-8-sig', 'utf-8'),
            ('utf-16', 'utf-16'),
            ('latin-1', 'latin-1'),
        ]
        for enc, enc_name in encodings_to_try:
            try:
                content = content_bytes.decode(enc)
                encoding = enc_name
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            # Last resort: decode with errors='replace'
            content = content_bytes.decode('utf-8', errors='replace')
            encoding = 'utf-8-lossy'
            logger.warning(f"File '{file_path}' has encoding issues, some characters replaced")

        self.lines = content.split('\n')
        line_count = len(self.lines)

        # Get file modification time
        try:
            mtime = os.path.getmtime(file_path)
            last_modified = datetime.fromtimestamp(mtime).isoformat()
        except (OSError, ValueError) as e:
            logger.warning(f"Could not get modification time for '{file_path}': {e}")
            last_modified = datetime.now().isoformat()

        # Create audit record
        audit = FileAudit(
            file_path=str(file_path),
            sha256=sha256,
            size_bytes=size_bytes,
            line_count=line_count,
            last_modified=last_modified,
            has_bom=has_bom,
            encoding=encoding
        )

        # Extract structure
        audit.includes = self._extract_includes(content)
        audit.defines = self._extract_defines(content)
        audit.classes = self._extract_classes(content)
        audit.structs = self._extract_structs(content)
        audit.enums = self._extract_enums(content)

        # Check for issues
        audit.issues = self._check_issues(content, audit)

        return audit

    def _extract_includes(self, content: str) -> List[str]:
        """Extract all #include directives"""
        return self.PATTERNS['include'].findall(content)

    def _extract_defines(self, content: str) -> List[str]:
        """Extract all #define directives"""
        return self.PATTERNS['define'].findall(content)

    def _extract_classes(self, content: str) -> List[str]:
        """Extract class definitions (including template classes)"""
        classes = []
        # Regular classes
        for match in self.PATTERNS['class'].finditer(content):
            classes.append(match.group(1))
        # Template classes
        for match in self.PATTERNS['template_class'].finditer(content):
            classes.append(match.group(1))
        return classes

    def _extract_structs(self, content: str) -> List[str]:
        """Extract struct definitions"""
        return self.PATTERNS['struct'].findall(content)

    def _extract_enums(self, content: str) -> List[str]:
        """Extract enum definitions"""
        return self.PATTERNS['enum'].findall(content)

    def _check_issues(self, content: str, audit: FileAudit) -> List[Issue]:
        """Check for various code issues"""
        issues = []

        # Check BOM for MQL5 (recommended)
        if not audit.has_bom and audit.file_path.endswith(('.mq5', '.mqh')):
            issues.append(Issue(
                file_path=audit.file_path,
                line=1,
                column=1,
                issue_type=IssueType.MISSING_BOM,
                severity=Severity.WARNING,
                message="MQL5 file missing UTF-8 BOM",
                suggestion="Add UTF-8 BOM (EF BB BF) at file start for better MT5 compatibility"
            ))

        # Check include guard
        if audit.file_path.endswith('.mqh'):
            issues.extend(self._check_include_guard(content, audit))

        # Check unsafe divisions
        issues.extend(self._check_unsafe_divisions(content, audit))

        # Check array accesses
        issues.extend(self._check_array_accesses(content, audit))

        # Check for #property strict
        if '#property strict' not in content:
            issues.append(Issue(
                file_path=audit.file_path,
                line=1,
                column=1,
                issue_type=IssueType.MISSING_PROPERTY,
                severity=Severity.WARNING,
                message="Missing #property strict directive",
                suggestion="Add '#property strict' for stricter type checking"
            ))

        return issues

    def _check_include_guard(self, content: str, audit: FileAudit) -> List[Issue]:
        """Check for proper include guards"""
        issues = []

        ifndef_matches = self.PATTERNS['ifndef_guard'].findall(content)

        if not ifndef_matches:
            issues.append(Issue(
                file_path=audit.file_path,
                line=1,
                column=1,
                issue_type=IssueType.MISSING_GUARD,
                severity=Severity.WARNING,
                message="Missing include guard (#ifndef)",
                suggestion="Add #ifndef FILENAME_MQH / #define FILENAME_MQH / #endif pattern"
            ))

        return issues

    def _check_unsafe_divisions(self, content: str, audit: FileAudit) -> List[Issue]:
        """Check for potential division by zero"""
        issues = []

        # Skip if SafeDiv is used consistently
        if 'SafeDiv' in content:
            return issues

        for i, line in enumerate(self.lines, 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('/*'):
                continue

            # Look for division operations not using SafeDiv
            if '/' in line and 'SafeDiv' not in line:
                # Simple heuristic: division by variable (not constant)
                div_matches = re.findall(r'/\s*([a-zA-Z_]\w*)', line)
                for var in div_matches:
                    if var not in ('0', '1', '2', '10', '100') and var not in self.KEYWORDS:
                        issues.append(Issue(
                            file_path=audit.file_path,
                            line=i,
                            column=line.find('/') + 1,
                            issue_type=IssueType.UNSAFE_DIVISION,
                            severity=Severity.WARNING,
                            message=f"Potential division by zero (variable: {var})",
                            suggestion="Use SafeDiv() or add zero-check before division",
                            context=line.strip()[:80]
                        ))
                        break  # One warning per line

        return issues

    def _check_array_accesses(self, content: str, audit: FileAudit) -> List[Issue]:
        """Check for potentially unsafe array accesses"""
        issues = []

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith('//'):
                continue

            # Find array accesses
            for match in self.PATTERNS['array_access'].finditer(line):
                array_name = match.group(1)
                index_expr = match.group(2)

                # Skip if it's a declaration or if bounds are checked nearby
                if 'ArrayResize' in line or 'ArraySize' in line:
                    continue

                # Flag accesses with complex expressions (potential OOB)
                if any(op in index_expr for op in ['+', '-', '*', '/']):
                    # Check if there's a bounds check in surrounding context
                    context_start = max(0, i - 3)
                    context_end = min(len(self.lines), i + 1)
                    context = '\n'.join(self.lines[context_start:context_end])

                    if f'ArraySize({array_name})' not in context and f'< ArraySize' not in context:
                        issues.append(Issue(
                            file_path=audit.file_path,
                            line=i,
                            column=match.start() + 1,
                            issue_type=IssueType.ARRAY_BOUNDS,
                            severity=Severity.INFO,
                            message=f"Array '{array_name}' access with computed index - verify bounds",
                            suggestion="Add bounds check: if(index >= 0 && index < ArraySize(arr))",
                            context=line.strip()[:80]
                        ))

        return issues


class DependencyResolver:
    """
    Resolves include dependencies and determines compilation order
    Detects circular dependencies
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.include_paths = [
            project_root / "MQL5" / "Include",
            project_root / "MQL5" / "Include" / "ProjectQuantum"
        ]
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)

    def build_dependency_graph(self, file_audits: List[FileAudit]) -> None:
        """Build dependency graph from file audits"""
        for audit in file_audits:
            file_key = self._normalize_path(audit.file_path)

            for include in audit.includes:
                include_key = self._normalize_include(include)
                self.graph[file_key].add(include_key)
                self.reverse_graph[include_key].add(file_key)

    def _normalize_path(self, path: str) -> str:
        """Normalize file path to relative key"""
        path = Path(path)
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            return str(path)

    def _normalize_include(self, include: str) -> str:
        """Normalize include path"""
        # Handle <> vs "" includes
        include = include.replace('\\', '/')

        # Try to find the actual file
        for base in self.include_paths:
            candidate = base / include
            if candidate.exists():
                return self._normalize_path(str(candidate))

        return include

    def get_topological_order(self) -> List[str]:
        """
        Get files in topological order (dependencies first)
        Uses Kahn's algorithm
        """
        # Calculate in-degrees
        in_degree = defaultdict(int)
        all_nodes = set(self.graph.keys()) | set(self.reverse_graph.keys())

        for node in all_nodes:
            in_degree[node] = len(self.graph.get(node, set()))

        # Start with nodes that have no dependencies
        queue = [n for n in all_nodes if in_degree[n] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree for dependents
            for dependent in self.reverse_graph.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for circular dependencies
        if len(result) < len(all_nodes):
            # Find nodes in cycles
            remaining = all_nodes - set(result)
            logger.warning(f"Circular dependency detected involving: {remaining}")

        return result

    def find_circular_dependencies(self) -> List[List[str]]:
        """Find all circular dependencies using DFS"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in self.graph:
            if node not in visited:
                dfs(node)

        return cycles


class MQL5CodeAuditor:
    """
    Main auditor class - orchestrates the audit process
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.parser = MQL5Parser()
        self.resolver = DependencyResolver(project_root)
        self.report: Optional[AuditReport] = None

    def audit(self, paths: Optional[List[Path]] = None) -> AuditReport:
        """
        Run full audit on project

        Args:
            paths: Specific paths to audit (default: all MQL5 files)
        """
        logger.info(f"Starting audit of {self.project_root}")

        # Find all MQL5 files
        if paths is None:
            try:
                paths = self._find_mql5_files()
            except (OSError, PermissionError) as e:
                logger.error(f"Error finding MQL5 files: {e}")
                paths = []

        if not paths:
            logger.warning("No MQL5 files found to audit")

        logger.info(f"Found {len(paths)} MQL5 files")

        # Parse each file
        file_audits = []
        total_lines = 0
        files_with_errors = 0

        for path in paths:
            try:
                audit = self.parser.parse_file(path)
                file_audits.append(audit)
                total_lines += audit.line_count

                issue_count = len(audit.issues)
                if issue_count > 0:
                    logger.info(f"  {path.name}: {issue_count} issues")

            except FileNotFoundError:
                files_with_errors += 1
                logger.warning(f"File not found: {path}")
            except PermissionError:
                files_with_errors += 1
                logger.warning(f"Permission denied: {path}")
            except (IOError, OSError) as e:
                files_with_errors += 1
                logger.error(f"I/O error parsing {path}: {e}")
            except Exception as e:
                files_with_errors += 1
                logger.error(f"Failed to parse {path}: {e}")

        if files_with_errors > 0:
            logger.warning(f"{files_with_errors} file(s) could not be parsed")

        # Build dependency graph
        self.resolver.build_dependency_graph(file_audits)
        dependency_order = self.resolver.get_topological_order()

        # Check for circular dependencies
        cycles = self.resolver.find_circular_dependencies()
        for cycle in cycles:
            logger.warning(f"Circular dependency: {' -> '.join(cycle)}")

        # Aggregate statistics
        issue_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        files_with_issues = 0

        for audit in file_audits:
            if audit.issues:
                files_with_issues += 1
            for issue in audit.issues:
                issue_counts[issue.issue_type.name] += 1
                severity_counts[issue.severity.name] += 1

        # Create report
        self.report = AuditReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            total_files=len(file_audits),
            total_lines=total_lines,
            files_with_issues=files_with_issues,
            issue_counts=dict(issue_counts),
            severity_counts=dict(severity_counts),
            file_audits=file_audits,
            dependency_order=dependency_order
        )

        return self.report

    def _find_mql5_files(self) -> List[Path]:
        """Find all MQL5 source files in project"""
        extensions = {'.mq5', '.mqh', '.mq4', '.mqt'}
        files = []

        mql5_dir = self.project_root / "MQL5"
        if mql5_dir.exists():
            for ext in extensions:
                files.extend(mql5_dir.rglob(f"*{ext}"))

        # Filter out backup files
        files = [f for f in files if '.backup' not in str(f)]

        return sorted(files)

    def save_report(self, output_path: Path) -> None:
        """Save audit report to JSON"""
        if self.report is None:
            raise ValueError("No audit report available. Run audit() first.")

        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.report.to_dict(), f, indent=2)
            logger.info(f"Report saved to {output_path}")
        except PermissionError:
            logger.error(f"Permission denied writing to: {output_path}")
            raise
        except (IOError, OSError) as e:
            logger.error(f"Failed to save report to '{output_path}': {e}")
            raise
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize report to JSON: {e}")
            raise

    def print_summary(self) -> None:
        """Print audit summary to console"""
        if self.report is None:
            raise ValueError("No audit report available. Run audit() first.")

        print("\n" + "=" * 70)
        print("MQL5 CODE AUDIT REPORT")
        print("=" * 70)
        print(f"Timestamp: {self.report.timestamp}")
        print(f"Project:   {self.report.project_root}")
        print("-" * 70)
        print(f"Total Files:        {self.report.total_files}")
        print(f"Total Lines:        {self.report.total_lines:,}")
        print(f"Files with Issues:  {self.report.files_with_issues}")
        print("-" * 70)

        if self.report.severity_counts:
            print("\nIssues by Severity:")
            for severity, count in sorted(self.report.severity_counts.items()):
                print(f"  {severity:12} : {count}")

        if self.report.issue_counts:
            print("\nIssues by Type:")
            for issue_type, count in sorted(self.report.issue_counts.items(),
                                           key=lambda x: x[1], reverse=True):
                print(f"  {issue_type:25} : {count}")

        print("=" * 70 + "\n")


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='MQL5 Code Auditor - Systematic code analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Audit entire project
  python mql5_code_auditor.py --project /path/to/ProjectQuantum

  # Audit and save report
  python mql5_code_auditor.py --project . --output audit_report.json

  # Audit specific files
  python mql5_code_auditor.py --project . --files Core.mqh CRL_Agent.mqh
        """
    )

    parser.add_argument('--project', type=Path, default=Path('.'),
                        help='Project root directory')
    parser.add_argument('--output', type=Path, default=None,
                        help='Output JSON report path')
    parser.add_argument('--files', nargs='+', type=str, default=None,
                        help='Specific files to audit')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Resolve project root
    try:
        project_root = args.project.resolve()
    except (OSError, ValueError) as e:
        logger.error(f"Invalid project path '{args.project}': {e}")
        return 2

    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        return 2
    if not project_root.is_dir():
        logger.error(f"Project path is not a directory: {project_root}")
        return 2

    try:
        # Run audit
        auditor = MQL5CodeAuditor(project_root)

        if args.files:
            # Audit specific files
            paths = []
            for f in args.files:
                try:
                    found = list(project_root.rglob(f))
                    if not found:
                        logger.warning(f"No files matching '{f}' found")
                    paths.extend(found)
                except (OSError, ValueError) as e:
                    logger.warning(f"Error searching for '{f}': {e}")
            if not paths:
                logger.error("No files found matching the specified patterns")
                return 2
            report = auditor.audit(paths)
        else:
            report = auditor.audit()

        # Print summary
        auditor.print_summary()

        # Save report if requested
        if args.output:
            try:
                auditor.save_report(args.output)
            except (PermissionError, IOError, OSError) as e:
                logger.error(f"Failed to save report: {e}")
                return 2

        # Return error code if critical issues found
        if report.severity_counts.get('CRITICAL', 0) > 0:
            return 1

        return 0

    except KeyboardInterrupt:
        logger.info("Audit interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error during audit: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
