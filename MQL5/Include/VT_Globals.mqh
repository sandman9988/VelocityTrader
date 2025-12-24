//+------------------------------------------------------------------+
//|                                                  VT_Globals.mqh  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|                                Global Variable Declarations       |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"

#ifndef VT_GLOBALS_MQH
#define VT_GLOBALS_MQH

#include <Trade\Trade.mqh>
#include "VT_Definitions.mqh"
#include "VT_RLParameters.mqh"
#include "VT_Structures.mqh"
#include "VT_Predictor.mqh"
#include "VT_CircuitBreaker.mqh"
#include "VT_KinematicRegimes.mqh"

//+------------------------------------------------------------------+
//| STRUCTURE: Physics Engine - Real Kinematic Calculations          |
//|                                                                   |
//| Wraps CKinematicRegimeDetector to provide velocity, acceleration,|
//| jerk, mass, and multi-timescale analysis for regime detection    |
//+------------------------------------------------------------------+
struct PhysicsEngine
{
private:
   CKinematicRegimeDetector* m_detector;
   string                     m_symbol;
   bool                       m_ownsDetector;
   double                     m_lastPrice;

public:
   bool Init(string sym)
   {
      m_symbol = sym;
      m_lastPrice = 0;
      m_ownsDetector = false;

      // Validate symbol
      if(StringLen(sym) == 0)
      {
         Print("ERROR: PhysicsEngine::Init - empty symbol provided");
         m_detector = NULL;
         return false;
      }

      // Attempt to create detector with error handling
      m_detector = new CKinematicRegimeDetector();
      if(m_detector == NULL)
      {
         Print("ERROR: PhysicsEngine::Init - failed to create CKinematicRegimeDetector for ", sym);
         return false;
      }

      m_ownsDetector = true;
      return true;
   }

   void Deinit()
   {
      if(m_ownsDetector && m_detector != NULL)
      {
         delete m_detector;
         m_detector = NULL;
      }
   }

   bool UpdateWithATR(double price, double atr)
   {
      // Validate detector is initialized
      if(m_detector == NULL)
      {
         return false;  // Silently fail if not initialized
      }

      // Validate price is positive and finite
      if(price <= 0 || !MathIsValidNumber(price))
      {
         return false;
      }

      // Validate ATR is positive and finite
      if(atr <= 0 || !MathIsValidNumber(atr))
      {
         return false;
      }

      // Additional sanity check: ATR should not be larger than price
      if(atr > price)
      {
         Print("WARNING: PhysicsEngine::UpdateWithATR - ATR (", atr, ") > price (", price, ") for ", m_symbol);
         atr = price * 0.1;  // Cap ATR at 10% of price
      }

      m_detector.Update(price, atr);
      m_lastPrice = price;
      return true;
   }

   // Legacy Update() for backward compatibility
   bool Update()
   {
      // Validate state
      if(StringLen(m_symbol) == 0)
      {
         return false;
      }

      if(m_detector == NULL)
      {
         return false;
      }

      // Get current price with validation
      double price = SymbolInfoDouble(m_symbol, SYMBOL_BID);
      if(price <= 0 || !MathIsValidNumber(price))
      {
         return false;
      }

      // Estimate ATR from recent movement if not provided
      double atr = 0.0;
      if(m_lastPrice > 0 && MathIsValidNumber(m_lastPrice))
      {
         atr = MathAbs(price - m_lastPrice) * 14.0;
      }
      else
      {
         atr = price * 0.001;  // Default 0.1% for first tick
      }

      // Ensure ATR is valid and within reasonable bounds
      atr = MathMax(atr, price * 0.0001);  // Minimum ATR: 0.01% of price
      atr = MathMin(atr, price * 0.5);      // Maximum ATR: 50% of price

      return UpdateWithATR(price, atr);
   }

   bool IsReady()
   {
      return (m_detector != NULL && m_detector.IsReady());
   }

   double GetVelocity()
   {
      if(m_detector == NULL) return 0.0;
      return m_detector.GetState().velocity;
   }

   double GetAcceleration()
   {
      if(m_detector == NULL) return 0.0;
      return m_detector.GetState().acceleration;
   }

   double GetJerk()
   {
      if(m_detector == NULL) return 0.0;
      return m_detector.GetState().jerk;
   }

   double GetMass()
   {
      if(m_detector == NULL) return 1.0;
      return m_detector.GetState().mass;
   }

   double GetMomentum()
   {
      if(m_detector == NULL) return 0.0;
      return m_detector.GetState().momentum;
   }

   double GetMicroVelocity()
   {
      if(m_detector == NULL) return 0.0;
      return m_detector.GetState().microVelocity;
   }

   double GetMesoVelocity()
   {
      if(m_detector == NULL) return 0.0;
      return m_detector.GetState().mesoVelocity;
   }

   double GetMacroVelocity()
   {
      if(m_detector == NULL) return 0.0;
      return m_detector.GetState().macroVelocity;
   }

   ENUM_KINEMATIC_STATE GetKinematicState()
   {
      if(m_detector == NULL) return KIN_CRUISING;
      return m_detector.GetState().state;
   }

