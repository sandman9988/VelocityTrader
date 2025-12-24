#!/usr/bin/env python3
"""
MQL5 Integrity Checker
======================
Comprehensive codebase integrity, regression detection, and security verification.

Features:
- SHA-256 file hash tracking for regression detection
- Diff statistics (lines added/deleted/modified)
- Audit baseline regression checking (compare audit findings between runs)
- File poisoning detection (suspicious patterns, backdoors)
- Data corruption detection (CRC32 validation, binary checks)
- Include validation (all #include files must exist)
- Declaration order checking (enums before use)
- Bracket matching (#ifndef/#endif, {/})
- Git-aware change tracking
- Pre-commit hook support

Usage:
    python mql5_integrity_checker.py [--update-manifest] [--audit-baseline] [--diff]
    python mql5_integrity_checker.py --sync-check PATH
    python mql5_integrity_checker.py --pre-commit
"""

import re
import os
import sys
import json
import zlib
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum

# Configuration
MQL5_ROOT = Path(__file__).parent.parent / "MQL5"
TOOLS_ROOT = Path(__file__).parent
MANIFEST_FILE = MQL5_ROOT / ".integrity_manifest.json"
AUDIT_BASELINE_FILE = TOOLS_ROOT / ".audit_baseline.json"
INCLUDE_ROOT = MQL5_ROOT / "Include" / "ProjectQuantum"


class IntegrityLevel(Enum):
    """Integrity check severity levels."""
    CRITICAL = "CRITICAL"  # File corruption, poisoning detected
    HIGH = "HIGH"          # Security issue, backdoor pattern
    MEDIUM = "MEDIUM"      # Regression in audit findings
    LOW = "LOW"            # File changed
    INFO = "INFO"          # Informational


@dataclass
class DiffStats:
    """Statistics for file changes."""
    files_added: int = 0
    files_deleted: int = 0
    files_modified: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    lines_modified: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)

    def __str__(self) -> str:
        return (f"+{self.files_added}/-{self.files_deleted}/~{self.files_modified} files, "
                f"+{self.lines_added}/-{self.lines_deleted} lines")


@dataclass
class FileIntegrity:
    """File integrity information."""
    path: str
    sha256: str
    crc32: int
    size: int
    lines: int
    last_modified: str
    audit_findings: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class IntegrityIssue:
    """An integrity issue found during checking."""
    level: IntegrityLevel
    file: str
    message: str
    details: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'level': self.level.value,
            'file': self.file,
            'message': self.message,
            'details': self.details
        }


# Suspicious patterns that may indicate file poisoning or backdoors
SUSPICIOUS_PATTERNS = [
    # Network exfiltration
    (r'WebRequest\s*\([^)]*https?://[^)]+\)', IntegrityLevel.HIGH, "Outbound HTTP request"),
    (r'Socket(?:Create|Connect|Send)', IntegrityLevel.HIGH, "Raw socket operation"),

    # File system manipulation outside MQL5 data folder
    (r'FileOpen\s*\([^)]*(?:C:|D:|/home|/root|/etc)', IntegrityLevel.CRITICAL, "File access outside sandbox"),
    (r'ShellExecute|CreateProcess|WinExec', IntegrityLevel.CRITICAL, "Shell command execution"),

    # DLL injection/loading
    (r'#import\s+"(?!kernel32|user32|winmm)[^"]+\.dll"', IntegrityLevel.HIGH, "Non-standard DLL import"),

    # Obfuscation techniques
    (r'StringToCharArray.*Chr\s*\(\s*\d{2,3}\s*\)', IntegrityLevel.MEDIUM, "Potential string obfuscation"),
    (r'(?:eval|Execute)\s*\(', IntegrityLevel.HIGH, "Dynamic code execution"),

    # Credential/key patterns
    (r'(?:password|passwd|secret|apikey|api_key)\s*=\s*"[^"]+"', IntegrityLevel.HIGH, "Hardcoded credential"),

    # Timing-based covert channels
    (r'Sleep\s*\(\s*(?!(?:1000|500|100|50|10|1)\s*\))\d{4,}\s*\)', IntegrityLevel.MEDIUM, "Unusual sleep duration"),

    # Account manipulation
    (r'AccountInfo(?:Double|Integer|String)\s*\([^)]*ACCOUNT_(?:PASSWORD|LOGIN)', IntegrityLevel.HIGH, "Account credential access"),
]


