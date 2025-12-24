#Requires -Version 5.1
<#
.SYNOPSIS
    ProjectQuantum MT5 Sync Tool - Offline-First Architecture

.DESCRIPTION
    Syncs MQL5 files from Git repo to MT5 terminals with:
    - SHA256 integrity verification
    - Version tracking
    - Full offline capability (no symlinks)
    - Automatic backup before sync
    - Conflict detection

.PARAMETER Mode
    sync    - Copy files from Git to MT5 terminals
    verify  - Check integrity without copying
    backup  - Create backup of MT5 files
    restore - Restore from backup

.EXAMPLE
    .\mt5_sync.ps1 -Mode sync
    .\mt5_sync.ps1 -Mode verify
#>

param(
    [ValidateSet('sync', 'verify', 'backup', 'restore', 'status', 'setup-symlinks', 'setup-copies')]
    [string]$Mode = 'status',

    # DevCentre is the central offline hub
    [string]$DevCentre = "C:\DevCenter",
    [string]$GitRepo = "C:\DevCenter\Git-Central\Repositories\ProjectQuantum\dev\MQL5",
    [string]$BackupRoot = "C:\DevCenter\Backups\MT5Sync",
    [switch]$Force
)

<#
ARCHITECTURE:
=============
DevCentre (Offline Hub)
├── Git-Central/Repositories/ProjectQuantum/  ← Git repo (source of truth)
│   ├── MQL5/                                 ← MQL5 files
│   └── Tools/                                ← Python tools
├── MT5-Unified/MQL5-Development/             ← Optional: Central MQL5 dev folder
└── Backups/                                  ← Backups

VS Code / Python → Open Git repo directly
MT5 Terminals    → Symlink Include/Experts to Git repo MQL5 folders

Two modes:
  setup-symlinks : MT5 reads directly from Git (recommended, single source)
  setup-copies   : MT5 has copies (for isolation, needs manual sync)
#>

$ErrorActionPreference = "Stop"

