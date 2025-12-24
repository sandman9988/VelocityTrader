# ProjectQuantum Handbook

## Purpose
This handbook distills the architecture, runtime flow, and interaction contracts of ProjectQuantum so teams can quickly spot mismatches, weak links, or missing pieces before deploying or extending the system. It is organized for rapid navigation during audits, incident response, and development.

## High-Level Architecture
ProjectQuantum is an Expert Advisor (EA) orchestrator (`ProjectQuantum_Main.mq5`) that composes modular components for sensing, regime classification, prediction, learning, risk control, and performance monitoring.

```
┌───────────────────────────┐
│      ProjectQuantum       │  Main EA orchestrates lifecycle and state machine
└───────────┬───────────────┘
            │
            ▼
┌───────────┴───────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│  Market Sensing &     │     │  Regime & Prediction │     │   Learning & Memory  │
│  Profiling            │     │  (CRegimeJudge,      │     │   (CRL_Agent,        │
│  (CMarketAgnostic,    │     │   CProbabilityPredictor)   │    CReplayBuffer)     │
│   CInstrumentProfiler)│     └───────────┬──────────┘     └───────────┬──────────┘
└───────────┬───────────┘                 │                            │
            ▼                             ▼                            │
┌───────────┴───────────┐     ┌──────────────────────┐                 │
│   Risk, Circuit,      │◄────┤  State Machine &     │                 │
│   Shadow Mgmt         │     │  Trade Execution     │                 │
│ (CRiskManager,        │     │  (ProcessTrading/    │                 │
│  CCircuitBreaker,     │     │   Manage/Close)      │                 │
│  CShadowManager)      │     └───────────┬──────────┘                 │
└───────────┬───────────┘                 │                            │
            ▼                             ▼                            │
┌───────────┴───────────┐     ┌──────────────────────┐                 │
│ Monitoring & HUD      │◄────┤ Persistence &        │◄────────────────┘
│ (CPerformanceMonitor, │     │ Position State       │
│  CLogger, CAgnostic   │     │ (planned Save/Load)  │
│  Clock, CSystemOptimizer)   │                      │
└───────────────────────┘     └──────────────────────┘
```

## Lifecycle & State Machine

### Initialization (`OnInit`)
1. Resolve target symbol/timeframe (`InpSymbol`, `InpTimeframe`).
2. Initialize logging via `CLogger::Initialize` and record session header.
3. Optionally run `CSystemOptimizer` when `InpOptimizeWindows` is enabled.
4. Construct all core components: sensors (`CMarketAgnostic`), profiling (`CInstrumentProfiler`), regime judge, RL agent, replay buffer, probability predictor, circuit breaker, shadow manager, risk manager, performance monitor, and agnostic clock.
5. Wire dependencies: circuit breaker references agent & replay buffer; shadow manager references live agent and clones current weights.
6. Start performance monitoring session and reset state/prediction/position trackers.
7. Honor manual release input if the circuit breaker is awaiting release.
8. Transition system state to `STATE_TRADING`.

### Tick Processing (`OnTick`)
Sequential flow executed per market tick:
1. Start tick timing and refresh health metrics via `CPerformanceMonitor`.
2. If terminal disconnected → set `STATE_DISCONNECTED`, draw HUD, and exit.
3. Refresh instrument profile (`g_profiler.Update`).
4. Capture current market state (`CMarketAgnostic.GetStateVector`) and enrich with instrument class/session metadata.
5. Classify regime (`CRegimeJudge.ClassifyRegime`) with smoothing over `InpRegimeSmoothing` ticks; update `g_current_regime` and confidence.
6. Generate probability prediction (`CProbabilityPredictor.Predict`).
7. Update circuit breaker thresholds using drawdown, consecutive losses, and Sortino inputs.
8. Update shadow strategies with current state, price, Yang-Zhang stop distance, live action, and Sortino.
9. Run state machine (`ProcessStateMachine`) to choose trade/management behavior.
10. If a position exists, update MAE/MFE metrics.
11. On new bar, trigger `OnNewBar` for predictor updates and weekend retraining checks.
12. Draw HUD (when enabled) and stop tick timing.

