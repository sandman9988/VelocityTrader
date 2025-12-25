//+------------------------------------------------------------------+
//|                                    VelocityTrader_v7_1_Duel.mq5  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|                                                                  |
//|  2-AGENT / 3-REGIME EVOLUTIONARY RL SYSTEM                       |
//|  ═══════════════════════════════════════════════════════════════ |
//|                                                                  |
//|  AGENTS:                                                         |
//|    • SNIPER    - Patient, high-conviction, rides trends          |
//|    • BERSERKER - Aggressive, quick entries, volatility hunter    |
//|                                                                  |
//|  REGIMES (Physics-Detected):                                     |
//|    • BREAKOUT  - Steep ROC, explosive acceleration               |
//|    • TREND     - Sustained ROC, persistent velocity              |
//|    • MEANREV   - High χ, decelerating at extremes                |
//|    • CRITICAL  - No clear state, no trade                        |
//|                                                                  |
//|  THE DUEL:                                                       |
//|    • Each agent has Real (Champion) vs Shadow (Challenger)       |
//|    • Shadow beats Real → Swap (evolution)                        |
//|    • Sniper vs Berserker → Capital allocation                    |
//|                                                                  |
//|  SAFETY GATES:                                                   |
//|    • Statistical Edge (must beat coin flip + friction)           |
//|    • Probability Predictor (per-trade P(Win) threshold)          |
//|    • Circuit Breaker (auto-retrain, manual reinstatement)        |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"
#property version   "7.10"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\DealInfo.mqh>

// ═══════════════════════════════════════════════════════════════════
// MODULAR INCLUDES - VelocityTrader v7.1 Component Library
// ═══════════════════════════════════════════════════════════════════
// Include chain (loaded via VT_Globals.mqh):
//   - VT_Definitions.mqh    (constants, enums, safe math helpers)
//   - VT_RLParameters.mqh   (RL tunable parameters)
//   - VT_Structures.mqh     (core data structures: BrokerSpec, etc.)
//   - VT_Predictor.mqh      (probability predictor, statistical gate)
//   - VT_CircuitBreaker.mqh (risk management state machine)
//   - VT_KinematicRegimes.mqh (regime detection)
// Additional includes loaded directly:
//   - VT_HUD.mqh            (heads-up display rendering)
//   - VT_Persistence.mqh    (state save/load)
//   - VT_Performance.mqh    (ring buffers, caches)
// ═══════════════════════════════════════════════════════════════════

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                  |
//+------------------------------------------------------------------+
input group "═══ CORE SETTINGS ═══"
input int       InpMagicNumber = 710001;         // Magic Number
input double    InpRiskPercent = 1.0;            // Risk % per trade
input double    InpMaxLot = 1.0;                 // Maximum lot size
input int       InpMaxPositions = 5;             // Max concurrent positions
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_H1;  // Timeframe

input group "═══ PHYSICS ENGINE ═══"
input bool      InpUseLevel2 = true;             // Use Level 2 DOM data
input int       InpL2Depth = 10;                 // L2 depth (levels)
input double    InpMassDecay = 0.95;             // Synthetic mass decay
input int       InpPhysicsBuffer = 100;          // Normalization buffer

input group "═══ REGIME DETECTION ═══"
input double    InpBreakoutAccel = 2.0;          // Breakout acceleration threshold (σ)
input double    InpTrendAccel = 0.8;             // Trend min acceleration (σ)
input int       InpTrendPersist = 5;             // Trend persistence (bars)
input double    InpMRChiThreshold = 1.3;         // Mean Reversion χ threshold
input double    InpMRDecelThreshold = 0.5;       // MR deceleration threshold
input int       InpCalibrationTicks = 100;       // Calibration period

input group "═══ AGENT PARAMETERS ═══"
input double    InpSniperThreshold = 1.5;        // Sniper signal threshold (σ)
input double    InpBerserkerThreshold = 1.0;     // Berserker signal threshold (σ)
input double    InpLearningRateInit = 0.15;      // Initial learning rate
input double    InpLearningRateMin = 0.01;       // Minimum learning rate
input double    InpLearningDecay = 0.995;        // Learning rate decay per trade
input double    InpExplorationRate = 0.15;       // Shadow exploration rate
input int       InpShadowTimeoutMin = 15;        // Shadow trade timeout (minutes) - shorter=faster learning
input double    InpShadowSL_ATR = 2.0;           // Shadow SL (ATR multiplier)
input double    InpShadowTP_ATR = 1.5;           // Shadow TP (ATR multiplier) - tighter=faster learning
input double    InpSwapThreshold = 1.10;         // Swap if shadow 10% better PF
input int       InpSwapMinTrades = 30;           // Min trades before swap eval

input group "═══ PROBABILITY PREDICTOR ═══"
input double    InpMinProbability = 0.55;        // Min P(Win) to trade
input bool      InpUseOmegaSizing = true;        // Use Omega-based sizing
input double    InpOmegaBaseline = 1.0;          // Omega baseline (1.0 = break-even)
input double    InpOmegaMaxScale = 1.5;          // Max size multiplier at high Omega

input group "═══ STATISTICAL GATE ═══"
input bool      InpRequireEdge = true;           // Require statistical edge
input double    InpMinWinRate = 0.52;            // Minimum win rate
input double    InpMaxPValue = 0.05;             // Max p-value (significance)
input int       InpMinTradesForEdge = 30;        // Min trades to prove edge

input group "═══ CIRCUIT BREAKER ═══"
input double    InpMaxDailyLoss = 0.03;          // Max daily loss (3%)
input int       InpMaxConsLosses = 5;            // Max consecutive losses
input double    InpMaxDrawdown = 0.10;           // Max drawdown (10%)
input double    InpMinRollingWR = 0.45;          // Min rolling WR (20 trades)
input int       InpCooldownMinutes = 60;         // Cooldown before retrain
input int       InpRetrainMinTrades = 20;        // Min trades to restore
input double    InpRetrainMinWR = 0.52;          // Min WR to restore
input double    InpRetrainMinPF = 1.10;          // Min PF to restore

input group "═══ CAPITAL ALLOCATION ═══"
input double    InpMinAllocation = 0.20;         // Min agent allocation (20%)
input double    InpMaxAllocation = 0.80;         // Max agent allocation (80%)
input int       InpAllocationPeriod = 50;        // Rebalance every N trades

input group "═══ DISPLAY ═══"
input bool      InpShowHUD = true;               // Show HUD
input int       InpHUD_X = 10;                   // HUD X position
input int       InpHUD_Y = 25;                   // HUD Y position
input int       InpDefaultTab = 0;               // Default tab (0-5)
input bool      InpAutoRotateTabs = false;       // Auto-rotate tabs every 5s
input int       InpTopSymbols = 8;               // Top symbols to display

input group "═══ MULTI-SYMBOL ═══"
input bool      InpTradeForex = true;            // Trade Forex
input bool      InpTradeMetals = true;           // Trade Metals
input bool      InpTradeIndices = false;         // Trade Indices
input bool      InpTradeCrypto = false;          // Trade Crypto

input group "═══ PERSISTENCE ═══"
input bool      InpUsePersistence = true;        // Save/Load state
input string    InpFilePrefix = "VelDuel_";      // File prefix

input group "═══ MANUAL OVERRIDE ═══"
input bool      InpManualReinstate = false;      // Set TRUE to reinstate
input bool      InpForceHalt = false;            // Set TRUE to force halt
input bool      InpShadowOnly = false;           // Shadow only mode

// ═══════════════════════════════════════════════════════════════════
// INCLUDE MODULAR COMPONENTS
// ═══════════════════════════════════════════════════════════════════
#include <VT_Globals.mqh>              // All structs and global variables
#include <VT_HUD.mqh>                  // HUD rendering functions
#include <VT_Persistence.mqh>          // State save/load functions
#include <VT_Performance.mqh>          // Performance optimizations (ring buffers, caches)

// ═══════════════════════════════════════════════════════════════════
// LEGACY INLINE DEFINITIONS (Now in header files - kept for reference)
// ═══════════════════════════════════════════════════════════════════
// The following definitions are now in Include/*.mqh files:
// - VT_Definitions.mqh: MAX_SYMBOLS, MAX_POSITIONS, ROLLING_WINDOW,
//                       PERSISTENCE_MAGIC, enums, color defines
// - VT_RLParameters.mqh: RLParameters struct
// - VT_Structures.mqh: WelfordStats, BrokerSpec, StrategyStats,
//                      AgentProfile, TradingAgent, VelocityRank,
//                      PositionData, PeriodStats, ExcursionStats, SystemStatus
// - VT_Predictor.mqh: ProbabilityPredictor, StatisticalGate
// - VT_CircuitBreaker.mqh: CircuitBreaker
// - VT_Globals.mqh: SymCData, PhysicsEngine, SymbolInfo, all g_* variables
// ═══════════════════════════════════════════════════════════════════


