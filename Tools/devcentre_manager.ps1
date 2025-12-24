<#
.SYNOPSIS
    Universal DevCentre Manager - Single Source of Truth for All Development

.DESCRIPTION
    Manages a centralized development environment where:
    - Git repositories are THE source of truth
    - VS Code opens Git repos directly (no copies)
    - MT5 terminals use symlinks to Git repos
    - All tools reference the same physical files

.PARAMETER Mode
    Operation mode:
    - init          : Initialize DevCentre structure
    - add-project   : Add a new project to DevCentre
    - status        : Show status of all projects
    - link-mt5      : Create MT5 symlinks for MQL5 projects
    - link-tool     : Create symlink for any tool needing a specific path
    - verify        : Verify all symlinks and project integrity
    - backup        : Create timestamped backup of all projects
    - list-tools    : List all detected development tools

.EXAMPLE
    .\devcentre_manager.ps1 -Mode init
    .\devcentre_manager.ps1 -Mode add-project -ProjectName "SentinelPractice" -GitUrl "https://github.com/sandman9988/SentinelPractice"
    .\devcentre_manager.ps1 -Mode link-mt5 -ProjectName "ProjectQuantum"
#>

param(
    [ValidateSet('init', 'add-project', 'status', 'link-mt5', 'link-tool', 'verify', 'backup', 'list-tools')]
    [string]$Mode = 'status',

    [string]$DevCentre = "C:\DevCenter",
    [string]$ProjectName,
    [string]$GitUrl,
    [string]$ToolName,
    [string]$ToolPath,
    [string]$TargetSubfolder
)

# ============================================================================
# ARCHITECTURE DEFINITION
# ============================================================================
#
# UNIVERSAL DEVCENTRE STRUCTURE:
#
# C:\DevCenter\
# ├── .devcentre.json              ← Master config (all projects, tools, symlinks)
# │
# ├── Repositories\                ← ALL Git repos live here (single source of truth)
# │   ├── ProjectQuantum\          ← Git repo IS the working directory
# │   │   ├── .git\
# │   │   ├── MQL5\                ← MT5 symlinks point HERE
# │   │   ├── Tools\
# │   │   └── .vscode\             ← VS Code opens THIS folder
# │   │
# │   ├── SentinelPractice\
# │   │   ├── .git\
# │   │   ├── src\
# │   │   └── .vscode\
# │   │
# │   ├── Scan2GL\
# │   │   └── ...
# │   │
# │   └── PracticeHub\
# │       └── ...
# │
# ├── Backups\                     ← Timestamped backups (contingency)
# │   ├── 2024-01-15_ProjectQuantum\
# │   └── ...
# │
# ├── Shared\                      ← Cross-project shared resources
# │   ├── Libraries\               ← Shared Python/JS libraries
# │   ├── Templates\               ← Project templates
# │   └── Tools\                   ← Universal dev tools
# │
# └── Config\                      ← Tool configurations
#     ├── vscode-profiles\         ← VS Code profiles per project type
#     └── git-hooks\               ← Shared git hooks
#
# ============================================================================
# KEY PRINCIPLES:
#
# 1. ONE LOCATION PER PROJECT: Git repo = Working directory = VS Code workspace
# 2. SYMLINKS FOR TOOLS: Tools that need specific paths get symlinks TO the repo
# 3. NEVER COPY: No duplicate files, ever. If a tool needs files elsewhere, symlink.
# 4. OFFLINE-FIRST: Everything in DevCenter works without internet
# 5. BACKUP STRATEGY: Automated backups before any destructive operation
# ============================================================================

$ErrorActionPreference = "Stop"
$ConfigFile = Join-Path $DevCentre ".devcentre.json"

