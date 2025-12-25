//+------------------------------------------------------------------+
//|                                                    VT_Logger.mqh |
//|                                       VelocityTrader Framework   |
//|                    Central Logger for RL Replay Learning         |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>
#include <Trade\DealInfo.mqh>
#include <Trade\HistoryOrderInfo.mqh>
#include "VT_Definitions.mqh"

//+------------------------------------------------------------------+
//| ENUMERATIONS                                                      |
//+------------------------------------------------------------------+
enum ENUM_LOG_LEVEL
{
   LOG_DEBUG = 0,      // Debug - all messages
   LOG_INFO = 1,       // Info - normal operations
   LOG_TRADE = 2,      // Trade - trade actions only
   LOG_WARNING = 3,    // Warning - potential issues
   LOG_ERROR = 4,      // Error - errors only
   LOG_CRITICAL = 5    // Critical - severe errors
};

enum ENUM_LOG_DESTINATION
{
   LOG_DEST_NONE = 0,        // No logging
   LOG_DEST_FILE = 1,        // File only
   LOG_DEST_PRINT = 2,       // Print only
   LOG_DEST_BOTH = 3,        // File and Print
   LOG_DEST_RL_BUFFER = 4    // RL replay buffer
};

enum ENUM_EVENT_TYPE
{
   EVENT_TICK = 0,           // Price tick
   EVENT_ORDER_SENT = 1,     // Order sent
   EVENT_ORDER_FILLED = 2,   // Order filled
   EVENT_ORDER_CANCELED = 3, // Order canceled
   EVENT_ORDER_MODIFIED = 4, // Order modified
   EVENT_POSITION_OPENED = 5,  // Position opened
   EVENT_POSITION_CLOSED = 6,  // Position closed
   EVENT_POSITION_MODIFIED = 7, // Position modified
   EVENT_SL_HIT = 8,         // Stop loss hit
   EVENT_TP_HIT = 9,         // Take profit hit
   EVENT_MARGIN_CALL = 10,   // Margin call
   EVENT_SIGNAL = 11,        // Signal generated
   EVENT_STATE_CHANGE = 12,  // State change
   EVENT_ERROR = 13,         // Error occurred
   EVENT_MARKED = 14         // Marked for replay
};

enum ENUM_TRADE_TAG
{
   TAG_NONE = 0,             // No tag
   TAG_BERSERKER = 1,        // Berserker mode trade
   TAG_CONSERVATIVE = 2,     // Conservative trade
   TAG_REVERSAL = 3,         // Reversal trade
   TAG_BREAKOUT = 4,         // Breakout trade
   TAG_MOMENTUM = 5,         // Momentum trade
   TAG_SCALP = 6,            // Scalp trade
   TAG_SWING = 7,            // Swing trade
   TAG_NEWS = 8,             // News event trade
   TAG_HEDGE = 9,            // Hedging trade
   TAG_STUDY = 10,           // Study/marked for review
   TAG_MEAN_REVERSION = 11,  // Mean reversion (MR) trade
   TAG_TREND_FOLLOW = 12     // Trend following trade
};

enum ENUM_MARKER_TYPE
{
   MARKER_CIRCLE = 0,        // Circle on chart
   MARKER_ARROW_UP = 1,      // Arrow up
   MARKER_ARROW_DOWN = 2,    // Arrow down
   MARKER_STAR = 3,          // Star
   MARKER_CROSS = 4,         // Cross
   MARKER_DIAMOND = 5        // Diamond
};

//+------------------------------------------------------------------+
//| STRUCTURE - Market State for RL                                   |
//+------------------------------------------------------------------+
struct MarketState
{
   datetime          timestamp;
   string            symbol;
   double            bid;
   double            ask;
   double            spread;
   double            volume;         // Tick volume
   double            atr;            // ATR if available
   double            rsi;            // RSI if available
   double            maFast;         // Fast MA
   double            maSlow;         // Slow MA
   double            momentum;       // Price momentum
   int               trendDir;       // -1, 0, 1
   double            volatility;     // Normalized volatility
   bool              sessionOpen;    // Market session open

   void Reset()
   {
      timestamp = 0;
      symbol = "";
      bid = 0.0;
      ask = 0.0;
      spread = 0.0;
      volume = 0.0;
      atr = 0.0;
      rsi = 50.0;
      maFast = 0.0;
      maSlow = 0.0;
      momentum = 0.0;
      trendDir = 0;
      volatility = 0.5;
      sessionOpen = false;
   }

   // Export to JSON for RL
   string ToJSON()
   {
      return StringFormat(
         "{\"t\":%I64d,\"s\":\"%s\",\"b\":%.5f,\"a\":%.5f,\"sp\":%.2f,"
         "\"v\":%.0f,\"atr\":%.5f,\"rsi\":%.2f,\"maF\":%.5f,\"maS\":%.5f,"
         "\"mom\":%.5f,\"trend\":%d,\"vol\":%.4f,\"open\":%s}",
         timestamp, symbol, bid, ask, spread, volume, atr, rsi,
         maFast, maSlow, momentum, trendDir, volatility,
         sessionOpen ? "true" : "false");
   }

