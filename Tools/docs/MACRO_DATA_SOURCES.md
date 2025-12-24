# Macro Data Sources - Broker vs External APIs
## VIX, 10-Year Yields, Dollar Index

**Version:** 1.0
**Date:** 2025-12-20

---

## 1. Broker Symbol Availability

### Common Broker Symbol Names

| Indicator | Common MT5 Symbols | Availability |
|-----------|-------------------|--------------|
| **VIX** | `VIX`, `VOLATILITY`, `VXX`, `VIXY` | ⚠️ Rare (mostly CFD brokers) |
| **10yr Yields** | `US10Y`, `USTEC10Y`, `US10YR`, `TNX` | ⚠️ Some brokers only |
| **Dollar Index** | `USDX`, `DXY`, `USDOLLAR` | ✅ Many brokers (as CFD) |

**Typical Forex Broker:** Most pure forex brokers (FXCM, Oanda, IC Markets, etc.) do **NOT** offer VIX or Treasury yields.

**CFD/Multi-Asset Brokers:** Brokers with stocks/indices (IG, Saxo, Interactive Brokers) often have these.

---

## 2. Automatic Detection & Fallback System

### MQL5 Implementation

```cpp
//+------------------------------------------------------------------+
//| CMacroDataSource.mqh - Intelligent Macro Data Sourcing          |
//+------------------------------------------------------------------+

enum ENUM_DATA_SOURCE {
    SOURCE_BROKER,      // Direct from MT5 broker
    SOURCE_CALCULATED,  // Calculated from component pairs (DXY only)
    SOURCE_WEB_API,     // WebRequest from Yahoo Finance
    SOURCE_GLOBAL_VAR,  // Manual global variables
    SOURCE_UNAVAILABLE  // No source available
};

class CMacroDataSource {
private:
    // VIX
    ENUM_DATA_SOURCE m_vix_source;
    string m_vix_symbol;

    // 10yr Yields
    ENUM_DATA_SOURCE m_yield_source;
    string m_yield_symbol;

    // Dollar Index
    ENUM_DATA_SOURCE m_dxy_source;
    string m_dxy_symbol;

    // WebRequest enabled?
    bool m_web_request_enabled;

public:
    //+------------------------------------------------------------------+
    //| Initialize - Detect best available sources                       |
    //+------------------------------------------------------------------+
    bool Initialize() {
        CLogger::Info("Detecting macro data sources...");

        // Check if WebRequest is enabled
        m_web_request_enabled = CheckWebRequestEnabled();

        // Detect VIX source
        m_vix_source = DetectVIXSource(m_vix_symbol);
        CLogger::Info(StringFormat("VIX source: %s (symbol: %s)",
                     EnumToString(m_vix_source), m_vix_symbol));

        // Detect 10yr yield source
        m_yield_source = DetectYieldSource(m_yield_symbol);
        CLogger::Info(StringFormat("10yr Yield source: %s (symbol: %s)",
                     EnumToString(m_yield_source), m_yield_symbol));

        // Detect DXY source
        m_dxy_source = DetectDXYSource(m_dxy_symbol);
        CLogger::Info(StringFormat("DXY source: %s (symbol: %s)",
                     EnumToString(m_dxy_source), m_dxy_symbol));

        return true;
    }

    //+------------------------------------------------------------------+
    //| Get VIX Value                                                     |
    //+------------------------------------------------------------------+
    double GetVIX() {
        switch(m_vix_source) {
            case SOURCE_BROKER:
                return GetBrokerPrice(m_vix_symbol);

            case SOURCE_WEB_API:
                return GetVIXFromYahoo();

            case SOURCE_GLOBAL_VAR:
                return GlobalVariableGet("VIX_CURRENT");

            default:
                CLogger::Warning("VIX source unavailable - using default 20.0");
                return 20.0;  // Neutral default
        }
    }

    //+------------------------------------------------------------------+
    //| Get 10yr Yield Value                                             |
    //+------------------------------------------------------------------+
    double GetYield10yr() {
        switch(m_yield_source) {
            case SOURCE_BROKER:
                return GetBrokerPrice(m_yield_symbol);

            case SOURCE_WEB_API:
                return GetYieldFromYahoo();

            case SOURCE_GLOBAL_VAR:
                return GlobalVariableGet("YIELD_10YR");

            default:
                CLogger::Warning("10yr Yield unavailable - using default 3.5%");
                return 3.5;  // Neutral default
        }
    }

    //+------------------------------------------------------------------+
    //| Get Dollar Index Value                                           |
    //+------------------------------------------------------------------+
    double GetDXY() {
        switch(m_dxy_source) {
            case SOURCE_BROKER:
                return GetBrokerPrice(m_dxy_symbol);

            case SOURCE_CALCULATED:
                return CalculateDXYFromPairs();

            case SOURCE_WEB_API:
                return GetDXYFromYahoo();

            case SOURCE_GLOBAL_VAR:
                return GlobalVariableGet("DXY_CURRENT");

            default:
                CLogger::Warning("DXY unavailable - using default 100.0");
                return 100.0;  // Neutral default
        }
    }

private:
    //+------------------------------------------------------------------+
    //| Detect VIX Source                                                |
    //+------------------------------------------------------------------+
    ENUM_DATA_SOURCE DetectVIXSource(string &symbol) {
        // Priority 1: Check broker symbols
        string broker_symbols[] = {"VIX", "VOLATILITY", "VXX", "VIXY", "^VIX"};

        for(int i = 0; i < ArraySize(broker_symbols); i++) {
            if(SymbolSelect(broker_symbols[i], true)) {
                symbol = broker_symbols[i];
                CLogger::Info(StringFormat("VIX available from broker: %s", symbol));
                return SOURCE_BROKER;
            }
        }

        // Priority 2: WebRequest (if enabled)
        if(m_web_request_enabled) {
            symbol = "^VIX";  // Yahoo Finance symbol
            CLogger::Info("VIX will be fetched via WebRequest (Yahoo Finance)");
            return SOURCE_WEB_API;
        }

        // Priority 3: Global variables (manual)
        if(GlobalVariableCheck("VIX_CURRENT")) {
            symbol = "VIX_CURRENT";
            CLogger::Warning("VIX will be read from global variable (manual update required)");
            return SOURCE_GLOBAL_VAR;
        }

        // No source available
        CLogger::Error("VIX not available - will use neutral default");
        return SOURCE_UNAVAILABLE;
    }

    //+------------------------------------------------------------------+
    //| Detect 10yr Yield Source                                         |
    //+------------------------------------------------------------------+
    ENUM_DATA_SOURCE DetectYieldSource(string &symbol) {
        // Priority 1: Check broker symbols
        string broker_symbols[] = {"US10Y", "USTEC10Y", "US10YR", "TNX", "^TNX"};

        for(int i = 0; i < ArraySize(broker_symbols); i++) {
            if(SymbolSelect(broker_symbols[i], true)) {
                symbol = broker_symbols[i];
                CLogger::Info(StringFormat("10yr Yield available from broker: %s", symbol));
                return SOURCE_BROKER;
            }
        }

        // Priority 2: WebRequest
        if(m_web_request_enabled) {
            symbol = "^TNX";  // Yahoo Finance: 10-year Treasury Note Yield
            CLogger::Info("10yr Yield will be fetched via WebRequest");
            return SOURCE_WEB_API;
        }

        // Priority 3: Global variables
        if(GlobalVariableCheck("YIELD_10YR")) {
            symbol = "YIELD_10YR";
            CLogger::Warning("10yr Yield from global variable (manual update)");
            return SOURCE_GLOBAL_VAR;
        }

        CLogger::Error("10yr Yield not available - will use neutral default");
        return SOURCE_UNAVAILABLE;
    }

    //+------------------------------------------------------------------+
    //| Detect DXY Source                                                |
    //+------------------------------------------------------------------+
    ENUM_DATA_SOURCE DetectDXYSource(string &symbol) {
        // Priority 1: Check broker symbols
        string broker_symbols[] = {"USDX", "DXY", "USDOLLAR", "DX"};

        for(int i = 0; i < ArraySize(broker_symbols); i++) {
            if(SymbolSelect(broker_symbols[i], true)) {
                symbol = broker_symbols[i];
                CLogger::Info(StringFormat("DXY available from broker: %s", symbol));
                return SOURCE_BROKER;
            }
        }

        // Priority 2: Calculate from component pairs (ALWAYS AVAILABLE for forex brokers)
        if(CanCalculateDXY()) {
            symbol = "CALCULATED";
            CLogger::Info("DXY will be calculated from component pairs (EURUSD, USDJPY, etc.)");
            return SOURCE_CALCULATED;
        }

        // Priority 3: WebRequest
        if(m_web_request_enabled) {
            symbol = "DX-Y.NYB";  // Yahoo Finance: Dollar Index
            CLogger::Info("DXY will be fetched via WebRequest");
            return SOURCE_WEB_API;
        }

        // Priority 4: Global variables
        if(GlobalVariableCheck("DXY_CURRENT")) {
            symbol = "DXY_CURRENT";
            CLogger::Warning("DXY from global variable (manual update)");
            return SOURCE_GLOBAL_VAR;
        }

        CLogger::Error("DXY not available - will use neutral default");
        return SOURCE_UNAVAILABLE;
    }

    //+------------------------------------------------------------------+
    //| Check if all component pairs available for DXY calculation       |
    //+------------------------------------------------------------------+
    bool CanCalculateDXY() {
        string required_pairs[] = {"EURUSD", "USDJPY", "GBPUSD", "USDCAD", "USDSEK", "USDCHF"};

        for(int i = 0; i < ArraySize(required_pairs); i++) {
            if(!SymbolSelect(required_pairs[i], true)) {
                CLogger::Warning(StringFormat("DXY calculation impossible - %s not available",
                               required_pairs[i]));
                return false;
            }
        }

        return true;
    }

    //+------------------------------------------------------------------+
    //| Calculate DXY from component FX pairs                            |
    //+------------------------------------------------------------------+
    double CalculateDXYFromPairs() {
        // DXY Formula:
        // DXY = 50.14348112 × EURUSD^(-0.576) × USDJPY^(0.136) × GBPUSD^(-0.119)
        //       × USDCAD^(0.091) × USDSEK^(0.042) × USDCHF^(0.036)

        double eurusd = SymbolInfoDouble("EURUSD", SYMBOL_BID);
        double usdjpy = SymbolInfoDouble("USDJPY", SYMBOL_BID);
        double gbpusd = SymbolInfoDouble("GBPUSD", SYMBOL_BID);
        double usdcad = SymbolInfoDouble("USDCAD", SYMBOL_BID);
        double usdsek = SymbolInfoDouble("USDSEK", SYMBOL_BID);
        double usdchf = SymbolInfoDouble("USDCHF", SYMBOL_BID);

        // Validate all prices
        if(eurusd <= 0 || usdjpy <= 0 || gbpusd <= 0 ||
           usdcad <= 0 || usdsek <= 0 || usdchf <= 0) {
            CLogger::Error("Invalid prices for DXY calculation");
            return 100.0;  // Default
        }

        double dxy = 50.14348112 *
                     MathPow(eurusd, -0.576) *
                     MathPow(usdjpy, 0.136) *
                     MathPow(gbpusd, -0.119) *
                     MathPow(usdcad, 0.091) *
                     MathPow(usdsek, 0.042) *
                     MathPow(usdchf, 0.036);

        return dxy;
    }

    //+------------------------------------------------------------------+
    //| Get price from broker symbol                                     |
    //+------------------------------------------------------------------+
    double GetBrokerPrice(string symbol) {
        double price = SymbolInfoDouble(symbol, SYMBOL_BID);

        if(price <= 0) {
            CLogger::Error(StringFormat("Invalid price for %s: %.5f", symbol, price));
            return 0.0;
        }

        return price;
    }

    //+------------------------------------------------------------------+
    //| Check if WebRequest is enabled                                   |
    //+------------------------------------------------------------------+
    bool CheckWebRequestEnabled() {
        // Try a test request to check if allowed
        char data[];
        char result[];
        string headers;

        string test_url = "https://query1.finance.yahoo.com";
        int res = WebRequest("GET", test_url, NULL, NULL, 500, data, 0, result, headers);

        if(res == -1) {
            int error = GetLastError();
            if(error == 4060) {  // ERR_FUNCTION_NOT_ALLOWED
                CLogger::Warning("WebRequest not allowed. Enable in Tools → Options → Expert Advisors");
                CLogger::Warning("Add URL: https://query1.finance.yahoo.com");
                return false;
            }
        }

        return true;
    }

    //+------------------------------------------------------------------+
    //| Get VIX from Yahoo Finance API                                   |
    //+------------------------------------------------------------------+
    double GetVIXFromYahoo() {
        string url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?interval=1d&range=1d";

        char data[];
        char result[];
        string headers;

        int timeout = 5000;  // 5 seconds
        int res = WebRequest("GET", url, NULL, NULL, timeout, data, 0, result, headers);

        if(res == 200) {
            string json = CharArrayToString(result);

            // Parse JSON: {"chart":{"result":[{"meta":{"regularMarketPrice":18.23}}]}}
            // Simple string search (for production, use JSON parser library)
            int pos = StringFind(json, "regularMarketPrice\":");
            if(pos >= 0) {
                string price_str = StringSubstr(json, pos + 20, 10);
                // Extract number
                double vix = StringToDouble(price_str);

                if(vix > 0 && vix < 200) {  // Sanity check
                    return vix;
                }
            }
        }

        CLogger::Error(StringFormat("Failed to fetch VIX from Yahoo (HTTP %d)", res));
        return 0.0;
    }

    //+------------------------------------------------------------------+
    //| Get 10yr Yield from Yahoo Finance                                |
    //+------------------------------------------------------------------+
    double GetYieldFromYahoo() {
        // ^TNX = CBOE 10-year Treasury Note Yield
        string url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?interval=1d&range=1d";

        char data[];
        char result[];
        string headers;

        int res = WebRequest("GET", url, NULL, NULL, 5000, data, 0, result, headers);

        if(res == 200) {
            string json = CharArrayToString(result);
            int pos = StringFind(json, "regularMarketPrice\":");

            if(pos >= 0) {
                string yield_str = StringSubstr(json, pos + 20, 10);
                double yield = StringToDouble(yield_str);

                if(yield > 0 && yield < 20) {  // Sanity check (0-20%)
                    return yield;
                }
            }
        }

        CLogger::Error(StringFormat("Failed to fetch 10yr Yield from Yahoo (HTTP %d)", res));
        return 0.0;
    }

    //+------------------------------------------------------------------+
    //| Get DXY from Yahoo Finance                                       |
    //+------------------------------------------------------------------+
    double GetDXYFromYahoo() {
        string url = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=1d";

        char data[];
        char result[];
        string headers;

        int res = WebRequest("GET", url, NULL, NULL, 5000, data, 0, result, headers);

        if(res == 200) {
            string json = CharArrayToString(result);
            int pos = StringFind(json, "regularMarketPrice\":");

            if(pos >= 0) {
                string dxy_str = StringSubstr(json, pos + 20, 10);
                double dxy = StringToDouble(dxy_str);

                if(dxy > 50 && dxy < 150) {  // Sanity check (50-150 range)
                    return dxy;
                }
            }
        }

        CLogger::Error(StringFormat("Failed to fetch DXY from Yahoo (HTTP %d)", res));
        return 0.0;
    }
};
```