# Default configuration structure
$DefaultConfig = @{
    version = "1.0.0"
    created = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    projects = @{}
    symlinks = @()
    tools = @{
        mt5_terminals = @()
        vscode = $null
        python = $null
        nodejs = $null
        git = $null
    }
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

function Write-Status {
    param([string]$Message, [string]$Type = "INFO")
    $colors = @{
        "INFO" = "Cyan"
        "SUCCESS" = "Green"
        "WARNING" = "Yellow"
        "ERROR" = "Red"
        "HEADER" = "Magenta"
    }
    $prefix = @{
        "INFO" = "[i]"
        "SUCCESS" = "[+]"
        "WARNING" = "[!]"
        "ERROR" = "[X]"
        "HEADER" = "[*]"
    }
    Write-Host "$($prefix[$Type]) $Message" -ForegroundColor $colors[$Type]
}

function Get-Config {
    if (Test-Path $ConfigFile) {
        return Get-Content $ConfigFile -Raw | ConvertFrom-Json -AsHashtable
    }
    return $null
}

function Save-Config {
    param([hashtable]$Config)
    $Config | ConvertTo-Json -Depth 10 | Set-Content $ConfigFile -Encoding UTF8
}

function Test-AdminPrivilege {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-FileHash256 {
    param([string]$Path)
    if (Test-Path $Path) {
        return (Get-FileHash -Path $Path -Algorithm SHA256).Hash
    }
    return $null
}

# ============================================================================
# TOOL DETECTION
# ============================================================================

function Find-DevelopmentTools {
    $tools = @{
        mt5_terminals = @()
        vscode = $null
        python = $null
        nodejs = $null
        git = $null
    }

    # Find MT5 terminals
    $mt5Base = "$env:APPDATA\MetaQuotes\Terminal"
    if (Test-Path $mt5Base) {
        Get-ChildItem $mt5Base -Directory | ForEach-Object {
            $terminalIni = Join-Path $_.FullName "terminal64.exe"
            $mql5Path = Join-Path $_.FullName "MQL5"
            if (Test-Path $mql5Path) {
                # Try to get terminal name from origin.txt or terminal.ini
                $name = $_.Name.Substring(0, 8) + "..."
                $originFile = Join-Path $_.FullName "origin.txt"
                if (Test-Path $originFile) {
                    $name = (Get-Content $originFile -First 1) -replace '[^\w\s-]', ''
                }
                $tools.mt5_terminals += @{
                    id = $_.Name
                    name = $name
                    path = $_.FullName
                    mql5_path = $mql5Path
                }
            }
        }
    }

    # Find VS Code
    $vscodePaths = @(
        "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe",
        "$env:ProgramFiles\Microsoft VS Code\Code.exe",
        "$env:ProgramFiles(x86)\Microsoft VS Code\Code.exe"
    )
    foreach ($p in $vscodePaths) {
        if (Test-Path $p) {
            $tools.vscode = $p
            break
        }
    }

    # Find Python
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $tools.python = $pythonCmd.Source
    }

    # Find Node.js
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
    if ($nodeCmd) {
        $tools.nodejs = $nodeCmd.Source
    }

    # Find Git
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        $tools.git = $gitCmd.Source
    }

    return $tools
}

# ============================================================================
# MODE: INIT
# ============================================================================

function Initialize-DevCentre {
    Write-Status "INITIALIZING DEVCENTRE" -Type HEADER
    Write-Host ""

    # Check admin for symlink capability
    if (-not (Test-AdminPrivilege)) {
        Write-Status "Running without admin - symlink creation may fail" -Type WARNING
        Write-Status "For full functionality, run as Administrator" -Type WARNING
        Write-Host ""
    }

    # Create structure
    $folders = @(
        "Repositories",
        "Backups",
        "Shared\Libraries",
        "Shared\Templates",
        "Shared\Tools",
        "Config\vscode-profiles",
        "Config\git-hooks"
    )

    foreach ($folder in $folders) {
        $path = Join-Path $DevCentre $folder
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
            Write-Status "Created: $folder" -Type SUCCESS
        } else {
            Write-Status "Exists: $folder" -Type INFO
        }
    }

    # Detect tools
    Write-Host ""
    Write-Status "DETECTING DEVELOPMENT TOOLS" -Type HEADER
    $tools = Find-DevelopmentTools

    Write-Status "MT5 Terminals: $($tools.mt5_terminals.Count) found" -Type INFO
    foreach ($terminal in $tools.mt5_terminals) {
        Write-Status "  - $($terminal.name) [$($terminal.id.Substring(0,8))...]" -Type INFO
    }

    if ($tools.vscode) { Write-Status "VS Code: Found" -Type SUCCESS }
    else { Write-Status "VS Code: Not found" -Type WARNING }

    if ($tools.python) { Write-Status "Python: $($tools.python)" -Type SUCCESS }
    else { Write-Status "Python: Not found" -Type WARNING }

    if ($tools.nodejs) { Write-Status "Node.js: Found" -Type SUCCESS }
    else { Write-Status "Node.js: Not found" -Type WARNING }

    if ($tools.git) { Write-Status "Git: Found" -Type SUCCESS }
    else { Write-Status "Git: Not found" -Type WARNING }

    # Create/update config
    $config = Get-Config
    if (-not $config) {
        $config = $DefaultConfig.Clone()
    }
    $config.tools = $tools
    $config.last_updated = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    Save-Config $config

    Write-Host ""
    Write-Status "DevCentre initialized at: $DevCentre" -Type SUCCESS
    Write-Status "Configuration saved to: $ConfigFile" -Type SUCCESS

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host " NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 1. Add your projects:" -ForegroundColor White
    Write-Host "    .\devcentre_manager.ps1 -Mode add-project -ProjectName 'ProjectQuantum' -GitUrl 'https://github.com/sandman9988/ProjectQuantum'" -ForegroundColor Gray
    Write-Host ""
    Write-Host " 2. For MQL5 projects, create MT5 symlinks:" -ForegroundColor White
    Write-Host "    .\devcentre_manager.ps1 -Mode link-mt5 -ProjectName 'ProjectQuantum'" -ForegroundColor Gray
    Write-Host ""
    Write-Host " 3. Open projects in VS Code directly from Repositories folder" -ForegroundColor White
    Write-Host ""
}

