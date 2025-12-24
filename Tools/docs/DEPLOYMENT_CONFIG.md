# 🚀 ProjectQuantum Deployment Configuration

## 📋 **Pre-Deployment Checklist**

### **✅ System Requirements**
- [ ] MetaTrader 5 Terminal (build 3260+)
- [ ] Windows 10/11 or Windows Server 2016+
- [ ] Minimum 8GB RAM, 16GB recommended
- [ ] SSD storage for fast I/O operations
- [ ] Stable internet connection (low latency preferred)

### **✅ Broker Requirements**
- [ ] MT5-compatible broker with API access
- [ ] Support for Expert Advisors (automated trading enabled)
- [ ] Sufficient margin and balance for initial positions
- [ ] Hedging allowed (if using multiple strategies)

---

## ⚙️ **Installation Steps**

### **1. Prepare MT5 Environment**

```batch
# Copy ProjectQuantum files to MT5 directory
copy ProjectQuantum_Main.mq5 "C:\Program Files\MetaTrader 5\MQL5\Experts\"
xcopy Include "C:\Program Files\MetaTrader 5\MQL5\Include\ProjectQuantum\" /E /I

# OR for portable installation:
copy ProjectQuantum_Main.mq5 "C:\MT5_Portable\MQL5\Experts\"
xcopy Include "C:\MT5_Portable\MQL5\Include\ProjectQuantum\" /E /I
```

### **2. Compilation Verification**

```cpp
// In MetaEditor, compile with these settings:
#property strict
#property version   "1.0"
#property description "ProjectQuantum - Physics-Based Trading System"

// Verify all includes resolve correctly
#include "Include/Architecture/Project_Quantum.mqh"
#include "Include/Core/Core.mqh"
// ... (all 44 includes)
```

### **3. Input Parameters Configuration**

```cpp
// Critical parameters for production deployment
input string    InpSymbol = "EURUSD";           // Trading symbol
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_M15; // Base timeframe
input double    InpInitialRisk = 0.02;          // 2% initial risk
input bool      InpPaperTrading = true;         // Start in paper mode
input int       InpWarmupPeriod = 1000;         // Bars for initialization
input bool      InpEnableLogging = true;        // Detailed logging
input string    InpLogPrefix = "PQ_PROD_";      // Log file prefix
```

---

## 🛡️ **Safety Configuration**

### **Circuit Breaker Settings**

```cpp
// Conservative production settings
input double    InpMaxDrawdown = 0.15;          // 15% max drawdown
input int       InpMaxConsecutiveLosses = 5;    // Stop after 5 losses
input double    InpDailyLossLimit = 0.05;       // 5% daily loss limit
input bool      InpEmergencyStopEnabled = true; // Manual stop capability
input string    InpEmergencyStopFile = "EMERGENCY_STOP.txt"; // Stop trigger file
```

### **Risk Management Overrides**

```cpp
input double    InpMaxPositionSize = 0.1;       // 10% max position
input double    InpOmegaMultiplier = 0.5;       // Conservative multiplier  
input bool      InpForceQuarterKelly = false;   // Use Omega by default
input double    InpVolatilityScaling = 0.8;     // Reduce size in high vol
```

---

## 📊 **Monitoring Setup**

### **1. Performance Metrics Dashboard**

```cpp
// Key metrics to monitor
- Real-time P&L
- Drawdown levels (current/maximum)
- Regime classification accuracy
- Circuit breaker status
- RL agent performance metrics
- Position sizing effectiveness
```

### **2. Alert System Configuration**

```cpp
// Email alerts for critical events
input string    InpEmailSMTP = "smtp.gmail.com";
input string    InpEmailUser = "trader@domain.com";  
input string    InpEmailPassword = "********";       // Use app password
input string    InpAlertEmail = "alerts@domain.com";

// Alert triggers
enum ENUM_ALERT_LEVEL {
    ALERT_INFO,      // Regime changes, position opens/closes
    ALERT_WARNING,   // Circuit breaker level changes  
    ALERT_CRITICAL   // Emergency stops, system errors
};
```

---

## 🔄 **Production Deployment Phases**

### **Phase 1: Paper Trading (2-4 weeks)**

