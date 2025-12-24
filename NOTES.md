# VelocityTrader v7.1 - Development Notes

## Priority Enhancements (Self-Notes)

### 1. Divergent RL Learning Per Agent
- **Current**: Both SNIPER and BERSERKER share `g_rlParams`
- **Goal**: Each agent evolves its OWN parameter set independently
- **Why**: Maximize performance through specialization
  - SNIPER: May evolve toward tighter SL, longer holds, higher conviction
  - BERSERKER: May evolve toward wider SL, quick exits, volume plays
- **Implementation**:
  ```mql5
  struct TradingAgent {
      RLParameters rlParams;  // Per-agent RL parameters
      // ... existing fields
  };
  ```

### 2. Profit Journey Matters
- Track the PATH to profit, not just the outcome
- Metrics to add:
  - Time-weighted P&L curve smoothness
  - Drawdown recovery speed
  - Profit consistency score
  - Win streak quality (consecutive vs scattered)
- Reward shaping should penalize volatile journeys even if profitable

### 3. Normalized, Agnostic, Dynamic Self-Healing Code
- **Normalized**: All parameters in [0,1] range (already done with `n_xxx`)
- **Agnostic**: Symbol/timeframe independent logic
- **Dynamic**: Auto-adapt to market regime changes
- **Self-Healing**:
  - Auto-detect degraded performance
  - Trigger parameter mutation/reset
  - Circuit breaker already provides foundation
  - Add: Automatic parameter rollback if performance degrades

### 4. Enhanced HUD Performance Measurement
- **Current**: Basic stats display
- **Goal**: Dramatically enhanced asymmetrical shape rewards visualization
- **New HUD Elements**:
  - Profit journey sparkline (mini chart)
  - Per-agent divergence metrics
  - Real-time Omega curve
  - Asymmetric reward distribution histogram
  - Heat map of regime performance
  - Convergence progress bars per agent
  - Shadow vs Real performance delta
  - Rolling Sharpe ratio

### 5. Asymmetrical Reward Shaping
- Losses should hurt MORE than wins feel good
- Current: `reward = netPnL * GetLossPenalty()` for losses
- Enhance with:
  - Progressive penalty (bigger losses = exponentially worse)
  - Streak multipliers (consecutive losses compound)
  - Time-decay rewards (quick profits > slow profits)
  - Drawdown-weighted penalties

---

## Code Standards & Compliance

**IMPORTANT**: All future code changes MUST comply with the financial auditor and MQL5 linter standards.

### Tools to Run Before Commit
```bash
# Financial-grade audit (must pass with 0 CRITICAL findings)
python3 Tools/mql5_financial_auditor.py --project .

# MQL5 linting
python3 Tools/mql5_enhanced_linter.py --file MQL5/Experts/VelocityTrader_v7_1_Duel.mq5
```

---

## Current Audit Status (2025-12-24)

**Total Findings: 696** | CRITICAL: 293 | HIGH: 93 | MEDIUM: 262 | LOW: 48

### Violations by Category

| Category | Count | Priority |
|----------|-------|----------|
| Memory Safety | 246 | CRITICAL |
| Data Integrity | 196 | HIGH |
| Numerical Safety | 82 | CRITICAL |
| Regulatory Compliance | 62 | MEDIUM |
| Code Quality | 48 | LOW |
| Defensive Programming | 31 | HIGH |
| Execution Safety | 27 | CRITICAL |
| Risk Controls | 4 | CRITICAL |

### Critical Violations to Fix

#### [MEM001] Array Access Without Bounds Check (200+ instances)
**Files**: All files, especially `VelocityTrader_v7_1_Duel.mq5`
**Pattern**: `g_symbols[idx]`, `g_positions[idx]`, `g_ranking[idx]`
**Fix Required**:
```mql5
// WRONG
double val = g_symbols[idx].price;

// CORRECT
if(idx >= 0 && idx < ArraySize(g_symbols))
    double val = g_symbols[idx].price;
```

#### [NUM001] Unsafe Division Operation (25+ instances)
**Files**: `VT_HUD.mqh`, `VT_Predictor.mqh`, main EA
**Pattern**: Division without zero-check
**Fix Required**:
```mql5
// WRONG
double ratio = upside / downside;

// CORRECT - Use existing SafeDivide() helper
double ratio = SafeDivide(upside, downside, 1.0);
```

