#!/bin/bash
# Quick safety check - run this frequently while coding
# Usage: ./Tools/quick-check.sh [file]

FILE=${1:-""}
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ -n "$FILE" ]; then
    echo "Checking: $FILE"
    echo "----------------------------------------"

    # Check for common dangerous patterns
    echo "Scanning for unsafe patterns..."

    # Division without zero check
    if grep -n "/ [a-zA-Z_][a-zA-Z0-9_]*[^=]" "$FILE" 2>/dev/null | grep -v "SafeDivide\|> 0\|!= 0\|== 0" | head -5; then
        echo "  ^ Potential unsafe division - use SafeDivide() or check for zero"
    fi

    # Array access without bounds check
    if grep -n "\[[a-zA-Z_][a-zA-Z0-9_]*\]" "$FILE" 2>/dev/null | grep -v "ArraySize\|< Array\|>= 0 &&" | head -5; then
        echo "  ^ Array access - ensure bounds check with ArraySize()"
    fi

    # Unchecked ArrayResize
    if grep -n "ArrayResize(" "$FILE" 2>/dev/null | grep -v "if(\|!= \|== " | head -5; then
        echo "  ^ Unchecked ArrayResize - verify return value"
    fi

    echo ""
    echo "Run full audit: python3 Tools/mql5_financial_auditor.py --project . --critical-only"
else
    # Full project quick scan
    echo "Quick project scan..."
    python3 "$PROJECT_ROOT/Tools/mql5_super_audit.py" --project "$PROJECT_ROOT" 2>&1 | tail -20
fi
