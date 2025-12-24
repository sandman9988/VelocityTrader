//+------------------------------------------------------------------+
//|                                                VT_Predictor.mqh  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|              Probability Predictor and Statistical Gate Structs  |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"

#ifndef VT_PREDICTOR_MQH
#define VT_PREDICTOR_MQH

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
         return MathMax(0.3, SafeDivide(omega, InpOmegaBaseline, 0.3));

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
      double observed = SafeDivide((double)wins, (double)total, 0.5);
      double variance = SafeDivide(p * (1.0 - p), (double)total, 0.0001);
      double stdErr = MathSqrt(variance);
      if(stdErr < 0.0001) return 1.0;

      double zScore = SafeDivide(observed - p, stdErr, 0.0);

      return 1.0 - NormalCDF(zScore);
   }

   bool HasEdge(int wins, int total, double avgWin, double avgLoss, double avgFriction)
   {
      if(total < InpMinTradesForEdge) return false;

      // Win rate must beat friction-adjusted coin flip
      double frictionHurdle = SafeDivide(avgFriction, avgWin, 0.0);
      double minWR = InpMinWinRate + frictionHurdle;
      double actualWR = SafeDivide((double)wins, (double)total, 0.0);

      if(actualWR < minWR) return false;

      // Statistical significance
      double pVal = CalculatePValue(wins, total);
      if(pVal > InpMaxPValue) return false;

      return true;
   }
};

#endif // VT_PREDICTOR_MQH
