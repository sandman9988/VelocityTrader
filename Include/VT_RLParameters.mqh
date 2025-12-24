//+------------------------------------------------------------------+
//|                                             VT_RLParameters.mqh  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|                    RL Parameters - Normalized [0,1] for tuning   |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"

#ifndef VT_RLPARAMETERS_MQH
#define VT_RLPARAMETERS_MQH

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

   // Conversion functions: [0,1] -> actual value
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

#endif // VT_RLPARAMETERS_MQH
