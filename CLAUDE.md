# VelocityTrader - AI Agent Coding Standards

**Read this file at the start of every session. These rules are mandatory.**

This document defines coding standards derived from financial code audits. Following these rules prevents CRITICAL and HIGH severity issues that could cause financial loss or system failure.

---

## Quick Reference Card

| Operation | NEVER | ALWAYS |
|-----------|-------|--------|
| Division | `a / b` | `SafeDivide(a, b, 0.0)` |
| Array access | `arr[i]` | `if(i >= 0 && i < ArraySize(arr))` |
| ArrayResize | `ArrayResize(a, n);` | `if(ArrayResize(a, n) != n) return false;` |
| File handle | `FileRead*(h);` | `if(h == INVALID_HANDLE) return false;` |
| Float compare | `if(a == b)` | `if(MathAbs(a - b) < EPSILON)` |
| Square root | `MathSqrt(x)` | `SafeSqrt(x)` or `if(x >= 0)` |
| Logarithm | `MathLog(x)` | `SafeLog(x)` or `if(x > 0)` |
| OrderSend | `OrderSend(...);` | Check `ResultRetcode()` after |
| External data | Use directly | `MathIsValidNumber()` first |

---

## 1. NUMERICAL SAFETY (89 findings)

### NUM001: Division Operations - CRITICAL
Division by zero causes crashes or infinity values.

```mql5
// NEVER:
double rate = profit / trades;
double pct = value / total * 100;

// ALWAYS:
double rate = SafeDivide(profit, trades, 0.0);
double pct = SafeDivide(value, total, 0.0) * 100.0;

// OR explicit check:
double rate = (trades > 0) ? profit / trades : 0.0;
```

### NUM002: Float Comparison - HIGH
Direct equality comparison of floats is unreliable due to precision.

```mql5
// NEVER:
if(price == targetPrice)
if(stopLoss != 0.0)

// ALWAYS:
if(MathAbs(price - targetPrice) < Point)
if(MathAbs(stopLoss) > Point)

// Or use EPSILON constant:
#define EPSILON 0.00000001
if(MathAbs(a - b) < EPSILON)
```

### NUM005: Square Root - MEDIUM
MathSqrt with negative input returns NaN.

```mql5
// NEVER:
double std = MathSqrt(variance);

// ALWAYS:
double std = (variance >= 0) ? MathSqrt(variance) : 0.0;
// OR use SafeSqrt() helper
```

### NUM006: Logarithm - MEDIUM
MathLog with zero or negative input is undefined.

```mql5
// NEVER:
double logReturn = MathLog(price / prevPrice);

// ALWAYS:
double ratio = SafeDivide(price, prevPrice, 1.0);
double logReturn = (ratio > 0) ? MathLog(ratio) : 0.0;
```

---

## 2. MEMORY SAFETY (26 findings)

### MEM001: Array Bounds - CRITICAL
Array access without bounds check causes crashes.

```mql5
// NEVER:
for(int i = 0; i < count; i++)
    values[i] = data[i];

// ALWAYS - check bounds immediately before access:
for(int i = 0; i < count; i++)
{
    if(i >= 0 && i < ArraySize(values) && i < ArraySize(data))
    {
        values[i] = data[i];
    }
}

// OR use safe loop bound:
int safeCount = MathMin(count, MathMin(ArraySize(values), ArraySize(data)));
for(int i = 0; i < safeCount; i++)
    values[i] = data[i];
```

### MEM004: ArrayResize - HIGH
ArrayResize can fail and returns -1 on failure.

```mql5
// NEVER:
ArrayResize(buffer, newSize);
buffer[0] = value;

// ALWAYS:
if(ArrayResize(buffer, newSize) != newSize)
{
    Log(LOG_ERROR, "ArrayResize failed");
    return false;
}
buffer[0] = value;
```

### MEM002/003: Dynamic Memory - HIGH
Dynamic allocation can fail; every `new` needs matching `delete`.

```mql5
// NEVER:
CMyObject* obj = new CMyObject();
obj.DoWork();

// ALWAYS:
CMyObject* obj = new CMyObject();
if(obj == NULL)
{
    Log(LOG_ERROR, "Memory allocation failed");
    return false;
}
obj.DoWork();
// ... later:
delete obj;
obj = NULL;
```

---

## 3. EXECUTION SAFETY (33 findings)

### EXEC001: Order Validation - CRITICAL
Always validate before OrderSend.

```mql5
// NEVER:
trade.Buy(lots, symbol, price, sl, tp);

// ALWAYS:
// 1. Validate symbol
if(!SymbolSelect(symbol, true))
    return false;

// 2. Validate volume
double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
lots = MathFloor(lots / lotStep) * lotStep;
lots = MathMax(minLot, MathMin(maxLot, lots));

// 3. Validate stops
int stopLevel = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);

// 4. Execute and check result
if(!trade.Buy(lots, symbol, price, sl, tp))
{
    Log(LOG_ERROR, StringFormat("Order failed: %d", trade.ResultRetcode()));
    return false;
}
```