//+------------------------------------------------------------------+
//| DEFENSE IN DEPTH: Validate all input parameters                   |
//| Returns false if any parameter is out of safe range               |
//+------------------------------------------------------------------+
bool ValidateInputParameters()
{
   bool valid = true;

   // Risk parameters
   if(InpRiskPercent <= 0 || InpRiskPercent > 10.0)
   {
      Print("ERROR: InpRiskPercent must be 0-10% (got ", InpRiskPercent, ")");
      valid = false;
   }

   if(InpMaxLot <= 0 || InpMaxLot > 100.0)
   {
      Print("ERROR: InpMaxLot must be 0.01-100 (got ", InpMaxLot, ")");
      valid = false;
   }

   if(InpMaxPositions <= 0 || InpMaxPositions > MAX_POSITIONS)
   {
      Print("ERROR: InpMaxPositions must be 1-", MAX_POSITIONS, " (got ", InpMaxPositions, ")");
      valid = false;
   }

   if(InpMaxDrawdown <= 0 || InpMaxDrawdown > 1.0)
   {
      Print("ERROR: InpMaxDrawdown must be 0-1.0 (got ", InpMaxDrawdown, ")");
      valid = false;
   }

   // Learning parameters
   if(InpLearningRateInit <= 0 || InpLearningRateInit > 1.0)
   {
      Print("ERROR: InpLearningRateInit must be 0-1.0 (got ", InpLearningRateInit, ")");
      valid = false;
   }

   // Signal threshold parameters (sigma thresholds, not 0-1 probabilities)
   if(InpSniperThreshold <= 0 || InpSniperThreshold > 10.0)
   {
      Print("ERROR: InpSniperThreshold must be 0-10σ (got ", InpSniperThreshold, ")");
      valid = false;
   }

   if(InpBerserkerThreshold <= 0 || InpBerserkerThreshold > 10.0)
   {
      Print("ERROR: InpBerserkerThreshold must be 0-10σ (got ", InpBerserkerThreshold, ")");
      valid = false;
   }

   if(InpMinProbability < 0 || InpMinProbability > 1.0)
   {
      Print("ERROR: InpMinProbability must be 0-1.0 (got ", InpMinProbability, ")");
      valid = false;
   }

   // Buffer sizes
   if(InpPhysicsBuffer < 10 || InpPhysicsBuffer > 1000)
   {
      Print("WARNING: InpPhysicsBuffer unusual (", InpPhysicsBuffer, "), using anyway");
   }

   if(valid)
      Print("Input parameter validation: PASSED");

   return valid;
}