---

## 3. Recommended Configuration by Broker Type

### Scenario A: Pure Forex Broker (No VIX/Yields)

**Example:** Oanda, FXCM, IC Markets

**Configuration:**
```cpp
// VIX: WebRequest or manual global variable
m_vix_source = SOURCE_WEB_API;  // or SOURCE_GLOBAL_VAR

// 10yr Yields: WebRequest or manual global variable
m_yield_source = SOURCE_WEB_API;  // or SOURCE_GLOBAL_VAR

// DXY: Calculate from pairs (ALWAYS AVAILABLE)
m_dxy_source = SOURCE_CALCULATED;
```

**Pros:**
- DXY calculation works perfectly (uses EURUSD, USDJPY, etc.)
- No broker dependency for DXY

**Cons:**
- Requires WebRequest setup or manual updates for VIX/Yields

---

### Scenario B: Multi-Asset Broker (Has VIX/Yields)

**Example:** IG, Saxo Bank, Interactive Brokers

**Configuration:**
```cpp
// All from broker (simplest)
m_vix_source = SOURCE_BROKER;      // Symbol: "VIX" or "VOLATILITY"
m_yield_source = SOURCE_BROKER;    // Symbol: "US10Y" or "USTEC10Y"
m_dxy_source = SOURCE_BROKER;      // Symbol: "USDX" or "DXY"
```

