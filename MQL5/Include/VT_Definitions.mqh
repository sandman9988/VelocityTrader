//+------------------------------------------------------------------+
//|                                              VT_Definitions.mqh  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|                     Constants, Enumerations, and Color Defines   |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"

#ifndef VT_DEFINITIONS_MQH
#define VT_DEFINITIONS_MQH

//+------------------------------------------------------------------+
//| CONSTANTS                                                         |
//+------------------------------------------------------------------+
#define MAX_SYMBOLS           64
#define MAX_POSITIONS         20
#define ROLLING_WINDOW        20
#define PERSISTENCE_MAGIC     0x56454C37   // "VEL7"
#define PERSISTENCE_VERSION   720

//+------------------------------------------------------------------+
//| HUD TAB CONSTANTS                                                 |
//+------------------------------------------------------------------+
#define TAB_OVERVIEW          0
#define TAB_PERFORMANCE       1
#define TAB_TRAINING          2
#define TAB_PROBABILITY       3
#define TAB_RISK              4
#define TAB_SIGNALS           5
#define TAB_COUNT             6

//+------------------------------------------------------------------+
//| ENUMERATIONS                                                      |
//+------------------------------------------------------------------+
enum ENUM_REGIME
{
   REGIME_BREAKOUT,      // Steep ROC, explosive
   REGIME_TREND,         // Sustained ROC, persistent
   REGIME_MEANREV,       // High chi, oscillating
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
//| SAFETY HELPERS - Defensive Programming                            |
//+------------------------------------------------------------------+

// Safe division - prevents divide by zero
double SafeDivide(double numerator, double denominator, double defaultValue = 0.0)
{
   if(denominator == 0.0 || !MathIsValidNumber(denominator))
      return defaultValue;
   double result = numerator / denominator;
   if(!MathIsValidNumber(result))
      return defaultValue;
   return result;
}

// Safe array index validation
bool IsValidIndex(int index, int arraySize)
{
   return (index >= 0 && index < arraySize);
}

// Safe number validation (not NaN or Infinity)
bool IsValidNumber(double value)
{
   return MathIsValidNumber(value) && value != EMPTY_VALUE;
}

// Normalize lot size to broker specifications
double NormalizeLots(double lots, double volumeMin, double volumeMax, double volumeStep)
{
   if(volumeStep <= 0) volumeStep = 0.01;
   lots = MathFloor(lots / volumeStep) * volumeStep;
   lots = MathMax(lots, volumeMin);
   lots = MathMin(lots, volumeMax);
   return NormalizeDouble(lots, 2);
}

// Clamp value to range
double ClampValue(double value, double minVal, double maxVal)
{
   return MathMax(minVal, MathMin(maxVal, value));
}

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

#endif // VT_DEFINITIONS_MQH
