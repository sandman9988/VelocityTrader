//+------------------------------------------------------------------+
//|                                            VT_KinematicRegimes.mqh |
//|                         VelocityTrader v7.1: Duel Architecture     |
//|          Kinematic Regime Detection, Agent Profiles & RL Shaping  |
//+------------------------------------------------------------------+
#ifndef VT_KINEMATIC_REGIMES_MQH
#define VT_KINEMATIC_REGIMES_MQH

#property copyright "VelocityTrader v7.1"

#include "VT_Definitions.mqh"
#include "VT_RLParameters.mqh"

//+------------------------------------------------------------------+
//| CONSTANTS - Kinematic Physics                                     |
//+------------------------------------------------------------------+
#define MICRO_WINDOW      5     // Micro timescale (fast oscillations)
#define MESO_WINDOW       20    // Meso timescale (trend detection)
#define MACRO_WINDOW      60    // Macro timescale (regime persistence)
#define SENSOR_DIM        24    // Total sensor vector dimension
#define KINEMATIC_STATES  6     // Number of kinematic states

//+------------------------------------------------------------------+
//| ENUM - Extended Kinematic States                                  |
//+------------------------------------------------------------------+
enum ENUM_KINEMATIC_STATE
{
   KIN_ACCELERATING = 0,   // Positive jerk, building momentum
   KIN_CRUISING = 1,       // Steady velocity, low acceleration
   KIN_DECELERATING = 2,   // Negative jerk, momentum fading
   KIN_REVERTING = 3,      // Moving towards equilibrium
   KIN_OSCILLATING = 4,    // High chi, bounded range
   KIN_EXPLOSIVE = 5       // Extreme acceleration spike
};

//+------------------------------------------------------------------+
//| ENUM - Agent Personality Type                                     |
//+------------------------------------------------------------------+
enum ENUM_AGENT_PERSONALITY
{
   PERSONALITY_SNIPER = 0,     // Patient, high-conviction, trend-rider
   PERSONALITY_BERSERKER = 1   // Aggressive, quick, volatility-hunter
};

//+------------------------------------------------------------------+
//| STRUCTURE - Kinematic State Vector                                |
//+------------------------------------------------------------------+
struct KinematicState
{
   // Position derivatives (price space)
   double            position;         // Normalized price level
   double            velocity;         // dP/dt (rate of change)
   double            acceleration;     // d²P/dt² (momentum change)
   double            jerk;             // d³P/dt³ (acceleration change)

   // Multi-timescale analysis
   double            microVelocity;    // Fast timescale velocity
   double            mesoVelocity;     // Medium timescale velocity
   double            macroVelocity;    // Slow timescale velocity

   // Regime indicators
   double            chi;              // Oscillation intensity
   double            chiZ;             // Normalized chi (z-score)
   double            mass;             // Synthetic inertia
   double            momentum;         // mass * velocity

   // Derived states
   ENUM_KINEMATIC_STATE state;
   ENUM_REGIME       regime;
   double            stateConfidence;  // 0-1 confidence in state
   int               statePersistence; // Bars in current state

   void Reset()
   {
      position = 0.5;
      velocity = 0.0;
      acceleration = 0.0;
      jerk = 0.0;
      microVelocity = 0.0;
      mesoVelocity = 0.0;
      macroVelocity = 0.0;
      chi = 1.0;
      chiZ = 0.0;
      mass = 1.0;
      momentum = 0.0;
      state = KIN_CRUISING;
      regime = REGIME_CALIBRATING;
      stateConfidence = 0.0;
      statePersistence = 0;
   }