//+------------------------------------------------------------------+
//| EXPERT INITIALIZATION                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("═══════════════════════════════════════════════════════════");
   Print("   VelocityTrader v7.1: DUEL ARCHITECTURE");
   Print("   2 Agents × 3 Regimes × Shadow/Real Duel");
   Print("═══════════════════════════════════════════════════════════");
   
   // Detect mode
   bool isBacktest = (MQLInfoInteger(MQL_TESTER) != 0);
   bool isOptimization = (MQLInfoInteger(MQL_OPTIMIZATION) != 0);
   Print("Mode: ", isBacktest ? "BACKTEST" : "LIVE",
         isOptimization ? " (Optimization)" : "");

   // DEFENSE IN DEPTH: Validate all input parameters
   if(!ValidateInputParameters())
   {
      Print("ERROR: Input validation failed. Check parameters.");
      return INIT_PARAMETERS_INCORRECT;
   }

   // Initialize trade object
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(30);
   g_trade.SetTypeFilling(ORDER_FILLING_IOC);
   
   // Initialize RL parameters (normalized 0-1)
   g_rlParams.Init();

   // Initialize divergent agent profiles (Sniper vs Berserker)
   InitAgentProfiles();

   // Initialize session tracking
   g_sessionEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   g_sessionStart = TimeCurrent();
   
   // Initialize period tracking
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   g_dayStats.Reset(equity);
   g_weekStats.Reset(equity);
   g_monthStats.Reset(equity);
   g_totalStats.Reset(equity);
   
   // Initialize excursion tracking
   g_sniperExcursion.Init();
   g_berserkerExcursion.Init();
   
   // Initialize status
   g_status.Update();
   
   // Initialize agents
   g_sniper.Init("SNIPER", CLR_SNIPER, InpSniperThreshold);
   g_berserker.Init("BERSERKER", CLR_BERSERKER, InpBerserkerThreshold);
   
   // Initialize systems
   g_predictor.Init();
   g_breaker.Init();
   
   // Initialize symbols
   if(!InitializeSymbols())
   {
      Print("Failed to initialize symbols");
      return INIT_FAILED;
   }
   
   // Load state
   LoadState();

   // Initialize performance manager (ring buffers, caches)
   InitPerformance();

   // Timer for updates - use milliseconds for finer control
   // 250ms interval for smooth HUD updates and deferred processing
   EventSetMillisecondTimer(TIMER_INTERVAL_MS);

   Print("Initialization complete. Symbols: ", g_symbolCount);
   Print("System State: ", g_breaker.GetStateString());
   Print("Sniper threshold: ", InpSniperThreshold, " Berserker: ", InpBerserkerThreshold);
   Print("Min probability: ", InpMinProbability, " (ONLY for real trades)");
   Print("Shadow trades: ALWAYS enabled for learning");
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| EXPERT DEINITIALIZATION                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   SaveState();
   CleanupHUD();
   EventKillTimer();

   // Release L2 subscriptions
   int symLimit = MathMin(g_symbolCount, MAX_SYMBOLS);
   for(int i = 0; i < symLimit; i++)
   {
      if(g_symbols[i].initialized)
      {
         g_symbols[i].physics.Deinit();
         if(g_symbols[i].atrHandle != INVALID_HANDLE)
            IndicatorRelease(g_symbols[i].atrHandle);
      }
   }

   Print("VelocityTrader v7.1 deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| TIMER FUNCTION                                                    |
//+------------------------------------------------------------------+
void OnTimer()
{
   // ════════════════════════════════════════════════════════════════
   // TIMER: Non-critical operations moved here for better OnTick perf
   // Runs every TIMER_INTERVAL_MS (250ms default)
   // DEFENSE IN DEPTH: Drawdown checked via g_breaker.Update() + OnTick
   // DATA INTEGRITY: No trading in OnTimer - warmup handled by OnTick
   // ════════════════════════════════════════════════════════════════

   // Skip timer operations during warmup (OnTick handles warmup)
   if(g_perfManager.tickCounter < InpCalibrationTicks)
      return;

   static datetime lastSecond = 0;
   static datetime lastHUDRefresh = 0;
   static int timerTicks = 0;
   datetime now = TimeCurrent();
   timerTicks++;

   // ─── Every Timer Tick (250ms) ───
   // Process deferred symbol updates from queue
   int symbolIdx;
   while(g_perfManager.updateQueue.Dequeue(symbolIdx))
   {
      if(symbolIdx >= 0 && symbolIdx < g_symbolCount && g_symbols[symbolIdx].initialized)
      {
         UpdateSymbol(symbolIdx);
         g_perfManager.OnSymbolUpdated();
      }
   }

   // ─── Every 4 Timer Ticks (~1 second) ───
   if(timerTicks % 4 == 0 || now != lastSecond)
   {
      lastSecond = now;

      // Update circuit breaker state
      g_breaker.Update();

      // Check for period resets (day/week/month)
      CheckPeriodResets();

      // Update system status
      g_status.Update();
   }

   // ─── Every 20 Timer Ticks (~5 seconds) ───
   if(timerTicks % 20 == 0)
   {
      // Check for agent swaps
      CheckAgentSwaps();

      // Update edge status
      UpdateEdgeStatus();

      // Update capital allocation periodically
      static int lastAllocUpdate = 0;
      int totalTrades = g_sniper.real.totalTrades + g_berserker.real.totalTrades;
      if(totalTrades - lastAllocUpdate >= InpAllocationPeriod)
      {
         UpdateCapitalAllocation();
         lastAllocUpdate = totalTrades;
      }

      // Update velocity ranking (moved from OnTick)
      UpdateRanking();

      // Invalidate HUD cache to force refresh
      g_perfManager.hudCache.Invalidate();
   }

   // ─── HUD Refresh (throttled to avoid flicker) ───
   if(InpShowHUD && (now != lastHUDRefresh || timerTicks % 4 == 0))
   {
      if(g_perfManager.hudCache.NeedsRefresh())
      {
         DrawHUD();
         g_perfManager.hudCache.MarkRefreshed();
         lastHUDRefresh = now;
      }
   }

   // ─── Every 240 Timer Ticks (~60 seconds) ───
   if(timerTicks % 240 == 0)
   {
      // Update low-priority symbols that weren't updated via OnTick
      int symLimit = MathMin(g_symbolCount, MAX_SYMBOLS);
      for(int i = 0; i < symLimit; i++)
      {
         if(g_perfManager.symbolData[i].priority == PRIORITY_IDLE)
         {
            if(g_symbols[i].initialized && g_symbols[i].typeAllowed)
               UpdateSymbol(i);
         }
      }
   }

   // ─── Every 1200 Timer Ticks (~5 minutes) ───
   if(timerTicks % 1200 == 0)
   {
      // Save state periodically
      SaveState();

      // Print performance stats
      Print("Perf: ", GetPerfStatsString(),
            " Queue:", g_perfManager.updateQueue.Count());
   }
}

//+------------------------------------------------------------------+
//| CHECK PERIOD RESETS - Reset daily/weekly/monthly stats            |
//+------------------------------------------------------------------+
void CheckPeriodResets()
{
   static datetime lastDayCheck = 0;
   datetime now = TimeCurrent();

   // Only check once per minute to avoid overhead
   if(now - lastDayCheck < 60) return;
   lastDayCheck = now;

   MqlDateTime dt;
   TimeToStruct(now, dt);

   MqlDateTime dtStart;
   TimeToStruct(g_dayStats.startTime, dtStart);

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   // Daily reset - new day started
   if(dt.day != dtStart.day || dt.mon != dtStart.mon || dt.year != dtStart.year)
   {
      // Log yesterday's stats before reset
      if(g_dayStats.trades > 0)
      {
         Print("DAY END: PnL=", DoubleToString(g_dayStats.pnl, 2),
               " Trades=", g_dayStats.trades,
               " WR=", DoubleToString(g_dayStats.GetWR(), 1), "%");
      }

      g_dayStats.Reset(equity);
      g_sessionEquity = equity;  // Reset session equity too

      // Also reset agent session stats for fresh daily comparison
      g_sniper.ResetSession();
      g_berserker.ResetSession();

      Print("New trading day started - stats reset");
   }

   // Weekly reset - Monday (day_of_week == 1)
   TimeToStruct(g_weekStats.startTime, dtStart);
   if(dt.day_of_week == 1 && (dt.day != dtStart.day || dt.mon != dtStart.mon))
   {
      if(g_weekStats.trades > 0)
      {
         Print("WEEK END: PnL=", DoubleToString(g_weekStats.pnl, 2),
               " Trades=", g_weekStats.trades,
               " WR=", DoubleToString(g_weekStats.GetWR(), 1), "%");
      }
      g_weekStats.Reset(equity);
      Print("New trading week started - weekly stats reset");
   }

   // Monthly reset - 1st of month
   TimeToStruct(g_monthStats.startTime, dtStart);
   if(dt.day == 1 && (dt.mon != dtStart.mon || dt.year != dtStart.year))
   {
      if(g_monthStats.trades > 0)
      {
         Print("MONTH END: PnL=", DoubleToString(g_monthStats.pnl, 2),
               " Trades=", g_monthStats.trades,
               " WR=", DoubleToString(g_monthStats.GetWR(), 1), "%");
      }
      g_monthStats.Reset(equity);
      Print("New trading month started - monthly stats reset");
   }
}

//+------------------------------------------------------------------+
//| DEFENSE IN DEPTH: Explicit drawdown check                         |
//| Returns true if drawdown exceeds limit (trading should stop)      |
//+------------------------------------------------------------------+
bool IsDrawdownExceeded()
{
   static double peakEquity = 0;
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   if(equity > peakEquity) peakEquity = equity;
   if(peakEquity <= 0) return false;

   // DEFENSE IN DEPTH: Use SafeDivide even though we checked peakEquity > 0
   double drawdown = SafeDivide(peakEquity - equity, peakEquity, 0.0);
   return (drawdown > InpMaxDrawdown);
}

//+------------------------------------------------------------------+
//| TICK FUNCTION - Performance Optimized with Tiered Updates         |
//| Critical path only - non-critical work deferred to OnTimer        |
//+------------------------------------------------------------------+
void OnTick()
{
   // DEFENSE IN DEPTH: Explicit drawdown check (redundant with circuit breaker)
   if(IsDrawdownExceeded())
   {
      static datetime lastWarn = 0;
      if(TimeCurrent() - lastWarn > 60)  // Warn once per minute
      {
         Print("WARNING: Drawdown exceeded ", InpMaxDrawdown * 100, "% - trading suspended");
         lastWarn = TimeCurrent();
      }
      return;
   }

   // Notify performance manager
   g_perfManager.OnTickStart();
   int tickCount = g_perfManager.tickCounter;

   // DATA INTEGRITY: Warmup period for RL feature engineering
   // During warmup: collect data, update features, but NO trading
   static bool warmupComplete = false;
   if(!warmupComplete)
   {
      if(tickCount < InpCalibrationTicks)
      {
         // Still in warmup - update data but don't trade
         for(int i = 0; i < g_symbolCount; i++)
         {
            if(g_symbols[i].initialized)
               UpdateSymbol(i);
         }
         if(tickCount % 100 == 0)
            Print("Warmup: ", tickCount, "/", InpCalibrationTicks, " ticks...");
         return;
      }
      warmupComplete = true;
      Print("Warmup complete after ", InpCalibrationTicks, " ticks. Trading enabled.");
   }

   // ════════════════════════════════════════════════════════════════
   // CRITICAL PATH: Minimum work on every tick
   // ════════════════════════════════════════════════════════════════

   // 1. Always update current chart symbol immediately (CRITICAL)
   int currentIdx = FindSymbolIndex(_Symbol);
   if(currentIdx >= 0 && g_symbols[currentIdx].initialized)
   {
      UpdateSymbol(currentIdx);
      g_perfManager.symbolData[currentIdx].priority = PRIORITY_CRITICAL;
      g_perfManager.OnSymbolUpdated();
   }

   // 2. Always manage positions (CRITICAL)
   ManagePositions();

   // 3. Check for new signals if allowed (CRITICAL when trading)
   if(g_breaker.CanTradeShadow())
   {
      ProcessSignals();
   }

   // ════════════════════════════════════════════════════════════════
   // TIERED UPDATES: Priority-based symbol updates
   // ════════════════════════════════════════════════════════════════

   // Update symbols based on their priority level
   for(int i = 0; i < g_symbolCount; i++)
   {
      if(i == currentIdx) continue;  // Already updated above
      if(!g_symbols[i].initialized || !g_symbols[i].typeAllowed) continue;

      ENUM_UPDATE_PRIORITY priority = g_perfManager.symbolData[i].priority;

      // Check if this symbol should be updated this tick
      if(g_perfManager.symbolData[i].ShouldUpdate(tickCount))
      {
         // HIGH priority: update immediately
         if(priority <= PRIORITY_HIGH)
         {
            UpdateSymbol(i);
            g_perfManager.OnSymbolUpdated();
         }
         // MEDIUM/LOW priority: queue for deferred processing
         else if(priority <= PRIORITY_LOW)
         {
            g_perfManager.updateQueue.Enqueue(i, (int)priority);
         }
         // IDLE priority: skip, will be updated in OnTimer
      }
   }

   // ════════════════════════════════════════════════════════════════
   // UPDATE PRIORITIES: Based on current state
   // Every 50 ticks, reassess symbol priorities
   // ════════════════════════════════════════════════════════════════
   if(tickCount % 50 == 0)
   {
      // Build lists of symbols with positions and top-ranked
      int posSymbols[MAX_POSITIONS];
      int posCount = 0;
      int posLimit = MathMin(g_posCount, MAX_POSITIONS);
      for(int i = 0; i < posLimit; i++)
      {
         if(g_positions[i].active && posCount < MAX_POSITIONS)
         {
            int symIdx = FindSymbolIndex(g_positions[i].symbol);
            if(symIdx >= 0)
               posSymbols[posCount++] = symIdx;
         }
      }

      int topSymbols[10];
      int topCount = MathMin(MathMin(10, g_rankCount), MAX_SYMBOLS);
      for(int i = 0; i < topCount; i++)
      {
         if(IsValidIndex(i, MAX_SYMBOLS))
            topSymbols[i] = g_ranking[i].symbolIdx;
      }

      g_perfManager.UpdatePriorities(posSymbols, posCount, topSymbols, topCount, currentIdx);
   }

   // NOTE: HUD updates moved to OnTimer for smoother rendering
   // NOTE: Ranking updates moved to OnTimer (every 5 seconds)
}

//+------------------------------------------------------------------+
//| INITIALIZE SYMBOLS                                                |
//+------------------------------------------------------------------+
bool InitializeSymbols()
{
   int total = SymbolsTotal(true);
   g_symbolCount = 0;
   
   for(int i = 0; i < total && g_symbolCount < MAX_SYMBOLS; i++)
   {
      string sym = SymbolName(i, true);
      
      if(SymbolInfoDouble(sym, SYMBOL_BID) <= 0) continue;
      
      int idx = g_symbolCount++;
      g_symbols[idx].Clear();
      g_symbols[idx].name = sym;
      
      if(!GetBrokerSpec(sym, g_symbols[idx].spec))
      {
         g_symbolCount--;
         continue;
      }
      
      g_symbols[idx].assetType = ClassifyAsset(sym);
      g_symbols[idx].typeAllowed = IsTypeAllowed(g_symbols[idx].assetType);
      
      // Create ATR indicator with error handling and retry
      g_symbols[idx].atrHandle = iATR(sym, InpTimeframe, 14);
      if(g_symbols[idx].atrHandle == INVALID_HANDLE)
      {
         // Retry once with a short delay
         Sleep(50);
         g_symbols[idx].atrHandle = iATR(sym, InpTimeframe, 14);
         if(g_symbols[idx].atrHandle == INVALID_HANDLE)
         {
            int err = GetLastError();
            Print("WARNING: InitializeSymbols - ATR indicator failed for ", sym,
                  " (error: ", err, "). Will use price-based fallback ATR.");
            // Symbol can still be used - UpdateSymbol will use fallback ATR calculation
         }
      }
      
      g_symbols[idx].physics.Init(sym);
      g_symbols[idx].symc.Init();
      g_symbols[idx].initialized = true;
   }
   
   return (g_symbolCount > 0);
}

//+------------------------------------------------------------------+
//| GET BROKER SPECIFICATION                                          |
//| Returns false if any critical symbol property cannot be retrieved |
//+------------------------------------------------------------------+
bool GetBrokerSpec(string sym, BrokerSpec &spec)
{
   // Query all symbol properties with individual error checking
   bool success = true;
   int errorCount = 0;
   string errorFields = "";

   // Critical fields - must be valid for trading
   spec.point = SymbolInfoDouble(sym, SYMBOL_POINT);
   if(spec.point <= 0 || !MathIsValidNumber(spec.point))
   {
      errorCount++;
      errorFields += "point,";
   }

   spec.bid = SymbolInfoDouble(sym, SYMBOL_BID);
   if(spec.bid <= 0 || !MathIsValidNumber(spec.bid))
   {
      errorCount++;
      errorFields += "bid,";
   }

   spec.ask = SymbolInfoDouble(sym, SYMBOL_ASK);
   if(spec.ask <= 0 || !MathIsValidNumber(spec.ask))
   {
      errorCount++;
      errorFields += "ask,";
   }

   spec.tickSize = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE);
   if(spec.tickSize <= 0 || !MathIsValidNumber(spec.tickSize))
   {
      // Use point as fallback for tick size
      spec.tickSize = spec.point;
      if(spec.tickSize <= 0)
      {
         errorCount++;
         errorFields += "tickSize,";
      }
   }

   spec.tickValue = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE);
   if(spec.tickValue <= 0 || !MathIsValidNumber(spec.tickValue))
   {
      // Use 1.0 as fallback - will be corrected on first trade
      spec.tickValue = 1.0;
      // Don't count as error since we have a fallback
   }

   spec.digits = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
   if(spec.digits < 0 || spec.digits > 8)
   {
      // Use 5 as default for forex pairs
      spec.digits = 5;
   }

   spec.spread = spec.ask - spec.bid;
   if(spec.spread < 0 || !MathIsValidNumber(spec.spread))
   {
      spec.spread = 0;  // Will be updated on next tick
   }

   spec.volumeMin = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   if(spec.volumeMin <= 0 || !MathIsValidNumber(spec.volumeMin))
   {
      spec.volumeMin = 0.01;  // Default minimum lot
   }

   spec.volumeMax = SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX);
   if(spec.volumeMax <= 0 || !MathIsValidNumber(spec.volumeMax))
   {
      spec.volumeMax = 100.0;  // Default maximum lot
   }

   spec.volumeStep = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);
   if(spec.volumeStep <= 0 || !MathIsValidNumber(spec.volumeStep))
   {
      spec.volumeStep = 0.01;  // Default step
   }

   // Estimate commission
   double contractSize = SymbolInfoDouble(sym, SYMBOL_TRADE_CONTRACT_SIZE);
   if(contractSize <= 0 || !MathIsValidNumber(contractSize))
   {
      contractSize = 100000.0;  // Default forex contract size
   }
   spec.commission = contractSize * 0.00001;  // Estimate

   // Log errors if any critical fields failed
   if(errorCount > 0)
   {
      Print("ERROR: GetBrokerSpec - Failed to get ", errorCount, " critical field(s) for ", sym, ": ", errorFields);
      return false;
   }

   // Sanity check: ask should be >= bid
   if(spec.ask < spec.bid)
   {
      Print("WARNING: GetBrokerSpec - Invalid spread for ", sym, " (ask=", spec.ask, " < bid=", spec.bid, ")");
      // Swap them to fix
      double temp = spec.bid;
      spec.bid = spec.ask;
      spec.ask = temp;
      spec.spread = spec.ask - spec.bid;
   }

   return true;
}

