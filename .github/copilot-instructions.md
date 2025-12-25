# GitHub Copilot Instructions for VelocityTrader

**These rules are mandatory for all MQL5 code suggestions.**

## Quick Reference

| Operation | Pattern to Use |
|-----------|----------------|
| Division | `SafeDivide(a, b, 0.0)` |
| Array access | `if(i >= 0 && i < ArraySize(arr))` before access |
| ArrayResize | `if(ArrayResize(arr, n) != n) return false;` |
| File handle | `if(h == INVALID_HANDLE) return false;` |
| Float compare | `MathAbs(a - b) < EPSILON` |
| Square root | `(x >= 0) ? MathSqrt(x) : 0.0` |
| OrderSend | Always check `ResultRetcode()` after |
| External data | `MathIsValidNumber(value)` before use |

## Numerical Safety

```mql5
// Division - use SafeDivide
double rate = SafeDivide(profit, trades, 0.0);

// Float comparison - use epsilon
if(MathAbs(price - target) < Point)

// Square root - validate input
double std = (variance >= 0) ? MathSqrt(variance) : 0.0;
```

## Memory Safety

```mql5
// Array bounds - always check
if(i >= 0 && i < ArraySize(arr))
    arr[i] = value;

// ArrayResize - check return
if(ArrayResize(buffer, size) != size)
    return false;
```

## Execution Safety

```mql5
// Normalize lots before trading
double lots = NormalizeLots(symbol, calculatedLots);

// Check trade result
if(!trade.Buy(lots, symbol, price, sl, tp))
{
    Log(LOG_ERROR, StringFormat("Trade failed: %d", trade.ResultRetcode()));
    return false;
}
```

## Risk Controls

```mql5
// Check drawdown in OnTick
if(IsDrawdownExceeded())
    return;

// Limit position size
lots = MathMin(lots, MAX_POSITION_SIZE);
```

## Data Integrity

```mql5
// Validate historical data
double close = iClose(symbol, period, shift);
if(close == 0 || close == EMPTY_VALUE)
    return;

// Validate file handles
int h = FileOpen(filename, FILE_READ);
if(h == INVALID_HANDLE)
    return false;
```

## Logging

```mql5
// Use Log() with appropriate level
Log(LOG_ERROR, "Critical failure");
Log(LOG_WARNING, "Spread too wide");
Log(LOG_INFO, "Position opened");
```

## Project Helpers (VT_Definitions.mqh)

- `SafeDivide(num, denom, default)` - Safe division
- `Log(level, message)` - Structured logging
- `LOG_ERROR`, `LOG_WARNING`, `LOG_INFO`, `LOG_DEBUG` - Log levels

---
*Based on financial audit of 418 findings*
