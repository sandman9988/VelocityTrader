#!/usr/bin/env python3
"""
MT5 Structure Fix Script
Reorganizes ProjectQuantum files into proper MT5 folder structure

MT5 Standard Structure:
- Experts/ (EA files .mq5)
- Include/ (library files .mqh)
- Indicators/ (indicator files .mq5)
- Scripts/ (script files .mq5)
- Libraries/ (library files .ex5/.mq5)

Current issues:
1. Duplicate ProjectQuantum-Full folder in MQL5-Development/
2. Main EA in wrong location
3. Include files mixed up
"""

import os
import shutil
import subprocess
from pathlib import Path

class MT5StructureFix:
    def __init__(self):
        self.source_root = Path("/home/renier/ProjectQuantum-Full")
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.mt5_terminal = Path("/mnt/c/Users/renie/AppData/Roaming/MetaQuotes/Terminal/8A503E260F28D3DD9CC9A37AA3CE29BC/MQL5")
        
    def cleanup_duplicate_folder(self):
        """Remove the duplicate ProjectQuantum-Full folder from MT5-Development"""
        duplicate_path = self.mt5_dev / "ProjectQuantum-Full"
        
        if duplicate_path.exists():
            print(f"🗑️  Removing duplicate folder: {duplicate_path}")
            try:
                subprocess.run(['rm', '-rf', str(duplicate_path)], check=True)
                print("✅ Duplicate folder removed")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to remove duplicate folder: {e}")
                return False
        else:
            print("✅ No duplicate folder found")
            return True
    
    def organize_experts(self):
        """Move EA files to proper Experts/ location"""
        source_main = self.source_root / "Main"
        target_experts = self.mt5_dev / "Experts" / "ProjectQuantum"
        
        # Create target directory
        target_experts.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Organizing Experts...")
        
        if source_main.exists():
            for ea_file in source_main.glob("*.mq5"):
                target_file = target_experts / ea_file.name
                print(f"   📄 {ea_file.name} -> Experts/ProjectQuantum/")
                shutil.copy2(str(ea_file), str(target_file))
        
        # Also copy to terminal
        terminal_experts = self.mt5_terminal / "Experts" / "ProjectQuantum"
        terminal_experts.mkdir(parents=True, exist_ok=True)
        
        if source_main.exists():
            for ea_file in source_main.glob("*.mq5"):
                target_file = terminal_experts / ea_file.name
                shutil.copy2(str(ea_file), str(target_file))
                
        return True
    
    def organize_includes(self):
        """Organize Include files properly"""
        source_include = self.source_root / "Include"
        target_include = self.mt5_dev / "Include" / "ProjectQuantum"
        
        # Create target directory
        target_include.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Organizing Include files...")
        
        if source_include.exists():
            # Copy entire Include structure to ProjectQuantum subfolder
            for item in source_include.rglob("*"):
                if item.is_file() and item.suffix == ".mqh":
                    # Calculate relative path
                    rel_path = item.relative_to(source_include)
                    target_path = target_include / rel_path
                    
                    # Create parent directories
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    print(f"   📄 {rel_path}")
                    shutil.copy2(str(item), str(target_path))
        
        # Also copy to terminal
        terminal_include = self.mt5_terminal / "Include" / "ProjectQuantum"
        terminal_include.mkdir(parents=True, exist_ok=True)
        
        if source_include.exists():
            for item in source_include.rglob("*"):
                if item.is_file() and item.suffix == ".mqh":
                    rel_path = item.relative_to(source_include)
                    target_path = terminal_include / rel_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(item), str(target_path))
                    
        return True
    
    def organize_indicators(self):
        """Organize indicator files"""
        source_indicators = self.source_root / "Indicators"
        target_indicators = self.mt5_dev / "Indicators" / "ProjectQuantum"
        
        if not source_indicators.exists():
            return True
            
        target_indicators.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Organizing Indicators...")
        
        for ind_file in source_indicators.glob("*.mq5"):
            target_file = target_indicators / ind_file.name
            print(f"   📄 {ind_file.name}")
            shutil.copy2(str(ind_file), str(target_file))
        
        # Also copy to terminal
        terminal_indicators = self.mt5_terminal / "Indicators" / "ProjectQuantum"
        terminal_indicators.mkdir(parents=True, exist_ok=True)
        
        for ind_file in source_indicators.glob("*.mq5"):
            target_file = terminal_indicators / ind_file.name
            shutil.copy2(str(ind_file), str(target_file))
            
        return True
    
    def organize_tests(self):
        """Organize test files as Scripts"""
        source_tests = self.source_root / "Tests"
        target_scripts = self.mt5_dev / "Scripts" / "ProjectQuantum"
        
        if not source_tests.exists():
            return True
            
        target_scripts.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Organizing Tests as Scripts...")
        
        for test_file in source_tests.glob("*.mq5"):
            target_file = target_scripts / test_file.name
            print(f"   📄 {test_file.name}")
            shutil.copy2(str(test_file), str(target_file))
        
        # Also copy to terminal  
        terminal_scripts = self.mt5_terminal / "Scripts" / "ProjectQuantum"
        terminal_scripts.mkdir(parents=True, exist_ok=True)
        
        for test_file in source_tests.glob("*.mq5"):
            target_file = terminal_scripts / test_file.name
            shutil.copy2(str(test_file), str(target_file))
            
        return True
    
    def create_main_include_wrapper(self):
        """Create a main include wrapper for easy importing"""
        target_file = self.mt5_dev / "Include" / "ProjectQuantum.mqh"
        
        content = '''//+------------------------------------------------------------------+
//|                                             ProjectQuantum v1.216 |
//|                          Copyright 2024, Quantum Trading Systems |
//|                                   https://www.quantum-trading.ai |
//|                                        Author: Renier De Jager |
//+------------------------------------------------------------------+
#property copyright "Renier De Jager"
#property link      "https://www.quantum-trading.ai"
#property version   "1.216"
#property strict

// ProjectQuantum Master Include File
// This file includes all ProjectQuantum components

#include "ProjectQuantum/Architecture/Project_Quantum.mqh"
#include "ProjectQuantum/Core/Core.mqh"
#include "ProjectQuantum/Core/CLogger.mqh"
#include "ProjectQuantum/Core/CVersionManager.mqh"
#include "ProjectQuantum/Core/CFileIntegrity.mqh"

// Intelligence Components
#include "ProjectQuantum/Intelligence/CRL_Agent.mqh"
#include "ProjectQuantum/Intelligence/CReplayBuffer.mqh"
#include "ProjectQuantum/Intelligence/CProbabilityPredictor.mqh"
#include "ProjectQuantum/Intelligence/CShadowManager.mqh"
#include "ProjectQuantum/Intelligence/CMarketProbability.mqh"

// Risk Management
#include "ProjectQuantum/Risk/CRiskManager.mqh"

// Performance Monitoring  
#include "ProjectQuantum/Performance/CPerformanceMonitor.mqh"
#include "ProjectQuantum/Performance/CInstrumentProfiler.mqh"
#include "ProjectQuantum/Performance/CRegimeJudge.mqh"
#include "ProjectQuantum/Performance/CAgnosticClock.mqh"

// Physics & Market Analysis
#include "ProjectQuantum/Physics/CMarketAgnostic.mqh"

// Safety Systems
#include "ProjectQuantum/Safety/CCircuitBreaker.mqh"
'''
        
        with open(target_file, 'w') as f:
            f.write(content)
        
        # Also create in terminal
        terminal_file = self.mt5_terminal / "Include" / "ProjectQuantum.mqh"
        with open(terminal_file, 'w') as f:
            f.write(content)
            
        print("✅ Created master include file: ProjectQuantum.mqh")
        
    def fix_main_ea_includes(self):
        """Fix include paths in main EA to use simplified structure"""
        main_ea_dev = self.mt5_dev / "Experts" / "ProjectQuantum" / "ProjectQuantum_Main.mq5"
        main_ea_terminal = self.mt5_terminal / "Experts" / "ProjectQuantum" / "ProjectQuantum_Main.mq5"
        
        # Read original file
        source_main = self.source_root / "Main" / "ProjectQuantum_Main.mq5"
        if not source_main.exists():
            return False
            
        with open(source_main, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace complex include paths with simple master include
        new_includes = '''#include <ProjectQuantum.mqh>'''
        
        # Find the include section and replace it
        lines = content.split('\n')
        new_lines = []
        include_section = False
        includes_added = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip existing include lines
            if stripped.startswith('#include') and 'home/renier/ProjectQuantum-Full' in stripped:
                if not includes_added:
                    new_lines.append(new_includes)
                    includes_added = True
                continue
            elif stripped.startswith('#include') and ('Core/' in stripped or 'Architecture/' in stripped or 
                                                     'Intelligence/' in stripped or 'Risk/' in stripped or
                                                     'Performance/' in stripped or 'Physics/' in stripped or
                                                     'Safety/' in stripped):
                continue
            else:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        # Write to both locations
        for target_file in [main_ea_dev, main_ea_terminal]:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
        
        print("✅ Fixed include paths in ProjectQuantum_Main.mq5")
        return True
        
    def verify_structure(self):
        """Verify the final MT5 structure"""
        print("\n📊 FINAL MT5 STRUCTURE")
        print("=" * 50)
        
        # Check development structure
        print("🔧 Development Structure:")
        for folder in ['Experts/ProjectQuantum', 'Include/ProjectQuantum', 'Indicators/ProjectQuantum', 'Scripts/ProjectQuantum']:
            path = self.mt5_dev / folder
            if path.exists():
                count = len(list(path.rglob("*.*")))
                print(f"   ✅ {folder} ({count} files)")
            else:
                print(f"   ❌ {folder} (missing)")
        
        # Check master include
        master_include = self.mt5_dev / "Include" / "ProjectQuantum.mqh" 
        if master_include.exists():
            print(f"   ✅ Master include: ProjectQuantum.mqh")
        else:
            print(f"   ❌ Master include missing")
            
        # Check terminal structure
        print("\n🖥️  Terminal Structure:")
        for folder in ['Experts/ProjectQuantum', 'Include/ProjectQuantum']:
            path = self.mt5_terminal / folder
            if path.exists():
                count = len(list(path.rglob("*.*")))
                print(f"   ✅ {folder} ({count} files)")
            else:
                print(f"   ❌ {folder} (missing)")
                
    def run(self):
        """Execute the complete MT5 structure fix"""
        print("🔧 ProjectQuantum MT5 Structure Fix")
        print("=" * 50)
        
        steps = [
            ("🗑️  Cleanup duplicate folders", self.cleanup_duplicate_folder),
            ("📁 Organize Experts", self.organize_experts),
            ("📁 Organize Include files", self.organize_includes),
            ("📁 Organize Indicators", self.organize_indicators),
            ("📁 Organize Tests as Scripts", self.organize_tests),
            ("📄 Create master include", self.create_main_include_wrapper),
            ("🔧 Fix main EA includes", self.fix_main_ea_includes),
        ]
        
        success_count = 0
        for desc, func in steps:
            print(f"\n{desc}...")
            try:
                if func():
                    print("✅ Success")
                    success_count += 1
                else:
                    print("❌ Failed")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print(f"\n📊 Completed {success_count}/{len(steps)} steps")
        
        # Verify final structure
        self.verify_structure()
        
        if success_count == len(steps):
            print("\n🎉 MT5 structure successfully reorganized!")
            print("📁 ProjectQuantum files are now properly organized")
            print("🔧 Ready for MT5 compilation")
        else:
            print(f"\n⚠️  {len(steps) - success_count} steps failed - manual intervention may be needed")
        
        return success_count == len(steps)

if __name__ == "__main__":
    fixer = MT5StructureFix()
    fixer.run()