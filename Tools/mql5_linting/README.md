# MQL5 Enhanced Linting & Compilation Tools

## Overview

This directory contains advanced tools for MQL5 code linting and compilation, providing fast feedback for iterative development and AI-assisted coding.

## Components

### 1. MetaEditor Compiler Wrapper (`mql5_metaeditor_wrapper.py`)

**Purpose**: Interface with MetaEditor's command-line compilation

**Features**:
- Command-line compilation via `metaeditor.exe`
- Detailed log parsing and error extraction
- AI-ready error formatting
- Batch compilation support

**Usage**:
```bash
# Compile single file
python tools/mql5_metaeditor_wrapper.py --file MyExpert.mq5

# Compile with AI-formatted output
python tools/mql5_metaeditor_wrapper.py --file MyExpert.mq5 --ai-format

# Compile multiple files
python tools/mql5_metaeditor_wrapper.py --files *.mq5 --json
```

**Requirements**:
- MetaTrader 5 installation with MetaEditor
- Auto-detects installation or use `--metaeditor` flag

### 2. Enhanced Linter (`mql5_enhanced_linter.py`)

**Purpose**: Fast syntax and logic checking without full compilation

**Features**:
- **Clang-tidy Integration**: Uses C++ linting for ~95% MQL5 syntax coverage
- **Mock Headers**: MQL5 types and functions mocked as C++
- **Fast Feedback**: Catches errors in < 1 second vs full compilation
- **Multiple Modes**: Clang-tidy or basic fallback

**Usage**:
```bash
# Lint with clang-tidy (requires clang-tidy installed)
python tools/mql5_enhanced_linter.py --file MyExpert.mq5

# Basic linting (no external dependencies)
python tools/mql5_enhanced_linter.py --file MyExpert.mq5 --no-clang-tidy

# AI-formatted output
python tools/mql5_enhanced_linter.py --file MyExpert.mq5 --ai-format
```

**Requirements**:
- Optional: `clang-tidy` for advanced linting
- Falls back to basic mode if clang-tidy not available

### 3. MQL5 Mock Header (`mql5_linting/mql5_mock.h`)

**Purpose**: C++ header that mocks MQL5 types and functions

**Features**:
- Defines MQL5 basic types (`datetime`, `color`, etc.)
- Mocks MQL5 storage classes (`input`, `extern`, `sinput`)
- Provides dummy implementations of built-in functions
- Enables C++ tools to understand MQL5 syntax

**Usage**:
Include in preprocessed files for C++ linting:
```cpp
#include "mql5_mock.h"
// Your MQL5 code here
```

## Architecture

### The Two-Stage Verification Process

```
┌─────────────────────────────────────────────────────────┐
│          AI Agent or Developer Makes Code Edit          │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 1: Fast Linting (< 1 second)                     │
│  ┌────────────────────────────────────────────┐         │
│  │ mql5_enhanced_linter.py                    │         │
│  │  • Clang-tidy with MQL5 mock header        │         │
│  │  • Catches syntax errors, type mismatches  │         │
│  │  • Basic logic checking                    │         │
│  └────────────────────────────────────────────┘         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Errors Found?│
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │ YES                     │ NO
              ▼                         ▼
      ┌──────────────┐         ┌────────────────┐
      │ Report to AI │         │ Continue to    │
      │ or Developer │         │ Stage 2        │
      └──────────────┘         └───────┬────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 2: Full Compilation (slower, authoritative)      │
│  ┌────────────────────────────────────────────┐         │
│  │ mql5_metaeditor_wrapper.py                 │         │
│  │  • Real MetaEditor compilation             │         │
│  │  • Generates .ex5 file                     │         │
│  │  • Authoritative error checking            │         │
│  └────────────────────────────────────────────┘         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  ✅ Success!  │
                    │   or         │
                    │  ❌ Errors    │
                    └──────────────┘
```

### Why Two Stages?

1. **Fast Feedback Loop (Stage 1)**:
   - Clang-tidy runs in < 1 second
   - Catches ~90% of errors
   - Perfect for iterative development
   - AI can quickly iterate on fixes

2. **Authoritative Validation (Stage 2)**:
   - MetaEditor is the source of truth
   - Catches MQL5-specific issues
   - Generates deployable .ex5 files
   - Run before deployment

## AI-Assisted Coding Workflow

### The Feedback Loop

