//+------------------------------------------------------------------+
//|                                               VT_Correlation.mqh |
//|                                       VelocityTrader Framework   |
//|                 Portfolio Correlation & Risk Management          |
//|                        v7.1.1 (RingBuffer + fixes)               |
//+------------------------------------------------------------------+
#ifndef VT_CORRELATION_MQH
#define VT_CORRELATION_MQH

#property copyright "VelocityTrader"

#include "VT_Performance.mqh"   // For RingBuffer<T>

//+------------------------------------------------------------------+
//| CONSTANTS                                                         |
//+------------------------------------------------------------------+
#define MAX_CORR_SYMBOLS    50
#define CORR_PERIOD         100    // Bars for correlation calculation
#define CORR_UPDATE_TICKS   100    // Update every N ticks

//+------------------------------------------------------------------+
//| STRUCTURE - Symbol Returns Data (RingBuffer version)              |
//+------------------------------------------------------------------+
struct SymbolReturns
{
   string            symbol;
   RingBuffer<double> returnsBuf;   // O(1) ring buffer instead of O(N) shift
   double            mean;
   double            stdDev;
   datetime          lastUpdate;
   bool              valid;         // True if we have enough data

   void Reset()
   {
      symbol = "";
      returnsBuf.Reset();
      mean = 0.0;
      stdDev = 0.0;
      lastUpdate = 0;
      valid = false;
   }

   void Init(string sym, int periods)
   {
      symbol = sym;
      returnsBuf.Init(periods);
      mean = 0.0;
      stdDev = 0.0;
      lastUpdate = 0;
      valid = false;
   }

   void AddReturn(double ret)
   {
      returnsBuf.Add(ret);
      lastUpdate = TimeCurrent();
      valid = (returnsBuf.Count() >= 10);
   }

   int Count() { return returnsBuf.Count(); }

   // Get return at logical index (0 = oldest still in buffer)
   double Get(int i)
   {
      if(returnsBuf.Capacity() == 0) return 0.0;
      return returnsBuf.Get(i);
   }

   // Get oldest aligned index for covariance with another SymbolReturns
   // Returns number of aligned samples available
   int GetOldestAligned(SymbolReturns &other)
   {
      return MathMin(returnsBuf.Count(), other.returnsBuf.Count());
   }

