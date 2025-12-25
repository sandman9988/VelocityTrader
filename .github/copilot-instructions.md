# GitHub Copilot Instructions for VelocityTrader

## MQL5 Safety Rules

When generating MQL5 code for this project, follow these mandatory patterns:

### Division: Always use SafeDivide
```mql5
// Use: SafeDivide(numerator, denominator, default_value)
double rate = SafeDivide(value, count, 0.0);
```

### Array Access: Always bounds check
```mql5
if(index >= 0 && index < ArraySize(array))
    array[index] = value;
```

### ArrayResize: Always verify
```mql5
if(ArrayResize(arr, size) != size) return false;
```

### File Operations: Always validate handle
```mql5
int h = FileOpen(path, FILE_READ);
if(h == INVALID_HANDLE) return false;
```

### Numeric Data: Always validate
```mql5
if(!MathIsValidNumber(value)) value = 0.0;
```

## Project Conventions

- Error logging: `Log(LOG_ERROR, "message")`
- Warning logging: `Log(LOG_WARNING, "message")`
- SafeDivide is in VT_Definitions.mqh
- All trading code must validate prices before OrderSend
