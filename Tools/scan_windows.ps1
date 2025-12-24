# ProjectQuantum Multi-Location Scanner - Windows PowerShell Script
# Run this on Windows to scan all DevCentre and Terminal locations

$ErrorActionPreference = "Continue"

# Output file
$OutputFile = "mql5_scan_results.json"

# Locations to scan
$Locations = @{
    "devcentre_main" = "C:\DevCenter\MT5-Unified\MQL5-Development"
    "devcentre_alt" = "C:\DevCentre\MT5\MQL5"
    "github_local" = "C:\path\to\ProjectQuantum\MQL5"  # Update this path
}

# Find MT5 terminals
$TerminalBase = "$env:APPDATA\MetaQuotes\Terminal"
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
            # Robust relative path calculation
            $relativePath = $file.FullName
            if ($relativePath.StartsWith($locPath)) {
                $relativePath = $relativePath.Substring($locPath.Length)
            }
            $relativePath = $relativePath.TrimStart("\")

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

# Save to JSON with UTF8 encoding for cross-platform compatibility
$Report | ConvertTo-Json -Depth 10 | Set-Content -Path $OutputFile -Encoding UTF8
Write-Host ""
Write-Host "Scan complete! Results saved to: $OutputFile" -ForegroundColor Green
Write-Host "Total files found: $($AllFiles.Count)" -ForegroundColor Green
Write-Host ""
Write-Host "Copy $OutputFile to your GitHub repo and run:" -ForegroundColor Yellow
Write-Host "  python multi_location_scanner.py --analyze $OutputFile" -ForegroundColor Yellow