#### [EXEC002] Position Size Not Normalized (11 instances)
**Files**: `VelocityTrader_v7_1_Duel.mq5`
**Pattern**: Lot sizes not validated against SYMBOL_VOLUME_STEP
**Fix Required**:
```mql5
// WRONG
double lots = riskAmount / (slTicks * tickValue);

// CORRECT
double lots = riskAmount / (slTicks * tickValue);
lots = NormalizeDouble(lots, (int)MathLog10(1.0/spec.volumeStep));
lots = MathMax(lots, spec.volumeMin);
lots = MathMin(lots, spec.volumeMax);
```

#### [RISK002] Missing Drawdown Check (3 instances)
**Files**: `VelocityTrader_v7_1_Duel.mq5` - `OnTimer()`, `OnTick()`
**Fix Required**: Add drawdown validation before trade decisions

#### [DATA001] Magic Number Validation (multiple)
**Fix Required**: Validate magic numbers in order operations

#### [REG001] Audit Trail / Logging (multiple)
**Fix Required**: Add structured logging for regulatory compliance

### Files by Violation Count

| File | Total | Critical |
|------|-------|----------|
| VelocityTrader_v7_1_Duel.mq5 | 483 | 236 |
| VT_Persistence.mqh | 84 | 0 |
| VT_RLParameters.mqh | 34 | 0 |
| VT_Structures.mqh | 29 | 24 |
| VT_HUD.mqh | 22 | 19 |
| VT_CircuitBreaker.mqh | 18 | 2 |
| VT_Globals.mqh | 15 | 3 |
| VT_Predictor.mqh | 11 | 9 |

---

## Coding Standards Checklist (Apply to ALL New Code)

### Memory Safety
- [ ] Always validate array indices before access
- [ ] Use `ArraySize()` for bounds checking
- [ ] Initialize all arrays before use
- [ ] Check pointer validity before dereferencing

### Numerical Safety
- [ ] Use `SafeDivide()` for all division operations
- [ ] Validate inputs with `MathIsValidNumber()`
- [ ] Clamp values to valid ranges
- [ ] Handle edge cases (zero, negative, infinity, NaN)

### Execution Safety
- [ ] Normalize lot sizes with `NormalizeDouble()`
- [ ] Validate against `SYMBOL_VOLUME_MIN/MAX/STEP`
- [ ] Check order send results
- [ ] Implement retry logic for failed operations

### Risk Controls
- [ ] Check drawdown before every trade decision
- [ ] Validate circuit breaker state
- [ ] Enforce position limits
- [ ] Log all risk-related decisions

### Data Integrity
- [ ] Validate all external inputs
- [ ] Check file operations for success
- [ ] Implement checksums for persistence
- [ ] Sanitize string inputs

### Regulatory Compliance
- [ ] Log all trade decisions with timestamps
- [ ] Record parameter changes
- [ ] Maintain audit trail
- [ ] Document algorithm behavior

---

## Architecture Evolution

```
Current:
[Single RLParameters] -> [SNIPER] + [BERSERKER]

Target:
[SNIPER.rlParams] -> SNIPER Evolution
[BERSERKER.rlParams] -> BERSERKER Evolution
         |                    |
         v                    v
   [Competition] -> Capital Allocation
```

---

## File Structure (Current)

```
VelocityTrader/
├── MQL5/                           # Standard MT5 structure
│   ├── Experts/
│   │   └── VelocityTrader_v7_1_Duel.mq5
│   ├── Include/
│   │   ├── VT_Definitions.mqh
│   │   ├── VT_RLParameters.mqh
│   │   ├── VT_Structures.mqh
│   │   ├── VT_Predictor.mqh
│   │   ├── VT_CircuitBreaker.mqh
│   │   ├── VT_Globals.mqh
│   │   ├── VT_HUD.mqh              # HUD rendering
│   │   ├── VT_Persistence.mqh      # Save/Load
│   │   └── VT_Physics.mqh          # Physics engine (TODO)
│   ├── Indicators/
│   ├── Scripts/
│   └── Libraries/
├── Tools/                          # MQL5 standards library
├── marketing/
├── README.md
└── NOTES.md
```

---

*Last Updated: 2025-12-24*
