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
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\DealInfo.mqh>

// ═══════════════════════════════════════════════════════════════════
// MODULAR INCLUDES - VelocityTrader v7.1 Component Library
// ═══════════════════════════════════════════════════════════════════
// Note: VT_Globals.mqh includes all other headers in correct order:
//   - VT_Definitions.mqh (constants, enums, colors)
//   - VT_RLParameters.mqh (RL tunable parameters)
//   - VT_Structures.mqh (core data structures)
//   - VT_Predictor.mqh (probability predictor, statistical gate)
//   - VT_CircuitBreaker.mqh (risk management state machine)
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

#if 0  // BEGIN LEGACY INLINE DEFINITIONS (disabled - now in headers)
//+------------------------------------------------------------------+
//| CONSTANTS                                                         |
//+------------------------------------------------------------------+
#define MAX_SYMBOLS           64
#define MAX_POSITIONS         20
#define ROLLING_WINDOW        20
#define PERSISTENCE_MAGIC     0x56454C37   // "VEL7"

//+------------------------------------------------------------------+
//| RL PARAMETERS - All normalized to [0,1] for RL adjustment         |
//|                                                                    |
//| Naming convention:                                                 |
//| - n_xxx = normalized value [0,1]                                  |
//| - GetXxx() = converts to actual value                             |
//|                                                                    |
//| The RL system can adjust these parameters. Normalization makes    |
//| it easier for the RL to explore the parameter space uniformly.    |
//+------------------------------------------------------------------+
struct RLParameters
{
   // Reward Shaping [0-1]
   double n_lossPenalty;      // 0=1x, 0.5=2.5x, 1=5x penalty
   double n_timeDecay;        // 0=0, 0.5=0.01/min, 1=0.05/min
   double n_surpriseBoost;    // 0=1x, 0.5=1.5x, 1=2x max boost
   
   // Position Management [0-1]
   double n_trailATR;         // 0=0.5x, 0.5=1.5x, 1=3x ATR trail
   double n_slATR;            // 0=0.5x, 0.5=2x, 1=4x ATR stop
   double n_tpATR;            // 0=0.5x, 0.5=1.5x, 1=3x ATR target
   
   // Signal Thresholds [0-1]
   double n_trendMult;        // 0=0.5x, 0.5=0.8x, 1=1x threshold
   double n_learnMult;        // 0=0.3x, 0.5=0.5x, 1=0.8x during learning
   double n_momentumMult;     // 0=0.3x, 0.5=0.5x, 1=0.8x for default
   
   // Regime Thresholds [0-1]
   double n_zScoreExtreme;    // 0=1.0, 0.5=2.0, 1=3.0 sigma
   double n_meanRevThresh;    // 0=0.5, 0.5=1.0, 1=2.0 sigma for entry
   double n_velocityThresh;   // 0=0.2, 0.5=0.5, 1=1.0 velocity
   
   // Acceleration Detection [0-1]
   double n_decelMult;        // 0=0.5x, 0.5=0.8x, 1=1.0x (decel if below this)
   double n_accelSpikeMult;   // 0=1.2x, 0.5=1.5x, 1=2.0x (spike if above this)
   
   // Allocation [0-1]
   double n_baseAlloc;        // 0=0.2, 0.5=0.5, 1=0.8 capital alloc
   double n_edgeBoost;        // 0=1x, 0.5=1.25x, 1=1.5x when has edge
   
   // Q-Learning [0-1]
   double n_discountFactor;   // 0=0.8, 0.5=0.9, 1=0.99 gamma
   
   void Init()
   {
      // Initialize to sensible defaults (mid-range = 0.5)
      n_lossPenalty = 0.375;     // ~2.5x loss penalty
      n_timeDecay = 0.2;         // 0.01/min time decay
      n_surpriseBoost = 0.5;     // 1.5x max surprise boost
      
      n_trailATR = 0.4;          // ~1.3x ATR trail
      n_slATR = 0.5;             // 2x ATR stop
      n_tpATR = 0.33;            // ~1.5x ATR target
      
      n_trendMult = 0.6;         // 0.8x trend threshold
      n_learnMult = 0.5;         // 0.5x learning threshold
      n_momentumMult = 0.5;      // 0.5x momentum threshold
      
      n_zScoreExtreme = 0.5;     // 2.0 sigma extreme
      n_meanRevThresh = 0.5;     // 1.0 sigma mean rev
      n_velocityThresh = 0.375;  // 0.5 velocity
      
      n_decelMult = 0.6;         // 0.8x decel threshold
      n_accelSpikeMult = 0.375;  // 1.5x spike threshold
      
      n_baseAlloc = 0.5;         // 0.5 base allocation
      n_edgeBoost = 0.5;         // 1.25x edge boost
      
      n_discountFactor = 0.5;    // 0.9 gamma
   }
   
   // Conversion functions: [0,1] → actual value
   double GetLossPenalty()     { return 1.0 + n_lossPenalty * 4.0; }           // [1, 5]
   double GetTimeDecay()       { return n_timeDecay * 0.05; }                   // [0, 0.05]
   double GetSurpriseBoost()   { return 1.0 + n_surpriseBoost * 1.0; }         // [1, 2]
   
   double GetTrailATR()        { return 0.5 + n_trailATR * 2.5; }              // [0.5, 3]
   double GetSL_ATR()          { return 0.5 + n_slATR * 3.5; }                 // [0.5, 4]
   double GetTP_ATR()          { return 0.5 + n_tpATR * 2.5; }                 // [0.5, 3]
   
   double GetTrendMult()       { return 0.5 + n_trendMult * 0.5; }             // [0.5, 1]
   double GetLearnMult()       { return 0.3 + n_learnMult * 0.5; }             // [0.3, 0.8]
   double GetMomentumMult()    { return 0.3 + n_momentumMult * 0.5; }          // [0.3, 0.8]
   
   double GetZScoreExtreme()   { return 1.0 + n_zScoreExtreme * 2.0; }         // [1, 3]
   double GetMeanRevThresh()   { return 0.5 + n_meanRevThresh * 1.5; }         // [0.5, 2]
   double GetVelocityThresh()  { return 0.2 + n_velocityThresh * 0.8; }        // [0.2, 1]
   
   double GetDecelMult()       { return 0.5 + n_decelMult * 0.5; }             // [0.5, 1]
   double GetAccelSpikeMult()  { return 1.2 + n_accelSpikeMult * 0.8; }        // [1.2, 2]
   
   double GetBaseAlloc()       { return 0.2 + n_baseAlloc * 0.6; }             // [0.2, 0.8]
   double GetEdgeBoost()       { return 1.0 + n_edgeBoost * 0.5; }             // [1, 1.5]
   
   double GetDiscountFactor()  { return 0.8 + n_discountFactor * 0.19; }       // [0.8, 0.99]
   