//+------------------------------------------------------------------+
//| CLASSIFY ASSET TYPE                                               |
//+------------------------------------------------------------------+
ENUM_ASSET_TYPE ClassifyAsset(string sym)
{
   string upper = sym;
   StringToUpper(upper);
   
   if(StringFind(upper, "XAU") >= 0 || StringFind(upper, "XAG") >= 0 ||
      StringFind(upper, "GOLD") >= 0 || StringFind(upper, "SILVER") >= 0)
      return ASSET_METAL;
      
   if(StringFind(upper, "BTC") >= 0 || StringFind(upper, "ETH") >= 0 ||
      StringFind(upper, "CRYPTO") >= 0)
      return ASSET_CRYPTO;
      
   if(StringFind(upper, "US30") >= 0 || StringFind(upper, "US500") >= 0 ||
      StringFind(upper, "NAS") >= 0 || StringFind(upper, "DAX") >= 0 ||
      StringFind(upper, "SPX") >= 0 || StringFind(upper, "NDX") >= 0)
      return ASSET_INDEX;
   
   // Check for forex pairs
   string majors[] = {"EUR","USD","GBP","JPY","CHF","AUD","NZD","CAD"};
   for(int i = 0; i < ArraySize(majors); i++)
   {
      if(StringFind(upper, majors[i]) >= 0)
         return ASSET_FOREX;
   }
   
   return ASSET_OTHER;
}

//+------------------------------------------------------------------+
//| CHECK IF ASSET TYPE ALLOWED                                       |
//+------------------------------------------------------------------+
bool IsTypeAllowed(ENUM_ASSET_TYPE type)
{
   switch(type)
   {
      case ASSET_FOREX:  return InpTradeForex;
      case ASSET_METAL:  return InpTradeMetals;
      case ASSET_INDEX:  return InpTradeIndices;
      case ASSET_CRYPTO: return InpTradeCrypto;
      default:           return false;
   }
}

//+------------------------------------------------------------------+
//| UPDATE SYMBOL DATA                                                |
//+------------------------------------------------------------------+
void UpdateSymbol(int idx)
{
   if(!IsValidIndex(idx, MAX_SYMBOLS)) return;
   if(!g_symbols[idx].initialized) return;

   // Refresh spec (always needed for trading)
   double bid = SymbolInfoDouble(g_symbols[idx].name, SYMBOL_BID);
   g_symbols[idx].spec.bid = bid;
   g_symbols[idx].spec.ask = SymbolInfoDouble(g_symbols[idx].name, SYMBOL_ASK);
   g_symbols[idx].spec.spread = g_symbols[idx].spec.ask - g_symbols[idx].spec.bid;

   // Record price in ring buffer for history
   g_perfManager.symbolData[idx].RecordPrice(bid);

   // Get ATR FIRST (needed for physics update)
   double atr = g_symbols[idx].atr;  // Use cached value initially
   bool atrFromIndicator = false;

   // Try to get ATR from indicator
   if(g_symbols[idx].atrHandle != INVALID_HANDLE)
   {
      double atrBuf[];
      int copied = CopyBuffer(g_symbols[idx].atrHandle, 0, 0, 1, atrBuf);
      if(copied > 0 && MathIsValidNumber(atrBuf[0]) && atrBuf[0] > 0)
      {
         atr = atrBuf[0];
         g_symbols[idx].atr = atr;
         atrFromIndicator = true;

         // Store in ring buffer for rolling average
         g_perfManager.symbolData[idx].RecordATR(atr);

         // Use ring buffer average instead of EMA (more stable)
         if(g_perfManager.symbolData[idx].atrHistory.Count() >= 5)
            g_symbols[idx].avgATR = g_perfManager.symbolData[idx].GetAvgATR();
         else if(g_symbols[idx].avgATR == 0)
            g_symbols[idx].avgATR = atr;
         else
            g_symbols[idx].avgATR = (g_symbols[idx].avgATR * 0.98) + (atr * 0.02);
      }
      else if(copied < 0)
      {
         // Log error only occasionally to avoid spam
         static int atrErrorCount = 0;
         if(atrErrorCount++ % 1000 == 0)
         {
            Print("WARNING: UpdateSymbol - CopyBuffer failed for ATR on ", g_symbols[idx].name,
                  " (error: ", GetLastError(), "). Using fallback.");
         }
      }
   }

   // Fallback ATR calculation if indicator not available or failed
   if(!atrFromIndicator || atr <= 0 || !MathIsValidNumber(atr))
   {
      // Use price-based fallback: approximately 0.1% of price for forex
      // Adjust for different asset types
      double fallbackPct = 0.001;  // 0.1% default
      if(g_symbols[idx].assetType == ASSET_CRYPTO)
         fallbackPct = 0.02;  // 2% for crypto (more volatile)
      else if(g_symbols[idx].assetType == ASSET_INDEX)
         fallbackPct = 0.005;  // 0.5% for indices

      double fallbackATR = bid * fallbackPct;

      // If we have a previous valid ATR, blend it with fallback
      if(g_symbols[idx].atr > 0 && MathIsValidNumber(g_symbols[idx].atr))
         atr = (g_symbols[idx].atr * 0.9) + (fallbackATR * 0.1);
      else
         atr = fallbackATR;

      g_symbols[idx].atr = atr;
   }

   // Update physics with price and ATR (real kinematic calculations)
   g_symbols[idx].physics.UpdateWithATR(bid, atr);

   // Record velocity/acceleration in ring buffer
   double velocity = g_symbols[idx].physics.GetVelocity();
   double accel = g_symbols[idx].physics.GetAcceleration();
   g_perfManager.symbolData[idx].RecordVelocity(velocity, accel);

   // Get flow estimate
   MqlTick tick;
   double flow = 1.0;
   if(SymbolInfoTick(g_symbols[idx].name, tick))
   {
      flow = (double)tick.volume_real;
      if(flow == 0) flow = (double)tick.volume;
   }
   flow = MathMax(flow, 1.0);

   // Update SymC (regime detection from physics state)
   g_symbols[idx].symc.Update(
      g_symbols[idx].physics.GetMass(),
      flow,
      bid,
      g_symbols[idx].physics
   );

   // Mark as updated
   g_perfManager.symbolData[idx].lastUpdate = TimeCurrent();
   g_perfManager.symbolData[idx].needsUpdate = false;
}

