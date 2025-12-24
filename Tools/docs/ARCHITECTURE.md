# Project Quantum v3.0 - System Architecture

## Executive Summary

Project Quantum v3.0 implements a **Physics-Informed Reinforcement Learning** trading system built on a four-layer architecture. The system combines econophysics feature engineering with proven RL methods, adversarial risk prediction, and defensive programming standards.

**Core Philosophy:** *"Physics teaches the agent what the market looks like, RL learns what to do about it, Safety prevents disasters"*

---

## Architectural Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAYER 4: SAFETY                                   │
│         Circuit Breakers · DEFCON Levels · Emergency Protocols              │
├─────────────────────────────────────────────────────────────────────────────┤
│                        LAYER 3: RISK CONTROL                                │
│    Three-Level Hierarchy: Micro (Instrument) → Meso (Asset) → Macro (Port) │
├─────────────────────────────────────────────────────────────────────────────┤
│                        LAYER 2: INTELLIGENCE                                │
│  Entry Agent · Exit Agent · Risk Adversary · Journey Reward · Experience    │
├─────────────────────────────────────────────────────────────────────────────┤
│                         LAYER 1: SENSING                                    │
│   Physics Metrics · Fractal Analysis · Portfolio Physics · Market Context  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Sensing (Physics Feature Engineering)

### Purpose
Extract market microstructure features using econophysics methods that are robust across instruments and timeframes.

### Components

| Component | File | Purpose |
|-----------|------|---------|
| CMarketAgnostic | `Include/Sensing/CMarketAgnostic.mqh` | Core physics metrics (Hurst, Entropy, Yang-Zhang Vol) |
| CFractalAnalyzer | `Include/Physics/CFractalAnalyzer.mqh` | Katz Fractal Dimension, Sample Entropy, FTLE |
| CPortfolioPhysics | `Include/Physics/CPortfolioPhysics.mqh` | Correlation Energy, System Entropy, VPIN |

### Key Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHYSICS METRICS                                      │
├──────────────────────┬──────────────────────────────────────────────────────┤
│ VPIN                 │ Volume-synchronized Probability of Informed Trading  │
│                      │ Detects toxic order flow before adverse moves         │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ Kurtosis             │ Fourth moment - fat tail risk indicator              │
│                      │ >4 signals elevated tail event probability            │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ Hurst Exponent       │ Long-term memory coefficient [0,1]                   │
│                      │ >0.5 trending, <0.5 mean-reverting, =0.5 random      │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ Katz Fractal Dim     │ Short-term path roughness (30-80 bars)               │
│                      │ >1.5 suggests trend continuation                      │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ Sample Entropy       │ Pattern predictability [0,2+]                        │
│                      │ Lower = more predictable patterns                     │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ FTLE                 │ Finite Time Lyapunov Exponent                        │
│                      │ Chaos/bifurcation proximity indicator                 │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ Correlation Energy   │ Portfolio binding force [0,1]                        │
│                      │ Pre-crash crystallization indicator                   │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ System Entropy       │ Portfolio disorder [0,1]                             │
│                      │ Extremes (<0.3 or >0.9) signal instability           │
└──────────────────────┴──────────────────────────────────────────────────────┘
```

### Data Flow

```
Raw Price/Volume Data
        │
        ▼
┌───────────────────┐
│  CMarketAgnostic  │ ──► SStateVector (40+ features)
│   CFractalAnalyzer│         │
│   CPortfolioPhysics        │
└───────────────────┘         │
                              ▼
                    Normalized [0,1] Features
                              │
                              ▼
                    Layer 2: Intelligence
