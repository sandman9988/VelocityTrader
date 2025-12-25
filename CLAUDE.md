# VelocityTrader - AI Coding Instructions

This file is read by Claude Code at session start. Follow these rules strictly.

## Critical Safety Rules (DO NO HARM)

### 1. Division Operations - ALWAYS use SafeDivide
```mql5
// NEVER write this:
double rate = value / count;

// ALWAYS write this:
double rate = SafeDivide(value, count, 0.0);
```

### 2. Array Access - ALWAYS bounds check before access
```mql5
// NEVER write this:
for(int i = 0; i < count; i++)
    arr[i] = value;

// ALWAYS write this:
if(i >= 0 && i < ArraySize(arr))
    arr[i] = value;
```

### 3. ArrayResize - ALWAYS check return value
```mql5
// NEVER write this:
ArrayResize(buffer, size);

// ALWAYS write this:
if(ArrayResize(buffer, size) != size)
{
    Print("ERROR: ArrayResize failed");
    return false;
}
```

### 4. File Handles - ALWAYS validate
```mql5
// NEVER write this:
int h = FileOpen(path, FILE_READ);
string data = FileReadString(h);

// ALWAYS write this:
int h = FileOpen(path, FILE_READ);
if(h == INVALID_HANDLE)
{
    Print("ERROR: Cannot open file: ", path);
    return false;
}
```

### 5. External Data - ALWAYS validate before use
```mql5
// NEVER trust file/network data:
double price = FileReadDouble(handle);
OrderSend(..., price, ...);

// ALWAYS validate:
double price = FileReadDouble(handle);
if(!MathIsValidNumber(price) || price <= 0)
{
    Print("ERROR: Invalid price");
    return false;
}
```

## Pre-Commit Verification

Before suggesting a commit, mentally run through:
1. Are all divisions using SafeDivide() or explicit zero checks?
2. Are all array accesses bounds-checked with ArraySize()?
3. Are all ArrayResize() calls checking return values?
4. Are all file handles validated against INVALID_HANDLE?
5. Is all external data validated with MathIsValidNumber()?

## Project-Specific Patterns

- Use `Log(LOG_ERROR, ...)` for errors, not `Print()`
- Use `SafeDivide()` helper defined in VT_Definitions.mqh
- Validate Q-values with `MathIsValidNumber()` before use
- Check `GetLastError()` after trade operations

## Audit Commands

Run before committing:
```bash
python3 Tools/mql5_financial_auditor.py --project . --critical-only
```

---
*Last updated: 2025-12-25 - Added from DO NO HARM audit findings*