### System States
`ProcessStateMachine` governs the following:
- `STATE_INITIALIZING`: transient, moves to trading.
- `STATE_TRADING`: normal flow via `ProcessTradingState`.
- `STATE_DEGRADED`: only manage existing positions; exits when circuit ≤ YELLOW and session Sortino > 0.5.
- `STATE_LOCKED`: halt entries and close positions after RED circuit; resumes when circuit ≤ YELLOW.
- `STATE_RETRAINING`: circuit breaker handles; transitions to awaiting release or trading based on circuit status.
- `STATE_AWAITING_RELEASE`: manual intervention required via UI/input.
- `STATE_READY`: post-release bridge back to trading.
- `STATE_EMERGENCY`: full halt until restart.
- `STATE_DISCONNECTED`: waits for broker reconnection.

### Trading State Flow (`ProcessTradingState`)
1. Block or close positions based on circuit level (ORANGE blocks new entries; RED+ closes and locks).
2. Respect market risk from `CAgnosticClock` (swap danger, dangerous sessions).
3. Enforce spread guard (`CInstrumentProfiler.IsSpreadAcceptable`).
4. Choose action from RL agent (`CRL_Agent.ChooseAction`) filtered by prediction edge (`edge_magnitude`).
5. No position: only act on BUY/SELL; Position open: honor CLOSE or manage existing via `ManagePosition`.

### Deinitialization (`OnDeinit`)
- End performance session, persist agent brain, clean HUD, delete components, and log reason.

### Bar Event (`OnNewBar`)
- Increment bars held, update predictor with bar returns, and trigger weekend retraining for regime judge once per weekend.

### Tester Metric (`OnTester`)
- Returns session Sortino for optimizer criteria.

## Trade & Learning Lifecycle

```
State Vector → Regime Judge → Prediction → RL Action
     │             │              │           │
     └─────────────┴──────┬───────┴───────────┘
                           ▼
                   Trade Execution (ExecuteTrade)
                           │
                           ▼
                    Position Tracking (MAE/MFE)
                           │
                           ▼
                  Exit (ClosePosition / SLTP)
                           │
                           ▼
      ┌───────────────────┬─────────────────────────┬───────────────────┐
      │                   │                         │                   │
 Replay Buffer     Predictor Outcome Update   Performance Monitor   Shadow Feedback
 (experience)      (edge calibration)         (Sortino, HUD)        (virtual vs live)
      │
      ▼
 RL Agent Q-Update (terminal) and Healing/Replay
```

**Execution highlights:**
- `ExecuteTrade` computes Yang-Zhang volatility stops (no ATR), risk-adjusted lot size (`CRiskManager.GetSafeLotSize`), applies circuit multipliers, and normalizes volume before sending orders.
- `ManagePosition` trails stops once unrealized P&L exceeds initial risk, using SLTP modification requests.
- `OnPositionClosed` reconstructs trade metrics (R-multiple, MAE/MFE capture, smoothness, path efficiency, duration, regime at exit) and feeds them to the agent, replay buffer, predictor, monitor, and shadows with fragility-aware reward shaping that asymmetrically penalizes MAE.
- Healing logic triggers after `InpHealingInterval` trades using win rate and Sortino thresholds; it invokes agent healing and experience replay or weight normalization.

