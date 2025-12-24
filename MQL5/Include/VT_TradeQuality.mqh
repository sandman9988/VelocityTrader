//+------------------------------------------------------------------+
//|                                              VT_TradeQuality.mqh |
//|                                       VelocityTrader Framework   |
//|                 Trade Quality Metrics & Classification           |
//+------------------------------------------------------------------+
#ifndef VT_TRADE_QUALITY_MQH
#define VT_TRADE_QUALITY_MQH

#property copyright "VelocityTrader"
#property strict

#include "VT_Logger.mqh"

//+------------------------------------------------------------------+
//| CONSTANTS                                                         |
//+------------------------------------------------------------------+
#ifndef M_PI
   #define M_PI 3.14159265358979323846
#endif

//+------------------------------------------------------------------+
//| CONSTANTS - Quality Thresholds                                    |
//+------------------------------------------------------------------+
#define QUALITY_EXCELLENT    0.8
#define QUALITY_GOOD         0.6
#define QUALITY_AVERAGE      0.4
#define QUALITY_POOR         0.2

//+------------------------------------------------------------------+
//| STRUCTURE - Quadratic Regression Result                           |
//+------------------------------------------------------------------+
struct QuadraticRegression
{
   double            a;                // Quadratic coefficient (curvature)
   double            b;                // Linear coefficient (slope)
   double            c;                // Constant (intercept)
   double            rSquared;         // Coefficient of determination (0-1)
   double            stdError;         // Standard error of regression
   double            currentDeviation; // Current price deviation from regression
   double            predictedValue;   // Predicted price at current bar
   double            curvature;        // Sign: +1 concave up, -1 concave down
   double            vertex;           // X-value of vertex (turning point)
   int               barsToVertex;     // Bars until predicted turning point
   bool              isValid;          // Regression calculated successfully

   void Reset()
   {
      a = 0.0;
      b = 0.0;
      c = 0.0;
      rSquared = 0.0;
      stdError = 0.0;
      currentDeviation = 0.0;
      predictedValue = 0.0;
      curvature = 0.0;
      vertex = 0.0;
      barsToVertex = 0;
      isValid = false;
   }

   // Is the regression fit reliable?
   bool IsReliable() { return isValid && rSquared >= 0.7; }

   // Is trend curving (parabolic)?
   bool IsCurved() { return isValid && MathAbs(a) > 0.0001; }

   // Is price above/below regression line?
   double GetDeviationATR(double atr)
   {
      return (atr > 0) ? currentDeviation / atr : 0.0;
   }

