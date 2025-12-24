#Requires -RunAsAdministrator
# ProjectQuantum Symlink Setup Script
# Creates symlinks from MT5 Terminal AppData to DevCentre (single source of truth)
# Run as Administrator: Start-Process pwsh -Verb RunAs -ArgumentList "-File setup_symlinks.ps1"

$ErrorActionPreference = "Stop"

# Configuration - EDIT THESE PATHS
$Config = @{
    # Source of truth - DevCentre paths
    SourceRoot = "C:\DevCenter\MT5-Unified\MQL5-Development"

    # Specific folders to symlink
    Symlinks = @(
        @{
            Name = "ProjectQuantum Include"
            Source = "Include\ProjectQuantum"
            Target = "Include\ProjectQuantum"
        },
        @{
            Name = "ProjectQuantum Experts"
            Source = "Experts\ProjectQuantum"
            Target = "Experts\ProjectQuantum"
        }
    )

    # Backup folder for existing files
    BackupRoot = "C:\DevCenter\Backups\MT5-Symlink-Migration"
}

function Write-Banner {
    param([string]$Text, [string]$Color = "Cyan")
    $line = "=" * 70
    Write-Host ""
    Write-Host $line -ForegroundColor $Color
    Write-Host "  $Text" -ForegroundColor $Color
    Write-Host $line -ForegroundColor $Color
    Write-Host ""
}

function Write-Step {
    param([string]$Text, [string]$Status = "INFO")
    $colors = @{
        "INFO" = "White"
        "OK" = "Green"
        "WARN" = "Yellow"
        "ERROR" = "Red"
        "SKIP" = "DarkGray"
    }
    $symbol = @{
        "INFO" = "[*]"
        "OK" = "[+]"
        "WARN" = "[!]"
        "ERROR" = "[X]"
        "SKIP" = "[-]"
    }
    Write-Host "$($symbol[$Status]) $Text" -ForegroundColor $colors[$Status]
}

function Test-IsSymlink {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $false }
    $item = Get-Item $Path -Force
    return ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
}

function Get-MT5Terminals {
    $terminalBase = "$env:APPDATA\MetaQuotes\Terminal"
    $terminals = @()

    if (Test-Path $terminalBase) {
        Get-ChildItem $terminalBase -Directory | ForEach-Object {
            $mql5Path = Join-Path $_.FullName "MQL5"
            if (Test-Path $mql5Path) {
                # Try to identify the terminal by checking terminal64.exe or origin.txt
                $terminalName = $_.Name.Substring(0, 8) + "..."  # Short hash

                $originFile = Join-Path $_.FullName "origin.txt"
                if (Test-Path $originFile) {
                    $origin = Get-Content $originFile -First 1 -ErrorAction SilentlyContinue
                    if ($origin) { $terminalName = [System.IO.Path]::GetFileName($origin) }
                }

                $terminals += @{
                    Path = $_.FullName
                    MQL5 = $mql5Path
                    Name = $terminalName
                    Hash = $_.Name
                }
            }
        }
    }

    return $terminals
}