## Component Catalog (Capabilities & Dependencies)
- **CLogger.mqh** — Structured logging, levels, performance timing; used everywhere.
- **ProjectQuantum_Architecture.mqh** — Enumerations and data structs (`ENUM_REGIME`, `ENUM_TRADING_ACTION`, `ENUM_SYSTEM_STATE`, `SStateVector`, `SProbabilityPrediction`, `SProjectQuantumTrade`).
- **Core.mqh** — Foundational utilities: hash table, ring buffer, object pool, statistical helpers (`SafeDiv`, `SafeLog`, clamping).
- **CMarketAgnostic.mqh** — Sensor fusion producing `SStateVector` (z-scores, MER, entropy, VPIN, etc.) with adaptive cycles.
- **CInstrumentProfiler.mqh** — Instrument class detection, adaptive lookbacks, Yang-Zhang volatility profiling, spread guard.
- **CRegimeJudge.mqh** — Regime classification with confidence scoring; weekend retraining hook.
- **CProbabilityPredictor.mqh** — Seven-layer probability edge model (Bayesian priors, adaptive fractal energy response, MER, entropy, VPIN, kurtosis, z-score extremity) producing `SProbabilityPrediction` with `edge_magnitude` and direction odds.
- **CRL_Agent.mqh** — Q-learning agent using hash table for O(1) lookups; supports healing, replay, weight persistence (`SaveBrain`/`LoadBrain`).
- **CReplayBuffer.mqh** — Experience storage with O(1) ring buffer operations; computes drawdown, win rate, Sortino, failing regimes.
- **CShadowManager.mqh** — Manages multiple shadow agents and virtual positions; tracks shadow metrics, promotions, and Sortino comparison to live agent using Yang-Zhang volatility sizing.
- **CRiskManager.mqh** — Kelly/CVaR-based sizing, stop validation, and volume normalization; integrates kurtosis penalties and broker constraints.
- **CCircuitBreaker.mqh** — Multi-level circuit responding to drawdown, loss streaks, and Sortino; orchestrates retraining and manual release gating.
- **CPerformanceMonitor.mqh** — Session metrics, HUD rendering, health updates, latency tracking; provides Sortino used by circuit/shadows.
- **CAgnosticClock.mqh** — Detects unsafe windows (dangerous sessions, swap risk) to suppress entries or close risk.
- **CSystemOptimizer.mqh** — Optional runtime optimizations and performance tuning.

## Key Data Structures & Signals
- **SStateVector**: Market snapshot enriched with instrument class, session id/progress, timestamp, and smoothed regime with probability.
- **SProbabilityPrediction**: Directional edge magnitude and probability split; consumed to gate trades (`edge_magnitude < 0.01` ⇒ wait).
- **SProjectQuantumTrade**: Captures full lifecycle stats (prices, regimes, MAE/MFE, path efficiency, duration, R-multiple, P&L, smoothness) for replay and monitoring.
- **System Inputs**: `InpLearningRate`, `InpDiscountFactor`, `InpEpsilon`, `InpKellyFraction`, `InpMaxCVaR`, `InpMaxDailyDD`, `InpShadowCount`, `InpShadowSwitchThreshold`, etc.
- **Global State Flags**: `g_system_state`, `g_has_position`, `g_trades_since_healing`, `g_current_regime`, `g_regime_tick_count` for smoothing stability.

## Risk, Circuit, and Shadow Controls
- **Circuit breaker flow**: Levels progress GREEN → YELLOW → ORANGE → RED → BLACK based on drawdown, losses, and Sortino. ORANGE disables new entries; RED enforces closes; BLACK requires manual release. Retraining occurs in retraining state with agent healing and replay buffer data.
- **Risk sizing**: Lot size derives from Yang-Zhang volatility stop distance, risk-adjustment factor, Kelly/CVaR constraints, circuit multipliers, and broker normalization.
- **Shadow strategies**: Each shadow agent mirrors the live state stream, runs virtual trades using Yang-Zhang volatility sizing, and feeds metrics to determine promotions when Sortino gap exceeds `InpShadowSwitchThreshold` and minimum trades are met.

## Persistence & Monitoring
- **Logging**: CSV/structured logs via `CLogger`; session health and tick timing tracked by `CPerformanceMonitor`.
- **Position persistence**: `SavePositionState`, `LoadPositionState`, and `ReconcileExistingPositions` now live in `ProjectQuantum_Main.mq5`, backed by `CPersistence`. State is restored on init, reconciled against broker positions, saved every 10 ticks when a position is open, and flushed on deinit.
- **HUD**: `CPerformanceMonitor.DrawHUD` renders live state (system state, circuit level, shadow metrics, Sortino, regime) on chart when `InpShowHUD` is true.
- **Manual release**: UI/button handling in `OnChartEvent` relays codes to `CCircuitBreaker.AttemptManualRelease`; `InputBox` currently proxies the `InpReleaseCode` input.