### EXEC002: Lot Normalization - CRITICAL
Lot sizes must be normalized to broker requirements.

```mql5
// NEVER:
double lots = risk / stopDistance;
trade.Buy(lots, ...);

// ALWAYS:
double lots = risk / stopDistance;
lots = NormalizeLots(symbol, lots);  // Normalize to step, min, max

double NormalizeLots(string symbol, double lots)
{
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

    lots = MathFloor(lots / lotStep) * lotStep;
    return MathMax(minLot, MathMin(maxLot, lots));
}
```

### EXEC004: Price Normalization - HIGH
Prices must be normalized to symbol digits.

```mql5
// NEVER:
double entry = Ask + 10 * Point;

// ALWAYS:
double entry = NormalizeDouble(Ask + 10 * Point, _Digits);
```

### EXEC005: Trade Result - MEDIUM
Always check trade execution result.

```mql5
// NEVER:
trade.Buy(lots, symbol, price, sl, tp);
// assume success

// ALWAYS:
if(!trade.Buy(lots, symbol, price, sl, tp))
{
    uint retcode = trade.ResultRetcode();
    Log(LOG_ERROR, StringFormat("Trade failed: %d - %s",
        retcode, trade.ResultRetcodeDescription()));
    return false;
}
```

---

## 4. RISK CONTROLS (14 findings)

### RISK001: Position Size Limits - CRITICAL
Always enforce maximum position size.

```mql5
// NEVER:
double lots = CalculateLotSize(risk);
trade.Buy(lots, ...);

// ALWAYS:
double lots = CalculateLotSize(risk);
lots = MathMin(lots, MAX_POSITION_SIZE);
lots = MathMin(lots, GetRemainingExposureLimit());
```

### RISK002: Drawdown Check - CRITICAL
Check drawdown before every trade decision.

```mql5
void OnTick()
{
    // ALWAYS check drawdown first
    if(IsDrawdownExceeded())
    {
        Log(LOG_WARNING, "Drawdown limit reached - trading suspended");
        return;
    }

    // Then proceed with trading logic
    // ...
}

bool IsDrawdownExceeded()
{
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double drawdown = (balance - equity) / balance * 100;
    return drawdown > MAX_DRAWDOWN_PERCENT;
}
```

### RISK003: Account State - HIGH
Verify margin and equity before trading.

```mql5
// ALWAYS check before OrderSend:
double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
double requiredMargin = lots * SymbolInfoDouble(symbol, SYMBOL_MARGIN_INITIAL);

if(freeMargin < requiredMargin * 1.5)  // 50% buffer
{
    Log(LOG_WARNING, "Insufficient margin");
    return false;
}
```

---

## 5. DATA INTEGRITY (42 findings)

### DATA001: Input Validation - HIGH
Validate all user input parameters in OnInit().

```mql5
int OnInit()
{
    // Validate all inputs
    if(InpLotSize <= 0 || InpLotSize > 100)
    {
        Alert("Invalid lot size: ", InpLotSize);
        return INIT_PARAMETERS_INCORRECT;
    }

    if(InpStopLoss <= 0)
    {
        Alert("Stop loss must be positive");
        return INIT_PARAMETERS_INCORRECT;
    }

    return INIT_SUCCEEDED;
}
```

### DATA002: Historical Data Validity - HIGH
Always check historical data before use.

```mql5
// NEVER:
double close = iClose(symbol, period, shift);
double signal = close - iClose(symbol, period, shift + 1);

// ALWAYS:
double close = iClose(symbol, period, shift);
if(close == 0 || close == EMPTY_VALUE)
{
    Log(LOG_WARNING, "Invalid historical data");
    return;
}
```

### DATA003: File Operations - MEDIUM
Always validate file handles and check operation results.

```mql5
// NEVER:
int h = FileOpen(filename, FILE_READ);
double value = FileReadDouble(h);

// ALWAYS:
int h = FileOpen(filename, FILE_READ);
if(h == INVALID_HANDLE)
{
    Log(LOG_ERROR, StringFormat("Cannot open file: %s (error %d)",
        filename, GetLastError()));
    return false;
}

double value = FileReadDouble(h);
if(GetLastError() != 0)
{
    FileClose(h);
    return false;
}
FileClose(h);
```

### DATA005: Warmup Period - HIGH
Wait for indicator warmup before trading.

```mql5
void OnTick()
{
    static int tickCount = 0;
    tickCount++;

    // Wait for warmup
    if(tickCount < WARMUP_TICKS)
        return;

    // Check indicator has enough data
    if(BarsCalculated(indicatorHandle) < MIN_BARS_REQUIRED)
        return;

    // Now safe to trade
    // ...
}
```

