#!/usr/bin/env python3
"""
ProjectQuantum Integrity Manifest Generator
Creates SHA256 checksums for all critical files to enable tamper detection

Usage:
    python3 generate_integrity_manifest.py
"""

import hashlib
import os
import json
from datetime import datetime
from pathlib import Path

def compute_sha256(file_path):
    """Compute SHA256 hash of file"""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest().upper()
    except Exception as e:
        print(f"Error hashing {file_path}: {e}")
        return None

def get_file_info(file_path):
    """Get file information for integrity record"""
    try:
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:]
        }
    except Exception as e:
        print(f"Error getting file info for {file_path}: {e}")
        return {"size": 0, "modified": "", "permissions": ""}

def main():
    print("🔐 ProjectQuantum Integrity Manifest Generator")
    print("=" * 50)
    
    # Define critical files
    critical_files = [
        "Main/ProjectQuantum_Main.mq5",
        "Include/Architecture/Project_Quantum.mqh",
        "Include/Core/Core.mqh",
        "Include/Intelligence/CRL_Agent.mqh",
        "Include/Risk/CRiskManager.mqh", 
        "Include/Safety/CCircuitBreaker.mqh",
        "Include/Core/CVersionManager.mqh",
        "Include/Core/CFileIntegrity.mqh",
        "Include/Core/CLogger.mqh",
        "Include/Core/CPersistence.mqh"
    ]
    
    manifest = {
        "generated": datetime.now().isoformat(),
        "version": "1.098",
        "generator": "ProjectQuantum Integrity System",
        "files": {}
    }
    
    processed = 0
    failed = 0
    
    for file_path in critical_files:
        full_path = Path(file_path)
        if not full_path.exists():
            print(f"⚠️  File not found: {file_path}")
            failed += 1
            continue
            
        print(f"📄 Processing: {file_path}")
        
        # Compute hash
        file_hash = compute_sha256(full_path)
        if not file_hash:
            failed += 1
            continue
            
        # Get file info
        file_info = get_file_info(full_path)
        
        # Add to manifest
        manifest["files"][file_path] = {
            "hash": file_hash,
            "size": file_info["size"],
            "modified": file_info["modified"],
            "permissions": file_info["permissions"],
            "critical": True,
            "hash_type": "SHA256"
        }
        
        processed += 1
        print(f"  ✅ Hash: {file_hash[:16]}...")
    
    # Save manifest
    manifest_path = "ProjectQuantum_Integrity_Manifest.json"
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
            
        print(f"\n🎯 Manifest generated successfully!")
        print(f"📁 Location: {manifest_path}")
        print(f"📊 Files processed: {processed}")
        print(f"❌ Files failed: {failed}")
        print(f"📏 Manifest size: {os.path.getsize(manifest_path):,} bytes")
        
        # Also create MQL5-compatible version for the integrity system
        mql5_manifest_path = "ProjectQuantum_Integrity.dat"
        print(f"\n🔧 Creating MQL5-compatible manifest: {mql5_manifest_path}")
        
        # Convert to simple format for MQL5 consumption
        with open(mql5_manifest_path, 'w', encoding='utf-8') as f:
            f.write(f"# ProjectQuantum Integrity Manifest v1.098\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Files: {processed}\n")
            f.write("#\n")
            
            for file_path, info in manifest["files"].items():
                f.write(f"{file_path}|{info['hash']}|{info['size']}|{info['modified']}\n")
                
        print(f"✅ MQL5 manifest created: {os.path.getsize(mql5_manifest_path):,} bytes")
        
    except Exception as e:
        print(f"❌ Error saving manifest: {e}")
        return 1
        
    print(f"\n🛡️  File integrity protection is now active!")
    print(f"🔍 Use CFileIntegrity class to verify these checksums at runtime")
    
    return 0

if __name__ == "__main__":
    exit(main())