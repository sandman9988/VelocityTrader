#!/usr/bin/env python3
"""
Deep Omega Cleanup
Comprehensive replacement of ALL Kelly/Sortino references including:
- Variable names in structures
- Function parameters 
- Comments and documentation
- Array names and member variables
"""

import os
import re
from pathlib import Path

class DeepOmegaCleanup:
    def __init__(self):
        self.project_root = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.include_dir = self.project_root / "Include/ProjectQuantum" 
        self.main_ea_path = self.project_root / "Experts/ProjectQuantum_Main.mq5"
        
        self.cleanup_stats = {
            'files_processed': 0,
            'total_replacements': 0
        }

    def run_deep_cleanup(self):
        """Run comprehensive deep cleanup of all Kelly/Sortino references"""
        print("🔧 Running DEEP Omega Cleanup - Eliminating ALL remaining references...")
        
        # Process all .mqh files
        if self.include_dir.exists():
            for file_path in self.include_dir.rglob("*.mqh"):
                self._deep_cleanup_file(file_path)
        
        # Process main EA
        if self.main_ea_path.exists():
            self._deep_cleanup_file(self.main_ea_path)
        
        print(f"\n✅ Deep cleanup completed: {self.cleanup_stats['total_replacements']} replacements in {self.cleanup_stats['files_processed']} files")
        
        return self.cleanup_stats

    def _deep_cleanup_file(self, file_path: Path):
        """Perform deep cleanup on a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            replacement_count = 0
            
            # Comprehensive replacement patterns
            deep_patterns = [
                # Variable and member names with word boundaries
                (r'\bm_sortino_history\b', 'm_omega_history'),
                (r'\bsortino_history\b', 'omega_history'),
                (r'\bm_sortino_gap_required\b', 'm_omega_gap_required'),
                (r'\bsortino_gap_required\b', 'omega_gap_required'),
                (r'\bm_retrain_target_sortino\b', 'm_retrain_target_omega'),
                (r'\bretrain_target_sortino\b', 'retrain_target_omega'),
                (r'\bpre_retrain_sortino\b', 'pre_retrain_omega'),
                (r'\bpost_retrain_sortino\b', 'post_retrain_omega'),
                (r'\bcurrent_sortino\b', 'current_omega'),
                (r'\bsortino_long\b', 'omega_long'),
                (r'\bsortino_short\b', 'omega_short'),
                (r'\brolling_sortino\b', 'rolling_omega'),
                (r'\bvirtual_sortino\b', 'virtual_omega'),
                (r'\bsession_sortino\b', 'session_omega'),
                (r'\bavg_sortino\b', 'avg_omega'),
                (r'\best_shadow_sortino\b', 'best_shadow_omega'),
                (r'\blive_sortino\b', 'live_omega'),
                (r'\bsortino_weight\b', 'omega_weight'),
                (r'\bsortino_reward\b', 'omega_reward'),
                (r'\bsortino_contribution\b', 'omega_contribution'),
                (r'\bsortino_criterion\b', 'omega_criterion'),
                (r'\bsortino_lookback\b', 'omega_lookback'),
                (r'\bsortino_index\b', 'omega_index'),
                (r'\bsortino_size\b', 'omega_size'),
                (r'\bsortinos\[\]', 'omegas[]'),
                (r'\bsortinos\[', 'omegas['),
                (r'\bm_kelly_fraction\b', 'm_omega_fraction'),
                (r'\bkelly_fraction\b', 'omega_fraction'),
                (r'\bkelly\b', 'omega'),
                
                # Function names and method calls
                (r'\bGetAdaptiveSortinoLookback\b', 'GetAdaptiveOmegaLookback'),
                (r'\bCalculateSortinoReward\b', 'CalculateOmegaReward'),
                (r'\bGetSessionSortino\b', 'GetSessionOmega'),
                (r'\bGetRollingSortino\b', 'GetRollingOmega'),
                (r'\bGetRegimeSortino\b', 'GetRegimeOmega'),
                (r'\bGetHUDMetrics\([^)]*sortinos\[\]', 'GetHUDMetrics(string &names[], double &omegas[], double &win_rates[], int &ranks[])'),
                
                # Comments and documentation
                (r'// Expected Omega for long', '// Expected Omega for long'),
                (r'// Expected Omega for short', '// Expected Omega for short'),
                (r'Get adaptive sortino lookback', 'Get adaptive omega lookback'),
                (r'sortino values', 'omega values'),
                (r'non-zero sortino', 'non-zero omega'),
                (r'For loss streaks/sortino', 'For loss streaks/omega'),
                (r'Count non-zero sortino', 'Count non-zero omega'),
                (r'Omega significantly better', 'Omega significantly better'),
                (r'Required Omega improvement', 'Required Omega improvement'),
                (r'Shadow Omega', 'Shadow Omega'),
                (r'superior Omega ratio', 'superior Omega ratio'),
                (r'session sortino', 'session omega'),
                (r'Session: Sort=', 'Session: Omega='),
                (r'Rolling: Sort=', 'Rolling: Omega='),
                (r'S=%.2f', 'O=%.2f'),  # Change display format
                (r'sortino\)', 'omega)'),
                (r'Fraction of full Omega', 'Fraction of full Omega'),
                (r'Risk-adjusted component', 'Risk-adjusted component'),
                (r'Omega contribution', 'Omega contribution'),
                
                # String formats and parameters
                (r'\"session sortino\"', '"session omega"'),
                (r'\"Omega\"', '"Omega"'),
                (r'StringFormat\([^)]*sortino', lambda m: m.group(0).replace('sortino', 'omega')),
                
                # Array operations and assignments
                (r'ArraySize\(m_sortino_history\)', 'ArraySize(m_omega_history)'),
                (r'm_sortino_history\[([^\]]+)\]', r'm_omega_history[\1]'),
                (r'sortino_history\[([^\]]+)\]', r'omega_history[\1]'),
                
                # Parameter lists (preserve full context)
                (r'double &sortino\)', 'double &omega)'),
                (r'double sortino,', 'double omega,'),
                (r'double sortino\)', 'double omega)'),
                (r', sortino,', ', omega,'),
                (r', sortino\)', ', omega)'),
                
                # Remaining generic references
                (r'\bSortino\b', 'Omega'),
                (r'\bsortino\b', 'omega'),
                (r'\bSORTINO\b', 'OMEGA'),
                (r'\bKelly\b', 'Omega'),
                (r'\bkelly\b', 'omega'),
                (r'\bKELLY\b', 'OMEGA'),
            ]
            
            # Apply all patterns
            for pattern, replacement in deep_patterns:
                if callable(replacement):
                    # Handle lambda replacements
                    matches = list(re.finditer(pattern, content))
                    for match in reversed(matches):  # Reverse to maintain positions
                        new_text = replacement(match)
                        content = content[:match.start()] + new_text + content[match.end():]
                        replacement_count += 1
                else:
                    # Handle string replacements
                    matches = len(re.findall(pattern, content))
                    if matches > 0:
                        content = re.sub(pattern, replacement, content)
                        replacement_count += matches
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.cleanup_stats['files_processed'] += 1
                self.cleanup_stats['total_replacements'] += replacement_count
                
                print(f"   🔧 {file_path.name}: {replacement_count} deep replacements")
                
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")

def main():
    """Run deep Omega cleanup"""
    print("🎯 Starting Deep Omega Cleanup...")
    
    cleaner = DeepOmegaCleanup()
    
    try:
        results = cleaner.run_deep_cleanup()
        print(f"\n✅ Deep Omega cleanup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during deep cleanup: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)