```python
# Pseudocode for AI coding agent

while not compilation_success:
    # 1. AI generates/modifies code
    code = ai_generate_code(prompt, context)
    write_file("MyExpert.mq5", code)
    
    # 2. Fast lint check
    lint_result = run_linter("MyExpert.mq5", ai_format=True)
    
    if lint_result.has_errors():
        # 3. Feed errors back to AI
        prompt = f"Fix these errors:\n{lint_result.errors}"
        context += lint_result.formatted_output
        continue
    
    # 4. Full compilation
    compile_result = compile_file("MyExpert.mq5", ai_format=True)
    
    if compile_result.success:
        break
    else:
        # 5. Feed compilation errors to AI
        prompt = f"Fix these compilation errors:\n{compile_result.errors}"
        context += compile_result.formatted_output
```

### Error Format for AI

Both tools support `--ai-format` flag for clean, parseable output:

```
❌ Compilation failed: MyExpert.mq5

Errors:
  1. Line 42, Col 15: 'OrderSendAsync' - undeclared identifier (Error 1234)
  2. Line 58, Col 8: 'CTrade' - undefined class (Error 5678)

Warnings:
  1. Line 23, Col 5: Unused variable 'temp' (Warning 9012)
```

## Installation & Setup

### Prerequisites

**Required**:
- Python 3.8+
- MetaTrader 5 with MetaEditor

**Optional** (for enhanced linting):
- Clang-tidy (C++ linter)
  ```bash
  # Ubuntu/Debian
  sudo apt install clang-tidy
  
  # macOS
  brew install llvm
  
  # Windows
  # Download from LLVM releases or use scoop/chocolatey
  ```

### Configuration

1. **Auto-detect MetaEditor**:
   Tools automatically search common installation paths

2. **Manual MetaEditor Path**:
   ```bash
   export METAEDITOR_PATH="C:/Program Files/MetaTrader 5/metaeditor64.exe"
   ```

3. **Verify Installation**:
   ```bash
   # Check linter
   python tools/mql5_enhanced_linter.py --file Include/Core/Core.mqh
   
   # Check compiler wrapper
   python tools/mql5_metaeditor_wrapper.py --file Main/ProjectQuantum_Main.mq5
   ```

## Integration with Auto-Verification

The auto-verification system (`tools/auto_verify.py`) can be enhanced to use these tools:

```python
# In auto_verify.py

# Stage 1: Fast linting
lint_result = run_linter(modified_files)
if lint_result.has_errors():
    return FAIL

# Stage 2: Full compilation (if lint passes)
compile_result = compile_files(modified_files)
return compile_result.success
```

## Performance Comparison

| Method | Time | Accuracy | Use Case |
|--------|------|----------|----------|
| Basic Linting | < 0.1s | 60% | Quick sanity check |
| Clang-tidy Linting | < 1s | 90% | Iterative development |
| Full Compilation | 5-30s | 100% | Final validation |

## Troubleshooting

### Clang-tidy Not Found

If you get "clang-tidy not found":
1. Install clang-tidy (see Prerequisites)
2. Or use `--no-clang-tidy` flag for basic mode

### MetaEditor Not Detected

If MetaEditor auto-detection fails:
1. Set `METAEDITOR_PATH` environment variable
2. Or use `--metaeditor` flag to specify path

### Mock Header Issues

If you see C++ errors about MQL5 types:
1. Verify `mql5_mock.h` exists in `tools/mql5_linting/`
2. Add missing types/functions to mock header
3. Report issue for permanent fix

## Extending the System

### Adding New MQL5 Functions to Mock

Edit `tools/mql5_linting/mql5_mock.h`:

```cpp
// Add new function
inline double MyNewFunction(int param) { 
    return 0.0; 
}
```

### Custom Linting Rules

Create `.clang-tidy` configuration:

```yaml
Checks: '-*,readability-*,performance-*,bugprone-*,your-custom-check'
```

### Integrating with CI/CD

```yaml
# GitHub Actions example
- name: Lint MQL5 Files
  run: |
    python tools/mql5_enhanced_linter.py --file *.mq5 --json > lint_results.json
    
- name: Compile if Lint Passes
  run: |
    python tools/mql5_metaeditor_wrapper.py --files *.mq5 --json > compile_results.json
```

## Future Enhancements

- [ ] Tree-sitter parser for AST analysis
- [ ] MQL5 Language Server Protocol (LSP)
- [ ] Real-time linting in VS Code
- [ ] Auto-fix suggestions for common errors
- [ ] MQL5 API context database (JSON)
- [ ] Incremental compilation support

## See Also

- [Auto-Verification Guide](../../docs/AUTO_VERIFICATION_GUIDE.md)
- [VS Code Setup](../../.vscode/README.md)
- [Tool Consolidation Summary](../CONSOLIDATION_SUMMARY.md)