```

---

## Layer 2: Intelligence (Adaptive RL)

### Purpose
Learn optimal trading decisions through experience while predicting and avoiding catastrophic losses.

### Components

| Component | File | Purpose |
|-----------|------|---------|
| CRL_Agent | `Include/Intelligence/CRL_Agent.mqh` | Entry Q-learning with eligibility traces |
| CRLExitAgent | `Include/Intelligence/CRLExitAgent.mqh` | Exit management with MFE/MAE state bins |
| CRiskAdversary | `Include/Intelligence/CRiskAdversary.mqh` | Crash prediction adversarial agent |
| CJourneyReward | `Include/Intelligence/CJourneyReward.mqh` | Multi-component reward shaping |
| CReplayBuffer | `Include/Intelligence/CReplayBuffer.mqh` | Prioritized experience replay |

### Entry Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENTRY AGENT (CRL_Agent)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  State Space: ~10-15k states (discretized physics features)                 │
│                                                                              │
│  Actions: {BUY, SELL, HOLD, CLOSE}                                          │
│                                                                              │
│  Learning: TD(λ) with eligibility traces                                    │
│            Q(s,a) ← Q(s,a) + α[r + γ·max(Q(s',a')) - Q(s,a)]·e(s,a)        │
│                                                                              │
│  Exploration: ε-greedy with adaptive decay                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Exit Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXIT AGENT (CRLExitAgent)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  State Space: MFE bins (5) × MAE bins (5) × Drawdown bins (5) × Bars (4)   │
│              = ~500 states                                                   │
│                                                                              │
│  Actions: {HOLD, EXIT_PARTIAL, EXIT_FULL, TRAIL_TIGHT, TRAIL_WIDE}         │
│                                                                              │
│  Journey Reward Components:                                                  │
│    ├── MFE Capture Reward (% of peak realized)                              │
│    ├── MAE Penalty (maximum adverse excursion)                              │
│    ├── Sortino Component (downside risk adjustment)                         │
│    ├── Path Efficiency (equity curve smoothness)                            │
│    ├── Profit Reward (absolute return)                                      │
│    └── Giveback Penalty (MFE → Close drawdown)                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Risk Adversary Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RISK ADVERSARY (CRiskAdversary)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Mission: Predict crashes/drawdowns BEFORE they happen                      │
│                                                                              │
│  Reward Function:                                                            │
│    +1.0 for correct crash prediction (predicted → occurred)                 │
│    -1.0 for false alarm (predicted → no crash)                              │
│                                                                              │
│  Output: Danger Score [0.0, 1.0] → Position Sizing Modulation               │
│                                                                              │
│  Metrics: F1 Score, Brier Score (calibration), Precision/Recall             │
│                                                                              │
│  Integration: size *= (1.0 - danger_score * modulation_factor)              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Experience Replay

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PRIORITIZED EXPERIENCE REPLAY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Capacity: 10,000 SARS tuples                                               │
│                                                                              │
│  Priority Calculation:                                                       │
│    priority = |R-multiple| + regime_rarity_bonus                            │
│                                                                              │
│  Sampling: CDF-based (not uniform)                                          │
│    - Build cumulative distribution from priorities                          │
│    - Binary search for random samples                                       │
│    - Importance sampling weights for unbiased updates                       │
│                                                                              │
│  Benefits:                                                                   │
│    - High-impact experiences sampled more frequently                        │
│    - Rare regimes get adequate representation                               │
│    - Temporal decorrelation reduces overfitting                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 3: Risk Control (Three-Level Hierarchy)

### Purpose
Validate trades at multiple scales before execution, from instrument-level to portfolio-wide.

### Components

| Component | File | Purpose |
|-----------|------|---------|
| CThreeLevelRisk | `Include/Risk/CThreeLevelRisk.mqh` | Validation pipeline coordinator |
| CAssetClassRisk | `Include/Risk/CAssetClassRisk.mqh` | Correlation clustering & exposure |
| CPositionSizer | `Include/Risk/CPositionSizer.mqh` | Unified position sizing logic |

### Validation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VALIDATION PIPELINE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

   RL Agent Decision
          │
          ▼
  ┌───────────────────┐
  │   MICRO LEVEL     │  Instrument-level validation
  │   (Instrument)    │  - Spread percentile check
  │                   │  - Volatility regime check
  │                   │  - Liquidity score threshold
  └─────────┬─────────┘
            │ Pass?
            ▼
  ┌───────────────────┐
  │   MESO LEVEL      │  Asset class validation
  │   (Asset Class)   │  - Correlation with existing positions
  │                   │  - Sector concentration limits
  │                   │  - Asset class exposure caps
  └─────────┬─────────┘
            │ Pass?
            ▼
  ┌───────────────────┐
  │   MACRO LEVEL     │  Portfolio-wide validation
  │   (Portfolio)     │  - System entropy bounds [0.3, 0.9]
  │                   │  - Correlation energy < 0.8
  │                   │  - Total portfolio risk budget
  └─────────┬─────────┘
            │ Pass?
            ▼
     ┌──────┴──────┐
     │   Execute   │
     │  or Reject  │
     │  (with reason)
     └─────────────┘
```

### Position Sizing Flow

```
Base Risk Amount
      │
      ├── Volatility Adjustment (Yang-Zhang, not ATR)
      │
      ├── Danger Score Modulation (from Risk Adversary)
      │         size *= (1.0 - danger_score * 0.9)
      │
      ├── Regime Adjustment (PLASMA = 0.5x)
      │
      ├── Correlation Adjustment (high correlation = reduce)
      │
      ├── Circuit Breaker Multiplier (YELLOW = 0.5x, etc.)
      │
      └── Broker Normalization (min/max/step)
                │
                ▼
         Final Lot Size
```

---

## Layer 4: Safety (Circuit Breakers)

### Purpose
Prevent catastrophic losses through graduated intervention levels.

### Components