# ============================================================================
# MODE: ADD-PROJECT
# ============================================================================

function Add-Project {
    param([string]$Name, [string]$Url)

    if (-not $Name) {
        Write-Status "ProjectName required" -Type ERROR
        return
    }

    $config = Get-Config
    if (-not $config) {
        Write-Status "DevCentre not initialized. Run with -Mode init first." -Type ERROR
        return
    }

    $repoPath = Join-Path $DevCentre "Repositories\$Name"

    Write-Status "ADDING PROJECT: $Name" -Type HEADER
    Write-Host ""

    if (Test-Path $repoPath) {
        Write-Status "Project folder already exists: $repoPath" -Type WARNING

        # Check if it's a git repo
        if (Test-Path (Join-Path $repoPath ".git")) {
            Write-Status "Valid Git repository detected" -Type SUCCESS

            # Update config
            if (-not $config.projects) { $config.projects = @{} }
            $config.projects[$Name] = @{
                path = $repoPath
                git_url = $Url
                added = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
                type = (Detect-ProjectType $repoPath)
            }
            Save-Config $config

            Write-Status "Project registered in DevCentre config" -Type SUCCESS
        } else {
            Write-Status "Folder exists but is not a Git repo" -Type ERROR
            Write-Status "Either delete the folder or initialize git manually" -Type INFO
        }
        return
    }

    # Clone if URL provided
    if ($Url) {
        Write-Status "Cloning from: $Url" -Type INFO

        try {
            git clone $Url $repoPath
            Write-Status "Repository cloned successfully" -Type SUCCESS
        } catch {
            Write-Status "Clone failed: $_" -Type ERROR
            return
        }
    } else {
        # Create new local repo
        Write-Status "Creating new local repository" -Type INFO
        New-Item -ItemType Directory -Path $repoPath -Force | Out-Null
        Push-Location $repoPath
        git init
        Pop-Location
        Write-Status "Empty repository created" -Type SUCCESS
    }

    # Detect project type
    $projectType = Detect-ProjectType $repoPath

    # Update config
    if (-not $config.projects) { $config.projects = @{} }
    $config.projects[$Name] = @{
        path = $repoPath
        git_url = $Url
        added = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        type = $projectType
    }
    Save-Config $config

    Write-Host ""
    Write-Status "Project added: $Name" -Type SUCCESS
    Write-Status "Location: $repoPath" -Type INFO
    Write-Status "Type: $projectType" -Type INFO

    # Provide next steps based on type
    Write-Host ""
    if ($projectType -contains "mql5") {
        Write-Status "MQL5 project detected. Create MT5 symlinks with:" -Type INFO
        Write-Host "  .\devcentre_manager.ps1 -Mode link-mt5 -ProjectName '$Name'" -ForegroundColor Gray
    }
    if ($projectType -contains "python") {
        Write-Status "Python project detected. Consider creating virtual environment." -Type INFO
    }
    if ($projectType -contains "nodejs") {
        Write-Status "Node.js project detected. Run 'npm install' in project folder." -Type INFO
    }
}