```cpp
// Configuration for paper trading phase
input bool      InpPaperTrading = true;
input double    InpInitialRisk = 0.01;           // Very conservative
input bool      InpShadowLearningOnly = true;    // No live agent updates
input int       InpMinWarmupBars = 2000;         // Extended warmup
```

**Objectives:**
- Verify all components work in production environment
- Validate data feeds and connectivity
- Confirm regime classification accuracy
- Test circuit breaker functionality
- Establish performance baselines

### **Phase 2: Micro-Capital Live (2-4 weeks)**

```cpp
input bool      InpPaperTrading = false;
input double    InpInitialRisk = 0.005;          // 0.5% risk per trade
input double    InpMaxPositionSize = 0.01;       // 1% max position
input bool      InpConservativeMode = true;      // Extra safety checks
```

**Objectives:**
- Test with real money but minimal risk
- Validate order execution and slippage handling
- Confirm broker compatibility
- Monitor system stability under live conditions

### **Phase 3: Scaled Production (Ongoing)**

```cpp
input double    InpInitialRisk = 0.02;           // Scale to target risk
input double    InpMaxPositionSize = 0.1;        // Scale position limits
input bool      InpConservativeMode = false;     // Normal operation
input bool      InpAutoScaling = true;           // Enable auto-scaling
```

---

## 📁 **File Structure for Production**

```
Production_Deploy/
├── Experts/
│   └── ProjectQuantum_Main.mq5
├── Include/
│   └── ProjectQuantum/              # All 44 .mqh files
│       ├── Architecture/
│       ├── Core/
│       ├── Intelligence/
│       ├── Risk/
│       ├── Safety/
│       ├── Performance/
│       └── Profiling/
├── Files/                           # Data storage
│   ├── ProjectQuantum_Logs/
│   ├── ProjectQuantum_Data/
│   └── ProjectQuantum_Models/
└── Config/
    ├── production_settings.set     # Saved input parameters
    ├── broker_config.json         # Broker-specific settings
    └── deployment_checklist.txt   # Pre-flight verification
```

---

## 🔍 **Post-Deployment Verification**

### **Daily Checks:**
- [ ] System running without errors
- [ ] All components initializing correctly
- [ ] Regime classification functioning
- [ ] Risk management operating within limits
- [ ] Circuit breaker responding appropriately
- [ ] Performance metrics within expected ranges

### **Weekly Reviews:**
- [ ] Overall performance vs benchmarks
- [ ] Regime classification accuracy analysis
- [ ] Risk-adjusted returns evaluation
- [ ] Circuit breaker effectiveness review
- [ ] RL agent learning progress assessment
- [ ] System resource utilization check

### **Monthly Optimization:**
- [ ] Parameter tuning based on performance data
- [ ] Model retraining if required
- [ ] Risk limit adjustments
- [ ] Strategy enhancement evaluation
- [ ] System capacity planning

---

## ⚠️ **Emergency Procedures**

### **Immediate Stop Protocol:**

```cpp
// Manual emergency stop
bool CreateEmergencyStop() {
    return FileCreate("EMERGENCY_STOP.txt", "MANUAL_STOP");
}

// System monitors this file every tick
bool CheckEmergencyStop() {
    return FileIsExist("EMERGENCY_STOP.txt");
}
```

### **Recovery Procedures:**

1. **System Restart:**
   - Close all positions safely
   - Save current state and model weights
   - Document incident details
   - Restart with conservative settings

2. **Model Reset:**
   - Revert to last stable model version
   - Reinitialize with extended warmup period
   - Monitor performance closely
   - Gradual return to normal operation

---

## 📈 **Success Metrics**

**Target Performance:**
- Sharpe Ratio: > 2.0
- Maximum Drawdown: < 15%
- Win Rate: > 55%
- Profit Factor: > 1.5
- Omega Ratio: > 1.3

**System Health:**
- Uptime: > 99.5%
- Circuit Breaker Activations: < 5% of trading time
- Regime Classification Accuracy: > 80%
- Risk Limit Violations: 0

---

**This deployment configuration ensures ProjectQuantum transitions safely from development to production, with comprehensive monitoring and safety measures at every step.**