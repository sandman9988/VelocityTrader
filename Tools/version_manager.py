#!/usr/bin/env python3
"""
Project Quantum Version & Signature Manager
Automated version control and file integrity system
Author: Renier De Jager
"""

import os
import hashlib
import json
import subprocess
import re
from datetime import datetime
from pathlib import Path

class VersionManager:
    def __init__(self):
        self.base_version = "1"
        self.build_number = self.get_build_number()
        self.project_root = Path(__file__).parent
        self.signature_file = self.project_root / "file_signatures.json"
        
    def get_build_number(self):
        """Generate build number from git commits"""
        try:
            result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
            return 1000  # Default if git not available
        except:
            return 1000
    
    def get_full_version(self):
        """Get full version string in MQL5 format (y.xxx)"""
        # Format build number to 3 digits for MQL5 standard
        build_formatted = f"{self.build_number:03d}"
        return f"{self.base_version}.{build_formatted}"
    
    def calculate_file_hash(self, filepath):
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return None
    
    def sign_file(self, filepath):
        """Create signature for a file"""
        file_hash = self.calculate_file_hash(filepath)
        if not file_hash:
            return None
            
        stat = os.stat(filepath)
        signature = {
            'path': str(filepath),
            'hash': file_hash,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'version': self.get_full_version(),
            'signed_at': datetime.now().isoformat()
        }
        return signature
    
    def update_file_version(self, filepath):
        """Update version information in MQL5 file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update version property
            content = re.sub(
                r'#property version\s+"[\d\.]+"',
                f'#property version   "{self.get_full_version()}"',
                content
            )
            
            # Update build info comment if exists
            build_info = f"// Build: {self.build_number} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            if "// Build:" in content:
                content = re.sub(
                    r'// Build:.*',
                    build_info,
                    content
                )
            else:
                # Add build info after version
                content = re.sub(
                    r'(#property version[^\n]*\n)',
                    f'\\1{build_info}\n',
                    content
                )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return True
        except Exception as e:
            print(f"❌ Failed to update version in {filepath}: {e}")
            return False
    
    def generate_signatures(self, patterns=None):
        """Generate signatures for all project files"""
        if patterns is None:
            patterns = ["**/*.mqh", "**/*.mq5", "**/*.py"]
        
        signatures = {}
        
        for pattern in patterns:
            files = self.project_root.glob(pattern)
            for filepath in files:
                if filepath.is_file():
                    signature = self.sign_file(filepath)
                    if signature:
                        rel_path = filepath.relative_to(self.project_root)
                        signatures[str(rel_path)] = signature
        
        return signatures
    
    def save_signatures(self, signatures):
        """Save signatures to file"""
        signature_data = {
            'project': 'Project Quantum',
            'version': self.get_full_version(),
            'generated': datetime.now().isoformat(),
            'total_files': len(signatures),
            'signatures': signatures
        }
        
        with open(self.signature_file, 'w') as f:
            json.dump(signature_data, f, indent=2)
        
        print(f"📄 Signatures saved: {len(signatures)} files")
        return True
    
    def verify_signatures(self):
        """Verify all file signatures"""
        if not self.signature_file.exists():
            print("❌ No signature file found")
            return False
        
        with open(self.signature_file, 'r') as f:
            data = json.load(f)
        
        signatures = data.get('signatures', {})
        verified = 0
        failed = 0
        modified_files = []
        
        for rel_path, stored_sig in signatures.items():
            filepath = self.project_root / rel_path
            
            if not filepath.exists():
                print(f"❌ Missing: {rel_path}")
                failed += 1
                continue
            
            current_hash = self.calculate_file_hash(filepath)
            if current_hash != stored_sig['hash']:
                print(f"⚠️  Modified: {rel_path}")
                modified_files.append(rel_path)
                failed += 1
            else:
                verified += 1
        
        print(f"📊 Verification: {verified} verified, {failed} failed")
        
        if modified_files:
            print("\n🔄 Modified files (need re-signing):")
            for filepath in modified_files:
                print(f"   • {filepath}")
        
        return failed == 0

def main():
    """Main version and signature management"""
    vm = VersionManager()
    
    print(f"🏷️  Project Quantum Version Manager")
    print("=" * 40)
    print(f"Version: {vm.get_full_version()}")
    print(f"Build: {vm.build_number}")
    print()
    
    # Update versions in all MQL5 files
    print("🔄 Updating version information...")
    mql_files = list(vm.project_root.glob("**/*.mq5")) + list(vm.project_root.glob("**/*.mqh"))
    
    updated = 0
    for filepath in mql_files:
        if vm.update_file_version(filepath):
            updated += 1
    
    print(f"✅ Updated {updated} files with version {vm.get_full_version()}")
    print()
    
    # Generate and save signatures
    print("🔐 Generating file signatures...")
    signatures = vm.generate_signatures()
    vm.save_signatures(signatures)
    print()
    
    # Verify signatures
    print("🔍 Verifying signatures...")
    if vm.verify_signatures():
        print("✅ All signatures verified")
    else:
        print("⚠️  Some files have signature mismatches")
    
    print(f"\n📁 Signature file: {vm.signature_file}")
    return 0

if __name__ == "__main__":
    main()