function Detect-ProjectType {
    param([string]$Path)

    $types = @()

    # MQL5 detection - check for folder or recursive file search
    if (Test-Path (Join-Path $Path "MQL5")) { $types += "mql5" }
    elseif (Get-ChildItem -Path $Path -Filter "*.mq5" -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1) { $types += "mql5" }

    # Node.js
    if (Test-Path (Join-Path $Path "package.json")) { $types += "nodejs" }

    # Python
    if (Test-Path (Join-Path $Path "requirements.txt")) { $types += "python" }
    if (Test-Path (Join-Path $Path "setup.py")) { $types += "python" }
    if (Test-Path (Join-Path $Path "pyproject.toml")) { $types += "python" }

    # .NET - recursive search for .csproj files
    if (Get-ChildItem -Path $Path -Filter "*.csproj" -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1) { $types += "dotnet" }

    # Rust
    if (Test-Path (Join-Path $Path "Cargo.toml")) { $types += "rust" }

    # Go
    if (Test-Path (Join-Path $Path "go.mod")) { $types += "go" }

    if ($types.Count -eq 0) { $types += "unknown" }

    return $types
}

# ============================================================================
# MODE: LINK-MT5
# ============================================================================

function Create-MT5Links {
    param([string]$Name)

    if (-not $Name) {
        Write-Status "ProjectName required" -Type ERROR
        return
    }

    if (-not (Test-AdminPrivilege)) {
        Write-Status "Administrator privileges required for symlinks" -Type ERROR
        Write-Status "Please run PowerShell as Administrator" -Type INFO
        return
    }

    $config = Get-Config
    if (-not $config -or -not $config.projects -or -not $config.projects[$Name]) {
        Write-Status "Project '$Name' not found. Add it first with -Mode add-project" -Type ERROR
        return
    }

    $project = $config.projects[$Name]
    $repoMql5 = Join-Path $project.path "MQL5"

    if (-not (Test-Path $repoMql5)) {
        Write-Status "No MQL5 folder in project: $repoMql5" -Type ERROR
        return
    }

    Write-Status "CREATING MT5 SYMLINKS FOR: $Name" -Type HEADER
    Write-Host ""

    $terminals = $config.tools.mt5_terminals
    if ($terminals.Count -eq 0) {
        Write-Status "No MT5 terminals found" -Type ERROR
        return
    }

    # Folders to symlink
    $mql5Folders = @("Include", "Experts", "Indicators", "Scripts", "Libraries")

    foreach ($terminal in $terminals) {
        Write-Host ""
        Write-Status "Terminal: $($terminal.name)" -Type HEADER

        foreach ($folder in $mql5Folders) {
            $sourcePath = Join-Path $repoMql5 $folder
            $targetPath = Join-Path $terminal.mql5_path $folder

            if (-not (Test-Path $sourcePath)) {
                Write-Status "  $folder`: Source not in repo, skipping" -Type INFO
                continue
            }

            # Check current state
            if (Test-Path $targetPath) {
                $item = Get-Item $targetPath -Force

                if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                    # Already a symlink
                    $linkTarget = $item.Target
                    if ($linkTarget -eq $sourcePath) {
                        Write-Status "  $folder`: Already linked correctly" -Type SUCCESS
                        continue
                    } else {
                        Write-Status "  $folder`: Symlink points elsewhere, updating..." -Type WARNING
                        Remove-Item $targetPath -Force
                    }
                } else {
                    # Regular folder - backup and replace
                    $backupPath = "$targetPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
                    Write-Status "  $folder`: Backing up existing folder..." -Type WARNING
                    Move-Item $targetPath $backupPath
                    Write-Status "  $folder`: Backed up to $backupPath" -Type INFO
                }
            }

            # Create symlink
            try {
                New-Item -ItemType SymbolicLink -Path $targetPath -Target $sourcePath -Force | Out-Null
                Write-Status "  $folder`: Symlink created" -Type SUCCESS

                # Record in config
                $config.symlinks += @{
                    source = $sourcePath
                    target = $targetPath
                    project = $Name
                    terminal = $terminal.id
                    created = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
                }
            } catch {
                Write-Status "  $folder`: Failed - $_" -Type ERROR
            }
        }
    }

    Save-Config $config

    Write-Host ""
    Write-Status "MT5 symlinks created for $Name" -Type SUCCESS
    Write-Status "All MT5 terminals now reference: $repoMql5" -Type INFO
}

# ============================================================================
# MODE: STATUS
# ============================================================================