## Diagrams for Audits

### Runtime State Machine
```
INITIALIZING → TRADING ↘
                 ↑      ↘
DISCONNECTED ────┘       DEGRADED ↘
                               ↑    ↘
LOCKED ← RED circuit  RETRAINING   AWAITING_RELEASE → READY → TRADING
     ↑                                                           ↙
EMERGENCY (requires restart) ← BLACK circuit
```

### Position Lifecycle & Feedback
```
Entry (ExecuteTrade)
  └─▶ Tracking (ManagePosition → TrailStop → UpdatePositionMetrics)
        └─▶ Exit (ClosePosition / External SLTP)
              └─▶ Metrics & Rewards (OnPositionClosed)
                    ├─▶ RL Update (UpdateQValue + ExperienceReplay)
                    ├─▶ Predictor Calibration (Update + RecordOutcome)
                    ├─▶ Replay Buffer (AddTrade + drawdown/Sortino stats)
                    ├─▶ Performance Monitor (RecordTrade + health)
                    └─▶ Shadow Feedback (FeedbackLivePerformance)
```

## Known Gaps, Mismatches, and Weaknesses to Track
- **Persistence validation**: Newly integrated persistence uses `CPersistence` plus periodic `SavePositionState` calls; exercise restart/resume scenarios on demo to confirm MAE/MFE tracking resumes and stale tickets are cleared.
- **Circuit release hardening pending**: `CCircuitBreaker` still needs the cryptographic release code enhancement referenced in the integration guide; manual release may be weaker than intended.
- **Manual release UX**: `InputBox` is a placeholder that simply returns `InpReleaseCode`; chart-side prompting is not implemented.
- **Smoothing sensitivity**: Regime smoothing relies on `InpRegimeSmoothing`; too small may cause oscillations, too large may lag transitions—validate per instrument.
- **Healing cadence**: Healing triggers on win rate/Sortino thresholds every `InpHealingInterval` trades; aggressive values can over-normalize the agent and reduce edge persistence.
- **HUD dependency**: `InpShowHUD` governs visualization; disabling it reduces at-a-glance observability of circuit status and shadow performance.

## `.mqh` Interaction Audit (Classes, Functions, and Cross-File Contracts)
> **Repository note:** All referenced `.mqh` component files now live under `Include/`. `ProjectQuantum_Architecture.mqh` acts as a compatibility shim over `Journey_Architecture.mqh`, exposing the legacy type aliases used by the main EA and documentation.

- **Architecture & Core**
  - `ProjectQuantum_Architecture.mqh` defines enums (`ENUM_REGIME`, `ENUM_TRADING_ACTION`, `ENUM_SYSTEM_STATE`) and structs (`SStateVector`, `SProbabilityPrediction`, `SProjectQuantumTrade`) consumed by every component and the main EA.
  - `Core.mqh` supplies foundational utilities (`CHashTable`, `CRingBuffer`, `CObjectPool`, statistical helpers) used by RL, buffers, risk, and validation layers.
  - `CLogger.mqh` underpins all logging; `CSystemOptimizer.mqh` is invoked first in `OnInit` to optimize runtime.
- **Market Sensing & Profiling**
  - `CMarketAgnostic.mqh` produces `SStateVector` snapshots; `CInstrumentProfiler.mqh` enriches class/session metadata and enforces spread guards consumed in `OnTick` and `ExecuteTrade`.
  - `CRegimeJudge.mqh` classifies regimes with confidence; `CAgnosticClock.mqh` blocks trades during dangerous sessions or swap windows (queried before entry).
- **Prediction, Learning, and Memory**
  - `CProbabilityPredictor.mqh` converts `SStateVector` into `SProbabilityPrediction` and edge magnitude; main EA gates actions when `edge_magnitude < 0.01`.
  - `CRL_Agent.mqh` chooses actions and updates Q-values; `CReplayBuffer.mqh` stores `SProjectQuantumTrade` records and exposes drawdown/win-rate/Sortino for circuit and healing logic.
  - `CShadowManager.mqh` mirrors live inputs (state, price, Yang-Zhang stop distance, live action, Sortino) to virtual agents and returns promotion metrics; fed every tick before the state machine.