# Configuration
$Config = @{
    GitRepo = $GitRepo
    BackupRoot = $BackupRoot
    Terminals = @(
        "29BC03B6BB995A90C75D3603F5C8A659",
        "B1C46BF3BCB8F64CB1B663A0F8847010",
        "D0E8209F77C8CF37AD8BF550E51FF075"
    )
    TerminalBase = "$env:APPDATA\MetaQuotes\Terminal"
    SyncFolders = @("Include\ProjectQuantum", "Experts\ProjectQuantum", "Scripts\ProjectQuantum", "Indicators\ProjectQuantum")
    Extensions = @("*.mqh", "*.mq5", "*.mq4")
    ManifestFile = "sync_manifest.json"
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

function Get-FileHashSHA256 {
    param([string]$Path)
    if (Test-Path $Path) {
        return (Get-FileHash -Path $Path -Algorithm SHA256).Hash
    }
    return $null
}

function Write-Status {
    param([string]$Message, [string]$Type = "INFO")
    $colors = @{
        "INFO" = "White"
        "OK" = "Green"
        "WARN" = "Yellow"
        "ERROR" = "Red"
        "SYNC" = "Cyan"
    }
    $symbols = @{
        "INFO" = "[*]"
        "OK" = "[+]"
        "WARN" = "[!]"
        "ERROR" = "[X]"
        "SYNC" = "[>]"
    }
    Write-Host "$($symbols[$Type]) $Message" -ForegroundColor $colors[$Type]
}

function Get-MQL5Files {
    param([string]$BasePath, [string[]]$Folders, [string[]]$Extensions)

    $files = @()
    foreach ($folder in $Folders) {
        $fullPath = Join-Path $BasePath $folder
        if (Test-Path $fullPath) {
            foreach ($ext in $Extensions) {
                $files += Get-ChildItem -Path $fullPath -Filter $ext -Recurse -File -ErrorAction SilentlyContinue
            }
        }
    }
    return $files
}

function New-FileManifest {
    param([string]$BasePath, [object[]]$Files)

    $manifest = @{
        generated = (Get-Date).ToString("o")
        base_path = $BasePath
        file_count = $Files.Count
        files = @{}
    }

    foreach ($file in $Files) {
        $relativePath = $file.FullName.Substring($BasePath.Length + 1)
        $manifest.files[$relativePath] = @{
            hash = Get-FileHashSHA256 -Path $file.FullName
            size = $file.Length
            modified = $file.LastWriteTime.ToString("o")
        }
    }

    return $manifest
}

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

function Get-SyncStatus {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  MT5 SYNC STATUS" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    # Check Git repo
    Write-Status "Git Repository: $($Config.GitRepo)"
    if (Test-Path $Config.GitRepo) {
        $gitFiles = Get-MQL5Files -BasePath $Config.GitRepo -Folders $Config.SyncFolders -Extensions $Config.Extensions
        Write-Status "  Files: $($gitFiles.Count)" "OK"
    } else {
        Write-Status "  NOT FOUND" "ERROR"
        return
    }

    # Check each terminal
    Write-Host "`nTerminals:" -ForegroundColor White
    foreach ($terminalId in $Config.Terminals) {
        $terminalPath = Join-Path $Config.TerminalBase $terminalId
        $mql5Path = Join-Path $terminalPath "MQL5"

        if (Test-Path $mql5Path) {
            $termFiles = Get-MQL5Files -BasePath $mql5Path -Folders $Config.SyncFolders -Extensions $Config.Extensions

            # Check for symlinks
            $includeLink = Join-Path $mql5Path "Include\ProjectQuantum"
            $isSymlink = $false
            if (Test-Path $includeLink) {
                $item = Get-Item $includeLink -Force
                $isSymlink = ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
            }

            $status = if ($isSymlink) { "SYMLINK" } else { "FILES" }
            $color = if ($isSymlink) { "Yellow" } else { "Green" }

            Write-Host "  $($terminalId.Substring(0,8))... : $($termFiles.Count) files [$status]" -ForegroundColor $color
        } else {
            Write-Host "  $($terminalId.Substring(0,8))... : NOT FOUND" -ForegroundColor Red
        }
    }

    # Check backup
    Write-Host "`nBackups:" -ForegroundColor White
    if (Test-Path $Config.BackupRoot) {
        $backups = Get-ChildItem $Config.BackupRoot -Directory | Sort-Object Name -Descending | Select-Object -First 5
        foreach ($backup in $backups) {
            Write-Host "  $($backup.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  No backups found" -ForegroundColor Gray
    }

    Write-Host ""
}

function Invoke-Backup {
    param([string]$TerminalId)

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = Join-Path $Config.BackupRoot "$timestamp`_$($TerminalId.Substring(0,8))"

    $mql5Path = Join-Path $Config.TerminalBase "$TerminalId\MQL5"

    # Create backup directory
    New-Item -Path $backupPath -ItemType Directory -Force | Out-Null

    # Copy ProjectQuantum folders
    foreach ($folder in $Config.SyncFolders) {
        $sourcePath = Join-Path $mql5Path $folder
        if (Test-Path $sourcePath) {
            $destPath = Join-Path $backupPath $folder
            Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
        }
    }

    # Create manifest
    $files = Get-MQL5Files -BasePath $backupPath -Folders $Config.SyncFolders -Extensions $Config.Extensions
    $manifest = New-FileManifest -BasePath $backupPath -Files $files
    $manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $backupPath $Config.ManifestFile)

    Write-Status "Backup created: $backupPath" "OK"
    return $backupPath
}

function Invoke-Sync {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  SYNCING TO MT5 TERMINALS" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    # Verify Git repo exists
    if (-not (Test-Path $Config.GitRepo)) {
        Write-Status "Git repo not found: $($Config.GitRepo)" "ERROR"
        return
    }

    # Get source files
    $sourceFiles = Get-MQL5Files -BasePath $Config.GitRepo -Folders $Config.SyncFolders -Extensions $Config.Extensions
    Write-Status "Source files: $($sourceFiles.Count)" "INFO"

    # Create source manifest
    $sourceManifest = New-FileManifest -BasePath $Config.GitRepo -Files $sourceFiles

    foreach ($terminalId in $Config.Terminals) {
        Write-Host "`nTerminal: $($terminalId.Substring(0,8))..." -ForegroundColor White

        $mql5Path = Join-Path $Config.TerminalBase "$terminalId\MQL5"

        if (-not (Test-Path $mql5Path)) {
            Write-Status "MQL5 path not found" "WARN"
            continue
        }

        # Backup first
        Write-Status "Creating backup..." "INFO"
        $backupPath = Invoke-Backup -TerminalId $terminalId

        # Remove symlinks if they exist
        foreach ($folder in $Config.SyncFolders) {
            $targetPath = Join-Path $mql5Path $folder
            if (Test-Path $targetPath) {
                $item = Get-Item $targetPath -Force
                if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    Write-Status "Removing symlink: $folder" "INFO"
                    $item.Delete()
                }
            }
        }

        # Sync each folder
        $copied = 0
        $skipped = 0

        foreach ($folder in $Config.SyncFolders) {
            $sourcePath = Join-Path $Config.GitRepo $folder
            $destPath = Join-Path $mql5Path $folder

            if (-not (Test-Path $sourcePath)) {
                continue
            }

            # Create destination folder
            if (-not (Test-Path $destPath)) {
                New-Item -Path $destPath -ItemType Directory -Force | Out-Null
            }

            # Copy files
            foreach ($ext in $Config.Extensions) {
                $files = Get-ChildItem -Path $sourcePath -Filter $ext -Recurse -File -ErrorAction SilentlyContinue
                foreach ($file in $files) {
                    $relativePath = $file.FullName.Substring($sourcePath.Length + 1)
                    $destFile = Join-Path $destPath $relativePath

                    # Create subdirectory if needed
                    $destDir = Split-Path $destFile -Parent
                    if (-not (Test-Path $destDir)) {
                        New-Item -Path $destDir -ItemType Directory -Force | Out-Null
                    }

                    # Check if file needs update
                    $needsCopy = $true
                    if (Test-Path $destFile) {
                        $sourceHash = Get-FileHashSHA256 -Path $file.FullName
                        $destHash = Get-FileHashSHA256 -Path $destFile
                        if ($sourceHash -eq $destHash) {
                            $needsCopy = $false
                            $skipped++
                        }
                    }

                    if ($needsCopy) {
                        Copy-Item -Path $file.FullName -Destination $destFile -Force
                        $copied++
                    }
                }
            }
        }

        Write-Status "Copied: $copied, Unchanged: $skipped" "SYNC"

        # Save manifest
        $manifestPath = Join-Path $mql5Path "Include\ProjectQuantum\$($Config.ManifestFile)"
        $sourceManifest | ConvertTo-Json -Depth 5 | Set-Content $manifestPath
    }

    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  SYNC COMPLETE" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
}