function Show-Status {
    $config = Get-Config

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host " DEVCENTRE STATUS" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""

    if (-not $config) {
        Write-Status "DevCentre not initialized. Run with -Mode init" -Type WARNING
        return
    }

    Write-Status "Location: $DevCentre" -Type INFO
    Write-Status "Last Updated: $($config.last_updated)" -Type INFO
    Write-Host ""

    # Projects
    Write-Status "PROJECTS" -Type HEADER
    if ($config.projects -and $config.projects.Count -gt 0) {
        foreach ($name in $config.projects.Keys) {
            $project = $config.projects[$name]
            $path = $project.path
            $exists = Test-Path $path
            $hasGit = Test-Path (Join-Path $path ".git")

            $status = if ($exists -and $hasGit) { "[OK]" }
                      elseif ($exists) { "[NO GIT]" }
                      else { "[MISSING]" }
            $color = if ($status -eq "[OK]") { "Green" }
                     elseif ($status -eq "[NO GIT]") { "Yellow" }
                     else { "Red" }

            Write-Host "  $status " -ForegroundColor $color -NoNewline
            Write-Host "$name " -ForegroundColor White -NoNewline
            Write-Host "($($project.type -join ', '))" -ForegroundColor Gray

            if ($exists -and $hasGit) {
                Push-Location $path
                $branch = git branch --show-current 2>$null
                $status = git status --porcelain 2>$null
                $dirty = if ($status) { " [uncommitted changes]" } else { "" }
                Pop-Location
                Write-Host "       Branch: $branch$dirty" -ForegroundColor Gray
            }
        }
    } else {
        Write-Status "  No projects registered" -Type INFO
    }

    Write-Host ""

    # Symlinks
    Write-Status "ACTIVE SYMLINKS" -Type HEADER
    if ($config.symlinks -and $config.symlinks.Count -gt 0) {
        $valid = 0
        $broken = 0

        foreach ($link in $config.symlinks) {
            if (Test-Path $link.target) {
                $item = Get-Item $link.target -Force -ErrorAction SilentlyContinue
                if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                    $valid++
                } else {
                    $broken++
                }
            } else {
                $broken++
            }
        }

        Write-Status "  Valid: $valid | Broken: $broken | Total: $($config.symlinks.Count)" -Type INFO
    } else {
        Write-Status "  No symlinks configured" -Type INFO
    }

    Write-Host ""

    # Tools
    Write-Status "DEVELOPMENT TOOLS" -Type HEADER
    if ($config.tools) {
        $tools = $config.tools
        Write-Host "  MT5 Terminals: $($tools.mt5_terminals.Count)" -ForegroundColor Gray
        Write-Host "  VS Code: $(if ($tools.vscode) { 'Found' } else { 'Not found' })" -ForegroundColor Gray
        Write-Host "  Python: $(if ($tools.python) { 'Found' } else { 'Not found' })" -ForegroundColor Gray
        Write-Host "  Node.js: $(if ($tools.nodejs) { 'Found' } else { 'Not found' })" -ForegroundColor Gray
        Write-Host "  Git: $(if ($tools.git) { 'Found' } else { 'Not found' })" -ForegroundColor Gray
    }

    Write-Host ""
}

# ============================================================================
# MODE: VERIFY
# ============================================================================

function Verify-DevCentre {
    $config = Get-Config

    if (-not $config) {
        Write-Status "DevCentre not initialized" -Type ERROR
        return
    }

    Write-Status "VERIFYING DEVCENTRE INTEGRITY" -Type HEADER
    Write-Host ""

    $issues = @()

    # Check projects
    Write-Status "Checking projects..." -Type INFO
    foreach ($name in $config.projects.Keys) {
        $project = $config.projects[$name]

        if (-not (Test-Path $project.path)) {
            $issues += "Project '$name' path missing: $($project.path)"
            Write-Status "  [FAIL] $name - path missing" -Type ERROR
        } elseif (-not (Test-Path (Join-Path $project.path ".git"))) {
            $issues += "Project '$name' has no .git folder"
            Write-Status "  [WARN] $name - no git repository" -Type WARNING
        } else {
            Write-Status "  [OK] $name" -Type SUCCESS
        }
    }

    Write-Host ""

    # Check symlinks
    Write-Status "Checking symlinks..." -Type INFO
    foreach ($link in $config.symlinks) {
        if (-not (Test-Path $link.target)) {
            $issues += "Symlink missing: $($link.target)"
            Write-Status "  [FAIL] $($link.target)" -Type ERROR
            continue
        }

        $item = Get-Item $link.target -Force
        if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            $issues += "Not a symlink (regular folder): $($link.target)"
            Write-Status "  [WARN] $($link.target) - not a symlink" -Type WARNING
        } else {
            $actualTarget = $item.Target
            if ($actualTarget -ne $link.source) {
                $issues += "Symlink points wrong: $($link.target) -> $actualTarget (expected $($link.source))"
                Write-Status "  [WARN] $($link.target) - wrong target" -Type WARNING
            } else {
                Write-Status "  [OK] $($link.target)" -Type SUCCESS
            }
        }
    }

    Write-Host ""

    if ($issues.Count -gt 0) {
        Write-Status "ISSUES FOUND: $($issues.Count)" -Type WARNING
        foreach ($issue in $issues) {
            Write-Host "  - $issue" -ForegroundColor Yellow
        }
    } else {
        Write-Status "All checks passed!" -Type SUCCESS
    }
}

