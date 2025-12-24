#!/usr/bin/env python3
"""
MQL5 Integrity Checker
======================
Verifies MQL5 codebase integrity, detects regressions, and ensures
all includes are valid.

Features:
- File hash tracking for regression detection
- Include validation (all #include files must exist)
- Declaration order checking (enums before use)
- Bracket matching (#ifndef/#endif, {/})
- DevCentre sync verification

Usage:
    python mql5_integrity_checker.py [--fix] [--sync-check PATH]
"""

import re
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configuration
MQL5_ROOT = Path(__file__).parent.parent / "MQL5"
MANIFEST_FILE = MQL5_ROOT / ".integrity_manifest.json"
INCLUDE_ROOT = MQL5_ROOT / "Include" / "ProjectQuantum"


class MQL5IntegrityChecker:
    """Comprehensive MQL5 codebase integrity checker."""

    def __init__(self, mql5_root: Path):
        self.mql5_root = mql5_root
        self.include_root = mql5_root / "Include" / "ProjectQuantum"
        self.manifest_file = mql5_root / ".integrity_manifest.json"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def compute_file_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash of file content."""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            return f"ERROR:{e}"

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

        for inc in includes:
            # Skip standard MQL5 library includes
            if any(inc.startswith(std) for std in ["Trade/", "Arrays/", "Expert/", "Indicators/"]):
                continue

            resolved = self.resolve_include_path(inc, filepath)
            if resolved and not resolved.exists():
                errors.append(f"Missing include: {inc}")

        return errors

    def check_brackets(self, filepath: Path, content: str) -> List[str]:
        """Check bracket matching."""
        errors = []

        # Check #ifndef/#endif matching
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

        # Check for raw division (potential div by zero)
        div_pattern = r'[^/]/[^/=*]'  # Matches single / not part of // or /* or /=
        for match in re.finditer(div_pattern, content):
            # Get context
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end]
            if 'SafeMath' not in context and 'SafeDiv' not in context:
                # Check if it's actually a division
                if '=' in context or 'return' in context:
                    warnings.append(f"Potential unsafe division near: ...{context[:30]}...")

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

    def check_file(self, filepath: Path) -> Dict:
        """Check a single file for issues."""
        result = {
            "file": str(filepath.relative_to(self.mql5_root)),
            "hash": self.compute_file_hash(filepath),
            "errors": [],
            "warnings": [],
            "lines": 0
        }

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            result["lines"] = content.count('\n') + 1
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

    def run_full_check(self, update_manifest: bool = False) -> Dict:
        """Run full integrity check on all files."""
        print("=" * 60)
        print("MQL5 Integrity Checker")
        print("=" * 60)

        files = self.get_all_mql5_files()
        print(f"\nChecking {len(files)} MQL5 files...\n")

        manifest = self.load_manifest()
        results = {
            "timestamp": datetime.now().isoformat(),
            "files_checked": len(files),
            "total_errors": 0,
            "total_warnings": 0,
            "file_results": {},
            "regressions": []
        }

        current_hashes = {}

        for filepath in files:
            rel_path = str(filepath.relative_to(self.mql5_root))
            file_result = self.check_file(filepath)
            results["file_results"][rel_path] = file_result
            current_hashes[rel_path] = file_result["hash"]

            results["total_errors"] += len(file_result["errors"])
            results["total_warnings"] += len(file_result["warnings"])

            # Print issues
            if file_result["errors"]:
                print(f"❌ {rel_path}")
                for err in file_result["errors"]:
                    print(f"   ERROR: {err}")
            elif file_result["warnings"]:
                print(f"⚠️  {rel_path}")
                for warn in file_result["warnings"][:3]:  # Limit warnings shown
                    print(f"   WARN: {warn}")
            else:
                print(f"✅ {rel_path}")

        # Check regressions
        results["regressions"] = self.check_regressions(current_hashes, manifest)

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Files Checked: {results['files_checked']}")
        print(f"Total Errors:  {results['total_errors']}")
        print(f"Total Warnings: {results['total_warnings']}")

        if results["regressions"]:
            print(f"\nChanges since last check:")
            for change in results["regressions"][:10]:
                print(f"  • {change}")
            if len(results["regressions"]) > 10:
                print(f"  ... and {len(results['regressions']) - 10} more")

        # Update manifest if requested
        if update_manifest:
            new_manifest = {
                "files": {k: {"hash": v, "checked": datetime.now().isoformat()}
                         for k, v in current_hashes.items()},
                "version": "1.0"
            }
            self.save_manifest(new_manifest)
            print(f"\n✅ Manifest updated: {self.manifest_file}")

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


def main():
    parser = argparse.ArgumentParser(description="MQL5 Integrity Checker")
    parser.add_argument("--update-manifest", action="store_true",
                       help="Update the integrity manifest after check")
    parser.add_argument("--sync-check", type=str, metavar="PATH",
                       help="Compare with DevCentre MQL5 path")
    parser.add_argument("--mql5-root", type=str, default=str(MQL5_ROOT),
                       help="MQL5 root directory")

    args = parser.parse_args()

    checker = MQL5IntegrityChecker(Path(args.mql5_root))

    if args.sync_check:
        checker.sync_check(Path(args.sync_check))
    else:
        results = checker.run_full_check(update_manifest=args.update_manifest)

        # Exit with error code if issues found
        if results["total_errors"] > 0:
            exit(1)


if __name__ == "__main__":
    main()
