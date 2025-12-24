#!/usr/bin/env python3
"""
ProjectQuantum MQL5 Terminal Sync
Syncs all corrected files to MetaTrader 5 terminal directory

Usage: python3 sync_to_mql5_terminal.py
"""

import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

# MQL5 Terminal Directory (using WSL mount path)
MT5_DIR = Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/8A503E260F28D3DD9CC9A37AA3CE29BC/MQL5")

def compute_hash(file_path):
    """Compute SHA256 hash for file comparison"""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except:
        return None

def sync_file(src_path, dst_path):
    """Sync a single file with hash comparison"""
    try:
        # Create destination directory if needed
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if files are different
        src_hash = compute_hash(src_path)
        dst_hash = compute_hash(dst_path) if dst_path.exists() else None
        
        if src_hash != dst_hash:
            # Create backup if destination exists
            if dst_path.exists():
                backup_path = dst_path.with_suffix(dst_path.suffix + '.backup')
                shutil.copy2(dst_path, backup_path)
                print(f"  📋 Backup: {dst_path.name} -> {backup_path.name}")
            
            # Copy file
            shutil.copy2(src_path, dst_path)
            print(f"  ✅ Synced: {src_path.name}")
            return True
        else:
            print(f"  ✓ Unchanged: {src_path.name}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {src_path.name} - {e}")
        return False

