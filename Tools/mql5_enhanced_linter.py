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
            
            # Basic checks
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for common issues
                if line_stripped and not line_stripped.startswith('//'):
                    # Unmatched braces (simple check)
                    if line_stripped.count('{') != line_stripped.count('}'):
                        if '{' in line_stripped and '}' not in line_stripped:
                            result["warnings"].append({
                                "line": i,
                                "column": line.index('{') + 1,
                                "message": "Possible unmatched opening brace",
                                "severity": "warning"
                            })
                    
                    # Missing semicolons (heuristic)
                    if (line_stripped.endswith(')') and 
                        not line_stripped.startswith('if') and
                        not line_stripped.startswith('while') and
                        not line_stripped.startswith('for')):
                        result["warnings"].append({
                            "line": i,
                            "column": len(line),
                            "message": "Possible missing semicolon",
                            "severity": "warning"
                        })
        
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
