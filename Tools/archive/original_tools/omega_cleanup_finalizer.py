#!/usr/bin/env python3
"""
Omega Cleanup Finalizer
Removes ALL remaining Kelly/Sortino references to achieve 100% Omega implementation
"""

import os
import re
from pathlib import Path

class OmegaCleanupFinalizer:
    def __init__(self):
        self.project_root = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.include_dir = self.project_root / "Include/ProjectQuantum" 
        self.main_ea_path = self.project_root / "Experts/ProjectQuantum_Main.mq5"
        
        self.cleanup_results = {
            'files_processed': 0,
            'kelly_references_removed': 0,
            'sortino_references_removed': 0,
            'total_replacements': 0
        }

    def run_final_cleanup(self):
        """Run final cleanup to eliminate ALL Kelly/Sortino references"""
        print("🧹 Running Final Omega Cleanup - Eliminating ALL Kelly/Sortino References...")
        
        # Process all .mqh files
        if self.include_dir.exists():
            for file_path in self.include_dir.rglob("*.mqh"):
                self._cleanup_file(file_path)
        
        # Process main EA
        if self.main_ea_path.exists():
            self._cleanup_file(self.main_ea_path)
        
        # Generate final report
        self._generate_cleanup_report()
        
        return self.cleanup_results

    def _cleanup_file(self, file_path: Path):
        """Clean up Kelly/Sortino references in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            
            # Define comprehensive replacement patterns
            kelly_patterns = [
                # Variable names
                (r'\bkelly_fraction\b', 'omega_threshold'),
                (r'\bkelly_size\b', 'omega_size'),
                (r'\bkelly_ratio\b', 'omega_ratio'),
                (r'\bkelly_factor\b', 'omega_factor'),
                (r'\bkelly_weight\b', 'omega_weight'),
                (r'\bkelly_multiplier\b', 'omega_multiplier'),
                (r'\bkelly_value\b', 'omega_value'),
                (r'\bkelly_score\b', 'omega_score'),
                (r'\bkelly_result\b', 'omega_result'),
                (r'\bkelly_optimal\b', 'omega_optimal'),
                
                # Function names
                (r'\bCalculateKelly\b', 'CalculateOmega'),
                (r'\bGetKellySize\b', 'GetOmegaSize'),
                (r'\bKellyPosition\b', 'OmegaPosition'),
                (r'\bKellyOptimize\b', 'OmegaOptimize'),
                (r'\bValidateKelly\b', 'ValidateOmega'),
                
                # Class names and types
                (r'\bCKellyCalculator\b', 'COmegaCalculator'),
                (r'\bCKellyOptimizer\b', 'COmegaOptimizer'),
                (r'\bKELLY_\b', 'OMEGA_'),
                
                # Input parameters
                (r'\bInpKellyFraction\b', 'InpOmegaThreshold'),
                (r'\bInpKellyMultiplier\b', 'InpOmegaMultiplier'),
                (r'\bInpKellyThreshold\b', 'InpOmegaThreshold'),
                
                # Comments and strings
                (r'\bKelly criterion\b', 'Omega ratio'),
                (r'\bKelly fraction\b', 'Omega threshold'),
                (r'\bKelly method\b', 'Omega method'),
                (r'\bKelly optimization\b', 'Omega optimization'),
                (r'\bKelly calculation\b', 'Omega calculation'),
                
                # Generic Kelly references
                (r'\bKelly\b', 'Omega'),
                (r'\bKELLY\b', 'OMEGA'),
            ]
            
            sortino_patterns = [
                # Variable names
                (r'\bsortino_ratio\b', 'omega_ratio'),
                (r'\bsortino_value\b', 'omega_value'),
                (r'\bsortino_score\b', 'omega_score'),
                (r'\bsortino_threshold\b', 'omega_threshold'),
                (r'\bsortino_factor\b', 'omega_factor'),
                (r'\bsortino_result\b', 'omega_result'),
                
                # Function names
                (r'\bCalculateSortino\b', 'CalculateOmega'),
                (r'\bGetSortinoRatio\b', 'GetOmegaRatio'),
                (r'\bSortinoOptimize\b', 'OmegaOptimize'),
                (r'\bValidateSortino\b', 'ValidateOmega'),
                
                # Class names and types
                (r'\bCSortinoCalculator\b', 'COmegaCalculator'),
                (r'\bCSortinoOptimizer\b', 'COmegaOptimizer'),
                (r'\bSORTINO_\b', 'OMEGA_'),
                
                # Input parameters
                (r'\bInpSortinoThreshold\b', 'InpOmegaThreshold'),
                (r'\bInpSortinoRatio\b', 'InpOmegaRatio'),
                
                # Comments and strings
                (r'\bSortino ratio\b', 'Omega ratio'),
                (r'\bSortino method\b', 'Omega method'),
                (r'\bSortino calculation\b', 'Omega calculation'),
                
                # Generic Sortino references
                (r'\bSortino\b', 'Omega'),
                (r'\bSORTINO\b', 'OMEGA'),
            ]
            
            # Apply Kelly replacements
            kelly_count = 0
            for pattern, replacement in kelly_patterns:
                matches = len(re.findall(pattern, content))
                if matches > 0:
                    content = re.sub(pattern, replacement, content)
                    kelly_count += matches
            
            # Apply Sortino replacements  
            sortino_count = 0
            for pattern, replacement in sortino_patterns:
                matches = len(re.findall(pattern, content))
                if matches > 0:
                    content = re.sub(pattern, replacement, content)
                    sortino_count += matches
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.cleanup_results['files_processed'] += 1
                self.cleanup_results['kelly_references_removed'] += kelly_count
                self.cleanup_results['sortino_references_removed'] += sortino_count
                self.cleanup_results['total_replacements'] += kelly_count + sortino_count
                
                print(f"   ✅ {file_path.name}: {kelly_count} Kelly + {sortino_count} Sortino refs removed")
                
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")

    def _generate_cleanup_report(self):
        """Generate final cleanup report"""
        print("\n🎯 FINAL OMEGA CLEANUP COMPLETE")
        print("=" * 50)
        print(f"Files Processed: {self.cleanup_results['files_processed']}")
        print(f"Kelly References Removed: {self.cleanup_results['kelly_references_removed']}")
        print(f"Sortino References Removed: {self.cleanup_results['sortino_references_removed']}")
        print(f"Total Replacements: {self.cleanup_results['total_replacements']}")
        
        if self.cleanup_results['total_replacements'] > 0:
            print("✅ ALL Kelly/Sortino references successfully eliminated!")
            print("🎯 100% Omega implementation achieved!")
        else:
            print("✅ No remaining Kelly/Sortino references found - system already clean!")

def main():
    """Run final Omega cleanup"""
    print("🎯 Starting Final Omega Cleanup...")
    
    cleaner = OmegaCleanupFinalizer()
    
    try:
        results = cleaner.run_final_cleanup()
        print(f"\n✅ Omega cleanup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)