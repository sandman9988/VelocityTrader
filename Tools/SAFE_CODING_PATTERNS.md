# Safe Coding Patterns for VelocityTrader

Reference guide for writing code that passes DO NO HARM audits.

## Division Operations

```mql5
// BAD - will trigger CRITICAL
double rate = value / count * 100;

// GOOD - use SafeDivide helper
double rate = SafeDivide(value, count, 0.0) * 100.0;

// GOOD - explicit check
double rate = (count > 0) ? (value / count * 100) : 0.0;
```

## Array Access

```mql5
// BAD - will trigger CRITICAL
for(int i = 0; i < count; i++)
    arr[i] = value;  // No bounds check visible

// GOOD - explicit bounds check immediately before access
for(int i = 0; i < count; i++)
{
    if(i >= 0 && i < ArraySize(arr))
        arr[i] = value;
}

// GOOD - validate loop bound against array
int safeCount = MathMin(count, ArraySize(arr));
for(int i = 0; i < safeCount; i++)
    arr[i] = value;
```

## ArrayResize

```mql5
// BAD - unchecked resize
ArrayResize(buffer, newSize);
buffer[0] = value;  // Could fail if resize failed

// GOOD - check return value
if(ArrayResize(buffer, newSize) != newSize)
{
    Print("ERROR: ArrayResize failed");
    return false;
}
buffer[0] = value;
```

## File Operations

```mql5
// BAD - no handle validation
int h = FileOpen(path, FILE_READ);
string data = FileReadString(h);  // Could crash

// GOOD - validate handle
int h = FileOpen(path, FILE_READ);
if(h == INVALID_HANDLE)
{
    Print("ERROR: Cannot open ", path);
    return false;
}
string data = FileReadString(h);
FileClose(h);
```

## Numeric Validation

```mql5
// BAD - trusting external data
double price = FileReadDouble(handle);
OrderSend(symbol, OP_BUY, lots, price, ...);

// GOOD - validate before use
double price = FileReadDouble(handle);
if(!MathIsValidNumber(price) || price <= 0)
{
    Print("ERROR: Invalid price from file");
    return false;
}
```

## Quick Reference

| Pattern | Check | Fix |
|---------|-------|-----|
| `a / b` | Division by zero | `SafeDivide(a, b, default)` |
| `arr[i]` | Bounds check | `if(i >= 0 && i < ArraySize(arr))` |
| `ArrayResize()` | Return value | `if(ArrayResize(...) != size)` |
| `FileOpen()` | Handle valid | `if(h == INVALID_HANDLE)` |
| `FileRead*()` | Data valid | `MathIsValidNumber()` |

## Workflow

1. **While coding**: Run `./Tools/quick-check.sh filename.mqh`
2. **Before commit**: Hook runs automatically
3. **Full audit**: `python3 Tools/mql5_financial_auditor.py --project .`

## Pre-commit Hook

Installed at `.githooks/pre-commit`. Blocks commits with CRITICAL findings.

To bypass in emergencies (not recommended):
```bash
git commit --no-verify -m "message"
```
