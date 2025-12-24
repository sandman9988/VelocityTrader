#!/usr/bin/env python3
"""
ProjectQuantum Enhanced MQL5 Compiler Wrapper
Integrates MetaEditor command-line compilation with detailed error parsing

This module provides:
1. Command-line compilation via metaeditor.exe
2. Detailed log parsing and error extraction
3. Integration with auto-verification system
4. AI-ready error formatting

Author: Renier De Jager
Version: 1.216
"""

import os
import sys
import re
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class MetaEditorCompiler:
    """Wrapper for MetaEditor command-line compilation"""
    
    def __init__(self, metaeditor_path: Optional[str] = None):
        """
        Initialize compiler with MetaEditor path
        
        Args:
            metaeditor_path: Path to metaeditor.exe (auto-detected if None)
        """
        self.metaeditor_path = metaeditor_path or self._find_metaeditor()
        self.compilation_results = []
        
    def _find_metaeditor(self) -> Optional[str]:
        """Auto-detect MetaEditor installation"""
        # Common installation paths
        possible_paths = [
            r"C:\Program Files\MetaTrader 5\metaeditor64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\metaeditor.exe",
            r"C:\Program Files\MetaTrader 5\metaeditor.exe",
            # Add more paths as needed
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        return None
    
    def compile_file(self, 
                    file_path: Path, 
                    log_path: Optional[Path] = None,
                    timeout: int = 60) -> Dict[str, Any]:
        """
        Compile a single MQL5 file using MetaEditor CLI
        
        Args:
            file_path: Path to .mq5 or .mqh file
            log_path: Path to log file (temp file if None)
            timeout: Compilation timeout in seconds
            
        Returns:
            Dictionary with compilation results
        """
        if not self.metaeditor_path:
            return {
                "success": False,
                "error": "MetaEditor not found. Please set METAEDITOR_PATH environment variable.",
                "file": str(file_path)
            }
        
        # Create temp log file if not specified
        if log_path is None:
            log_fd, log_path = tempfile.mkstemp(suffix=".log", prefix="mql5_compile_")
            os.close(log_fd)
            log_path = Path(log_path)
        
        result = {
            "file": str(file_path),
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "errors": [],
            "warnings": [],
            "log_path": str(log_path)
        }
        
        try:
            # Build command
            cmd = [
                str(self.metaeditor_path),
                "/compile:" + str(file_path.absolute()),
                "/log:" + str(log_path.absolute())
            ]
            
            # Execute compilation
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            result["return_code"] = process.returncode
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            
            # Parse log file
            if log_path.exists():
                errors, warnings = self._parse_log_file(log_path)
                result["errors"] = errors
                result["warnings"] = warnings
                result["success"] = len(errors) == 0
            else:
                result["error"] = "Log file not created"
            
            # Clean up temp log file
            if log_path.exists() and "/tmp" in str(log_path):
                log_path.unlink()
            
        except subprocess.TimeoutExpired:
            result["error"] = f"Compilation timeout after {timeout} seconds"
        except Exception as e:
            result["error"] = f"Compilation error: {str(e)}"
        
        self.compilation_results.append(result)
        return result
    
    def _parse_log_file(self, log_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse MetaEditor log file for errors and warnings
        
        Args:
            log_path: Path to log file
            
        Returns:
            Tuple of (errors, warnings) lists
        """
        errors = []
        warnings = []
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
            
            # Parse error patterns
            # Example: "filename.mq5(42,15) : error 1234: 'function' - undeclared identifier"
            error_pattern = r'(.+?)\((\d+),(\d+)\)\s*:\s*error\s+(\d+):\s*(.+)'
            warning_pattern = r'(.+?)\((\d+),(\d+)\)\s*:\s*warning\s+(\d+):\s*(.+)'
            
            for match in re.finditer(error_pattern, log_content):
                errors.append({
                    "file": match.group(1).strip(),
                    "line": int(match.group(2)),
                    "column": int(match.group(3)),
                    "code": match.group(4),
                    "message": match.group(5).strip(),
                    "type": "error"
                })
            
            for match in re.finditer(warning_pattern, log_content):
                warnings.append({
                    "file": match.group(1).strip(),
                    "line": int(match.group(2)),
                    "column": int(match.group(3)),
                    "code": match.group(4),
                    "message": match.group(5).strip(),
                    "type": "warning"
                })
            
        except Exception as e:
            errors.append({
                "file": str(log_path),
                "line": 0,
                "column": 0,
                "code": "PARSE_ERROR",
                "message": f"Failed to parse log file: {str(e)}",
                "type": "error"
            })
        
        return errors, warnings
    
    def compile_batch(self, 
                      file_paths: List[Path],
                      max_workers: int = 4,
                      stop_on_error: bool = False) -> Dict[str, Any]:
        """
        Compile multiple files
        
        Args:
            file_paths: List of files to compile
            max_workers: Maximum parallel compilations (not implemented yet)
            stop_on_error: Stop on first error
            
        Returns:
            Summary of compilation results
        """
        results = {
            "total": len(file_paths),
            "success": 0,
            "failed": 0,
            "files": []
        }
        
        for file_path in file_paths:
            result = self.compile_file(file_path)
            results["files"].append(result)
            
            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1
                if stop_on_error:
                    break
        
        return results
    
    def format_errors_for_ai(self, compilation_result: Dict[str, Any]) -> str:
        """
        Format compilation errors in a way that's useful for AI assistants
        
        Args:
            compilation_result: Result from compile_file()
            
        Returns:
            Formatted error message suitable for AI context
        """
        if compilation_result["success"]:
            return f"✅ Compilation successful: {compilation_result['file']}"
        
        output = [
            f"❌ Compilation failed: {compilation_result['file']}",
            ""
        ]
        
        if compilation_result.get("errors"):
            output.append("Errors:")
            for i, error in enumerate(compilation_result["errors"], 1):
                output.append(
                    f"  {i}. Line {error['line']}, Col {error['column']}: "
                    f"{error['message']} (Error {error['code']})"
                )
            output.append("")
        
        if compilation_result.get("warnings"):
            output.append("Warnings:")
            for i, warning in enumerate(compilation_result["warnings"], 1):
                output.append(
                    f"  {i}. Line {warning['line']}, Col {warning['column']}: "
                    f"{warning['message']} (Warning {warning['code']})"
                )
        
        return "\n".join(output)


def main():
    """CLI interface for compiler wrapper"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MetaEditor Command-Line Compiler Wrapper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compile single file
  python mql5_metaeditor_wrapper.py --file MyExpert.mq5
  
  # Compile with custom MetaEditor path
  python mql5_metaeditor_wrapper.py --file MyExpert.mq5 --metaeditor "C:/MT5/metaeditor64.exe"
  
  # Compile multiple files
  python mql5_metaeditor_wrapper.py --files *.mq5
  
  # Output for AI processing
  python mql5_metaeditor_wrapper.py --file MyExpert.mq5 --ai-format
        """
    )
    
    parser.add_argument('--file', type=Path, help='Single file to compile')
    parser.add_argument('--files', nargs='+', type=Path, help='Multiple files to compile')
    parser.add_argument('--metaeditor', help='Path to metaeditor.exe')
    parser.add_argument('--log', type=Path, help='Log file path')
    parser.add_argument('--ai-format', action='store_true', help='Format output for AI')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--stop-on-error', action='store_true', help='Stop on first error')
    
    args = parser.parse_args()
    
    if not args.file and not args.files:
        parser.print_help()
        return 1
    
    # Initialize compiler
    compiler = MetaEditorCompiler(args.metaeditor)
    
    # Compile file(s)
    if args.file:
        result = compiler.compile_file(args.file, args.log)
        
        if args.json:
            print(json.dumps(result, indent=2))
        elif args.ai_format:
            print(compiler.format_errors_for_ai(result))
        else:
            print(f"Compilation {'succeeded' if result['success'] else 'failed'}: {result['file']}")
            if result.get('errors'):
                print(f"  Errors: {len(result['errors'])}")
            if result.get('warnings'):
                print(f"  Warnings: {len(result['warnings'])}")
        
        return 0 if result['success'] else 1
    
    elif args.files:
        results = compiler.compile_batch(args.files, stop_on_error=args.stop_on_error)
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"Compiled {results['total']} files:")
            print(f"  ✅ Success: {results['success']}")
            print(f"  ❌ Failed: {results['failed']}")
        
        return 0 if results['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