### DATA007: Price Spike Detection - HIGH
Filter out anomalous price data.

```mql5
bool IsValidPriceMove(double currentPrice, double previousPrice, double atr)
{
    double move = MathAbs(currentPrice - previousPrice);
    double threshold = atr * MAX_ATR_MULTIPLIER;  // e.g., 5.0

    if(move > threshold)
    {
        Log(LOG_WARNING, StringFormat("Price spike detected: %.5f (threshold: %.5f)",
            move, threshold));
        return false;
    }
    return true;
}
```

---

## 6. DEFENSIVE PROGRAMMING (96 findings)

### DEF001: Error Logging - MEDIUM
Use structured logging with appropriate levels.

```mql5
// Use Log() helper, not Print()
Log(LOG_ERROR, "Critical failure in OrderSend");
Log(LOG_WARNING, "Spread too wide, skipping trade");
Log(LOG_INFO, "Position opened successfully");
Log(LOG_DEBUG, StringFormat("Calculated lots: %.2f", lots));
```

### DEF002: GetLastError - MEDIUM
Check and clear GetLastError() after operations that can fail.

```mql5
bool result = OrderSend(request, response);
if(!result)
{
    int error = GetLastError();
    Log(LOG_ERROR, StringFormat("OrderSend failed: %d", error));
    ResetLastError();  // Clear for next operation
    return false;
}
```

### DEF003: Null/Empty Checks - HIGH
Always validate strings and objects before use.

```mql5
// NEVER:
string symbol = PositionGetString(POSITION_SYMBOL);
double price = SymbolInfoDouble(symbol, SYMBOL_BID);

// ALWAYS:
string symbol = PositionGetString(POSITION_SYMBOL);
if(StringLen(symbol) == 0)
{
    Log(LOG_ERROR, "Empty symbol from position");
    return false;
}
```

---

## 7. REGULATORY COMPLIANCE (60 findings)

### REG001: Audit Trail - HIGH
Log all trade decisions and executions.

```mql5
// Before trade
Log(LOG_INFO, StringFormat("TRADE_SIGNAL: %s %s lots=%.2f price=%.5f sl=%.5f tp=%.5f",
    (isBuy ? "BUY" : "SELL"), symbol, lots, price, sl, tp));

// After trade
Log(LOG_INFO, StringFormat("TRADE_EXECUTED: ticket=%d retcode=%d",
    trade.ResultOrder(), trade.ResultRetcode()));
```

### REG002: Timestamps - MEDIUM
Include timestamps in all log entries.

```mql5
// Use structured logging that includes timestamps
// The Log() function should prepend: [2024-01-15 14:30:25.123]
```

---

## 8. CODE QUALITY (58 findings)

### Naming Constants
Use named constants, not magic numbers.

```mql5
// NEVER:
if(spread > 50)
ArrayResize(buffer, 1000);
Sleep(5000);

// ALWAYS:
#define MAX_SPREAD_POINTS 50
#define BUFFER_SIZE 1000
#define RETRY_DELAY_MS 5000

if(spread > MAX_SPREAD_POINTS)
ArrayResize(buffer, BUFFER_SIZE);
Sleep(RETRY_DELAY_MS);
```

---

## Project-Specific Helpers

The following helpers are defined in VT_Definitions.mqh:

```mql5
// Safe division with default value
double SafeDivide(double numerator, double denominator, double defaultValue);

// Safe array access (returns default if out of bounds)
double SafeArrayGet(const double &arr[], int index, double defaultValue);

// Logging with levels
void Log(int level, string message);
enum { LOG_ERROR=1, LOG_WARNING=2, LOG_INFO=3, LOG_DEBUG=4 };
```

---

## Pre-Commit Checklist

Before committing any MQL5 code, verify:

1. [ ] All divisions use SafeDivide() or explicit zero-check
2. [ ] All array accesses have bounds checks with ArraySize()
3. [ ] All ArrayResize() calls check return value
4. [ ] All file handles validated against INVALID_HANDLE
5. [ ] All external numeric data validated with MathIsValidNumber()
6. [ ] All float comparisons use epsilon, not ==
7. [ ] All OrderSend results checked
8. [ ] All lots normalized to broker requirements
9. [ ] Drawdown check exists in OnTick()
10. [ ] Input parameters validated in OnInit()

---

## Audit Commands

```bash
# Full audit
python3 Tools/mql5_financial_auditor.py --project .

# Critical issues only
python3 Tools/mql5_financial_auditor.py --project . --critical-only

# Quick pattern check
python3 Tools/mql5_super_audit.py --project .

# Update these instructions from findings
python3 Tools/update_ai_instructions.py --from-audit --apply
```

---

*Document Version: 2.0*
*Last Updated: 2025-12-25*
*Source: Financial audit of VelocityTrader codebase (418 findings analyzed)*