- **Risk, Circuit, and Monitoring**
  - `CRiskManager.mqh` validates stops, normalizes volume, and sizes positions using CVaR/Kelly plus circuit multipliers; used inside `ExecuteTrade`.
  - `CCircuitBreaker.mqh` tracks drawdown/loss/Sortino inputs, sets system states (`STATE_LOCKED`, `STATE_RETRAINING`, `STATE_AWAITING_RELEASE`), and integrates `CRL_Agent`/`CReplayBuffer` for healing and retraining.
  - `CPerformanceMonitor.mqh` supplies session Sortino, tick timing, health status, and HUD rendering; consumed in `OnTick`, `OnDeinit`, and `OnTester`.
- **Persistence & Utilities**
  - `CPersistence.mqh` underpins the new `SavePositionState`/`LoadPositionState`/`ReconcileExistingPositions` trio in the main EA; it writes to global variables and a binary file with staleness checks.
  - `CSymbolNormalizer.mqh`, `CCompositeValidator.mqh`, `CGenetics.mqh`, and other utility headers are dependency-only in this snapshot; re-validate their interfaces once present.

## Main EA Coverage & Defensive Programming Checks
- **Strict syntax:** `ProjectQuantum_Main.mq5` declares `#property strict`, ensuring MQL5 strict compilation (type safety and explicit casting).
- **State integrity:** All enumerated system states are represented in `ProcessStateMachine`, with explicit reconnection handling, degraded/locked/retraining/awaiting release bridges, and READY passthrough.
- **Initialization safeguards:** `OnInit` verifies every component pointer, logs critical failures, initializes state/prediction structs, wires circuit/shadow references, and exits with `INIT_FAILED` on allocation issues.
- **Entry gating:** `ProcessTradingState` enforces circuit levels, dangerous-market checks (`CAgnosticClock`), and spread guards before consulting the RL agent; probability edges below threshold force `ACTION_WAIT`.
- **Risk controls:** `ExecuteTrade` validates stop distances, applies risk/circuit multipliers, normalizes volume, retries transient trade errors (via `CCore::IsRetryableError`), and records full position context for downstream metrics.
- **Position defense:** `ManagePosition` validates existence via `PositionSelectByTicket`, updates MAE/MFE defensively, and trails stops only after unrealized P&L exceeds initial risk with normalized SL precision.
- **Exit and feedback hygiene:** `ClosePosition` confirms selection, executes opposing market orders with magic number tagging, and reports failures. `OnPositionClosed` reconstructs trade metrics from history, guards divisions with `CCore::SafeDiv`, feeds agent/replay/predictor/monitor/shadow channels, increments healing counters, and triggers healing cadence.
- **Tick-time checks:** `OnTick` exits early on disconnection (state change + HUD), smooths regimes to avoid thrash, and updates predictor/shadow inputs before state machine decisions. `OnNewBar` refreshes predictor data and controls once-per-weekend retraining of `CRegimeJudge`.
- **Manual control path:** `OnChartEvent` and `InputBox` route release codes to `CCircuitBreaker`; UI prompt remains TODO but respects awaiting-release state.

## Quick Navigation Checklist for Audits
- **Entry/Exit correctness**: `ExecuteTrade`, `ManagePosition`, `TrailStop`, `ClosePosition`.
- **Learning integrity**: `OnPositionClosed`, `g_agent.UpdateQValue`, `g_agent.ExperienceReplay`, predictor updates.
- **Risk gating**: Circuit levels in `ProcessTradingState`, spread/clock guards, lot normalization.
- **Shadow alignment**: `CShadowManager.Update` inputs and promotion criteria against live Sortino.
- **Persistence readiness**: Confirm presence of position state functions and `CCircuitBreaker` release code security before production rollout.