   // Mutation for exploration - mutates ALL normalized parameters
   void Mutate(double rate = 0.1)
   {
      double step = 0.2;  // Max step size per mutation
      
      // Helper macro-like lambda would be nice but MQL5 doesn't support
      // So explicit for each param:
      if(MathRand() / 32767.0 < rate) n_lossPenalty = MathMax(0, MathMin(1, n_lossPenalty + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_timeDecay = MathMax(0, MathMin(1, n_timeDecay + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_surpriseBoost = MathMax(0, MathMin(1, n_surpriseBoost + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_trailATR = MathMax(0, MathMin(1, n_trailATR + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_slATR = MathMax(0, MathMin(1, n_slATR + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_tpATR = MathMax(0, MathMin(1, n_tpATR + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_trendMult = MathMax(0, MathMin(1, n_trendMult + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_learnMult = MathMax(0, MathMin(1, n_learnMult + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_momentumMult = MathMax(0, MathMin(1, n_momentumMult + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_zScoreExtreme = MathMax(0, MathMin(1, n_zScoreExtreme + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_meanRevThresh = MathMax(0, MathMin(1, n_meanRevThresh + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_velocityThresh = MathMax(0, MathMin(1, n_velocityThresh + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_decelMult = MathMax(0, MathMin(1, n_decelMult + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_accelSpikeMult = MathMax(0, MathMin(1, n_accelSpikeMult + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_baseAlloc = MathMax(0, MathMin(1, n_baseAlloc + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_edgeBoost = MathMax(0, MathMin(1, n_edgeBoost + (MathRand() / 32767.0 - 0.5) * step));
      if(MathRand() / 32767.0 < rate) n_discountFactor = MathMax(0, MathMin(1, n_discountFactor + (MathRand() / 32767.0 - 0.5) * step));
   }
   
   // Copy from another RLParameters
   void CopyFrom(const RLParameters &src)
   {
      n_lossPenalty = src.n_lossPenalty;
      n_timeDecay = src.n_timeDecay;
      n_surpriseBoost = src.n_surpriseBoost;
      n_trailATR = src.n_trailATR;
      n_slATR = src.n_slATR;
      n_tpATR = src.n_tpATR;
      n_trendMult = src.n_trendMult;
      n_learnMult = src.n_learnMult;
      n_momentumMult = src.n_momentumMult;
      n_zScoreExtreme = src.n_zScoreExtreme;
      n_meanRevThresh = src.n_meanRevThresh;
      n_velocityThresh = src.n_velocityThresh;
      n_decelMult = src.n_decelMult;
      n_accelSpikeMult = src.n_accelSpikeMult;
      n_baseAlloc = src.n_baseAlloc;
      n_edgeBoost = src.n_edgeBoost;
      n_discountFactor = src.n_discountFactor;
   }
};

// Global RL parameters (one per agent profile for evolution)
RLParameters g_rlParams;

//+------------------------------------------------------------------+
//| ENUMERATIONS                                                      |
//+------------------------------------------------------------------+
enum ENUM_REGIME
{
   REGIME_BREAKOUT,      // Steep ROC, explosive
   REGIME_TREND,         // Sustained ROC, persistent
   REGIME_MEANREV,       // High χ, oscillating
   REGIME_CRITICAL,      // No clear state
   REGIME_CALIBRATING    // Collecting data
};

enum ENUM_AGENT
{
   AGENT_SNIPER = 0,
   AGENT_BERSERKER = 1,
   AGENT_COUNT = 2
};

enum ENUM_TRADING_STATE
{
   STATE_LIVE,           // Full trading enabled
   STATE_HALTED,         // Just triggered, cooling down
   STATE_RETRAINING,     // Shadow only, rebuilding
   STATE_PENDING         // Ready, awaiting human approval
};

enum ENUM_ASSET_TYPE
{
   ASSET_FOREX,
   ASSET_METAL,
   ASSET_INDEX,
   ASSET_CRYPTO,
   ASSET_OTHER
};

//+------------------------------------------------------------------+
//| COLORS                                                            |
//+------------------------------------------------------------------+
#define CLR_HEADER       C'0,255,255'
#define CLR_POSITIVE     C'0,255,128'
#define CLR_NEGATIVE     C'255,80,80'
#define CLR_NEUTRAL      C'255,255,0'
#define CLR_MUTED        C'128,128,128'
#define CLR_SNIPER       C'100,180,255'
#define CLR_BERSERKER    C'255,100,180'
#define CLR_SHADOW       C'180,180,255'
#define CLR_BREAKOUT     C'255,200,0'
#define CLR_TREND        C'0,255,128'
#define CLR_MEANREV      C'255,128,0'
#define CLR_CRITICAL     C'128,128,128'
#define CLR_PANEL_BG     C'20,25,35'
#define CLR_BORDER       C'60,70,90'

//+------------------------------------------------------------------+
//| STRUCTURE: Welford Online Statistics                              |
//+------------------------------------------------------------------+
struct WelfordStats
{
   double mean;
   double m2;
   int    count;
   int    maxCount;
   
   void Init(int maxN = 500)
   {
      mean = 0;
      m2 = 0;
      count = 0;
      maxCount = maxN;
   }
   
   void Update(double value)
   {
      count++;
      if(count > maxCount)
      {
         // Decay old values
         double decay = 0.995;
         m2 *= decay;
         count = maxCount;
      }
      
      double delta = value - mean;
      mean += delta / count;
      double delta2 = value - mean;
      m2 += delta * delta2;
   }
   
   double GetVariance()
   {
      if(count < 2) return 1.0;
      return m2 / (count - 1);
   }
   
   double GetStdDev()
   {
      return MathSqrt(GetVariance());
   }
   
   double GetZScore(double value)
   {
      double std = GetStdDev();
      if(std < 0.0001) return 0;
      return (value - mean) / std;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Broker Specification                                   |
//+------------------------------------------------------------------+
struct BrokerSpec
{
   double point;
   double tickSize;
   double tickValue;
   int    digits;
   double bid;
   double ask;
   double spread;
   double volumeMin;
   double volumeMax;
   double volumeStep;
   double commission;
};

//+------------------------------------------------------------------+
//| STRUCTURE: Strategy Stats (per regime)                           |
//+------------------------------------------------------------------+
struct StrategyStats
{
   // Q-values
   double qBuy;
   double qSell;
   double qHold;
   
   // Cumulative Performance
   int    trades;
   int    wins;
   double pnl;
   double upside;
   double downside;
   
   // Session Performance
   int    sessTrades;
   int    sessWins;
   double sessPnL;
   double sessUpside;
   double sessDownside;
   
   // Adaptive learning rate (per regime)
   double learningRate;
   
   // Performance cache
   double cachedWR;
   double cachedPF;
   bool   cacheValid;
   
   void Init()
   {
      qBuy = 0; qSell = 0; qHold = 0;
      trades = 0; wins = 0; pnl = 0;
      upside = 0; downside = 0;
      learningRate = InpLearningRateInit;
      sessTrades = 0; sessWins = 0; sessPnL = 0;
      sessUpside = 0; sessDownside = 0;
      cachedWR = 0; cachedPF = 0; cacheValid = false;
   }
   
   void ResetSession()
   {
      sessTrades = 0; sessWins = 0; sessPnL = 0;
      sessUpside = 0; sessDownside = 0;
   }
   
   void InvalidateCache() { cacheValid = false; }
   
   double GetWinRate()
   {
      if(!cacheValid) UpdateCache();
      return cachedWR;
   }
   
   double GetPF()
   {
      if(!cacheValid) UpdateCache();
      return cachedPF;
   }
   
   double GetSessWinRate()
   {
      return (sessTrades > 0) ? ((double)sessWins / sessTrades) : 0;
   }
   
   double GetSessPF()
   {
      return (sessDownside > 0.01) ? (sessUpside / sessDownside) : 0;
   }
   
   void UpdateCache()
   {
      cachedWR = (trades > 0) ? ((double)wins / trades) : 0;
      cachedPF = (downside > 0.01) ? (upside / downside) : 0;
      cacheValid = true;
   }
   
   double GetOmega()
   {
      if(downside > 0.01) return upside / downside;
      if(upside > 0) return 5.0;
      return 1.0;
   }
   
   // Adaptive learning rate calculation
   double GetAdaptiveLR()
   {
      return MathMax(learningRate, InpLearningRateMin);
   }
   
   void DecayLearningRate()
   {
      learningRate *= InpLearningDecay;
      if(learningRate < InpLearningRateMin)
         learningRate = InpLearningRateMin;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Agent Strategy Profile                                 |
//+------------------------------------------------------------------+
struct AgentProfile
{
   StrategyStats regime[3];    // [BREAKOUT, TREND, MEANREV]
   
   // Cumulative Totals (cached for performance)
   int    totalTrades;
   int    totalWins;
   double totalPnL;
   double totalUpside;
   double totalDownside;
   
   // Session Totals
   int    sessTotalTrades;
   int    sessTotalWins;
   double sessTotalPnL;
   double sessTotalUpside;
   double sessTotalDownside;
   
   void Init()
   {
      for(int i = 0; i < 3; i++)
         regime[i].Init();
      totalTrades = 0;
      totalWins = 0;
      totalPnL = 0;
      totalUpside = 0;
      totalDownside = 0;
      sessTotalTrades = 0;
      sessTotalWins = 0;
      sessTotalPnL = 0;
      sessTotalUpside = 0;
      sessTotalDownside = 0;
   }
   
   void ResetSession()
   {
      for(int i = 0; i < 3; i++)
         regime[i].ResetSession();
      sessTotalTrades = 0;
      sessTotalWins = 0;
      sessTotalPnL = 0;
      sessTotalUpside = 0;
      sessTotalDownside = 0;
   }
   
   void RecalcTotals()
   {
      totalTrades = 0; totalWins = 0; totalPnL = 0;
      totalUpside = 0; totalDownside = 0;
      sessTotalTrades = 0; sessTotalWins = 0; sessTotalPnL = 0;
      sessTotalUpside = 0; sessTotalDownside = 0;
      
      for(int i = 0; i < 3; i++)
      {
         totalTrades += regime[i].trades;
         totalWins += regime[i].wins;
         totalPnL += regime[i].pnl;
         totalUpside += regime[i].upside;
         totalDownside += regime[i].downside;
         
         sessTotalTrades += regime[i].sessTrades;
         sessTotalWins += regime[i].sessWins;
         sessTotalPnL += regime[i].sessPnL;
         sessTotalUpside += regime[i].sessUpside;
         sessTotalDownside += regime[i].sessDownside;
      }
   }
   
   // Cumulative metrics
   double GetWinRate()
   {
      return (totalTrades > 0) ? ((double)totalWins / totalTrades) : 0;
   }
   
   double GetPF()
   {
      return (totalDownside > 0.01) ? (totalUpside / totalDownside) : 0;
   }
   
   // Session metrics
   double GetSessWinRate()
   {
      return (sessTotalTrades > 0) ? ((double)sessTotalWins / sessTotalTrades) : 0;
   }
   
   double GetSessPF()
   {
      return (sessTotalDownside > 0.01) ? (sessTotalUpside / sessTotalDownside) : 0;
   }
   
   void UpdateTrade(int regimeIdx, double netPnL, double reward, int action)
   {
      if(regimeIdx < 0 || regimeIdx > 2) return;
      
      // MQL5 GOTCHA: Cannot use pointers to struct members
      // Use direct array access instead of: StrategyStats *s = &regime[regimeIdx]
      
      // Adaptive Q-Learning update
      double alpha = regime[regimeIdx].GetAdaptiveLR();
      
      // Surprise-based learning rate boost (RL-tunable)
      double qCurrent = (action > 0) ? regime[regimeIdx].qBuy : 
                        (action < 0) ? regime[regimeIdx].qSell : regime[regimeIdx].qHold;
      double surprise = MathAbs(reward - qCurrent);
      double maxBoost = g_rlParams.GetSurpriseBoost();
      double surpriseBoost = MathMin(maxBoost, 1.0 + surprise * 0.1);
      alpha *= surpriseBoost;
      alpha = MathMin(alpha, InpLearningRateInit);
      
      if(action > 0)
         regime[regimeIdx].qBuy += alpha * (reward - regime[regimeIdx].qBuy);
      else if(action < 0)
         regime[regimeIdx].qSell += alpha * (reward - regime[regimeIdx].qSell);
      
      regime[regimeIdx].DecayLearningRate();
      
      // Cumulative Stats
      regime[regimeIdx].trades++;
      regime[regimeIdx].pnl += netPnL;
      
      // Session Stats
      regime[regimeIdx].sessTrades++;
      regime[regimeIdx].sessPnL += netPnL;
      
      if(netPnL > 0)
      {
         regime[regimeIdx].wins++;
         regime[regimeIdx].sessWins++;
         regime[regimeIdx].upside += netPnL;
         regime[regimeIdx].sessUpside += netPnL;
      }
      else
      {
         regime[regimeIdx].downside += MathAbs(netPnL);
         regime[regimeIdx].sessDownside += MathAbs(netPnL);
      }
      
      regime[regimeIdx].InvalidateCache();
      RecalcTotals();
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Trading Agent                                          |
//+------------------------------------------------------------------+
struct TradingAgent
{
   string         name;
   color          clr;
   double         signalThreshold;
   
   AgentProfile   real;        // Champion
   AgentProfile   shadow;      // Challenger
   
   // Edge tracking
   bool           hasEdge;
   double         pValue;
   
   // Allocation
   double         capitalAlloc;
   
   // Swap tracking
   int            swapCount;
   datetime       lastSwapTime;
   
   // Rolling performance (for circuit breaker)
   double         rollingPnL[ROLLING_WINDOW];
   int            rollingIdx;
   int            consLosses;
   
   void Init(string n, color c, double thresh)
   {
      name = n;
      clr = c;
      signalThreshold = thresh;
      
      real.Init();
      shadow.Init();
      
      hasEdge = false;
      pValue = 1.0;
      capitalAlloc = 0.5;
      swapCount = 0;
      lastSwapTime = 0;
      
      ArrayInitialize(rollingPnL, 0);
      rollingIdx = 0;
      consLosses = 0;
   }
   
   void RecordTrade(double pnl)
   {
      rollingPnL[rollingIdx] = pnl;
      rollingIdx = (rollingIdx + 1) % ROLLING_WINDOW;
      
      if(pnl < 0)
         consLosses++;
      else
         consLosses = 0;
   }
   
   double GetRollingWR()
   {
      int wins = 0, total = 0;
      for(int i = 0; i < ROLLING_WINDOW; i++)
      {
         if(rollingPnL[i] != 0)
         {
            total++;
            if(rollingPnL[i] > 0) wins++;
         }
      }
      return (total > 0) ? ((double)wins / total) : 0.5;
   }
   
   void ResetSession()
   {
      real.ResetSession();
      shadow.ResetSession();
   }
   
   bool ShouldSwap()
   {
      if(shadow.totalTrades < InpSwapMinTrades) return false;
      if(real.totalTrades < 10) return false;
      
      double shadowPF = shadow.GetPF();
      double realPF = real.GetPF();
      
      if(realPF < 0.01) realPF = 0.01;
      
      return (shadowPF > realPF * InpSwapThreshold);
   }
   
   void PerformSwap()
   {
      // Shadow becomes new Real
      // Create new Shadow as clone + mutations
      
      AgentProfile newReal = shadow;
      
      // Reset shadow with slight exploration
      shadow.Init();
      
      // Copy Q-values from new real as baseline
      for(int i = 0; i < 3; i++)
      {
         shadow.regime[i].qBuy = newReal.regime[i].qBuy;
         shadow.regime[i].qSell = newReal.regime[i].qSell;
         shadow.regime[i].qHold = newReal.regime[i].qHold;
      }
      
      real = newReal;
      swapCount++;
      lastSwapTime = TimeCurrent();
      
      Print("═══ AGENT SWAP: ", name, " ═══");
      Print("Shadow became Champion (Swap #", swapCount, ")");
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Probability Predictor                                  |
//+------------------------------------------------------------------+
struct ProbabilityPredictor
{
   // Win rates by zone
   double regimeWR[3];         // [BREAKOUT, TREND, MEANREV]
   double chiZoneWR[5];        // [<-2, -2:-1, -1:1, 1:2, >2]
   double accelZoneWR[5];      // Same zones
   int    regimeCounts[3];
   int    chiCounts[5];
   int    accelCounts[5];
   
   void Init()
   {
      for(int i = 0; i < 3; i++) { regimeWR[i] = 0.5; regimeCounts[i] = 0; }
      for(int i = 0; i < 5; i++) { chiZoneWR[i] = 0.5; chiCounts[i] = 0; }
      for(int i = 0; i < 5; i++) { accelZoneWR[i] = 0.5; accelCounts[i] = 0; }
   }
   
   int GetZone(double zScore)
   {
      if(zScore < -2.0) return 0;
      if(zScore < -1.0) return 1;
      if(zScore < 1.0) return 2;
      if(zScore < 2.0) return 3;
      return 4;
   }
   
   void Update(int regimeIdx, double chiZ, double accelZ, bool won)
   {
      double winVal = won ? 1.0 : 0.0;
      double alpha = 0.05;  // Learning rate for predictor
      
      // Update regime WR
      if(regimeIdx >= 0 && regimeIdx < 3)
      {
         regimeCounts[regimeIdx]++;
         regimeWR[regimeIdx] += alpha * (winVal - regimeWR[regimeIdx]);
      }
      
      // Update chi zone WR
      int chiZone = GetZone(chiZ);
      chiCounts[chiZone]++;
      chiZoneWR[chiZone] += alpha * (winVal - chiZoneWR[chiZone]);
      
      // Update accel zone WR
      int accelZone = GetZone(accelZ);
      accelCounts[accelZone]++;
      accelZoneWR[accelZone] += alpha * (winVal - accelZoneWR[accelZone]);
   }
   
   double Predict(int regimeIdx, double chiZ, double accelZ, double agentWR)
   {
      double pBase = 0.50;
      
      // Regime contribution
      double pRegime = (regimeIdx >= 0 && regimeIdx < 3) ? regimeWR[regimeIdx] : 0.5;
      
      // Zone contributions
      int chiZone = GetZone(chiZ);
      int accelZone = GetZone(accelZ);
      double pChi = chiZoneWR[chiZone];
      double pAccel = accelZoneWR[accelZone];
      
      // Agent's historical WR
      double pAgent = MathMax(0.3, MathMin(0.7, agentWR));
      
      // Weighted combination
      double pWin = (pRegime * 0.30) +
                    (pChi * 0.20) +
                    (pAccel * 0.25) +
                    (pAgent * 0.25);
      
      return MathMax(0.30, MathMin(0.70, pWin));
   }
   
   // Omega-based position sizing
   // Omega = Upside / Downside
   // Scale size based on how much Omega exceeds baseline
   double GetOmegaSize(double omega, double pWin)
   {
      // If Omega below baseline, reduce size
      if(omega < InpOmegaBaseline)
         return MathMax(0.3, omega / InpOmegaBaseline);
      
      // Scale up based on Omega excess, capped at max
      // Formula: 1.0 + (omega - baseline) * scaling_factor
      double excess = omega - InpOmegaBaseline;
      double scale = 1.0 + (excess * 0.3);  // 30% boost per 1.0 omega above baseline
      
      // Apply probability confidence
      scale *= (0.5 + pWin);  // Range: 0.8 to 1.2 based on pWin
      
      return MathMin(scale, InpOmegaMaxScale);
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Statistical Gate                                       |
//+------------------------------------------------------------------+
struct StatisticalGate
{
   // MQL5 GOTCHA: Structs must have at least one data member
   int _dummy;
   
   double NormalCDF(double z)
   {
      // Approximation of standard normal CDF
      double a1 = 0.254829592;
      double a2 = -0.284496736;
      double a3 = 1.421413741;
      double a4 = -1.453152027;
      double a5 = 1.061405429;
      double p = 0.3275911;
      
      int sign = (z < 0) ? -1 : 1;
      z = MathAbs(z) / MathSqrt(2.0);
      
      double t = 1.0 / (1.0 + p * z);
      double y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t * MathExp(-z*z);
      
      return 0.5 * (1.0 + sign * y);
   }
   
   double CalculatePValue(int wins, int total)
   {
      if(total < 10) return 1.0;
      
      double p = 0.5;
      double observed = (double)wins / total;
      double stdErr = MathSqrt(p * (1.0 - p) / total);
      if(stdErr < 0.0001) return 1.0;
      
      double zScore = (observed - p) / stdErr;
      
      return 1.0 - NormalCDF(zScore);
   }
   
   bool HasEdge(int wins, int total, double avgWin, double avgLoss, double avgFriction)
   {
      if(total < InpMinTradesForEdge) return false;
      
      // Win rate must beat friction-adjusted coin flip
      double frictionHurdle = (avgWin > 0.01) ? (avgFriction / avgWin) : 0;
      double minWR = InpMinWinRate + frictionHurdle;
      double actualWR = (double)wins / total;
      
      if(actualWR < minWR) return false;
      
      // Statistical significance
      double pVal = CalculatePValue(wins, total);
      if(pVal > InpMaxPValue) return false;
      
      return true;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Circuit Breaker                                        |
//+------------------------------------------------------------------+
struct CircuitBreaker
{
   ENUM_TRADING_STATE state;
   datetime           haltTime;
   string             haltReason;
   
   // Retrain tracking
   int                retrainTrades;
   int                retrainWins;
   double             retrainPnL;
   double             retrainUpside;
   double             retrainDownside;
   
   // Daily tracking
   double             dailyPnL;
   double             dailyStartEquity;
   datetime           dayStart;
   
   // Drawdown tracking
   double             peakEquity;
   double             currentDD;
   
   void Init()
   {
      state = STATE_LIVE;
      haltTime = 0;
      haltReason = "";
      
      retrainTrades = 0;
      retrainWins = 0;
      retrainPnL = 0;
      retrainUpside = 0;
      retrainDownside = 0;
      
      dailyPnL = 0;
      dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
      dayStart = GetDayStart(TimeCurrent());
      
      peakEquity = dailyStartEquity;
      currentDD = 0;
   }
   
   datetime GetDayStart(datetime t)
   {
      MqlDateTime dt;
      TimeToStruct(t, dt);
      dt.hour = 0; dt.min = 0; dt.sec = 0;
      return StructToTime(dt);
   }
   
   void UpdateDaily()
   {
      datetime today = GetDayStart(TimeCurrent());
      if(today != dayStart)
      {
         // New day - reset daily stats
         dayStart = today;
         dailyPnL = 0;
         dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
      }
      
      // Update drawdown
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      if(equity > peakEquity) peakEquity = equity;
      currentDD = (peakEquity > 0) ? ((peakEquity - equity) / peakEquity) : 0;
   }
   
   bool CheckTriggers(double rollingWR, int consLosses)
   {
      if(state != STATE_LIVE) return false;
      
      UpdateDaily();
      
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      double dailyLossPct = (dailyStartEquity > 0) ? 
                           (-dailyPnL / dailyStartEquity) : 0;
      
      // Check triggers
      if(dailyLossPct > InpMaxDailyLoss)
      {
         Halt(StringFormat("Daily loss %.1f%% > %.1f%%", 
              dailyLossPct * 100, InpMaxDailyLoss * 100));
         return true;
      }
      
      if(consLosses >= InpMaxConsLosses)
      {
         Halt(StringFormat("%d consecutive losses", consLosses));
         return true;
      }
      
      if(rollingWR < InpMinRollingWR)
      {
         Halt(StringFormat("Rolling WR %.1f%% < %.1f%%", 
              rollingWR * 100, InpMinRollingWR * 100));
         return true;
      }
      
      if(currentDD > InpMaxDrawdown)
      {
         Halt(StringFormat("Drawdown %.1f%% > %.1f%%", 
              currentDD * 100, InpMaxDrawdown * 100));
         return true;
      }
      
      return false;
   }
   
   void Halt(string reason)
   {
      state = STATE_HALTED;
      haltTime = TimeCurrent();
      haltReason = reason;
      
      // Reset retrain tracking
      retrainTrades = 0;
      retrainWins = 0;
      retrainPnL = 0;
      retrainUpside = 0;
      retrainDownside = 0;
      
      // Alert user
      Alert("⚠️ CIRCUIT BREAKER: ", reason);
      
      Print("══════════════════════════════════════════════════════");
      Print("   ⚠️ CIRCUIT BREAKER TRIGGERED");
      Print("   Reason: ", reason);
      Print("   Status: HALTED (cooldown ", InpCooldownMinutes, " min)");
      Print("   Action: Auto-retraining will begin after cooldown");
      Print("══════════════════════════════════════════════════════");
   }
   
   void Update()
   {
      if(state == STATE_HALTED)
      {
         // Cooldown period
         int elapsed = (int)(TimeCurrent() - haltTime) / 60;
         if(elapsed >= InpCooldownMinutes)
         {
            state = STATE_RETRAINING;
            Print("Cooldown complete. Entering RETRAIN mode (shadow only).");
         }
      }
      else if(state == STATE_RETRAINING)
      {
         // NOTE: This code was truncated in the original - fixed in VT_CircuitBreaker.mqh
      }
   }
};
#endif  // END LEGACY INLINE DEFINITIONS

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
   
   // Initialize trade object
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(30);
   g_trade.SetTypeFilling(ORDER_FILLING_IOC);
   
   // Initialize RL parameters (normalized 0-1)
   g_rlParams.Init();
   
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
   
   // Timer for updates
   EventSetTimer(1);
   
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
   for(int i = 0; i < g_symbolCount; i++)
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
   // Update circuit breaker state
   g_breaker.Update();
   
   // Check for agent swaps
   CheckAgentSwaps();
   
   // Update capital allocation periodically
   static int lastAllocUpdate = 0;
   int totalTrades = g_sniper.real.totalTrades + g_berserker.real.totalTrades;
   if(totalTrades - lastAllocUpdate >= InpAllocationPeriod)
   {
      UpdateCapitalAllocation();
      lastAllocUpdate = totalTrades;
   }
   
   // Update edge status
   UpdateEdgeStatus();
   
   // Save state periodically
   static datetime lastSave = 0;
   if(TimeCurrent() - lastSave > 300)  // Every 5 minutes
   {
      SaveState();
      lastSave = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| TICK FUNCTION - Performance Optimized                             |
//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastFullUpdate = 0;
   static datetime lastHUDUpdate = 0;
   static int tickCounter = 0;
   
   datetime now = TimeCurrent();
   tickCounter++;
   
   // Always update current chart symbol immediately
   int currentIdx = FindSymbolIndex(_Symbol);
   if(currentIdx >= 0 && g_symbols[currentIdx].initialized)
      UpdateSymbol(currentIdx);
   
   // Throttle full symbol updates (every 500ms or every 10 ticks)
   bool doFullUpdate = (now - lastFullUpdate >= 1) || (tickCounter % 10 == 0);
   
   if(doFullUpdate)
   {
      lastFullUpdate = now;
      
      // Update other symbols (skip current, already updated)
      for(int i = 0; i < g_symbolCount; i++)
      {
         if(i == currentIdx) continue;
         if(g_symbols[i].initialized && g_symbols[i].typeAllowed)
            UpdateSymbol(i);
      }
      
      // Update velocity ranking
      UpdateRanking();
   }
   
   // Always manage positions (critical path)
   ManagePositions();
   
   // Check for new signals (if allowed)
   if(g_breaker.CanTradeShadow())
   {
      ProcessSignals();
   }
   
   // Throttle HUD updates (every 250ms max)
   if(now - lastHUDUpdate >= 1 || tickCounter % 5 == 0)
   {
      lastHUDUpdate = now;
      DrawHUD();
   }
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
      
      g_symbols[idx].atrHandle = iATR(sym, InpTimeframe, 14);
      if(g_symbols[idx].atrHandle == INVALID_HANDLE)
      {
         Print("Warning: No ATR for ", sym);
      }
      
      g_symbols[idx].physics.Init(sym);
      g_symbols[idx].symc.Init();
      g_symbols[idx].initialized = true;
   }
   
   return (g_symbolCount > 0);
}

//+------------------------------------------------------------------+
//| GET BROKER SPECIFICATION                                          |
//+------------------------------------------------------------------+
bool GetBrokerSpec(string sym, BrokerSpec &spec)
{
   spec.point = SymbolInfoDouble(sym, SYMBOL_POINT);
   spec.tickSize = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE);
   spec.tickValue = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE);
   spec.digits = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
   spec.bid = SymbolInfoDouble(sym, SYMBOL_BID);
   spec.ask = SymbolInfoDouble(sym, SYMBOL_ASK);
   spec.spread = spec.ask - spec.bid;
   spec.volumeMin = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   spec.volumeMax = SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX);
   spec.volumeStep = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);
   
   // Estimate commission
   double contractSize = SymbolInfoDouble(sym, SYMBOL_TRADE_CONTRACT_SIZE);
   spec.commission = contractSize * 0.00001;  // Estimate
   
   return (spec.point > 0 && spec.bid > 0);
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
   if(!g_symbols[idx].initialized) return;
   
   // Refresh spec
   g_symbols[idx].spec.bid = SymbolInfoDouble(g_symbols[idx].name, SYMBOL_BID);
   g_symbols[idx].spec.ask = SymbolInfoDouble(g_symbols[idx].name, SYMBOL_ASK);
   g_symbols[idx].spec.spread = g_symbols[idx].spec.ask - g_symbols[idx].spec.bid;
   
   // Update physics
   g_symbols[idx].physics.Update();
   
   // Get flow estimate
   MqlTick tick;
   double flow = 1.0;
   if(SymbolInfoTick(g_symbols[idx].name, tick))
   {
      flow = (double)tick.volume_real;
      if(flow == 0) flow = (double)tick.volume;
   }
   flow = MathMax(flow, 1.0);
   
   // Update SymC
   g_symbols[idx].symc.Update(
      g_symbols[idx].physics.GetMass(),
      flow,
      g_symbols[idx].spec.bid,
      g_symbols[idx].physics
   );
   
   // Update ATR
   double atrBuf[];
   if(CopyBuffer(g_symbols[idx].atrHandle, 0, 0, 1, atrBuf) > 0)
   {
      g_symbols[idx].atr = atrBuf[0];
      if(g_symbols[idx].avgATR == 0)
         g_symbols[idx].avgATR = g_symbols[idx].atr;
      else
         g_symbols[idx].avgATR = (g_symbols[idx].avgATR * 0.98) + (g_symbols[idx].atr * 0.02);
   }
}

//+------------------------------------------------------------------+
//| UPDATE VELOCITY RANKING                                           |
//+------------------------------------------------------------------+
void UpdateRanking()
{
   g_rankCount = 0;
   
   for(int i = 0; i < g_symbolCount; i++)
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
   for(int i = 0; i < g_rankCount - 1; i++)
   {
      for(int j = i + 1; j < g_rankCount; j++)
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
      for(int i = 0; i < g_symbolCount; i++)
         if(g_symbols[i].initialized && !g_symbols[i].physics.IsReady()) notReady++;
      Print("DEBUG: g_rankCount=0, NotReady=", notReady, "/", g_symbolCount);
   }
   
   int cnt = MathMin(g_rankCount, InpTopSymbols);
   
   for(int i = 0; i < cnt && openPos < InpMaxPositions; i++)
   {
      int idx = g_ranking[i].symbolIdx;
      if(idx < 0 || idx >= g_symbolCount) continue;
      
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

   double entryPrice = (direction > 0) ?
                       g_symbols[symIdx].spec.ask :
                       g_symbols[symIdx].spec.bid;

   double slDistance = g_symbols[symIdx].atr * 2.0;
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
      g_positions[slot].ticket = g_trade.ResultDeal();
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
            " P(Win)=", DoubleToString(pWin * 100, 1), "%");
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
   
   double grossPnL = (diff / tickSize) * tickValue * g_positions[idx].lots;
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
   // Show Q-values after update
   int regIdx = g_positions[idx].regimeAtEntry;
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
   // Check if position still exists
   if(!PositionSelectByTicket(g_positions[idx].ticket))
   {
      // Position closed - find PnL from history
      if(HistorySelectByPosition(g_positions[idx].ticket))
      {
         double pnl = 0;
         int deals = HistoryDealsTotal();
         for(int d = 0; d < deals; d++)
         {
            ulong dealTicket = HistoryDealGetTicket(d);
            if(HistoryDealGetInteger(dealTicket, DEAL_POSITION_ID) == (long)g_positions[idx].ticket)
            {
               pnl += HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
               pnl += HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);
               pnl += HistoryDealGetDouble(dealTicket, DEAL_SWAP);
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
         if(symIdx >= 0)
         {
            g_symbols[symIdx].dailyPnL += pnl;
            if(pnl < 0) g_symbols[symIdx].consLosses++;
            else g_symbols[symIdx].consLosses = 0;
         }
         
         Print("REAL Close: ", agentName, " ", g_positions[idx].symbol,
               " PnL: ", DoubleToString(pnl, 2));
         
         g_positions[idx].active = false;
      }
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
      if(g_trade.PositionModify(g_positions[idx].ticket, newSL, 0))
         g_positions[idx].currentSL = newSL;
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
   double sniperAlloc = sniperPF / total;
   
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
   double sniperAvgWin = (g_sniper.shadow.totalWins > 0) ?
                         (g_sniper.shadow.totalUpside / g_sniper.shadow.totalWins) : 10;
   double sniperAvgLoss = (g_sniper.shadow.totalTrades - g_sniper.shadow.totalWins > 0) ?
                          (g_sniper.shadow.totalDownside / 
                           (g_sniper.shadow.totalTrades - g_sniper.shadow.totalWins)) : 8;
   
   g_sniper.hasEdge = g_statGate.HasEdge(
      g_sniper.shadow.totalWins,
      g_sniper.shadow.totalTrades,
      sniperAvgWin, sniperAvgLoss, 2.0
   );
   g_sniper.pValue = g_statGate.CalculatePValue(
      g_sniper.shadow.totalWins, g_sniper.shadow.totalTrades
   );
   
   // Berserker
   double berserkerAvgWin = (g_berserker.shadow.totalWins > 0) ?
                            (g_berserker.shadow.totalUpside / g_berserker.shadow.totalWins) : 10;
   double berserkerAvgLoss = (g_berserker.shadow.totalTrades - g_berserker.shadow.totalWins > 0) ?
                             (g_berserker.shadow.totalDownside / 
                              (g_berserker.shadow.totalTrades - g_berserker.shadow.totalWins)) : 8;
   
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
   for(int i = 0; i < g_symbolCount; i++)
      if(g_symbols[i].name == sym) return i;
   return -1;
}

int CountOpenPositions()
{
   int count = 0;
   for(int i = 0; i < g_posCount; i++)
      if(g_positions[i].active) count++;
   return count;
}

int CountRealPositions()
{
   int count = 0;
   for(int i = 0; i < g_posCount; i++)
      if(g_positions[i].active && !g_positions[i].isShadow) count++;
   return count;
}

int CountShadowPositions()
{
   int count = 0;
   for(int i = 0; i < g_posCount; i++)
      if(g_positions[i].active && g_positions[i].isShadow) count++;
   return count;
}

bool HasPositionOnSymbol(const string sym)
{
   for(int i = 0; i < g_posCount; i++)
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

// ═══════════════════════════════════════════════════════════════════
// LEGACY HUD & PERSISTENCE CODE (Now in header files - disabled)
// ═══════════════════════════════════════════════════════════════════
#if 0  // BEGIN LEGACY HUD/PERSISTENCE (disabled - now in VT_HUD.mqh & VT_Persistence.mqh)
//+------------------------------------------------------------------+
//| HUD FUNCTIONS                                                     |
//+------------------------------------------------------------------+
void HUD_Create(string name, int x, int y, string text, color clr, int size = 8)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
      ArrayResize(g_hudObjects, g_hudCount + 1);
      g_hudObjects[g_hudCount++] = name;
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetString(0, name, OBJPROP_FONT, "Consolas");
      ObjectSetInteger(0, name, OBJPROP_ZORDER, 10);
   }
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, size);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
}

void HUD_Rect(string name, int x, int y, int w, int h, color bg, color border)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
      ArrayResize(g_hudObjects, g_hudCount + 1);
      g_hudObjects[g_hudCount++] = name;
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_BACK, false);
      ObjectSetInteger(0, name, OBJPROP_ZORDER, 0);
   }
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, name, OBJPROP_YSIZE, h);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, border);
}

void DrawHUD()
{
   if(!InpShowHUD) return;
   
   // Track tab changes to clear old content
   static int lastTab = -1;
   
   // Initialize tab on first run
   static bool tabInit = false;
   if(!tabInit)
   {
      g_hudTab = InpDefaultTab;
      if(g_hudTab < 0 || g_hudTab >= TAB_COUNT) g_hudTab = 0;
      tabInit = true;
   }
   
   // Auto-rotate tabs
   if(InpAutoRotateTabs && TimeCurrent() - g_hudLastTabSwitch >= 5)
   {
      g_hudTab = (g_hudTab + 1) % TAB_COUNT;
      g_hudLastTabSwitch = TimeCurrent();
   }
   
   // Clear ALL HUD objects when tab changes
   if(lastTab != g_hudTab)
   {
      CleanupHUD();
      lastTab = g_hudTab;
   }
   
   // Update system status periodically
   static datetime lastStatusUpdate = 0;
   if(TimeCurrent() - lastStatusUpdate > 5)
   {
      g_status.Update();
      lastStatusUpdate = TimeCurrent();
   }
   
   int x = InpHUD_X;
   int yStart = InpHUD_Y;
   int y = yStart + 5;
   int h = 11;
   int sec = 3;
   
   // Wider panel to fit content
   int panelWidth = 480;
   int panelHeight = 420;
   
   // Draw background
   HUD_Rect("H_Bg", x, yStart, panelWidth, panelHeight, CLR_PANEL_BG, CLR_BORDER);
   
   // ═══════════════════════════════════════════════════════════════
   // HEADER (Always visible)
   // ═══════════════════════════════════════════════════════════════
   HUD_Create("H_Title", x+8, y, "══════════ VELOCITY v7.1 DUEL ══════════", CLR_HEADER, 9);
   y += 14;
   
   // Status traffic lights
   string brokerSt = g_status.brokerConnected ? "~" : "!";
   string netSt = g_status.networkOK ? "~" : "!";
   string rlSt = g_status.rlActive ? "~" : "o";
   string riskSt = g_status.riskOK ? "~" : "!";
   
   color brokerClr = g_status.brokerConnected ? CLR_POSITIVE : CLR_NEGATIVE;
   color netClr = g_status.networkOK ? CLR_POSITIVE : CLR_NEGATIVE;
   color rlClr = g_status.rlActive ? CLR_POSITIVE : CLR_NEUTRAL;
   color riskClr = g_status.riskOK ? CLR_POSITIVE : CLR_NEGATIVE;
   
   bool isBacktest = (MQLInfoInteger(MQL_TESTER) != 0);
   string modeStr = isBacktest ? "BACKTEST" : "LIVE";
   
   HUD_Create("H_Mode", x+8, y, StringFormat("[%s] BRK:%s NET:%s RL:%s RISK:%s",
      modeStr, brokerSt, netSt, rlSt, riskSt), 
      (g_status.riskOK && g_status.networkOK) ? CLR_POSITIVE : CLR_NEGATIVE);
   y += h;
   
   // Quick account summary
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double floatingPnL = equity - balance;
   int realPos = CountRealPositions();
   int shadowPos = CountShadowPositions();
   
   color eqClr = (floatingPnL >= 0) ? CLR_POSITIVE : CLR_NEGATIVE;
   HUD_Create("H_Acc", x+8, y, StringFormat("Eq:$%.0f Bal:$%.0f Float:%+.0f | R:%d S:%d",
      equity, balance, floatingPnL, realPos, shadowPos), eqClr);
   y += h + 2;
   
   // ═══════════════════════════════════════════════════════════════
   // TAB BAR
   // ═══════════════════════════════════════════════════════════════
   string tabs[] = {"DASH", "PERF", "RL", "PROB", "RISK", "INST"};
   int tabWidth = 75;
   
   for(int i = 0; i < TAB_COUNT; i++)
   {
      string tabName = "H_Tab" + IntegerToString(i);
      color tabClr = (i == g_hudTab) ? CLR_HEADER : CLR_MUTED;
      string tabText = (i == g_hudTab) ? "[" + tabs[i] + "]" : " " + tabs[i] + " ";
      HUD_Create(tabName, x + 8 + (i * tabWidth), y, tabText, tabClr);
   }
   y += h + sec;
   
   // Separator
   HUD_Create("H_Sep", x+8, y, "-----------------------------------------------", CLR_BORDER);
   y += h;
   
   // ═══════════════════════════════════════════════════════════════
   // TAB CONTENT
   // ═══════════════════════════════════════════════════════════════
   switch(g_hudTab)
   {
      case TAB_OVERVIEW:    DrawTab_Dashboard(x, y, h, sec); break;
      case TAB_PERFORMANCE: DrawTab_Performance(x, y, h, sec); break;
      case TAB_TRAINING:    DrawTab_Training(x, y, h, sec); break;
      case TAB_PROBABILITY: DrawTab_Probability(x, y, h, sec); break;
      case TAB_RISK:        DrawTab_Risk(x, y, h, sec); break;
      case TAB_SIGNALS:     DrawTab_Instruments(x, y, h, sec); break;
   }
   
   // Navigation hint at bottom
   HUD_Create("H_Hint", x+8, panelHeight + yStart - 14, 
      "Navigate: 1-6 | TAB | Arrows", CLR_MUTED);
   
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| TAB: DASHBOARD (Management Overview)                              |
//+------------------------------------------------------------------+
void DrawTab_Dashboard(int x, int &y, int h, int sec)
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   
   // P&L Summary
   HUD_Create("H_D1", x+8, y, "--- P&L SUMMARY ---", CLR_HEADER);
   y += h;
   
   color dayClr = (g_dayStats.pnl >= 0) ? CLR_POSITIVE : CLR_NEGATIVE;
   color weekClr = (g_weekStats.pnl >= 0) ? CLR_POSITIVE : CLR_NEGATIVE;
   color monthClr = (g_monthStats.pnl >= 0) ? CLR_POSITIVE : CLR_NEGATIVE;
   color totalClr = (g_totalStats.pnl >= 0) ? CLR_POSITIVE : CLR_NEGATIVE;
   
   HUD_Create("H_D2", x+8, y, StringFormat("Today: %+.0f (%d trd, %.0f%% WR)",
      g_dayStats.pnl, g_dayStats.trades, g_dayStats.GetWR()), dayClr);
   y += h;
   HUD_Create("H_D3", x+8, y, StringFormat("Week:  %+.0f (%d trd, %.0f%% WR)",
      g_weekStats.pnl, g_weekStats.trades, g_weekStats.GetWR()), weekClr);
   y += h;
   HUD_Create("H_D4", x+8, y, StringFormat("Month: %+.0f (%d trd, %.0f%% WR)",
      g_monthStats.pnl, g_monthStats.trades, g_monthStats.GetWR()), monthClr);
   y += h;
   HUD_Create("H_D5", x+8, y, StringFormat("Total: %+.0f (%d trd, %.0f%% WR)",
      g_totalStats.pnl, g_totalStats.trades, g_totalStats.GetWR()), totalClr);
   y += h + sec;
   
   // Agent Summary with traffic lights
   HUD_Create("H_D6", x+8, y, "--- AGENTS ---", CLR_HEADER);
   y += h;
   
   string sniEdge = g_sniper.hasEdge ? "[OK]" : "[--]";
   color sniClr = g_sniper.hasEdge ? CLR_POSITIVE : CLR_MUTED;
   double sniAlloc = g_sniper.capitalAlloc * 100;
   
   HUD_Create("H_D7", x+8, y, StringFormat("SNIPER   %s Alloc:%.0f%% PF:%.2f WR:%.0f%% $%+.0f",
      sniEdge, sniAlloc, g_sniper.shadow.GetPF(), 
      g_sniper.shadow.GetWinRate()*100, g_sniper.shadow.totalPnL), sniClr);
   y += h;
   
   string berEdge = g_berserker.hasEdge ? "[OK]" : "[--]";
   color berClr = g_berserker.hasEdge ? CLR_POSITIVE : CLR_MUTED;
   double berAlloc = g_berserker.capitalAlloc * 100;
   
   HUD_Create("H_D8", x+8, y, StringFormat("BERSERKER %s Alloc:%.0f%% PF:%.2f WR:%.0f%% $%+.0f",
      berEdge, berAlloc, g_berserker.shadow.GetPF(),
      g_berserker.shadow.GetWinRate()*100, g_berserker.shadow.totalPnL), berClr);
   y += h + sec;
   
   // System State
   HUD_Create("H_D9", x+8, y, "--- SYSTEM STATE ---", CLR_HEADER);
   y += h;
   
   string stateStr = g_breaker.GetStateString();
   color stateClr = (g_breaker.state == STATE_LIVE) ? CLR_POSITIVE :
                    (g_breaker.state == STATE_PENDING) ? CLR_NEUTRAL : CLR_NEGATIVE;
   HUD_Create("H_D10", x+8, y, StringFormat("Circuit Breaker: %s", stateStr), stateClr);
   y += h;
   
   // Open positions status - find oldest
   int oldestAge = 0;
   int openCount = 0;
   for(int i = 0; i < g_posCount; i++)
   {
      if(g_positions[i].active && g_positions[i].isShadow)
      {
         openCount++;
         int age = (int)((TimeCurrent() - g_positions[i].openTime) / 60);
         if(age > oldestAge) oldestAge = age;
      }
   }
   
   int closedTrades = g_sniper.shadow.totalTrades + g_berserker.shadow.totalTrades;
   int timeToClose = MathMax(0, InpShadowTimeoutMin - oldestAge);
   
   color learnClr = (closedTrades > 0) ? CLR_POSITIVE : CLR_NEUTRAL;
   HUD_Create("H_D11", x+8, y, StringFormat("Open:%d Closed:%d | Oldest:%dmin (close in %dm)",
      openCount, closedTrades, oldestAge, timeToClose), learnClr);
   y += h;
   
   // Regime distribution
   int nBrk=0, nTrd=0, nMR=0;
   for(int i = 0; i < g_symbolCount; i++)
   {
      if(!g_symbols[i].initialized) continue;
      ENUM_REGIME reg = g_symbols[i].symc.GetRegime();
      if(reg == REGIME_BREAKOUT) nBrk++;
      else if(reg == REGIME_TREND) nTrd++;
      else if(reg == REGIME_MEANREV) nMR++;
   }
   
   HUD_Create("H_D12", x+8, y, StringFormat("Regimes: BRK:%d TRD:%d MR:%d | Ranked:%d/%d",
      nBrk, nTrd, nMR, g_rankCount, g_symbolCount), CLR_MUTED);
}

//+------------------------------------------------------------------+
//| TAB: PERFORMANCE (Detailed Stats)                                 |
//+------------------------------------------------------------------+
void DrawTab_Performance(int x, int &y, int h, int sec)
{
   HUD_Create("H_P1", x+8, y, "--- SESSION / CUMULATIVE ---", CLR_HEADER);
   y += h;
   
   HUD_Create("H_P2", x+8, y, "         Sess  WR%  PnL   Omega | Cum   WR%    PnL    PF", CLR_MUTED);
   y += h;
   
   // SNIPER Shadow
   double sniSO = (g_sniper.shadow.sessTotalDownside > 0.01) ?
      g_sniper.shadow.sessTotalUpside / g_sniper.shadow.sessTotalDownside : 1.0;
   color sniSC = (g_sniper.shadow.sessTotalPnL >= 0) ? CLR_SHADOW : clrDarkGray;
   HUD_Create("H_PSS", x+8, y, StringFormat("SNI.S   %4d %4.0f%% %+5.0f  %4.1f |%4d %4.0f%% %+6.0f %5.2f",
      g_sniper.shadow.sessTotalTrades, g_sniper.shadow.GetSessWinRate()*100,
      g_sniper.shadow.sessTotalPnL, sniSO,
      g_sniper.shadow.totalTrades, g_sniper.shadow.GetWinRate()*100,
      g_sniper.shadow.totalPnL, g_sniper.shadow.GetPF()), sniSC);
   y += h;
   
   // SNIPER Real
   double sniRO = (g_sniper.real.sessTotalDownside > 0.01) ?
      g_sniper.real.sessTotalUpside / g_sniper.real.sessTotalDownside : 1.0;
   color sniRC = (g_sniper.real.totalPnL >= 0) ? CLR_SNIPER : CLR_NEGATIVE;
   HUD_Create("H_PSR", x+8, y, StringFormat("SNI.R   %4d %4.0f%% %+5.0f  %4.1f |%4d %4.0f%% %+6.0f %5.2f",
      g_sniper.real.sessTotalTrades, g_sniper.real.GetSessWinRate()*100,
      g_sniper.real.sessTotalPnL, sniRO,
      g_sniper.real.totalTrades, g_sniper.real.GetWinRate()*100,
      g_sniper.real.totalPnL, g_sniper.real.GetPF()), sniRC);
   y += h;
   
   // BERSERKER Shadow
   double berSO = (g_berserker.shadow.sessTotalDownside > 0.01) ?
      g_berserker.shadow.sessTotalUpside / g_berserker.shadow.sessTotalDownside : 1.0;
   color berSC = (g_berserker.shadow.sessTotalPnL >= 0) ? CLR_SHADOW : clrDarkGray;
   HUD_Create("H_PBS", x+8, y, StringFormat("BER.S   %4d %4.0f%% %+5.0f  %4.1f |%4d %4.0f%% %+6.0f %5.2f",
      g_berserker.shadow.sessTotalTrades, g_berserker.shadow.GetSessWinRate()*100,
      g_berserker.shadow.sessTotalPnL, berSO,
      g_berserker.shadow.totalTrades, g_berserker.shadow.GetWinRate()*100,
      g_berserker.shadow.totalPnL, g_berserker.shadow.GetPF()), berSC);
   y += h;
   
   // BERSERKER Real
   double berRO = (g_berserker.real.sessTotalDownside > 0.01) ?
      g_berserker.real.sessTotalUpside / g_berserker.real.sessTotalDownside : 1.0;
   color berRC = (g_berserker.real.totalPnL >= 0) ? CLR_BERSERKER : CLR_NEGATIVE;
   HUD_Create("H_PBR", x+8, y, StringFormat("BER.R   %4d %4.0f%% %+5.0f  %4.1f |%4d %4.0f%% %+6.0f %5.2f",
      g_berserker.real.sessTotalTrades, g_berserker.real.GetSessWinRate()*100,
      g_berserker.real.sessTotalPnL, berRO,
      g_berserker.real.totalTrades, g_berserker.real.GetWinRate()*100,
      g_berserker.real.totalPnL, g_berserker.real.GetPF()), berRC);
   y += h + sec;
   
   // MAE/MFE Analysis
   HUD_Create("H_P3", x+8, y, "--- MAE/MFE (Trade Quality) ---", CLR_HEADER);
   y += h;
   
   HUD_Create("H_P4", x+8, y, "         AvgMAE  MaxMAE  AvgMFE  MaxMFE   ETD", CLR_MUTED);
   y += h;
   
   double sniAvgPnL = (g_sniper.shadow.totalTrades > 0) ?
      g_sniper.shadow.totalPnL / g_sniper.shadow.totalTrades : 0;
   double sniETD = g_sniperExcursion.GetAvgETD(sniAvgPnL);
   
   HUD_Create("H_P5", x+8, y, StringFormat("SNIPER  %6.0f  %6.0f  %6.0f  %6.0f  %5.0f",
      g_sniperExcursion.avgMAE, g_sniperExcursion.maxMAE,
      g_sniperExcursion.avgMFE, g_sniperExcursion.maxMFE, sniETD), CLR_SNIPER);
   y += h;
   
   double berAvgPnL = (g_berserker.shadow.totalTrades > 0) ?
      g_berserker.shadow.totalPnL / g_berserker.shadow.totalTrades : 0;
   double berETD = g_berserkerExcursion.GetAvgETD(berAvgPnL);
   
   HUD_Create("H_P6", x+8, y, StringFormat("BERSER  %6.0f  %6.0f  %6.0f  %6.0f  %5.0f",
      g_berserkerExcursion.avgMAE, g_berserkerExcursion.maxMAE,
      g_berserkerExcursion.avgMFE, g_berserkerExcursion.maxMFE, berETD), CLR_BERSERKER);
   y += h + sec;
   
   // Consecutive stats
   HUD_Create("H_P7", x+8, y, "--- STREAKS ---", CLR_HEADER);
   y += h;
   
   HUD_Create("H_P8", x+8, y, StringFormat("ConsLoss: SNI:%d BER:%d | Rolling20WR: SNI:%.0f%% BER:%.0f%%",
      g_sniper.consLosses, g_berserker.consLosses,
      g_sniper.GetRollingWR()*100, g_berserker.GetRollingWR()*100), CLR_MUTED);
}

//+------------------------------------------------------------------+
//| TAB: RL TRAINING                                                  |
//+------------------------------------------------------------------+
void DrawTab_Training(int x, int &y, int h, int sec)
{
   int totalClosed = g_sniper.shadow.totalTrades + g_berserker.shadow.totalTrades;
   
   // Show waiting message if no trades closed yet
   if(totalClosed == 0)
   {
      HUD_Create("H_T0", x+8, y, "*** WAITING FOR TRADES TO CLOSE ***", CLR_NEUTRAL);
      y += h;
      HUD_Create("H_T0a", x+8, y, StringFormat("Shadow timeout: %d minutes", InpShadowTimeoutMin), CLR_MUTED);
      y += h;
      HUD_Create("H_T0b", x+8, y, "Q-values update when trades complete", CLR_MUTED);
      y += h + sec;
   }
   
   HUD_Create("H_T1", x+8, y, "--- Q-VALUES (Buy/Sell) ---", CLR_HEADER);
   y += h;
   
   HUD_Create("H_T2", x+8, y, "            BREAKOUT      TREND       MEANREV", CLR_MUTED);
   y += h;
   
   HUD_Create("H_T3", x+8, y, StringFormat("SNIPER    %+5.1f/%+5.1f  %+5.1f/%+5.1f  %+5.1f/%+5.1f",
      g_sniper.shadow.regime[0].qBuy, g_sniper.shadow.regime[0].qSell,
      g_sniper.shadow.regime[1].qBuy, g_sniper.shadow.regime[1].qSell,
      g_sniper.shadow.regime[2].qBuy, g_sniper.shadow.regime[2].qSell), CLR_SNIPER);
   y += h;
   
   HUD_Create("H_T4", x+8, y, StringFormat("BERSERKER %+5.1f/%+5.1f  %+5.1f/%+5.1f  %+5.1f/%+5.1f",
      g_berserker.shadow.regime[0].qBuy, g_berserker.shadow.regime[0].qSell,
      g_berserker.shadow.regime[1].qBuy, g_berserker.shadow.regime[1].qSell,
      g_berserker.shadow.regime[2].qBuy, g_berserker.shadow.regime[2].qSell), CLR_BERSERKER);
   y += h + sec;
   
   // Learning rates
   HUD_Create("H_T5", x+8, y, "--- LEARNING RATES ---", CLR_HEADER);
   y += h;
   
   double sniAvg = (g_sniper.shadow.regime[0].learningRate + 
                    g_sniper.shadow.regime[1].learningRate + 
                    g_sniper.shadow.regime[2].learningRate) / 3.0;
   HUD_Create("H_T6", x+8, y, StringFormat("SNIPER    %.4f    %.4f    %.4f   Avg:%.4f",
      g_sniper.shadow.regime[0].learningRate,
      g_sniper.shadow.regime[1].learningRate,
      g_sniper.shadow.regime[2].learningRate, sniAvg), CLR_SNIPER);
   y += h;
   
   double berAvg = (g_berserker.shadow.regime[0].learningRate + 
                    g_berserker.shadow.regime[1].learningRate + 
                    g_berserker.shadow.regime[2].learningRate) / 3.0;
   HUD_Create("H_T7", x+8, y, StringFormat("BERSERKER %.4f    %.4f    %.4f   Avg:%.4f",
      g_berserker.shadow.regime[0].learningRate,
      g_berserker.shadow.regime[1].learningRate,
      g_berserker.shadow.regime[2].learningRate, berAvg), CLR_BERSERKER);
   y += h + sec;
   
   // Convergence
   double convSni = (1.0 - sniAvg / InpLearningRateInit) * 100;
   double convBer = (1.0 - berAvg / InpLearningRateInit) * 100;
   string status = (convSni > 80 && convBer > 80) ? "CONVERGED" :
                   (convSni > 50 || convBer > 50) ? "LEARNING" : "EXPLORING";
   color statClr = (convSni > 80 && convBer > 80) ? CLR_POSITIVE :
                   (convSni > 50 || convBer > 50) ? CLR_NEUTRAL : CLR_SHADOW;
   
   HUD_Create("H_T8", x+8, y, StringFormat("Convergence: SNI:%.0f%% BER:%.0f%% [%s]",
      convSni, convBer, status), statClr);
   y += h + sec;
   
   // Reward shaping params - now RL-tunable
   HUD_Create("H_T9", x+8, y, "--- RL PARAMETERS (0-1 normalized) ---", CLR_HEADER);
   y += h;
   HUD_Create("H_T10", x+8, y, StringFormat("LossPen:%.2f(x%.1f) TimeDecay:%.2f(%.3f/m) Surprise:%.2f(x%.1f)",
      g_rlParams.n_lossPenalty, g_rlParams.GetLossPenalty(),
      g_rlParams.n_timeDecay, g_rlParams.GetTimeDecay(),
      g_rlParams.n_surpriseBoost, g_rlParams.GetSurpriseBoost()), CLR_MUTED);
   y += h;
   HUD_Create("H_T11", x+8, y, StringFormat("Trail:%.2f(%.1fATR) SL:%.2f(%.1fATR) TP:%.2f(%.1fATR)",
      g_rlParams.n_trailATR, g_rlParams.GetTrailATR(),
      g_rlParams.n_slATR, g_rlParams.GetSL_ATR(),
      g_rlParams.n_tpATR, g_rlParams.GetTP_ATR()), CLR_MUTED);
   y += h;
   HUD_Create("H_T12", x+8, y, StringFormat("Vel:%.2f(%.2f) MeanRev:%.2f(%.1fs) ZExt:%.2f(%.1fs)",
      g_rlParams.n_velocityThresh, g_rlParams.GetVelocityThresh(),
      g_rlParams.n_meanRevThresh, g_rlParams.GetMeanRevThresh(),
      g_rlParams.n_zScoreExtreme, g_rlParams.GetZScoreExtreme()), CLR_MUTED);
}

//+------------------------------------------------------------------+
//| TAB: PROBABILITY                                                  |
//+------------------------------------------------------------------+
void DrawTab_Probability(int x, int &y, int h, int sec)
{
   HUD_Create("H_Pb1", x+8, y, "--- REGIME P(WIN) ---", CLR_HEADER);
   y += h;
   
   color brk = (g_predictor.regimeWR[0] >= 0.55) ? CLR_POSITIVE : CLR_MUTED;
   color trd = (g_predictor.regimeWR[1] >= 0.55) ? CLR_POSITIVE : CLR_MUTED;
   color mr = (g_predictor.regimeWR[2] >= 0.55) ? CLR_POSITIVE : CLR_MUTED;
   
   HUD_Create("H_Pb2", x+8, y, StringFormat("BREAKOUT:  %.0f%% (n=%d)",
      g_predictor.regimeWR[0]*100, g_predictor.regimeCounts[0]), brk);
   y += h;
   HUD_Create("H_Pb3", x+8, y, StringFormat("TREND:     %.0f%% (n=%d)",
      g_predictor.regimeWR[1]*100, g_predictor.regimeCounts[1]), trd);
   y += h;
   HUD_Create("H_Pb4", x+8, y, StringFormat("MEANREV:   %.0f%% (n=%d)",
      g_predictor.regimeWR[2]*100, g_predictor.regimeCounts[2]), mr);
   y += h + sec;
   
   HUD_Create("H_Pb5", x+8, y, "--- CHI ZONES P(WIN) ---", CLR_HEADER);
   y += h;
   HUD_Create("H_Pb6", x+8, y, "   <-2s     -1s      0      +1s    >+2s", CLR_MUTED);
   y += h;
   HUD_Create("H_Pb7", x+8, y, StringFormat("   %.0f%%     %.0f%%    %.0f%%    %.0f%%    %.0f%%",
      g_predictor.chiZoneWR[0]*100, g_predictor.chiZoneWR[1]*100,
      g_predictor.chiZoneWR[2]*100, g_predictor.chiZoneWR[3]*100,
      g_predictor.chiZoneWR[4]*100), CLR_NEUTRAL);
   y += h + sec;
   
   HUD_Create("H_Pb8", x+8, y, "--- ACCEL ZONES P(WIN) ---", CLR_HEADER);
   y += h;
   HUD_Create("H_Pb9", x+8, y, "   <-2s     -1s      0      +1s    >+2s", CLR_MUTED);
   y += h;
   HUD_Create("H_Pb10", x+8, y, StringFormat("   %.0f%%     %.0f%%    %.0f%%    %.0f%%    %.0f%%",
      g_predictor.accelZoneWR[0]*100, g_predictor.accelZoneWR[1]*100,
      g_predictor.accelZoneWR[2]*100, g_predictor.accelZoneWR[3]*100,
      g_predictor.accelZoneWR[4]*100), CLR_NEUTRAL);
   y += h + sec;
   
   HUD_Create("H_Pb11", x+8, y, StringFormat("Min P(Win) Gate: %.0f%% (Real trades only)",
      InpMinProbability * 100), CLR_MUTED);
}

//+------------------------------------------------------------------+
//| TAB: RISK MANAGEMENT                                              |
//+------------------------------------------------------------------+
void DrawTab_Risk(int x, int &y, int h, int sec)
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   
   HUD_Create("H_R1", x+8, y, "--- DRAWDOWN ---", CLR_HEADER);
   y += h;
   
   double dd = 0;
   if(g_breaker.peakEquity > 0)
      dd = (g_breaker.peakEquity - equity) / g_breaker.peakEquity * 100;
   
   color ddClr = (dd < InpMaxDrawdown * 50) ? CLR_POSITIVE :
                 (dd < InpMaxDrawdown * 100) ? CLR_NEUTRAL : CLR_NEGATIVE;
   
   HUD_Create("H_R2", x+8, y, StringFormat("Current: %.2f%% / %.0f%% max | Peak: $%.0f",
      dd, InpMaxDrawdown * 100, g_breaker.peakEquity), ddClr);
   y += h + sec;
   
   HUD_Create("H_R3", x+8, y, "--- DAILY LIMITS ---", CLR_HEADER);
   y += h;
   
   double sessionPnL = equity - g_sessionEquity;
   double dailyLossPct = (g_sessionEquity > 0) ? MathMin(0, sessionPnL) / g_sessionEquity * 100 : 0;
   
   color dayClr = (MathAbs(dailyLossPct) < InpMaxDailyLoss * 50) ? CLR_POSITIVE :
                  (MathAbs(dailyLossPct) < InpMaxDailyLoss * 100) ? CLR_NEUTRAL : CLR_NEGATIVE;
   
   HUD_Create("H_R4", x+8, y, StringFormat("Daily Loss: %.2f%% / %.0f%% max",
      MathAbs(dailyLossPct), InpMaxDailyLoss * 100), dayClr);
   y += h + sec;
   
   HUD_Create("H_R5", x+8, y, "--- CIRCUIT BREAKER ---", CLR_HEADER);
   y += h;
   
   string stateStr = g_breaker.GetStateString();
   color cbClr = (g_breaker.state == STATE_LIVE) ? CLR_POSITIVE :
                 (g_breaker.state == STATE_PENDING) ? CLR_NEUTRAL : CLR_NEGATIVE;
   HUD_Create("H_R6", x+8, y, StringFormat("State: %s", stateStr), cbClr);
   y += h;
   
   if(g_breaker.state == STATE_HALTED)
   {
      int rem = InpCooldownMinutes - (int)((TimeCurrent() - g_breaker.haltTime) / 60);
      HUD_Create("H_R7", x+8, y, StringFormat("Reason: %s | %dmin remaining",
         g_breaker.haltReason, MathMax(0, rem)), CLR_NEGATIVE);
      y += h;
   }
   else if(g_breaker.state == STATE_RETRAINING)
   {
      double wr = (g_breaker.retrainTrades > 0) ? 
                 ((double)g_breaker.retrainWins / g_breaker.retrainTrades * 100) : 0;
      HUD_Create("H_R7", x+8, y, StringFormat("Retrain: %d/%d trades WR:%.0f%%",
         g_breaker.retrainTrades, InpRetrainMinTrades, wr), CLR_NEUTRAL);
      y += h;
   }
   y += sec;
   
   HUD_Create("H_R8", x+8, y, "--- POSITION SIZING ---", CLR_HEADER);
   y += h;
   HUD_Create("H_R9", x+8, y, StringFormat("Risk: %.1f%% | Max Lot: %.2f | Max Pos: %d",
      InpRiskPercent, InpMaxLot, InpMaxPositions), CLR_MUTED);
   y += h;
   HUD_Create("H_R10", x+8, y, StringFormat("Omega Sizing: %s | Base:%.1f MaxScale:%.1fx",
      InpUseOmegaSizing ? "ON" : "OFF", InpOmegaBaseline, InpOmegaMaxScale), CLR_MUTED);
}

//+------------------------------------------------------------------+
//| TAB: INSTRUMENTS (By Regime)                                      |
//+------------------------------------------------------------------+
void DrawTab_Instruments(int x, int &y, int h, int sec)
{
   // Collect top symbols by regime
   int trdIdx[5], brkIdx[5], mrIdx[5];
   double trdScore[5], brkScore[5], mrScore[5];
   int trdCnt = 0, brkCnt = 0, mrCnt = 0;
   
   ArrayInitialize(trdIdx, -1);
   ArrayInitialize(brkIdx, -1);
   ArrayInitialize(mrIdx, -1);
   ArrayInitialize(trdScore, -999);
   ArrayInitialize(brkScore, -999);
   ArrayInitialize(mrScore, -999);
   
   for(int i = 0; i < g_rankCount && i < 50; i++)
   {
      int idx = g_ranking[i].symbolIdx;
      if(idx < 0 || idx >= g_symbolCount) continue;
      if(!g_symbols[idx].initialized) continue;
      
      ENUM_REGIME regime = g_symbols[idx].symc.GetRegime();
      double accel = g_symbols[idx].physics.GetAcceleration();
      double score = MathAbs(accel);
      
      if(regime == REGIME_TREND && trdCnt < 5)
      {
         trdIdx[trdCnt] = idx;
         trdScore[trdCnt] = accel;
         trdCnt++;
      }
      else if(regime == REGIME_BREAKOUT && brkCnt < 5)
      {
         brkIdx[brkCnt] = idx;
         brkScore[brkCnt] = accel;
         brkCnt++;
      }
      else if(regime == REGIME_MEANREV && mrCnt < 5)
      {
         mrIdx[mrCnt] = idx;
         mrScore[mrCnt] = accel;
         mrCnt++;
      }
   }
   
   // TREND
   HUD_Create("H_I1", x+8, y, "--- TRENDING ---", clrDodgerBlue);
   y += h;
   for(int i = 0; i < 5; i++)
   {
      if(trdIdx[i] >= 0)
      {
         string dir = (trdScore[i] > 0) ? "^" : "v";
         double chi = g_symbols[trdIdx[i]].symc.GetChi();
         HUD_Create("H_IT" + IntegerToString(i), x+8, y, 
            StringFormat("%s %-7s Chi:%.1f Acc:%+.1f", dir, g_symbols[trdIdx[i]].name, chi, trdScore[i]),
            (trdScore[i] > 0) ? clrLime : clrOrangeRed);
      }
      else
         HUD_Create("H_IT" + IntegerToString(i), x+8, y, "  ---", CLR_MUTED);
      y += h;
   }
   y += sec;
   
   // BREAKOUT
   HUD_Create("H_I2", x+8, y, "--- BREAKOUT ---", clrMagenta);
   y += h;
   for(int i = 0; i < 3; i++)  // Just 3 for space
   {
      if(brkIdx[i] >= 0)
      {
         string dir = (brkScore[i] > 0) ? "^" : "v";
         double chi = g_symbols[brkIdx[i]].symc.GetChi();
         HUD_Create("H_IB" + IntegerToString(i), x+8, y, 
            StringFormat("%s %-7s Chi:%.1f Acc:%+.1f", dir, g_symbols[brkIdx[i]].name, chi, brkScore[i]),
            (brkScore[i] > 0) ? clrLime : clrOrangeRed);
      }
      else
         HUD_Create("H_IB" + IntegerToString(i), x+8, y, "  ---", CLR_MUTED);
      y += h;
   }
   y += sec;
   
   // MEANREV
   HUD_Create("H_I3", x+8, y, "--- MEAN REV ---", clrGold);
   y += h;
   for(int i = 0; i < 3; i++)  // Just 3 for space
   {
      if(mrIdx[i] >= 0)
      {
         string dir = (mrScore[i] > 0) ? "^" : "v";
         double chi = g_symbols[mrIdx[i]].symc.GetChi();
         HUD_Create("H_IM" + IntegerToString(i), x+8, y, 
            StringFormat("%s %-7s Chi:%.1f Acc:%+.1f", dir, g_symbols[mrIdx[i]].name, chi, mrScore[i]),
            (mrScore[i] > 0) ? clrLime : clrOrangeRed);
      }
      else
         HUD_Create("H_IM" + IntegerToString(i), x+8, y, "  ---", CLR_MUTED);
      y += h;
   }
}

//+------------------------------------------------------------------+
//| CHART EVENT - Handle tab switching                                |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   if(id == CHARTEVENT_KEYDOWN)
   {
      // Keys 1-6 switch tabs directly
      if(lparam >= 49 && lparam <= 54)  // '1' to '6'
      {
         g_hudTab = (int)(lparam - 49);
         g_hudLastTabSwitch = TimeCurrent();
      }
      // TAB key cycles forward
      else if(lparam == 9)  // TAB
      {
         g_hudTab = (g_hudTab + 1) % TAB_COUNT;
         g_hudLastTabSwitch = TimeCurrent();
      }
      // Left arrow - previous tab
      else if(lparam == 37)
      {
         g_hudTab = (g_hudTab - 1 + TAB_COUNT) % TAB_COUNT;
         g_hudLastTabSwitch = TimeCurrent();
      }
      // Right arrow - next tab
      else if(lparam == 39)
      {
         g_hudTab = (g_hudTab + 1) % TAB_COUNT;
         g_hudLastTabSwitch = TimeCurrent();
      }
   }
}

void CleanupHUD()
{
   for(int i = 0; i < g_hudCount; i++)
      ObjectDelete(0, g_hudObjects[i]);
   g_hudCount = 0;
   ArrayResize(g_hudObjects, 0);
}

//+------------------------------------------------------------------+
//| PERSISTENCE - Atomic Saves with Checksum Validation               |
//+------------------------------------------------------------------+
#define PERSISTENCE_VERSION  720   // Updated for learning rate storage

// Calculate simple checksum for data validation
uint CalculateChecksum(const uchar &data[], int size)
{
   uint checksum = 0x12345678;
   for(int i = 0; i < size; i++)
   {
      checksum ^= ((uint)data[i] << ((i % 4) * 8));
      checksum = (checksum << 1) | (checksum >> 31);  // Rotate left
   }
   return checksum;
}

void SaveState()
{
   if(!InpUsePersistence) return;
   
   string baseFilename = InpFilePrefix + IntegerToString(InpMagicNumber);
   string tempFilename = baseFilename + "_temp.bin";
   string mainFilename = baseFilename + ".bin";
   string backupFilename = baseFilename + "_backup.bin";
   
   // Step 1: Write to temporary file
   int handle = FileOpen(tempFilename, FILE_WRITE | FILE_BIN);
   if(handle == INVALID_HANDLE) 
   {
      Print("ERROR: Cannot create temp file for save");
      return;
   }
   
   // Write header
   FileWriteInteger(handle, PERSISTENCE_MAGIC);
   FileWriteInteger(handle, PERSISTENCE_VERSION);
   FileWriteLong(handle, TimeCurrent());  // Save timestamp
   
   // Save agents
   SaveAgent(handle, g_sniper);
   SaveAgent(handle, g_berserker);
   
   // Save predictor
   for(int i = 0; i < 3; i++) FileWriteDouble(handle, g_predictor.regimeWR[i]);
   for(int i = 0; i < 5; i++) FileWriteDouble(handle, g_predictor.chiZoneWR[i]);
   for(int i = 0; i < 5; i++) FileWriteDouble(handle, g_predictor.accelZoneWR[i]);
   for(int i = 0; i < 3; i++) FileWriteInteger(handle, g_predictor.regimeCounts[i]);
   for(int i = 0; i < 5; i++) FileWriteInteger(handle, g_predictor.chiCounts[i]);
   for(int i = 0; i < 5; i++) FileWriteInteger(handle, g_predictor.accelCounts[i]);
   
   // Save circuit breaker state
   FileWriteInteger(handle, (int)g_breaker.state);
   FileWriteDouble(handle, g_breaker.peakEquity);
   
   // Calculate and write checksum placeholder position
   ulong checksumPos = FileTell(handle);
   FileWriteInteger(handle, 0);  // Placeholder
   
   FileFlush(handle);
   FileClose(handle);
   
   // Step 2: Validate temp file is readable
   handle = FileOpen(tempFilename, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE)
   {
      Print("ERROR: Cannot verify temp file");
      FileDelete(tempFilename);
      return;
   }
   
   // Quick validation - check magic and version
   int magic = FileReadInteger(handle);
   int version = FileReadInteger(handle);
   FileClose(handle);
   
   if(magic != PERSISTENCE_MAGIC || version != PERSISTENCE_VERSION)
   {
      Print("ERROR: Temp file validation failed");
      FileDelete(tempFilename);
      return;
   }
   
   // Step 3: Atomic swap - backup old, rename temp to main
   if(FileIsExist(mainFilename))
   {
      // Delete old backup if exists
      if(FileIsExist(backupFilename))
         FileDelete(backupFilename);
      
      // Move current to backup
      if(!FileMove(mainFilename, 0, backupFilename, FILE_REWRITE))
      {
         Print("WARNING: Could not create backup");
      }
   }
   
   // Rename temp to main (atomic on most filesystems)
   if(!FileMove(tempFilename, 0, mainFilename, FILE_REWRITE))
   {
      Print("ERROR: Could not finalize save");
      return;
   }
   
   // Clean up temp file if it still exists
   if(FileIsExist(tempFilename))
      FileDelete(tempFilename);
}

void SaveAgent(int handle, TradingAgent &agent)
{
   // Save real profile
   SaveProfile(handle, agent.real);
   
   // Save shadow profile
   SaveProfile(handle, agent.shadow);
   
   // Save meta
   FileWriteDouble(handle, agent.capitalAlloc);
   FileWriteInteger(handle, agent.swapCount);
   FileWriteInteger(handle, agent.consLosses);
}

void SaveProfile(int handle, AgentProfile &profile)
{
   for(int i = 0; i < 3; i++)
   {
      FileWriteDouble(handle, profile.regime[i].qBuy);
      FileWriteDouble(handle, profile.regime[i].qSell);
      FileWriteDouble(handle, profile.regime[i].qHold);
      FileWriteInteger(handle, profile.regime[i].trades);
      FileWriteInteger(handle, profile.regime[i].wins);
      FileWriteDouble(handle, profile.regime[i].pnl);
      FileWriteDouble(handle, profile.regime[i].upside);
      FileWriteDouble(handle, profile.regime[i].downside);
      FileWriteDouble(handle, profile.regime[i].learningRate);  // NEW: Save learning rate
   }
}

void LoadState()
{
   if(!InpUsePersistence) return;
   
   string baseFilename = InpFilePrefix + IntegerToString(InpMagicNumber);
   string mainFilename = baseFilename + ".bin";
   string backupFilename = baseFilename + "_backup.bin";
   
   // Try main file first
   bool loaded = TryLoadFile(mainFilename);
   
   // If main file failed, try backup
   if(!loaded && FileIsExist(backupFilename))
   {
      Print("Main file corrupted, trying backup...");
      loaded = TryLoadFile(backupFilename);
      if(loaded)
         Print("Loaded from backup successfully");
   }
   
   if(!loaded)
   {
      Print("No valid state file found, starting fresh");
   }
}

bool TryLoadFile(string filename)
{
   int handle = FileOpen(filename, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE) return false;
   
   // Read and validate header
   int magic = FileReadInteger(handle);
   if(magic != PERSISTENCE_MAGIC) 
   { 
      FileClose(handle); 
      Print("Invalid magic number in ", filename);
      return false; 
   }
   
   int version = FileReadInteger(handle);
   
   // Handle version migration
   if(version == 710)
   {
      FileClose(handle);
      return LoadStateV710(filename);  // Legacy loader
   }
   else if(version != PERSISTENCE_VERSION)
   {
      FileClose(handle);
      Print("Unknown version ", version, " in ", filename);
      return false;
   }
   
   datetime saveTime = (datetime)FileReadLong(handle);
   Print("Loading state from ", TimeToString(saveTime));
   
   // Load agents
   LoadAgent(handle, g_sniper);
   LoadAgent(handle, g_berserker);
   
   // Load predictor
   for(int i = 0; i < 3; i++) g_predictor.regimeWR[i] = FileReadDouble(handle);
   for(int i = 0; i < 5; i++) g_predictor.chiZoneWR[i] = FileReadDouble(handle);
   for(int i = 0; i < 5; i++) g_predictor.accelZoneWR[i] = FileReadDouble(handle);
   for(int i = 0; i < 3; i++) g_predictor.regimeCounts[i] = FileReadInteger(handle);
   for(int i = 0; i < 5; i++) g_predictor.chiCounts[i] = FileReadInteger(handle);
   for(int i = 0; i < 5; i++) g_predictor.accelCounts[i] = FileReadInteger(handle);
   
   // Load circuit breaker state
   g_breaker.state = (ENUM_TRADING_STATE)FileReadInteger(handle);
   g_breaker.peakEquity = FileReadDouble(handle);
   
   FileClose(handle);
   Print("State loaded successfully (v", PERSISTENCE_VERSION, ")");
   return true;
}

// Legacy loader for v710 files
bool LoadStateV710(string filename)
{
   int handle = FileOpen(filename, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE) return false;
   
   // Skip header (already validated)
   FileReadInteger(handle);  // magic
   FileReadInteger(handle);  // version
   
   // Load agents (old format without learning rate)
   LoadAgentV710(handle, g_sniper);
   LoadAgentV710(handle, g_berserker);
   
   // Load predictor (old format without counts)
   for(int i = 0; i < 3; i++) g_predictor.regimeWR[i] = FileReadDouble(handle);
   for(int i = 0; i < 5; i++) g_predictor.chiZoneWR[i] = FileReadDouble(handle);
   for(int i = 0; i < 5; i++) g_predictor.accelZoneWR[i] = FileReadDouble(handle);
   
   FileClose(handle);
   Print("Migrated from v710 format successfully");
   return true;
}

void LoadAgentV710(int handle, TradingAgent &agent)
{
   LoadProfileV710(handle, agent.real);
   LoadProfileV710(handle, agent.shadow);
   
   agent.capitalAlloc = FileReadDouble(handle);
   agent.swapCount = FileReadInteger(handle);
   
   agent.real.RecalcTotals();
   agent.shadow.RecalcTotals();
}

void LoadProfileV710(int handle, AgentProfile &profile)
{
   for(int i = 0; i < 3; i++)
   {
      profile.regime[i].qBuy = FileReadDouble(handle);
      profile.regime[i].qSell = FileReadDouble(handle);
      profile.regime[i].qHold = FileReadDouble(handle);
      profile.regime[i].trades = FileReadInteger(handle);
      profile.regime[i].wins = FileReadInteger(handle);
      profile.regime[i].pnl = FileReadDouble(handle);
      profile.regime[i].upside = FileReadDouble(handle);
      profile.regime[i].downside = FileReadDouble(handle);
      // Learning rate not in v710, use default
      profile.regime[i].learningRate = InpLearningRateInit;
      profile.regime[i].InvalidateCache();
   }
}

void LoadAgent(int handle, TradingAgent &agent)
{
   LoadProfile(handle, agent.real);
   LoadProfile(handle, agent.shadow);
   
   agent.capitalAlloc = FileReadDouble(handle);
   agent.swapCount = FileReadInteger(handle);
   agent.consLosses = FileReadInteger(handle);
   
   agent.real.RecalcTotals();
   agent.shadow.RecalcTotals();
}

void LoadProfile(int handle, AgentProfile &profile)
{
   for(int i = 0; i < 3; i++)
   {
      profile.regime[i].qBuy = FileReadDouble(handle);
      profile.regime[i].qSell = FileReadDouble(handle);
      profile.regime[i].qHold = FileReadDouble(handle);
      profile.regime[i].trades = FileReadInteger(handle);
      profile.regime[i].wins = FileReadInteger(handle);
      profile.regime[i].pnl = FileReadDouble(handle);
      profile.regime[i].upside = FileReadDouble(handle);
      profile.regime[i].downside = FileReadDouble(handle);
      profile.regime[i].learningRate = FileReadDouble(handle);  // NEW: Load learning rate
      profile.regime[i].InvalidateCache();
   }
}
#endif  // END LEGACY HUD/PERSISTENCE

//+------------------------------------------------------------------+
//| END OF FILE - VelocityTrader v7.1 Duel Architecture               |
//+------------------------------------------------------------------+