   string ToJSON()
   {
      return StringFormat(
         "{\"pos\":%.4f,\"vel\":%.4f,\"acc\":%.4f,\"jerk\":%.4f,"
         "\"chi\":%.3f,\"chiZ\":%.2f,\"state\":%d,\"regime\":%d,\"conf\":%.2f}",
         position, velocity, acceleration, jerk,
         chi, chiZ, (int)state, (int)regime, stateConfidence);
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Agent Sensor Profile                                  |
//|                                                                    |
//| Sniper: Emphasizes trend confirmation, patience, high conviction  |
//| Berserker: Emphasizes volatility, quick signals, momentum spikes  |
//+------------------------------------------------------------------+
struct AgentSensorProfile
{
   ENUM_AGENT_PERSONALITY personality;

   // Sensor weightings (sum to 1.0)
   double            w_velocity;       // Velocity importance
   double            w_acceleration;   // Acceleration importance
   double            w_jerk;           // Jerk (rate of accel change)
   double            w_momentum;       // Mass-weighted momentum
   double            w_chi;            // Oscillation intensity
   double            w_timescaleAlign; // Multi-timescale alignment
   double            w_regime;         // Regime match bonus
   double            w_volatility;     // Volatility factor

   // Entry thresholds (divergent per agent)
   double            signalThreshold;  // Min signal strength to enter
   double            velocityMin;      // Min velocity for entry
   double            accelMin;         // Min acceleration for entry
   double            chiMax;           // Max chi (Berserker likes high)
   double            persistenceMin;   // Min bars in state before entry

   // Exit parameters
   double            trailMultiplier;  // ATR multiplier for trail
   double            stopMultiplier;   // ATR multiplier for stop
   double            targetMultiplier; // ATR multiplier for target
   double            timeDecayRate;    // Reward decay per minute

   // Reward shaping (divergent)
   double            winMultiplier;    // Bonus for wins
   double            lossPenalty;      // Penalty for losses
   double            speedBonus;       // Bonus for quick profits
   double            patienceBonus;    // Bonus for holding trends
   double            reversalPenalty;  // Penalty for getting reversed

   void InitSniper()
   {
      personality = PERSONALITY_SNIPER;

      // Sniper emphasizes trend alignment and patience
      w_velocity = 0.25;        // Strong focus on velocity
      w_acceleration = 0.15;    // Moderate acceleration
      w_jerk = 0.05;            // Low jerk sensitivity
      w_momentum = 0.20;        // Strong momentum focus
      w_chi = 0.10;             // Moderate chi (prefers trending)
      w_timescaleAlign = 0.15;  // High timescale alignment
      w_regime = 0.05;          // Some regime matching
      w_volatility = 0.05;      // Low volatility focus

      // Higher thresholds = more patient
      signalThreshold = 1.5;    // 1.5σ signal required
      velocityMin = 0.3;        // Need decent velocity
      accelMin = 0.1;           // Small acceleration ok
      chiMax = 1.5;             // Prefers trending (low chi)
      persistenceMin = 3;       // Wait for confirmation

      // Wider stops, longer holds
      trailMultiplier = 2.0;
      stopMultiplier = 2.5;
      targetMultiplier = 3.0;
      timeDecayRate = 0.005;    // Low time pressure

      // Reward: patience pays
      winMultiplier = 1.2;
      lossPenalty = 1.5;
      speedBonus = 0.5;         // Low speed bonus
      patienceBonus = 1.5;      // High patience bonus
      reversalPenalty = 2.0;    // Harsh reversal penalty
   }

   void InitBerserker()
   {
      personality = PERSONALITY_BERSERKER;

      // Berserker emphasizes volatility and quick action
      w_velocity = 0.15;        // Moderate velocity focus
      w_acceleration = 0.25;    // Strong acceleration focus
      w_jerk = 0.15;            // High jerk sensitivity
      w_momentum = 0.10;        // Lower momentum focus
      w_chi = 0.15;             // High chi interest
      w_timescaleAlign = 0.05;  // Low timescale alignment
      w_regime = 0.05;          // Some regime matching
      w_volatility = 0.10;      // High volatility focus

      // Lower thresholds = more aggressive
      signalThreshold = 1.0;    // 1.0σ signal sufficient
      velocityMin = 0.1;        // Any velocity ok
      accelMin = 0.3;           // Need acceleration spike
      chiMax = 3.0;             // Comfortable with high chi
      persistenceMin = 1;       // Quick trigger

      // Tighter stops, quick exits
      trailMultiplier = 1.0;
      stopMultiplier = 1.5;
      targetMultiplier = 1.5;
      timeDecayRate = 0.02;     // High time pressure

      // Reward: speed pays
      winMultiplier = 1.5;
      lossPenalty = 1.2;
      speedBonus = 2.0;         // High speed bonus
      patienceBonus = 0.5;      // Low patience bonus
      reversalPenalty = 1.0;    // Accepts some reversals
   }

   // Calculate sensor vector (normalized 0-1) for RL input
   void CalculateSensorVector(KinematicState &kin, double atr, double &vector[])
   {
      if(ArrayResize(vector, SENSOR_DIM) != SENSOR_DIM)
      {
         Print("ERROR: ArrayResize failed for sensor vector - cannot compute kinematics");
         return;
      }

      // Core kinematics (indices 0-5)
      vector[0] = ClampNormalize(kin.velocity, -2.0, 2.0);
      vector[1] = ClampNormalize(kin.acceleration, -2.0, 2.0);
      vector[2] = ClampNormalize(kin.jerk, -1.0, 1.0);
      vector[3] = ClampNormalize(kin.momentum, -2.0, 2.0);
      vector[4] = ClampNormalize(kin.chi, 0.5, 3.0);
      vector[5] = ClampNormalize(kin.chiZ, -3.0, 3.0);

      // Multi-timescale (indices 6-8)
      vector[6] = ClampNormalize(kin.microVelocity, -2.0, 2.0);
      vector[7] = ClampNormalize(kin.mesoVelocity, -2.0, 2.0);
      vector[8] = ClampNormalize(kin.macroVelocity, -2.0, 2.0);

      // Timescale alignment (index 9)
      double align = 0.0;
      if(kin.microVelocity * kin.mesoVelocity > 0) align += 0.33;
      if(kin.mesoVelocity * kin.macroVelocity > 0) align += 0.33;
      if(kin.microVelocity * kin.macroVelocity > 0) align += 0.34;
      vector[9] = align;

      // State encoding (indices 10-15) - one-hot
      for(int i = 0; i < KINEMATIC_STATES; i++)
         vector[10 + i] = (kin.state == (ENUM_KINEMATIC_STATE)i) ? 1.0 : 0.0;

      // Regime encoding (indices 16-19) - one-hot
      for(int i = 0; i < 4; i++)
         vector[16 + i] = (kin.regime == (ENUM_REGIME)i) ? 1.0 : 0.0;

      // Additional features (indices 20-23)
      vector[20] = kin.stateConfidence;
      vector[21] = ClampNormalize((double)kin.statePersistence, 0, 20);
      vector[22] = ClampNormalize(kin.position, 0, 1);
      vector[23] = ClampNormalize(atr, 0.0001, 0.01);  // ATR normalized
   }

   // Calculate weighted signal strength
   double CalculateSignalStrength(KinematicState &kin, bool isBuy)
   {
      double signal = 0.0;
      int dir = isBuy ? 1 : -1;

      // Velocity component (direction-aware)
      signal += w_velocity * kin.velocity * dir;

      // Acceleration component
      signal += w_acceleration * kin.acceleration * dir;

      // Jerk component
      signal += w_jerk * kin.jerk * dir;

      // Momentum component
      signal += w_momentum * kin.momentum * dir;

      // Chi component (inverse - low chi is good for trends)
      signal += w_chi * (2.0 - kin.chi) * 0.5;

      // Timescale alignment
      double align = 0.0;
      if(isBuy)
      {
         if(kin.microVelocity > 0 && kin.mesoVelocity > 0) align += 0.5;
         if(kin.mesoVelocity > 0 && kin.macroVelocity > 0) align += 0.5;
      }
      else
      {
         if(kin.microVelocity < 0 && kin.mesoVelocity < 0) align += 0.5;
         if(kin.mesoVelocity < 0 && kin.macroVelocity < 0) align += 0.5;
      }
      signal += w_timescaleAlign * align;

      return signal;
   }

   // Check if entry conditions are met
   bool IsEntryValid(KinematicState &kin, double signalZ)
   {
      // Signal threshold
      if(MathAbs(signalZ) < signalThreshold)
         return false;

      // Velocity minimum
      if(MathAbs(kin.velocity) < velocityMin)
         return false;

      // Acceleration minimum (Berserker needs more)
      if(personality == PERSONALITY_BERSERKER)
      {
         if(MathAbs(kin.acceleration) < accelMin)
            return false;
      }

      // Chi maximum (Sniper prefers trending)
      if(personality == PERSONALITY_SNIPER)
      {
         if(kin.chi > chiMax)
            return false;
      }

      // State persistence
      if(kin.statePersistence < persistenceMin)
         return false;

      return true;
   }

private:
   double ClampNormalize(double value, double minVal, double maxVal)
   {
      double range = maxVal - minVal;
      if(range <= 0) return 0.5;
      double normalized = (value - minVal) / range;
      return MathMax(0.0, MathMin(1.0, normalized));
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Agent Reward Shaper                                   |
//|                                                                    |
//| Shapes rewards to accelerate learning with divergent profiles     |
//+------------------------------------------------------------------+
struct AgentRewardShaper
{
   AgentSensorProfile profile;

   // Calculate shaped reward based on trade outcome
   double ShapeReward(double grossPnL, double friction, int durationMins,
                      double mfe, double mae, KinematicState &entryState,
                      KinematicState &exitState, bool wasReversal)
   {
      double netPnL = grossPnL - friction;
      double reward = netPnL;

      // === Base Win/Loss Shaping ===
      if(netPnL > 0)
      {
         reward *= profile.winMultiplier;

         // Speed bonus (Berserker loves quick wins)
         if(durationMins < 30)
         {
            double speedMult = 1.0 + profile.speedBonus * (30.0 - durationMins) / 30.0;
            reward *= speedMult;
         }

         // Patience bonus (Sniper loves trend riding)
         if(durationMins > 60 && entryState.regime == REGIME_TREND)
         {
            double patienceMult = 1.0 + profile.patienceBonus * MathMin(durationMins / 60.0, 3.0) / 3.0;
            reward *= patienceMult;
         }

         // MFE capture bonus - reward capturing most of the move
         if(mfe > 0)
         {
            double captureRatio = netPnL / mfe;
            if(captureRatio > 0.7)
               reward *= 1.2;
            else if(captureRatio < 0.3)
               reward *= 0.8;  // Penalty for leaving too much on table
         }
      }
      else
      {
         // Loss penalty
         reward *= profile.lossPenalty;

         // Reversal penalty (Sniper hates reversals)
         if(wasReversal)
            reward *= profile.reversalPenalty;

         // MAE penalty - punish deep drawdowns
         if(mae < -mfe && mfe > 0)
         {
            // MAE was worse than MFE was good - bad trade management
            reward *= 1.2;
         }
      }

      // === Time Decay ===
      reward -= durationMins * profile.timeDecayRate;

      // === Regime Alignment Bonus ===
      // Sniper gets bonus for correct regime trades
      if(profile.personality == PERSONALITY_SNIPER)
      {
         if(entryState.regime == REGIME_TREND && netPnL > 0)
            reward *= 1.1;
         if(entryState.regime == REGIME_MEANREV && netPnL < 0)
            reward *= 0.9;  // Extra penalty for wrong regime
      }

      // Berserker gets bonus for explosive entries
      if(profile.personality == PERSONALITY_BERSERKER)
      {
         if(entryState.state == KIN_EXPLOSIVE && netPnL > 0)
            reward *= 1.2;
         if(entryState.state == KIN_ACCELERATING && netPnL > 0)
            reward *= 1.1;
      }

      return reward;
   }

   // Calculate intrinsic reward for exploration (pre-trade)
   double GetExplorationBonus(KinematicState &kin, int tradesInState)
   {
      double bonus = 0.0;

      // Curiosity bonus - reward exploring under-sampled states
      if(tradesInState < 10)
      {
         bonus += 0.1 * (10 - tradesInState);
      }

      // Berserker gets bonus for high-volatility exploration
      if(profile.personality == PERSONALITY_BERSERKER)
      {
         if(kin.chi > 2.0)
            bonus += 0.05 * kin.chi;
         if(kin.state == KIN_EXPLOSIVE)
            bonus += 0.1;
      }

      // Sniper gets bonus for high-confidence states
      if(profile.personality == PERSONALITY_SNIPER)
      {
         if(kin.stateConfidence > 0.8)
            bonus += 0.1;
         if(kin.statePersistence > 5)
            bonus += 0.05;
      }

      return bonus;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Replay Priority Calculator                            |
//|                                                                    |
//| Prioritizes experiences for replay to accelerate learning         |
//+------------------------------------------------------------------+
struct ReplayPriority
{
   double            tdError;          // Temporal difference error
   double            surprise;         // |actual - expected|
   double            rarity;           // How rare is this state?
   double            importance;       // Combined priority score
   ENUM_TRADE_TAG    tag;              // For categorization
   ENUM_AGENT_PERSONALITY agent;

   void Calculate(double expectedReward, double actualReward,
                  KinematicState &state, int stateVisits,
                  ENUM_AGENT_PERSONALITY agentType)
   {
      agent = agentType;

      // TD error (key for prioritized experience replay)
      tdError = MathAbs(actualReward - expectedReward);

      // Surprise factor
      surprise = tdError / (MathAbs(expectedReward) + 0.1);

      // Rarity (inverse of visit count)
      rarity = 1.0 / (stateVisits + 1);

      // Combined importance score
      // High TD error = high priority
      // High surprise = high priority
      // Rare states = high priority
      importance = 0.5 * tdError + 0.3 * surprise + 0.2 * rarity;

      // Boost importance for specific scenarios
      if(actualReward > 0 && state.state == KIN_EXPLOSIVE)
         importance *= 1.5;  // Successful explosive trades are valuable

      if(actualReward < 0 && surprise > 1.0)
         importance *= 1.3;  // Surprising losses are learning opportunities

      // Assign tag based on characteristics
      AssignTag(state, actualReward);
   }

   void AssignTag(KinematicState &state, double reward)
   {
      // Berserker trades
      if(agent == PERSONALITY_BERSERKER)
      {
         if(state.state == KIN_EXPLOSIVE)
            tag = TAG_BERSERKER;
         else if(state.chi > 2.0)
            tag = TAG_MOMENTUM;
         else
            tag = TAG_SCALP;
      }
      // Sniper trades
      else
      {
         if(state.regime == REGIME_TREND)
            tag = TAG_TREND_FOLLOW;
         else if(state.regime == REGIME_MEANREV)
            tag = TAG_MEAN_REVERSION;
         else if(state.state == KIN_REVERTING)
            tag = TAG_REVERSAL;
         else
            tag = TAG_SWING;
      }

      // Override with study tag for high-importance experiences
      if(importance > 1.0)
         tag = TAG_STUDY;
   }

   bool ShouldMarkForReplay()
   {
      // Mark if importance is high enough
      if(importance > 0.5)
         return true;

      // Always mark extreme outcomes
      if(tdError > 2.0)
         return true;

      // Mark rare states
      if(rarity > 0.5)
         return true;

      return false;
   }

   string ToJSON()
   {
      return StringFormat(
         "{\"td\":%.4f,\"surprise\":%.3f,\"rarity\":%.3f,"
         "\"importance\":%.3f,\"tag\":%d,\"agent\":%d}",
         tdError, surprise, rarity, importance, (int)tag, (int)agent);
   }
};

//+------------------------------------------------------------------+
//| CLASS - Kinematic Regime Detector                                 |
//+------------------------------------------------------------------+
class CKinematicRegimeDetector
{
private:
   // History buffers
   double            m_priceHistory[];
   double            m_velocityHistory[];
   double            m_accelHistory[];
   int               m_historySize;
   int               m_historyIdx;
   bool              m_initialized;

   // Running statistics
   WelfordStats      m_velocityStats;
   WelfordStats      m_accelStats;
   WelfordStats      m_chiStats;

   // Current state
   KinematicState    m_state;
   ENUM_KINEMATIC_STATE m_prevState;
   int               m_stateCount[KINEMATIC_STATES];

public:
   CKinematicRegimeDetector()
   {
      m_historySize = MACRO_WINDOW + 10;
      m_historyIdx = 0;
      m_initialized = false;
      m_prevState = KIN_CRUISING;
      if(ArrayResize(m_priceHistory, m_historySize) != m_historySize ||
         ArrayResize(m_velocityHistory, m_historySize) != m_historySize ||
         ArrayResize(m_accelHistory, m_historySize) != m_historySize)
      {
         Print("CRITICAL: ArrayResize failed in CKinematicRegimeDetector - regime detection disabled!");
         m_historySize = 0;  // Mark as unusable
         return;
      }
      ArrayInitialize(m_priceHistory, 0);
      ArrayInitialize(m_velocityHistory, 0);
      ArrayInitialize(m_accelHistory, 0);
      ArrayInitialize(m_stateCount, 0);
      m_velocityStats.Init(100);
      m_accelStats.Init(100);
      m_chiStats.Init(100);
      m_state.Reset();
   }

   void Update(double price, double atr)
   {
      if(atr <= 0) atr = 0.0001;

      // Store price
      int idx = m_historyIdx % m_historySize;
      m_priceHistory[idx] = price;

      // Calculate velocity (normalized by ATR)
      if(m_historyIdx > 0)
      {
         int prevIdx = (m_historyIdx - 1) % m_historySize;
         m_state.velocity = (price - m_priceHistory[prevIdx]) / atr;
         m_velocityHistory[idx] = m_state.velocity;
         m_velocityStats.Update(m_state.velocity);
      }

      // Calculate acceleration
      if(m_historyIdx > 1)
      {
         int prevIdx = (m_historyIdx - 1) % m_historySize;
         m_state.acceleration = m_state.velocity - m_velocityHistory[prevIdx];
         m_accelHistory[idx] = m_state.acceleration;
         m_accelStats.Update(m_state.acceleration);
      }

      // Calculate jerk
      if(m_historyIdx > 2)
      {
         int prevIdx = (m_historyIdx - 1) % m_historySize;
         m_state.jerk = m_state.acceleration - m_accelHistory[prevIdx];
      }

      // Calculate multi-timescale velocities
      m_state.microVelocity = CalculateAverageVelocity(MICRO_WINDOW);
      m_state.mesoVelocity = CalculateAverageVelocity(MESO_WINDOW);
      m_state.macroVelocity = CalculateAverageVelocity(MACRO_WINDOW);

      // Calculate chi (oscillation intensity)
      m_state.chi = CalculateChi();
      m_chiStats.Update(m_state.chi);
      m_state.chiZ = m_chiStats.GetZScore(m_state.chi);

      // Calculate mass (inverse of volatility = inertia)
      double volatility = CalculateVolatility(MESO_WINDOW);
      m_state.mass = 1.0 / (volatility + 0.1);
      m_state.mass = MathMin(m_state.mass, 5.0);

      // Calculate momentum
      m_state.momentum = m_state.mass * m_state.velocity;

      // Normalize position (0-1 based on recent range)
      m_state.position = CalculateNormalizedPosition();

      // Classify kinematic state
      ClassifyState();

      // Classify regime
      ClassifyRegime();

      m_historyIdx++;
      m_initialized = (m_historyIdx >= MACRO_WINDOW);
   }

   KinematicState GetState() { return m_state; }
   bool IsReady() { return m_initialized; }
   int GetStateVisitCount(ENUM_KINEMATIC_STATE state)
   {
      int idx = (int)state;
      if(idx < 0 || idx >= KINEMATIC_STATES) return 0;
      return m_stateCount[idx];
   }

private:
   double CalculateAverageVelocity(int window)
   {
      if(m_historyIdx < window) return 0.0;

      double sum = 0.0;
      for(int i = 0; i < window; i++)
      {
         int idx = (m_historyIdx - i) % m_historySize;
         sum += m_velocityHistory[idx];
      }
      return SafeDivide(sum, (double)window, 0.0);
   }

   double CalculateVolatility(int window)
   {
      if(m_historyIdx < window) return 0.01;

      double mean = 0.0;
      for(int i = 0; i < window; i++)
      {
         int idx = (m_historyIdx - i) % m_historySize;
         mean += m_velocityHistory[idx];
      }
      mean = SafeDivide(mean, (double)window, 0.0);

      double sumSq = 0.0;
      for(int i = 0; i < window; i++)
      {
         int idx = (m_historyIdx - i) % m_historySize;
         double diff = m_velocityHistory[idx] - mean;
         sumSq += diff * diff;
      }

      return MathSqrt(SafeDivide(sumSq, (double)window, 0.0));
   }

   double CalculateChi()
   {
      // Chi measures oscillation intensity
      // High chi = price reverting frequently
      // Low chi = trending smoothly
      if(m_historyIdx < MESO_WINDOW) return 1.0;

      int reversals = 0;
      double prevVel = 0;

      for(int i = 0; i < MESO_WINDOW; i++)
      {
         int idx = (m_historyIdx - i) % m_historySize;
         double vel = m_velocityHistory[idx];

         if(i > 0 && vel * prevVel < 0)
            reversals++;

         prevVel = vel;
      }

      // Normalize: 0 reversals = chi of 0.5, many reversals = high chi
      return 0.5 + SafeDivide((double)reversals, (double)MESO_WINDOW, 0.0) * 2.0;
   }

   double CalculateNormalizedPosition()
   {
      if(m_historyIdx < MESO_WINDOW) return 0.5;

      double minP = DBL_MAX, maxP = -DBL_MAX;
      double currentP = m_priceHistory[m_historyIdx % m_historySize];

      for(int i = 0; i < MESO_WINDOW; i++)
      {
         int idx = (m_historyIdx - i) % m_historySize;
         double p = m_priceHistory[idx];
         if(p < minP) minP = p;
         if(p > maxP) maxP = p;
      }

      if(maxP <= minP) return 0.5;
      return (currentP - minP) / (maxP - minP);
   }

   void ClassifyState()
   {
      m_prevState = m_state.state;

      // Get z-scores for classification
      double velZ = m_velocityStats.GetZScore(m_state.velocity);
      double accZ = m_accelStats.GetZScore(m_state.acceleration);

      // Classify based on kinematic signatures
      if(MathAbs(accZ) > 2.5)
      {
         m_state.state = KIN_EXPLOSIVE;
         m_state.stateConfidence = MathMin(1.0, MathAbs(accZ) / 3.0);
      }
      else if(m_state.acceleration > 0 && m_state.jerk > 0)
      {
         m_state.state = KIN_ACCELERATING;
         m_state.stateConfidence = MathMin(1.0, accZ * 0.5);
      }
      else if(m_state.acceleration < 0 && m_state.jerk < 0)
      {
         m_state.state = KIN_DECELERATING;
         m_state.stateConfidence = MathMin(1.0, MathAbs(accZ) * 0.5);
      }
      else if(m_state.chiZ > 1.0)
      {
         m_state.state = KIN_OSCILLATING;
         m_state.stateConfidence = MathMin(1.0, m_state.chiZ / 2.0);
      }
      else if(MathAbs(m_state.velocity) < 0.2 && m_state.position > 0.3 && m_state.position < 0.7)
      {
         m_state.state = KIN_REVERTING;
         m_state.stateConfidence = 1.0 - MathAbs(m_state.velocity) * 2.0;
      }
      else
      {
         m_state.state = KIN_CRUISING;
         m_state.stateConfidence = 0.5;
      }

      // Track state persistence
      if(m_state.state == m_prevState)
         m_state.statePersistence++;
      else
         m_state.statePersistence = 1;

      // Update visit counts (with bounds check)
      int stateIdx = (int)m_state.state;
      if(stateIdx >= 0 && stateIdx < KINEMATIC_STATES)
         m_stateCount[stateIdx]++;
   }

   void ClassifyRegime()
   {
      if(!m_initialized)
      {
         m_state.regime = REGIME_CALIBRATING;
         return;
      }

      // Use kinematic state and multi-timescale analysis
      double alignScore = 0.0;

      // Check timescale alignment (all moving same direction = trend)
      if(m_state.microVelocity * m_state.mesoVelocity > 0) alignScore += 0.33;
      if(m_state.mesoVelocity * m_state.macroVelocity > 0) alignScore += 0.33;
      if(m_state.microVelocity * m_state.macroVelocity > 0) alignScore += 0.34;

      // BREAKOUT: Explosive acceleration, strong alignment
      if(m_state.state == KIN_EXPLOSIVE && alignScore > 0.8)
      {
         m_state.regime = REGIME_BREAKOUT;
         return;
      }

      // TREND: High alignment, consistent velocity, low chi
      if(alignScore > 0.7 && m_state.chi < 1.2 && MathAbs(m_state.mesoVelocity) > 0.3)
      {
         m_state.regime = REGIME_TREND;
         return;
      }

      // MEANREV: High chi, oscillating state, velocity mean-reverting
      if(m_state.chi > 1.5 || m_state.state == KIN_OSCILLATING || m_state.state == KIN_REVERTING)
      {
         m_state.regime = REGIME_MEANREV;
         return;
      }

      // CRITICAL: No clear pattern
      m_state.regime = REGIME_CRITICAL;
   }
};

//+------------------------------------------------------------------+
//| GLOBAL INSTANCES - Agent Profiles                                 |
//+------------------------------------------------------------------+
AgentSensorProfile g_sniperProfile;
AgentSensorProfile g_berserkerProfile;
AgentRewardShaper g_sniperReward;
AgentRewardShaper g_berserkerReward;

//+------------------------------------------------------------------+
//| INITIALIZATION                                                    |
//+------------------------------------------------------------------+
void InitAgentProfiles()
{
   g_sniperProfile.InitSniper();
   g_berserkerProfile.InitBerserker();
   g_sniperReward.profile = g_sniperProfile;
   g_berserkerReward.profile = g_berserkerProfile;
}

#endif // VT_KINEMATIC_REGIMES_MQH
