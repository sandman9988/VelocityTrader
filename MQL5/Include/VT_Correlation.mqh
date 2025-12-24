//+------------------------------------------------------------------+
//|                                               VT_Correlation.mqh |
//|                                       VelocityTrader Framework   |
//|                 Portfolio Correlation & Risk Management          |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader"
#property strict

#include "VT_Performance.mqh"

//+------------------------------------------------------------------+
//| CONSTANTS                                                         |
//+------------------------------------------------------------------+
#define MAX_CORR_SYMBOLS    50
#define CORR_PERIOD         100    // Bars for correlation calculation
#define CORR_UPDATE_TICKS   100    // Update every N ticks

//+------------------------------------------------------------------+
//| STRUCTURE - Symbol Returns Data                                   |
//+------------------------------------------------------------------+
struct SymbolReturns
{
   string            symbol;
   double            returns[];
   int               count;
   double            mean;
   double            stdDev;
   datetime          lastUpdate;

   void Reset()
   {
      symbol = "";
      ArrayResize(returns, 0);
      count = 0;
      mean = 0.0;
      stdDev = 0.0;
      lastUpdate = 0;
   }

   void Init(string sym, int periods)
   {
      symbol = sym;
      ArrayResize(returns, periods);
      ArrayInitialize(returns, 0.0);
      count = 0;
      mean = 0.0;
      stdDev = 0.0;
      lastUpdate = 0;
   }

   void AddReturn(double ret)
   {
      if(count < ArraySize(returns))
      {
         returns[count] = ret;
         count++;
      }
      else
      {
         // Shift array
         for(int i = 0; i < count - 1; i++)
            returns[i] = returns[i + 1];
         returns[count - 1] = ret;
      }
      lastUpdate = TimeCurrent();
   }

   void CalculateStats()
   {
      if(count < 2)
      {
         mean = 0.0;
         stdDev = 0.0;
         return;
      }

      // Mean
      double sum = 0.0;
      for(int i = 0; i < count; i++)
         sum += returns[i];
      mean = sum / count;

      // Std Dev
      double sumSq = 0.0;
      for(int i = 0; i < count; i++)
         sumSq += MathPow(returns[i] - mean, 2);
      stdDev = MathSqrt(sumSq / count);
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
         double ret = (price - m_lastPrices[idx]) / m_lastPrices[idx];
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

      SymbolReturns &s1 = m_symbolData[idx1];
      SymbolReturns &s2 = m_symbolData[idx2];

      // Need sufficient data
      int n = MathMin(s1.count, s2.count);
      if(n < 10)
         return 0.0;

      // Calculate means
      s1.CalculateStats();
      s2.CalculateStats();

      // Calculate covariance
      double covar = 0.0;
      for(int i = 0; i < n; i++)
      {
         covar += (s1.returns[i] - s1.mean) * (s2.returns[i] - s2.mean);
      }
      covar /= n;

      // Correlation
      if(s1.stdDev > 0 && s2.stdDev > 0)
         return covar / (s1.stdDev * s2.stdDev);

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
            ArrayResize(correlated, count + 1);
            ArrayResize(correlations, count + 1);
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
            ArrayResize(hedges, count + 1);
            ArrayResize(correlations, count + 1);
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
      ArrayResize(exposures, m_symbolCount);
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
            m_exposure.diversificationRatio = sumIndividual / portfolioVol;
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
      double bestCorr = 0.0;

      for(int i = 0; i < m_symbolCount; i++)
      {
         if(i == idx)
            continue;

         double corr = m_corrMatrix[idx][i];

         // For long position, best hedge is negatively correlated
         // For short position, best hedge is positively correlated
         if(isLong && corr < bestCorr)
         {
            bestCorr = corr;
            bestHedge = m_symbolData[i].symbol;
         }
         else if(!isLong && corr > -bestCorr)
         {
            bestCorr = -corr;
            bestHedge = m_symbolData[i].symbol;
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
      int idx = FindSymbol(symbol);

      // Features: avg correlation, max correlation, min correlation,
      //           exposure ratio, diversification
      if(ArraySize(features) < startIdx + 5)
         ArrayResize(features, startIdx + 5);

      if(idx < 0)
      {
         ArrayInitialize(features, 0.5);
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
         avgCorr /= count;

      // Normalize to 0-1
      features[startIdx + 0] = (avgCorr + 1.0) / 2.0;
      features[startIdx + 1] = (maxCorr + 1.0) / 2.0;
      features[startIdx + 2] = (minCorr + 1.0) / 2.0;
      features[startIdx + 3] = m_exposure.grossExposure > 0 ?
         MathMin(1.0, m_exposure.netExposure / m_exposure.grossExposure) : 0.5;
      features[startIdx + 4] = MathMin(1.0, m_exposure.diversificationRatio / 3.0);
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
