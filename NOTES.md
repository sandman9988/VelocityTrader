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

## Code Standards
Reference: `/Tools/` directory (from ProjectQuantum)
- Follow MQL5 financial programming best practices
- Consistent naming conventions
- Proper error handling
- Performance-optimized loops

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

## File Structure (Target)

```
VelocityTrader/
├── VelocityTrader_v7_1_Duel.mq5    # Main EA (slim)
├── Include/
│   ├── VT_Definitions.mqh
│   ├── VT_RLParameters.mqh
│   ├── VT_Structures.mqh
│   ├── VT_Predictor.mqh
│   ├── VT_CircuitBreaker.mqh
│   ├── VT_Globals.mqh
│   ├── VT_HUD.mqh                  # Enhanced HUD
│   ├── VT_Persistence.mqh          # Save/Load
│   └── VT_Physics.mqh              # Physics engine (TODO)
├── Tools/                          # MQL5 standards library
└── marketing/
```

---

*Last Updated: 2024-12-24*