   void CalculateStats()
   {
      int n = returnsBuf.Count();
      if(n < 2)
      {
         mean = 0.0;
         stdDev = 0.0;
         return;
      }

      // Mean
      double sum = 0.0;
      for(int i = 0; i < n; i++)
         sum += returnsBuf.Get(i);
      mean = SafeDivide(sum, (double)n, 0.0);

      // Std Dev
      double sumSq = 0.0;
      for(int i = 0; i < n; i++)
         sumSq += MathPow(returnsBuf.Get(i) - mean, 2);
      stdDev = MathSqrt(SafeDivide(sumSq, (double)n, 0.0));
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Correlation Pair                                      |
//+------------------------------------------------------------------+
struct CorrelationPair
{
   string            symbol1;
   string            symbol2;
   double            correlation;    // -1 to +1
   double            covariance;
   double            beta;           // Beta of sym1 vs sym2
   datetime          lastUpdate;
   bool              isValid;

   void Reset()
   {
      symbol1 = "";
      symbol2 = "";
      correlation = 0.0;
      covariance = 0.0;
      beta = 0.0;
      lastUpdate = 0;
      isValid = false;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Portfolio Exposure                                    |
//+------------------------------------------------------------------+
struct PortfolioExposure
{
   double            totalLong;         // Total long exposure
   double            totalShort;        // Total short exposure
   double            netExposure;       // Net exposure
   double            grossExposure;     // Gross exposure
   double            maxSingleExposure; // Largest single position
   string            maxSymbol;         // Symbol with max exposure
   double            correlatedRisk;    // Risk from correlated positions
   double            diversificationRatio; // Diversification benefit
   datetime          lastUpdate;

   void Reset()
   {
      totalLong = 0.0;
      totalShort = 0.0;
      netExposure = 0.0;
      grossExposure = 0.0;
      maxSingleExposure = 0.0;
      maxSymbol = "";
      correlatedRisk = 0.0;
      diversificationRatio = 1.0;
      lastUpdate = 0;
   }
};

//+------------------------------------------------------------------+
//| CLASS - Correlation Tracker                                       |
//+------------------------------------------------------------------+
class CCorrelationTracker
{
private:
   SymbolReturns     m_symbolData[MAX_CORR_SYMBOLS];
   int               m_symbolCount;

   CorrelationPair   m_correlations[];
   int               m_corrCount;

   double            m_corrMatrix[MAX_CORR_SYMBOLS][MAX_CORR_SYMBOLS];

   PortfolioExposure m_exposure;

   int               m_lookbackPeriod;
   long              m_tickCounter;
   int               m_updateFrequency;

   // Price tracking for returns
   double            m_lastPrices[MAX_CORR_SYMBOLS];

   // Correlation thresholds
   double            m_highCorrThreshold;    // Highly correlated
   double            m_negCorrThreshold;     // Negatively correlated

public:
   //+------------------------------------------------------------------+
   //| Constructor                                                       |
   //+------------------------------------------------------------------+
   CCorrelationTracker()
   {
      m_symbolCount = 0;
      m_corrCount = 0;
      m_lookbackPeriod = CORR_PERIOD;
      m_tickCounter = 0;
      m_updateFrequency = CORR_UPDATE_TICKS;

      m_highCorrThreshold = 0.7;   // Highly correlated
      m_negCorrThreshold = -0.5;   // Negatively correlated

      m_exposure.Reset();

      // Initialize correlation matrix to zero
      for(int i = 0; i < MAX_CORR_SYMBOLS; i++)
      {
         m_lastPrices[i] = 0.0;
         m_symbolData[i].Reset();
         for(int j = 0; j < MAX_CORR_SYMBOLS; j++)
            m_corrMatrix[i][j] = (i == j) ? 1.0 : 0.0;
      }
   }

   //+------------------------------------------------------------------+
   //| Add symbol to tracking                                            |
   //+------------------------------------------------------------------+
   int AddSymbol(string symbol)
   {
      // Check if already exists
      int idx = FindSymbol(symbol);
      if(idx >= 0)
         return idx;

      if(m_symbolCount >= MAX_CORR_SYMBOLS)
         return -1;

      m_symbolData[m_symbolCount].Init(symbol, m_lookbackPeriod);
      m_lastPrices[m_symbolCount] = SymbolInfoDouble(symbol, SYMBOL_BID);
      m_symbolCount++;

      return m_symbolCount - 1;
   }

   //+------------------------------------------------------------------+
   //| Find symbol index                                                 |
   //+------------------------------------------------------------------+
   int FindSymbol(string symbol)
   {
      for(int i = 0; i < m_symbolCount; i++)
      {
         if(m_symbolData[i].symbol == symbol)
            return i;
      }
      return -1;
   }

   //+------------------------------------------------------------------+
   //| Record price for returns calculation                              |
   //+------------------------------------------------------------------+
   void RecordPrice(string symbol, double price)
   {
      int idx = FindSymbol(symbol);
      if(idx < 0)
         idx = AddSymbol(symbol);
      if(idx < 0)
         return;

      // Calculate return
      if(m_lastPrices[idx] > 0)
      {
         double ret = SafeDivide(price - m_lastPrices[idx], m_lastPrices[idx], 0.0);
         m_symbolData[idx].AddReturn(ret);
      }

      m_lastPrices[idx] = price;
   }

   //+------------------------------------------------------------------+
   //| On tick update                                                    |
   //+------------------------------------------------------------------+
   void OnTick()
   {
      m_tickCounter++;

      // Update correlations periodically
      if(m_tickCounter % m_updateFrequency == 0)
      {
         UpdateAllCorrelations();
         UpdateExposure();
      }
   }

   //+------------------------------------------------------------------+
   //| Calculate correlation between two symbols                         |
   //+------------------------------------------------------------------+
   double CalculateCorrelation(int idx1, int idx2)
   {
      if(idx1 < 0 || idx1 >= m_symbolCount ||
         idx2 < 0 || idx2 >= m_symbolCount)
         return 0.0;

      if(idx1 == idx2)
         return 1.0;

      // Need sufficient aligned data
      int n = m_symbolData[idx1].GetOldestAligned(m_symbolData[idx2]);
      if(n < 10)
         return 0.0;

      // Calculate means
      m_symbolData[idx1].CalculateStats();
      m_symbolData[idx2].CalculateStats();

      // Calculate covariance using aligned samples
      // We use the NEWEST n samples from each buffer
      int count1 = m_symbolData[idx1].Count();
      int count2 = m_symbolData[idx2].Count();
      int offset1 = count1 - n;
      int offset2 = count2 - n;

      double covar = 0.0;
      for(int i = 0; i < n; i++)
      {
         covar += (m_symbolData[idx1].Get(offset1 + i) - m_symbolData[idx1].mean) *
                  (m_symbolData[idx2].Get(offset2 + i) - m_symbolData[idx2].mean);
      }
      covar = SafeDivide(covar, (double)n, 0.0);

      // Correlation
      double denom = m_symbolData[idx1].stdDev * m_symbolData[idx2].stdDev;
      if(denom > 0)
         return SafeDivide(covar, denom, 0.0);

      return 0.0;
   }

   //+------------------------------------------------------------------+
   //| Update all correlation pairs                                      |
   //+------------------------------------------------------------------+
   void UpdateAllCorrelations()
   {
      // Update matrix
      for(int i = 0; i < m_symbolCount; i++)
      {
         for(int j = i; j < m_symbolCount; j++)
         {
            if(i == j)
            {
               m_corrMatrix[i][j] = 1.0;
            }
            else
            {
               double corr = CalculateCorrelation(i, j);
               m_corrMatrix[i][j] = corr;
               m_corrMatrix[j][i] = corr;  // Symmetric
            }
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Get correlation between two symbols                               |
   //+------------------------------------------------------------------+
   double GetCorrelation(string sym1, string sym2)
   {
      int idx1 = FindSymbol(sym1);
      int idx2 = FindSymbol(sym2);

      if(idx1 < 0 || idx2 < 0)
         return 0.0;

      return m_corrMatrix[idx1][idx2];
   }

   //+------------------------------------------------------------------+
   //| Find highly correlated pairs                                      |
   //+------------------------------------------------------------------+
   int FindHighlyCorrelated(string symbol, string &correlated[], double &correlations[])
   {
      int idx = FindSymbol(symbol);
      if(idx < 0)
         return 0;

      ArrayResize(correlated, 0);
      ArrayResize(correlations, 0);
      int count = 0;

      for(int i = 0; i < m_symbolCount; i++)
      {
         if(i == idx)
            continue;

         double corr = m_corrMatrix[idx][i];
         if(MathAbs(corr) >= m_highCorrThreshold)
         {
            int newSize = count + 1;
            if(ArrayResize(correlated, newSize) != newSize ||
               ArrayResize(correlations, newSize) != newSize)
            {
               Print("ERROR: ArrayResize failed in correlation search - incomplete results");
               break;
            }
            correlated[count] = m_symbolData[i].symbol;
            correlations[count] = corr;
            count++;
         }
      }

      return count;
   }

   //+------------------------------------------------------------------+
   //| Find negatively correlated pairs (for hedging)                    |
   //+------------------------------------------------------------------+
   int FindNegativelyCorrelated(string symbol, string &hedges[], double &correlations[])
   {
      int idx = FindSymbol(symbol);
      if(idx < 0)
         return 0;

      ArrayResize(hedges, 0);
      ArrayResize(correlations, 0);
      int count = 0;

      for(int i = 0; i < m_symbolCount; i++)
      {
         if(i == idx)
            continue;

         double corr = m_corrMatrix[idx][i];
         if(corr <= m_negCorrThreshold)
         {
            int newSize = count + 1;
            if(ArrayResize(hedges, newSize) != newSize ||
               ArrayResize(correlations, newSize) != newSize)
            {
               Print("ERROR: ArrayResize failed in hedge search - incomplete results");
               break;
            }
            hedges[count] = m_symbolData[i].symbol;
            correlations[count] = corr;
            count++;
         }
      }

      return count;
   }

   //+------------------------------------------------------------------+
   //| Calculate portfolio variance                                      |
   //+------------------------------------------------------------------+
   double CalculatePortfolioVariance(string &symbols[], double &weights[])
   {
      int n = ArraySize(symbols);
      if(n != ArraySize(weights) || n == 0)
         return 0.0;

      double variance = 0.0;

      for(int i = 0; i < n; i++)
      {
         int idxI = FindSymbol(symbols[i]);
         if(idxI < 0)
            continue;

         for(int j = 0; j < n; j++)
         {
            int idxJ = FindSymbol(symbols[j]);
            if(idxJ < 0)
               continue;

            double corr = m_corrMatrix[idxI][idxJ];
            double sigmaI = m_symbolData[idxI].stdDev;
            double sigmaJ = m_symbolData[idxJ].stdDev;

            variance += weights[i] * weights[j] * corr * sigmaI * sigmaJ;
         }
      }

      return variance;
   }

   //+------------------------------------------------------------------+
   //| Update portfolio exposure                                         |
   //+------------------------------------------------------------------+
   void UpdateExposure()
   {
      m_exposure.Reset();
      m_exposure.lastUpdate = TimeCurrent();

      double exposures[];
      if(ArrayResize(exposures, m_symbolCount) != m_symbolCount)
      {
         Print("ERROR: ArrayResize failed for exposures array - cannot calculate exposure");
         return;
      }
      ArrayInitialize(exposures, 0.0);

      // Calculate exposures from positions
      int total = PositionsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0)
            continue;

         string symbol = PositionGetString(POSITION_SYMBOL);
         double volume = PositionGetDouble(POSITION_VOLUME);
         double price = PositionGetDouble(POSITION_PRICE_CURRENT);
         ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)
            PositionGetInteger(POSITION_TYPE);

         double exposure = volume * price * SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE);

         // Track by symbol
         int idx = FindSymbol(symbol);
         if(idx >= 0)
         {
            if(type == POSITION_TYPE_BUY)
               exposures[idx] += exposure;
            else
               exposures[idx] -= exposure;
         }

         // Track totals
         if(type == POSITION_TYPE_BUY)
            m_exposure.totalLong += exposure;
         else
            m_exposure.totalShort += exposure;

         if(MathAbs(exposure) > m_exposure.maxSingleExposure)
         {
            m_exposure.maxSingleExposure = MathAbs(exposure);
            m_exposure.maxSymbol = symbol;
         }
      }

      m_exposure.netExposure = m_exposure.totalLong - m_exposure.totalShort;
      m_exposure.grossExposure = m_exposure.totalLong + m_exposure.totalShort;

      // Calculate correlated risk
      m_exposure.correlatedRisk = CalculateCorrelatedRisk(exposures);

      // Calculate diversification ratio
      if(m_exposure.grossExposure > 0)
      {
         double sumIndividual = 0.0;
         for(int i = 0; i < m_symbolCount; i++)
         {
            sumIndividual += MathAbs(exposures[i]) * m_symbolData[i].stdDev;
         }

         if(sumIndividual > 0)
         {
            double portfolioVol = MathSqrt(CalculateExposureVariance(exposures));
            m_exposure.diversificationRatio = SafeDivide(sumIndividual, portfolioVol, 1.0);
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Calculate correlated risk                                         |
   //+------------------------------------------------------------------+
   double CalculateCorrelatedRisk(double &exposures[])
   {
      double risk = 0.0;

      for(int i = 0; i < m_symbolCount; i++)
      {
         if(MathAbs(exposures[i]) < 0.01)
            continue;

         for(int j = i + 1; j < m_symbolCount; j++)
         {
            if(MathAbs(exposures[j]) < 0.01)
               continue;

            double corr = m_corrMatrix[i][j];

            // Same direction with positive correlation = higher risk
            // Opposite direction with positive correlation = lower risk (hedge)
            bool sameDir = (exposures[i] * exposures[j] > 0);

            if(sameDir && corr > m_highCorrThreshold)
            {
               risk += MathAbs(exposures[i] * exposures[j]) * corr;
            }
         }
      }

      return risk;
   }

   //+------------------------------------------------------------------+
   //| Calculate variance of exposures                                   |
   //+------------------------------------------------------------------+
   double CalculateExposureVariance(double &exposures[])
   {
      double variance = 0.0;

      for(int i = 0; i < m_symbolCount; i++)
      {
         for(int j = 0; j < m_symbolCount; j++)
         {
            double corr = m_corrMatrix[i][j];
            double sigmaI = m_symbolData[i].stdDev;
            double sigmaJ = m_symbolData[j].stdDev;

            variance += exposures[i] * exposures[j] * corr * sigmaI * sigmaJ;
         }
      }

      return MathMax(0.0, variance);
   }

   //+------------------------------------------------------------------+
   //| Check if new position would increase correlation risk             |
   //+------------------------------------------------------------------+
   bool WouldIncreaseRisk(string newSymbol, bool isBuy, double volume)
   {
      int idx = FindSymbol(newSymbol);
      if(idx < 0)
         return false;  // No correlation data

      // Check correlation with existing positions
      for(int i = 0; i < PositionsTotal(); i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0)
            continue;

         string posSymbol = PositionGetString(POSITION_SYMBOL);
         ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)
            PositionGetInteger(POSITION_TYPE);

         int posIdx = FindSymbol(posSymbol);
         if(posIdx < 0)
            continue;

         double corr = m_corrMatrix[idx][posIdx];
         bool posBuy = (type == POSITION_TYPE_BUY);

         // Same direction + high positive correlation = risk increase
         if(isBuy == posBuy && corr > m_highCorrThreshold)
            return true;

         // Opposite direction + high negative correlation = risk increase
         if(isBuy != posBuy && corr < m_negCorrThreshold)
            return true;
      }

      return false;
   }

   //+------------------------------------------------------------------+
   //| Get best hedge for position                                       |
   //+------------------------------------------------------------------+
   string GetBestHedge(string symbol, bool isLong)
   {
      int idx = FindSymbol(symbol);
      if(idx < 0)
         return "";

      string bestHedge = "";
      double bestCorr = 0.0;  // Looking for most negative correlation

      for(int i = 0; i < m_symbolCount; i++)
      {
         if(i == idx)
            continue;

         double corr = m_corrMatrix[idx][i];

         // For BOTH long and short positions, best hedge is most negatively correlated
         // A long position hedges with a long in negatively correlated asset
         // A short position hedges with a short in negatively correlated asset
         // (or equivalently, with a long in positively correlated asset)
         if(isLong)
         {
            // Long position: best hedge is most negative correlation
            if(corr < bestCorr)
            {
               bestCorr = corr;
               bestHedge = m_symbolData[i].symbol;
            }
         }
         else
         {
            // Short position: best hedge is also most negative correlation
            // (take opposing direction in negatively correlated asset)
            if(corr < bestCorr)
            {
               bestCorr = corr;
               bestHedge = m_symbolData[i].symbol;
            }
         }
      }

      return bestHedge;
   }

   //+------------------------------------------------------------------+
   //| Get portfolio exposure                                            |
   //+------------------------------------------------------------------+
   PortfolioExposure GetExposure()
   {
      return m_exposure;
   }

   //+------------------------------------------------------------------+
   //| Export correlation matrix to JSON                                 |
   //+------------------------------------------------------------------+
   string ExportMatrixJSON()
   {
      string json = "{\"symbols\":[";

      for(int i = 0; i < m_symbolCount; i++)
      {
         if(i > 0)
            json += ",";
         json += "\"" + m_symbolData[i].symbol + "\"";
      }

      json += "],\"matrix\":[";

      for(int i = 0; i < m_symbolCount; i++)
      {
         if(i > 0)
            json += ",";
         json += "[";

         for(int j = 0; j < m_symbolCount; j++)
         {
            if(j > 0)
               json += ",";
            json += DoubleToString(m_corrMatrix[i][j], 4);
         }
         json += "]";
      }

      json += "]}";

      return json;
   }

   //+------------------------------------------------------------------+
   //| Export for RL features                                            |
   //+------------------------------------------------------------------+
   void ToRLFeatures(string symbol, double &features[], int startIdx = 0)
   {
      // Validate startIdx early - don't corrupt array on invalid input
      if(startIdx < 0)
      {
         Print("ERROR: ToRLFeatures called with negative startIdx=", startIdx);
         return;
      }

      int idx = FindSymbol(symbol);

      // Features: avg correlation, max correlation, min correlation,
      //           exposure ratio, diversification
      int requiredSize = startIdx + 5;
      if(ArraySize(features) < requiredSize)
      {
         if(ArrayResize(features, requiredSize) != requiredSize)
         {
            Print("ERROR: ArrayResize failed for RL features - cannot populate correlation data");
            return;
         }
      }

      // Set only our 5 slots to neutral if symbol not found
      if(idx < 0)
      {
         features[startIdx + 0] = 0.5;
         features[startIdx + 1] = 0.5;
         features[startIdx + 2] = 0.5;
         features[startIdx + 3] = 0.5;
         features[startIdx + 4] = 0.5;
         return;
      }

      double avgCorr = 0.0;
      double maxCorr = -1.0;
      double minCorr = 1.0;
      int count = 0;

      for(int i = 0; i < m_symbolCount; i++)
      {
         if(i == idx)
            continue;

         double corr = m_corrMatrix[idx][i];
         avgCorr += corr;
         if(corr > maxCorr)
            maxCorr = corr;
         if(corr < minCorr)
            minCorr = corr;
         count++;
      }

      if(count > 0)
         avgCorr = SafeDivide(avgCorr, (double)count, 0.0);

      // Normalize correlations to 0-1 range
      features[startIdx + 0] = (avgCorr + 1.0) / 2.0;
      features[startIdx + 1] = (maxCorr + 1.0) / 2.0;
      features[startIdx + 2] = (minCorr + 1.0) / 2.0;

      // Net exposure ratio: normalize to [0,1] where 0.5 = neutral
      // netExposure/grossExposure ranges from -1 to +1
      double expRatio = 0.0;
      if(m_exposure.grossExposure > 0)
      {
         expRatio = SafeDivide(m_exposure.netExposure, m_exposure.grossExposure, 0.0);
      }
      features[startIdx + 3] = (expRatio + 1.0) / 2.0;  // Map [-1,1] to [0,1]

      // Diversification ratio: cap at 3.0 and normalize
      features[startIdx + 4] = MathMin(1.0, SafeDivide(m_exposure.diversificationRatio, 3.0, 0.0));
   }

   //+------------------------------------------------------------------+
   //| Get symbol count                                                  |
   //+------------------------------------------------------------------+
   int GetSymbolCount() { return m_symbolCount; }

   //+------------------------------------------------------------------+
   //| Set thresholds                                                    |
   //+------------------------------------------------------------------+
   void SetHighCorrThreshold(double thresh) { m_highCorrThreshold = thresh; }
   void SetNegCorrThreshold(double thresh) { m_negCorrThreshold = thresh; }

   //+------------------------------------------------------------------+
   //| Get symbol volatility                                             |
   //+------------------------------------------------------------------+
   double GetVolatility(string symbol)
   {
      int idx = FindSymbol(symbol);
      if(idx < 0)
         return 0.0;

      return m_symbolData[idx].stdDev;
   }
};

//+------------------------------------------------------------------+
//| GLOBAL INSTANCE                                                   |
//+------------------------------------------------------------------+
CCorrelationTracker g_correlation;

#endif // VT_CORRELATION_MQH