# ============================================================================
# MODE: BACKUP
# ============================================================================

function Backup-Projects {
    $config = Get-Config

    if (-not $config) {
        Write-Status "DevCentre not initialized" -Type ERROR
        return
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
    $backupBase = Join-Path $DevCentre "Backups\$timestamp"

    Write-Status "CREATING BACKUP" -Type HEADER
    Write-Status "Destination: $backupBase" -Type INFO
    Write-Host ""

    New-Item -ItemType Directory -Path $backupBase -Force | Out-Null

    foreach ($name in $config.projects.Keys) {
        $project = $config.projects[$name]

        if (Test-Path $project.path) {
            Write-Status "Backing up: $name..." -Type INFO

            $dest = Join-Path $backupBase $name

            # Use robocopy for efficient copying, excluding .git and node_modules
            robocopy $project.path $dest /E /XD .git node_modules __pycache__ .venv /MT:4 /R:2 /W:1 /NFL /NDL /NJH /NJS /NC /NS | Out-Null

            Write-Status "  Completed: $name" -Type SUCCESS
        } else {
            Write-Status "  Skipped (missing): $name" -Type WARNING
        }
    }

    # Create backup manifest
    $manifest = @{
        timestamp = $timestamp
        projects = $config.projects.Keys
        created_by = "DevCentre Manager"
    }
    $manifest | ConvertTo-Json | Set-Content (Join-Path $backupBase "manifest.json") -Encoding UTF8

    Write-Host ""
    Write-Status "Backup complete: $backupBase" -Type SUCCESS
}

# ============================================================================
# MODE: LIST-TOOLS
# ============================================================================

function List-Tools {
    Write-Status "SCANNING FOR DEVELOPMENT TOOLS" -Type HEADER
    Write-Host ""

    $tools = Find-DevelopmentTools

    Write-Status "MT5 TERMINALS ($($tools.mt5_terminals.Count))" -Type HEADER
    foreach ($terminal in $tools.mt5_terminals) {
        Write-Host "  Name: $($terminal.name)" -ForegroundColor White
        Write-Host "  ID: $($terminal.id)" -ForegroundColor Gray
        Write-Host "  MQL5: $($terminal.mql5_path)" -ForegroundColor Gray
        Write-Host ""
    }

    Write-Status "OTHER TOOLS" -Type HEADER
    Write-Host "  VS Code: $(if ($tools.vscode) { $tools.vscode } else { 'Not found' })" -ForegroundColor $(if ($tools.vscode) { 'Green' } else { 'Yellow' })
    Write-Host "  Python: $(if ($tools.python) { $tools.python } else { 'Not found' })" -ForegroundColor $(if ($tools.python) { 'Green' } else { 'Yellow' })
    Write-Host "  Node.js: $(if ($tools.nodejs) { $tools.nodejs } else { 'Not found' })" -ForegroundColor $(if ($tools.nodejs) { 'Green' } else { 'Yellow' })
    Write-Host "  Git: $(if ($tools.git) { $tools.git } else { 'Not found' })" -ForegroundColor $(if ($tools.git) { 'Green' } else { 'Yellow' })
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

switch ($Mode) {
    'init' { Initialize-DevCentre }
    'add-project' { Add-Project -Name $ProjectName -Url $GitUrl }
    'link-mt5' { Create-MT5Links -Name $ProjectName }
    'status' { Show-Status }
    'verify' { Verify-DevCentre }
    'backup' { Backup-Projects }
    'list-tools' { List-Tools }
    default { Show-Status }
}