function Invoke-Verify {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  VERIFYING FILE INTEGRITY" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    # Get source manifest
    $sourceFiles = Get-MQL5Files -BasePath $Config.GitRepo -Folders $Config.SyncFolders -Extensions $Config.Extensions
    $sourceManifest = New-FileManifest -BasePath $Config.GitRepo -Files $sourceFiles

    foreach ($terminalId in $Config.Terminals) {
        Write-Host "`nTerminal: $($terminalId.Substring(0,8))..." -ForegroundColor White

        $mql5Path = Join-Path $Config.TerminalBase "$terminalId\MQL5"
        $matched = 0
        $mismatched = 0
        $missing = 0

        foreach ($relativePath in $sourceManifest.files.Keys) {
            $destFile = Join-Path $mql5Path $relativePath
            $sourceHash = $sourceManifest.files[$relativePath].hash

            if (Test-Path $destFile) {
                $destHash = Get-FileHashSHA256 -Path $destFile
                if ($sourceHash -eq $destHash) {
                    $matched++
                } else {
                    $mismatched++
                    Write-Status "  MISMATCH: $relativePath" "WARN"
                }
            } else {
                $missing++
                Write-Status "  MISSING: $relativePath" "ERROR"
            }
        }

        $color = if ($mismatched -eq 0 -and $missing -eq 0) { "Green" } else { "Yellow" }
        Write-Host "  Matched: $matched, Mismatched: $mismatched, Missing: $missing" -ForegroundColor $color
    }
}

