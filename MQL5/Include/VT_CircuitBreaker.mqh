//+------------------------------------------------------------------+
//|                                           VT_CircuitBreaker.mqh  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|                           Circuit Breaker for Risk Management    |
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
      currentDD = SafeDivide(peakEquity - equity, peakEquity, 0.0);
   }

   bool CheckTriggers(double rollingWR, int consLosses)
   {
      if(state != STATE_LIVE) return false;

      UpdateDaily();

      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      double dailyLossPct = SafeDivide(-dailyPnL, dailyStartEquity, 0.0);

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
         int elapsed = (int)(TimeCurrent() - haltTime) / 60;
         if(elapsed >= InpCooldownMinutes)
         {
            state = STATE_RETRAINING;
            Print("Cooldown complete. Entering RETRAIN mode (shadow only).");
         }
      }
      else if(state == STATE_RETRAINING)
      {
         // Check if retrain criteria met
         if(retrainTrades >= InpRetrainMinTrades)
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
         // Check for manual reinstatement (via input parameter)
         // This is handled in OnTick/OnTimer
      }

      UpdateDaily();
   }

   //+------------------------------------------------------------------+
   //| Get state as string for display                                   |
   //+------------------------------------------------------------------+
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

   //+------------------------------------------------------------------+
   //| Can execute shadow trades (learning)?                             |
   //+------------------------------------------------------------------+
   bool CanTradeShadow()
   {
      // Shadow trades are allowed in all states except forced halt
      return (state != STATE_HALTED ||
              (int)(TimeCurrent() - haltTime) / 60 >= InpCooldownMinutes);
   }

   //+------------------------------------------------------------------+
   //| Can execute real (live) trades?                                   |
   //+------------------------------------------------------------------+
   bool CanTradeLive()
   {
      return (state == STATE_LIVE);
   }

   //+------------------------------------------------------------------+
   //| Record a trade during retraining phase                            |
   //+------------------------------------------------------------------+
   void RecordRetrainTrade(double pnl)
   {
      if(state == STATE_RETRAINING || state == STATE_HALTED)
      {
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
   }

   //+------------------------------------------------------------------+
   //| Record daily P&L for circuit breaker tracking                     |
   //+------------------------------------------------------------------+
   void RecordDailyPnL(double pnl)
   {
      dailyPnL += pnl;
   }

   //+------------------------------------------------------------------+
   //| Manual reinstatement                                              |
   //+------------------------------------------------------------------+
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

   //+------------------------------------------------------------------+
   //| Force halt (manual override)                                      |
   //+------------------------------------------------------------------+
   void ForceHalt()
   {
      Halt("Manual force halt");
   }
};

#endif // VT_CIRCUITBREAKER_MQH
