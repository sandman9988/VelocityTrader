# VelocityTrader Deployment Script for MetaTrader 5
# Run this from the repository root folder

param(
    [string]$MT5Path = "C:\Users\renie\AppData\Roaming\MetaQuotes\Terminal\29BC03B6BB995A90C75D3603F5C8A659\MQL5"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VelocityTrader MT5 Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verify MT5 path exists
if (-not (Test-Path $MT5Path)) {
    Write-Host "ERROR: MT5 path not found: $MT5Path" -ForegroundColor Red
    exit 1
}

Write-Host "MT5 Path: $MT5Path" -ForegroundColor Green
Write-Host ""

# Define source and destination paths
$repoRoot = $PSScriptRoot
if (-not $repoRoot) { $repoRoot = Get-Location }

$sourceInclude = Join-Path $repoRoot "MQL5\Include"
$sourceExperts = Join-Path $repoRoot "MQL5\Experts"

$destInclude = Join-Path $MT5Path "Include"
$destExperts = Join-Path $MT5Path "Experts"

# Copy Include files
Write-Host "Copying Include files..." -ForegroundColor Yellow
$includeFiles = @(
    "VT_CircuitBreaker.mqh",
    "VT_Definitions.mqh",
    "VT_Globals.mqh",
    "VT_HUD.mqh",
    "VT_KinematicRegimes.mqh",
    "VT_Performance.mqh",
    "VT_Persistence.mqh",
    "VT_Predictor.mqh",
    "VT_RLParameters.mqh",
    "VT_Structures.mqh"
)

foreach ($file in $includeFiles) {
    $src = Join-Path $sourceInclude $file
    $dst = Join-Path $destInclude $file

    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $dst -Force
        Write-Host "  Copied: $file" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $file" -ForegroundColor Red
    }
}

# Copy Expert files
Write-Host ""
Write-Host "Copying Expert Advisors..." -ForegroundColor Yellow
$expertFiles = Get-ChildItem -Path $sourceExperts -Filter "*.mq5" -ErrorAction SilentlyContinue

foreach ($file in $expertFiles) {
    $dst = Join-Path $destExperts $file.Name
    Copy-Item -Path $file.FullName -Destination $dst -Force
    Write-Host "  Copied: $($file.Name)" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Now open MetaEditor and compile:" -ForegroundColor Yellow
Write-Host "  1. Open MetaEditor (F4 in MT5)" -ForegroundColor White
Write-Host "  2. Navigate to Experts folder" -ForegroundColor White
Write-Host "  3. Open VelocityTrader_v7_1_Duel.mq5" -ForegroundColor White
Write-Host "  4. Press F7 to compile" -ForegroundColor White
Write-Host ""
