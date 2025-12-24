//+------------------------------------------------------------------+
//|                                               VT_Structures.mqh  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|                          Core Data Structures and Agent Profiles |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"

#ifndef VT_STRUCTURES_MQH
#define VT_STRUCTURES_MQH

#include "VT_Definitions.mqh"

// Forward declaration - g_rlParams must be defined in globals
extern RLParameters g_rlParams;

// Forward declaration of input parameters (defined in main EA)
extern double InpLearningRateInit;
extern double InpLearningRateMin;
extern double InpLearningDecay;
extern int    InpSwapMinTrades;
extern double InpSwapThreshold;

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

      Print("=== AGENT SWAP: ", name, " ===");
      Print("Shadow became Champion (Swap #", swapCount, ")");
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Position Info                                          |
//+------------------------------------------------------------------+
struct PositionData
{
   ulong    ticket;
   string   symbol;
   int      direction;       // 1=BUY, -1=SELL
   double   entryPrice;
   double   currentSL;
   double   lots;
   double   entryATR;
   int      agentId;
   bool     isShadow;
   int      regimeAtEntry;
   double   frictionCost;
   datetime openTime;
   double   pWinAtEntry;
   bool     active;
   double   mae;             // Maximum Adverse Excursion
   double   mfe;             // Maximum Favorable Excursion
   double   currentPnL;
};

//+------------------------------------------------------------------+
//| STRUCTURE: Velocity Ranking Entry                                 |
//+------------------------------------------------------------------+
struct VelocityRank
{
   int    symbolIdx;
   double score;
};

//+------------------------------------------------------------------+
//| STRUCTURE: Period Statistics                                      |
//+------------------------------------------------------------------+
struct PeriodStats
{
   double pnl;
   int    trades;
   int    wins;
   double startEquity;
   datetime startTime;

   void Reset(double equity)
   {
      pnl = 0;
      trades = 0;
      wins = 0;
      startEquity = equity;
      startTime = TimeCurrent();
   }

   double GetWR()
   {
      return (trades > 0) ? ((double)wins / trades * 100) : 0;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Excursion Tracking                                     |
//+------------------------------------------------------------------+
struct ExcursionStats
{
   double avgMAE;
   double maxMAE;
   double avgMFE;
   double maxMFE;
   int    count;

   void Init()
   {
      avgMAE = 0;
      maxMAE = 0;
      avgMFE = 0;
      maxMFE = 0;
      count = 0;
   }

   void Update(double mae, double mfe)
   {
      count++;
      avgMAE = avgMAE + (mae - avgMAE) / count;
      avgMFE = avgMFE + (mfe - avgMFE) / count;
      if(mae < maxMAE) maxMAE = mae;  // MAE is negative
      if(mfe > maxMFE) maxMFE = mfe;
   }

   double GetAvgETD(double avgPnL)
   {
      // Edge to Drawdown ratio
      if(avgMAE == 0) return 0;
      return avgPnL / MathAbs(avgMAE);
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: System Status                                          |
//+------------------------------------------------------------------+
struct SystemStatus
{
   bool brokerConnected;
   bool networkOK;
   bool rlActive;
   bool riskOK;

   void Update()
   {
      brokerConnected = (TerminalInfoInteger(TERMINAL_CONNECTED) != 0);
      networkOK = brokerConnected;
      rlActive = true;  // RL is always running
      riskOK = true;    // Updated by circuit breaker
   }
};

#endif // VT_STRUCTURES_MQH
