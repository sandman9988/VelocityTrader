#!/usr/bin/env python3
"""
Multi-Location MQL5 File Scanner
================================
Deep recursive scanner that finds ALL MQL5 files across multiple locations,
computes cryptographic hashes, and identifies duplicates/conflicts.

Designed to scan:
- GitHub Repository (MQL5/)
- DevCentre Development (C:\DevCenter\MT5-Unified\MQL5-Development)
- MT5 Terminals (AppData\Roaming\MetaQuotes\Terminal\*\MQL5)

Features:
- Deep recursive scanning with configurable depth
- SHA256 cryptographic hashing
- Duplicate detection by filename and by content
- Version conflict identification
- Authoritative source determination
- Comprehensive reconciliation reports

Usage:
    # Scan GitHub repo only
    python multi_location_scanner.py --github-only

    # Scan all locations (run on Windows with paths accessible)
    python multi_location_scanner.py --all

    # Generate PowerShell script to run on Windows
    python multi_location_scanner.py --generate-windows-script

    # Analyze results from Windows scan
    python multi_location_scanner.py --analyze scan_results.json

Author: ProjectQuantum Team
Version: 1.0
"""

import re
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, asdict


@dataclass
class FileInfo:
    """Information about a single file."""
    path: str
    relative_path: str
    location: str  # 'github', 'devcentre', 'terminal_1', etc.
    hash: str
    size: int
    modified: str
    version: Optional[str] = None  # Extracted from #property version


@dataclass
class DuplicateGroup:
    """Group of files with the same filename across locations."""
    filename: str
    files: List[FileInfo]
    hash_match: bool  # True if all hashes are identical
    unique_hashes: int