**Pros:**
- Real-time updates every tick
- No external dependencies
- Simple implementation

**Cons:**
- Broker-specific symbol names (need mapping)
- Spread costs if CFD symbols

---

### Scenario C: No WebRequest, Manual Updates

**Example:** Restricted VPS environment

**Configuration:**
```cpp
// User runs daily update script
GlobalVariableSet("VIX_CURRENT", 18.45);
GlobalVariableSet("YIELD_10YR", 4.23);
GlobalVariableSet("DXY_CURRENT", 103.67);

// EA reads from global variables
m_vix_source = SOURCE_GLOBAL_VAR;
m_yield_source = SOURCE_GLOBAL_VAR;
m_dxy_source = SOURCE_CALCULATED;  // Still calculate DXY (more accurate)
```

**Pros:**
- Works even without WebRequest
- User controls data source

**Cons:**
- Manual daily updates required
- Stale data risk if user forgets

---

## 4. Enabling WebRequest in MT5

**Steps:**

1. **Open MT5 Terminal**
2. **Tools → Options → Expert Advisors**
3. **Check:** "Allow WebRequest for listed URL:"
4. **Add URL:** `https://query1.finance.yahoo.com`
5. **Click OK**
6. **Restart Terminal**

**Testing WebRequest:**
```cpp
void OnStart() {
    char data[];
    char result[];
    string headers;

    string url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?interval=1d&range=1d";
    int res = WebRequest("GET", url, NULL, NULL, 5000, data, 0, result, headers);

    if(res == 200) {
        Print("WebRequest SUCCESS");
        Print(CharArrayToString(result));
    } else {
        Print("WebRequest FAILED: ", res);
        Print("Error: ", GetLastError());
    }
}
```