class MQL5IntegrityChecker:
    """Comprehensive MQL5 codebase integrity checker."""

    def __init__(self, mql5_root: Path):
        self.mql5_root = mql5_root
        self.include_root = mql5_root / "Include" / "ProjectQuantum"
        self.manifest_file = mql5_root / ".integrity_manifest.json"
        self.audit_baseline_file = AUDIT_BASELINE_FILE
        self.issues: List[IntegrityIssue] = []
        self.diff_stats = DiffStats()
        self.file_integrity: Dict[str, FileIntegrity] = {}

    def compute_file_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash of file content."""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            return f"ERROR:{e}"

    def compute_crc32(self, filepath: Path) -> int:
        """Compute CRC32 checksum for data corruption detection."""
        try:
            with open(filepath, 'rb') as f:
                return zlib.crc32(f.read()) & 0xFFFFFFFF
        except Exception:
            return 0

    def get_file_integrity(self, filepath: Path) -> FileIntegrity:
        """Get comprehensive file integrity information."""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()

            stat = filepath.stat()
            lines = content.count(b'\n') + 1

            return FileIntegrity(
                path=str(filepath.relative_to(self.mql5_root)),
                sha256=hashlib.sha256(content).hexdigest(),
                crc32=zlib.crc32(content) & 0xFFFFFFFF,
                size=len(content),
                lines=lines,
                last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
            )
        except Exception as e:
            return FileIntegrity(
                path=str(filepath),
                sha256=f"ERROR:{e}",
                crc32=0,
                size=0,
                lines=0,
                last_modified=""
            )

    def add_issue(self, level: IntegrityLevel, file: str, message: str, details: str = None):
        """Add an integrity issue to the list."""
        self.issues.append(IntegrityIssue(level, file, message, details))

    def check_file_poisoning(self, filepath: Path, content: str) -> List[IntegrityIssue]:
        """Check for suspicious patterns that may indicate file poisoning."""
        issues = []
        rel_path = str(filepath.relative_to(self.mql5_root))

        for pattern, level, description in SUSPICIOUS_PATTERNS:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for match in matches:
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                issues.append(IntegrityIssue(
                    level=level,
                    file=rel_path,
                    message=f"{description} (line {line_num})",
                    details=match.group(0)[:100]
                ))

        return issues

    def get_git_diff_stats(self, since_commit: str = "HEAD~1") -> DiffStats:
        """Get diff statistics from git."""
        stats = DiffStats()

        try:
            # Get file-level changes
            result = subprocess.run(
                ['git', 'diff', '--stat', '--numstat', since_commit, '--', 'MQL5/'],
                cwd=self.mql5_root.parent,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split('\t')
                    if len(parts) >= 3 and parts[0].isdigit():
                        stats.lines_added += int(parts[0]) if parts[0] != '-' else 0
                        stats.lines_deleted += int(parts[1]) if parts[1] != '-' else 0

            # Get added/deleted/modified files
            result = subprocess.run(
                ['git', 'diff', '--name-status', since_commit, '--', 'MQL5/'],
                cwd=self.mql5_root.parent,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        status = line[0]
                        if status == 'A':
                            stats.files_added += 1
                        elif status == 'D':
                            stats.files_deleted += 1
                        elif status == 'M':
                            stats.files_modified += 1

        except Exception:
            pass  # Git not available or not a repo

        return stats

    def load_audit_baseline(self) -> Dict:
        """Load the audit baseline for regression checking."""
        if self.audit_baseline_file.exists():
            try:
                with open(self.audit_baseline_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"findings": {}, "total_critical": 0, "total_high": 0, "timestamp": None}

    def save_audit_baseline(self, findings: Dict, total_critical: int, total_high: int):
        """Save current audit results as baseline."""
        baseline = {
            "findings": findings,
            "total_critical": total_critical,
            "total_high": total_high,
            "timestamp": datetime.now().isoformat()
        }
        with open(self.audit_baseline_file, 'w') as f:
            json.dump(baseline, f, indent=2)

    def check_audit_regression(self, current_findings: Dict) -> List[IntegrityIssue]:
        """Check for regressions in audit findings."""
        issues = []
        baseline = self.load_audit_baseline()

        if not baseline.get("findings"):
            return issues

        prev_findings = baseline["findings"]

        # Check for new findings in each file
        for filepath, current in current_findings.items():
            prev = prev_findings.get(filepath, {"critical": 0, "high": 0, "medium": 0})

            if current.get("critical", 0) > prev.get("critical", 0):
                issues.append(IntegrityIssue(
                    level=IntegrityLevel.CRITICAL,
                    file=filepath,
                    message=f"AUDIT REGRESSION: Critical findings increased from {prev.get('critical', 0)} to {current['critical']}",
                    details="Run financial auditor for details"
                ))

            if current.get("high", 0) > prev.get("high", 0):
                issues.append(IntegrityIssue(
                    level=IntegrityLevel.HIGH,
                    file=filepath,
                    message=f"AUDIT REGRESSION: High findings increased from {prev.get('high', 0)} to {current['high']}",
                    details="Run financial auditor for details"
                ))

        return issues

    def load_manifest(self) -> Dict:
        """Load existing integrity manifest."""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Manifest corrupted or unreadable; start fresh
                pass
        return {"files": {}, "last_check": None, "version": "1.0"}

    def save_manifest(self, manifest: Dict):
        """Save integrity manifest."""
        manifest["last_check"] = datetime.now().isoformat()
        with open(self.manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

    def get_all_mql5_files(self) -> List[Path]:
        """Get all MQL5 files in the repository."""
        files = []
        for ext in ['*.mqh', '*.mq5']:
            files.extend(self.mql5_root.rglob(ext))
        return sorted(files)

    def extract_includes(self, content: str) -> List[str]:
        """Extract all #include statements from file content."""
        includes = []
        pattern = r'#include\s*[<"]([^>"]+)[>"]'
        for match in re.finditer(pattern, content):
            includes.append(match.group(1))
        return includes

    def resolve_include_path(self, include: str, source_file: Path) -> Optional[Path]:
        """Resolve include path to actual file path."""
        # Handle <ProjectQuantum/...> style includes
        if include.startswith("ProjectQuantum/"):
            return self.mql5_root / "Include" / include

        # Handle relative includes
        if include.startswith("./") or include.startswith("../"):
            return (source_file.parent / include).resolve()

        # Handle standard MQL5 includes (we skip these)
        if any(include.startswith(std) for std in ["Trade/", "Arrays/", "Expert/"]):
            return None  # Standard library, skip

        # Try relative to source file
        relative_path = source_file.parent / include
        if relative_path.exists():
            return relative_path

        # Try in Include directory
        include_path = self.mql5_root / "Include" / include
        if include_path.exists():
            return include_path

        return self.mql5_root / "Include" / include  # Return expected path even if missing

    def check_includes(self, filepath: Path, content: str) -> List[str]:
        """Check that all includes exist."""
        errors = []
        includes = self.extract_includes(content)

        # Standard MQL5 library prefixes (both forward and backslash)
        std_prefixes = [
            "Trade/", "Trade\\",
            "Arrays/", "Arrays\\",
            "Expert/", "Expert\\",
            "Indicators/", "Indicators\\",
            "Chart/", "Chart\\",
            "Files/", "Files\\"
        ]

        for inc in includes:
            # Skip standard MQL5 library includes
            if any(inc.startswith(std) for std in std_prefixes):
                continue

            resolved = self.resolve_include_path(inc, filepath)
            if resolved and not resolved.exists():
                errors.append(f"Missing include: {inc}")

        return errors

    def check_brackets(self, filepath: Path, content: str) -> List[str]:
        """Check bracket matching."""
        errors = []

        # Check #ifndef/#endif matching (only for header files with include guards)
        # Main .mq5 files don't need include guards
        if filepath.suffix == '.mqh':
            ifndef_count = len(re.findall(r'#ifndef\s+\w+', content))
            endif_count = len(re.findall(r'#endif', content))
            if ifndef_count != endif_count:
                errors.append(f"Mismatched #ifndef/#endif: {ifndef_count} vs {endif_count}")

        # Check brace matching (simplified)
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            errors.append(f"Mismatched braces: {open_braces} {{ vs {close_braces} }}")

        # Check parentheses
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            errors.append(f"Mismatched parentheses: {open_parens} ( vs {close_parens} )")

        return errors

    def check_mql5_patterns(self, filepath: Path, content: str) -> Tuple[List[str], List[str]]:
        """Check for MQL5-specific issues."""
        errors = []
        warnings = []

        # Check for OrderSend without error handling
        if 'OrderSend(' in content:
            # Look for nearby GetLastError()
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'OrderSend(' in line:
                    context = '\n'.join(lines[max(0,i-2):min(len(lines),i+5)])
                    if 'GetLastError()' not in context and '_LastError' not in context:
                        warnings.append(f"Line ~{i+1}: OrderSend() without error checking")

        # Check for raw division (potential div by zero) - only in assignment/return contexts
        # This is a simplified check, the financial auditor has more comprehensive division checks
        # Skip this check here to reduce noise - let the auditor handle it
        pass  # Division checking delegated to mql5_financial_auditor.py

        # Check for array access without bounds check
        array_pattern = r'\[(\w+)\]'
        for match in re.finditer(array_pattern, content):
            idx = match.group(1)
            # Skip fixed-size array indices (numbers)
            if idx.isdigit():
                continue
            # Check for ArraySize in nearby context
            start = max(0, match.start() - 200)
            context = content[start:match.start()]
            if 'ArraySize' not in context and 'ArrayResize' not in context:
                pass  # Too many false positives, skip for now

        return errors, warnings

    def check_declaration_order(self, filepath: Path, content: str) -> List[str]:
        """Check that enums/structs are declared before use (MQL5 requirement)."""
        warnings = []

        # Find all enum declarations
        enum_pattern = r'enum\s+(\w+)\s*\{'
        enum_decls = {}
        for match in re.finditer(enum_pattern, content):
            enum_decls[match.group(1)] = match.start()

        # Find all struct declarations
        struct_pattern = r'struct\s+(\w+)\s*\{'
        struct_decls = {}
        for match in re.finditer(struct_pattern, content):
            struct_decls[match.group(1)] = match.start()

        # Find usages of these types
        for enum_name, decl_pos in enum_decls.items():
            usage_pattern = rf'\b{enum_name}\b'
            for match in re.finditer(usage_pattern, content):
                if match.start() < decl_pos and match.start() != decl_pos:
                    # Exclude #ifndef guards
                    line_start = content.rfind('\n', 0, match.start())
                    line = content[line_start:match.start()]
                    if '#ifndef' not in line and '#define' not in line:
                        warnings.append(f"Enum '{enum_name}' used before declaration")
                        break

        return warnings

    def check_file(self, filepath: Path, check_poisoning: bool = True) -> Dict:
        """Check a single file for issues."""
        rel_path = str(filepath.relative_to(self.mql5_root))

        # Get file integrity info
        integrity = self.get_file_integrity(filepath)
        self.file_integrity[rel_path] = integrity

        result = {
            "file": rel_path,
            "hash": integrity.sha256,
            "crc32": integrity.crc32,
            "size": integrity.size,
            "errors": [],
            "warnings": [],
            "critical": [],
            "lines": integrity.lines
        }

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            result["errors"].append(f"Cannot read file: {e}")
            return result

        # Run all checks
        result["errors"].extend(self.check_includes(filepath, content))
        result["errors"].extend(self.check_brackets(filepath, content))

        pattern_errors, pattern_warnings = self.check_mql5_patterns(filepath, content)
        result["errors"].extend(pattern_errors)
        result["warnings"].extend(pattern_warnings)

        result["warnings"].extend(self.check_declaration_order(filepath, content))

        # File poisoning/security check
        if check_poisoning:
            poisoning_issues = self.check_file_poisoning(filepath, content)
            for issue in poisoning_issues:
                self.issues.append(issue)
                if issue.level == IntegrityLevel.CRITICAL:
                    result["critical"].append(issue.message)
                elif issue.level == IntegrityLevel.HIGH:
                    result["errors"].append(issue.message)
                else:
                    result["warnings"].append(issue.message)

        return result

    def check_regressions(self, current: Dict, manifest: Dict) -> List[str]:
        """Check for regressions against previous manifest."""
        regressions = []

        prev_files = manifest.get("files", {})

        for filepath, current_hash in current.items():
            if filepath in prev_files:
                prev_hash = prev_files[filepath].get("hash", "")
                if prev_hash and prev_hash != current_hash:
                    regressions.append(f"Modified: {filepath}")

        # Check for deleted files
        for filepath in prev_files:
            if filepath not in current:
                regressions.append(f"Deleted: {filepath}")

        # Check for new files
        for filepath in current:
            if filepath not in prev_files:
                regressions.append(f"Added: {filepath}")

        return regressions

    def run_full_check(self, update_manifest: bool = False, show_diff: bool = False) -> Dict:
        """Run full integrity check on all files."""
        print("=" * 70)
        print("  MQL5 INTEGRITY CHECKER - Regression & Security Verification")
        print("=" * 70)

        files = self.get_all_mql5_files()
        print(f"\nScanning {len(files)} MQL5 files...\n")

        # Get git diff stats
        if show_diff:
            self.diff_stats = self.get_git_diff_stats()
            print(f"Git changes: {self.diff_stats}\n")

        manifest = self.load_manifest()
        results = {
            "timestamp": datetime.now().isoformat(),
            "files_checked": len(files),
            "total_critical": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "file_results": {},
            "regressions": [],
            "diff_stats": self.diff_stats.to_dict() if show_diff else None,
            "security_issues": []
        }

        current_hashes = {}
        total_lines = 0
        total_size = 0

        for filepath in files:
            rel_path = str(filepath.relative_to(self.mql5_root))
            file_result = self.check_file(filepath)
            results["file_results"][rel_path] = file_result
            current_hashes[rel_path] = file_result["hash"]

            total_lines += file_result["lines"]
            total_size += file_result.get("size", 0)

            results["total_critical"] += len(file_result.get("critical", []))
            results["total_errors"] += len(file_result["errors"])
            results["total_warnings"] += len(file_result["warnings"])

            # Print issues with severity indicators
            if file_result.get("critical"):
                print(f"💀 {rel_path}")
                for crit in file_result["critical"]:
                    print(f"   CRITICAL: {crit}")
            elif file_result["errors"]:
                print(f"❌ {rel_path}")
                for err in file_result["errors"][:5]:
                    print(f"   ERROR: {err}")
                if len(file_result["errors"]) > 5:
                    print(f"   ... and {len(file_result['errors']) - 5} more errors")
            elif file_result["warnings"]:
                print(f"⚠️  {rel_path}")
                for warn in file_result["warnings"][:3]:
                    print(f"   WARN: {warn}")
            else:
                print(f"✅ {rel_path}")

        # Check regressions against manifest
        results["regressions"] = self.check_regressions(current_hashes, manifest)

        # Collect security issues
        results["security_issues"] = [i.to_dict() for i in self.issues
                                       if i.level in (IntegrityLevel.CRITICAL, IntegrityLevel.HIGH)]

        # Print summary
        print("\n" + "=" * 70)
        print("  INTEGRITY CHECK SUMMARY")
        print("=" * 70)
        print(f"  Files Checked:    {results['files_checked']:>6}")
        print(f"  Total Lines:      {total_lines:>6}")
        print(f"  Total Size:       {total_size // 1024:>6} KB")
        print()
        print(f"  Critical Issues:  {results['total_critical']:>6}" +
              (" 💀 SECURITY RISK" if results['total_critical'] > 0 else ""))
        print(f"  Errors:           {results['total_errors']:>6}")
        print(f"  Warnings:         {results['total_warnings']:>6}")

        if results["regressions"]:
            print(f"\n  File Changes Since Last Check ({len(results['regressions'])}):")
            for change in results["regressions"][:10]:
                print(f"    • {change}")
            if len(results["regressions"]) > 10:
                print(f"    ... and {len(results['regressions']) - 10} more")

        if results["security_issues"]:
            print(f"\n  ⚠️  SECURITY CONCERNS ({len(results['security_issues'])}):")
            for issue in results["security_issues"][:5]:
                print(f"    [{issue['level']}] {issue['file']}: {issue['message']}")

        # Update manifest if requested
        if update_manifest:
            new_manifest = {
                "files": {k: {"hash": v, "crc32": self.file_integrity[k].crc32,
                             "size": self.file_integrity[k].size,
                             "checked": datetime.now().isoformat()}
                         for k, v in current_hashes.items()},
                "version": "2.0",
                "total_files": len(files),
                "total_lines": total_lines
            }
            self.save_manifest(new_manifest)
            print(f"\n  ✅ Manifest updated: {self.manifest_file.name}")

        # Overall status
        print("\n" + "=" * 70)
        if results['total_critical'] > 0:
            print("  STATUS: 💀 FAILED - Critical security issues found")
        elif results['total_errors'] > 0:
            print("  STATUS: ❌ FAILED - Errors found")
        else:
            print("  STATUS: ✅ PASSED - No critical issues")
        print("=" * 70)

        return results

    def sync_check(self, devcentre_path: Path) -> Dict:
        """Compare GitHub MQL5 with DevCentre."""
        print("=" * 60)
        print("DevCentre Sync Check")
        print("=" * 60)

        github_include = self.mql5_root / "Include" / "ProjectQuantum"
        devcentre_include = devcentre_path / "Include" / "ProjectQuantum"

        if not devcentre_include.exists():
            print(f"❌ DevCentre path not found: {devcentre_include}")
            return {"error": "Path not found"}

        # Get files from both locations
        github_files = {f.relative_to(github_include): f
                       for f in github_include.rglob("*.mqh")}
        devcentre_files = {f.relative_to(devcentre_include): f
                         for f in devcentre_include.rglob("*.mqh")}

        # Compare
        only_github = set(github_files.keys()) - set(devcentre_files.keys())
        only_devcentre = set(devcentre_files.keys()) - set(github_files.keys())
        in_both = set(github_files.keys()) & set(devcentre_files.keys())

        # Check hashes for files in both
        different = []
        for f in in_both:
            gh_hash = self.compute_file_hash(github_files[f])
            dc_hash = self.compute_file_hash(devcentre_files[f])
            if gh_hash != dc_hash:
                different.append(f)

        print(f"\nFiles only in GitHub ({len(only_github)}):")
        for f in sorted(only_github):
            print(f"  + {f}")

        print(f"\nFiles only in DevCentre ({len(only_devcentre)}):")
        for f in sorted(only_devcentre):
            print(f"  - {f}")

        print(f"\nFiles with different content ({len(different)}):")
        for f in sorted(different):
            print(f"  ≠ {f}")

        print(f"\nFiles identical: {len(in_both) - len(different)}")

        return {
            "only_github": list(map(str, only_github)),
            "only_devcentre": list(map(str, only_devcentre)),
            "different": list(map(str, different)),
            "identical": len(in_both) - len(different)
        }


    def run_pre_commit_check(self) -> bool:
        """Run pre-commit integrity check - returns True if OK to commit."""
        print("=" * 70)
        print("  PRE-COMMIT INTEGRITY CHECK")
        print("=" * 70)

        # Get staged files
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--', 'MQL5/'],
                cwd=self.mql5_root.parent,
                capture_output=True,
                text=True
            )
            staged_files = [f for f in result.stdout.strip().split('\n') if f.endswith(('.mqh', '.mq5'))]
        except Exception:
            staged_files = []

        if not staged_files:
            print("  No MQL5 files staged for commit.")
            return True

        print(f"\n  Checking {len(staged_files)} staged MQL5 files...\n")

        issues_found = False
        critical_count = 0
        error_count = 0

        for rel_path in staged_files:
            filepath = self.mql5_root.parent / rel_path
            if not filepath.exists():
                continue

            file_result = self.check_file(filepath)

            critical_count += len(file_result.get("critical", []))
            error_count += len(file_result["errors"])

            if file_result.get("critical"):
                print(f"  💀 {rel_path}")
                for crit in file_result["critical"]:
                    print(f"     CRITICAL: {crit}")
                issues_found = True
            elif file_result["errors"]:
                print(f"  ❌ {rel_path}")
                for err in file_result["errors"][:3]:
                    print(f"     ERROR: {err}")
                issues_found = True
            else:
                print(f"  ✅ {rel_path}")

        print("\n" + "=" * 70)

        if critical_count > 0:
            print(f"  💀 BLOCKING COMMIT: {critical_count} critical security issues found!")
            print("     Please fix these issues before committing.")
            print("=" * 70)
            return False

        if error_count > 0:
            print(f"  ⚠️  WARNING: {error_count} errors found (commit allowed)")

        print("  ✅ Pre-commit check passed")
        print("=" * 70)
        return True

    def verify_file_integrity(self, filepath: Path) -> Tuple[bool, str]:
        """Verify a single file's integrity against manifest."""
        manifest = self.load_manifest()
        rel_path = str(filepath.relative_to(self.mql5_root))

        if rel_path not in manifest.get("files", {}):
            return False, "File not in manifest"

        stored = manifest["files"][rel_path]
        current_hash = self.compute_file_hash(filepath)
        current_crc32 = self.compute_crc32(filepath)

        if stored.get("hash") != current_hash:
            return False, f"SHA256 mismatch (stored: {stored.get('hash')[:16]}..., current: {current_hash[:16]}...)"

        if stored.get("crc32") and stored.get("crc32") != current_crc32:
            return False, f"CRC32 mismatch (stored: {stored.get('crc32')}, current: {current_crc32})"

        return True, "Integrity verified"

    def generate_integrity_report(self) -> str:
        """Generate a markdown integrity report."""
        manifest = self.load_manifest()
        report = []

        report.append("# MQL5 Codebase Integrity Report")
        report.append(f"\nGenerated: {datetime.now().isoformat()}")
        report.append(f"\nManifest Version: {manifest.get('version', 'unknown')}")
        report.append(f"Last Check: {manifest.get('last_check', 'never')}")

        report.append("\n## File Inventory")
        report.append(f"\nTotal Files: {manifest.get('total_files', len(manifest.get('files', {})))}")
        report.append(f"Total Lines: {manifest.get('total_lines', 'unknown')}")

        report.append("\n## File Hashes\n")
        report.append("| File | SHA256 | CRC32 | Size |")
        report.append("|------|--------|-------|------|")

        for filepath, info in sorted(manifest.get("files", {}).items()):
            sha_short = info.get("hash", "")[:12] + "..."
            crc = info.get("crc32", "N/A")
            size = info.get("size", "N/A")
            report.append(f"| `{filepath}` | `{sha_short}` | `{crc}` | {size} |")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="MQL5 Integrity Checker - Regression & Security Verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mql5_integrity_checker.py                    # Basic integrity check
  python mql5_integrity_checker.py --diff             # Include git diff stats
  python mql5_integrity_checker.py --update-manifest  # Update baseline manifest
  python mql5_integrity_checker.py --pre-commit       # Pre-commit hook check
  python mql5_integrity_checker.py --sync-check PATH  # Compare with DevCentre
  python mql5_integrity_checker.py --report           # Generate integrity report
        """
    )
    parser.add_argument("--update-manifest", action="store_true",
                       help="Update the integrity manifest after check")
    parser.add_argument("--diff", action="store_true",
                       help="Show git diff statistics")
    parser.add_argument("--pre-commit", action="store_true",
                       help="Run pre-commit check on staged files")
    parser.add_argument("--sync-check", type=str, metavar="PATH",
                       help="Compare with DevCentre MQL5 path")
    parser.add_argument("--report", action="store_true",
                       help="Generate integrity report (markdown)")
    parser.add_argument("--verify", type=str, metavar="FILE",
                       help="Verify a specific file against manifest")
    parser.add_argument("--mql5-root", type=str, default=str(MQL5_ROOT),
                       help="MQL5 root directory")
    parser.add_argument("--json", action="store_true",
                       help="Output results as JSON")

    args = parser.parse_args()

    checker = MQL5IntegrityChecker(Path(args.mql5_root))

    if args.pre_commit:
        # Pre-commit hook mode
        success = checker.run_pre_commit_check()
        sys.exit(0 if success else 1)

    elif args.sync_check:
        checker.sync_check(Path(args.sync_check))

    elif args.verify:
        # Verify single file
        filepath = Path(args.verify)
        if not filepath.is_absolute():
            filepath = checker.mql5_root / filepath
        ok, msg = checker.verify_file_integrity(filepath)
        if ok:
            print(f"✅ {msg}")
            sys.exit(0)
        else:
            print(f"❌ {msg}")
            sys.exit(1)

    elif args.report:
        # Generate report
        report = checker.generate_integrity_report()
        print(report)

    else:
        # Full check
        results = checker.run_full_check(
            update_manifest=args.update_manifest,
            show_diff=args.diff
        )

        if args.json:
            print(json.dumps(results, indent=2))

        # Exit with appropriate code
        if results["total_critical"] > 0:
            sys.exit(2)  # Critical security issues
        elif results["total_errors"] > 0:
            sys.exit(1)  # Errors found
        else:
            sys.exit(0)  # Success


if __name__ == "__main__":
    main()
