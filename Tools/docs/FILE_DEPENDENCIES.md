# ProjectQuantum System - File Dependency Map & Cross-References

## Core Foundation Files (No Dependencies)

### 1. CLogger.mqh
**Status:** ✅ ENHANCED v2.1
**Dependencies:** None
**Used By:** ALL files
**Enhancements:**
- Log level filtering (DEBUG/INFO/WARN/ERROR/CRITICAL)
- Performance tracking
- Specialized logging methods
- Runtime configuration

---

### 2. ProjectQuantum_Architecture.mqh  
**Status:** ✅ Original (well-commented)
**Dependencies:** None
**Used By:** ALL component files
**Contains:**
- Enumerations (ENUM_REGIME, ENUM_TRADING_ACTION, ENUM_SYSTEM_STATE, etc.)
- Data structures (SStateVector, SProbabilityPrediction, SProjectQuantumTrade, etc.)
- No code logic, only definitions

---

### 3. Core.mqh
**Status:** ✅ Original (excellent implementation)
**Dependencies:** 
- CLogger.mqh
- ProjectQuantum_Architecture.mqh
**Used By:** ALL component classes
**Contains:**
- CHashTable<T> - O(1) Q-table lookups
- CRingBuffer<T> - O(1) replay buffer
- CObjectPool<T> - Memory management
- Statistical utilities (Welford's algorithm)
**Notes:** Hash table and ring buffer implementations are production-ready

---

## Utility & Helper Files

### 4. CAdaptiveCycle.mqh
**Dependencies:** Core.mqh
**Used By:** CMarketAgnostic.mqh
**Purpose:** Hilbert Transform for adaptive lookback periods

### 5. CAgnosticClock.mqh
**Dependencies:** Core.mqh
**Used By:** ProjectQuantum_Main.mq5
**Purpose:** Time-agnostic market hours detection

### 6. CSymbolNormalizer.mqh
**Dependencies:** Core.mqh
**Used By:** Multiple risk/trading components
**Purpose:** Broker-agnostic symbol formatting

### 7. CSystemOptimizer.mqh
**Dependencies:** CLogger.mqh
**Used By:** ProjectQuantum_Main.mq5
**Purpose:** Performance monitoring and system optimization

---

## Market Analysis Components

### 8. CMarketAgnostic.mqh
**Dependencies:** 
- Core.mqh
- CAdaptiveCycle.mqh
**Used By:** ProjectQuantum_Main.mq5
**Purpose:** Physics-based market sensors (NO static periods)
**Key Methods:**
- GetStateVector() - Returns SStateVector
- Calculates z-scores, MER, entropy, VPIN, etc.

### 9. CInstrumentProfiler.mqh
**Dependencies:** Core.mqh
**Used By:** ProjectQuantum_Main.mq5
**Purpose:** Instrument class detection (Forex/Metal/Index/Crypto/etc.)
**Key Methods:**
- GetInstrumentClass() → ENUM_INSTRUMENT_CLASS
- GetAdaptiveLookback() - Dynamic periods
- Provide Yang-Zhang realized volatility context (adaptive lookbacks, daily volatility) for stop sizing

### 10. CRegimeJudge.mqh
**Dependencies:** 
- Core.mqh
- ProjectQuantum_Architecture.mqh
**Used By:** ProjectQuantum_Main.mq5
**Purpose:** Classify market regime (Crystalline/Liquid/Gaseous/Plasma)
**Key Methods:**
- ClassifyRegime(SStateVector) → ENUM_REGIME
- GetConfidence() → regime probability

### 11. CMarketPhysics.mqh
**Dependencies:** Core.mqh
**Used By:** Various analysis components
**Purpose:** Physics-based market calculations

### 12. CPhysicsMonitor.mqh
**Dependencies:** Core.mqh
**Used By:** Monitoring components
**Purpose:** Track physics-based metrics

---

## AI/Learning Components

### 13. CRL_Agent.mqh
**Status:** ✅ Uses CHashTable for O(1) Q-lookups
**Dependencies:**
- Core.mqh (CHashTable)
- ProjectQuantum_Architecture.mqh
**Used By:** 
- ProjectQuantum_Main.mq5 (g_agent)
- CShadowManager.mqh (shadow agents)
- CCircuitBreaker.mqh (healing)
**Purpose:** Q-learning agent with eligibility traces
**Key Methods:**
- ChooseAction(regime, state) → ACTION
- UpdateQ(state, action, reward, next_state)
- SaveBrain() / LoadBrain()
- Heal(regime, factor) - Reduce Q-values for failing regime
**Critical:** Uses hash table (O(1)) instead of linear search (O(n))

### 14. CReplayBuffer.mqh
**Status:** ✅ Uses CRingBuffer for O(1) operations
**Dependencies:**
- Core.mqh (CRingBuffer)
- ProjectQuantum_Architecture.mqh (SProjectQuantumTrade)
**Used By:**
- ProjectQuantum_Main.mq5
- CCircuitBreaker.mqh (retraining)
**Purpose:** Experience storage with ring buffer
**Key Methods:**
- AddTrade(SProjectQuantumTrade)
- GetRecentTrades() - For experience replay
- CalculateSortinoRatio(n)
- GetCurrentDrawdown()
**Notes:** O(1) push operations, no array shifting

### 15. CProbabilityPredictor.mqh
**Dependencies:**
- Core.mqh
- ProjectQuantum_Architecture.mqh
**Used By:** ProjectQuantum_Main.mq5
**Purpose:** 7-layer physics-based prediction
**Layers:**
1. Bayesian Prior (P(direction|regime))
2. Adaptive fractal energy response (market roughness/persistence)
3. MER Signal (trend strength)
4. Entropy Scaling (predictability)
5. VPIN Toxicity (informed trader detection)
6. Kurtosis Risk (fat tail adjustment)
7. Z-Score Extremity (mean reversion)
**Key Methods:**
- Predict(state) → SProbabilityPrediction
- BayesianUpdate(regime, direction)

### 16. CCompositeValidator.mqh
**Dependencies:** Core.mqh
**Used By:** Trading decision components
**Purpose:** Multi-layer validation

### 17. CGenetics.mqh
**Dependencies:** Core.mqh
**Used By:** Optimization components
**Purpose:** Genetic algorithm for parameter optimization

---

## Risk Management Components

### 18. CCircuitBreaker.mqh
**Status:** ⚠️ NEEDS Enhancement #3 (Release Code Security)
**Dependencies:**
- Core.mqh
- CRL_Agent.mqh (for healing)
- CReplayBuffer.mqh (for retraining)
**Used By:** ProjectQuantum_Main.mq5
**Purpose:** Graduated circuit breaker with auto-retraining
**Levels:** GREEN → YELLOW → ORANGE → RED → BLACK
**Key Methods:**
- Update(drawdown, losses, sortino, state)
- GetLevel() → ENUM_CIRCUIT_LEVEL
- InitiateRetraining()
- PerformRetrainingStep()
- AttemptManualRelease(code) - NEEDS ENHANCEMENT
**Enhancement Needed:** Stronger cryptographic release codes

### 19. CRiskManager.mqh
**Dependencies:**
- Core.mqh (CRingBuffer for statistics)
- ProjectQuantum_Architecture.mqh
**Used By:** ProjectQuantum_Main.mq5
**Purpose:** Dynamic Kelly position sizing with CVaR
**Key Methods:**
- CalculatePositionSize(state, prediction) → lot size
- UpdatePerformance(trade)
- ApplyKurtosisPenalty(size, kurtosis)
- GetCVaRScalar()

### 20. CPortfolioRisk.mqh
**Dependencies:** Core.mqh
**Used By:** Portfolio management
**Purpose:** Portfolio-level risk management

### 21. CPortfolioPhysics.mqh
**Dependencies:** Core.mqh
**Used By:** Portfolio components
**Purpose:** Portfolio physics calculations

### 22. CPositionRegistry.mqh
**Dependencies:** Core.mqh
**Used By:** Position tracking
**Purpose:** Multi-position registry

---

## Shadow Strategy System

### 23. CShadowManager.mqh
**Dependencies:**
- Core.mqh
- CRL_Agent.mqh (creates shadow agents)
- CProbabilityPredictor.mqh
**Used By:** ProjectQuantum_Main.mq5
**Purpose:** Virtual trading with 3 shadow strategies
**Key Methods:**
- Update(state, price, yz_stop, live_action, live_sortino)
- GetBestShadow() → shadow ID and metrics
- ShouldPromoteShadow(id) → bool
- OpenVirtualPosition() / CloseVirtualPosition()
**Notes:** Full virtual P&L tracking with MAE/MFE

---

## Monitoring & Persistence

### 24. CPerformanceMonitor.mqh
**Dependencies:**
- Core.mqh (CRingBuffer for metrics)
- ProjectQuantum_Architecture.mqh
**Used By:** ProjectQuantum_Main.mq5
**Purpose:** HUD display + session/cumulative metrics
**Key Methods:**
- StartSession() / EndSession()
- RecordTrade(SProjectQuantumTrade)
- DrawHUD()
- GetSessionSortino() / GetCumulativeSortino()
- UpdateHealth()

### 25. CPersistence.mqh
**Dependencies:** Core.mqh
**Used By:** Save/load components
**Purpose:** File I/O utilities

---

## Main Expert Advisor

### 26. ProjectQuantum_Main.mq5
**Status:** ✅ Persistence & reconciliation integrated
**Dependencies:** ALL above components
**Purpose:** Main EA orchestration
**Global Objects:**
- g_sensors (CMarketAgnostic)
- g_profiler (CInstrumentProfiler)
- g_judge (CRegimeJudge)
- g_agent (CRL_Agent)
- g_replay (CReplayBuffer)
- g_predictor (CProbabilityPredictor)
- g_circuit (CCircuitBreaker)
- g_shadows (CShadowManager)
- g_risk (CRiskManager)
- g_monitor (CPerformanceMonitor)
- g_clock (CAgnosticClock)
- g_optimizer (CSystemOptimizer)

**Key Functions:**
- OnInit()
- OnDeinit()
- OnTick()
- ProcessStateMachine()
- ProcessTradingState()
- ExecuteTrade()
- ManagePosition()
- ClosePosition()
- OnPositionClosed()

**Persistence Coverage:**
1. SavePositionState()
2. LoadPositionState()
3. ReconcileExistingPositions()
4. LoadPositionState() called in OnInit()
5. ReconcileExistingPositions() called in OnInit()
6. SavePositionState() invoked from OnTick() every 10 ticks when a position is open

---

## Data Flow Diagram

```
                    ┌────────────────────┐
                    │  ProjectQuantum_Main.mq5  │
                    │   (Orchestrator)   │
                    └─────────┬──────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
        ┌──────────┐   ┌──────────┐  ┌──────────┐
        │ Sensors  │   │ Learning │  │   Risk   │
        │ (Market  │   │ (Agent/  │  │ (Circuit │
        │  State)  │   │  Shadow) │  │  Breaker)│
        └────┬─────┘   └────┬─────┘  └────┬─────┘
             │              │              │
             ▼              ▼              ▼
        SStateVector → Q-Learning → Position Size
                            ↓
                      SProbability
                      Prediction
```

---

## Critical Cross-References

### State Vector Flow:
1. CMarketAgnostic.GetStateVector() → SStateVector
2. CRegimeJudge.ClassifyRegime(state) → ENUM_REGIME
3. CProbabilityPredictor.Predict(state) → SProbabilityPrediction
4. CRL_Agent.ChooseAction(regime, state) → ENUM_TRADING_ACTION
5. CRiskManager.CalculatePositionSize(state, prediction) → lot size

### Trade Lifecycle:
1. ExecuteTrade() → Opens position
2. UpdatePositionMetrics() → Tracks MAE/MFE
3. ClosePosition() → Exits position
4. OnPositionClosed() → Creates SProjectQuantumTrade
5. CReplayBuffer.AddTrade() → Stores experience
6. CRL_Agent.UpdateQ() → Learns from result
7. CPerformanceMonitor.RecordTrade() → Tracks metrics

### Circuit Breaker Flow:
1. CCircuitBreaker.Update() → Checks thresholds
2. If RED: InitiateRetraining()
3. CRL_Agent.Heal() → Reduces Q-values
4. CReplayBuffer.GetRecentTrades() → Experience replay
5. If BLACK: Requires manual release code

### Shadow Strategy Flow:
1. CShadowManager.Update() → Updates all shadows
2. Shadow agents make decisions independently
3. Virtual positions track MAE/MFE
4. Compare shadow Sortino vs live Sortino
5. If shadow better + threshold → Promote

---

## Files Requiring NO Changes (Already Excellent)

✅ Core.mqh - Hash table and ring buffer perfect
✅ ProjectQuantum_Architecture.mqh - Data structures well-defined
✅ CMarketAgnostic.mqh - Adaptive sensors excellent
✅ CInstrumentProfiler.mqh - Agnostic detection complete
✅ CRegimeJudge.mqh - Physics-based classification sound
✅ CRL_Agent.mqh - Q-learning with O(1) lookups perfect
✅ CReplayBuffer.mqh - Ring buffer implementation excellent
✅ CProbabilityPredictor.mqh - 7-layer system complete
✅ CRiskManager.mqh - Kelly + CVaR well-implemented
✅ CShadowManager.mqh - Shadow system comprehensive
✅ CPerformanceMonitor.mqh - Metrics tracking complete

---

## Files Requiring Enhancements

### HIGH PRIORITY:
❌ ProjectQuantum_Main.mq5
   - Add SavePositionState()
   - Add LoadPositionState()
   - Add ReconcileExistingPositions()

### MEDIUM PRIORITY:
❌ CCircuitBreaker.mqh
   - Enhance GenerateReleaseCode()
   - Add cryptographic security

### COMPLETED:
✅ CLogger.mqh - Enhanced with log levels

---

## Version Information

**Original Version:** 2.0
**Enhanced Version:** 2.1
**Enhancement Date:** December 19, 2024
**Total Files:** 26 (25 .mqh + 1 .mq5)
**Lines of Code:** ~6,000
**Compilation Target:** MQL5 Build 3960+

---

## Verification Checklist

- [ ] All #include paths verified
- [ ] No circular dependencies
- [ ] All global objects properly initialized
- [ ] All global objects properly cleaned up in OnDeinit()
- [ ] Memory leaks checked (all new have corresponding delete)
- [ ] File handles closed in all paths
- [ ] Error codes handled
- [ ] Backward compatibility maintained

---

**Document Status:** COMPLETE
**Mapped By:** Claude (Expert MQL5 Analyst)
**Last Updated:** December 19, 2024
