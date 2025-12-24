//+------------------------------------------------------------------+
//|                                                VT_Predictor.mqh  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|              Probability Predictor and Statistical Gate Structs  |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"

#ifndef VT_PREDICTOR_MQH
#define VT_PREDICTOR_MQH

#include "VT_Definitions.mqh"  // Required for SafeDivide()

// Forward declaration of input parameters (defined in main EA)
extern double InpOmegaBaseline;
extern double InpOmegaMaxScale;
extern double InpMinWinRate;
extern double InpMaxPValue;
extern int    InpMinTradesForEdge;

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
      // Validate input - return middle zone for invalid values
      if(!MathIsValidNumber(zScore))
      {
         return 2;  // Middle zone is safest default
      }

      // Clamp extreme values to prevent unexpected behavior
      zScore = MathMax(-10.0, MathMin(10.0, zScore));

      if(zScore < -2.0) return 0;
      if(zScore < -1.0) return 1;
      if(zScore < 1.0) return 2;
      if(zScore < 2.0) return 3;
      return 4;
   }

   bool Update(int regimeIdx, double chiZ, double accelZ, bool won)
   {
      // Validate inputs
      if(!MathIsValidNumber(chiZ))
      {
         chiZ = 0.0;  // Default to neutral
      }
      if(!MathIsValidNumber(accelZ))
      {
         accelZ = 0.0;  // Default to neutral
      }

      double winVal = won ? 1.0 : 0.0;
      double alpha = 0.05;  // Learning rate for predictor

      // Update regime WR with bounds checking
      if(regimeIdx >= 0 && regimeIdx < 3)
      {
         // Protect against integer overflow
         if(regimeCounts[regimeIdx] < INT_MAX - 1)
         {
            regimeCounts[regimeIdx]++;
         }
         regimeWR[regimeIdx] += alpha * (winVal - regimeWR[regimeIdx]);
         // Ensure WR stays in valid range
         regimeWR[regimeIdx] = MathMax(0.0, MathMin(1.0, regimeWR[regimeIdx]));
      }

      // Update chi zone WR with bounds checking
      int chiZone = GetZone(chiZ);
      if(chiZone >= 0 && chiZone < 5)
      {
         if(chiCounts[chiZone] < INT_MAX - 1)
         {
            chiCounts[chiZone]++;
         }
         chiZoneWR[chiZone] += alpha * (winVal - chiZoneWR[chiZone]);
         chiZoneWR[chiZone] = MathMax(0.0, MathMin(1.0, chiZoneWR[chiZone]));
      }

      // Update accel zone WR with bounds checking
      int accelZone = GetZone(accelZ);
      if(accelZone >= 0 && accelZone < 5)
      {
         if(accelCounts[accelZone] < INT_MAX - 1)
         {
            accelCounts[accelZone]++;
         }
         accelZoneWR[accelZone] += alpha * (winVal - accelZoneWR[accelZone]);
         accelZoneWR[accelZone] = MathMax(0.0, MathMin(1.0, accelZoneWR[accelZone]));
      }

      return true;
   }

   double Predict(int regimeIdx, double chiZ, double accelZ, double agentWR)
   {
      // Validate inputs and use safe defaults
      if(!MathIsValidNumber(chiZ)) chiZ = 0.0;
      if(!MathIsValidNumber(accelZ)) accelZ = 0.0;
      if(!MathIsValidNumber(agentWR)) agentWR = 0.5;

      double pBase = 0.50;

      // Regime contribution with bounds validation
      double pRegime = pBase;
      if(regimeIdx >= 0 && regimeIdx < 3)
      {
         pRegime = regimeWR[regimeIdx];
         // Validate stored value is in valid range
         if(!MathIsValidNumber(pRegime) || pRegime < 0.0 || pRegime > 1.0)
         {
            pRegime = pBase;
         }
      }

      // Zone contributions with validation
      int chiZone = GetZone(chiZ);
      int accelZone = GetZone(accelZ);

      // Validate zone indices (should always be valid from GetZone, but defensive)
      if(chiZone < 0 || chiZone >= 5) chiZone = 2;
      if(accelZone < 0 || accelZone >= 5) accelZone = 2;

      double pChi = chiZoneWR[chiZone];
      double pAccel = accelZoneWR[accelZone];

      // Validate zone WRs
      if(!MathIsValidNumber(pChi) || pChi < 0.0 || pChi > 1.0) pChi = pBase;
      if(!MathIsValidNumber(pAccel) || pAccel < 0.0 || pAccel > 1.0) pAccel = pBase;

      // Agent's historical WR (clamp to reasonable range)
      double pAgent = MathMax(0.3, MathMin(0.7, agentWR));

      // Weighted combination
      double pWin = (pRegime * 0.30) +
                    (pChi * 0.20) +
                    (pAccel * 0.25) +
                    (pAgent * 0.25);

      // Final validation and clamping
      if(!MathIsValidNumber(pWin))
      {
         return pBase;  // Safe default
      }

      return MathMax(0.30, MathMin(0.70, pWin));
   }

   // Omega-based position sizing
   // Omega = Upside / Downside
   // Scale size based on how much Omega exceeds baseline
   double GetOmegaSize(double omega, double pWin)
   {
      // Validate inputs
      if(!MathIsValidNumber(omega) || omega <= 0.0)
      {
         return 0.3;  // Minimum safe size for invalid omega
      }
      if(!MathIsValidNumber(pWin))
      {
         pWin = 0.5;  // Default probability
      }

      // Clamp pWin to valid probability range
      pWin = MathMax(0.0, MathMin(1.0, pWin));

      // Validate baseline parameter
      double baseline = InpOmegaBaseline;
      if(!MathIsValidNumber(baseline) || baseline <= 0.0)
      {
         baseline = 1.0;  // Safe default
      }

      // If Omega below baseline, reduce size
      if(omega < baseline)
      {
         return MathMax(0.3, SafeDivide(omega, baseline, 0.3));
      }

      // Scale up based on Omega excess, capped at max
      // Formula: 1.0 + (omega - baseline) * scaling_factor
      double excess = omega - baseline;
      double scale = 1.0 + (excess * 0.3);  // 30% boost per 1.0 omega above baseline

      // Apply probability confidence
      scale *= (0.5 + pWin);  // Range: 0.8 to 1.2 based on pWin

      // Validate and cap the result
      if(!MathIsValidNumber(scale) || scale <= 0.0)
      {
         return 0.3;  // Minimum safe size
      }

      double maxScale = InpOmegaMaxScale;
      if(!MathIsValidNumber(maxScale) || maxScale <= 0.0)
      {
         maxScale = 2.0;  // Safe default max
      }

      return MathMin(scale, maxScale);
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
      // Validate inputs
      if(total < 10)
      {
         return 1.0;  // Not enough data
      }

      // Ensure wins is within valid range
      if(wins < 0)
      {
         wins = 0;
      }
      if(wins > total)
      {
         wins = total;
      }

      double p = 0.5;  // Null hypothesis: random chance
      double observed = SafeDivide((double)wins, (double)total, 0.5);

      // Validate observed is in valid range
      if(!MathIsValidNumber(observed) || observed < 0.0 || observed > 1.0)
      {
         return 1.0;
      }

      double variance = SafeDivide(p * (1.0 - p), (double)total, 0.0001);
      if(variance <= 0.0)
      {
         return 1.0;  // Invalid variance
      }

      double stdErr = MathSqrt(variance);
      if(!MathIsValidNumber(stdErr) || stdErr < 0.0001)
      {
         return 1.0;  // Standard error too small
      }

      double zScore = SafeDivide(observed - p, stdErr, 0.0);
      if(!MathIsValidNumber(zScore))
      {
         return 1.0;
      }

      double pValue = 1.0 - NormalCDF(zScore);

      // Validate result
      if(!MathIsValidNumber(pValue) || pValue < 0.0 || pValue > 1.0)
      {
         return 1.0;
      }

      return pValue;
   }

   bool HasEdge(int wins, int total, double avgWin, double avgLoss, double avgFriction)
   {
      // Validate inputs
      if(total < 0 || wins < 0 || wins > total)
      {
         return false;
      }

      int minTrades = InpMinTradesForEdge;
      if(minTrades <= 0)
      {
         minTrades = 10;  // Safe default
      }

      if(total < minTrades)
      {
         return false;
      }

      // Validate average values
      if(!MathIsValidNumber(avgWin) || avgWin <= 0.0)
      {
         return false;  // Can't calculate edge without valid win average
      }
      if(!MathIsValidNumber(avgLoss))
      {
         avgLoss = 0.0;
      }
      if(!MathIsValidNumber(avgFriction))
      {
         avgFriction = 0.0;
      }

      // Win rate must beat friction-adjusted coin flip
      double frictionHurdle = SafeDivide(avgFriction, avgWin, 0.0);

      double minWR = InpMinWinRate;
      if(!MathIsValidNumber(minWR) || minWR < 0.0 || minWR > 1.0)
      {
         minWR = 0.5;  // Safe default
      }
      minWR += frictionHurdle;

      double actualWR = SafeDivide((double)wins, (double)total, 0.0);
      if(!MathIsValidNumber(actualWR))
      {
         return false;
      }

      if(actualWR < minWR)
      {
         return false;
      }

      // Statistical significance
      double pVal = CalculatePValue(wins, total);

      double maxPValue = InpMaxPValue;
      if(!MathIsValidNumber(maxPValue) || maxPValue <= 0.0 || maxPValue > 1.0)
      {
         maxPValue = 0.05;  // Safe default (5% significance level)
      }

      if(pVal > maxPValue)
      {
         return false;
      }

      return true;
   }
};

#endif // VT_PREDICTOR_MQH
