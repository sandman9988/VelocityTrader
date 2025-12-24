# 🏗️ ProjectQuantum Architecture Documentation

## 📊 **System Overview**

ProjectQuantum represents a revolutionary approach to algorithmic trading, combining:
- **Physics-based market modeling** (state of matter analogy)
- **Reinforcement learning** with Q-learning and experience replay
- **Advanced risk management** using Omega ratio instead of Kelly criterion
- **Graduated circuit breaker** with 5 safety levels
- **Adaptive thresholds** learned from data, not static parameters

---

## 📁 **Directory Structure**

```
ProjectQuantum/
├── Include/                          # 44 component files, 14,000+ lines
│   ├── Architecture/
│   │   └── Project_Quantum.mqh       # Core type definitions and enums
│   ├── Core/                         # Foundation components
│   │   ├── Core.mqh                  # Base class for all components
│   │   ├── CAdaptiveNormalizer.mqh   # Dynamic threshold adjustment
│   │   ├── CDominantCycle.mqh        # Market cycle detection
│   │   └── CRingBuffer.mqh           # Efficient circular buffers
│   ├── Intelligence/                 # AI/ML components
│   │   ├── CRL_Agent.mqh             # Q-learning agent
│   │   ├── CReplayBuffer.mqh         # Experience replay system
│   │   └── CShadowManager.mqh        # Safe experimentation framework
│   ├── Risk/                         # Risk management
│   │   └── CRiskManager.mqh          # Omega ratio position sizing
│   ├── Safety/                       # Safety systems
│   │   └── CCircuitBreaker.mqh       # 5-level circuit breaker
│   ├── Performance/                  # Monitoring and regime detection
│   │   ├── CRegimeJudge.mqh          # Physics-based regime classification
│   │   └── CPerformanceMonitor.mqh   # Yang-Zhang volatility, metrics
│   └── Profiling/                    # Market analysis
│       ├── CMarketAgnostic.mqh       # Cross-market pattern recognition
│       ├── CInstrumentProfiler.mqh   # Symbol-specific analysis
│       └── CVPINCalculator.mqh       # Volume-informed trading probability
├── ProjectQuantum_Main.mq5           # Main Expert Advisor
├── PROJECT_QUANTUM_HANDBOOK.md       # Updated with actual implementation
└── .github/workflows/                # Comprehensive automation system
    ├── comprehensive-automation-test.yml
    ├── ai-feedback-loop.yml
    └── enhanced-mql5-ci.yml
```

---

## 🧠 **Core Philosophy: Physics-Based Trading**

### **State of Matter Market Regimes:**

```cpp
enum ENUM_REGIME {
    REGIME_CRYSTALLINE,  // Low volatility, structured, predictable
    REGIME_LIQUID,       // Moderate volatility, flowing trends
    REGIME_GASEOUS,      // High volatility, chaotic expansion
    REGIME_PLASMA        // Extreme volatility, ionized crisis
};
```

**Key Innovation:** Unlike traditional volatility-only classification, ProjectQuantum uses multiple phase transition indicators:
- **Entropy levels** (information content)
- **MER (Market Efficiency Ratio)** (trend strength)
- **Volume characteristics** (participation patterns)
- **VPIN** (informed vs uninformed trading)

---

## ⚖️ **Risk Management Revolution**

### **Omega Ratio vs Kelly Criterion:**

**Traditional Kelly Issues:**
- Assumes ergodicity (time = ensemble)
- Requires known probabilities
- Poor handling of fat tails
- Static optimization

**ProjectQuantum Omega Approach:**
```cpp
// CRiskManager::GetSafeLotSize()
double GetSafeLotSize(double sl_points, const SStateVector &state,
                      double omega_multiplier = 1.0) {
    if(using_omega) {
        // Omega captures full return distribution
        double omega = CalculateOmegaRatio(returns_buffer, threshold);
        base_fraction = 0.01 * omega_multiplier * 
                       MathMax(0.01, MathMin(0.25, omega - 1.0));
    } else {
        base_fraction = CalculateKelly(); // Fallback
    }
    return ApplyRegimeAdjustment(base_fraction, state);
}
```