function Invoke-SetupSymlinks {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  SETTING UP SYMLINKS (Single Source)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Git Repo -> MT5 Terminals" -ForegroundColor Gray
    Write-Host "========================================`n" -ForegroundColor Cyan

    # Check admin
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Status "REQUIRES ADMINISTRATOR PRIVILEGES" "ERROR"
        Write-Status "Run: Start-Process pwsh -Verb RunAs" "INFO"
        return
    }

    # Verify Git repo
    if (-not (Test-Path $Config.GitRepo)) {
        Write-Status "Git repo not found: $($Config.GitRepo)" "ERROR"
        return
    }

    Write-Status "Source: $($Config.GitRepo)" "INFO"

    foreach ($terminalId in $Config.Terminals) {
        Write-Host "`nTerminal: $($terminalId.Substring(0,8))..." -ForegroundColor White

        $mql5Path = Join-Path $Config.TerminalBase "$terminalId\MQL5"

        if (-not (Test-Path $mql5Path)) {
            Write-Status "MQL5 path not found" "WARN"
            continue
        }

        foreach ($folder in $Config.SyncFolders) {
            $linkPath = Join-Path $mql5Path $folder
            $targetPath = Join-Path $Config.GitRepo $folder

            # Skip if target doesn't exist in Git repo
            if (-not (Test-Path $targetPath)) {
                continue
            }

            # Backup and remove existing
            if (Test-Path $linkPath) {
                $item = Get-Item $linkPath -Force
                $isSymlink = ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0

                if ($isSymlink) {
                    Write-Status "  Removing old symlink: $folder" "INFO"
                    $item.Delete()
                } else {
                    # Backup real folder
                    $backupName = "$($terminalId.Substring(0,8))_$($folder -replace '\\','_')_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
                    $backupPath = Join-Path $Config.BackupRoot $backupName
                    Write-Status "  Backing up: $folder -> $backupPath" "INFO"
                    if (-not (Test-Path $Config.BackupRoot)) {
                        New-Item -Path $Config.BackupRoot -ItemType Directory -Force | Out-Null
                    }
                    Move-Item -Path $linkPath -Destination $backupPath -Force
                }
            }

            # Ensure parent directory exists
            $parentDir = Split-Path $linkPath -Parent
            if (-not (Test-Path $parentDir)) {
                New-Item -Path $parentDir -ItemType Directory -Force | Out-Null
            }

            # Create symlink
            try {
                New-Item -ItemType SymbolicLink -Path $linkPath -Target $targetPath -Force | Out-Null
                Write-Status "  Linked: $folder" "OK"
            } catch {
                Write-Status "  Failed: $folder - $_" "ERROR"
            }
        }
    }

    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  SYMLINKS CONFIGURED" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  All MT5 terminals now read from Git repo" -ForegroundColor Gray
    Write-Host "  git pull = instant MT5 update" -ForegroundColor Gray
    Write-Host "========================================`n" -ForegroundColor Green
}

function Invoke-SetupCopies {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  SETTING UP COPIES (Isolated Mode)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Git Repo -> Copy -> MT5 Terminals" -ForegroundColor Gray
    Write-Host "  Use 'sync' mode to update later" -ForegroundColor Gray
    Write-Host "========================================`n" -ForegroundColor Cyan

    # Remove any existing symlinks first
    foreach ($terminalId in $Config.Terminals) {
        $mql5Path = Join-Path $Config.TerminalBase "$terminalId\MQL5"

        foreach ($folder in $Config.SyncFolders) {
            $path = Join-Path $mql5Path $folder
            if (Test-Path $path) {
                $item = Get-Item $path -Force
                if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    Write-Status "Removing symlink: $folder" "INFO"
                    $item.Delete()
                }
            }
        }
    }

    # Now do a full sync
    Invoke-Sync
}

# ============================================================================
# MAIN
# ============================================================================

switch ($Mode) {
    'status' { Get-SyncStatus }
    'sync' { Invoke-Sync }
    'verify' { Invoke-Verify }
    'setup-symlinks' { Invoke-SetupSymlinks }
    'setup-copies' { Invoke-SetupCopies }
    'backup' {
        foreach ($t in $Config.Terminals) {
            Invoke-Backup -TerminalId $t
        }
    }
    'restore' {
        Write-Status "Restore not yet implemented - use backup folder manually" "WARN"
    }
}