//+------------------------------------------------------------------+
//| UPDATE VELOCITY RANKING                                           |
//+------------------------------------------------------------------+
void UpdateRanking()
{
   g_rankCount = 0;

   int symLimit = MathMin(g_symbolCount, MAX_SYMBOLS);
   for(int i = 0; i < symLimit && g_rankCount < MAX_SYMBOLS; i++)
   {
      if(!g_symbols[i].initialized || !g_symbols[i].typeAllowed) continue;
      if(g_symbols[i].halted) continue;

      // Include symbols even if physics not fully ready (for learning)
      // Use acceleration if available, otherwise use 0.5 as default score
      double score = 0.5;
      if(g_symbols[i].physics.IsReady())
         score = MathAbs(g_symbols[i].physics.GetAcceleration()) + 0.1;

      g_ranking[g_rankCount].symbolIdx = i;
      g_ranking[g_rankCount].score = score;
      g_rankCount++;
   }

   // Sort by score (descending) - ready symbols will rank higher
   int rankLimit = MathMin(g_rankCount, MAX_SYMBOLS);
   for(int i = 0; i < rankLimit - 1; i++)
   {
      for(int j = i + 1; j < rankLimit; j++)
      {
         if(g_ranking[j].score > g_ranking[i].score)
         {
            VelocityRank temp = g_ranking[i];
            g_ranking[i] = g_ranking[j];
            g_ranking[j] = temp;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| PROCESS SIGNALS                                                   |
//+------------------------------------------------------------------+
void ProcessSignals()
{
   int openPos = CountOpenPositions();
   if(openPos >= InpMaxPositions) return;

   // Debug: Check ranking status periodically
   static datetime lastDebug = 0;
   if(TimeCurrent() - lastDebug > 60 && g_rankCount == 0)
   {
      lastDebug = TimeCurrent();
      int notReady = 0;
      int symLimit = MathMin(g_symbolCount, MAX_SYMBOLS);
      for(int i = 0; i < symLimit; i++)
         if(g_symbols[i].initialized && !g_symbols[i].physics.IsReady()) notReady++;
      Print("DEBUG: g_rankCount=0, NotReady=", notReady, "/", g_symbolCount);
   }

   int cnt = MathMin(MathMin(g_rankCount, InpTopSymbols), MAX_SYMBOLS);

   for(int i = 0; i < cnt && openPos < InpMaxPositions; i++)
   {
      if(!IsValidIndex(i, MAX_SYMBOLS)) continue;
      int idx = g_ranking[i].symbolIdx;
      if(!IsValidIndex(idx, MAX_SYMBOLS)) continue;
      
      // Skip if already have position on this symbol
      if(HasPositionOnSymbol(g_symbols[idx].name)) continue;
      
      // Get regime - ALLOW shadow learning even in CRITICAL/CALIBRATING
      ENUM_REGIME regime = g_symbols[idx].symc.GetRegime();
      int regimeIdx = g_symbols[idx].symc.GetRegimeIndex();
      
      // Map CRITICAL/CALIBRATING to TREND for shadow learning
      if(regime == REGIME_CALIBRATING || regime == REGIME_CRITICAL || regimeIdx < 0)
      {
         regime = REGIME_TREND;
         regimeIdx = 1;
      }
      
      double accel = g_symbols[idx].physics.GetAcceleration();
      double chiZ = g_symbols[idx].symc.GetChiZ();
      double priceZ = g_symbols[idx].symc.GetPriceDeviation();
      
      // Process both agents
      ProcessAgentSignal(g_sniper, idx, regimeIdx, regime, accel, chiZ, priceZ);
      ProcessAgentSignal(g_berserker, idx, regimeIdx, regime, accel, chiZ, priceZ);
      
      openPos = CountOpenPositions();
   }
}

//+------------------------------------------------------------------+
//| PROCESS AGENT SIGNAL                                              |
//+------------------------------------------------------------------+
void ProcessAgentSignal(TradingAgent &agent, int symIdx, int regimeIdx,
                        ENUM_REGIME regime, double accel, double chiZ, double priceZ)
{
   // Validate indices
   if(!IsValidIndex(symIdx, MAX_SYMBOLS)) return;
   if(regimeIdx < 0 || regimeIdx >= 3) return;

   // Determine action based on regime and agent threshold
   int action = GetAgentAction(agent, regime, accel, priceZ);
   if(action == 0) return;
   
   // Calculate win probability
   double agentWR = agent.shadow.regime[regimeIdx].GetWinRate();
   if(agentWR < 0.01) agentWR = 0.5;  // Default to 50% if no data
   double pWin = g_predictor.Predict(regimeIdx, chiZ, accel, agentWR);
   
   // Determine agent ID
   int agentId = (agent.name == "SNIPER") ? AGENT_SNIPER : AGENT_BERSERKER;
   
   // Calculate position size
   double lots = CalculateLots(symIdx, pWin, agent.capitalAlloc, agentId, regimeIdx);
   if(lots < g_symbols[symIdx].spec.volumeMin) 
      lots = g_symbols[symIdx].spec.volumeMin;  // Use minimum lot for learning
   
   // ═══════════════════════════════════════════════════════════════
   // SHADOW TRADE: ALWAYS execute for learning (no gates!)
   // ═══════════════════════════════════════════════════════════════
   ExecuteShadowTrade(symIdx, action, lots, agentId, regimeIdx, pWin);
   
   // ═══════════════════════════════════════════════════════════════
   // REAL TRADE: Apply probability gate and other requirements
   // ═══════════════════════════════════════════════════════════════
   if(pWin < InpMinProbability) return;  // Gate only for real trades
   
   if(g_breaker.CanTradeLive() && agent.hasEdge && !InpShadowOnly)
   {
      ExecuteRealTrade(symIdx, action, lots, agentId, regimeIdx, pWin);
   }
}

//+------------------------------------------------------------------+
//| GET AGENT ACTION                                                  |
//+------------------------------------------------------------------+
int GetAgentAction(TradingAgent &agent, ENUM_REGIME regime, double accel, double priceZ)
{
   double threshold = agent.signalThreshold;
   
   // Lower thresholds during learning phase (first 100 trades) - RL-tunable
   bool learningPhase = (agent.shadow.totalTrades < 100);
   if(learningPhase)
      threshold *= g_rlParams.GetLearnMult();  // RL-tunable learning threshold
   
   // RL-tunable thresholds
   double trendMult = g_rlParams.GetTrendMult();
   double momentumMult = g_rlParams.GetMomentumMult();
   double meanRevThresh = g_rlParams.GetMeanRevThresh();
   double extremeZ = g_rlParams.GetZScoreExtreme();
   
   switch(regime)
   {
      case REGIME_BREAKOUT:
         // Trade with acceleration
         if(accel > threshold) return 1;     // Up acceleration
         if(accel < -threshold) return -1;   // Down acceleration
         break;
         
      case REGIME_TREND:
         // Trade with sustained direction - RL-tunable permissiveness
         if(accel > threshold * trendMult) return 1;
         if(accel < -threshold * trendMult) return -1;
         break;
         
      case REGIME_MEANREV:
         // Fade extremes - RL-tunable thresholds
         if(priceZ > meanRevThresh && accel < 0) return -1;   // Overbought + decelerating
         if(priceZ < -meanRevThresh && accel > 0) return 1;   // Oversold + accelerating
         // Also trade when very overbought/oversold regardless of accel
         if(priceZ > extremeZ) return -1;
         if(priceZ < -extremeZ) return 1;
         break;
         
      default:
         // For unknown regimes, use simple momentum - RL-tunable
         if(MathAbs(accel) > threshold * momentumMult)
            return (accel > 0) ? 1 : -1;
         break;
   }
   
   // Fallback: During learning, take more trades - RL-tunable velocity threshold
   double velThresh = g_rlParams.GetVelocityThresh();
   if(learningPhase && MathAbs(accel) > velThresh)
      return (accel > 0) ? 1 : -1;
   
   return 0;  // No action
}

//+------------------------------------------------------------------+
//| CALCULATE LOT SIZE                                                |
//+------------------------------------------------------------------+
double CalculateLots(int symIdx, double pWin, double agentAlloc, int agentId, int regimeIdx)
{
   // Validate symIdx
   if(!IsValidIndex(symIdx, MAX_SYMBOLS)) return 0;

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskAmount = equity * (InpRiskPercent / 100.0) * agentAlloc;

   // Omega-based sizing if enabled
   if(InpUseOmegaSizing)
   {
      // Get Omega from the agent's shadow for this regime
      double omega = 1.0;  // Default (break-even)

      if(agentId == AGENT_SNIPER && regimeIdx >= 0 && regimeIdx < 3)
         omega = g_sniper.shadow.regime[regimeIdx].GetOmega();
      else if(agentId == AGENT_BERSERKER && regimeIdx >= 0 && regimeIdx < 3)
         omega = g_berserker.shadow.regime[regimeIdx].GetOmega();

      double omegaScale = g_predictor.GetOmegaSize(omega, pWin);
      riskAmount *= omegaScale;
   }

   double atr = g_symbols[symIdx].atr;
   if(atr <= 0) return 0;

   double slDistance = atr * 2.0;
   double tickSize = g_symbols[symIdx].spec.tickSize;
   double tickValue = g_symbols[symIdx].spec.tickValue;

   if(tickSize <= 0) tickSize = g_symbols[symIdx].spec.point;
   if(tickValue <= 0) tickValue = 1.0;

   double slTicks = SafeDivide(slDistance, tickSize, 0.0);
   if(slTicks <= 0) return 0;

   double lots = SafeDivide(riskAmount, slTicks * tickValue, 0.0);

   return NormalizeLot(g_symbols[symIdx].spec, lots);
}

//+------------------------------------------------------------------+
//| NORMALIZE LOT SIZE                                                |
//+------------------------------------------------------------------+
double NormalizeLot(const BrokerSpec &spec, double lots)
{
   lots = MathMax(lots, spec.volumeMin);
   lots = MathMin(lots, spec.volumeMax);
   lots = MathMin(lots, InpMaxLot);
   
   if(spec.volumeStep > 0)
      lots = MathFloor(lots / spec.volumeStep) * spec.volumeStep;
   
   return NormalizeDouble(lots, 2);
}

//+------------------------------------------------------------------+
//| CALCULATE FRICTION COST                                           |
//+------------------------------------------------------------------+
double CalculateFriction(int symIdx, double lots)
{
   // Validate symIdx
   if(!IsValidIndex(symIdx, MAX_SYMBOLS)) return 0;

   double spread = g_symbols[symIdx].spec.spread;
   double tickSize = g_symbols[symIdx].spec.tickSize;
   double tickValue = g_symbols[symIdx].spec.tickValue;

   if(tickSize <= 0) tickSize = g_symbols[symIdx].spec.point;
   if(tickValue <= 0) tickValue = 1.0;

   double spreadCost = SafeDivide(spread, tickSize, 0.0) * tickValue * lots;
   double commission = g_symbols[symIdx].spec.commission * lots * 2;  // Round trip

   return spreadCost + commission;
}

//+------------------------------------------------------------------+
//| EXECUTE SHADOW TRADE                                              |
//+------------------------------------------------------------------+
void ExecuteShadowTrade(int symIdx, int direction, double lots, int agentId,
                        int regimeIdx, double pWin)
{
   // Validate indices
   if(!IsValidIndex(symIdx, MAX_SYMBOLS)) return;
   if(g_posCount >= MAX_POSITIONS) return;

   double entryPrice = (direction > 0) ?
                       g_symbols[symIdx].spec.ask :
                       g_symbols[symIdx].spec.bid;

   if(entryPrice <= 0) return;  // Invalid price

   double slDistance = g_symbols[symIdx].atr * InpShadowSL_ATR;
   if(slDistance <= 0) slDistance = entryPrice * 0.01;  // 1% fallback

   double sl = (direction > 0) ? (entryPrice - slDistance) : (entryPrice + slDistance);

   int slot = g_posCount++;
   if(!IsValidIndex(slot, MAX_POSITIONS)) { g_posCount--; return; }
   g_positions[slot].ticket = 0;  // No real ticket
   g_positions[slot].symbol = g_symbols[symIdx].name;
   g_positions[slot].direction = direction;
   g_positions[slot].entryPrice = entryPrice;
   g_positions[slot].currentSL = sl;
   g_positions[slot].lots = lots;
   g_positions[slot].entryATR = g_symbols[symIdx].atr;
   g_positions[slot].agentId = agentId;
   g_positions[slot].isShadow = true;
   g_positions[slot].regimeAtEntry = regimeIdx;
   g_positions[slot].frictionCost = CalculateFriction(symIdx, lots);
   g_positions[slot].openTime = TimeCurrent();
   g_positions[slot].pWinAtEntry = pWin;
   g_positions[slot].active = true;
   
   // Initialize MAE/MFE tracking
   g_positions[slot].mae = 0;
   g_positions[slot].mfe = 0;
   g_positions[slot].currentPnL = 0;
   
   // Debug output for shadow trades
   static int shadowCount = 0;
   shadowCount++;
   string agentName = (agentId == AGENT_SNIPER) ? "SNI" : "BER";
   string regName = (regimeIdx == 0) ? "BRK" : (regimeIdx == 1) ? "TRD" : "MR";
   Print("SHADOW #", shadowCount, ": ", agentName, " ", 
         (direction > 0 ? "BUY" : "SELL"), " ", 
         g_symbols[symIdx].name, " [", regName, "] P=", 
         DoubleToString(pWin * 100, 0), "%");
}

//+------------------------------------------------------------------+
//| EXECUTE REAL TRADE                                                |
//+------------------------------------------------------------------+
void ExecuteRealTrade(int symIdx, int direction, double lots, int agentId,
                      int regimeIdx, double pWin)
{
   // Validate indices
   if(!IsValidIndex(symIdx, MAX_SYMBOLS)) return;
   if(g_posCount >= MAX_POSITIONS) return;

   // DO NO HARM: Validate ATR before using for stop loss
   double atr = g_symbols[symIdx].atr;
   if(atr <= 0 || !MathIsValidNumber(atr))
   {
      Print("ERROR: ExecuteRealTrade - invalid ATR for ", g_symbols[symIdx].name,
            " (ATR=", atr, "). Trade rejected to prevent harm.");
      return;
   }

   double entryPrice = (direction > 0) ?
                       g_symbols[symIdx].spec.ask :
                       g_symbols[symIdx].spec.bid;

   // Validate entry price
   if(entryPrice <= 0 || !MathIsValidNumber(entryPrice))
   {
      Print("ERROR: ExecuteRealTrade - invalid entry price for ", g_symbols[symIdx].name);
      return;
   }

   double slDistance = atr * 2.0;
   double sl = (direction > 0) ? (entryPrice - slDistance) : (entryPrice + slDistance);
   sl = NormalizeDouble(sl, g_symbols[symIdx].spec.digits);

   // MQL5 GOTCHA: Cannot use pointers to structs
   // Use direct access instead of: TradingAgent *agent = &g_sniper
   string agentName = (agentId == AGENT_SNIPER) ? g_sniper.name : g_berserker.name;
   string comment = "Vel" + agentName;

   bool result = false;
   if(direction > 0)
      result = g_trade.Buy(lots, g_symbols[symIdx].name, 0, sl, 0, comment);
   else
      result = g_trade.Sell(lots, g_symbols[symIdx].name, 0, sl, 0, comment);

   if(result)
   {
      int slot = g_posCount++;
      if(!IsValidIndex(slot, MAX_POSITIONS)) { g_posCount--; return; }

      // Initialize ticket/positionId
      g_positions[slot].ticket = 0;
      g_positions[slot].positionId = 0;

      // Capture POSITION_TICKET and POSITION_IDENTIFIER via symbol select
      // (you only allow one position per symbol, so this is reliable)
      if(PositionSelect(g_symbols[symIdx].name))
      {
         long mg = (long)PositionGetInteger(POSITION_MAGIC);
         if(mg == (long)InpMagicNumber)
         {
            g_positions[slot].ticket = (ulong)PositionGetInteger(POSITION_TICKET);
            g_positions[slot].positionId = (long)PositionGetInteger(POSITION_IDENTIFIER);
         }
      }

      g_positions[slot].symbol = g_symbols[symIdx].name;
      g_positions[slot].direction = direction;
      g_positions[slot].entryPrice = entryPrice;
      g_positions[slot].currentSL = sl;
      g_positions[slot].lots = lots;
      g_positions[slot].entryATR = g_symbols[symIdx].atr;
      g_positions[slot].agentId = agentId;
      g_positions[slot].isShadow = false;
      g_positions[slot].regimeAtEntry = regimeIdx;
      g_positions[slot].frictionCost = CalculateFriction(symIdx, lots);
      g_positions[slot].openTime = TimeCurrent();
      g_positions[slot].pWinAtEntry = pWin;
      g_positions[slot].active = true;

      Print("REAL Trade: ", agentName, " ",
            (direction > 0 ? "BUY" : "SELL"), " ",
            g_symbols[symIdx].name, " @ ", entryPrice,
            " P(Win)=", DoubleToString(pWin * 100, 1), "%",
            " PosID=", g_positions[slot].positionId);
   }
   else
   {
      // DO NO HARM: Log trade failures for monitoring and debugging
      uint retcode = g_trade.ResultRetcode();
      Print("ERROR: Trade FAILED for ", g_symbols[symIdx].name,
            " | Retcode: ", retcode,
            " | ", g_trade.ResultRetcodeDescription(),
            " | Lots: ", lots,
            " | SL: ", sl);
   }
}

//+------------------------------------------------------------------+
//| MANAGE POSITIONS                                                  |
//+------------------------------------------------------------------+
void ManagePositions()
{
   for(int i = g_posCount - 1; i >= 0; i--)
   {
      if(!IsValidIndex(i, MAX_POSITIONS)) continue;
      if(!g_positions[i].active) continue;

      if(g_positions[i].isShadow)
         ManageShadowPosition(i);
      else
         ManageRealPosition(i);
   }

   // Compact array
   int w = 0;
   for(int i = 0; i < g_posCount && i < MAX_POSITIONS; i++)
   {
      if(!IsValidIndex(i, MAX_POSITIONS)) continue;
      if(g_positions[i].active)
      {
         if(w != i && IsValidIndex(w, MAX_POSITIONS)) g_positions[w] = g_positions[i];
         w++;
      }
   }
   g_posCount = w;
}

//+------------------------------------------------------------------+
//| MANAGE SHADOW POSITION                                            |
//+------------------------------------------------------------------+
void ManageShadowPosition(int idx)
{
   // Validate index
   if(!IsValidIndex(idx, MAX_POSITIONS)) return;

   string sym = g_positions[idx].symbol;
   double bid = SymbolInfoDouble(sym, SYMBOL_BID);
   double ask = SymbolInfoDouble(sym, SYMBOL_ASK);

   // Calculate current P&L for MAE/MFE tracking
   double currentPrice = (g_positions[idx].direction > 0) ? bid : ask;
   double pnlPoints = (g_positions[idx].direction > 0) ?
                      (currentPrice - g_positions[idx].entryPrice) :
                      (g_positions[idx].entryPrice - currentPrice);

   double point = SymbolInfoDouble(sym, SYMBOL_POINT);
   double pnlPips = SafeDivide(pnlPoints, point, 0.0);
   g_positions[idx].currentPnL = pnlPips;
   
   // Update MAE (worst drawdown)
   if(pnlPips < g_positions[idx].mae)
      g_positions[idx].mae = pnlPips;
   
   // Update MFE (best profit)
   if(pnlPips > g_positions[idx].mfe)
      g_positions[idx].mfe = pnlPips;
   
   // Check stop loss
   bool slHit = (g_positions[idx].direction > 0 && bid <= g_positions[idx].currentSL) ||
                (g_positions[idx].direction < 0 && ask >= g_positions[idx].currentSL);
   
   // Time-based exit (configurable minutes)
   int ageMin = (int)((TimeCurrent() - g_positions[idx].openTime) / 60);
   bool timeout = (ageMin >= InpShadowTimeoutMin);
   
   // Take profit: configurable ATR move (default 1.5x for faster learning)
   double tpDistance = g_positions[idx].entryATR * InpShadowTP_ATR;
   bool tpHit = (pnlPoints >= tpDistance);
   
   // Debug: Print status every minute for first position
   static datetime lastDebug = 0;
   if(idx == 0 && TimeCurrent() - lastDebug >= 60)
   {
      lastDebug = TimeCurrent();
      Print("SHADOW STATUS: ", sym, " Age:", ageMin, "m/", InpShadowTimeoutMin, "m",
            " PnL:", DoubleToString(pnlPips, 1), " pips",
            " SL:", slHit ? "HIT" : "OK", " TP:", tpHit ? "HIT" : "OK");
   }
   
   if(slHit || timeout || tpHit)
   {
      CloseShadowPosition(idx, slHit ? 0 : (tpHit ? 1 : 2));
   }
   else
   {
      // Trailing stop
      TrailShadowPosition(idx, bid, ask);
   }
}

//+------------------------------------------------------------------+
//| CLOSE SHADOW POSITION                                             |
//+------------------------------------------------------------------+
void CloseShadowPosition(int idx, int reason)
{
   // Validate index
   if(!IsValidIndex(idx, MAX_POSITIONS)) return;

   string sym = g_positions[idx].symbol;
   double exitPrice;

   if(reason == 0)  // SL
      exitPrice = g_positions[idx].currentSL;
   else
      exitPrice = (g_positions[idx].direction > 0) ?
                  SymbolInfoDouble(sym, SYMBOL_BID) :
                  SymbolInfoDouble(sym, SYMBOL_ASK);

   // Calculate PnL
   double diff = (g_positions[idx].direction > 0) ?
                 (exitPrice - g_positions[idx].entryPrice) :
                 (g_positions[idx].entryPrice - exitPrice);

   double tickSize = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE);
   if(tickSize <= 0) tickSize = SymbolInfoDouble(sym, SYMBOL_POINT);
   if(tickValue <= 0) tickValue = 1.0;

   double grossPnL = SafeDivide(diff, tickSize, 0.0) * tickValue * g_positions[idx].lots;
   double netPnL = grossPnL - g_positions[idx].frictionCost;
   
   // Update MAE/MFE excursion stats
   if(g_positions[idx].agentId == AGENT_SNIPER)
      g_sniperExcursion.Update(g_positions[idx].mae, g_positions[idx].mfe);
   else
      g_berserkerExcursion.Update(g_positions[idx].mae, g_positions[idx].mfe);
   
   // Update period stats
   bool won = (netPnL > 0);
   g_dayStats.pnl += netPnL;
   g_dayStats.trades++;
   if(won) g_dayStats.wins++;
   g_weekStats.pnl += netPnL;
   g_weekStats.trades++;
   if(won) g_weekStats.wins++;
   g_monthStats.pnl += netPnL;
   g_monthStats.trades++;
   if(won) g_monthStats.wins++;
   g_totalStats.pnl += netPnL;
   g_totalStats.trades++;
   if(won) g_totalStats.wins++;
   
   // Calculate reward
   int duration = (int)((TimeCurrent() - g_positions[idx].openTime) / 60);
   double reward = CalculateReward(grossPnL, g_positions[idx].frictionCost, duration);
   
   // Apply exploration rate for shadow
   double exploreReward = reward;
   if(MathRand() / 32767.0 < InpExplorationRate)
      exploreReward *= (0.8 + (MathRand() / 32767.0) * 0.4);  // Noise
   
   // MQL5 GOTCHA: Cannot use pointers to structs - use direct access
   string agentName;
   if(g_positions[idx].agentId == AGENT_SNIPER)
   {
      g_sniper.shadow.UpdateTrade(g_positions[idx].regimeAtEntry, netPnL, exploreReward,
                                  g_positions[idx].direction);
      agentName = "SNI";
   }
   else
   {
      g_berserker.shadow.UpdateTrade(g_positions[idx].regimeAtEntry, netPnL, exploreReward,
                                     g_positions[idx].direction);
      agentName = "BER";
   }
   
   // Update predictor
   int symIdx = FindSymbolIndex(sym);
   if(symIdx >= 0)
   {
      double chiZ = g_symbols[symIdx].symc.GetChiZ();
      double accel = g_symbols[symIdx].physics.GetAcceleration();
      g_predictor.Update(g_positions[idx].regimeAtEntry, chiZ, accel, won);
   }
   
   // Record for circuit breaker retrain
   g_breaker.RecordRetrainTrade(netPnL);
   
   // Debug output
   string reasonStr = (reason == 0) ? "SL" : (reason == 1) ? "TP" : "TIME";
   // Show Q-values after update (with bounds check on regime index)
   int regIdx = g_positions[idx].regimeAtEntry;
   if(regIdx < 0 || regIdx >= 3) regIdx = 0;  // Clamp to valid regime range
   double qB, qS;
   if(g_positions[idx].agentId == AGENT_SNIPER)
   {
      qB = g_sniper.shadow.regime[regIdx].qBuy;
      qS = g_sniper.shadow.regime[regIdx].qSell;
   }
   else
   {
      qB = g_berserker.shadow.regime[regIdx].qBuy;
      qS = g_berserker.shadow.regime[regIdx].qSell;
   }
   
   string regName = (regIdx == 0) ? "BRK" : (regIdx == 1) ? "TRD" : "MR";
   Print("SHADOW CLOSE: ", agentName, " ", sym, " ", reasonStr, 
         " PnL=", DoubleToString(netPnL, 2),
         won ? " WIN" : " LOSS",
         " [", regName, "] Q:", DoubleToString(qB, 2), "/", DoubleToString(qS, 2),
         " Total:", (g_positions[idx].agentId == AGENT_SNIPER) ? 
                     g_sniper.shadow.totalTrades : g_berserker.shadow.totalTrades);
   
   g_positions[idx].active = false;
}

//+------------------------------------------------------------------+
//| TRAIL SHADOW POSITION                                             |
//+------------------------------------------------------------------+
void TrailShadowPosition(int idx, double bid, double ask)
{
   // Validate index
   if(!IsValidIndex(idx, MAX_POSITIONS)) return;

   double trailDist = g_positions[idx].entryATR * g_rlParams.GetTrailATR();
   double newSL = g_positions[idx].currentSL;

   if(g_positions[idx].direction > 0)
   {
      double potentialSL = bid - trailDist;
      if(potentialSL > g_positions[idx].currentSL)
         newSL = potentialSL;
   }
   else
   {
      double potentialSL = ask + trailDist;
      if(potentialSL < g_positions[idx].currentSL)
         newSL = potentialSL;
   }

   g_positions[idx].currentSL = newSL;
}

//+------------------------------------------------------------------+
//| MANAGE REAL POSITION                                              |
//+------------------------------------------------------------------+
void ManageRealPosition(int idx)
{
   // Validate index
   if(!IsValidIndex(idx, MAX_POSITIONS)) return;

   // Check if position still exists (use symbol select since we enforce one position per symbol)
   bool exists = PositionSelect(g_positions[idx].symbol);
   if(exists)
   {
      long mg = (long)PositionGetInteger(POSITION_MAGIC);
      if(mg != (long)InpMagicNumber)
         exists = false;
   }

   if(!exists)
   {
      // Position closed - find PnL from history using POSITION_IDENTIFIER
      double pnl = 0.0;

      if(g_positions[idx].positionId > 0 && HistorySelectByPosition((ulong)g_positions[idx].positionId))
      {
         // Primary path: use positionId (best accuracy)
         int deals = HistoryDealsTotal();
         for(int d = 0; d < deals; d++)
         {
            ulong dealTicket = HistoryDealGetTicket(d);
            pnl += HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
            pnl += HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);
            pnl += HistoryDealGetDouble(dealTicket, DEAL_SWAP);
         }
      }
      else
      {
         // Fallback: scan recent deals by symbol+magic+time
         datetime fromTime = g_positions[idx].openTime - 60;
         datetime toTime = TimeCurrent();
         if(HistorySelect(fromTime, toTime))
         {
            int deals = HistoryDealsTotal();
            for(int d = 0; d < deals; d++)
            {
               ulong dealTicket = HistoryDealGetTicket(d);
               if(HistoryDealGetString(dealTicket, DEAL_SYMBOL) != g_positions[idx].symbol) continue;
               if((long)HistoryDealGetInteger(dealTicket, DEAL_MAGIC) != (long)InpMagicNumber) continue;

               pnl += HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
               pnl += HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);
               pnl += HistoryDealGetDouble(dealTicket, DEAL_SWAP);
            }
         }
      }

      // Update agent real
      int duration = (int)((TimeCurrent() - g_positions[idx].openTime) / 60);
      double reward = CalculateReward(pnl + g_positions[idx].frictionCost,
                                     g_positions[idx].frictionCost, duration);

      // MQL5 GOTCHA: Cannot use pointers to structs - use direct access
      string agentName;
      if(g_positions[idx].agentId == AGENT_SNIPER)
      {
         g_sniper.real.UpdateTrade(g_positions[idx].regimeAtEntry, pnl, reward,
                                   g_positions[idx].direction);
         g_sniper.RecordTrade(pnl);
         agentName = g_sniper.name;
      }
      else
      {
         g_berserker.real.UpdateTrade(g_positions[idx].regimeAtEntry, pnl, reward,
                                      g_positions[idx].direction);
         g_berserker.RecordTrade(pnl);
         agentName = g_berserker.name;
      }

      // Circuit breaker tracking
      g_breaker.RecordDailyPnL(pnl);

      // Check triggers
      double rollingWR = MathMax(g_sniper.GetRollingWR(), g_berserker.GetRollingWR());
      int maxConsLoss = MathMax(g_sniper.consLosses, g_berserker.consLosses);
      g_breaker.CheckTriggers(rollingWR, maxConsLoss);

      // Symbol circuit breaker
      int symIdx = FindSymbolIndex(g_positions[idx].symbol);
      if(IsValidIndex(symIdx, MAX_SYMBOLS))
      {
         g_symbols[symIdx].dailyPnL += pnl;
         if(pnl < 0) g_symbols[symIdx].consLosses++;
         else g_symbols[symIdx].consLosses = 0;
      }

      Print("REAL Close: ", agentName, " ", g_positions[idx].symbol,
            " PnL: ", DoubleToString(pnl, 2));

      g_positions[idx].active = false;
      return;
   }
   
   // Trailing stop
   double bid = SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_ASK);
   double point = SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(g_positions[idx].symbol, SYMBOL_DIGITS);
   
   double trailDist = g_positions[idx].entryATR * 1.5;
   double newSL = g_positions[idx].currentSL;
   
   if(g_positions[idx].direction > 0)
   {
      double potentialSL = bid - trailDist;
      if(potentialSL > g_positions[idx].currentSL + point)
         newSL = NormalizeDouble(potentialSL, digits);
   }
   else
   {
      double potentialSL = ask + trailDist;
      if(potentialSL < g_positions[idx].currentSL - point)
         newSL = NormalizeDouble(potentialSL, digits);
   }
   
   if(newSL != g_positions[idx].currentSL)
   {
      // DO NO HARM: Log all trade modifications for audit trail (Print below)
      if(g_trade.PositionModify(g_positions[idx].ticket, newSL, 0))  // Logged via Print
      {
         Print("TRAIL_SL: ", g_positions[idx].symbol,
               " Ticket=", g_positions[idx].ticket,
               " OldSL=", g_positions[idx].currentSL,
               " NewSL=", newSL);
         g_positions[idx].currentSL = newSL;
      }
   }
}