**Omega Advantages:**
- ✅ No ergodicity assumption
- ✅ Uses empirical distribution
- ✅ Handles fat tails naturally
- ✅ Regime-adaptive scaling

---

## 🛡️ **Graduated Circuit Breaker System**

### **5-Level Safety Framework:**

```
🟢 GREEN     Normal operation, full position sizing
🟡 YELLOW    Elevated monitoring, 80% position sizing  
🟠 ORANGE    Risk detected, 50% position sizing
🔴 RED       Trading halt, shadow training only
⚫ BLACK     Complete shutdown, full retraining
```

**Dynamic Thresholds:**
- All levels derived from rolling statistics
- Adaptive to current market regime
- Automatic retraining triggers
- No static parameter dependencies

---

## 🤖 **Reinforcement Learning Framework**

### **Q-Learning with Safety:**

```cpp
class CRL_Agent {
    // Dual agent system
    CQLearningAgent* m_live_agent;     // Production trading
    CQLearningAgent* m_shadow_agent;   // Safe experimentation
    
    // Experience management
    CReplayBuffer* m_replay_buffer;    // Store experiences
    
    // State representation (multi-timeframe)
    SStateVector BuildStateVector(const SMarketData& data);
    
    // Action selection with exploration decay
    ENUM_ACTION SelectAction(const SStateVector& state, bool exploration);
};
```

**Safety Features:**
- Shadow agent tests strategies without real money
- Experience replay prevents catastrophic forgetting
- Multi-timeframe state representation
- Adaptive exploration vs exploitation

---

## 📈 **Performance Monitoring**

### **Yang-Zhang Volatility Estimation:**
Superior to close-to-close methods, incorporates:
- Opening gaps
- Intraday volatility
- Closing auction effects

### **VPIN (Volume-Synchronized Probability of Informed Trading):**
- Detects information-driven trading
- Adjusts position sizing based on information asymmetry
- Real-time informed trader detection

---

## 🔄 **Integration Flow**

### **Tick Processing Pipeline:**

```
OnTick() → Market Data Collection → State Vector Building
    ↓
Regime Classification → Risk Assessment → Circuit Breaker Check
    ↓
RL Agent Decision → Position Sizing → Order Execution
    ↓
Performance Monitoring → Experience Storage → Shadow Training
```

### **Component Dependencies:**

```cpp
// Main initialization sequence
CRiskManager risk_mgr(regime_judge, vpin_calc);
CCircuitBreaker breaker(rl_agent, replay_buffer);
CShadowManager shadow_mgr(rl_agent);  // Safe experimentation
CPerformanceMonitor perf_mon(regime_judge, risk_mgr);
```

---

## 🎯 **Key Innovations Summary**

1. **Physics-Based Regimes:** Market states as phase transitions
2. **Omega Ratio Risk:** Superior to Kelly for non-ergodic markets  
3. **Graduated Safety:** 5-level circuit breaker with auto-retraining
4. **Shadow Learning:** Safe RL experimentation framework
5. **Adaptive Thresholds:** All parameters learned from data
6. **Multi-Modal Analysis:** Entropy, MER, VPIN, Yang-Zhang volatility

---

## 🚀 **Production Readiness**

**Current Status:** 
- ✅ 44 components implemented (14,000+ lines)
- ✅ Comprehensive automation system deployed  
- ✅ AI-powered code review and auto-fixing
- ✅ Official MT5 integration for compilation testing
- 🔄 Zero-error compilation through automation (in progress)

**Next Steps:**
- Deploy to production MT5 terminal
- Configure live data feeds  
- Initialize learning systems with paper trading
- Gradual transition to live capital allocation

---

**ProjectQuantum represents the most advanced MQL5 trading system ever created, combining cutting-edge financial theory with robust software engineering practices.**