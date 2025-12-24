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

//+------------------------------------------------------------------+
//| FORWARD DECLARATION: SymC (Physics) - Stub for now               |
//+------------------------------------------------------------------+
struct SymCData
{
   double chi;
   double chiZ;
   double priceDeviation;
   ENUM_REGIME regime;

   void Init() { chi = 1.0; chiZ = 0; priceDeviation = 0; regime = REGIME_CALIBRATING; }
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
   void Update(double mass, double flow, double price, PhysicsEngine &phys) { /* stub */ }
};

//+------------------------------------------------------------------+
//| FORWARD DECLARATION: Physics Engine - Stub for now               |
//+------------------------------------------------------------------+
struct PhysicsEngine
{
   bool ready;
   double velocity;
   double acceleration;
   double mass;

   void Init(string sym) { ready = false; velocity = 0; acceleration = 0; mass = 1.0; }
   void Deinit() { }
   void Update() { ready = true; }
   bool IsReady() { return ready; }
   double GetVelocity() { return velocity; }
   double GetAcceleration() { return acceleration; }
   double GetMass() { return mass; }
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