def main():
    print("🔄 ProjectQuantum MQL5 Terminal Sync")
    print("=" * 50)
    print(f"Target: {MT5_DIR}")
    
    if not MT5_DIR.exists():
        print(f"❌ MQL5 terminal directory not found: {MT5_DIR}")
        print("Please verify MetaTrader 5 is installed and path is correct.")
        return 1
    
    # Files to sync
    sync_map = {
        # Main EA
        "Main/ProjectQuantum_Main.mq5": "Experts/ProjectQuantum_Main.mq5",
        
        # Core Architecture
        "Include/Architecture/Project_Quantum.mqh": "Include/Architecture/Project_Quantum.mqh",
        "Include/Architecture/ProjectQuantum_Architecture.mqh": "Include/Architecture/ProjectQuantum_Architecture.mqh",
        "Include/Architecture/Journey_Architecture.mqh": "Include/Architecture/Journey_Architecture.mqh",
        
        # Security System (NEW)
        "Include/Core/CVersionManager.mqh": "Include/Core/CVersionManager.mqh",
        "Include/Core/CFileIntegrity.mqh": "Include/Core/CFileIntegrity.mqh",
        
        # Core Components
        "Include/Core/Core.mqh": "Include/Core/Core.mqh",
        "Include/Core/CLogger.mqh": "Include/Core/CLogger.mqh",
        "Include/Core/CPersistence.mqh": "Include/Core/CPersistence.mqh",
        "Include/Core/ArrayUtils.mqh": "Include/Core/ArrayUtils.mqh",
        "Include/Core/SafeMath.mqh": "Include/Core/SafeMath.mqh",
        "Include/Core/SymbolUtils.mqh": "Include/Core/SymbolUtils.mqh",
        "Include/Core/Defensive.mqh": "Include/Core/Defensive.mqh",
        "Include/Core/TestFramework.mqh": "Include/Core/TestFramework.mqh",
        "Include/Core/CAdaptiveNormalizer.mqh": "Include/Core/CAdaptiveNormalizer.mqh",
        "Include/Core/CSymbolNormalizer.mqh": "Include/Core/CSymbolNormalizer.mqh",
        "Include/Core/CDominantCycle.mqh": "Include/Core/CDominantCycle.mqh",
        "Include/Core/CSystemOptimizer.mqh": "Include/Core/CSystemOptimizer.mqh",
        
        # Intelligence
        "Include/Intelligence/CRL_Agent.mqh": "Include/Intelligence/CRL_Agent.mqh",
        "Include/Intelligence/CReplayBuffer.mqh": "Include/Intelligence/CReplayBuffer.mqh",
        "Include/Intelligence/CProbabilityPredictor.mqh": "Include/Intelligence/CProbabilityPredictor.mqh",
        "Include/Intelligence/CRLExitAgent.mqh": "Include/Intelligence/CRLExitAgent.mqh",
        "Include/Intelligence/CErrorLearningAgent.mqh": "Include/Intelligence/CErrorLearningAgent.mqh",
        "Include/Intelligence/CJourneyReward.mqh": "Include/Intelligence/CJourneyReward.mqh",
        "Include/Intelligence/CMarketProbability.mqh": "Include/Intelligence/CMarketProbability.mqh",
        "Include/Intelligence/CGenetics.mqh": "Include/Intelligence/CGenetics.mqh",
        "Include/Intelligence/CRiskAdversary.mqh": "Include/Intelligence/CRiskAdversary.mqh",
        "Include/Intelligence/CShadowManager.mqh": "Include/Intelligence/CShadowManager.mqh",
        
        # Risk Management
        "Include/Risk/CRiskManager.mqh": "Include/Risk/CRiskManager.mqh",
        "Include/Risk/CPortfolioRisk.mqh": "Include/Risk/CPortfolioRisk.mqh",
        "Include/Risk/CAssetClassRisk.mqh": "Include/Risk/CAssetClassRisk.mqh",
        "Include/Risk/CCompositeValidator.mqh": "Include/Risk/CCompositeValidator.mqh",
        "Include/Risk/CPositionSizer.mqh": "Include/Risk/CPositionSizer.mqh",
        "Include/Risk/CThreeLevelRisk.mqh": "Include/Risk/CThreeLevelRisk.mqh",
        
        # Safety
        "Include/Safety/CCircuitBreaker.mqh": "Include/Safety/CCircuitBreaker.mqh",
        
        # Performance
        "Include/Performance/CPerformanceMonitor.mqh": "Include/Performance/CPerformanceMonitor.mqh",
        "Include/Performance/CInstrumentProfiler.mqh": "Include/Performance/CInstrumentProfiler.mqh",
        "Include/Performance/CRegimeJudge.mqh": "Include/Performance/CRegimeJudge.mqh",
        "Include/Performance/CAdaptiveCycle.mqh": "Include/Performance/CAdaptiveCycle.mqh",
        "Include/Performance/CAgnosticClock.mqh": "Include/Performance/CAgnosticClock.mqh",
        "Include/Performance/CLearningMetrics.mqh": "Include/Performance/CLearningMetrics.mqh",
        "Include/Performance/CPositionRegistry.mqh": "Include/Performance/CPositionRegistry.mqh",
        "Include/Performance/CRiskIntelligence.mqh": "Include/Performance/CRiskIntelligence.mqh",
        
        # Physics
        "Include/Physics/CMarketPhysics.mqh": "Include/Physics/CMarketPhysics.mqh",
        "Include/Physics/CPhysicsMonitor.mqh": "Include/Physics/CPhysicsMonitor.mqh",
        "Include/Physics/CMarketAgnostic.mqh": "Include/Physics/CMarketAgnostic.mqh",
        "Include/Physics/CFractalAnalyzer.mqh": "Include/Physics/CFractalAnalyzer.mqh",
        "Include/Physics/CPortfolioPhysics.mqh": "Include/Physics/CPortfolioPhysics.mqh",
        
        # Monitoring
        "Include/Monitoring/CRealTimeLogMonitor.mqh": "Include/Monitoring/CRealTimeLogMonitor.mqh",
        
        # Integrity Manifests (NEW)
        "ProjectQuantum_Integrity.dat": "Files/ProjectQuantum_Integrity.dat",
        "ProjectQuantum_Integrity_Manifest.json": "Files/ProjectQuantum_Integrity_Manifest.json"
    }
    
    # Execute sync
    total_files = len(sync_map)
    synced_files = 0
    unchanged_files = 0
    error_files = 0
    
    for src_rel, dst_rel in sync_map.items():
        src_path = Path(src_rel)
        dst_path = MT5_DIR / dst_rel
        
        print(f"\n📂 {dst_rel}")
        
        if not src_path.exists():
            print(f"  ⚠️  Source not found: {src_rel}")
            error_files += 1
            continue
            
        if sync_file(src_path, dst_path):
            synced_files += 1
        else:
            unchanged_files += 1
    
    # Remove duplicates
    print(f"\n🧹 Cleaning up duplicates...")
    cleanup_patterns = [
        "Experts/ ProjectQuantum_Main.mq5",  # File with leading space
        "Experts/*backup*",
        "Include/*~"
    ]
    
    for pattern in cleanup_patterns:
        for file_path in MT5_DIR.rglob(pattern):
            if file_path.exists():
                print(f"  🗑️  Removed: {file_path.name}")
                file_path.unlink()
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"📊 SYNC SUMMARY")
    print(f"=" * 50)
    print(f"Total files: {total_files}")
    print(f"✅ Synced: {synced_files}")
    print(f"✓ Unchanged: {unchanged_files}")
    print(f"❌ Errors: {error_files}")
    print(f"📁 Target: {MT5_DIR}")
    print(f"🕒 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if error_files == 0:
        print(f"\n🎯 All files successfully synced to MQL5 terminal!")
        print(f"🔧 MetaTrader 5 is ready for compilation and testing")
    else:
        print(f"\n⚠️  {error_files} files had errors during sync")
    
    return 0 if error_files == 0 else 1

if __name__ == "__main__":
    exit(main())