   string ToJSON()
   {
      return StringFormat(
         "{\"a\":%.6f,\"b\":%.4f,\"c\":%.2f,\"r2\":%.3f,"
         "\"dev\":%.2f,\"curve\":%+.0f,\"vertex\":%d}",
         a, b, c, rSquared, currentDeviation, curvature, barsToVertex);
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Entropy Analysis for Cycle Detection                  |
//+------------------------------------------------------------------+
struct EntropyAnalysis
{
   double            shannonEntropy;   // Shannon entropy of returns (bits)
   double            normalizedEntropy; // Normalized 0-1 (vs max entropy)
   double            cycleLength;      // Detected cycle length in bars
   double            cyclePhase;       // Current phase in cycle (0-2π)
   double            dominantFreq;     // Dominant frequency (FFT)
   double            cycleStrength;    // Confidence in cycle detection
   bool              isLowEntropy;     // Ordered/trending market
   bool              isHighEntropy;    // Random/choppy market
   bool              atCycleTrough;    // Near cycle low
   bool              atCyclePeak;      // Near cycle high
   bool              isValid;

   void Reset()
   {
      shannonEntropy = 0.0;
      normalizedEntropy = 0.5;
      cycleLength = 0.0;
      cyclePhase = 0.0;
      dominantFreq = 0.0;
      cycleStrength = 0.0;
      isLowEntropy = false;
      isHighEntropy = false;
      atCycleTrough = false;
      atCyclePeak = false;
      isValid = false;
   }

   // Low entropy = predictable trends
   bool IsTrending() { return isValid && normalizedEntropy < 0.4; }

   // High entropy = random walk / choppy
   bool IsChoppy() { return isValid && normalizedEntropy > 0.7; }

   // Cycle is reliable enough to trade
   bool IsCycleReliable() { return isValid && cycleStrength >= 0.6; }

   string ToJSON()
   {
      return StringFormat(
         "{\"entropy\":%.3f,\"norm\":%.2f,\"cycle\":%.1f,"
         "\"phase\":%.2f,\"strength\":%.2f}",
         shannonEntropy, normalizedEntropy, cycleLength,
         cyclePhase, cycleStrength);
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - VPIN (Volume-synchronized Probability of Informed Trading)
//| Measures order flow toxicity - likelihood of informed trading      |
//+------------------------------------------------------------------+
struct VPINAnalysis
{
   double            vpin;             // VPIN value (0-1)
   double            vpinMA;           // Moving average of VPIN
   double            vpinStdDev;       // Std dev of VPIN
   double            buyVolume;        // Aggregated buy volume
   double            sellVolume;       // Aggregated sell volume
   double            volumeImbalance;  // |buy - sell| / (buy + sell)
   int               bucketsUsed;      // Number of volume buckets
   bool              highToxicity;     // VPIN above threshold
   bool              risingToxicity;   // VPIN trending up
   bool              isValid;

   void Reset()
   {
      vpin = 0.0;
      vpinMA = 0.0;
      vpinStdDev = 0.0;
      buyVolume = 0.0;
      sellVolume = 0.0;
      volumeImbalance = 0.0;
      bucketsUsed = 0;
      highToxicity = false;
      risingToxicity = false;
      isValid = false;
   }

   // High VPIN = informed traders active, risky for retail
   bool IsHighRisk() { return isValid && vpin >= 0.7; }

   // VPIN trending up = increasing toxicity
   bool IsRising() { return isValid && risingToxicity; }

   // Low VPIN = retail-friendly environment
   bool IsLowRisk() { return isValid && vpin <= 0.3; }

   string ToJSON()
   {
      return StringFormat(
         "{\"vpin\":%.3f,\"ma\":%.3f,\"imbalance\":%.2f,"
         "\"toxic\":%s,\"rising\":%s}",
         vpin, vpinMA, volumeImbalance,
         highToxicity ? "true" : "false",
         risingToxicity ? "true" : "false");
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Entry Quality Metrics                                 |
//+------------------------------------------------------------------+
struct EntryQuality
{
   // Trend Alignment
   double            trendScore;       // 0-1: MA alignment, ADX direction
   bool              withTrend;        // Trading with dominant trend
   int               maAlignment;      // How many MAs aligned (-3 to +3)

   // Momentum
   double            momentumScore;    // 0-1: RSI/momentum strength
   double            rsiValue;         // Raw RSI at entry
   double            momentumSlope;    // Rate of change

   // Breakout Quality
   double            breakoutScore;    // 0-1: S/R break quality
   double            breakoutStrength; // How far past level
   bool              volumeConfirm;    // Volume spike on break
   int               retests;          // Number of level retests before break

   // Volatility Context
   double            volatilityScore;  // 0-1: appropriate volatility
   double            atrRatio;         // Current ATR vs average
   bool              inRange;          // Was market ranging

   // Price Action
   double            priceActionScore; // 0-1: candle patterns
   bool              pinBar;           // Pin bar / rejection
   bool              engulfing;        // Engulfing pattern
   bool              insideBar;        // Inside bar breakout

   // Risk/Reward Setup
   double            rrSetupScore;     // 0-1: R:R quality
   double            rrRatio;          // Reward/Risk ratio
   double            slDistance;       // Stop distance in ATR
   double            tpDistance;       // TP distance in ATR

   // Timing
   double            timingScore;      // 0-1: session/timing quality
   bool              sessionOpen;      // At session open
   bool              newsWindow;       // Near news event
   int               minutesToNews;    // Minutes to next news

   // Quadratic Regression Analysis
   QuadraticRegression regression;     // Full regression data
   double            regressionScore;  // 0-1: quality of regression setup
   bool              atRegressionMean; // Price near regression line
   bool              overextended;     // Price far from regression (MR opportunity)
   bool              trendCurving;     // Trend showing curvature (potential reversal)

   // Entropy / Cycle Analysis
   EntropyAnalysis   entropy;          // Full entropy data
   double            entropyScore;     // 0-1: how tradeable is this regime
   bool              inCycle;          // Detected meaningful cycle
   bool              atCycleExtreme;   // At cycle peak/trough

   // VPIN / Order Flow Toxicity
   VPINAnalysis      vpin;             // Full VPIN data
   double            vpinScore;        // 0-1: order flow favorability
   bool              toxicFlow;        // High informed trading risk

   // Composite Score
   double            overallScore;     // Weighted average 0-1

   void Reset()
   {
      trendScore = 0.5;
      withTrend = true;
      maAlignment = 0;

      momentumScore = 0.5;
      rsiValue = 50.0;
      momentumSlope = 0.0;

      breakoutScore = 0.0;
      breakoutStrength = 0.0;
      volumeConfirm = false;
      retests = 0;

      volatilityScore = 0.5;
      atrRatio = 1.0;
      inRange = false;

      priceActionScore = 0.5;
      pinBar = false;
      engulfing = false;
      insideBar = false;

      rrSetupScore = 0.5;
      rrRatio = 1.0;
      slDistance = 1.0;
      tpDistance = 1.0;

      timingScore = 0.5;
      sessionOpen = false;
      newsWindow = false;
      minutesToNews = 999;

      regression.Reset();
      regressionScore = 0.5;
      atRegressionMean = false;
      overextended = false;
      trendCurving = false;

      entropy.Reset();
      entropyScore = 0.5;
      inCycle = false;
      atCycleExtreme = false;

      vpin.Reset();
      vpinScore = 0.5;
      toxicFlow = false;

      overallScore = 0.5;
   }

   void CalculateOverall()
   {
      // Weighted average of all components (with regression, entropy, VPIN)
      overallScore = (
         trendScore * 0.15 +
         momentumScore * 0.10 +
         breakoutScore * 0.10 +
         volatilityScore * 0.07 +
         priceActionScore * 0.10 +
         rrSetupScore * 0.15 +
         timingScore * 0.05 +
         regressionScore * 0.10 +  // Quadratic regression context
         entropyScore * 0.08 +     // Cycle/regime tradability
         vpinScore * 0.10          // Order flow favorability
      );
   }

   string ToJSON()
   {
      return StringFormat(
         "{\"trend\":%.3f,\"mom\":%.3f,\"break\":%.3f,\"vol\":%.3f,"
         "\"pa\":%.3f,\"rr\":%.3f,\"time\":%.3f,\"reg\":%.3f,"
         "\"ent\":%.3f,\"vpin\":%.3f,\"overall\":%.3f,"
         "\"rrRatio\":%.2f,\"rsi\":%.1f,\"atr\":%.2f,"
         "\"regression\":%s,\"entropy\":%s,\"vpinData\":%s}",
         trendScore, momentumScore, breakoutScore, volatilityScore,
         priceActionScore, rrSetupScore, timingScore, regressionScore,
         entropyScore, vpinScore, overallScore,
         rrRatio, rsiValue, atrRatio,
         regression.ToJSON(), entropy.ToJSON(), vpin.ToJSON());
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Exit Quality Metrics                                  |
//+------------------------------------------------------------------+
struct ExitQuality
{
   // Execution
   double            executionScore;   // 0-1: slippage, timing
   double            slippage;         // Pips of slippage
   double            fillTime;         // Seconds to fill

   // Trade Management
   double            managementScore;  // 0-1: trailing, partials
   bool              trailedStop;      // Used trailing stop
   bool              partialClose;     // Took partial profits
   int               adjustments;      // Number of SL/TP adjustments

   // Outcome
   double            outcomeScore;     // 0-1: result vs expectation
   double            capturedMove;     // % of move captured
   double            maxFavorable;     // Max favorable excursion
   double            maxAdverse;       // Max adverse excursion
   double            mfeRatio;         // MFE / MAE ratio

   // Exit Reason
   bool              hitTP;
   bool              hitSL;
   bool              manualClose;
   bool              signalExit;
   bool              timeExit;

   double            overallScore;

   void Reset()
   {
      executionScore = 0.5;
      slippage = 0.0;
      fillTime = 0.0;

      managementScore = 0.5;
      trailedStop = false;
      partialClose = false;
      adjustments = 0;

      outcomeScore = 0.5;
      capturedMove = 0.0;
      maxFavorable = 0.0;
      maxAdverse = 0.0;
      mfeRatio = 1.0;

      hitTP = false;
      hitSL = false;
      manualClose = false;
      signalExit = false;
      timeExit = false;

      overallScore = 0.5;
   }

   void CalculateOverall()
   {
      overallScore = (
         executionScore * 0.20 +
         managementScore * 0.30 +
         outcomeScore * 0.50
      );
   }

   string ToJSON()
   {
      return StringFormat(
         "{\"exec\":%.3f,\"mgmt\":%.3f,\"outcome\":%.3f,\"overall\":%.3f,"
         "\"mfe\":%.2f,\"mae\":%.2f,\"captured\":%.1f%%,\"slip\":%.1f}",
         executionScore, managementScore, outcomeScore, overallScore,
         maxFavorable, maxAdverse, capturedMove * 100, slippage);
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Complete Trade Quality Record                         |
//+------------------------------------------------------------------+
struct TradeQualityRecord
{
   ulong             ticket;
   string            symbol;
   datetime          entryTime;
   datetime          exitTime;
   ENUM_TRADE_TAG    autoTag;          // Auto-detected tag
   ENUM_TRADE_TAG    manualTag;        // User-assigned tag

   EntryQuality      entry;
   ExitQuality       exit;

   double            profitPips;
   double            profitPercent;
   double            holdingHours;
   int               holdingBars;

   double            totalScore;       // Combined entry + exit

   void Reset()
   {
      ticket = 0;
      symbol = "";
      entryTime = 0;
      exitTime = 0;
      autoTag = TAG_NONE;
      manualTag = TAG_NONE;

      entry.Reset();
      exit.Reset();

      profitPips = 0.0;
      profitPercent = 0.0;
      holdingHours = 0.0;
      holdingBars = 0;

      totalScore = 0.5;
   }

   void CalculateTotalScore()
   {
      entry.CalculateOverall();
      exit.CalculateOverall();

      // Weight entry higher for learning what to look for
      totalScore = entry.overallScore * 0.6 + exit.overallScore * 0.4;
   }

   string ToJSON()
   {
      return StringFormat(
         "{\"ticket\":%I64u,\"symbol\":\"%s\",\"tag\":%d,"
         "\"entry\":%s,\"exit\":%s,"
         "\"profit\":%.2f,\"hours\":%.1f,\"total\":%.3f}",
         ticket, symbol, (int)autoTag,
         entry.ToJSON(), exit.ToJSON(),
         profitPips, holdingHours, totalScore);
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Classification Thresholds                             |
//+------------------------------------------------------------------+
struct ClassificationThresholds
{
   // Berserker: High risk, aggressive, counter-trend or extreme vol
   double            berserkerMinVol;        // Min volatility ratio
   double            berserkerMaxRR;         // Very high R:R
   double            berserkerMinMomentum;   // Strong momentum
   bool              berserkerCounterTrend;  // Against main trend

   // Breakout: S/R break with confirmation
   double            breakoutMinStrength;    // Min break strength (ATR)
   double            breakoutMinVolume;      // Volume spike ratio
   int               breakoutMinRetests;     // Level retests

   // Trend: With-trend, aligned MAs
   int               trendMinMAAlign;        // Min MAs aligned
   double            trendMinADX;            // Min ADX
   double            trendMinTrendScore;     // Min trend score

   // Reversal: Counter-trend at extremes
   double            reversalRSIThreshold;   // RSI extreme (>70 or <30)
   bool              reversalDivergence;     // Require divergence
   double            reversalMinPAScore;     // Min price action score

   // Momentum: Strong directional move
   double            momentumMinSlope;       // Min momentum slope
   double            momentumMinRSI;         // RSI above threshold
   double            momentumVolSpike;       // Volume confirmation

   // Scalp: Quick, tight
   double            scalpMaxHoldingMins;    // Max minutes
   double            scalpMaxSLAtr;          // Max SL in ATR

   // Mean Reversion: Price deviation from mean
   double            mrMinDeviation;         // Min deviation from MA (ATR)
   double            mrMaxADX;               // Max ADX (ranging market)
   double            mrRSIExtreme;           // RSI extreme for entry
   double            mrBBWidth;              // Bollinger Band squeeze
   bool              mrRequireBounce;        // Require rejection candle

   // Trend Following: Strong trend, pullback entry
   double            tfMinADX;               // Min ADX for trend strength
   int               tfMinMAAlign;           // Min MA alignment
   double            tfPullbackATR;          // Pullback depth in ATR
   double            tfMinTrendScore;        // Min trend score

   // Quadratic Regression: Curved trend and MR detection
   double            regMinR2;               // Min R² for valid regression
   double            regMRDeviation;         // Deviation ATR for MR signal
   double            regCurvatureMin;        // Min curvature for parabolic
   int               regLookback;            // Lookback period for regression
   double            regOverextended;        // ATR deviation = overextended

   void SetDefaults()
   {
      // Berserker
      berserkerMinVol = 1.5;
      berserkerMaxRR = 3.0;
      berserkerMinMomentum = 0.7;
      berserkerCounterTrend = true;

      // Breakout
      breakoutMinStrength = 0.5;  // 0.5 ATR past level
      breakoutMinVolume = 1.5;    // 150% of average
      breakoutMinRetests = 2;

      // Trend
      trendMinMAAlign = 2;
      trendMinADX = 25.0;
      trendMinTrendScore = 0.6;

      // Reversal
      reversalRSIThreshold = 70.0;
      reversalDivergence = false;
      reversalMinPAScore = 0.6;

      // Momentum
      momentumMinSlope = 0.5;
      momentumMinRSI = 55.0;
      momentumVolSpike = 1.3;

      // Scalp
      scalpMaxHoldingMins = 30.0;
      scalpMaxSLAtr = 0.5;

      // Mean Reversion
      mrMinDeviation = 1.5;       // 1.5 ATR from MA
      mrMaxADX = 25.0;            // Low ADX = ranging
      mrRSIExtreme = 30.0;        // RSI < 30 or > 70
      mrBBWidth = 0.02;           // Tight BB = expecting expansion
      mrRequireBounce = true;     // Need rejection candle

      // Trend Following
      tfMinADX = 25.0;            // Strong trend
      tfMinMAAlign = 2;           // MAs aligned
      tfPullbackATR = 0.5;        // Pullback 0.5-1.5 ATR
      tfMinTrendScore = 0.6;      // Good trend score

      // Quadratic Regression
      regMinR2 = 0.7;             // 70% of variance explained
      regMRDeviation = 1.5;       // 1.5 ATR from regression = MR entry
      regCurvatureMin = 0.0001;   // Min curvature for parabolic detection
      regLookback = 20;           // 20 bars for regression
      regOverextended = 2.0;      // 2.0 ATR = overextended
   }
};

//+------------------------------------------------------------------+
//| CLASS - Trade Quality Analyzer                                    |
//+------------------------------------------------------------------+
class CTradeQualityAnalyzer
{
private:
   ClassificationThresholds m_thresholds;

   // Indicator handles for analysis
   int               m_hATR;
   int               m_hRSI;
   int               m_hADX;
   int               m_hMA_fast;
   int               m_hMA_medium;
   int               m_hMA_slow;

   string            m_currentSymbol;
   ENUM_TIMEFRAMES   m_timeframe;

   // Buffers
   double            m_atr[];
   double            m_rsi[];
   double            m_adx[];
   double            m_maFast[];
   double            m_maMedium[];
   double            m_maSlow[];

   // Tracking
   TradeQualityRecord m_activeRecords[];
   int               m_recordCount;

public:
   //+------------------------------------------------------------------+
   //| Constructor                                                       |
   //+------------------------------------------------------------------+
   CTradeQualityAnalyzer()
   {
      m_thresholds.SetDefaults();
      m_currentSymbol = "";
      m_timeframe = PERIOD_CURRENT;
      m_hATR = INVALID_HANDLE;
      m_hRSI = INVALID_HANDLE;
      m_hADX = INVALID_HANDLE;
      m_hMA_fast = INVALID_HANDLE;
      m_hMA_medium = INVALID_HANDLE;
      m_hMA_slow = INVALID_HANDLE;
      m_recordCount = 0;

      ArraySetAsSeries(m_atr, true);
      ArraySetAsSeries(m_rsi, true);
      ArraySetAsSeries(m_adx, true);
      ArraySetAsSeries(m_maFast, true);
      ArraySetAsSeries(m_maMedium, true);
      ArraySetAsSeries(m_maSlow, true);
   }

   //+------------------------------------------------------------------+
   //| Initialize for symbol                                             |
   //+------------------------------------------------------------------+
   bool Init(string symbol, ENUM_TIMEFRAMES tf = PERIOD_CURRENT)
   {
      m_currentSymbol = symbol;
      m_timeframe = tf;

      // Create indicator handles
      m_hATR = iATR(symbol, tf, 14);
      m_hRSI = iRSI(symbol, tf, 14, PRICE_CLOSE);
      m_hADX = iADX(symbol, tf, 14);
      m_hMA_fast = iMA(symbol, tf, 10, 0, MODE_EMA, PRICE_CLOSE);
      m_hMA_medium = iMA(symbol, tf, 20, 0, MODE_EMA, PRICE_CLOSE);
      m_hMA_slow = iMA(symbol, tf, 50, 0, MODE_SMA, PRICE_CLOSE);

      if(m_hATR == INVALID_HANDLE || m_hRSI == INVALID_HANDLE)
         return false;

      return true;
   }

   //+------------------------------------------------------------------+
   //| Deinitialize                                                      |
   //+------------------------------------------------------------------+
   void Deinit()
   {
      if(m_hATR != INVALID_HANDLE) IndicatorRelease(m_hATR);
      if(m_hRSI != INVALID_HANDLE) IndicatorRelease(m_hRSI);
      if(m_hADX != INVALID_HANDLE) IndicatorRelease(m_hADX);
      if(m_hMA_fast != INVALID_HANDLE) IndicatorRelease(m_hMA_fast);
      if(m_hMA_medium != INVALID_HANDLE) IndicatorRelease(m_hMA_medium);
      if(m_hMA_slow != INVALID_HANDLE) IndicatorRelease(m_hMA_slow);
   }

   //+------------------------------------------------------------------+
   //| Refresh indicator buffers                                         |
   //+------------------------------------------------------------------+
   void RefreshIndicators(int count = 10)
   {
      CopyBuffer(m_hATR, 0, 0, count, m_atr);
      CopyBuffer(m_hRSI, 0, 0, count, m_rsi);
      CopyBuffer(m_hADX, 0, 0, count, m_adx);
      CopyBuffer(m_hMA_fast, 0, 0, count, m_maFast);
      CopyBuffer(m_hMA_medium, 0, 0, count, m_maMedium);
      CopyBuffer(m_hMA_slow, 0, 0, count, m_maSlow);
   }

   //+------------------------------------------------------------------+
   //| Calculate Quadratic Regression: y = ax² + bx + c                  |
   //| Uses least squares fitting on price data                          |
   //+------------------------------------------------------------------+
   void CalculateQuadraticRegression(string symbol, int lookback,
                                      QuadraticRegression &reg)
   {
      reg.Reset();

      if(lookback < 5)
         return;

      // Get price data (close prices)
      double prices[];
      ArraySetAsSeries(prices, true);
      int copied = CopyClose(symbol, m_timeframe, 0, lookback, prices);

      if(copied < lookback)
         return;

      // Least squares for quadratic: y = ax² + bx + c
      // Using normal equations: [n, Σx, Σx²] [c]   [Σy]
      //                         [Σx, Σx², Σx³] [b] = [Σxy]
      //                         [Σx², Σx³, Σx⁴] [a]   [Σx²y]

      double sumX = 0, sumX2 = 0, sumX3 = 0, sumX4 = 0;
      double sumY = 0, sumXY = 0, sumX2Y = 0;
      int n = lookback;

      for(int i = 0; i < n; i++)
      {
         // x is the bar index (0 = current, 1 = previous, etc.)
         double x = (double)i;
         double y = prices[i];

         sumX += x;
         sumX2 += x * x;
         sumX3 += x * x * x;
         sumX4 += x * x * x * x;
         sumY += y;
         sumXY += x * y;
         sumX2Y += x * x * y;
      }

      // Solve 3x3 system using Cramer's rule
      // Matrix:
      // |n     sumX   sumX2 |   |c|   |sumY  |
      // |sumX  sumX2  sumX3 | * |b| = |sumXY |
      // |sumX2 sumX3  sumX4 |   |a|   |sumX2Y|

      double det = n * (sumX2 * sumX4 - sumX3 * sumX3)
                 - sumX * (sumX * sumX4 - sumX3 * sumX2)
                 + sumX2 * (sumX * sumX3 - sumX2 * sumX2);

      if(MathAbs(det) < 1e-10)
         return;  // Singular matrix

      // Calculate c (constant) - DEFENSE IN DEPTH: SafeDivide even with det check
      double detC = sumY * (sumX2 * sumX4 - sumX3 * sumX3)
                  - sumX * (sumXY * sumX4 - sumX3 * sumX2Y)
                  + sumX2 * (sumXY * sumX3 - sumX2 * sumX2Y);
      reg.c = SafeDivide(detC, det, 0.0);

      // Calculate b (linear coefficient)
      double detB = n * (sumXY * sumX4 - sumX3 * sumX2Y)
                  - sumY * (sumX * sumX4 - sumX3 * sumX2)
                  + sumX2 * (sumX * sumX2Y - sumX2 * sumXY);
      reg.b = SafeDivide(detB, det, 0.0);

      // Calculate a (quadratic coefficient)
      double detA = n * (sumX2 * sumX2Y - sumXY * sumX3)
                  - sumX * (sumX * sumX2Y - sumXY * sumX2)
                  + sumY * (sumX * sumX3 - sumX2 * sumX2);
      reg.a = SafeDivide(detA, det, 0.0);

      // Calculate R² (coefficient of determination)
      double meanY = SafeDivide(sumY, (double)n, 0.0);
      double ssTot = 0, ssRes = 0;

      for(int i = 0; i < n; i++)
      {
         double x = (double)i;
         double predicted = reg.a * x * x + reg.b * x + reg.c;
         double actual = prices[i];

         ssTot += (actual - meanY) * (actual - meanY);
         ssRes += (actual - predicted) * (actual - predicted);
      }

      reg.rSquared = (ssTot > 0) ? 1.0 - (ssRes / ssTot) : 0.0;

      // Standard error
      reg.stdError = (n > 3) ? MathSqrt(ssRes / (n - 3)) : 0.0;

      // Current predicted value (at x=0, the current bar)
      reg.predictedValue = reg.c;  // At x=0: y = c

      // Current deviation from regression
      reg.currentDeviation = prices[0] - reg.predictedValue;

      // Curvature sign: +a = concave up (U-shape), -a = concave down
      reg.curvature = (reg.a > 0) ? 1.0 : ((reg.a < 0) ? -1.0 : 0.0);

      // Vertex (turning point): x = -b / (2a)
      if(MathAbs(reg.a) > 1e-10)
      {
         reg.vertex = -reg.b / (2 * reg.a);
         reg.barsToVertex = (int)MathRound(reg.vertex);

         // Negative = vertex in past, Positive = vertex in future
         if(reg.barsToVertex < 0)
            reg.barsToVertex = 0;  // Already past the turn
      }
      else
      {
         reg.vertex = 0;
         reg.barsToVertex = 0;
      }

      reg.isValid = true;
   }

   //+------------------------------------------------------------------+
   //| Analyze regression for entry quality scoring                      |
   //+------------------------------------------------------------------+
   void AnalyzeRegression(string symbol, bool isBuy, double currentPrice,
                          double atr, EntryQuality &quality)
   {
      CalculateQuadraticRegression(symbol, m_thresholds.regLookback,
                                   quality.regression);

      if(!quality.regression.isValid)
      {
         quality.regressionScore = 0.5;
         return;
      }

      QuadraticRegression &reg = quality.regression;
      double devATR = (atr > 0) ? MathAbs(reg.currentDeviation) / atr : 0;

      // === Mean Reversion Setup Detection ===
      // Price far from regression line = potential MR entry
      if(devATR >= m_thresholds.regMRDeviation)
      {
         quality.overextended = true;

         // Good MR setup: price extended + curving back
         bool curvingBack = (reg.currentDeviation > 0 && reg.curvature < 0) ||
                            (reg.currentDeviation < 0 && reg.curvature > 0);

         if(curvingBack)
            quality.regressionScore = 0.85;  // Strong MR signal
         else
            quality.regressionScore = 0.65;  // Overextended but no curve yet
      }
      // === At Regression Mean ===
      else if(devATR < 0.5)
      {
         quality.atRegressionMean = true;

         // Good for trend continuation if curving in trade direction
         bool curvingWithTrade = (isBuy && reg.curvature > 0) ||
                                 (!isBuy && reg.curvature < 0);

         if(curvingWithTrade && reg.rSquared >= m_thresholds.regMinR2)
            quality.regressionScore = 0.75;  // Good trend entry
         else
            quality.regressionScore = 0.5;   // Neutral
      }
      // === Moderate Deviation ===
      else
      {
         quality.regressionScore = 0.6;  // Okay but not ideal
      }

      // === Trend Curving Detection (potential reversal) ===
      if(MathAbs(reg.a) >= m_thresholds.regCurvatureMin)
      {
         quality.trendCurving = true;

         // If trend is curving against our trade direction, penalize
         bool curveAgainstTrade = (isBuy && reg.curvature < 0 && reg.b > 0) ||
                                  (!isBuy && reg.curvature > 0 && reg.b < 0);

         if(curveAgainstTrade && reg.rSquared >= m_thresholds.regMinR2)
         {
            // Trend losing momentum - risky entry
            quality.regressionScore *= 0.7;
         }
      }

      // === Bonus for high R² (reliable regression) ===
      if(reg.rSquared >= 0.85)
         quality.regressionScore = MathMin(1.0, quality.regressionScore + 0.1);

      // === Penalty for low R² (unreliable) ===
      if(reg.rSquared < 0.5)
         quality.regressionScore *= 0.8;
   }

   //+------------------------------------------------------------------+
   //| Calculate Shannon Entropy for Cycle Detection                     |
   //| Lower entropy = more predictable (trending)                       |
   //| Higher entropy = more random (choppy)                             |
   //+------------------------------------------------------------------+
   void CalculateEntropy(string symbol, int lookback, EntropyAnalysis &ent)
   {
      ent.Reset();

      if(lookback < 10)
         return;

      // Get price returns
      double closes[];
      ArraySetAsSeries(closes, true);
      int copied = CopyClose(symbol, m_timeframe, 0, lookback + 1, closes);

      if(copied < lookback + 1)
         return;

      // Calculate returns
      double returns[];
      ArrayResize(returns, lookback);

      for(int i = 0; i < lookback; i++)
         returns[i] = SafeDivide(closes[i] - closes[i + 1], closes[i + 1], 0.0) * 100.0;

      // Bin returns into categories for Shannon entropy
      int numBins = 10;
      double binWidth = 0.1;  // 0.1% per bin
      int bins[];
      ArrayResize(bins, numBins);
      ArrayInitialize(bins, 0);

      for(int i = 0; i < lookback; i++)
      {
         int binIdx = (int)MathFloor(returns[i] / binWidth) + numBins / 2;
         binIdx = MathMax(0, MathMin(numBins - 1, binIdx));
         bins[binIdx]++;
      }

      // Calculate Shannon entropy: H = -Σ p(x) * log2(p(x))
      double entropy = 0.0;
      for(int i = 0; i < numBins; i++)
      {
         if(bins[i] > 0)
         {
            double p = SafeDivide((double)bins[i], (double)lookback, 0.0);
            if(p > 0) entropy -= p * MathLog(p) / MathLog(2.0);  // log base 2
         }
      }

      ent.shannonEntropy = entropy;
      ent.normalizedEntropy = entropy / MathLog((double)numBins) * MathLog(2.0);

      // Low entropy = trending, high entropy = choppy
      ent.isLowEntropy = (ent.normalizedEntropy < 0.4);
      ent.isHighEntropy = (ent.normalizedEntropy > 0.7);

      // === Simple Cycle Detection via Autocorrelation ===
      // Find dominant cycle by looking for peaks in autocorrelation
      double maxCorr = 0;
      int bestLag = 0;

      for(int lag = 3; lag < lookback / 2; lag++)
      {
         double corr = 0, var1 = 0, var2 = 0;
         double mean = 0;

         for(int i = 0; i < lookback - lag; i++)
            mean += returns[i];
         mean /= (lookback - lag);

         for(int i = 0; i < lookback - lag; i++)
         {
            double x1 = returns[i] - mean;
            double x2 = returns[i + lag] - mean;
            corr += x1 * x2;
            var1 += x1 * x1;
            var2 += x2 * x2;
         }

         if(var1 > 0 && var2 > 0)
         {
            corr /= MathSqrt(var1 * var2);
            if(corr > maxCorr)
            {
               maxCorr = corr;
               bestLag = lag;
            }
         }
      }

      if(maxCorr > 0.3)  // Significant cycle found
      {
         ent.cycleLength = (double)bestLag;
         ent.cycleStrength = maxCorr;

         // Estimate current phase (0 to 2π)
         ent.cyclePhase = SafeDivide(MathMod((double)lookback, ent.cycleLength),
                          ent.cycleLength, 0.0) * 2.0 * M_PI;

         // At cycle extremes?
         ent.atCycleTrough = (ent.cyclePhase > 0.9 * M_PI && ent.cyclePhase < 1.1 * M_PI);
         ent.atCyclePeak = (ent.cyclePhase < 0.1 * M_PI || ent.cyclePhase > 1.9 * M_PI);
      }

      ent.isValid = true;
   }

   //+------------------------------------------------------------------+
   //| Analyze entropy for entry quality scoring                         |
   //+------------------------------------------------------------------+
   void AnalyzeEntropy(string symbol, bool isBuy, EntryQuality &quality)
   {
      CalculateEntropy(symbol, 50, quality.entropy);

      if(!quality.entropy.isValid)
      {
         quality.entropyScore = 0.5;
         return;
      }

      EntropyAnalysis &ent = quality.entropy;

      // === Low entropy = good for trend-following ===
      if(ent.IsTrending())
      {
         if(quality.withTrend)
            quality.entropyScore = 0.85;  // Trending + with trend = excellent
         else
            quality.entropyScore = 0.4;   // Trending but counter = risky
      }
      // === High entropy = avoid or use MR ===
      else if(ent.IsChoppy())
      {
         quality.entropyScore = 0.35;  // Random, hard to trade
      }
      else
      {
         quality.entropyScore = 0.5;   // Neutral regime
      }

      // === Cycle extremes bonus ===
      if(ent.IsCycleReliable())
      {
         quality.inCycle = true;

         // At trough and buying, or at peak and selling
         if((ent.atCycleTrough && isBuy) || (ent.atCyclePeak && !isBuy))
         {
            quality.atCycleExtreme = true;
            quality.entropyScore = MathMin(1.0, quality.entropyScore + 0.15);
         }
         // Wrong side of cycle
         else if((ent.atCyclePeak && isBuy) || (ent.atCycleTrough && !isBuy))
         {
            quality.entropyScore *= 0.7;
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Calculate VPIN (Volume-synchronized Probability of Informed Trading)
   //| High VPIN = informed traders active, toxic for retail             |
   //+------------------------------------------------------------------+
   void CalculateVPIN(string symbol, int bucketCount, double volumePerBucket,
                      VPINAnalysis &vpinData)
   {
      vpinData.Reset();

      if(bucketCount < 10)
         return;

      // Get tick volume data
      long volumes[];
      double closes[];
      ArraySetAsSeries(volumes, true);
      ArraySetAsSeries(closes, true);

      int bars = bucketCount * 5;  // Estimate bars needed
      int copied = CopyTickVolume(symbol, m_timeframe, 0, bars, volumes);
      int copiedClose = CopyClose(symbol, m_timeframe, 0, bars, closes);

      if(copied < 10 || copiedClose < 10)
         return;

      // Calculate average volume per bar for bucket sizing
      double avgVol = 0;
      for(int i = 0; i < copied; i++)
         avgVol += (double)volumes[i];
      avgVol = SafeDivide(avgVol, (double)copied, 1.0);

      // Use 1/N of average daily volume per bucket
      double bucketVol = (volumePerBucket > 0) ? volumePerBucket : avgVol * 10;

      // Classify volume as buy/sell using tick rule
      // Buy = price up, Sell = price down
      double buyVol = 0, sellVol = 0;
      double currentBucketVol = 0;
      double buyBuckets = 0, sellBuckets = 0;
      int numBuckets = 0;

      double vpinHistory[];
      ArrayResize(vpinHistory, bucketCount);

      for(int i = 1; i < MathMin(copied, copiedClose) && numBuckets < bucketCount; i++)
      {
         double vol = (double)volumes[i];
         double priceChange = closes[i - 1] - closes[i];

         // Classify volume using tick rule
         double buyFrac = 0.5;
         if(priceChange > 0)
            buyFrac = MathMin(1.0, 0.5 + MathAbs(priceChange) * 100);
         else if(priceChange < 0)
            buyFrac = MathMax(0.0, 0.5 - MathAbs(priceChange) * 100);

         buyVol += vol * buyFrac;
         sellVol += vol * (1.0 - buyFrac);
         currentBucketVol += vol;

         // Bucket filled
         if(currentBucketVol >= bucketVol)
         {
            buyBuckets += buyVol;
            sellBuckets += sellVol;

            // VPIN for this bucket
            double totalVol = buyVol + sellVol;
            if(totalVol > 0)
            {
               vpinHistory[numBuckets] = MathAbs(buyVol - sellVol) / totalVol;
            }

            numBuckets++;
            buyVol = 0;
            sellVol = 0;
            currentBucketVol = 0;
         }
      }

      if(numBuckets < 5)
         return;

      // Calculate average VPIN over buckets
      double sum = 0, sumSq = 0;
      for(int i = 0; i < numBuckets; i++)
      {
         sum += vpinHistory[i];
         sumSq += vpinHistory[i] * vpinHistory[i];
      }

      vpinData.vpin = SafeDivide(sum, (double)numBuckets, 0.0);
      double variance = SafeDivide(sumSq, (double)numBuckets, 0.0) - vpinData.vpin * vpinData.vpin;
      vpinData.vpinStdDev = MathSqrt(MathMax(0.0, variance));

      // Moving average (recent half)
      double recentSum = 0;
      int halfBuckets = numBuckets / 2;
      for(int i = 0; i < halfBuckets; i++)
         recentSum += vpinHistory[i];
      vpinData.vpinMA = SafeDivide(recentSum, (double)halfBuckets, vpinData.vpin);

      // Store volume data
      vpinData.buyVolume = buyBuckets;
      vpinData.sellVolume = sellBuckets;
      vpinData.volumeImbalance = MathAbs(buyBuckets - sellBuckets) / (buyBuckets + sellBuckets + 1);
      vpinData.bucketsUsed = numBuckets;

      // Toxicity flags
      vpinData.highToxicity = (vpinData.vpin >= 0.6);
      vpinData.risingToxicity = (vpinData.vpinMA > vpinData.vpin * 0.9);

      vpinData.isValid = true;
   }

   //+------------------------------------------------------------------+
   //| Analyze VPIN for entry quality scoring                            |
   //+------------------------------------------------------------------+
   void AnalyzeVPIN(string symbol, EntryQuality &quality)
   {
      CalculateVPIN(symbol, 20, 0, quality.vpin);

      if(!quality.vpin.isValid)
      {
         quality.vpinScore = 0.5;
         return;
      }

      VPINAnalysis &v = quality.vpin;

      // === Low VPIN = retail-friendly, good ===
      if(v.IsLowRisk())
      {
         quality.vpinScore = 0.85;  // Low informed trading, safe
      }
      // === High VPIN = toxic, avoid ===
      else if(v.IsHighRisk())
      {
         quality.vpinScore = 0.25;  // High toxicity
         quality.toxicFlow = true;
      }
      else
      {
         quality.vpinScore = 0.5;   // Normal conditions
      }

      // === Rising toxicity penalty ===
      if(v.IsRising())
      {
         quality.vpinScore *= 0.8;  // Getting worse
      }

      // === Volume imbalance bonus/penalty ===
      // Strong imbalance in our direction is good
      if(v.volumeImbalance > 0.3)
      {
         quality.vpinScore = MathMin(1.0, quality.vpinScore + 0.1);
      }
   }

   //+------------------------------------------------------------------+
   //| Analyze entry quality                                             |
   //+------------------------------------------------------------------+
   void AnalyzeEntry(string symbol, bool isBuy, double entryPrice,
                     double sl, double tp, EntryQuality &quality)
   {
      quality.Reset();

      if(symbol != m_currentSymbol)
         Init(symbol, m_timeframe);

      RefreshIndicators(20);

      double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
      double bid = SymbolInfoDouble(symbol, SYMBOL_BID);

      // === TREND ANALYSIS ===
      if(ArraySize(m_maFast) >= 3 && ArraySize(m_maSlow) >= 3)
      {
         double fast = m_maFast[0];
         double med = m_maMedium[0];
         double slow = m_maSlow[0];

         // Count MA alignment
         int align = 0;
         if(fast > med) align++;
         if(med > slow) align++;
         if(fast > slow) align++;

         if(!isBuy)
            align = -align;

         quality.maAlignment = align;
         quality.withTrend = (isBuy && align > 0) || (!isBuy && align < 0);

         // Trend score: fully aligned = 1.0
         quality.trendScore = MathMin(1.0, MathAbs(align) / 3.0);

         // Bonus for strong trend alignment
         if(MathAbs(align) == 3)
            quality.trendScore = 1.0;
      }

      // === MOMENTUM ===
      if(ArraySize(m_rsi) >= 2)
      {
         quality.rsiValue = m_rsi[0];

         // RSI momentum score
         if(isBuy)
         {
            if(quality.rsiValue > 50 && quality.rsiValue < 70)
               quality.momentumScore = 0.8;  // Sweet spot
            else if(quality.rsiValue < 30)
               quality.momentumScore = 0.3;  // Oversold but risky
            else if(quality.rsiValue > 70)
               quality.momentumScore = 0.4;  // Overbought
            else
               quality.momentumScore = 0.5;
         }
         else
         {
            if(quality.rsiValue < 50 && quality.rsiValue > 30)
               quality.momentumScore = 0.8;
            else if(quality.rsiValue > 70)
               quality.momentumScore = 0.3;
            else if(quality.rsiValue < 30)
               quality.momentumScore = 0.4;
            else
               quality.momentumScore = 0.5;
         }

         // Momentum slope
         quality.momentumSlope = m_rsi[0] - m_rsi[1];
         if((isBuy && quality.momentumSlope > 0) || (!isBuy && quality.momentumSlope < 0))
            quality.momentumScore += 0.1;
      }

      // === VOLATILITY ===
      if(ArraySize(m_atr) >= 10)
      {
         double avgATR = 0;
         for(int i = 0; i < 10; i++)
            avgATR += m_atr[i];
         avgATR /= 10;

         quality.atrRatio = SafeDivide(m_atr[0], avgATR, 1.0);

         // Ideal volatility: 0.8 - 1.5 ATR ratio
         if(quality.atrRatio >= 0.8 && quality.atrRatio <= 1.5)
            quality.volatilityScore = 0.8;
         else if(quality.atrRatio < 0.5 || quality.atrRatio > 2.5)
            quality.volatilityScore = 0.3;  // Too quiet or too wild
         else
            quality.volatilityScore = 0.5;
      }

      // === RISK/REWARD ===
      if(sl > 0 && tp > 0 && point > 0)
      {
         double slPips = MathAbs(entryPrice - sl) / point;
         double tpPips = MathAbs(tp - entryPrice) / point;

         if(slPips > 0)
         {
            quality.rrRatio = tpPips / slPips;

            // Score R:R ratio
            if(quality.rrRatio >= 2.0)
               quality.rrSetupScore = 0.9;
            else if(quality.rrRatio >= 1.5)
               quality.rrSetupScore = 0.7;
            else if(quality.rrRatio >= 1.0)
               quality.rrSetupScore = 0.5;
            else
               quality.rrSetupScore = 0.3;

            // SL/TP distance in ATR
            if(ArraySize(m_atr) > 0 && m_atr[0] > 0)
            {
               quality.slDistance = (slPips * point) / m_atr[0];
               quality.tpDistance = (tpPips * point) / m_atr[0];

               // Penalize very tight or very wide stops
               if(quality.slDistance < 0.5 || quality.slDistance > 3.0)
                  quality.rrSetupScore *= 0.8;
            }
         }
      }

      // === TIMING ===
      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);

      // Session timing
      if((dt.hour >= 8 && dt.hour <= 11) ||   // London open
         (dt.hour >= 13 && dt.hour <= 16))     // NY overlap
      {
         quality.timingScore = 0.8;
         quality.sessionOpen = (dt.hour == 8 || dt.hour == 13);
      }
      else if(dt.hour < 7 || dt.hour > 20)
      {
         quality.timingScore = 0.3;  // Asian session / off hours
      }
      else
      {
         quality.timingScore = 0.5;
      }

      // Friday afternoon penalty
      if(dt.day_of_week == 5 && dt.hour >= 15)
         quality.timingScore *= 0.7;

      // === PRICE ACTION ===
      // Simplified - check for rejection candles
      double open = iOpen(symbol, m_timeframe, 0);
      double high = iHigh(symbol, m_timeframe, 0);
      double low = iLow(symbol, m_timeframe, 0);
      double close = iClose(symbol, m_timeframe, 0);

      double body = MathAbs(close - open);
      double range = high - low;

      if(range > 0)
      {
         double bodyRatio = body / range;

         // Pin bar detection
         if(bodyRatio < 0.3)
         {
            double upperWick = high - MathMax(open, close);
            double lowerWick = MathMin(open, close) - low;

            if(isBuy && lowerWick > range * 0.6)
            {
               quality.pinBar = true;
               quality.priceActionScore = 0.8;
            }
            else if(!isBuy && upperWick > range * 0.6)
            {
               quality.pinBar = true;
               quality.priceActionScore = 0.8;
            }
         }

         // Engulfing check (compare with previous bar)
         double prevOpen = iOpen(symbol, m_timeframe, 1);
         double prevClose = iClose(symbol, m_timeframe, 1);

         if(isBuy && close > open && open < prevClose && close > prevOpen)
         {
            quality.engulfing = true;
            quality.priceActionScore = MathMax(quality.priceActionScore, 0.75);
         }
         else if(!isBuy && close < open && open > prevClose && close < prevOpen)
         {
            quality.engulfing = true;
            quality.priceActionScore = MathMax(quality.priceActionScore, 0.75);
         }
      }

      // === QUADRATIC REGRESSION ===
      double atr = (ArraySize(m_atr) > 0) ? m_atr[0] : 0;
      AnalyzeRegression(symbol, isBuy, entryPrice, atr, quality);

      // === ENTROPY / CYCLE ANALYSIS ===
      AnalyzeEntropy(symbol, isBuy, quality);

      // === VPIN / ORDER FLOW TOXICITY ===
      AnalyzeVPIN(symbol, quality);

      // Calculate overall
      quality.CalculateOverall();
   }

   //+------------------------------------------------------------------+
   //| Classify trade type based on entry quality                        |
   //+------------------------------------------------------------------+
   ENUM_TRADE_TAG ClassifyTrade(EntryQuality &entry, double holdingMins = 0)
   {
      // === BERSERKER ===
      // High volatility, extreme momentum, or counter-trend with conviction
      if(entry.atrRatio >= m_thresholds.berserkerMinVol &&
         entry.momentumScore >= m_thresholds.berserkerMinMomentum &&
         !entry.withTrend)
      {
         return TAG_BERSERKER;
      }

      // Also Berserker if very high R:R (aggressive)
      if(entry.rrRatio >= m_thresholds.berserkerMaxRR &&
         entry.volatilityScore < 0.5)  // Aggressive in uncertain conditions
      {
         return TAG_BERSERKER;
      }

      // === BREAKOUT ===
      if(entry.breakoutScore >= 0.6 &&
         entry.breakoutStrength >= m_thresholds.breakoutMinStrength)
      {
         return TAG_BREAKOUT;
      }

      // === REVERSAL ===
      if(!entry.withTrend &&
         (entry.rsiValue > m_thresholds.reversalRSIThreshold ||
          entry.rsiValue < (100 - m_thresholds.reversalRSIThreshold)) &&
         entry.priceActionScore >= m_thresholds.reversalMinPAScore)
      {
         return TAG_REVERSAL;
      }

      // === SCALP ===
      if(holdingMins > 0 && holdingMins <= m_thresholds.scalpMaxHoldingMins &&
         entry.slDistance <= m_thresholds.scalpMaxSLAtr)
      {
         return TAG_SCALP;
      }

      // === MOMENTUM ===
      if(entry.momentumScore >= 0.7 &&
         MathAbs(entry.momentumSlope) >= m_thresholds.momentumMinSlope &&
         entry.withTrend)
      {
         return TAG_MOMENTUM;
      }

      // === MEAN REVERSION ===
      // Price overextended from regression, curving back
      if(entry.overextended &&
         entry.regression.IsReliable() &&
         entry.rsiValue <= m_thresholds.mrRSIExtreme ||
         entry.rsiValue >= (100 - m_thresholds.mrRSIExtreme))
      {
         // Curving back towards mean?
         if(entry.trendCurving)
            return TAG_MEAN_REVERSION;
      }

      // Also MR if ADX low (ranging) and price at extreme from MA
      if(ArraySize(m_adx) > 0 && m_adx[0] <= m_thresholds.mrMaxADX &&
         entry.overextended)
      {
         return TAG_MEAN_REVERSION;
      }

      // === TREND FOLLOWING ===
      // Strong trend, price at regression mean, curving with trend
      if(entry.atRegressionMean &&
         entry.regression.IsReliable() &&
         entry.trendScore >= m_thresholds.tfMinTrendScore &&
         MathAbs(entry.maAlignment) >= m_thresholds.tfMinMAAlign)
      {
         // Pullback entry into trend
         if(ArraySize(m_adx) > 0 && m_adx[0] >= m_thresholds.tfMinADX)
            return TAG_TREND_FOLLOW;
      }

      // === TREND (SWING) ===
      if(entry.trendScore >= m_thresholds.trendMinTrendScore &&
         MathAbs(entry.maAlignment) >= m_thresholds.trendMinMAAlign)
      {
         return TAG_SWING;
      }

      // === CONSERVATIVE ===
      if(entry.overallScore >= 0.6 &&
         entry.rrRatio >= 1.5 &&
         entry.volatilityScore >= 0.5 &&
         entry.timingScore >= 0.5)
      {
         return TAG_CONSERVATIVE;
      }

      return TAG_NONE;
   }

   //+------------------------------------------------------------------+
   //| Analyze exit quality                                              |
   //+------------------------------------------------------------------+
   void AnalyzeExit(ulong ticket, double profit, double maxFav, double maxAdv,
                    bool hitTP, bool hitSL, ExitQuality &quality)
   {
      quality.Reset();

      quality.hitTP = hitTP;
      quality.hitSL = hitSL;

      // MFE/MAE analysis
      quality.maxFavorable = maxFav;
      quality.maxAdverse = maxAdv;

      if(maxAdv > 0)
         quality.mfeRatio = maxFav / maxAdv;
      else
         quality.mfeRatio = maxFav > 0 ? 10.0 : 1.0;  // No adverse = perfect

      // Outcome score based on MFE capture
      if(maxFav > 0 && profit > 0)
      {
         quality.capturedMove = profit / maxFav;
         if(quality.capturedMove >= 0.8)
            quality.outcomeScore = 0.9;
         else if(quality.capturedMove >= 0.5)
            quality.outcomeScore = 0.7;
         else
            quality.outcomeScore = 0.5;
      }
      else if(profit > 0)
      {
         quality.outcomeScore = 0.6;  // Profitable but unknown MFE
      }
      else
      {
         // Loss - score based on limiting damage
         if(maxAdv > 0 && MathAbs(profit) < maxAdv * 0.5)
            quality.outcomeScore = 0.4;  // Limited damage
         else
            quality.outcomeScore = 0.2;
      }

      // Hit TP is good execution
      if(hitTP)
         quality.outcomeScore = MathMax(quality.outcomeScore, 0.8);

      // Management score
      if(quality.trailedStop || quality.partialClose)
         quality.managementScore = 0.8;
      else if(quality.adjustments > 0)
         quality.managementScore = 0.6;

      quality.CalculateOverall();
   }

   //+------------------------------------------------------------------+
   //| Check if trade is worth marking for replay                        |
   //+------------------------------------------------------------------+
   bool IsWorthMarking(TradeQualityRecord &record)
   {
      // Mark excellent trades for learning what works
      if(record.totalScore >= QUALITY_EXCELLENT)
         return true;

      // Mark Berserker trades (interesting edge cases)
      if(record.autoTag == TAG_BERSERKER)
         return true;

      // Mark trades with very high R:R setup
      if(record.entry.rrRatio >= 3.0)
         return true;

      // Mark trades with good entry but poor exit (learning opportunity)
      if(record.entry.overallScore >= QUALITY_GOOD &&
         record.exit.overallScore < QUALITY_POOR)
         return true;

      // Mark poor entry with good outcome (luck or hidden pattern)
      if(record.entry.overallScore < QUALITY_POOR &&
         record.exit.overallScore >= QUALITY_GOOD)
         return true;

      return false;
   }

   //+------------------------------------------------------------------+
   //| Get quality description                                           |
   //+------------------------------------------------------------------+
   string GetQualityLevel(double score)
   {
      if(score >= QUALITY_EXCELLENT)
         return "Excellent";
      else if(score >= QUALITY_GOOD)
         return "Good";
      else if(score >= QUALITY_AVERAGE)
         return "Average";
      else if(score >= QUALITY_POOR)
         return "Poor";
      else
         return "VeryPoor";
   }

   //+------------------------------------------------------------------+
   //| Create quality record for position                                |
   //+------------------------------------------------------------------+
   void RecordPosition(ulong ticket, TradeQualityRecord &record)
   {
      record.Reset();

      if(!PositionSelectByTicket(ticket))
         return;

      record.ticket = ticket;
      record.symbol = PositionGetString(POSITION_SYMBOL);
      record.entryTime = (datetime)PositionGetInteger(POSITION_TIME);

      double entry = PositionGetDouble(POSITION_PRICE_OPEN);
      double sl = PositionGetDouble(POSITION_SL);
      double tp = PositionGetDouble(POSITION_TP);
      bool isBuy = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);

      // Analyze entry
      AnalyzeEntry(record.symbol, isBuy, entry, sl, tp, record.entry);

      // Classify
      record.autoTag = ClassifyTrade(record.entry);
   }

   //+------------------------------------------------------------------+
   //| Get thresholds for adjustment                                     |
   //+------------------------------------------------------------------+
   ClassificationThresholds GetThresholds()
   {
      return m_thresholds;
   }

   void SetThresholds(ClassificationThresholds &thresh)
   {
      m_thresholds = thresh;
   }
};

//+------------------------------------------------------------------+
//| GLOBAL INSTANCE                                                   |
//+------------------------------------------------------------------+
CTradeQualityAnalyzer g_tradeQuality;

#endif // VT_TRADE_QUALITY_MQH
