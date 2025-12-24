#!/usr/bin/env python3
"""
Reverse Sync from MQL5 Terminal to Dev Directory
Syncs the production-ready, fixed files back from terminal to development

Usage: python3 reverse_sync_from_terminal.py
"""

import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

def compute_hash(file_path):
    """Compute SHA256 hash for file comparison"""
    if not file_path.exists():
        return None
    
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
    print("🔄 Reverse Sync: MQL5 Terminal → Dev Directory")
    print("=" * 60)
    
    # Define paths
    mt5_dir = Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/8A503E260F28D3DD9CC9A37AA3CE29BC/MQL5")
    dev_dir = Path("/home/renier/ProjectQuantum-Full")
    
    print(f"Source: {mt5_dir}")
    print(f"Target: {dev_dir}")
    
    if not mt5_dir.exists():
        print(f"❌ MQL5 terminal directory not found: {mt5_dir}")
        return 1
    
    # Files to reverse sync (terminal → dev)
    reverse_sync_map = {
        # (mt5_rel_path, dev_rel_path, description)
        ("Experts/ProjectQuantum_Main.mq5", "Main/ProjectQuantum_Main.mq5", "Main EA - Production Ready"),
        ("Include/Core/CSystemOptimizer.mqh", "Include/Core/CSystemOptimizer.mqh", "System Optimizer - CheckMemoryPressure Implemented"),
        ("Include/Intelligence/CShadowManager.mqh", "Include/Intelligence/CShadowManager.mqh", "Shadow Manager - PeriodicEvolution Implemented"),
        ("Include/Core/CVersionManager.mqh", "Include/Core/CVersionManager.mqh", "Version Manager - Security System"),
        ("Include/Core/CFileIntegrity.mqh", "Include/Core/CFileIntegrity.mqh", "File Integrity - Security System"),
        ("Include/Core/Defensive.mqh", "Include/Core/Defensive.mqh", "Defensive - Fixed Parameter Syntax"),
        ("Include/Performance/CPerformanceMonitor.mqh", "Include/Performance/CPerformanceMonitor.mqh", "Performance Monitor - Template Fixes"),
        ("Include/Performance/CAgnosticClock.mqh", "Include/Performance/CAgnosticClock.mqh", "Agnostic Clock - Template Fixes"),
        ("Include/Intelligence/CRL_Agent.mqh", "Include/Intelligence/CRL_Agent.mqh", "RL Agent - Template Fixes"),
        ("Include/Intelligence/CReplayBuffer.mqh", "Include/Intelligence/CReplayBuffer.mqh", "Replay Buffer - Template Fixes"),
        ("Include/Intelligence/CProbabilityPredictor.mqh", "Include/Intelligence/CProbabilityPredictor.mqh", "Probability Predictor - Template Fixes"),
        ("Include/Risk/CRiskManager.mqh", "Include/Risk/CRiskManager.mqh", "Risk Manager - Template Fixes"),
        ("Include/Safety/CCircuitBreaker.mqh", "Include/Safety/CCircuitBreaker.mqh", "Circuit Breaker - Template Fixes"),
        ("Files/ProjectQuantum_Integrity.dat", "ProjectQuantum_Integrity.dat", "Integrity Data"),
        ("Files/ProjectQuantum_Integrity_Manifest.json", "ProjectQuantum_Integrity_Manifest.json", "Integrity Manifest")
    }
    
    # Execute reverse sync
    total_files = len(reverse_sync_map)
    synced_files = 0
    unchanged_files = 0
    error_files = 0
    
    for mt5_rel, dev_rel, desc in reverse_sync_map:
        mt5_path = mt5_dir / mt5_rel
        dev_path = dev_dir / dev_rel
        
        print(f"\n📄 {desc}")
        print(f"   MT5: {mt5_rel}")
        print(f"   Dev: {dev_rel}")
        
        if not mt5_path.exists():
            print(f"   ⚠️  Source not found: {mt5_rel}")
            error_files += 1
            continue
            
        if sync_file(mt5_path, dev_path):
            synced_files += 1
        else:
            unchanged_files += 1
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📊 REVERSE SYNC SUMMARY")
    print(f"=" * 60)
    print(f"Total files processed: {total_files}")
    print(f"✅ Synced to dev: {synced_files}")
    print(f"✓ Already current: {unchanged_files}")
    print(f"❌ Errors: {error_files}")
    print(f"🕒 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if error_files == 0:
        print(f"\n🎯 REVERSE SYNC SUCCESSFUL!")
        print(f"✅ Production-ready files synced from terminal to dev")
        print(f"🚀 Ready to commit to main branch")
    else:
        print(f"\n⚠️  {error_files} files had errors during reverse sync")
    
    return 0 if error_files == 0 else 1

if __name__ == "__main__":
    exit(main())