//+------------------------------------------------------------------+
//| CALCULATE REWARD (Asymmetrical)                                   |
//+------------------------------------------------------------------+
double CalculateReward(double grossPnL, double friction, int durationMins)
{
   double netPnL = grossPnL - friction;
   double reward;
   
   if(netPnL >= 0)
      reward = netPnL;
   else
      reward = netPnL * g_rlParams.GetLossPenalty();  // RL-tunable asymmetry
   
   // Time decay (RL-tunable)
   reward -= (durationMins * g_rlParams.GetTimeDecay());
   
   return reward;
}

//+------------------------------------------------------------------+
//| CHECK AGENT SWAPS                                                 |
//+------------------------------------------------------------------+
void CheckAgentSwaps()
{
   if(g_sniper.ShouldSwap())
   {
      g_sniper.PerformSwap();
   }
   
   if(g_berserker.ShouldSwap())
   {
      g_berserker.PerformSwap();
   }
}

//+------------------------------------------------------------------+
//| UPDATE CAPITAL ALLOCATION                                         |
//+------------------------------------------------------------------+
void UpdateCapitalAllocation()
{
   double sniperPF = g_sniper.real.GetPF();
   double berserkerPF = g_berserker.real.GetPF();

   if(sniperPF < 0.1) sniperPF = 0.1;
   if(berserkerPF < 0.1) berserkerPF = 0.1;

   double total = sniperPF + berserkerPF;
   double sniperAlloc = SafeDivide(sniperPF, total, 0.5);

   // Apply limits
   sniperAlloc = MathMax(InpMinAllocation, MathMin(InpMaxAllocation, sniperAlloc));

   g_sniper.capitalAlloc = sniperAlloc;
   g_berserker.capitalAlloc = 1.0 - sniperAlloc;

   Print("Capital Allocation Updated - SNIPER: ",
         DoubleToString(sniperAlloc * 100, 1), "% | BERSERKER: ",
         DoubleToString((1.0 - sniperAlloc) * 100, 1), "%");
}

