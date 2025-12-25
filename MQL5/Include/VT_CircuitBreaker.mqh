//+------------------------------------------------------------------+
//|                                           VT_CircuitBreaker.mqh  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|                           Circuit Breaker for Risk Management    |
//|                         v7.1.1 (floating DD/daily loss fixes)    |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"

#ifndef VT_CIRCUITBREAKER_MQH
#define VT_CIRCUITBREAKER_MQH

#include "VT_Definitions.mqh"

// Note: Input parameters (InpMaxDailyLoss, etc.) are defined
// in the main EA file and are automatically globally accessible.
// DO NOT redeclare them with 'extern' as this causes type conflicts.

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

   // Daily tracking (dailyPnL is realized; dailyStartEquity is used for floating-inclusive checks)
   double             dailyPnL;
   double             dailyStartEquity;
   datetime           dayStart;

   // Drawdown tracking (session peak by design)
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
         // New day - reset daily stats (but keep peakEquity as session peak)
         dayStart = today;
         dailyPnL = 0;
         dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
      }

      // Update drawdown from session peak
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      if(equity > peakEquity) peakEquity = equity;
      currentDD = SafeDivide(peakEquity - equity, peakEquity, 0.0);
   }

   bool CheckTriggers(double rollingWR, int consLosses)
   {
      if(state != STATE_LIVE) return false;

      UpdateDaily();

      const double equity = AccountInfoDouble(ACCOUNT_EQUITY);

      // Floating-inclusive daily loss (more conservative / correct)
      // dailyPnL is realized; this check is equity-based.
      const double dailyPnL_equity = equity - dailyStartEquity;              // includes floating
      const double dailyLossPct    = SafeDivide(-MathMin(0.0, dailyPnL_equity), dailyStartEquity, 0.0);

      // Daily loss (treat <=0 as disabled)
      if(InpMaxDailyLoss > 0.0 && dailyLossPct > InpMaxDailyLoss)
      {
         Halt(StringFormat("Daily loss %.1f%% > %.1f%%",
              dailyLossPct * 100.0, InpMaxDailyLoss * 100.0));
         return true;
      }

      // Consecutive losses (treat <=0 as disabled)
      if(InpMaxConsLosses > 0 && consLosses >= InpMaxConsLosses)
      {
         Halt(StringFormat("%d consecutive losses", consLosses));
         return true;
      }

      // Rolling win rate (treat <=0 as disabled)
      if(InpMinRollingWR > 0.0 && rollingWR < InpMinRollingWR)
      {
         Halt(StringFormat("Rolling WR %.1f%% < %.1f%%",
              rollingWR * 100.0, InpMinRollingWR * 100.0));
         return true;
      }

      // Drawdown (session peak) (treat <=0 as disabled)
      if(InpMaxDrawdown > 0.0 && currentDD > InpMaxDrawdown)
      {
         Halt(StringFormat("Drawdown %.1f%% > %.1f%%",
              currentDD * 100.0, InpMaxDrawdown * 100.0));
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

      Alert("CIRCUIT BREAKER: ", reason);

      Print("======================================================");
      Print("   CIRCUIT BREAKER TRIGGERED");
      Print("   Reason: ", reason);
      Print("   Status: HALTED (cooldown ", InpCooldownMinutes, " min)");
      Print("   Action: Auto-retraining will begin after cooldown");
      Print("======================================================");
   }

   void Update()
   {
      if(state == STATE_HALTED)
      {
         // Cooldown period
         int elapsedMin = (int)(TimeCurrent() - haltTime) / 60;
         if(elapsedMin >= InpCooldownMinutes)
         {
            state = STATE_RETRAINING;
            Print("Cooldown complete. Entering RETRAIN mode (shadow only).");
         }
      }
      else if(state == STATE_RETRAINING)
      {
         if(retrainTrades >= InpRetrainMinTrades && InpRetrainMinTrades > 0)
         {
            double wr = SafeDivide((double)retrainWins, (double)retrainTrades, 0.0);
            double pf = SafeDivide(retrainUpside, retrainDownside, 0.0);

            if(wr >= InpRetrainMinWR && pf >= InpRetrainMinPF)
            {
               state = STATE_PENDING;
               Print("======================================================");
               Print("   RETRAIN COMPLETE - PENDING APPROVAL");
               Print("   WR: ", DoubleToString(wr * 100, 1), "% PF: ", DoubleToString(pf, 2));
               Print("   Set InpManualReinstate=true to go LIVE");
               Print("======================================================");
            }
         }
      }
      else if(state == STATE_PENDING)
      {
         // Manual reinstatement handled elsewhere
      }

      UpdateDaily();
   }

   string GetStateString()
   {
      switch(state)
      {
         case STATE_LIVE:       return "LIVE";
         case STATE_HALTED:     return "HALTED";
         case STATE_RETRAINING: return "RETRAINING";
         case STATE_PENDING:    return "PENDING";
         default:               return "UNKNOWN";
      }
   }

   bool CanTradeShadow()
   {
      // Shadow trades allowed after cooldown; during cooldown keep system quiet.
      if(state == STATE_HALTED)
         return ((int)(TimeCurrent() - haltTime) / 60 >= InpCooldownMinutes);

      return true;
   }

   bool CanTradeLive()
   {
      return (state == STATE_LIVE);
   }

   void RecordRetrainTrade(double pnl)
   {
      // Only record during actual retraining phase
      if(state != STATE_RETRAINING)
         return;

      retrainTrades++;
      retrainPnL += pnl;

      if(pnl > 0)
      {
         retrainWins++;
         retrainUpside += pnl;
      }
      else
      {
         retrainDownside += MathAbs(pnl);
      }
   }

   void RecordDailyPnL(double pnl)
   {
      // Realized-only tracking (equity-based daily loss is handled in CheckTriggers)
      dailyPnL += pnl;
   }

   void Reinstate()
   {
      if(state == STATE_PENDING)
      {
         state = STATE_LIVE;
         Print("======================================================");
         Print("   SYSTEM REINSTATED - NOW LIVE");
         Print("======================================================");
      }
   }

   void ForceHalt()
   {
      Halt("Manual force halt");
   }
};

#endif // VT_CIRCUITBREAKER_MQH