---

## 5. Recommended Implementation Strategy

### Phase 4 - Week 8: Macro Environment

**Step 1:** Implement `CMacroDataSource` with auto-detection

**Step 2:** On EA startup, detect available sources:
```cpp
int OnInit() {
    CMacroDataSource macro_source;
    macro_source.Initialize();  // Auto-detects best sources

    // Log detected sources
    Print("=== Macro Data Sources ===");
    Print("VIX: ", macro_source.GetVIXSource());
    Print("10yr Yield: ", macro_source.GetYieldSource());
    Print("DXY: ", macro_source.GetDXYSource());

    return INIT_SUCCEEDED;
}
```

**Step 3:** Update macro environment daily (or on demand):
```cpp
void OnTimer() {
    // Update macro data (e.g., every 1 hour)
    double vix = g_macro_source.GetVIX();
    double yield = g_macro_source.GetYield10yr();
    double dxy = g_macro_source.GetDXY();

    g_macro_env.Update(vix, yield, dxy);
}
```

---

## 6. Comparison Table

| Source | VIX | 10yr Yield | DXY | Pros | Cons |
|--------|-----|------------|-----|------|------|
| **Broker** | ⚠️ Rare | ⚠️ Some | ✅ Common | Real-time, simple | Broker-dependent |
| **Calculated** | ❌ N/A | ❌ N/A | ✅ **BEST** | Always available | DXY only |
| **WebRequest** | ✅ Good | ✅ Good | ✅ Good | Reliable, free | Requires setup |
| **Global Var** | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual | Works anywhere | User must update |

---

## 7. Recommended Final Setup

**For Most Users (Forex Brokers):**

```cpp
// Auto-detect and use best available source
CMacroDataSource macro_source;
macro_source.Initialize();

// This will automatically:
// - Use broker DXY if available, else calculate from pairs
// - Use WebRequest for VIX if enabled, else global variables
// - Use WebRequest for Yields if enabled, else global variables
```

**User Action Required:**
1. ✅ Enable WebRequest (5-minute one-time setup)
2. ✅ Check broker symbols (automatic detection on first run)
3. ✅ (Optional) Set global variables as fallback

**Result:** Fully automatic macro environment tracking! 🎯

---

## 8. Next Steps

**Phase 1 (Foundation):**
- Implement basic `CMacroDataSource` structure

**Phase 4 - Week 8 (Macro Environment):**
- Full implementation with auto-detection
- WebRequest integration
- Testing with different broker configurations

**User Testing:**
- Run detection script
- Verify sources detected correctly
- Report which broker type you have (forex-only or multi-asset)

---

**This gives you maximum flexibility regardless of broker! The system will intelligently use the best available source.** 🚀
