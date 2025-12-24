#!/bin/bash
# ProjectQuantum Auto-Verification Wrapper Script
# 
# This script provides easy access to the auto-verification system.
# Run this after every code edit to ensure no regressions.
#
# Usage:
#   ./verify.sh          # Full verification
#   ./verify.sh --quick  # Quick verification (for iterative development)

# Get script directory (this is the project root)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run auto-verification
python3 "$PROJECT_ROOT/tools/auto_verify.py" --project "$PROJECT_ROOT" "$@"
