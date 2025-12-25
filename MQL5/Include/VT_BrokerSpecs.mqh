//+------------------------------------------------------------------+
//|                                               VT_BrokerSpecs.mqh |
//|                                       VelocityTrader Framework   |
//|                        Dynamic Broker Contract Specifications    |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader"

#include "VT_Definitions.mqh"

//+------------------------------------------------------------------+
//| ENUMERATIONS - Trading Modes & Classifications                   |
//+------------------------------------------------------------------+
enum ENUM_TRADE_DIRECTION
{
   TRADE_DIR_BOTH = 0,        // Long and Short allowed
   TRADE_DIR_LONG_ONLY = 1,   // Only long positions
   TRADE_DIR_SHORT_ONLY = 2,  // Only short positions
   TRADE_DIR_DISABLED = 3     // Trading disabled
};

enum ENUM_ORDER_EXECUTION
{
   EXEC_INSTANT = 0,          // Instant execution
   EXEC_MARKET = 1,           // Market execution
   EXEC_EXCHANGE = 2,         // Exchange execution
   EXEC_REQUEST = 3           // Request execution
};

enum ENUM_SWAP_DAY
{
   SWAP_WEDNESDAY = 0,        // Triple swap on Wednesday
   SWAP_FRIDAY = 1,           // Triple swap on Friday
   SWAP_UNKNOWN = 2           // Unknown/variable
};

enum ENUM_ASSET_CLASS
{
   ASSET_FOREX_MAJOR = 0,
   ASSET_FOREX_MINOR = 1,
   ASSET_FOREX_EXOTIC = 2,
   ASSET_CRYPTO = 3,
   ASSET_INDEX = 4,
   ASSET_COMMODITY = 5,
   ASSET_STOCK = 6,
   ASSET_ETF = 7,
   ASSET_BOND = 8,
   ASSET_UNKNOWN = 9
};

enum ENUM_SPEC_VALIDITY
{
   SPEC_VALID = 0,            // All specs valid
   SPEC_STALE = 1,            // Needs refresh
   SPEC_INVALID = 2,          // Invalid/corrupted
   SPEC_UNAVAILABLE = 3       // Symbol not available
};

enum ENUM_ACCOUNT_MARGIN_MODE
{
   MARGIN_MODE_HEDGING = 0,   // Multiple positions per symbol (EU/most)
   MARGIN_MODE_NETTING = 1,   // One aggregate position per symbol
   MARGIN_MODE_FIFO = 2       // First-In-First-Out (US/NFA)
};

enum ENUM_CLOSE_PRIORITY
{
   CLOSE_OLDEST_FIRST = 0,    // FIFO - oldest position first
   CLOSE_NEWEST_FIRST = 1,    // LIFO - newest position first
   CLOSE_LARGEST_FIRST = 2,   // Largest position first
   CLOSE_SMALLEST_FIRST = 3,  // Smallest position first
   CLOSE_MOST_PROFIT = 4,     // Most profitable first
   CLOSE_MOST_LOSS = 5        // Most losing first
};

//+------------------------------------------------------------------+
//| STRUCTURE - Trading Session                                       |
//+------------------------------------------------------------------+
struct TradingSession
{
   int               dayOfWeek;        // 0=Sunday, 6=Saturday
   datetime          openTime;         // Session open (time only)
   datetime          closeTime;        // Session close (time only)
   bool              isActive;         // Session active today