   // Export to normalized feature array (0-1)
   void ToFeatures(double &features[], int startIdx = 0)
   {
      if(ArraySize(features) < startIdx + 8)
         ArrayResize(features, startIdx + 8);

      features[startIdx + 0] = MathMin(1.0, spread / 50.0);  // Spread norm
      features[startIdx + 1] = rsi / 100.0;                   // RSI norm
      features[startIdx + 2] = (momentum + 1.0) / 2.0;        // Momentum norm
      features[startIdx + 3] = (double)(trendDir + 1) / 2.0;  // Trend norm
      features[startIdx + 4] = volatility;                    // Vol already normalized
      features[startIdx + 5] = sessionOpen ? 1.0 : 0.0;       // Session flag
      features[startIdx + 6] = MathMin(1.0, atr / 0.01);      // ATR norm
      features[startIdx + 7] = maFast > maSlow ? 1.0 : 0.0;   // MA crossover
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Marked Candle for Replay                              |
//+------------------------------------------------------------------+
struct MarkedCandle
{
   datetime          timestamp;
   string            symbol;
   ENUM_TIMEFRAMES   timeframe;
   int               barIndex;       // Bar index when marked
   double            open;
   double            high;
   double            low;
   double            close;
   long              volume;
   ENUM_TRADE_TAG    tag;            // Trade tag
   ENUM_MARKER_TYPE  markerType;
   color             markerColor;
   string            notes;          // User notes
   ulong             relatedTicket;  // Related trade ticket
   double            score;          // Importance score 0-1

   void Reset()
   {
      timestamp = 0;
      symbol = "";
      timeframe = PERIOD_M1;
      barIndex = 0;
      open = 0.0;
      high = 0.0;
      low = 0.0;
      close = 0.0;
      volume = 0;
      tag = TAG_NONE;
      markerType = MARKER_CIRCLE;
      markerColor = clrRed;
      notes = "";
      relatedTicket = 0;
      score = 0.5;
   }

   string ToJSON()
   {
      return StringFormat(
         "{\"t\":%I64d,\"s\":\"%s\",\"tf\":%d,\"bar\":%d,"
         "\"o\":%.5f,\"h\":%.5f,\"l\":%.5f,\"c\":%.5f,\"v\":%I64d,"
         "\"tag\":%d,\"marker\":%d,\"ticket\":%I64u,\"score\":%.4f,\"notes\":\"%s\"}",
         timestamp, symbol, (int)timeframe, barIndex,
         open, high, low, close, volume,
         (int)tag, (int)markerType, relatedTicket, score, notes);
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Action Taken for RL                                   |
//+------------------------------------------------------------------+
struct ActionRecord
{
   datetime          timestamp;
   string            symbol;
   ENUM_EVENT_TYPE   eventType;
   int               action;         // 0=hold, 1=buy, 2=sell, 3=close
   double            volume;
   double            entryPrice;
   double            stopLoss;
   double            takeProfit;
   ulong             ticket;
   long              magic;
   string            comment;
   int               retcode;        // Result code
   ENUM_TRADE_TAG    tag;            // Trade classification tag
   bool              isMarked;       // Marked for replay study

   void Reset()
   {
      timestamp = 0;
      symbol = "";
      eventType = EVENT_TICK;
      action = 0;
      volume = 0.0;
      entryPrice = 0.0;
      stopLoss = 0.0;
      takeProfit = 0.0;
      ticket = 0;
      magic = 0;
      comment = "";
      retcode = 0;
      tag = TAG_NONE;
      isMarked = false;
   }

   string ToJSON()
   {
      return StringFormat(
         "{\"t\":%I64d,\"s\":\"%s\",\"ev\":%d,\"act\":%d,\"vol\":%.2f,"
         "\"price\":%.5f,\"sl\":%.5f,\"tp\":%.5f,\"ticket\":%I64u,"
         "\"magic\":%d,\"ret\":%d,\"tag\":%d,\"marked\":%s}",
         timestamp, symbol, (int)eventType, action, volume,
         entryPrice, stopLoss, takeProfit, ticket, magic, retcode,
         (int)tag, isMarked ? "true" : "false");
   }

   string TagToString()
   {
      switch(tag)
      {
         case TAG_BERSERKER:       return "Berserker";
         case TAG_CONSERVATIVE:    return "Conservative";
         case TAG_REVERSAL:        return "Reversal";
         case TAG_BREAKOUT:        return "Breakout";
         case TAG_MOMENTUM:        return "Momentum";
         case TAG_SCALP:           return "Scalp";
         case TAG_SWING:           return "Swing";
         case TAG_NEWS:            return "News";
         case TAG_HEDGE:           return "Hedge";
         case TAG_STUDY:           return "Study";
         case TAG_MEAN_REVERSION:  return "MeanReversion";
         case TAG_TREND_FOLLOW:    return "TrendFollow";
         default:                  return "None";
      }
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Reward/Outcome for RL                                 |
//+------------------------------------------------------------------+
struct RewardRecord
{
   datetime          timestamp;
   ulong             ticket;
   double            profit;         // Realized P/L
   double            unrealizedPL;   // Unrealized P/L
   double            drawdown;       // Max drawdown
   double            reward;         // Calculated reward signal
   double            sharpe;         // Rolling Sharpe
   int               holdingBars;    // Bars held
   bool              hitSL;          // Stop loss hit
   bool              hitTP;          // Take profit hit

   void Reset()
   {
      timestamp = 0;
      ticket = 0;
      profit = 0.0;
      unrealizedPL = 0.0;
      drawdown = 0.0;
      reward = 0.0;
      sharpe = 0.0;
      holdingBars = 0;
      hitSL = false;
      hitTP = false;
   }

   string ToJSON()
   {
      return StringFormat(
         "{\"t\":%I64d,\"ticket\":%I64u,\"pnl\":%.2f,\"upnl\":%.2f,"
         "\"dd\":%.2f,\"r\":%.4f,\"sharpe\":%.4f,\"bars\":%d,"
         "\"sl\":%s,\"tp\":%s}",
         timestamp, ticket, profit, unrealizedPL, drawdown, reward,
         sharpe, holdingBars, hitSL ? "true" : "false", hitTP ? "true" : "false");
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE - Complete RL Experience Tuple                          |
//+------------------------------------------------------------------+
struct ExperienceTuple
{
   MarketState       state;          // S(t)
   ActionRecord      action;         // A(t)
   RewardRecord      reward;         // R(t)
   MarketState       nextState;      // S(t+1)
   bool              done;           // Episode terminal

   void Reset()
   {
      state.Reset();
      action.Reset();
      reward.Reset();
      nextState.Reset();
      done = false;
   }

   string ToJSON()
   {
      return StringFormat(
         "{\"state\":%s,\"action\":%s,\"reward\":%s,\"next\":%s,\"done\":%s}",
         state.ToJSON(), action.ToJSON(), reward.ToJSON(),
         nextState.ToJSON(), done ? "true" : "false");
   }
};

//+------------------------------------------------------------------+
//| CLASS - Central Logger for RL Replay Learning                     |
//+------------------------------------------------------------------+
class CVTLogger
{
private:
   // Settings
   ENUM_LOG_LEVEL       m_logLevel;
   ENUM_LOG_DESTINATION m_destination;
   string               m_logPath;
   string               m_logPrefix;
   bool                 m_initialized;

   // File handles
   int                  m_hLog;           // General log file
   int                  m_hTrades;        // Trade log file
   int                  m_hRL;            // RL experience file

   // RL Replay Buffer
   ExperienceTuple      m_replayBuffer[];
   int                  m_bufferSize;
   int                  m_bufferHead;
   int                  m_bufferCount;
   int                  m_maxBufferSize;

   // Trade lifecycle tracking using std MQL5
   CPositionInfo        m_posInfo;
   COrderInfo           m_orderInfo;
   CDealInfo            m_dealInfo;
   CHistoryOrderInfo    m_histOrderInfo;

   // Performance tracking
   double               m_totalPL;
   double               m_peakEquity;
   double               m_maxDrawdown;
   int                  m_totalTrades;
   int                  m_winningTrades;
   double               m_returns[];
   int                  m_returnsCount;

   // Session tracking
   datetime             m_sessionStart;
   long                 m_tickCount;
   long                 m_eventCount;

   // Marked candles/trades for replay study
   MarkedCandle         m_markedCandles[];
   int                  m_markedCount;
   int                  m_maxMarkedCandles;
   int                  m_hMarked;        // Marked candles file
   string               m_markerPrefix;   // Chart object prefix

public:
   //+------------------------------------------------------------------+
   //| Constructor                                                       |
   //+------------------------------------------------------------------+
   CVTLogger()
   {
      m_logLevel = LOG_INFO;
      m_destination = LOG_DEST_FILE;
      m_logPath = "VelocityTrader\\Logs";
      m_logPrefix = "VT";
      m_initialized = false;

      m_hLog = INVALID_HANDLE;
      m_hTrades = INVALID_HANDLE;
      m_hRL = INVALID_HANDLE;

      m_bufferSize = 0;
      m_bufferHead = 0;
      m_bufferCount = 0;
      m_maxBufferSize = 100000;  // 100k experiences default

      m_totalPL = 0.0;
      m_peakEquity = 0.0;
      m_maxDrawdown = 0.0;
      m_totalTrades = 0;
      m_winningTrades = 0;
      m_returnsCount = 0;

      m_sessionStart = 0;
      m_tickCount = 0;
      m_eventCount = 0;

      m_markedCount = 0;
      m_maxMarkedCandles = 10000;
      m_hMarked = INVALID_HANDLE;
      m_markerPrefix = "VT_MARK_";
   }

   //+------------------------------------------------------------------+
   //| Destructor                                                        |
   //+------------------------------------------------------------------+
   ~CVTLogger()
   {
      Shutdown();
   }

   //+------------------------------------------------------------------+
   //| Initialize logger                                                 |
   //+------------------------------------------------------------------+
   bool Init(string prefix = "VT", ENUM_LOG_LEVEL level = LOG_INFO,
             ENUM_LOG_DESTINATION dest = LOG_DEST_FILE, int bufferSize = 100000)
   {
      // Validate inputs
      if(StringLen(prefix) == 0)
      {
         prefix = "VT";  // Default prefix
      }

      if(bufferSize < 0)
      {
         bufferSize = 100000;  // Default buffer size
      }

      // Cap buffer size to prevent excessive memory allocation
      if(bufferSize > 10000000)  // 10 million max
      {
         Print("WARNING: CVTLogger::Init - buffer size capped at 10,000,000");
         bufferSize = 10000000;
      }

      m_logPrefix = prefix;
      m_logLevel = level;
      m_destination = dest;
      m_maxBufferSize = bufferSize;
      m_sessionStart = TimeCurrent();

      // Create log directory with proper error handling
      if(!FolderCreate(m_logPath))
      {
         int err = GetLastError();
         // Error 5020 = folder already exists, which is fine
         if(err != 5020 && err != 0)
         {
            Print("WARNING: CVTLogger::Init - Cannot create log folder: ", m_logPath, " (error: ", err, ")");
         }
      }

      // Open log files
      if(m_destination == LOG_DEST_FILE || m_destination == LOG_DEST_BOTH)
      {
         string dateStr = TimeToString(TimeCurrent(), TIME_DATE);
         StringReplace(dateStr, ".", "");

         // Open general log file
         string logFile = m_logPath + "\\" + m_logPrefix + "_" + dateStr + ".log";
         m_hLog = FileOpen(logFile, FILE_WRITE|FILE_TXT|FILE_SHARE_READ);
         if(m_hLog == INVALID_HANDLE)
         {
            int err = GetLastError();
            Print("WARNING: CVTLogger::Init - Cannot open log file: ", logFile, " (error: ", err, ")");
         }

         // Open trades CSV file
         string tradeFile = m_logPath + "\\" + m_logPrefix + "_trades_" + dateStr + ".csv";
         m_hTrades = FileOpen(tradeFile, FILE_WRITE|FILE_CSV|FILE_SHARE_READ, ',');
         if(m_hTrades != INVALID_HANDLE)
         {
            // Write CSV header
            FileWrite(m_hTrades, "Timestamp", "Symbol", "Action", "Volume",
                     "Price", "SL", "TP", "Ticket", "Profit", "Comment");
         }
         else
         {
            int err = GetLastError();
            Print("WARNING: CVTLogger::Init - Cannot open trades file: ", tradeFile, " (error: ", err, ")");
         }

         // Open RL experience file
         string rlFile = m_logPath + "\\" + m_logPrefix + "_rl_" + dateStr + ".jsonl";
         m_hRL = FileOpen(rlFile, FILE_WRITE|FILE_TXT|FILE_SHARE_READ);
         if(m_hRL == INVALID_HANDLE)
         {
            int err = GetLastError();
            Print("WARNING: CVTLogger::Init - Cannot open RL file: ", rlFile, " (error: ", err, ")");
         }
      }

      // Initialize replay buffer
      if(m_destination == LOG_DEST_RL_BUFFER || m_maxBufferSize > 0)
      {
         int resized = ArrayResize(m_replayBuffer, m_maxBufferSize);
         if(resized != m_maxBufferSize)
         {
            Print("WARNING: CVTLogger::Init - Could not allocate full replay buffer. Requested: ",
                  m_maxBufferSize, ", Allocated: ", resized);
            m_bufferSize = resized;
         }
         else
         {
            m_bufferSize = m_maxBufferSize;
         }
      }

      // Initialize returns tracking
      if(ArrayResize(m_returns, 1000) != 1000)
      {
         Print("WARNING: CVTLogger::Init - Could not allocate returns array");
      }

      m_initialized = true;

      Log(LOG_INFO, "Logger initialized - Level: " + EnumToString(level));

      return true;
   }

   //+------------------------------------------------------------------+
   //| Shutdown logger                                                   |
   //+------------------------------------------------------------------+
   void Shutdown()
   {
      if(!m_initialized)
         return;

      // Write final stats
      Log(LOG_INFO, StringFormat(
         "Session Summary - Ticks: %I64d, Events: %I64d, Trades: %d, P/L: %.2f",
         m_tickCount, m_eventCount, m_totalTrades, m_totalPL));

      // Close files
      if(m_hLog != INVALID_HANDLE)
      {
         FileClose(m_hLog);
         m_hLog = INVALID_HANDLE;
      }

      if(m_hTrades != INVALID_HANDLE)
      {
         FileClose(m_hTrades);
         m_hTrades = INVALID_HANDLE;
      }

      if(m_hRL != INVALID_HANDLE)
      {
         FileClose(m_hRL);
         m_hRL = INVALID_HANDLE;
      }

      m_initialized = false;
   }

   //+------------------------------------------------------------------+
   //| Log message at specified level                                    |
   //+------------------------------------------------------------------+
   void Log(ENUM_LOG_LEVEL level, string message)
   {
      if(level < m_logLevel)
         return;

      string levelStr = "";
      switch(level)
      {
         case LOG_DEBUG:    levelStr = "DEBUG"; break;
         case LOG_INFO:     levelStr = "INFO"; break;
         case LOG_TRADE:    levelStr = "TRADE"; break;
         case LOG_WARNING:  levelStr = "WARN"; break;
         case LOG_ERROR:    levelStr = "ERROR"; break;
         case LOG_CRITICAL: levelStr = "CRIT"; break;
      }

      string timestamp = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
      string logLine = StringFormat("[%s] [%s] %s", timestamp, levelStr, message);

      if(m_destination == LOG_DEST_PRINT || m_destination == LOG_DEST_BOTH)
      {
         Print(logLine);
      }

      if((m_destination == LOG_DEST_FILE || m_destination == LOG_DEST_BOTH) &&
         m_hLog != INVALID_HANDLE)
      {
         FileWriteString(m_hLog, logLine + "\n");
         FileFlush(m_hLog);
      }

      m_eventCount++;
   }

   //+------------------------------------------------------------------+
   //| Log debug message                                                 |
   //+------------------------------------------------------------------+
   void Debug(string message) { Log(LOG_DEBUG, message); }

   //+------------------------------------------------------------------+
   //| Log info message                                                  |
   //+------------------------------------------------------------------+
   void Info(string message) { Log(LOG_INFO, message); }

   //+------------------------------------------------------------------+
   //| Log warning message                                               |
   //+------------------------------------------------------------------+
   void Warn(string message) { Log(LOG_WARNING, message); }

   //+------------------------------------------------------------------+
   //| Log error message                                                 |
   //+------------------------------------------------------------------+
   void Error(string message) { Log(LOG_ERROR, message); }

   //+------------------------------------------------------------------+
   //| Log trade action                                                  |
   //+------------------------------------------------------------------+
   void LogTrade(ActionRecord &action)
   {
      string actionStr = "";
      switch(action.action)
      {
         case 0: actionStr = "HOLD"; break;
         case 1: actionStr = "BUY"; break;
         case 2: actionStr = "SELL"; break;
         case 3: actionStr = "CLOSE"; break;
      }

      Log(LOG_TRADE, StringFormat("%s %s %.2f @ %.5f SL:%.5f TP:%.5f [#%I64u]",
         actionStr, action.symbol, action.volume, action.entryPrice,
         action.stopLoss, action.takeProfit, action.ticket));

      // Write to trades CSV
      if(m_hTrades != INVALID_HANDLE)
      {
         FileWrite(m_hTrades,
            TimeToString(action.timestamp, TIME_DATE|TIME_SECONDS),
            action.symbol, actionStr, action.volume, action.entryPrice,
            action.stopLoss, action.takeProfit, action.ticket, 0.0, action.comment);
         FileFlush(m_hTrades);
      }
   }

   //+------------------------------------------------------------------+
   //| Log order send using standard CTrade result                       |
   //+------------------------------------------------------------------+
   void LogOrderResult(CTrade &trade, string symbol, string actionDesc)
   {
      MqlTradeResult result = trade.ResultRetcode() == 0 ?
         MqlTradeResult() : trade.ResultRetcode() > 0 ? MqlTradeResult() : MqlTradeResult();

      uint retcode = trade.ResultRetcode();

      if(retcode == TRADE_RETCODE_DONE || retcode == TRADE_RETCODE_PLACED)
      {
         Log(LOG_TRADE, StringFormat("%s %s - Ticket: %I64u, Price: %.5f",
            actionDesc, symbol, trade.ResultOrder(), trade.ResultPrice()));
      }
      else
      {
         Log(LOG_ERROR, StringFormat("%s %s FAILED - Code: %d, Desc: %s",
            actionDesc, symbol, retcode, trade.ResultRetcodeDescription()));
      }
   }

   //+------------------------------------------------------------------+
   //| Log position opened                                               |
   //+------------------------------------------------------------------+
   void LogPositionOpen(ulong ticket)
   {
      if(!m_posInfo.SelectByTicket(ticket))
         return;

      ActionRecord action;
      action.Reset();
      action.timestamp = TimeCurrent();
      action.symbol = m_posInfo.Symbol();
      action.eventType = EVENT_POSITION_OPENED;
      action.action = m_posInfo.PositionType() == POSITION_TYPE_BUY ? 1 : 2;
      action.volume = m_posInfo.Volume();
      action.entryPrice = m_posInfo.PriceOpen();
      action.stopLoss = m_posInfo.StopLoss();
      action.takeProfit = m_posInfo.TakeProfit();
      action.ticket = ticket;
      action.magic = m_posInfo.Magic();
      action.comment = m_posInfo.Comment();
      action.retcode = TRADE_RETCODE_DONE;

      LogTrade(action);
      m_totalTrades++;
   }

   //+------------------------------------------------------------------+
   //| Log position closed                                               |
   //+------------------------------------------------------------------+
   void LogPositionClose(ulong ticket, double profit, bool hitSL = false, bool hitTP = false)
   {
      ActionRecord action;
      action.Reset();
      action.timestamp = TimeCurrent();
      action.eventType = hitSL ? EVENT_SL_HIT : (hitTP ? EVENT_TP_HIT : EVENT_POSITION_CLOSED);
      action.action = 3;  // Close
      action.ticket = ticket;
      action.retcode = TRADE_RETCODE_DONE;

      Log(LOG_TRADE, StringFormat("CLOSE #%I64u - Profit: %.2f %s",
         ticket, profit, hitSL ? "(SL)" : (hitTP ? "(TP)" : "")));

      // Track performance
      m_totalPL += profit;
      if(profit > 0)
         m_winningTrades++;

      // Track returns
      if(m_returnsCount < ArraySize(m_returns))
      {
         m_returns[m_returnsCount] = profit;
         m_returnsCount++;
      }

      // Update drawdown
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      if(equity > m_peakEquity)
         m_peakEquity = equity;

      double dd = SafeDivide(m_peakEquity - equity, m_peakEquity, 0.0) * 100;
      if(dd > m_maxDrawdown)
         m_maxDrawdown = dd;
   }

   //+------------------------------------------------------------------+
   //| Record tick for RL                                                |
   //+------------------------------------------------------------------+
   void RecordTick(string symbol)
   {
      m_tickCount++;
   }

   //+------------------------------------------------------------------+
   //| Record market state for RL                                        |
   //+------------------------------------------------------------------+
   void RecordState(MarketState &state)
   {
      if(m_hRL != INVALID_HANDLE)
      {
         FileWriteString(m_hRL, state.ToJSON() + "\n");

         // Flush periodically
         if(m_tickCount % 1000 == 0)
            FileFlush(m_hRL);
      }
   }

   //+------------------------------------------------------------------+
   //| Record experience tuple for RL replay                             |
   //+------------------------------------------------------------------+
   void RecordExperience(ExperienceTuple &exp)
   {
      // Write to RL file
      if(m_hRL != INVALID_HANDLE)
      {
         FileWriteString(m_hRL, exp.ToJSON() + "\n");
      }

      // Add to replay buffer
      if(m_bufferSize > 0)
      {
         int idx = m_bufferHead;
         m_replayBuffer[idx] = exp;
         m_bufferHead = (m_bufferHead + 1) % m_bufferSize;
         if(m_bufferCount < m_bufferSize)
            m_bufferCount++;
      }
   }

   //+------------------------------------------------------------------+
   //| Sample random batch from replay buffer                            |
   //+------------------------------------------------------------------+
   int SampleBatch(ExperienceTuple &batch[], int batchSize)
   {
      // Validate inputs
      if(batchSize <= 0)
      {
         return 0;
      }

      if(m_bufferCount == 0)
      {
         return 0;
      }

      int actualSize = MathMin(batchSize, m_bufferCount);
      if(actualSize <= 0)
      {
         return 0;
      }

      if(ArrayResize(batch, actualSize) != actualSize)
      {
         Print("WARNING: CVTLogger::SampleBatch - cannot allocate batch array");
         return 0;
      }

      for(int i = 0; i < actualSize; i++)
      {
         // Use modulo with bounds check to prevent any overflow issues
         int randIdx = MathAbs(MathRand()) % m_bufferCount;
         if(randIdx >= 0 && randIdx < m_bufferCount)
         {
            batch[i] = m_replayBuffer[randIdx];
         }
         else
         {
            // Fallback to first entry if something goes wrong
            batch[i] = m_replayBuffer[0];
         }
      }

      return actualSize;
   }

   //+------------------------------------------------------------------+
   //| Calculate reward from trade                                       |
   //+------------------------------------------------------------------+
   double CalculateReward(double profit, double drawdown, int holdingBars,
                          bool hitSL, bool hitTP)
   {
      // Reward shaping for RL
      double reward = 0.0;

      // Base reward from profit (normalized by risk)
      reward = profit / 100.0;  // Scale by typical risk

      // Penalty for drawdown
      reward -= drawdown * 0.01;

      // Slight penalty for long holding times (encourage efficiency)
      reward -= holdingBars * 0.001;

      // Bonus for hitting TP (good prediction)
      if(hitTP)
         reward += 0.1;

      // Penalty for hitting SL (bad prediction)
      if(hitSL)
         reward -= 0.05;

      return reward;
   }

   //+------------------------------------------------------------------+
   //| Calculate rolling Sharpe ratio                                    |
   //+------------------------------------------------------------------+
   double CalculateSharpe(int lookback = 50)
   {
      if(m_returnsCount < 2)
         return 0.0;

      int n = MathMin(lookback, m_returnsCount);
      if(n <= 0) return 0.0;

      int start = m_returnsCount - n;

      double sum = 0.0;
      for(int i = start; i < m_returnsCount; i++)
         sum += m_returns[i];
      double mean = SafeDivide(sum, (double)n, 0.0);

      double sumSq = 0.0;
      for(int i = start; i < m_returnsCount; i++)
         sumSq += MathPow(m_returns[i] - mean, 2);
      double stdDev = MathSqrt(SafeDivide(sumSq, (double)n, 0.0));

      if(stdDev < 0.0001)
         return 0.0;

      return SafeDivide(mean, stdDev, 0.0);
   }

   //+------------------------------------------------------------------+
   //| Get statistics                                                    |
   //+------------------------------------------------------------------+
   double GetTotalPL()        { return m_totalPL; }
   double GetMaxDrawdown()    { return m_maxDrawdown; }
   int    GetTotalTrades()    { return m_totalTrades; }
   int    GetWinningTrades()  { return m_winningTrades; }
   double GetWinRate()        { return m_totalTrades > 0 ?
                                 (double)m_winningTrades / m_totalTrades * 100 : 0; }
   long   GetTickCount()      { return m_tickCount; }
   long   GetEventCount()     { return m_eventCount; }
   int    GetBufferCount()    { return m_bufferCount; }

   //+------------------------------------------------------------------+
   //| Export replay buffer to file                                      |
   //+------------------------------------------------------------------+
   bool ExportReplayBuffer(string filename)
   {
      // Validate filename
      if(StringLen(filename) == 0)
      {
         Log(LOG_ERROR, "ExportReplayBuffer - empty filename provided");
         return false;
      }

      if(m_bufferCount == 0)
      {
         Log(LOG_WARNING, "ExportReplayBuffer - buffer is empty, nothing to export");
         return false;
      }

      string path = m_logPath + "\\" + filename;
      int h = FileOpen(path, FILE_WRITE|FILE_TXT);

      if(h == INVALID_HANDLE)
      {
         int err = GetLastError();
         Log(LOG_ERROR, StringFormat("ExportReplayBuffer - cannot create file: %s (error: %d)", path, err));
         return false;
      }

      int exportedCount = 0;
      int errorCount = 0;

      for(int i = 0; i < m_bufferCount; i++)
      {
         string json = m_replayBuffer[i].ToJSON();
         if(StringLen(json) > 0)
         {
            uint written = FileWriteString(h, json + "\n");
            if(written > 0)
            {
               exportedCount++;
            }
            else
            {
               errorCount++;
            }
         }
         else
         {
            errorCount++;
         }
      }

      FileClose(h);

      if(errorCount > 0)
      {
         Log(LOG_WARNING, StringFormat("ExportReplayBuffer - %d/%d entries had errors",
             errorCount, m_bufferCount));
      }

      Log(LOG_INFO, StringFormat("Exported %d experiences to %s", exportedCount, filename));

      return exportedCount > 0;
   }

   //+------------------------------------------------------------------+
   //| Clear replay buffer                                               |
   //+------------------------------------------------------------------+
   void ClearBuffer()
   {
      m_bufferHead = 0;
      m_bufferCount = 0;
      Log(LOG_INFO, "Replay buffer cleared");
   }

   //+------------------------------------------------------------------+
   //| Log performance summary                                           |
   //+------------------------------------------------------------------+
   void LogPerformanceSummary()
   {
      Log(LOG_INFO, "=== Performance Summary ===");
      Log(LOG_INFO, StringFormat("Total P/L: %.2f", m_totalPL));
      Log(LOG_INFO, StringFormat("Trades: %d (Win: %d, Loss: %d)",
         m_totalTrades, m_winningTrades, m_totalTrades - m_winningTrades));
      Log(LOG_INFO, StringFormat("Win Rate: %.1f%%", GetWinRate()));
      Log(LOG_INFO, StringFormat("Max Drawdown: %.2f%%", m_maxDrawdown));
      Log(LOG_INFO, StringFormat("Sharpe Ratio: %.4f", CalculateSharpe()));
      Log(LOG_INFO, StringFormat("Buffer Size: %d/%d", m_bufferCount, m_bufferSize));
   }

   //+------------------------------------------------------------------+
   //| Process trade history using std MQL5                              |
   //+------------------------------------------------------------------+
   void ProcessDealHistory(datetime from, datetime to, long magic = 0)
   {
      if(!HistorySelect(from, to))
         return;

      int deals = HistoryDealsTotal();

      for(int i = 0; i < deals; i++)
      {
         ulong ticket = HistoryDealGetTicket(i);
         if(ticket == 0)
            continue;

         if(!m_dealInfo.SelectByIndex(i))
            continue;

         if(magic != 0 && m_dealInfo.Magic() != magic)
            continue;

         ENUM_DEAL_ENTRY entry = m_dealInfo.Entry();

         if(entry == DEAL_ENTRY_IN)
         {
            Log(LOG_DEBUG, StringFormat("Deal IN: %s %.2f @ %.5f",
               m_dealInfo.Symbol(), m_dealInfo.Volume(), m_dealInfo.Price()));
         }
         else if(entry == DEAL_ENTRY_OUT)
         {
            Log(LOG_DEBUG, StringFormat("Deal OUT: %s %.2f @ %.5f P/L: %.2f",
               m_dealInfo.Symbol(), m_dealInfo.Volume(), m_dealInfo.Price(),
               m_dealInfo.Profit()));
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Sync with live positions using std MQL5                           |
   //+------------------------------------------------------------------+
   void SyncPositions(long magic = 0)
   {
      int total = PositionsTotal();

      for(int i = 0; i < total; i++)
      {
         if(!m_posInfo.SelectByIndex(i))
            continue;

         if(magic != 0 && m_posInfo.Magic() != magic)
            continue;

         Log(LOG_DEBUG, StringFormat("Position: %s %s %.2f @ %.5f P/L: %.2f",
            m_posInfo.Symbol(),
            m_posInfo.TypeDescription(),
            m_posInfo.Volume(),
            m_posInfo.PriceOpen(),
            m_posInfo.Profit()));
      }
   }

   //+------------------------------------------------------------------+
   //| Set log level                                                     |
   //+------------------------------------------------------------------+
   void SetLogLevel(ENUM_LOG_LEVEL level)
   {
      m_logLevel = level;
   }

   //+------------------------------------------------------------------+
   //| Set destination                                                   |
   //+------------------------------------------------------------------+
   void SetDestination(ENUM_LOG_DESTINATION dest)
   {
      m_destination = dest;
   }

   //+------------------------------------------------------------------+
   //| Mark current candle for replay study                              |
   //+------------------------------------------------------------------+
   bool MarkCandle(string symbol, ENUM_TIMEFRAMES tf, ENUM_TRADE_TAG tag,
                   color clr = clrRed, string notes = "", ulong ticket = 0,
                   ENUM_MARKER_TYPE marker = MARKER_CIRCLE, double score = 0.5)
   {
      // Validate symbol
      if(StringLen(symbol) == 0)
      {
         Print("ERROR: CVTLogger::MarkCandle - empty symbol provided");
         return false;
      }

      // Validate score is in valid range
      if(!MathIsValidNumber(score) || score < 0.0 || score > 1.0)
      {
         score = 0.5;  // Default score
      }

      if(m_markedCount >= m_maxMarkedCandles)
      {
         // Shift array to make room
         for(int i = 0; i < m_markedCount - 1; i++)
            m_markedCandles[i] = m_markedCandles[i + 1];
         m_markedCount--;
      }

      if(m_markedCount >= ArraySize(m_markedCandles))
      {
         int newSize = m_markedCount + 100;
         if(ArrayResize(m_markedCandles, newSize) != newSize)
         {
            Print("ERROR: CVTLogger::MarkCandle - cannot allocate memory for marked candles");
            return false;
         }
      }

      MarkedCandle mc;
      mc.Reset();
      mc.timestamp = TimeCurrent();
      mc.symbol = symbol;
      mc.timeframe = tf;
      mc.barIndex = 0;  // Current bar

      // Get OHLCV with validation
      mc.open = iOpen(symbol, tf, 0);
      mc.high = iHigh(symbol, tf, 0);
      mc.low = iLow(symbol, tf, 0);
      mc.close = iClose(symbol, tf, 0);
      mc.volume = iVolume(symbol, tf, 0);

      // Validate OHLCV data
      if(mc.open <= 0 || mc.high <= 0 || mc.low <= 0 || mc.close <= 0)
      {
         Print("WARNING: CVTLogger::MarkCandle - invalid OHLCV data for ", symbol,
               " (O:", mc.open, " H:", mc.high, " L:", mc.low, " C:", mc.close, ")");
         // Don't fail completely, but use current price if available
         double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
         if(bid > 0)
         {
            mc.open = mc.high = mc.low = mc.close = bid;
         }
         else
         {
            return false;
         }
      }

      mc.tag = tag;
      mc.markerType = marker;
      mc.markerColor = clr;
      mc.notes = notes;
      mc.relatedTicket = ticket;
      mc.score = score;

      // Ensure array has space before assignment
      if(m_markedCount >= ArraySize(m_markedCandles))
      {
         int newSize = m_markedCount + 100;
         if(ArrayResize(m_markedCandles, newSize) != newSize)
         {
            Print("ERROR: CVTLogger::MarkCandle - failed to resize array");
            return false;
         }
      }
      m_markedCandles[m_markedCount] = mc;
      m_markedCount++;

      // Draw on chart
      DrawMarker(mc);

      // Log it
      Log(LOG_TRADE, StringFormat("MARKED: %s [%s] - %s %s",
         symbol, EnumToString(tag), mc.notes, EnumToString(marker)));

      // Write to marked file
      WriteMarkedCandle(mc);

      return true;
   }

   //+------------------------------------------------------------------+
   //| Mark trade with Berserker tag (red circle)                        |
   //+------------------------------------------------------------------+
   void MarkBerserker(string symbol, ulong ticket = 0, string notes = "")
   {
      MarkCandle(symbol, PERIOD_CURRENT, TAG_BERSERKER, clrRed, notes,
                 ticket, MARKER_CIRCLE, 0.9);
   }

   //+------------------------------------------------------------------+
   //| Mark trade with specific tag                                      |
   //+------------------------------------------------------------------+
   void MarkTrade(ulong ticket, ENUM_TRADE_TAG tag, string notes = "")
   {
      if(!PositionSelectByTicket(ticket))
         return;

      string symbol = PositionGetString(POSITION_SYMBOL);
      color clr = clrGray;

      switch(tag)
      {
         case TAG_BERSERKER:    clr = clrRed; break;
         case TAG_CONSERVATIVE: clr = clrGreen; break;
         case TAG_REVERSAL:     clr = clrOrange; break;
         case TAG_BREAKOUT:     clr = clrBlue; break;
         case TAG_MOMENTUM:     clr = clrPurple; break;
         case TAG_SCALP:        clr = clrYellow; break;
         case TAG_SWING:        clr = clrCyan; break;
         case TAG_NEWS:         clr = clrMagenta; break;
         case TAG_HEDGE:        clr = clrLime; break;
         case TAG_STUDY:        clr = clrWhite; break;
         default:               clr = clrGray;
      }

      MarkCandle(symbol, PERIOD_CURRENT, tag, clr, notes, ticket);
   }

   //+------------------------------------------------------------------+
   //| Mark historical bar for study                                     |
   //+------------------------------------------------------------------+
   void MarkBar(string symbol, ENUM_TIMEFRAMES tf, int barShift,
                ENUM_TRADE_TAG tag, string notes = "")
   {
      MarkedCandle mc;
      mc.Reset();
      mc.timestamp = iTime(symbol, tf, barShift);
      mc.symbol = symbol;
      mc.timeframe = tf;
      mc.barIndex = barShift;

      mc.open = iOpen(symbol, tf, barShift);
      mc.high = iHigh(symbol, tf, barShift);
      mc.low = iLow(symbol, tf, barShift);
      mc.close = iClose(symbol, tf, barShift);
      mc.volume = iVolume(symbol, tf, barShift);

      mc.tag = tag;
      mc.markerType = MARKER_CIRCLE;
      mc.notes = notes;

      switch(tag)
      {
         case TAG_BERSERKER: mc.markerColor = clrRed; break;
         default: mc.markerColor = clrYellow;
      }

      if(m_markedCount >= ArraySize(m_markedCandles))
         ArrayResize(m_markedCandles, m_markedCount + 100);

      m_markedCandles[m_markedCount] = mc;
      m_markedCount++;

      DrawMarker(mc);
      WriteMarkedCandle(mc);
   }

   //+------------------------------------------------------------------+
   //| Draw marker on chart                                              |
   //+------------------------------------------------------------------+
   bool DrawMarker(MarkedCandle &mc)
   {
      // Validate timestamp and price
      if(mc.timestamp <= 0)
      {
         Print("WARNING: CVTLogger::DrawMarker - invalid timestamp");
         return false;
      }
      if(mc.high <= 0 || !MathIsValidNumber(mc.high))
      {
         Print("WARNING: CVTLogger::DrawMarker - invalid high price");
         return false;
      }

      string name = m_markerPrefix + IntegerToString(m_markedCount);

      int code = 159;  // Circle by default
      switch(mc.markerType)
      {
         case MARKER_CIRCLE:     code = 159; break;
         case MARKER_ARROW_UP:   code = 233; break;
         case MARKER_ARROW_DOWN: code = 234; break;
         case MARKER_STAR:       code = 171; break;
         case MARKER_CROSS:      code = 251; break;
         case MARKER_DIAMOND:    code = 168; break;
         default:                code = 159; break;
      }

      // Create arrow object with error checking
      if(!ObjectCreate(0, name, OBJ_ARROW, 0, mc.timestamp, mc.high))
      {
         int err = GetLastError();
         // Error 4200 = object already exists, try with unique name
         if(err == 4200)
         {
            name = m_markerPrefix + IntegerToString(m_markedCount) + "_" +
                   IntegerToString(GetTickCount());
            if(!ObjectCreate(0, name, OBJ_ARROW, 0, mc.timestamp, mc.high))
            {
               Print("WARNING: CVTLogger::DrawMarker - cannot create marker object (error: ", GetLastError(), ")");
               return false;
            }
         }
         else if(err != 0)
         {
            Print("WARNING: CVTLogger::DrawMarker - ObjectCreate failed (error: ", err, ")");
            return false;
         }
      }

      ObjectSetInteger(0, name, OBJPROP_ARROWCODE, code);
      ObjectSetInteger(0, name, OBJPROP_COLOR, mc.markerColor);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 2);
      ObjectSetString(0, name, OBJPROP_TOOLTIP,
         StringFormat("%s: %s", EnumToString(mc.tag), mc.notes));

      return true;
   }

   //+------------------------------------------------------------------+
   //| Write marked candle to file                                       |
   //+------------------------------------------------------------------+
   bool WriteMarkedCandle(MarkedCandle &mc)
   {
      if(m_hMarked == INVALID_HANDLE)
      {
         string dateStr = TimeToString(TimeCurrent(), TIME_DATE);
         StringReplace(dateStr, ".", "");
         string markFile = m_logPath + "\\" + m_logPrefix + "_marked_" + dateStr + ".jsonl";
         m_hMarked = FileOpen(markFile, FILE_WRITE|FILE_TXT|FILE_SHARE_READ);

         if(m_hMarked == INVALID_HANDLE)
         {
            int err = GetLastError();
            Print("WARNING: CVTLogger::WriteMarkedCandle - cannot open marked file: ", markFile, " (error: ", err, ")");
            return false;
         }
      }

      if(m_hMarked != INVALID_HANDLE)
      {
         string json = mc.ToJSON();
         if(StringLen(json) > 0)
         {
            uint written = FileWriteString(m_hMarked, json + "\n");
            if(written == 0)
            {
               Print("WARNING: CVTLogger::WriteMarkedCandle - failed to write to file");
               return false;
            }
            FileFlush(m_hMarked);
            return true;
         }
      }

      return false;
   }

   //+------------------------------------------------------------------+
   //| Get marked candles by tag (for replay)                            |
   //+------------------------------------------------------------------+
   int GetMarkedByTag(ENUM_TRADE_TAG tag, MarkedCandle &result[])
   {
      ArrayResize(result, 0);
      int count = 0;

      for(int i = 0; i < m_markedCount; i++)
      {
         if(m_markedCandles[i].tag == tag)
         {
            ArrayResize(result, count + 1);
            result[count] = m_markedCandles[i];
            count++;
         }
      }

      return count;
   }

   //+------------------------------------------------------------------+
   //| Get all Berserker marked candles                                  |
   //+------------------------------------------------------------------+
   int GetBerserkerMarks(MarkedCandle &result[])
   {
      return GetMarkedByTag(TAG_BERSERKER, result);
   }

   //+------------------------------------------------------------------+
   //| Export marked candles for RL training                             |
   //+------------------------------------------------------------------+
   bool ExportMarkedForRL(string filename, ENUM_TRADE_TAG filterTag = TAG_NONE)
   {
      string path = m_logPath + "\\" + filename;
      int h = FileOpen(path, FILE_WRITE|FILE_TXT);

      if(h == INVALID_HANDLE)
         return false;

      int exported = 0;
      for(int i = 0; i < m_markedCount; i++)
      {
         if(filterTag != TAG_NONE && m_markedCandles[i].tag != filterTag)
            continue;

         FileWriteString(h, m_markedCandles[i].ToJSON() + "\n");
         exported++;
      }

      FileClose(h);

      Log(LOG_INFO, StringFormat("Exported %d marked candles to %s", exported, filename));

      return true;
   }

   //+------------------------------------------------------------------+
   //| Clear markers from chart                                          |
   //+------------------------------------------------------------------+
   void ClearMarkers()
   {
      ObjectsDeleteAll(0, m_markerPrefix);
      Log(LOG_DEBUG, "Chart markers cleared");
   }

   //+------------------------------------------------------------------+
   //| Get marked count                                                  |
   //+------------------------------------------------------------------+
   int GetMarkedCount() { return m_markedCount; }

   //+------------------------------------------------------------------+
   //| Get marked count by tag                                           |
   //+------------------------------------------------------------------+
   int GetMarkedCountByTag(ENUM_TRADE_TAG tag)
   {
      int count = 0;
      for(int i = 0; i < m_markedCount; i++)
      {
         if(m_markedCandles[i].tag == tag)
            count++;
      }
      return count;
   }
};

//+------------------------------------------------------------------+
//| GLOBAL INSTANCE                                                   |
//+------------------------------------------------------------------+
CVTLogger g_logger;

//+------------------------------------------------------------------+
//| Helper functions for quick logging                                |
//+------------------------------------------------------------------+
void LogDebug(string msg)    { g_logger.Debug(msg); }
void LogInfo(string msg)     { g_logger.Info(msg); }
void LogWarn(string msg)     { g_logger.Warn(msg); }
void LogError(string msg)    { g_logger.Error(msg); }

#endif // VT_LOGGER_MQH
