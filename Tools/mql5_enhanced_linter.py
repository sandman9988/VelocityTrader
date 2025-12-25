#!/usr/bin/env python3
"""
ProjectQuantum Enhanced MQL5 Linter
Fast syntax and logic checking using C++ tooling

This module provides:
1. Clang-tidy integration for MQL5 files
2. Fast syntax checking without full compilation
3. Type checking and logic validation
4. AI-ready error formatting

Author: Renier De Jager
Version: 1.216
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any


class MQL5Linter:
    """Fast MQL5 linting using C++ tools"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize linter
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.mock_header = Path(__file__).parent / "mql5_linting" / "mql5_mock.h"
        self.results = []
        
    def lint_file(self, file_path: Path, use_clang_tidy: bool = True) -> Dict[str, Any]:
        """
        Lint a single MQL5 file
        
        Args:
            file_path: Path to .mq5 or .mqh file
            use_clang_tidy: Use clang-tidy if available
            
        Returns:
            Dictionary with linting results
        """
        result = {
            "file": str(file_path),
            "success": True,
            "errors": [],
            "warnings": [],
            "method": "unknown"
        }
        
        # Try clang-tidy first
        if use_clang_tidy and self._has_clang_tidy():
            return self._lint_with_clang_tidy(file_path)
        
        # Fallback to basic syntax checking
        return self._lint_basic(file_path)
    
    def _has_clang_tidy(self) -> bool:
        """Check if clang-tidy is available"""
        try:
            subprocess.run(
                ["clang-tidy", "--version"],
                capture_output=True,
                timeout=5
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _lint_with_clang_tidy(self, file_path: Path) -> Dict[str, Any]:
        """
        Lint using clang-tidy with MQL5 mock header
        
        Args:
            file_path: Path to file
            
        Returns:
            Linting results
        """
        result = {
            "file": str(file_path),
            "success": True,
            "errors": [],
            "warnings": [],
            "method": "clang-tidy"
        }
        
        try:
            # Create temporary preprocessed file with mock header
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as tf:
                temp_file = Path(tf.name)
                
                # Add mock header include
                tf.write(f'#include "{self.mock_header.absolute()}"\n')
                
                # Add original file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Remove MQL5-specific preprocessor directives that might confuse clang
                    content = self._preprocess_mql5(content)
                    tf.write(content)
            
            # Run clang-tidy
            cmd = [
                "clang-tidy",
                str(temp_file),
                "--checks=-*,readability-*,performance-*,bugprone-*",
                "--",
                "-std=c++11"
            ]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse output
            output = process.stdout + process.stderr
            errors, warnings = self._parse_clang_tidy_output(output, file_path)
            
            result["errors"] = errors
            result["warnings"] = warnings
            result["success"] = len(errors) == 0
            result["raw_output"] = output
            
            # Clean up
            temp_file.unlink()
            
        except subprocess.TimeoutExpired:
            result["success"] = False
            result["errors"].append({
                "line": 0,
                "column": 0,
                "message": "Linting timeout",
                "severity": "error"
            })
        except Exception as e:
            result["success"] = False
            result["errors"].append({
                "line": 0,
                "column": 0,
                "message": f"Linting error: {str(e)}",
                "severity": "error"
            })
        
        return result
    
    def _preprocess_mql5(self, content: str) -> str:
        """
        Preprocess MQL5 code for C++ linting
        
        Args:
            content: MQL5 source code
            
        Returns:
            Preprocessed content
        """
        # Remove #property directives (MQL5-specific)
        content = '\n'.join(
            line for line in content.split('\n')
            if not line.strip().startswith('#property')
        )
        
        # Convert input group to comment
        content = content.replace('input group', '// input group')
        
        return content
    
    def _parse_clang_tidy_output(self, output: str, file_path: Path) -> tuple:
        """
        Parse clang-tidy output
        
        Args:
            output: Clang-tidy output
            file_path: Original file path
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Parse clang-tidy output format:
        # file.cpp:10:5: warning: message [check-name]
        import re
        pattern = r'(.+?):(\d+):(\d+):\s+(warning|error):\s+(.+?)\s+\[(.+?)\]'
        
        for match in re.finditer(pattern, output):
            item = {
                "line": int(match.group(2)),
                "column": int(match.group(3)),
                "severity": match.group(4),
                "message": match.group(5).strip(),
                "check": match.group(6).strip()
            }
            
            if item["severity"] == "error":
                errors.append(item)
            else:
                warnings.append(item)
        
        return errors, warnings
    
    def _lint_basic(self, file_path: Path) -> Dict[str, Any]:
        """
        Basic syntax checking without external tools

        Args:
            file_path: Path to file

        Returns:
            Basic linting results
        """
        import re

        result = {
            "file": str(file_path),
            "success": True,
            "errors": [],
            "warnings": [],
            "method": "basic"
        }

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            lines = content.split('\n')

            # Track brace balance across file
            brace_count = 0
            paren_count = 0
            in_multiline_comment = False
            in_string = False

            # Patterns for recognizing constructs that don't need semicolons
            func_def_pattern = re.compile(
                r'^[\w\s\*&:<>]+\s+\w+\s*\([^)]*\)\s*(const)?\s*$'
            )
            control_flow_pattern = re.compile(
                r'^\s*(if|else\s*if|else|while|for|switch|do)\s*[\(\{]?'
            )
            struct_class_pattern = re.compile(
                r'^\s*(struct|class|enum)\s+\w+'
            )

            for i, line in enumerate(lines, 1):
                original_line = line
                line_stripped = line.strip()

                # Skip empty lines
                if not line_stripped:
                    continue

                # Handle multi-line comments
                if '/*' in line_stripped and '*/' not in line_stripped:
                    in_multiline_comment = True
                    continue
                if in_multiline_comment:
                    if '*/' in line_stripped:
                        in_multiline_comment = False
                    continue

                # Skip single-line comments
                if line_stripped.startswith('//'):
                    continue

                # Remove inline comments for analysis
                comment_pos = line_stripped.find('//')
                if comment_pos > 0:
                    line_stripped = line_stripped[:comment_pos].strip()

                # Skip preprocessor directives
                if line_stripped.startswith('#'):
                    continue

                # Count braces (excluding those in strings/comments)
                for char in line_stripped:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                    elif char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1

                # Check for unbalanced braces going negative
                if brace_count < 0:
                    result["errors"].append({
                        "line": i,
                        "column": 1,
                        "message": "Unmatched closing brace",
                        "severity": "error"
                    })
                    brace_count = 0  # Reset to continue checking

                # Check for common real issues

                # 1. Empty blocks (but not for forward declarations)
                if line_stripped == '{}':
                    # Check previous line for context
                    if i > 1:
                        prev = lines[i - 2].strip()
                        if not prev.endswith(';') and 'class' not in prev:
                            result["warnings"].append({
                                "line": i,
                                "column": 1,
                                "message": "Empty block - consider adding implementation or comment",
                                "severity": "warning"
                            })

                # 2. Assignment in condition (common bug)
                # Only check the condition part inside if(...), not the statement after
                if_match = re.search(r'\bif\s*\(([^)]+)\)', line_stripped)
                if if_match:
                    condition = if_match.group(1)
                    # Look for single = that's not ==, !=, <=, >=
                    if re.search(r'(?<![=!<>])=(?!=)', condition):
                        result["warnings"].append({
                            "line": i,
                            "column": 1,
                            "message": "Possible assignment in condition (use == for comparison)",
                            "severity": "warning"
                        })

                # 3. Potential division by zero (basic check)
                if re.search(r'/\s*0[^.]', line_stripped):
                    result["warnings"].append({
                        "line": i,
                        "column": 1,
                        "message": "Potential division by zero",
                        "severity": "warning"
                    })

                # 4. TODO/FIXME comments
                if 'TODO' in original_line or 'FIXME' in original_line:
                    result["warnings"].append({
                        "line": i,
                        "column": 1,
                        "message": "TODO/FIXME marker found",
                        "severity": "info"
                    })

                # 5. Very long lines (readability)
                if len(original_line) > 150:
                    result["warnings"].append({
                        "line": i,
                        "column": 150,
                        "message": f"Line too long ({len(original_line)} chars)",
                        "severity": "info"
                    })

                # 6. FINANCIAL SAFETY: Lossy type conversions (critical for money)
                # Explicit casts that lose precision
                lossy_casts = [
                    (r'\(int\)\s*\w+', 'Cast to int loses decimal precision'),
                    (r'\(short\)\s*\w+', 'Cast to short may overflow'),
                    (r'\(char\)\s*\w+', 'Cast to char loses data'),
                    (r'\(float\)\s*\w+', 'Cast to float loses double precision'),
                    (r'\(uint\)\s*-', 'Cast negative to unsigned'),
                    (r'\(ulong\)\s*-', 'Cast negative to unsigned long'),
                ]
                for pattern, msg in lossy_casts:
                    if re.search(pattern, line_stripped):
                        result["warnings"].append({
                            "line": i,
                            "column": 1,
                            "message": f"FINANCIAL RISK: {msg}",
                            "severity": "warning"
                        })

                # 7. FINANCIAL SAFETY: Implicit integer division (loses decimals)
                # Pattern: int/int without explicit double conversion
                if re.search(r'\b\d+\s*/\s*\d+\b', line_stripped):
                    # Check if not already in a double context
                    if not re.search(r'\d+\.\d*\s*/|\s*/\s*\d+\.\d*', line_stripped):
                        result["warnings"].append({
                            "line": i,
                            "column": 1,
                            "message": "FINANCIAL RISK: Integer division may lose decimal precision",
                            "severity": "warning"
                        })

                # 8. SECURITY: Magic numbers in financial context
                # Large numbers that look like prices/amounts without constants
                if re.search(r'[=<>+\-*/]\s*\d{4,}\.?\d*\s*[;,)\]]', line_stripped):
                    if not line_stripped.startswith('#define') and 'const' not in line_stripped:
                        result["warnings"].append({
                            "line": i,
                            "column": 1,
                            "message": "SECURITY: Magic number detected - use named constant",
                            "severity": "warning"
                        })

                # 9. SECURITY: Hardcoded lot sizes or monetary values
                lot_patterns = [
                    r'OrderSend\s*\([^)]*,\s*\d+\.?\d*\s*,',  # Hardcoded lot in OrderSend
                    r'PositionOpen\s*\([^)]*,\s*\d+\.?\d*\s*,',
                    r'lotSize\s*=\s*\d+\.?\d*\s*;',
                    r'volume\s*=\s*\d+\.?\d*\s*;',
                ]
                for pattern in lot_patterns:
                    if re.search(pattern, line_stripped, re.IGNORECASE):
                        result["warnings"].append({
                            "line": i,
                            "column": 1,
                            "message": "SECURITY: Hardcoded trading volume - use parameter",
                            "severity": "warning"
                        })

            # Track variable declarations and usage for unused variable detection
            declared_vars = {}
            used_vars = set()
            in_struct_or_class = False
            struct_brace_depth = 0

            # Second pass: detect unused variables (attack vector)
            # Only flag function-local variables, not struct/class members
            var_decl_pattern = re.compile(
                r'^\s*(?:int|double|float|string|bool|long|ulong|datetime|color)\s+'
                r'(\w+)\s*[;=]'
            )

            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                if line_stripped.startswith('//') or not line_stripped:
                    continue

                # Track struct/class context to avoid flagging member fields
                if re.match(r'^\s*(struct|class|enum)\s+\w+', line_stripped):
                    in_struct_or_class = True
                    struct_brace_depth = 0

                if in_struct_or_class:
                    struct_brace_depth += line_stripped.count('{')
                    struct_brace_depth -= line_stripped.count('}')
                    if struct_brace_depth <= 0 and '}' in line_stripped:
                        in_struct_or_class = False
                    continue  # Skip struct/class member declarations

                # Find declarations (only in function scope)
                match = var_decl_pattern.match(line_stripped)
                if match:
                    var_name = match.group(1)
                    # Skip loop vars, globals (g_), and member vars (m_)
                    if var_name not in ['i', 'j', 'k', 'n', 'x', 'y', 'm']:
                        if not var_name.startswith('g_') and not var_name.startswith('m_'):
                            declared_vars[var_name] = i

                # Find usages (simple word boundary check)
                for var in list(declared_vars.keys()):
                    if re.search(rf'\b{var}\b', line_stripped):
                        # Check if it's not just the declaration line
                        if declared_vars[var] != i:
                            used_vars.add(var)

            # Report unused variables (potential dead code / attack vector)
            for var, line_num in declared_vars.items():
                if var not in used_vars:
                    result["warnings"].append({
                        "line": line_num,
                        "column": 1,
                        "message": f"SECURITY: Unused variable '{var}' - dead code is an attack vector",
                        "severity": "warning"
                    })

            # Final brace balance check
            if brace_count != 0:
                result["errors"].append({
                    "line": len(lines),
                    "column": 1,
                    "message": f"Unbalanced braces: {brace_count} unclosed '{{'" if brace_count > 0 else f"Unbalanced braces: {-brace_count} extra '}}'",
                    "severity": "error"
                })

            # Final paren balance check
            if paren_count != 0:
                result["errors"].append({
                    "line": len(lines),
                    "column": 1,
                    "message": f"Unbalanced parentheses: {paren_count} unclosed '('" if paren_count > 0 else f"Unbalanced parentheses: {-paren_count} extra ')'",
                    "severity": "error"
                })

            # Set success based on errors
            result["success"] = len(result["errors"]) == 0

        except Exception as e:
            result["success"] = False
            result["errors"].append({
                "line": 0,
                "column": 0,
                "message": f"Failed to lint file: {str(e)}",
                "severity": "error"
            })

        return result
    
    def format_for_ai(self, lint_result: Dict[str, Any]) -> str:
        """
        Format linting results for AI consumption
        
        Args:
            lint_result: Result from lint_file()
            
        Returns:
            Formatted output
        """
        if lint_result["success"]:
            return f"✅ Linting passed: {lint_result['file']}"
        
        output = [
            f"⚠️  Linting issues found: {lint_result['file']}",
            f"Method: {lint_result['method']}",
            ""
        ]
        
        if lint_result.get("errors"):
            output.append("Errors:")
            for i, error in enumerate(lint_result["errors"], 1):
                output.append(
                    f"  {i}. Line {error['line']}, Col {error['column']}: "
                    f"{error['message']}"
                )
            output.append("")
        
        if lint_result.get("warnings"):
            output.append("Warnings:")
            for i, warning in enumerate(lint_result["warnings"][:5], 1):  # Limit warnings
                output.append(
                    f"  {i}. Line {warning['line']}, Col {warning['column']}: "
                    f"{warning['message']}"
                )
            if len(lint_result["warnings"]) > 5:
                output.append(f"  ... and {len(lint_result['warnings']) - 5} more warnings")
        
        return "\n".join(output)


def main():
    """CLI interface for MQL5 linter"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fast MQL5 Linter using C++ Tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Lint single file with clang-tidy
  python mql5_enhanced_linter.py --file MyExpert.mq5
  
  # Lint without clang-tidy (basic mode)
  python mql5_enhanced_linter.py --file MyExpert.mq5 --no-clang-tidy
  
  # Format for AI
  python mql5_enhanced_linter.py --file MyExpert.mq5 --ai-format
        """
    )
    
    parser.add_argument('--file', type=Path, required=True, help='File to lint')
    parser.add_argument('--no-clang-tidy', action='store_true', help='Skip clang-tidy')
    parser.add_argument('--ai-format', action='store_true', help='Format for AI')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    linter = MQL5Linter()
    result = linter.lint_file(args.file, use_clang_tidy=not args.no_clang_tidy)
    
    if args.json:
        print(json.dumps(result, indent=2))
    elif args.ai_format:
        print(linter.format_for_ai(result))
    else:
        print(f"Linting {'passed' if result['success'] else 'failed'}: {result['file']}")
        print(f"Method: {result['method']}")
        if result.get('errors'):
            print(f"  Errors: {len(result['errors'])}")
        if result.get('warnings'):
            print(f"  Warnings: {len(result['warnings'])}")
    
    return 0 if result['success'] else 1


if __name__ == "__main__":
    sys.exit(main())
