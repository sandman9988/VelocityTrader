#!/usr/bin/env python3
"""
Fix static keyword issues in MQL5 files
"""

import re
from pathlib import Path

def fix_static_in_parameters(content):
    """Remove static keyword from function parameters"""
    # Pattern to find static in parameters
    # Look for 'static' before parameter types in function definitions
    
    # Fix pattern: static double value -> double value in parameters
    pattern = r'(\(.*?)static\s+(double|int|float|bool|string)\s+(\w+)'
    content = re.sub(pattern, r'\1\2 \3', content)
    
    # Also fix in function declarations with multiple parameters
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # If line contains function parameter with static
        if '(' in line and 'static' in line and ('double' in line or 'int' in line):
            # Remove static from parameters only (not from function declaration)
            # This is a bit complex - we need to identify parameters
            if re.search(r'\(.*static\s+(double|int|float|bool)', line):
                # Extract the part inside parentheses
                match = re.search(r'(\([^)]*\))', line)
                if match:
                    params = match.group(1)
                    # Remove static from parameters
                    new_params = re.sub(r'static\s+(double|int|float|bool|string)', r'\1', params)
                    line = line.replace(params, new_params)
        
        new_lines.append(line)
    
    return '\n'.join(new_lines)

def fix_static_local_variables(content):
    """Fix incorrect use of static in local variables"""
    # Pattern: static double result = ... -> double result = ...
    # But only inside functions, not class members
    
    lines = content.split('\n')
    new_lines = []
    in_function = False
    brace_count = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Track if we're inside a function
        if '{' in line:
            brace_count += line.count('{')
            if brace_count > 0 and ('(' in prev_line if 'prev_line' in locals() else False):
                in_function = True
        if '}' in line:
            brace_count -= line.count('}')
            if brace_count == 0:
                in_function = False
        
        # Fix static in local variables
        if in_function and 'static double result' in line:
            line = line.replace('static double result', 'double result')
        elif in_function and 'static double' in line and '=' in line and 'class' not in line:
            line = re.sub(r'static\s+double\s+', 'double ', line)
        
        new_lines.append(line)
        prev_line = line
    
    return '\n'.join(new_lines)

def fix_file(filepath):
    """Fix static issues in a single file"""
    print(f"Fixing: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Apply fixes
        content = fix_static_in_parameters(content)
        content = fix_static_local_variables(content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ Fixed static issues")
            return True
        else:
            print(f"   ✅ No static issues found")
            return True
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

# Fix SafeMath.mqh specifically
safemath_path = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development/Include/ProjectQuantum/Core/SafeMath.mqh")
fix_file(safemath_path)

# Also fix other core files that might have similar issues
core_files = [
    "/mnt/c/DevCenter/MT5-Unified/MQL5-Development/Include/ProjectQuantum/Core/ArrayUtils.mqh",
    "/mnt/c/DevCenter/MT5-Unified/MQL5-Development/Include/ProjectQuantum/Core/SymbolUtils.mqh",
    "/mnt/c/DevCenter/MT5-Unified/MQL5-Development/Include/ProjectQuantum/Core/Defensive.mqh"
]

for file in core_files:
    fix_file(Path(file))