class MultiLocationScanner:
    """Scans multiple locations for MQL5 files and detects duplicates."""

    # Default locations (Windows paths - adjust for WSL with /mnt/c/ prefix)
    DEFAULT_LOCATIONS = {
        'github': Path(__file__).parent.parent / 'MQL5',
        'devcentre': Path('/mnt/c/DevCenter/MT5-Unified/MQL5-Development'),
        'devcentre_alt': Path('/mnt/c/DevCentre/MT5/MQL5'),  # Alternative spelling
    }

    # MT5 Terminal pattern - use environment variable for user-agnostic path
    # On Windows: %APPDATA%\MetaQuotes\Terminal
    # On WSL: /mnt/c/Users/{username}/AppData/Roaming/MetaQuotes/Terminal
    @staticmethod
    def get_mt5_terminal_base() -> Path:
        """Get MT5 terminal base path using environment variables."""
        # Check for APPDATA environment variable (Windows native or WSL passthrough)
        appdata = os.environ.get('APPDATA')
        if appdata:
            return Path(appdata) / 'MetaQuotes' / 'Terminal'

        # WSL fallback: try to get username from environment
        username = os.environ.get('USER') or os.environ.get('USERNAME')
        if username:
            wsl_path = Path(f'/mnt/c/Users/{username}/AppData/Roaming/MetaQuotes/Terminal')
            if wsl_path.exists():
                return wsl_path

        # Default fallback (will fail gracefully if not exists)
        return Path('/mnt/c/Users/Default/AppData/Roaming/MetaQuotes/Terminal')

    MQL5_EXTENSIONS = {'.mqh', '.mq5', '.mq4', '.mqt'}

    def __init__(self, locations: Optional[Dict[str, Path]] = None):
        self.locations = locations or {}
        self.files: List[FileInfo] = []
        self.scan_errors: List[str] = []

    def compute_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash of file content."""
        try:
            hasher = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            return f"ERROR:{e}"

    def extract_version(self, filepath: Path) -> Optional[str]:
        """Extract #property version from MQL5 file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # Version is usually near the top
            match = re.search(r'#property\s+version\s+"([^"]+)"', content)
            return match.group(1) if match else None
        except (IOError, OSError):
            return None

    def scan_location(self, location_name: str, base_path: Path,
                      max_depth: int = 20) -> List[FileInfo]:
        """Recursively scan a location for MQL5 files."""
        files = []

        if not base_path.exists():
            self.scan_errors.append(f"{location_name}: Path not found - {base_path}")
            return files

        print(f"  Scanning {location_name}: {base_path}")

        try:
            for ext in self.MQL5_EXTENSIONS:
                for filepath in base_path.rglob(f"*{ext}"):
                    try:
                        stat = filepath.stat()
                        relative = str(filepath.relative_to(base_path))

                        file_info = FileInfo(
                            path=str(filepath),
                            relative_path=relative,
                            location=location_name,
                            hash=self.compute_hash(filepath),
                            size=stat.st_size,
                            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            version=self.extract_version(filepath)
                        )
                        files.append(file_info)
                    except Exception as e:
                        self.scan_errors.append(f"{location_name}: Error scanning {filepath} - {e}")
        except Exception as e:
            self.scan_errors.append(f"{location_name}: Scan failed - {e}")

        print(f"    Found {len(files)} MQL5 files")
        return files

    def discover_mt5_terminals(self) -> Dict[str, Path]:
        """Discover all MT5 terminal directories."""
        terminals = {}

        if not self.MT5_TERMINAL_BASE.exists():
            return terminals

        try:
            for i, terminal_dir in enumerate(self.MT5_TERMINAL_BASE.iterdir(), 1):
                if terminal_dir.is_dir():
                    mql5_path = terminal_dir / 'MQL5'
                    if mql5_path.exists():
                        terminals[f'terminal_{i}'] = mql5_path
        except Exception as e:
            self.scan_errors.append(f"Terminal discovery failed: {e}")

        return terminals

    def run_full_scan(self, include_terminals: bool = True) -> Dict[str, Any]:
        """Run complete scan of all configured locations."""
        print("=" * 60)
        print("Multi-Location MQL5 File Scanner")
        print("=" * 60)
        print(f"Scan started: {datetime.now().isoformat()}")
        print()

        self.files = []
        self.scan_errors = []

        # Scan GitHub repo (always)
        github_path = self.locations.get('github', self.DEFAULT_LOCATIONS['github'])
        self.files.extend(self.scan_location('github', github_path))

        # Scan DevCentre locations
        for name in ['devcentre', 'devcentre_alt']:
            path = self.locations.get(name, self.DEFAULT_LOCATIONS.get(name))
            if path and path.exists():
                self.files.extend(self.scan_location(name, path))

        # Scan MT5 terminals
        if include_terminals:
            terminals = self.discover_mt5_terminals()
            for name, path in terminals.items():
                self.files.extend(self.scan_location(name, path))

        print()
        print(f"Total files scanned: {len(self.files)}")

        return self.generate_report()

    def find_duplicates_by_name(self) -> Dict[str, DuplicateGroup]:
        """Find files with the same filename across different locations."""
        by_filename: Dict[str, List[FileInfo]] = defaultdict(list)

        for f in self.files:
            filename = Path(f.path).name
            by_filename[filename].append(f)

        duplicates = {}
        for filename, file_list in by_filename.items():
            if len(file_list) > 1:
                # Check if from different locations
                locations = set(f.location for f in file_list)
                if len(locations) > 1:
                    unique_hashes = len(set(f.hash for f in file_list if not f.hash.startswith('ERROR')))
                    duplicates[filename] = DuplicateGroup(
                        filename=filename,
                        files=file_list,
                        hash_match=(unique_hashes == 1),
                        unique_hashes=unique_hashes
                    )

        return duplicates

    def find_hash_conflicts(self) -> List[DuplicateGroup]:
        """Find files with same name but different content."""
        duplicates = self.find_duplicates_by_name()
        return [d for d in duplicates.values() if not d.hash_match]

    def find_missing_in_github(self) -> List[FileInfo]:
        """Find files that exist elsewhere but not in GitHub."""
        github_files = {Path(f.relative_path).name for f in self.files if f.location == 'github'}
        return [f for f in self.files if f.location != 'github' and Path(f.path).name not in github_files]

    def find_github_only(self) -> List[FileInfo]:
        """Find files that only exist in GitHub."""
        non_github_files = {Path(f.path).name for f in self.files if f.location != 'github'}
        return [f for f in self.files if f.location == 'github' and Path(f.path).name not in non_github_files]

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        duplicates = self.find_duplicates_by_name()
        conflicts = self.find_hash_conflicts()
        missing_in_github = self.find_missing_in_github()
        github_only = self.find_github_only()

        # Group files by location
        by_location = defaultdict(list)
        for f in self.files:
            by_location[f.location].append(f)

        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": len(self.files),
                "locations_scanned": len(by_location),
                "files_per_location": {loc: len(files) for loc, files in by_location.items()},
                "duplicate_filenames": len(duplicates),
                "hash_conflicts": len(conflicts),
                "missing_in_github": len(missing_in_github),
                "github_only": len(github_only),
                "scan_errors": len(self.scan_errors)
            },
            "conflicts": [
                {
                    "filename": c.filename,
                    "unique_hashes": c.unique_hashes,
                    "locations": [
                        {
                            "location": f.location,
                            "path": f.relative_path,
                            "hash": f.hash[:16] + "...",
                            "size": f.size,
                            "modified": f.modified,
                            "version": f.version
                        }
                        for f in c.files
                    ]
                }
                for c in conflicts
            ],
            "missing_in_github": [
                {
                    "filename": Path(f.path).name,
                    "location": f.location,
                    "path": f.relative_path,
                    "hash": f.hash[:16] + "..." if not f.hash.startswith('ERROR') else f.hash
                }
                for f in missing_in_github[:50]  # Limit output
            ],
            "github_only": [
                {
                    "filename": Path(f.path).name,
                    "path": f.relative_path
                }
                for f in github_only
            ],
            "all_files": [asdict(f) for f in self.files],
            "scan_errors": self.scan_errors
        }

        return report

    def print_report(self, report: Dict[str, Any]):
        """Print human-readable report."""
        print()
        print("=" * 60)
        print("SCAN RESULTS")
        print("=" * 60)

        summary = report['summary']
        print(f"\nTotal Files Scanned: {summary['total_files']}")
        print(f"Locations Scanned: {summary['locations_scanned']}")
        print("\nFiles per Location:")
        for loc, count in summary['files_per_location'].items():
            print(f"  {loc}: {count} files")

        print(f"\n{'='*60}")
        print("ISSUES FOUND")
        print("=" * 60)

        # Hash conflicts (different content)
        conflicts = report['conflicts']
        if conflicts:
            print(f"\n{len(conflicts)} FILES WITH CONFLICTING CONTENT:")
            for c in conflicts[:10]:
                print(f"\n  {c['filename']} ({c['unique_hashes']} different versions)")
                for loc in c['locations']:
                    print(f"    [{loc['location']}] {loc['path']}")
                    print(f"      Hash: {loc['hash']} | Size: {loc['size']} | Modified: {loc['modified'][:10]}")
                    if loc['version']:
                        print(f"      Version: {loc['version']}")
            if len(conflicts) > 10:
                print(f"\n  ... and {len(conflicts) - 10} more conflicts")
        else:
            print("\nNo hash conflicts found.")

        # Missing in GitHub
        missing = report['missing_in_github']
        if missing:
            print(f"\n{len(missing)} FILES NOT IN GITHUB:")
            for m in missing[:20]:
                print(f"  [{m['location']}] {m['filename']}")
            if len(missing) > 20:
                print(f"  ... and {len(missing) - 20} more")

        # GitHub only
        github_only = report['github_only']
        if github_only:
            print(f"\n{len(github_only)} FILES ONLY IN GITHUB:")
            for g in github_only[:20]:
                print(f"  {g['filename']}")
            if len(github_only) > 20:
                print(f"  ... and {len(github_only) - 20} more")

        # Scan errors
        if report['scan_errors']:
            print(f"\n{len(report['scan_errors'])} SCAN ERRORS:")
            for err in report['scan_errors'][:5]:
                print(f"  {err}")

        print()
        print("=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)

        if conflicts:
            print("\n1. RESOLVE CONFLICTS:")
            print("   - Compare conflicting files to identify the authoritative version")
            print("   - Use timestamps and version numbers as guides")
            print("   - Sync authoritative version to all locations")

        if missing:
            print("\n2. SYNC MISSING FILES TO GITHUB:")
            print("   - Review files only in DevCentre/Terminals")
            print("   - Add necessary files to GitHub repository")
            print("   - Update master include if needed")

        if summary['scan_errors'] > 0:
            print("\n3. FIX ACCESS ISSUES:")
            print("   - Some paths could not be scanned")
            print("   - Check permissions and path existence")

    def save_report(self, report: Dict[str, Any], output_path: Path):
        """Save report to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {output_path}")


def generate_windows_script() -> str:
    """Generate PowerShell script to run on Windows."""
    return '''# ProjectQuantum Multi-Location Scanner - Windows PowerShell Script
# Run this on Windows to scan all DevCentre and Terminal locations

$ErrorActionPreference = "Continue"

# Output file
$OutputFile = "mql5_scan_results.json"

# Locations to scan
$Locations = @{
    "devcentre_main" = "C:\\DevCenter\\MT5-Unified\\MQL5-Development"
    "devcentre_alt" = "C:\\DevCentre\\MT5\\MQL5"
    "github_local" = "C:\\path\\to\\ProjectQuantum\\MQL5"  # Update this path
}

# Find MT5 terminals
$TerminalBase = "$env:APPDATA\\MetaQuotes\\Terminal"
if (Test-Path $TerminalBase) {
    $i = 1
    Get-ChildItem $TerminalBase -Directory | ForEach-Object {
        $mql5Path = Join-Path $_.FullName "MQL5"
        if (Test-Path $mql5Path) {
            $Locations["terminal_$i"] = $mql5Path
            $i++
        }
    }
}

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Multi-Location MQL5 File Scanner" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$AllFiles = @()

foreach ($locName in $Locations.Keys) {
    $locPath = $Locations[$locName]

    if (-not (Test-Path $locPath)) {
        Write-Host "  SKIP: $locName - Path not found: $locPath" -ForegroundColor Yellow
        continue
    }

    Write-Host "  Scanning $locName`: $locPath" -ForegroundColor Green

    $files = Get-ChildItem -Path $locPath -Recurse -Include "*.mqh","*.mq5","*.mq4" -File -ErrorAction SilentlyContinue

    foreach ($file in $files) {
        try {
            $hash = (Get-FileHash -Path $file.FullName -Algorithm SHA256).Hash
            $relativePath = $file.FullName.Replace($locPath, "").TrimStart("\\")

            # Extract version from file
            $version = $null
            $content = Get-Content -Path $file.FullName -First 50 -ErrorAction SilentlyContinue
            $versionMatch = $content | Select-String -Pattern '#property\s+version\s+"([^"]+)"'
            if ($versionMatch) {
                $version = $versionMatch.Matches[0].Groups[1].Value
            }

            $fileInfo = @{
                path = $file.FullName
                relative_path = $relativePath
                location = $locName
                hash = $hash
                size = $file.Length
                modified = $file.LastWriteTime.ToString("o")
                version = $version
            }

            $AllFiles += $fileInfo
        }
        catch {
            Write-Host "    Error scanning $($file.Name): $_" -ForegroundColor Red
        }
    }

    Write-Host "    Found $($files.Count) files" -ForegroundColor Gray
}

# Generate report
$Report = @{
    scan_timestamp = (Get-Date).ToString("o")
    total_files = $AllFiles.Count
    locations = $Locations
    files = $AllFiles
}

# Save to JSON
$Report | ConvertTo-Json -Depth 10 | Set-Content -Path $OutputFile
Write-Host ""
Write-Host "Scan complete! Results saved to: $OutputFile" -ForegroundColor Green
Write-Host "Total files found: $($AllFiles.Count)" -ForegroundColor Green
Write-Host ""
Write-Host "Copy $OutputFile to your GitHub repo and run:" -ForegroundColor Yellow
Write-Host "  python multi_location_scanner.py --analyze $OutputFile" -ForegroundColor Yellow
'''


def main():
    parser = argparse.ArgumentParser(description="Multi-Location MQL5 File Scanner")
    parser.add_argument("--github-only", action="store_true",
                        help="Only scan GitHub repository")
    parser.add_argument("--all", action="store_true",
                        help="Scan all accessible locations")
    parser.add_argument("--generate-windows-script", action="store_true",
                        help="Generate PowerShell script for Windows scanning")
    parser.add_argument("--analyze", type=str, metavar="JSON_FILE",
                        help="Analyze results from Windows scan")
    parser.add_argument("--output", type=str, default="scan_report.json",
                        help="Output file for scan results")

    args = parser.parse_args()

    if args.generate_windows_script:
        script = generate_windows_script()
        script_path = Path(__file__).parent / "scan_windows.ps1"
        with open(script_path, 'w') as f:
            f.write(script)
        print(f"PowerShell script generated: {script_path}")
        print("\nCopy to Windows and run:")
        print("  powershell -ExecutionPolicy Bypass -File scan_windows.ps1")
        return 0

    if args.analyze:
        # Load and analyze Windows scan results
        print(f"Analyzing: {args.analyze}")
        with open(args.analyze, 'r') as f:
            windows_data = json.load(f)

        # Convert to FileInfo objects
        scanner = MultiLocationScanner()
        scanner.files = [
            FileInfo(
                path=f['path'],
                relative_path=f['relative_path'],
                location=f['location'],
                hash=f['hash'],
                size=f['size'],
                modified=f['modified'],
                version=f.get('version')
            )
            for f in windows_data.get('files', [])
        ]

        report = scanner.generate_report()
        scanner.print_report(report)
        scanner.save_report(report, Path(args.output))
        return 0

    # Default: scan accessible locations
    scanner = MultiLocationScanner()

    if args.github_only:
        scanner.files = scanner.scan_location(
            'github',
            Path(__file__).parent.parent / 'MQL5'
        )
        report = scanner.generate_report()
    else:
        report = scanner.run_full_scan(include_terminals=args.all)

    scanner.print_report(report)
    scanner.save_report(report, Path(args.output))

    # Return error code if conflicts found
    if report['summary']['hash_conflicts'] > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