   double GetStateConfidence()
   {
      if(m_detector == NULL) return 0.0;
      return m_detector.GetState().stateConfidence;
   }

   int GetStatePersistence()
   {
      if(m_detector == NULL) return 0;
      return m_detector.GetState().statePersistence;
   }

   KinematicState GetFullState()
   {
      if(m_detector == NULL)
      {
         KinematicState empty;
         empty.Reset();
         return empty;
      }
      return m_detector.GetState();
   }

   int GetStateVisitCount(ENUM_KINEMATIC_STATE kinState)
   {
      if(m_detector == NULL) return 0;
      return m_detector.GetStateVisitCount(kinState);
   }

   double GetChi()
   {
      if(m_detector == NULL) return 1.0;
      return m_detector.GetState().chi;
   }

   double GetChiZ()
   {
      if(m_detector == NULL) return 0.0;
      return m_detector.GetState().chiZ;
   }

   ENUM_REGIME GetRegime()
   {
      if(m_detector == NULL) return REGIME_CALIBRATING;
      return m_detector.GetState().regime;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: SymC Data - Regime Detection Interface                |
//|                                                                   |
//| Provides chi (oscillation), regime classification, and price     |
//| deviation metrics derived from the PhysicsEngine kinematic state |
//+------------------------------------------------------------------+
struct SymCData
{
   double chi;
   double chiZ;
   double priceDeviation;
   ENUM_REGIME regime;

   void Init()
   {
      chi = 1.0;
      chiZ = 0;
      priceDeviation = 0;
      regime = REGIME_CALIBRATING;
   }

   double GetChi() { return chi; }
   double GetChiZ() { return chiZ; }
   double GetPriceDeviation() { return priceDeviation; }
   ENUM_REGIME GetRegime() { return regime; }

   int GetRegimeIndex()
   {
      if(regime == REGIME_BREAKOUT) return 0;
      if(regime == REGIME_TREND) return 1;
      if(regime == REGIME_MEANREV) return 2;
      return -1;
   }

   bool Update(double mass, double flow, double price, PhysicsEngine &phys)
   {
      // Validate inputs
      if(!MathIsValidNumber(mass) || !MathIsValidNumber(flow) || !MathIsValidNumber(price))
      {
         return false;
      }

      if(price <= 0)
      {
         return false;
      }

      // Get kinematic state from physics engine with validation
      if(!phys.IsReady())
      {
         // Use defaults when physics engine is not ready
         chi = 1.0;
         chiZ = 0.0;
         priceDeviation = 0.0;
         regime = REGIME_CALIBRATING;
         return false;
      }

      KinematicState kinState = phys.GetFullState();

      // Update chi and chiZ from kinematic analysis with validation
      chi = MathIsValidNumber(kinState.chi) ? kinState.chi : 1.0;
      chiZ = MathIsValidNumber(kinState.chiZ) ? kinState.chiZ : 0.0;

      // Price deviation: normalized position converted to centered scale
      // position 0.5 = neutral, <0.5 = oversold, >0.5 = overbought
      double position = MathIsValidNumber(kinState.position) ? kinState.position : 0.5;
      position = MathMax(0.0, MathMin(1.0, position));  // Clamp to [0, 1]
      priceDeviation = (position - 0.5) * 2.0;

      // Regime from kinematic classification
      regime = kinState.regime;
      return true;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Symbol Info                                            |
//+------------------------------------------------------------------+
struct SymbolInfo
{
   string         name;
   BrokerSpec     spec;
   ENUM_ASSET_TYPE assetType;
   bool           typeAllowed;
   bool           initialized;
   bool           halted;
   int            atrHandle;
   double         atr;
   double         avgATR;
   double         dailyPnL;
   int            consLosses;
   PhysicsEngine  physics;
   SymCData       symc;

   void Clear()
   {
      name = "";
      initialized = false;
      halted = false;
      atrHandle = INVALID_HANDLE;
      atr = 0;
      avgATR = 0;
      dailyPnL = 0;
      consLosses = 0;
   }
};

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+
// Trade object
CTrade g_trade;

// RL Parameters
RLParameters g_rlParams;

// Agents
TradingAgent g_sniper;
TradingAgent g_berserker;

// Systems
ProbabilityPredictor g_predictor;
StatisticalGate g_statGate;
CircuitBreaker g_breaker;
SystemStatus g_status;

// Symbol management
SymbolInfo g_symbols[MAX_SYMBOLS];
int g_symbolCount = 0;

// Velocity ranking
VelocityRank g_ranking[MAX_SYMBOLS];
int g_rankCount = 0;

// Position management
PositionData g_positions[MAX_POSITIONS];
int g_posCount = 0;

// Session tracking
double g_sessionEquity = 0;
datetime g_sessionStart = 0;

// Period statistics
PeriodStats g_dayStats;
PeriodStats g_weekStats;
PeriodStats g_monthStats;
PeriodStats g_totalStats;

// Excursion tracking
ExcursionStats g_sniperExcursion;
ExcursionStats g_berserkerExcursion;

// HUD
string g_hudObjects[];
int g_hudCount = 0;
int g_hudTab = 0;
datetime g_hudLastTabSwitch = 0;

#endif // VT_GLOBALS_MQH