| Component | File | Purpose |
|-----------|------|---------|
| CCircuitBreaker | `Include/Safety/CCircuitBreaker.mqh` | DEFCON level management |
| CRiskIntelligence | `Include/Performance/CRiskIntelligence.mqh` | Physics-informed risk monitoring |
| CLearningMetrics | `Include/Performance/CLearningMetrics.mqh` | Learning quality & self-healing |

### DEFCON Levels

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DEFCON LEVELS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  GREEN   ████████████████████████  Normal operation                         │
│          Full position sizing, all strategies active                        │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  YELLOW  ████████████░░░░░░░░░░░░  Warning - Elevated risk                  │
│          Position sizing × 0.5, increased monitoring                        │
│          Triggers: Danger score >0.5, correlation >0.6                      │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ORANGE  ████████░░░░░░░░░░░░░░░░  Partial freeze                           │
│          No new positions, manage existing only                             │
│          Triggers: Entropy extremes, kurtosis >6, VPIN >0.7                 │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RED     ████░░░░░░░░░░░░░░░░░░░░  Full freeze                              │
│          Close all positions, stop trading                                  │
│          Triggers: Correlation >0.85, drawdown >20%, danger >0.9            │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BLACK   ░░░░░░░░░░░░░░░░░░░░░░░░  System lockdown                          │
│          Requires release code to restart                                   │
│          Triggers: Catastrophic event, manual override                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Self-Healing System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SELF-HEALING TRIGGERS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Trigger                    │ Condition                │ Action             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  needs_genetic_refresh      │ Action diversity <30%    │ Inject random Qs   │
│  needs_q_table_reset        │ Q stability <20%         │ Reset Q-table      │
│  needs_exploration_boost    │ ε<0.05 & coverage<30%    │ Set ε=0.3          │
│  needs_reward_rebalancing   │ Signal clarity <0.1      │ Adjust weights     │
│  needs_physics_recalibration│ Prediction accuracy <50% │ Reset trust weights│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Architecture

### Complete System Flow

```
                           ┌─────────────────┐
                           │   MARKET DATA   │
                           │  (Price/Volume) │
                           └────────┬────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        LAYER 1: SENSING                                    │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                      │
│  │  Market     │   │  Fractal    │   │ Portfolio   │                      │
│  │  Agnostic   │   │  Analyzer   │   │  Physics    │                      │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                      │
│         └─────────────────┼─────────────────┘                              │
│                           ▼                                                 │
│                   SStateVector [40+ features, normalized 0-1]              │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                      LAYER 2: INTELLIGENCE                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │
│  │ Entry Agent │   │ Exit Agent  │   │    Risk     │   │  Replay     │   │
│  │ (Q-learning)│   │ (Journey RL)│   │  Adversary  │   │  Buffer     │   │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   │
│         │                 │                  │                 │          │
│         ▼                 ▼                  ▼                 │          │
│     Action           Exit Signal       Danger Score            │          │
│    Proposal          Proposal           [0,1]                  │          │
│         └─────────────────┼──────────────────┘                 │          │
│                           │                                     │          │
│                           ▼                                     │          │
│                   Trade Decision ◄──────────────────────────────┘          │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                      LAYER 3: RISK CONTROL                                 │
│                                                                            │
│       Micro Check → Meso Check → Macro Check → Position Sizing            │
│                                                                            │
│       [spread]      [correlation]  [entropy]    [danger × vol × regime]   │
│       [volatility]  [exposure]     [cor.energy]                            │
│       [liquidity]   [sector]       [bifurcation]                           │
│                                                                            │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        LAYER 4: SAFETY                                     │
│                                                                            │
│    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│    │   Circuit    │     │    Risk      │     │   Learning   │            │
│    │   Breaker    │     │ Intelligence │     │   Metrics    │            │
│    └───────┬──────┘     └───────┬──────┘     └───────┬──────┘            │
│            │                    │                    │                    │
│            ▼                    ▼                    ▼                    │
│        DEFCON Level         Alerts              Self-Healing              │
│                                                                            │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    EXECUTE    │
                    │   or REJECT   │
                    └───────────────┘
```

---

## State Vector Composition