   void Reset()
   {
      dayOfWeek = -1;
      openTime = 0;
      closeTime = 0;
      isActive = false;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Normalized Values for RL (0-1 range)                  |
//+------------------------------------------------------------------+
struct NormalizedSpecs
{
   double            spreadNorm;       // Spread relative to price (0-1)
   double            swapLongNorm;     // Swap cost normalized (-1 to 1)
   double            swapShortNorm;    // Swap cost normalized (-1 to 1)
   double            commissionNorm;   // Commission normalized (0-1)
   double            marginNorm;       // Margin requirement normalized (0-1)
   double            volatilityNorm;   // Volatility normalized (0-1)
   double            liquidityNorm;    // Liquidity score (0-1)
   double            sessionNorm;      // Time to session close (0-1)
   double            riskScoreNorm;    // Combined risk score (0-1)
   datetime          lastUpdate;       // Last normalization update

   void Reset()
   {
      spreadNorm = 0.5;
      swapLongNorm = 0.0;
      swapShortNorm = 0.0;
      commissionNorm = 0.0;
      marginNorm = 0.5;
      volatilityNorm = 0.5;
      liquidityNorm = 0.5;
      sessionNorm = 1.0;
      riskScoreNorm = 0.5;
      lastUpdate = 0;
   }

   // Pack into feature vector for RL
   void ToFeatureVector(double &features[], int startIdx = 0)
   {
      int requiredSize = startIdx + 9;
      if(ArraySize(features) < requiredSize)
      {
         if(ArrayResize(features, requiredSize) != requiredSize)
         {
            Print("ERROR: ArrayResize failed for features vector - cannot populate broker data");
            return;
         }
      }

      // Bounds-safe assignment
      int size = ArraySize(features);
      if(startIdx + 8 < size)
      {
         features[startIdx + 0] = spreadNorm;
         features[startIdx + 1] = swapLongNorm;
         features[startIdx + 2] = swapShortNorm;
         features[startIdx + 3] = commissionNorm;
         features[startIdx + 4] = marginNorm;
         features[startIdx + 5] = volatilityNorm;
         features[startIdx + 6] = liquidityNorm;
         features[startIdx + 7] = sessionNorm;
         features[startIdx + 8] = riskScoreNorm;
      }
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Full Contract Specification                           |
//+------------------------------------------------------------------+
struct ContractSpec
{
   // === IDENTIFICATION ===
   string            symbol;           // Full symbol name
   string            baseName;         // Base name without suffix
   string            suffix;           // Broker suffix (e.g., ".raw", "m", "#")
   ENUM_ASSET_CLASS  assetClass;       // Asset classification

   // === LOT SPECIFICATIONS ===
   double            lotMin;           // Minimum lot size
   double            lotMax;           // Maximum lot size
   double            lotStep;          // Lot step increment
   double            contractSize;     // Contract size

   // === PRICE SPECIFICATIONS ===
   double            point;            // Point value
   int               digits;           // Price digits
   double            tickSize;         // Minimum tick size
   double            tickValue;        // Value per tick in account currency

   // === STOPS & LEVELS ===
   int               stopsLevel;       // Minimum stop level in points
   int               freezeLevel;      // Freeze level in points
   double            spreadTypical;    // Typical spread
   double            spreadCurrent;    // Current spread

   // === SWAP & FINANCING ===
   double            swapLong;         // Swap for long positions
   double            swapShort;        // Swap for short positions
   ENUM_SWAP_DAY     tripleSwapDay;    // Triple swap day
   int               swapMode;         // Swap calculation mode

   // === MARGIN & COMMISSION ===
   double            marginInitial;    // Initial margin requirement
   double            marginMaintenance; // Maintenance margin
   double            marginHedged;     // Hedged margin
   double            commission;       // Commission per lot (one way)
   int               marginMode;       // Margin calculation mode

   // === EXECUTION ===
   ENUM_ORDER_EXECUTION executionMode; // Execution type
   int               fillingMode;      // Allowed filling modes
   bool              marketOrders;     // Market orders allowed
   bool              limitOrders;      // Limit orders allowed
   bool              stopOrders;       // Stop orders allowed
   bool              stopLimitOrders;  // Stop-limit orders allowed

   // === TRADING RESTRICTIONS ===
   ENUM_TRADE_DIRECTION tradeDirection; // Allowed trade direction
   bool              tradingEnabled;   // Trading currently enabled
   datetime          expirationTime;   // Contract expiration (for futures)

   // === SESSIONS ===
   TradingSession    sessions[7];      // Sessions for each day
   bool              isMarketOpen;     // Market currently open
   datetime          nextOpen;         // Next market open time
   datetime          nextClose;        // Next market close time

   // === NORMALIZATION ===
   NormalizedSpecs   normalized;       // RL-ready normalized values

   // === VALIDATION ===
   ENUM_SPEC_VALIDITY validity;        // Specification validity
   datetime          lastRefresh;      // Last refresh timestamp
   int               refreshFailures;  // Consecutive refresh failures
   uint              checksum;         // Data integrity checksum

   //+------------------------------------------------------------------+
   //| Initialize with defaults                                         |
   //+------------------------------------------------------------------+
   void Reset()
   {
      symbol = "";
      baseName = "";
      suffix = "";
      assetClass = ASSET_UNKNOWN;

      lotMin = 0.01;
      lotMax = 100.0;
      lotStep = 0.01;
      contractSize = 100000.0;

      point = 0.00001;
      digits = 5;
      tickSize = 0.00001;
      tickValue = 1.0;

      stopsLevel = 0;
      freezeLevel = 0;
      spreadTypical = 0.0;
      spreadCurrent = 0.0;

      swapLong = 0.0;
      swapShort = 0.0;
      tripleSwapDay = SWAP_WEDNESDAY;
      swapMode = 0;

      marginInitial = 0.0;
      marginMaintenance = 0.0;
      marginHedged = 0.0;
      commission = 0.0;
      marginMode = 0;

      executionMode = EXEC_MARKET;
      fillingMode = 0;
      marketOrders = true;
      limitOrders = true;
      stopOrders = true;
      stopLimitOrders = false;

      tradeDirection = TRADE_DIR_BOTH;
      tradingEnabled = true;
      expirationTime = 0;

      for(int i = 0; i < 7; i++)
         sessions[i].Reset();

      isMarketOpen = false;
      nextOpen = 0;
      nextClose = 0;

      normalized.Reset();

      validity = SPEC_UNAVAILABLE;
      lastRefresh = 0;
      refreshFailures = 0;
      checksum = 0;
   }

   //+------------------------------------------------------------------+
   //| Calculate checksum for integrity                                 |
   //+------------------------------------------------------------------+
   uint CalculateChecksum()
   {
      uint sum = 0;

      // Hash key numeric values
      sum ^= (uint)(lotMin * 10000);
      sum ^= (uint)(lotMax * 100);
      sum ^= (uint)(lotStep * 100000);
      sum ^= (uint)(point * 1000000000);
      sum ^= (uint)digits << 24;
      sum ^= (uint)stopsLevel << 16;
      sum ^= (uint)(swapLong * 1000);
      sum ^= (uint)(swapShort * 1000);
      sum ^= (uint)(marginInitial * 100);

      return sum;
   }

   //+------------------------------------------------------------------+
   //| Validate integrity                                               |
   //+------------------------------------------------------------------+
   bool ValidateIntegrity()
   {
      // Check for corrupted/impossible values
      if(lotMin <= 0 || lotMin > lotMax)
         return false;
      if(lotStep <= 0 || lotStep > lotMax)
         return false;
      if(point <= 0)
         return false;
      if(digits < 0 || digits > 8)
         return false;
      if(stopsLevel < 0 || stopsLevel > 10000)
         return false;
      if(contractSize <= 0)
         return false;

      // Verify checksum
      if(checksum != 0 && checksum != CalculateChecksum())
         return false;

      return true;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Risk Parameters per Instrument                        |
//+------------------------------------------------------------------+
struct InstrumentRisk
{
   string            symbol;
   double            maxLotSize;       // Max allowed lot for this instrument
   double            maxExposure;      // Max exposure in account currency
   double            maxDrawdown;      // Max allowed drawdown %
   double            correlationLimit; // Max correlation with portfolio
   int               maxPositions;     // Max concurrent positions
   double            riskPerTrade;     // Risk % per trade
   bool              hedgingAllowed;   // Allow hedging
   datetime          lastUpdate;

   void Reset()
   {
      symbol = "";
      maxLotSize = 1.0;
      maxExposure = 10000.0;
      maxDrawdown = 5.0;
      correlationLimit = 0.7;
      maxPositions = 3;
      riskPerTrade = 1.0;
      hedgingAllowed = true;
      lastUpdate = 0;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Asset Class Risk                                      |
//+------------------------------------------------------------------+
struct ClassRisk
{
   ENUM_ASSET_CLASS  assetClass;
   double            maxExposure;      // Max exposure for this class
   double            maxCorrelation;   // Max internal correlation
   int               maxInstruments;   // Max instruments in this class
   double            volatilityMult;   // Volatility multiplier for sizing

   void Reset()
   {
      assetClass = ASSET_UNKNOWN;
      maxExposure = 25.0;  // 25% of portfolio
      maxCorrelation = 0.6;
      maxInstruments = 5;
      volatilityMult = 1.0;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Portfolio Risk                                        |
//+------------------------------------------------------------------+
struct PortfolioRisk
{
   double            maxTotalExposure;    // Max total exposure
   double            maxDrawdown;         // Max portfolio drawdown
   double            targetVolatility;    // Target annualized volatility
   double            maxCorrelation;      // Max average correlation
   int               maxPositions;        // Max total positions
   double            marginCallLevel;     // Margin call warning level
   double            stopOutLevel;        // Stop out level
   bool              hedgingEnabled;      // Global hedging flag

   void Reset()
   {
      maxTotalExposure = 100.0;
      maxDrawdown = 20.0;
      targetVolatility = 15.0;
      maxCorrelation = 0.5;
      maxPositions = 20;
      marginCallLevel = 100.0;
      stopOutLevel = 50.0;
      hedgingEnabled = true;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Account Settings (Hedging/Netting/FIFO)               |
//+------------------------------------------------------------------+
struct AccountSettings
{
   ENUM_ACCOUNT_MARGIN_MODE marginMode;   // Hedging, Netting, or FIFO
   ENUM_CLOSE_PRIORITY      closePriority; // Position close order
   bool              hedgingAllowed;      // Hedging allowed
   bool              nettingAllowed;      // Netting allowed
   bool              fifoRequired;        // FIFO required (US/NFA)
   int               maxPositionsTotal;   // Max positions across all symbols
   int               maxPositionsPerSymbol; // Max positions per symbol
   double            marginCallLevel;     // Margin call warning %
   double            stopOutLevel;        // Stop out %
   string            accountCurrency;     // Account currency
   int               leverage;            // Account leverage
   bool              isDemo;              // Demo account flag
   datetime          lastUpdate;          // Last settings refresh

   void Reset()
   {
      marginMode = MARGIN_MODE_HEDGING;
      closePriority = CLOSE_OLDEST_FIRST;
      hedgingAllowed = true;
      nettingAllowed = true;
      fifoRequired = false;
      maxPositionsTotal = 100;
      maxPositionsPerSymbol = 10;
      marginCallLevel = 100.0;
      stopOutLevel = 50.0;
      accountCurrency = "USD";
      leverage = 100;
      isDemo = true;
      lastUpdate = 0;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Position Info for FIFO sorting                        |
//+------------------------------------------------------------------+
struct PositionInfo
{
   ulong             ticket;              // Position ticket
   string            symbol;              // Symbol
   datetime          openTime;            // Open time (for FIFO)
   double            volume;              // Volume
   double            profit;              // Current profit
   ENUM_POSITION_TYPE type;               // Buy or Sell
   double            openPrice;           // Open price
   double            stopLoss;            // Stop loss
   double            takeProfit;          // Take profit
   long              magic;               // Magic number

   void Reset()
   {
      ticket = 0;
      symbol = "";
      openTime = 0;
      volume = 0.0;
      profit = 0.0;
      type = POSITION_TYPE_BUY;
      openPrice = 0.0;
      stopLoss = 0.0;
      takeProfit = 0.0;
      magic = 0;
   }
};

//+------------------------------------------------------------------+
//| CLASS - Broker Specification Manager                              |
//+------------------------------------------------------------------+
class CBrokerSpecManager
{
private:
   ContractSpec      m_specs[];           // All symbol specifications
   int               m_specCount;         // Number of loaded specs
   string            m_symbolMap[];       // Symbol to index mapping

   InstrumentRisk    m_instrRisk[];       // Per-instrument risk
   ClassRisk         m_classRisk[10];     // Per-class risk
   PortfolioRisk     m_portfolioRisk;     // Portfolio risk
   AccountSettings   m_accountSettings;   // Account hedging/netting/FIFO

   string            m_brokerSuffix;      // Detected broker suffix
   bool              m_suffixDetected;    // Suffix detection done
   bool              m_accountDetected;   // Account mode detection done

   int               m_refreshInterval;   // Refresh interval seconds
   int               m_maxFailures;       // Max failures before disable

   // Normalization ranges (for RL scaling)
   double            m_spreadMin;
   double            m_spreadMax;
   double            m_swapMin;
   double            m_swapMax;
   double            m_volMin;
   double            m_volMax;

public:
   //+------------------------------------------------------------------+
   //| Constructor                                                       |
   //+------------------------------------------------------------------+
   CBrokerSpecManager()
   {
      m_specCount = 0;
      m_brokerSuffix = "";
      m_suffixDetected = false;
      m_accountDetected = false;
      m_refreshInterval = 60;  // Refresh every 60 seconds
      m_maxFailures = 3;

      // Default normalization ranges
      m_spreadMin = 0.1;
      m_spreadMax = 100.0;  // pips
      m_swapMin = -50.0;
      m_swapMax = 50.0;
      m_volMin = 0.0001;
      m_volMax = 0.05;

      m_portfolioRisk.Reset();
      m_accountSettings.Reset();
      for(int i = 0; i < 10; i++)
         m_classRisk[i].Reset();
   }

   //+------------------------------------------------------------------+
   //| Detect broker suffix from available symbols                       |
   //+------------------------------------------------------------------+
   string DetectBrokerSuffix()
   {
      if(m_suffixDetected)
         return m_brokerSuffix;

      // Common base pairs to search for
      string basePairs[] = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD"};

      // Common suffixes to check
      string suffixes[] = {"", ".", ".raw", "m", "M", "#", ".i", ".std",
                           ".pro", "_SB", ".ecn", "-ECN", ".r"};

      int totalSymbols = SymbolsTotal(false);

      for(int i = 0; i < ArraySize(basePairs); i++)
      {
         for(int j = 0; j < ArraySize(suffixes); j++)
         {
            string testSymbol = basePairs[i] + suffixes[j];

            // Check if symbol exists
            for(int k = 0; k < totalSymbols; k++)
            {
               string availSymbol = SymbolName(k, false);
               if(availSymbol == testSymbol)
               {
                  m_brokerSuffix = suffixes[j];
                  m_suffixDetected = true;
                  return m_brokerSuffix;
               }
            }
         }
      }

      // Try to extract suffix from first forex pair found
      for(int i = 0; i < totalSymbols && i < 100; i++)
      {
         string sym = SymbolName(i, false);

         for(int j = 0; j < ArraySize(basePairs); j++)
         {
            if(StringFind(sym, basePairs[j]) == 0)
            {
               m_brokerSuffix = StringSubstr(sym, StringLen(basePairs[j]));
               m_suffixDetected = true;
               return m_brokerSuffix;
            }
         }
      }

      m_suffixDetected = true;
      m_brokerSuffix = "";
      return m_brokerSuffix;
   }

   //+------------------------------------------------------------------+
   //| Get full symbol name with broker suffix                          |
   //+------------------------------------------------------------------+
   string GetFullSymbol(string baseName)
   {
      if(!m_suffixDetected)
         DetectBrokerSuffix();

      return baseName + m_brokerSuffix;
   }

   //+------------------------------------------------------------------+
   //| Strip suffix to get base symbol name                             |
   //+------------------------------------------------------------------+
   string GetBaseName(string fullSymbol)
   {
      if(!m_suffixDetected)
         DetectBrokerSuffix();

      if(m_brokerSuffix == "")
         return fullSymbol;

      int suffixPos = StringFind(fullSymbol, m_brokerSuffix);
      if(suffixPos > 0)
         return StringSubstr(fullSymbol, 0, suffixPos);

      return fullSymbol;
   }

   //+------------------------------------------------------------------+
   //| Detect asset class from symbol name                              |
   //+------------------------------------------------------------------+
   ENUM_ASSET_CLASS DetectAssetClass(string symbol)
   {
      string baseName = GetBaseName(symbol);
      string upper = baseName;
      StringToUpper(upper);

      // Crypto detection
      if(StringFind(upper, "BTC") >= 0 || StringFind(upper, "ETH") >= 0 ||
         StringFind(upper, "XRP") >= 0 || StringFind(upper, "LTC") >= 0 ||
         StringFind(upper, "DOGE") >= 0 || StringFind(upper, "SOL") >= 0)
         return ASSET_CRYPTO;

      // Index detection
      if(StringFind(upper, "US30") >= 0 || StringFind(upper, "US500") >= 0 ||
         StringFind(upper, "NAS100") >= 0 || StringFind(upper, "DAX") >= 0 ||
         StringFind(upper, "FTSE") >= 0 || StringFind(upper, "NIK") >= 0 ||
         StringFind(upper, "SPX") >= 0 || StringFind(upper, "DJI") >= 0)
         return ASSET_INDEX;

      // Commodity detection
      if(StringFind(upper, "XAUUSD") >= 0 || StringFind(upper, "GOLD") >= 0 ||
         StringFind(upper, "XAGUSD") >= 0 || StringFind(upper, "SILVER") >= 0 ||
         StringFind(upper, "OIL") >= 0 || StringFind(upper, "BRENT") >= 0 ||
         StringFind(upper, "WTI") >= 0 || StringFind(upper, "NATGAS") >= 0)
         return ASSET_COMMODITY;

      // Forex classification
      string majors[] = {"EURUSD", "GBPUSD", "USDJPY", "USDCHF",
                         "AUDUSD", "USDCAD", "NZDUSD"};
      for(int i = 0; i < ArraySize(majors); i++)
         if(StringFind(upper, majors[i]) >= 0)
            return ASSET_FOREX_MAJOR;

      string minors[] = {"EURGBP", "EURJPY", "GBPJPY", "EURAUD",
                         "EURCAD", "AUDCAD", "AUDNZD", "NZDJPY"};
      for(int i = 0; i < ArraySize(minors); i++)
         if(StringFind(upper, minors[i]) >= 0)
            return ASSET_FOREX_MINOR;

      // Exotic pairs (emerging market currencies)
      string exotics[] = {"TRY", "ZAR", "MXN", "PLN", "HUF",
                          "CZK", "SEK", "NOK", "DKK", "SGD"};
      for(int i = 0; i < ArraySize(exotics); i++)
         if(StringFind(upper, exotics[i]) >= 0)
            return ASSET_FOREX_EXOTIC;

      // Default to forex if 6 chars (currency pair)
      if(StringLen(baseName) == 6)
         return ASSET_FOREX_MINOR;

      return ASSET_UNKNOWN;
   }

   //+------------------------------------------------------------------+
   //| Detect triple swap day (Wednesday or Friday)                     |
   //+------------------------------------------------------------------+
   ENUM_SWAP_DAY DetectTripleSwapDay(string symbol)
   {
      // Most forex brokers use Wednesday for triple swap
      // Crypto often uses Friday or no triple swap
      // Some metals may vary

      ENUM_ASSET_CLASS assetClass = DetectAssetClass(symbol);

      switch(assetClass)
      {
         case ASSET_CRYPTO:
            // Crypto markets trade 24/7, triple swap varies
            return SWAP_FRIDAY;

         case ASSET_FOREX_MAJOR:
         case ASSET_FOREX_MINOR:
         case ASSET_FOREX_EXOTIC:
            // Standard forex uses Wednesday
            return SWAP_WEDNESDAY;

         case ASSET_INDEX:
         case ASSET_STOCK:
            // Indices/stocks typically Friday
            return SWAP_FRIDAY;

         case ASSET_COMMODITY:
            // Commodities usually Wednesday
            return SWAP_WEDNESDAY;

         default:
            return SWAP_UNKNOWN;
      }
   }

   //+------------------------------------------------------------------+
   //| Load specification for a symbol                                   |
   //+------------------------------------------------------------------+
   bool LoadSpec(string symbol, ContractSpec &spec)
   {
      spec.Reset();

      // Check if symbol exists
      if(!SymbolInfoInteger(symbol, SYMBOL_EXIST))
      {
         spec.validity = SPEC_UNAVAILABLE;
         return false;
      }

      // Select symbol in Market Watch if needed
      if(!SymbolInfoInteger(symbol, SYMBOL_SELECT))
         SymbolSelect(symbol, true);

      // === IDENTIFICATION ===
      spec.symbol = symbol;
      spec.baseName = GetBaseName(symbol);
      spec.suffix = m_brokerSuffix;
      spec.assetClass = DetectAssetClass(symbol);

      // === LOT SPECIFICATIONS ===
      spec.lotMin = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
      spec.lotMax = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
      spec.lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
      spec.contractSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE);

      // === PRICE SPECIFICATIONS ===
      spec.point = SymbolInfoDouble(symbol, SYMBOL_POINT);
      spec.digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
      spec.tickSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
      spec.tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);

      // === STOPS & LEVELS ===
      spec.stopsLevel = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
      spec.freezeLevel = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_FREEZE_LEVEL);

      double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
      double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
      if(bid > 0 && ask > 0 && spec.point > 0)
      {
         spec.spreadCurrent = (ask - bid) / spec.point;
         spec.spreadTypical = spec.spreadCurrent;  // Will be averaged over time
      }

      // === SWAP & FINANCING ===
      spec.swapLong = SymbolInfoDouble(symbol, SYMBOL_SWAP_LONG);
      spec.swapShort = SymbolInfoDouble(symbol, SYMBOL_SWAP_SHORT);
      spec.tripleSwapDay = DetectTripleSwapDay(symbol);
      spec.swapMode = (int)SymbolInfoInteger(symbol, SYMBOL_SWAP_MODE);

      // === MARGIN & COMMISSION ===
      spec.marginInitial = SymbolInfoDouble(symbol, SYMBOL_MARGIN_INITIAL);
      spec.marginMaintenance = SymbolInfoDouble(symbol, SYMBOL_MARGIN_MAINTENANCE);
      spec.marginHedged = SymbolInfoDouble(symbol, SYMBOL_MARGIN_HEDGED);
      spec.marginMode = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_CALC_MODE);

      // Commission requires trade history - use default estimate
      spec.commission = 0.0;  // Will be updated from trade history

      // === EXECUTION ===
      ENUM_SYMBOL_TRADE_EXECUTION execMode = (ENUM_SYMBOL_TRADE_EXECUTION)
         SymbolInfoInteger(symbol, SYMBOL_TRADE_EXEMODE);
      switch(execMode)
      {
         case SYMBOL_TRADE_EXECUTION_INSTANT:
            spec.executionMode = EXEC_INSTANT;
            break;
         case SYMBOL_TRADE_EXECUTION_MARKET:
            spec.executionMode = EXEC_MARKET;
            break;
         case SYMBOL_TRADE_EXECUTION_EXCHANGE:
            spec.executionMode = EXEC_EXCHANGE;
            break;
         case SYMBOL_TRADE_EXECUTION_REQUEST:
            spec.executionMode = EXEC_REQUEST;
            break;
         default:
            spec.executionMode = EXEC_MARKET;
      }

      spec.fillingMode = (int)SymbolInfoInteger(symbol, SYMBOL_FILLING_MODE);

      // Check allowed order types
      int orderMode = (int)SymbolInfoInteger(symbol, SYMBOL_ORDER_MODE);
      spec.marketOrders = (orderMode & SYMBOL_ORDER_MARKET) != 0;
      spec.limitOrders = (orderMode & SYMBOL_ORDER_LIMIT) != 0;
      spec.stopOrders = (orderMode & SYMBOL_ORDER_STOP) != 0;
      spec.stopLimitOrders = (orderMode & SYMBOL_ORDER_STOP_LIMIT) != 0;

      // === TRADING RESTRICTIONS ===
      ENUM_SYMBOL_TRADE_MODE tradeMode = (ENUM_SYMBOL_TRADE_MODE)
         SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE);

      switch(tradeMode)
      {
         case SYMBOL_TRADE_MODE_DISABLED:
            spec.tradeDirection = TRADE_DIR_DISABLED;
            spec.tradingEnabled = false;
            break;
         case SYMBOL_TRADE_MODE_LONGONLY:
            spec.tradeDirection = TRADE_DIR_LONG_ONLY;
            spec.tradingEnabled = true;
            break;
         case SYMBOL_TRADE_MODE_SHORTONLY:
            spec.tradeDirection = TRADE_DIR_SHORT_ONLY;
            spec.tradingEnabled = true;
            break;
         case SYMBOL_TRADE_MODE_CLOSEONLY:
            spec.tradeDirection = TRADE_DIR_DISABLED;
            spec.tradingEnabled = false;
            break;
         default:
            spec.tradeDirection = TRADE_DIR_BOTH;
            spec.tradingEnabled = true;
      }

      spec.expirationTime = (datetime)SymbolInfoInteger(symbol, SYMBOL_EXPIRATION_TIME);

      // === SESSIONS ===
      LoadTradingSessions(symbol, spec);

      // === VALIDATION ===
      spec.lastRefresh = TimeCurrent();
      spec.checksum = spec.CalculateChecksum();

      if(spec.ValidateIntegrity())
         spec.validity = SPEC_VALID;
      else
         spec.validity = SPEC_INVALID;

      return (spec.validity == SPEC_VALID);
   }

   //+------------------------------------------------------------------+
   //| Load trading sessions for a symbol                                |
   //+------------------------------------------------------------------+
   void LoadTradingSessions(string symbol, ContractSpec &spec)
   {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);

      for(int day = 0; day < 7; day++)
      {
         spec.sessions[day].Reset();
         spec.sessions[day].dayOfWeek = day;

         datetime from, to;

         // Get first trading session for this day
         if(SymbolInfoSessionTrade(symbol, (ENUM_DAY_OF_WEEK)day, 0, from, to))
         {
            spec.sessions[day].openTime = from;
            spec.sessions[day].closeTime = to;
            spec.sessions[day].isActive = true;
         }
      }

      // Check if market is currently open
      spec.isMarketOpen = IsMarketOpen(symbol);

      // Calculate next open/close
      CalculateNextSessionTimes(spec);
   }

   //+------------------------------------------------------------------+
   //| Check if market is currently open                                 |
   //+------------------------------------------------------------------+
   bool IsMarketOpen(string symbol)
   {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);

      datetime from, to;

      // Check if trading session active for current day
      if(SymbolInfoSessionTrade(symbol, (ENUM_DAY_OF_WEEK)now.day_of_week, 0, from, to))
      {
         // Extract time portion
         datetime currentTime = TimeCurrent() % 86400;  // Seconds since midnight
         datetime openTime = from % 86400;
         datetime closeTime = to % 86400;

         // Handle overnight sessions
         if(closeTime < openTime)
         {
            // Session spans midnight
            return (currentTime >= openTime || currentTime <= closeTime);
         }
         else
         {
            return (currentTime >= openTime && currentTime <= closeTime);
         }
      }

      return false;
   }

   //+------------------------------------------------------------------+
   //| Calculate next session open/close times                           |
   //+------------------------------------------------------------------+
   void CalculateNextSessionTimes(ContractSpec &spec)
   {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);

      spec.nextOpen = 0;
      spec.nextClose = 0;

      // Look forward up to 7 days
      for(int offset = 0; offset < 7; offset++)
      {
         int checkDay = (now.day_of_week + offset) % 7;
         if(checkDay < 0 || checkDay >= 7) continue;  // Bounds check

         if(spec.sessions[checkDay].isActive)
         {
            datetime sessionOpen = spec.sessions[checkDay].openTime;
            datetime sessionClose = spec.sessions[checkDay].closeTime;

            // Calculate actual datetime
            datetime baseDate = TimeCurrent() - (now.hour * 3600 + now.min * 60 + now.sec);
            baseDate += offset * 86400;

            datetime fullOpen = baseDate + (sessionOpen % 86400);
            datetime fullClose = baseDate + (sessionClose % 86400);

            // Handle overnight sessions
            if(sessionClose < sessionOpen)
               fullClose += 86400;

            datetime current = TimeCurrent();

            if(spec.nextOpen == 0 && fullOpen > current)
               spec.nextOpen = fullOpen;

            if(spec.nextClose == 0 && fullClose > current)
               spec.nextClose = fullClose;

            if(spec.nextOpen != 0 && spec.nextClose != 0)
               break;
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Normalize specifications for RL (0-1 range)                       |
   //+------------------------------------------------------------------+
   void NormalizeSpec(ContractSpec &spec)
   {
      NormalizedSpecs &norm = spec.normalized;
      norm.lastUpdate = TimeCurrent();

      // Spread normalization (log scale for wide range)
      if(spec.spreadCurrent > 0)
      {
         double spreadLog = MathLog(spec.spreadCurrent + 1);
         double minLog = MathLog(m_spreadMin + 1);
         double maxLog = MathLog(m_spreadMax + 1);
         double logRange = maxLog - minLog;
         norm.spreadNorm = MathMin(1.0, MathMax(0.0,
            SafeDivide(spreadLog - minLog, logRange, 0.5)));
      }

      // Swap normalization (-1 to 1 range)
      double swapRange = m_swapMax - m_swapMin;
      if(swapRange > 0)
      {
         norm.swapLongNorm = MathMin(1.0, MathMax(-1.0,
            2.0 * SafeDivide(spec.swapLong - m_swapMin, swapRange, 0.5) - 1.0));
         norm.swapShortNorm = MathMin(1.0, MathMax(-1.0,
            2.0 * SafeDivide(spec.swapShort - m_swapMin, swapRange, 0.5) - 1.0));
      }

      // Commission normalization (assume max $50 per lot)
      norm.commissionNorm = MathMin(1.0, spec.commission / 50.0);

      // Margin normalization (assume 0.1% to 100% range)
      if(spec.marginInitial > 0 && spec.contractSize > 0)
      {
         double marginPercent = SafeDivide(spec.marginInitial, spec.contractSize, 0.0) * 100;
         norm.marginNorm = MathMin(1.0, SafeDivide(marginPercent, 100.0, 0.5));
      }

      // Session time normalization (time to close as fraction of session)
      if(spec.isMarketOpen && spec.nextClose > 0)
      {
         datetime remaining = spec.nextClose - TimeCurrent();
         // Assume 24-hour max session
         norm.sessionNorm = MathMin(1.0, MathMax(0.0,
            (double)remaining / 86400.0));
      }
      else
      {
         norm.sessionNorm = 0.0;  // Market closed
      }

      // Risk score (composite)
      norm.riskScoreNorm = CalculateRiskScore(spec);
   }

   //+------------------------------------------------------------------+
   //| Calculate composite risk score                                    |
   //+------------------------------------------------------------------+
   double CalculateRiskScore(ContractSpec &spec)
   {
      double score = 0.5;  // Base score

      // Higher spread = higher risk
      score += spec.normalized.spreadNorm * 0.2;

      // Higher margin = higher risk
      score += spec.normalized.marginNorm * 0.1;

      // Exotic assets = higher risk
      switch(spec.assetClass)
      {
         case ASSET_CRYPTO:
            score += 0.15;
            break;
         case ASSET_FOREX_EXOTIC:
            score += 0.1;
            break;
         case ASSET_INDEX:
         case ASSET_COMMODITY:
            score += 0.05;
            break;
      }

      // High stops level = higher risk
      if(spec.stopsLevel > 50)
         score += 0.05;

      // Limited trade direction = higher risk
      if(spec.tradeDirection != TRADE_DIR_BOTH)
         score += 0.05;

      return MathMin(1.0, MathMax(0.0, score));
   }

   //+------------------------------------------------------------------+
   //| Get or load specification with caching                            |
   //+------------------------------------------------------------------+
   bool GetSpec(string symbol, ContractSpec &spec)
   {
      // Check cache first
      int idx = FindSpecIndex(symbol);

      if(idx >= 0)
      {
         // Check if needs refresh
         if(TimeCurrent() - m_specs[idx].lastRefresh > m_refreshInterval)
         {
            // Refresh in background (return cached for now)
            RefreshSpec(idx);
         }

         spec = m_specs[idx];
         return (spec.validity == SPEC_VALID);
      }

      // Load new specification
      if(LoadSpec(symbol, spec))
      {
         NormalizeSpec(spec);
         AddToCache(spec);
         return true;
      }

      return false;
   }

   //+------------------------------------------------------------------+
   //| Find specification index in cache                                 |
   //+------------------------------------------------------------------+
   int FindSpecIndex(string symbol)
   {
      for(int i = 0; i < m_specCount; i++)
      {
         if(m_specs[i].symbol == symbol)
            return i;
      }
      return -1;
   }

   //+------------------------------------------------------------------+
   //| Add specification to cache                                        |
   //+------------------------------------------------------------------+
   void AddToCache(ContractSpec &spec)
   {
      int idx = FindSpecIndex(spec.symbol);

      if(idx >= 0)
      {
         m_specs[idx] = spec;
      }
      else
      {
         int newSize = m_specCount + 1;
         if(ArrayResize(m_specs, newSize) != newSize ||
            ArrayResize(m_symbolMap, newSize) != newSize)
         {
            Print("ERROR: ArrayResize failed for specs cache - spec not added: ", spec.symbol);
            return;
         }
         m_specs[m_specCount] = spec;
         m_symbolMap[m_specCount] = spec.symbol;
         m_specCount++;
      }
   }

   //+------------------------------------------------------------------+
   //| Refresh specification from server                                 |
   //+------------------------------------------------------------------+
   bool RefreshSpec(int idx)
   {
      if(idx < 0 || idx >= m_specCount)
         return false;

      string symbol = m_specs[idx].symbol;
      ContractSpec newSpec;

      if(LoadSpec(symbol, newSpec))
      {
         // Preserve some historical data
         newSpec.spreadTypical = (m_specs[idx].spreadTypical + newSpec.spreadCurrent) / 2.0;

         NormalizeSpec(newSpec);

         m_specs[idx] = newSpec;
         m_specs[idx].refreshFailures = 0;
         return true;
      }
      else
      {
         m_specs[idx].refreshFailures++;

         if(m_specs[idx].refreshFailures >= m_maxFailures)
            m_specs[idx].validity = SPEC_STALE;

         return false;
      }
   }

   //+------------------------------------------------------------------+
   //| Validate lot size and normalize to broker specs                   |
   //+------------------------------------------------------------------+
   double NormalizeLot(string symbol, double lots)
   {
      ContractSpec spec;
      if(!GetSpec(symbol, spec))
         return 0.0;

      // Clamp to min/max
      lots = MathMax(spec.lotMin, MathMin(spec.lotMax, lots));

      // Round to step
      if(spec.lotStep > 0)
         lots = MathFloor(lots / spec.lotStep) * spec.lotStep;

      // Final validation
      if(lots < spec.lotMin)
         return 0.0;

      return NormalizeDouble(lots, 2);
   }

   //+------------------------------------------------------------------+
   //| Validate and normalize stop loss price                            |
   //+------------------------------------------------------------------+
   double ValidateStopLoss(string symbol, double entryPrice, double stopPrice,
                           bool isBuy)
   {
      ContractSpec spec;
      if(!GetSpec(symbol, spec))
         return 0.0;

      double minDistance = spec.stopsLevel * spec.point;
      double spread = spec.spreadCurrent * spec.point;

      if(isBuy)
      {
         // Stop must be below entry for buy
         double minStop = entryPrice - minDistance - spread;
         if(stopPrice > minStop)
            stopPrice = minStop;
      }
      else
      {
         // Stop must be above entry for sell
         double minStop = entryPrice + minDistance + spread;
         if(stopPrice < minStop)
            stopPrice = minStop;
      }

      return NormalizeDouble(stopPrice, spec.digits);
   }

   //+------------------------------------------------------------------+
   //| Validate and normalize take profit price                          |
   //+------------------------------------------------------------------+
   double ValidateTakeProfit(string symbol, double entryPrice, double tpPrice,
                             bool isBuy)
   {
      ContractSpec spec;
      if(!GetSpec(symbol, spec))
         return 0.0;

      double minDistance = spec.stopsLevel * spec.point;
      double spread = spec.spreadCurrent * spec.point;

      if(isBuy)
      {
         // TP must be above entry for buy
         double minTP = entryPrice + minDistance + spread;
         if(tpPrice < minTP)
            tpPrice = minTP;
      }
      else
      {
         // TP must be below entry for sell
         double minTP = entryPrice - minDistance - spread;
         if(tpPrice > minTP)
            tpPrice = minTP;
      }

      return NormalizeDouble(tpPrice, spec.digits);
   }

   //+------------------------------------------------------------------+
   //| Check if trade direction is allowed                               |
   //+------------------------------------------------------------------+
   bool IsDirectionAllowed(string symbol, bool isBuy)
   {
      ContractSpec spec;
      if(!GetSpec(symbol, spec))
         return false;

      switch(spec.tradeDirection)
      {
         case TRADE_DIR_BOTH:
            return true;
         case TRADE_DIR_LONG_ONLY:
            return isBuy;
         case TRADE_DIR_SHORT_ONLY:
            return !isBuy;
         case TRADE_DIR_DISABLED:
            return false;
      }

      return false;
   }

   //+------------------------------------------------------------------+
   //| Get appropriate filling mode for symbol                           |
   //+------------------------------------------------------------------+
   ENUM_ORDER_TYPE_FILLING GetFillingMode(string symbol)
   {
      ContractSpec spec;
      if(!GetSpec(symbol, spec))
         return ORDER_FILLING_FOK;

      // Check what's available
      if((spec.fillingMode & SYMBOL_FILLING_IOC) != 0)
         return ORDER_FILLING_IOC;

      if((spec.fillingMode & SYMBOL_FILLING_FOK) != 0)
         return ORDER_FILLING_FOK;

      // Return or Cancel (BOC) for ECN
      return ORDER_FILLING_RETURN;
   }

   //+------------------------------------------------------------------+
   //| Calculate position value for risk management                      |
   //+------------------------------------------------------------------+
   double CalculatePositionValue(string symbol, double lots)
   {
      ContractSpec spec;
      if(!GetSpec(symbol, spec))
         return 0.0;

      double price = SymbolInfoDouble(symbol, SYMBOL_BID);
      return lots * spec.contractSize * price;
   }

   //+------------------------------------------------------------------+
   //| Calculate margin required for position                            |
   //+------------------------------------------------------------------+
   double CalculateMarginRequired(string symbol, double lots, bool isBuy)
   {
      double margin = 0.0;

      ENUM_ORDER_TYPE orderType = isBuy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      double price = isBuy ? SymbolInfoDouble(symbol, SYMBOL_ASK) :
                             SymbolInfoDouble(symbol, SYMBOL_BID);

      if(!OrderCalcMargin(orderType, symbol, lots, price, margin))
         return 0.0;

      return margin;
   }

   //+------------------------------------------------------------------+
   //| Get all cached specifications                                     |
   //+------------------------------------------------------------------+
   int GetAllSpecs(ContractSpec &specs[])
   {
      if(m_specCount == 0)
         return 0;

      if(ArrayResize(specs, m_specCount) != m_specCount)
      {
         Print("ERROR: ArrayResize failed for specs output array");
         return 0;
      }
      for(int i = 0; i < m_specCount; i++)
         specs[i] = m_specs[i];

      return m_specCount;
   }

   //+------------------------------------------------------------------+
   //| Set instrument risk parameters                                    |
   //+------------------------------------------------------------------+
   void SetInstrumentRisk(string symbol, InstrumentRisk &risk)
   {
      risk.symbol = symbol;
      risk.lastUpdate = TimeCurrent();

      // Find or add
      int count = ArraySize(m_instrRisk);
      for(int i = 0; i < count; i++)
      {
         if(m_instrRisk[i].symbol == symbol)
         {
            m_instrRisk[i] = risk;
            return;
         }
      }

      int newSize = count + 1;
      if(ArrayResize(m_instrRisk, newSize) != newSize)
      {
         Print("ERROR: ArrayResize failed for instrument risk - data not saved: ", symbol);
         return;
      }
      m_instrRisk[count] = risk;
   }

   //+------------------------------------------------------------------+
   //| Get instrument risk parameters                                    |
   //+------------------------------------------------------------------+
   bool GetInstrumentRisk(string symbol, InstrumentRisk &risk)
   {
      int count = ArraySize(m_instrRisk);
      for(int i = 0; i < count; i++)
      {
         if(m_instrRisk[i].symbol == symbol)
         {
            risk = m_instrRisk[i];
            return true;
         }
      }

      // Return defaults
      risk.Reset();
      risk.symbol = symbol;
      return false;
   }

   //+------------------------------------------------------------------+
   //| Set class-level risk parameters                                   |
   //+------------------------------------------------------------------+
   void SetClassRisk(ENUM_ASSET_CLASS assetClass, ClassRisk &risk)
   {
      int idx = (int)assetClass;
      if(idx >= 0 && idx < 10)
      {
         risk.assetClass = assetClass;
         m_classRisk[idx] = risk;
      }
   }

   //+------------------------------------------------------------------+
   //| Get class-level risk parameters                                   |
   //+------------------------------------------------------------------+
   ClassRisk GetClassRisk(ENUM_ASSET_CLASS assetClass)
   {
      int idx = (int)assetClass;
      if(idx >= 0 && idx < 10)
         return m_classRisk[idx];

      ClassRisk defaultRisk;
      defaultRisk.Reset();
      return defaultRisk;
   }

   //+------------------------------------------------------------------+
   //| Set portfolio risk parameters                                     |
   //+------------------------------------------------------------------+
   void SetPortfolioRisk(PortfolioRisk &risk)
   {
      m_portfolioRisk = risk;
   }

   //+------------------------------------------------------------------+
   //| Get portfolio risk parameters                                     |
   //+------------------------------------------------------------------+
   PortfolioRisk GetPortfolioRisk()
   {
      return m_portfolioRisk;
   }

   //+------------------------------------------------------------------+
   //| Export specifications for RL training                             |
   //+------------------------------------------------------------------+
   string ExportForRL(ContractSpec &spec)
   {
      string json = "{";

      // Identification
      json += "\"symbol\":\"" + spec.symbol + "\",";
      json += "\"baseName\":\"" + spec.baseName + "\",";
      json += "\"assetClass\":" + IntegerToString((int)spec.assetClass) + ",";

      // Normalized features
      json += "\"features\":[";
      json += DoubleToString(spec.normalized.spreadNorm, 6) + ",";
      json += DoubleToString(spec.normalized.swapLongNorm, 6) + ",";
      json += DoubleToString(spec.normalized.swapShortNorm, 6) + ",";
      json += DoubleToString(spec.normalized.commissionNorm, 6) + ",";
      json += DoubleToString(spec.normalized.marginNorm, 6) + ",";
      json += DoubleToString(spec.normalized.volatilityNorm, 6) + ",";
      json += DoubleToString(spec.normalized.liquidityNorm, 6) + ",";
      json += DoubleToString(spec.normalized.sessionNorm, 6) + ",";
      json += DoubleToString(spec.normalized.riskScoreNorm, 6);
      json += "],";

      // Raw values for context
      json += "\"spread\":" + DoubleToString(spec.spreadCurrent, 2) + ",";
      json += "\"swapLong\":" + DoubleToString(spec.swapLong, 4) + ",";
      json += "\"swapShort\":" + DoubleToString(spec.swapShort, 4) + ",";
      json += "\"marketOpen\":" + (spec.isMarketOpen ? "true" : "false") + ",";
      json += "\"tradeDir\":" + IntegerToString((int)spec.tradeDirection);

      json += "}";

      return json;
   }

   //+------------------------------------------------------------------+
   //| Self-healing: detect and fix spec anomalies                       |
   //+------------------------------------------------------------------+
   void SelfHeal()
   {
      for(int i = 0; i < m_specCount; i++)
      {
         // Validate integrity
         if(!m_specs[i].ValidateIntegrity())
         {
            // Attempt refresh
            RefreshSpec(i);
         }

         // Check for stale data
         if(TimeCurrent() - m_specs[i].lastRefresh > m_refreshInterval * 5)
         {
            m_specs[i].validity = SPEC_STALE;
            RefreshSpec(i);
         }

         // Check for impossible spread
         if(m_specs[i].spreadCurrent > 1000)
         {
            RefreshSpec(i);
         }

         // Recalculate checksum
         m_specs[i].checksum = m_specs[i].CalculateChecksum();
      }
   }

   //+------------------------------------------------------------------+
   //| Get broker suffix                                                 |
   //+------------------------------------------------------------------+
   string GetBrokerSuffix()
   {
      if(!m_suffixDetected)
         DetectBrokerSuffix();
      return m_brokerSuffix;
   }

   //+------------------------------------------------------------------+
   //| Check if today is triple swap day for symbol                      |
   //+------------------------------------------------------------------+
   bool IsTrippleSwapDay(string symbol)
   {
      ContractSpec spec;
      if(!GetSpec(symbol, spec))
         return false;

      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);

      if(spec.tripleSwapDay == SWAP_WEDNESDAY && now.day_of_week == 3)
         return true;
      if(spec.tripleSwapDay == SWAP_FRIDAY && now.day_of_week == 5)
         return true;

      return false;
   }

   //+------------------------------------------------------------------+
   //| Get swap cost for position held N days                            |
   //+------------------------------------------------------------------+
   double CalculateSwapCost(string symbol, double lots, bool isBuy, int days)
   {
      ContractSpec spec;
      if(!GetSpec(symbol, spec))
         return 0.0;

      double dailySwap = isBuy ? spec.swapLong : spec.swapShort;
      double totalSwap = 0.0;

      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);

      for(int d = 0; d < days; d++)
      {
         int dayOfWeek = (now.day_of_week + d) % 7;

         // Check for triple swap day
         if((spec.tripleSwapDay == SWAP_WEDNESDAY && dayOfWeek == 3) ||
            (spec.tripleSwapDay == SWAP_FRIDAY && dayOfWeek == 5))
         {
            totalSwap += dailySwap * 3;
         }
         else if(dayOfWeek > 0 && dayOfWeek < 6)  // Weekday
         {
            totalSwap += dailySwap;
         }
         // Weekend days often have no swap (already charged on triple day)
      }

      return totalSwap * lots;
   }

   //+------------------------------------------------------------------+
   //| Detect account margin mode (Hedging/Netting/FIFO)                |
   //+------------------------------------------------------------------+
   ENUM_ACCOUNT_MARGIN_MODE DetectAccountMode()
   {
      if(m_accountDetected)
         return m_accountSettings.marginMode;

      // Get account margin mode from MT5
      ENUM_ACCOUNT_MARGIN_MODE mode = (ENUM_ACCOUNT_MARGIN_MODE)
         AccountInfoInteger(ACCOUNT_MARGIN_MODE);

      switch(mode)
      {
         case ACCOUNT_MARGIN_MODE_RETAIL_HEDGING:
            m_accountSettings.marginMode = MARGIN_MODE_HEDGING;
            m_accountSettings.hedgingAllowed = true;
            m_accountSettings.fifoRequired = false;
            break;

         case ACCOUNT_MARGIN_MODE_RETAIL_NETTING:
            m_accountSettings.marginMode = MARGIN_MODE_NETTING;
            m_accountSettings.hedgingAllowed = false;
            m_accountSettings.fifoRequired = false;
            break;

         case ACCOUNT_MARGIN_MODE_EXCHANGE:
            // Exchange mode - typically netting with FIFO
            m_accountSettings.marginMode = MARGIN_MODE_FIFO;
            m_accountSettings.hedgingAllowed = false;
            m_accountSettings.fifoRequired = true;
            break;

         default:
            m_accountSettings.marginMode = MARGIN_MODE_HEDGING;
      }

      // Detect if FIFO is required (US/NFA regulation)
      string server = AccountInfoString(ACCOUNT_SERVER);
      string company = AccountInfoString(ACCOUNT_COMPANY);

      // US brokers typically require FIFO
      if(StringFind(server, "OANDA") >= 0 ||
         StringFind(server, "FOREX.com") >= 0 ||
         StringFind(server, "FXCM") >= 0 ||
         StringFind(server, "Interactive") >= 0 ||
         StringFind(company, "NFA") >= 0)
      {
         m_accountSettings.fifoRequired = true;
         m_accountSettings.closePriority = CLOSE_OLDEST_FIRST;
      }

      // Get account properties
      m_accountSettings.marginCallLevel = AccountInfoDouble(ACCOUNT_MARGIN_SO_CALL);
      m_accountSettings.stopOutLevel = AccountInfoDouble(ACCOUNT_MARGIN_SO_SO);
      m_accountSettings.accountCurrency = AccountInfoString(ACCOUNT_CURRENCY);
      m_accountSettings.leverage = (int)AccountInfoInteger(ACCOUNT_LEVERAGE);
      m_accountSettings.isDemo = (AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_DEMO);
      m_accountSettings.lastUpdate = TimeCurrent();

      m_accountDetected = true;
      return m_accountSettings.marginMode;
   }

   //+------------------------------------------------------------------+
   //| Get account settings                                              |
   //+------------------------------------------------------------------+
   AccountSettings GetAccountSettings()
   {
      if(!m_accountDetected)
         DetectAccountMode();
      return m_accountSettings;
   }

   //+------------------------------------------------------------------+
   //| Check if hedging is allowed                                       |
   //+------------------------------------------------------------------+
   bool IsHedgingAllowed()
   {
      if(!m_accountDetected)
         DetectAccountMode();
      return m_accountSettings.hedgingAllowed;
   }

   //+------------------------------------------------------------------+
   //| Check if FIFO is required                                         |
   //+------------------------------------------------------------------+
   bool IsFIFORequired()
   {
      if(!m_accountDetected)
         DetectAccountMode();
      return m_accountSettings.fifoRequired;
   }

   //+------------------------------------------------------------------+
   //| Get positions for symbol sorted by close priority                 |
   //+------------------------------------------------------------------+
   int GetPositionsSorted(string symbol, PositionInfo &positions[],
                          ENUM_CLOSE_PRIORITY priority, long magicFilter = 0)
   {
      ArrayResize(positions, 0);  // Clear array - always succeeds
      int count = 0;

      // Collect all positions for this symbol
      int total = PositionsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0)
            continue;

         if(PositionGetString(POSITION_SYMBOL) != symbol)
            continue;

         if(magicFilter != 0 && PositionGetInteger(POSITION_MAGIC) != magicFilter)
            continue;

         int newSize = count + 1;
         if(ArrayResize(positions, newSize) != newSize)
         {
            Print("ERROR: ArrayResize failed for positions array - incomplete data");
            break;  // Return what we have so far
         }
         positions[count].ticket = ticket;
         positions[count].symbol = symbol;
         positions[count].openTime = (datetime)PositionGetInteger(POSITION_TIME);
         positions[count].volume = PositionGetDouble(POSITION_VOLUME);
         positions[count].profit = PositionGetDouble(POSITION_PROFIT);
         positions[count].type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         positions[count].openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         positions[count].stopLoss = PositionGetDouble(POSITION_SL);
         positions[count].takeProfit = PositionGetDouble(POSITION_TP);
         positions[count].magic = PositionGetInteger(POSITION_MAGIC);
         count++;
      }

      // Sort by priority
      if(count > 1)
         SortPositions(positions, count, priority);

      return count;
   }

   //+------------------------------------------------------------------+
   //| Sort positions by priority                                        |
   //+------------------------------------------------------------------+
   void SortPositions(PositionInfo &positions[], int count, ENUM_CLOSE_PRIORITY priority)
   {
      // Simple bubble sort (positions array typically small)
      for(int i = 0; i < count - 1; i++)
      {
         for(int j = 0; j < count - i - 1; j++)
         {
            bool swap = false;

            switch(priority)
            {
               case CLOSE_OLDEST_FIRST:  // FIFO
                  swap = (positions[j].openTime > positions[j+1].openTime);
                  break;

               case CLOSE_NEWEST_FIRST:  // LIFO
                  swap = (positions[j].openTime < positions[j+1].openTime);
                  break;

               case CLOSE_LARGEST_FIRST:
                  swap = (positions[j].volume < positions[j+1].volume);
                  break;

               case CLOSE_SMALLEST_FIRST:
                  swap = (positions[j].volume > positions[j+1].volume);
                  break;

               case CLOSE_MOST_PROFIT:
                  swap = (positions[j].profit < positions[j+1].profit);
                  break;

               case CLOSE_MOST_LOSS:
                  swap = (positions[j].profit > positions[j+1].profit);
                  break;
            }

            if(swap)
            {
               PositionInfo temp = positions[j];
               positions[j] = positions[j+1];
               positions[j+1] = temp;
            }
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Get FIFO position to close (oldest for same direction)           |
   //+------------------------------------------------------------------+
   ulong GetFIFOPositionToClose(string symbol, ENUM_POSITION_TYPE type, long magic = 0)
   {
      PositionInfo positions[];
      int count = GetPositionsSorted(symbol, positions, CLOSE_OLDEST_FIRST, magic);

      for(int i = 0; i < count; i++)
      {
         if(positions[i].type == type)
            return positions[i].ticket;
      }

      return 0;  // No position found
   }

   //+------------------------------------------------------------------+
   //| Check if can open new position (respecting mode limits)          |
   //+------------------------------------------------------------------+
   bool CanOpenPosition(string symbol, bool isBuy, long magic = 0)
   {
      if(!m_accountDetected)
         DetectAccountMode();

      // Check symbol direction restrictions
      if(!IsDirectionAllowed(symbol, isBuy))
         return false;

      // Count existing positions
      int totalPositions = 0;
      int symbolPositions = 0;
      bool hasOpposite = false;

      for(int i = 0; i < PositionsTotal(); i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0)
            continue;

         if(magic != 0 && PositionGetInteger(POSITION_MAGIC) != magic)
            continue;

         totalPositions++;

         if(PositionGetString(POSITION_SYMBOL) == symbol)
         {
            symbolPositions++;

            ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)
               PositionGetInteger(POSITION_TYPE);

            if((isBuy && posType == POSITION_TYPE_SELL) ||
               (!isBuy && posType == POSITION_TYPE_BUY))
            {
               hasOpposite = true;
            }
         }
      }

      // Check limits
      if(totalPositions >= m_accountSettings.maxPositionsTotal)
         return false;

      if(symbolPositions >= m_accountSettings.maxPositionsPerSymbol)
         return false;

      // Check hedging rules
      if(hasOpposite && !m_accountSettings.hedgingAllowed)
      {
         // In netting mode, opposite position is allowed (will net)
         // In FIFO mode with no hedging, must close opposite first
         if(m_accountSettings.fifoRequired)
            return false;
      }

      return true;
   }

   //+------------------------------------------------------------------+
   //| Get net position for symbol (for netting accounts)               |
   //+------------------------------------------------------------------+
   double GetNetPosition(string symbol, long magic = 0)
   {
      double netVolume = 0.0;

      for(int i = 0; i < PositionsTotal(); i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0)
            continue;

         if(PositionGetString(POSITION_SYMBOL) != symbol)
            continue;

         if(magic != 0 && PositionGetInteger(POSITION_MAGIC) != magic)
            continue;

         double volume = PositionGetDouble(POSITION_VOLUME);
         ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)
            PositionGetInteger(POSITION_TYPE);

         if(type == POSITION_TYPE_BUY)
            netVolume += volume;
         else
            netVolume -= volume;
      }

      return netVolume;
   }

   //+------------------------------------------------------------------+
   //| Get required close sequence for FIFO compliance                   |
   //+------------------------------------------------------------------+
   int GetFIFOCloseSequence(string symbol, double volumeToClose,
                            ENUM_POSITION_TYPE type, ulong &tickets[],
                            double &volumes[], long magic = 0)
   {
      ArrayResize(tickets, 0);   // Clear arrays - always succeeds
      ArrayResize(volumes, 0);

      if(!m_accountSettings.fifoRequired)
         return 0;

      PositionInfo positions[];
      int count = GetPositionsSorted(symbol, positions, CLOSE_OLDEST_FIRST, magic);

      double remaining = volumeToClose;
      int closeCount = 0;

      for(int i = 0; i < count && remaining > 0; i++)
      {
         if(positions[i].type != type)
            continue;

         int newSize = closeCount + 1;
         if(ArrayResize(tickets, newSize) != newSize ||
            ArrayResize(volumes, newSize) != newSize)
         {
            Print("ERROR: ArrayResize failed in FIFO sequence - aborting to prevent invalid trades");
            return closeCount;  // Return what we have so far
         }

         tickets[closeCount] = positions[i].ticket;

         if(positions[i].volume <= remaining)
         {
            volumes[closeCount] = positions[i].volume;
            remaining -= positions[i].volume;
         }
         else
         {
            volumes[closeCount] = remaining;
            remaining = 0;
         }

         closeCount++;
      }

      return closeCount;
   }

   //+------------------------------------------------------------------+
   //| Get account margin mode string                                    |
   //+------------------------------------------------------------------+
   string GetMarginModeString()
   {
      if(!m_accountDetected)
         DetectAccountMode();

      switch(m_accountSettings.marginMode)
      {
         case MARGIN_MODE_HEDGING:
            return "Hedging";
         case MARGIN_MODE_NETTING:
            return "Netting";
         case MARGIN_MODE_FIFO:
            return "FIFO";
      }
      return "Unknown";
   }

   //+------------------------------------------------------------------+
   //| Export account settings for RL                                    |
   //+------------------------------------------------------------------+
   string ExportAccountForRL()
   {
      if(!m_accountDetected)
         DetectAccountMode();

      string json = "{";
      json += "\"marginMode\":" + IntegerToString((int)m_accountSettings.marginMode) + ",";
      json += "\"hedgingAllowed\":" + (m_accountSettings.hedgingAllowed ? "true" : "false") + ",";
      json += "\"fifoRequired\":" + (m_accountSettings.fifoRequired ? "true" : "false") + ",";
      json += "\"leverage\":" + IntegerToString(m_accountSettings.leverage) + ",";
      json += "\"marginCall\":" + DoubleToString(m_accountSettings.marginCallLevel, 2) + ",";
      json += "\"stopOut\":" + DoubleToString(m_accountSettings.stopOutLevel, 2) + ",";
      json += "\"isDemo\":" + (m_accountSettings.isDemo ? "true" : "false");
      json += "}";

      return json;
   }
};

//+------------------------------------------------------------------+
//| GLOBAL INSTANCE                                                   |
//+------------------------------------------------------------------+
CBrokerSpecManager g_brokerSpecs;

//+------------------------------------------------------------------+
//| Helper function - Normalize lot                                   |
//+------------------------------------------------------------------+
double NormalizeLotSize(string symbol, double lots)
{
   return g_brokerSpecs.NormalizeLot(symbol, lots);
}

//+------------------------------------------------------------------+
//| Helper function - Validate SL                                     |
//+------------------------------------------------------------------+
double ValidateSL(string symbol, double entry, double sl, bool isBuy)
{
   return g_brokerSpecs.ValidateStopLoss(symbol, entry, sl, isBuy);
}

//+------------------------------------------------------------------+
//| Helper function - Validate TP                                     |
//+------------------------------------------------------------------+
double ValidateTP(string symbol, double entry, double tp, bool isBuy)
{
   return g_brokerSpecs.ValidateTakeProfit(symbol, entry, tp, isBuy);
}

//+------------------------------------------------------------------+
//| Helper function - Get filling mode                                |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING GetBestFilling(string symbol)
{
   return g_brokerSpecs.GetFillingMode(symbol);
}

//+------------------------------------------------------------------+
//| Helper function - Check trade direction                           |
//+------------------------------------------------------------------+
bool CanTrade(string symbol, bool isBuy)
{
   return g_brokerSpecs.IsDirectionAllowed(symbol, isBuy);
}

#endif // VT_BROKER_SPECS_MQH