function Backup-Folder {
    param(
        [string]$SourcePath,
        [string]$BackupName
    )

    if (-not (Test-Path $SourcePath)) { return $null }
    if (Test-IsSymlink $SourcePath) {
        Write-Step "Already a symlink, skipping backup: $SourcePath" "SKIP"
        return "SYMLINK"
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = Join-Path $Config.BackupRoot "$BackupName`_$timestamp"

    # Create backup directory
    if (-not (Test-Path $Config.BackupRoot)) {
        New-Item -Path $Config.BackupRoot -ItemType Directory -Force | Out-Null
    }

    Write-Step "Backing up to: $backupPath" "INFO"
    Copy-Item -Path $SourcePath -Destination $backupPath -Recurse -Force

    return $backupPath
}

function New-SymlinkSafe {
    param(
        [string]$Link,
        [string]$Target
    )

    # Verify target exists
    if (-not (Test-Path $Target)) {
        Write-Step "Target does not exist: $Target" "ERROR"
        return $false
    }

    # Remove existing item (file, folder, or old symlink)
    if (Test-Path $Link) {
        if (Test-IsSymlink $Link) {
            # Remove old symlink
            (Get-Item $Link).Delete()
        } else {
            # This shouldn't happen if backup worked, but safety check
            Write-Step "Warning: Removing non-symlink at $Link" "WARN"
            Remove-Item $Link -Recurse -Force
        }
    }

    # Ensure parent directory exists
    $parentDir = Split-Path $Link -Parent
    if (-not (Test-Path $parentDir)) {
        New-Item -Path $parentDir -ItemType Directory -Force | Out-Null
    }

    # Create symlink
    try {
        New-Item -ItemType SymbolicLink -Path $Link -Target $Target -Force | Out-Null
        return $true
    } catch {
        Write-Step "Failed to create symlink: $_" "ERROR"
        return $false
    }
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

Write-Banner "ProjectQuantum Symlink Setup" "Cyan"

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Step "This script requires Administrator privileges for creating symlinks!" "ERROR"
    Write-Step "Run: Start-Process pwsh -Verb RunAs -ArgumentList '-File setup_symlinks.ps1'" "INFO"
    exit 1
}

Write-Step "Running with Administrator privileges" "OK"

# Verify source paths exist
Write-Banner "Verifying Source Paths" "Yellow"

foreach ($symlink in $Config.Symlinks) {
    $sourcePath = Join-Path $Config.SourceRoot $symlink.Source
    if (Test-Path $sourcePath) {
        $fileCount = (Get-ChildItem $sourcePath -Recurse -File -ErrorAction SilentlyContinue).Count
        Write-Step "$($symlink.Name): $sourcePath ($fileCount files)" "OK"
    } else {
        Write-Step "$($symlink.Name): $sourcePath (NOT FOUND)" "WARN"
        Write-Step "  Creating empty folder structure..." "INFO"
        New-Item -Path $sourcePath -ItemType Directory -Force | Out-Null
    }
}

# Find MT5 terminals
Write-Banner "Discovering MT5 Terminals" "Yellow"

$terminals = Get-MT5Terminals

if ($terminals.Count -eq 0) {
    Write-Step "No MT5 terminals found in AppData!" "ERROR"
    exit 1
}

Write-Step "Found $($terminals.Count) MT5 terminal(s):" "OK"
foreach ($term in $terminals) {
    Write-Host "    - $($term.Name) [$($term.Hash)]" -ForegroundColor Gray
}

# Process each terminal
Write-Banner "Creating Symlinks" "Green"

$results = @{
    Success = 0
    Skipped = 0
    Failed = 0
    Backups = @()
}

foreach ($terminal in $terminals) {
    Write-Host ""
    Write-Host "Terminal: $($terminal.Name)" -ForegroundColor Cyan
    Write-Host "  Path: $($terminal.MQL5)" -ForegroundColor Gray

    foreach ($symlink in $Config.Symlinks) {
        $targetPath = Join-Path $Config.SourceRoot $symlink.Source
        $linkPath = Join-Path $terminal.MQL5 $symlink.Target

        Write-Host ""
        Write-Step "Processing: $($symlink.Name)" "INFO"
        Write-Step "  Link: $linkPath" "INFO"
        Write-Step "  Target: $targetPath" "INFO"

        # Check if already correctly linked
        if (Test-IsSymlink $linkPath) {
            $existingTarget = (Get-Item $linkPath).Target
            if ($existingTarget -eq $targetPath) {
                Write-Step "Already correctly linked!" "SKIP"
                $results.Skipped++
                continue
            } else {
                Write-Step "Symlink exists but points to: $existingTarget" "WARN"
            }
        }

        # Backup existing folder
        if ((Test-Path $linkPath) -and -not (Test-IsSymlink $linkPath)) {
            $backupName = "$($terminal.Hash)_$($symlink.Target -replace '\\','_')"
            $backupPath = Backup-Folder -SourcePath $linkPath -BackupName $backupName
            if ($backupPath -and $backupPath -ne "SYMLINK") {
                $results.Backups += $backupPath
                Write-Step "Backed up existing folder" "OK"

                # Remove original after backup
                Remove-Item $linkPath -Recurse -Force
            }
        }

        # Create symlink
        if (New-SymlinkSafe -Link $linkPath -Target $targetPath) {
            Write-Step "Symlink created successfully!" "OK"
            $results.Success++
        } else {
            Write-Step "Failed to create symlink" "ERROR"
            $results.Failed++
        }
    }
}

# Summary
Write-Banner "Setup Complete" "Green"

Write-Host "Results:" -ForegroundColor White
Write-Host "  Symlinks created: $($results.Success)" -ForegroundColor Green
Write-Host "  Already linked:   $($results.Skipped)" -ForegroundColor Gray
Write-Host "  Failed:           $($results.Failed)" -ForegroundColor $(if ($results.Failed -gt 0) { "Red" } else { "Gray" })

if ($results.Backups.Count -gt 0) {
    Write-Host ""
    Write-Host "Backups created:" -ForegroundColor Yellow
    foreach ($backup in $results.Backups) {
        Write-Host "  - $backup" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Source of Truth: $($Config.SourceRoot)" -ForegroundColor Cyan
Write-Host ""
Write-Host "All MT5 terminals now read from DevCentre via symlinks." -ForegroundColor Green
Write-Host "Edit files in DevCentre - changes appear instantly in MT5!" -ForegroundColor Green
Write-Host ""

# Verification
Write-Banner "Verification" "Yellow"

foreach ($terminal in $terminals) {
    Write-Host "Terminal: $($terminal.Name)" -ForegroundColor Cyan
    foreach ($symlink in $Config.Symlinks) {
        $linkPath = Join-Path $terminal.MQL5 $symlink.Target
        if (Test-IsSymlink $linkPath) {
            $target = (Get-Item $linkPath).Target
            Write-Host "  [OK] $($symlink.Target) -> $target" -ForegroundColor Green
        } elseif (Test-Path $linkPath) {
            Write-Host "  [!!] $($symlink.Target) is NOT a symlink!" -ForegroundColor Red
        } else {
            Write-Host "  [--] $($symlink.Target) does not exist" -ForegroundColor Gray
        }
    }
}

Write-Host ""
Write-Host "Done! Restart MT5 to pick up the changes." -ForegroundColor Green