### SStateVector Fields (40+ features)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STATE VECTOR FIELDS                                  │
├──────────────────────────┬──────────────────────────────────────────────────┤
│ CATEGORY                 │ FIELDS                                           │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Regime                   │ current_regime, regime_confidence                │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Momentum                 │ z_score_momentum, trend_signal [-1,1]            │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Volatility               │ volatility_z, yang_zhang_vol, volatility_regime  │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Entropy                  │ entropy_score, sample_entropy                    │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Fractal                  │ katz_fractal_dimension, ftle                     │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Risk Metrics             │ vpin, kurtosis, mer_score                        │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Portfolio Physics        │ correlation_energy, system_entropy,              │
│                          │ bifurcation_proximity, avg_correlation           │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Context                  │ session_progress, bars_since_entry,              │
│                          │ time_of_day, day_of_week                         │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Danger                   │ danger_score (from Risk Adversary)               │
└──────────────────────────┴──────────────────────────────────────────────────┘
```

---

## Persistence Architecture

### Two-Phase Commit Protocol

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TWO-PHASE COMMIT PROTOCOL                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: Write to temporary file                                           │
│           filename.dat.tmp                                                   │
│                │                                                             │
│                ▼                                                             │
│  Phase 2: Verify write completed (size check)                               │
│                │                                                             │
│                ▼                                                             │
│  Phase 3: Atomic rename                                                      │
│           filename.dat.tmp → filename.dat                                   │
│                │                                                             │
│                ▼                                                             │
│  Phase 4: Rotate backups                                                     │
│           .bak2 ← .bak1 ← .bak ← .dat (old)                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Files Persisted

```
MQL5/Files/
├── ProjectQuantum_EntryAgent.dat         (~10 MB)
├── ProjectQuantum_EntryAgent.dat.bak     (backup gen 1)
├── ProjectQuantum_EntryAgent.dat.bak1    (backup gen 2)
├── ProjectQuantum_EntryAgent.dat.bak2    (backup gen 3)
├── ProjectQuantum_ExitAgent.dat          (~15 MB)
├── ProjectQuantum_ReplayBuffer.dat       (~200 MB)
├── ProjectQuantum_RiskAdversary.dat      (~5 MB)
├── ProjectQuantum_LearningMetrics.dat    (~2 MB)
├── ProjectQuantum_RiskState.dat          (~1 MB)
└── ProjectQuantum_ActivePosition.dat     (temp, deleted on close)
```

---

## Deployment Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          METATRADER 5                                       │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     ProjectQuantum_Main.mq5                            │ │
│  │                     (Expert Advisor)                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────┬──────────────┬──────────────┬──────────────────────┐ │
│  │  Include/Core/   │ Include/     │ Include/     │ Include/             │ │
│  │  ├─ Core.mqh     │ Physics/     │ Intelligence/│ Performance/         │ │
│  │  ├─ SafeMath     │ ├─ CFractal  │ ├─ CRL_Agent │ ├─ CLearningMetrics  │ │
│  │  ├─ ArrayUtils   │ ├─ CPortfolio│ ├─ CRLExit   │ ├─ CRiskIntelligence │ │
│  │  ├─ SymbolUtils  │ └─ Physics   │ ├─ CAdversary│ └─ CPerformance      │ │
│  │  └─ Defensive    │              │ ├─ CJourney  │                      │ │
│  │                  │              │ └─ CReplay   │                      │ │
│  └──────────────────┴──────────────┴──────────────┴──────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────┬──────────────┬──────────────────────────────────────┐ │
│  │  Include/Risk/   │ Include/     │ Include/Architecture/               │ │
│  │  ├─ CThreeLevel  │ Safety/      │ ├─ Project_Quantum.mqh              │ │
│  │  ├─ CAssetClass  │ ├─ CCircuit  │ └─ (enums, structs, constants)      │ │
│  │  └─ CPositionSzr │ └─ Breaker   │                                      │ │
│  └──────────────────┴──────────────┴──────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │       BROKER API               │
                    │   (Orders/Positions/Data)      │
                    └────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Physics as Features, Not Constraints
Markets are reflexive and don't follow conservation laws. Physics metrics **inform** but don't **constrain** RL agent actions. The agent is free to learn any policy.

### 2. Adversarial Risk Prediction
A separate adversary trained to predict crashes provides **independent** risk assessment. Its reward (+1 correct, -1 false alarm) aligns incentives with crash prevention.

### 3. Three-Level Risk Hierarchy
Different risk concerns at different scales:
- **Micro**: Instrument volatility and liquidity
- **Meso**: Sector correlation and exposure
- **Macro**: Portfolio entropy and systemic risk

### 4. Journey RL Reward System
Multi-component reward shapes better exit behavior than simple profit maximization:
- MFE capture (take profits)
- MAE penalty (cut losses)
- Path efficiency (smooth equity curve)

### 5. Learning Quality Over Profit Metrics
"It's the journey that counts" - sample efficiency, Q-value stability, exploration quality, and physics predictive power measure **learning health**. Profit is outcome; learning is process.

### 6. NO ATR - Physics-Based Volatility Only
Yang-Zhang volatility estimator replaces ATR throughout. More robust, accounts for overnight gaps, and derived from price distribution rather than lagging indicator.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2024-12 | Four-layer architecture, Journey RL, Risk Adversary |
| 2.0.0 | 2024-Q3 | Physics integration, fractal analysis |
| 1.0.0 | 2024-Q1 | Initial release with basic RL |

---

*Document prepared by: Project Quantum Development Team*
*Last updated: 2024-12-21*