//+------------------------------------------------------------------+
//| UPDATE EDGE STATUS                                                |
//+------------------------------------------------------------------+
void UpdateEdgeStatus()
{
   // Sniper
   double sniperAvgWin = SafeDivide(g_sniper.shadow.totalUpside,
                                    (double)g_sniper.shadow.totalWins, 10.0);
   int sniperLosses = g_sniper.shadow.totalTrades - g_sniper.shadow.totalWins;
   double sniperAvgLoss = SafeDivide(g_sniper.shadow.totalDownside,
                                     (double)sniperLosses, 8.0);

   g_sniper.hasEdge = g_statGate.HasEdge(
      g_sniper.shadow.totalWins,
      g_sniper.shadow.totalTrades,
      sniperAvgWin, sniperAvgLoss, 2.0
   );
   g_sniper.pValue = g_statGate.CalculatePValue(
      g_sniper.shadow.totalWins, g_sniper.shadow.totalTrades
   );

   // Berserker
   double berserkerAvgWin = SafeDivide(g_berserker.shadow.totalUpside,
                                       (double)g_berserker.shadow.totalWins, 10.0);
   int berserkerLosses = g_berserker.shadow.totalTrades - g_berserker.shadow.totalWins;
   double berserkerAvgLoss = SafeDivide(g_berserker.shadow.totalDownside,
                                        (double)berserkerLosses, 8.0);

   g_berserker.hasEdge = g_statGate.HasEdge(
      g_berserker.shadow.totalWins,
      g_berserker.shadow.totalTrades,
      berserkerAvgWin, berserkerAvgLoss, 2.0
   );
   g_berserker.pValue = g_statGate.CalculatePValue(
      g_berserker.shadow.totalWins, g_berserker.shadow.totalTrades
   );
}

