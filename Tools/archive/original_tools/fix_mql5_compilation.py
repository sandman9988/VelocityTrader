#!/usr/bin/env python3
"""
Fix MQL5 Compilation Issues
Systematically fixes common compilation errors in ProjectQuantum files
"""

import os
import re
from pathlib import Path

class MQL5CompilationFixer:
    def __init__(self):
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.fixes_applied = {}
        
    def fix_duplicate_properties(self, content):
        """Remove duplicate #property statements"""
        lines = content.split('\n')
        new_lines = []
        properties_seen = set()
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#property'):
                # Extract property type
                prop_match = re.match(r'#property\s+(\w+)', stripped)
                if prop_match:
                    prop_type = prop_match.group(1)
                    if prop_type not in properties_seen:
                        properties_seen.add(prop_type)
                        new_lines.append(line)
                    # Skip duplicate
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def fix_namespace_issues(self, content):
        """Fix namespace syntax for MQL5"""
        # MQL5 doesn't support namespaces - convert to class
        if 'namespace ' in content:
            # Replace namespace with static class
            content = re.sub(
                r'namespace\s+(\w+)\s*\{',
                r'class \1\n{\npublic:',
                content
            )
            
            # Make all functions static
            lines = content.split('\n')
            in_class = False
            new_lines = []
            
            for line in lines:
                if 'class SafeMath' in line:
                    in_class = True
                elif in_class and ('double ' in line or 'float ' in line or 'int ' in line) and '(' in line:
                    # Add static if not already there
                    if 'static' not in line:
                        line = line.replace('double ', 'static double ', 1)
                        line = line.replace('float ', 'static float ', 1)
                        line = line.replace('int ', 'static int ', 1)
                        line = line.replace('bool ', 'static bool ', 1)
                
                new_lines.append(line)
            
            content = '\n'.join(new_lines)
        
        return content
    
    def fix_isfinite_function(self, content):
        """Fix IsFinite function call"""
        # Replace IsFinite with MQL5's MathIsValidNumber
        content = content.replace('IsFinite(', 'MathIsValidNumber(')
        content = content.replace('!IsFinite(', '!MathIsValidNumber(')
        
        return content
    
    def fix_static_const_in_class(self, content):
        """Fix static const member initialization"""
        # Pattern: static const type name = value;
        pattern = r'static\s+const\s+(\w+)\s+(\w+)\s*=\s*([^;]+);'
        
        def replace_static_const(match):
            type_name = match.group(1)
            var_name = match.group(2)
            value = match.group(3)
            
            # Create a getter method instead
            getter = f'''   static {type_name} Get{var_name}() {{ return {value}; }}'''
            return getter
        
        content = re.sub(pattern, replace_static_const, content)
        return content
    
    def add_missing_includes(self, content, filename):
        """Add missing standard includes"""
        includes_needed = []
        
        # Check what's used
        if 'DBL_EPSILON' in content and '#include <Math' not in content:
            includes_needed.append('#include <Math/MathConstants.mqh>')
        
        if includes_needed:
            # Find where to insert (after #property strict)
            lines = content.split('\n')
            insert_index = 0
            
            for i, line in enumerate(lines):
                if '#property strict' in line:
                    insert_index = i + 1
                    break
            
            # Insert the includes
            for include in includes_needed:
                lines.insert(insert_index, include)
                insert_index += 1
                
            content = '\n'.join(lines)
        
        return content
    
    def fix_file(self, filepath):
        """Apply all fixes to a single file"""
        print(f"\n🔧 Fixing: {filepath}")
        
        full_path = self.mt5_dev / filepath
        if not full_path.exists():
            print(f"   ❌ File not found")
            return False
        
        try:
            # Read file
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes = []
            
            # Apply fixes
            new_content = self.fix_duplicate_properties(content)
            if new_content != content:
                fixes.append("Removed duplicate properties")
                content = new_content
            
            new_content = self.fix_namespace_issues(content)
            if new_content != content:
                fixes.append("Fixed namespace syntax")
                content = new_content
            
            new_content = self.fix_isfinite_function(content)
            if new_content != content:
                fixes.append("Fixed IsFinite calls")
                content = new_content
            
            new_content = self.fix_static_const_in_class(content)
            if new_content != content:
                fixes.append("Fixed static const in class")
                content = new_content
                
            new_content = self.add_missing_includes(content, filepath)
            if new_content != content:
                fixes.append("Added missing includes")
                content = new_content
            
            # Write back if changed
            if content != original_content:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"   ✅ Applied {len(fixes)} fixes:")
                for fix in fixes:
                    print(f"      • {fix}")
                
                self.fixes_applied[filepath] = fixes
                return True
            else:
                print(f"   ✅ No fixes needed")
                return True
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def fix_core_files(self):
        """Fix all core files first"""
        core_files = [
            "Include/ProjectQuantum/Core/SafeMath.mqh",
            "Include/ProjectQuantum/Core/ArrayUtils.mqh",
            "Include/ProjectQuantum/Core/SymbolUtils.mqh",
            "Include/ProjectQuantum/Core/CLogger.mqh",
            "Include/ProjectQuantum/Core/Defensive.mqh",
        ]
        
        print("🔧 Fixing Core Files for Compilation")
        print("=" * 50)
        
        success_count = 0
        for file in core_files:
            if self.fix_file(file):
                success_count += 1
        
        print(f"\n📊 Fixed {success_count}/{len(core_files)} core files")
        
        if self.fixes_applied:
            print("\n📝 Fixes Summary:")
            for filepath, fixes in self.fixes_applied.items():
                print(f"\n{filepath}:")
                for fix in fixes:
                    print(f"   • {fix}")
        
        return success_count == len(core_files)
    
    def fix_all_project_files(self):
        """Fix all ProjectQuantum files"""
        include_path = self.mt5_dev / "Include/ProjectQuantum"
        
        all_files = []
        for mqh_file in include_path.rglob("*.mqh"):
            rel_path = mqh_file.relative_to(self.mt5_dev)
            all_files.append(str(rel_path))
        
        print(f"\n🔧 Fixing all {len(all_files)} ProjectQuantum files...")
        
        success_count = 0
        for file in all_files:
            if self.fix_file(file):
                success_count += 1
                
        print(f"\n✅ Fixed {success_count}/{len(all_files)} files")
        return success_count == len(all_files)

if __name__ == "__main__":
    fixer = MQL5CompilationFixer()
    
    # First fix core files
    if fixer.fix_core_files():
        print("\n✅ Core files fixed successfully!")
        
        # Ask if we should fix all files
        response = input("\nFix all ProjectQuantum files? (y/n): ")
        if response.lower() == 'y':
            fixer.fix_all_project_files()
    else:
        print("\n❌ Some core files failed to fix")