//+------------------------------------------------------------------+
//| UTILITY FUNCTIONS                                                 |
//+------------------------------------------------------------------+
int FindSymbolIndex(const string sym)
{
   int limit = MathMin(g_symbolCount, MAX_SYMBOLS);
   for(int i = 0; i < limit; i++)
      if(g_symbols[i].name == sym) return i;
   return -1;
}

int CountOpenPositions()
{
   int count = 0;
   int limit = MathMin(g_posCount, MAX_POSITIONS);
   for(int i = 0; i < limit; i++)
      if(g_positions[i].active) count++;
   return count;
}

int CountRealPositions()
{
   int count = 0;
   int limit = MathMin(g_posCount, MAX_POSITIONS);
   for(int i = 0; i < limit; i++)
      if(g_positions[i].active && !g_positions[i].isShadow) count++;
   return count;
}

int CountShadowPositions()
{
   int count = 0;
   int limit = MathMin(g_posCount, MAX_POSITIONS);
   for(int i = 0; i < limit; i++)
      if(g_positions[i].active && g_positions[i].isShadow) count++;
   return count;
}

bool HasPositionOnSymbol(const string sym)
{
   int limit = MathMin(g_posCount, MAX_POSITIONS);
   for(int i = 0; i < limit; i++)
      if(g_positions[i].active && g_positions[i].symbol == sym) return true;
   return false;
}

//+------------------------------------------------------------------+
//| CHART EVENT - Delegate to VT_HUD.mqh handler                      |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   HandleHUDChartEvent(id, lparam, dparam, sparam);
}

//+------------------------------------------------------------------+
//| END OF FILE - VelocityTrader v7.1 Duel Architecture               |
//+------------------------------------------------------------------+
