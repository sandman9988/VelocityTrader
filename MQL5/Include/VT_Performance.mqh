//+------------------------------------------------------------------+
//|                                               VT_Performance.mqh |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|             Performance Optimization: Ring Buffers, Caches, Async |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"

#ifndef VT_PERFORMANCE_MQH
#define VT_PERFORMANCE_MQH

#include "VT_Definitions.mqh"

//+------------------------------------------------------------------+
//| CONSTANTS                                                         |
//+------------------------------------------------------------------+
#define RINGBUF_SIZE_SMALL    32     // For price/velocity history
#define RINGBUF_SIZE_MEDIUM   64     // For ATR/stats history
#define RINGBUF_SIZE_LARGE    128    // For comprehensive history
#define CACHE_TTL_SHORT       5      // 5 seconds for hot cache
#define CACHE_TTL_MEDIUM      30     // 30 seconds for warm cache
#define CACHE_TTL_LONG        300    // 5 minutes for cold cache
#define UPDATE_QUEUE_SIZE     64     // Max pending symbol updates (expanded for bursty feeds)
#define TIMER_INTERVAL_MS     250    // OnTimer interval (milliseconds)

//+------------------------------------------------------------------+
//| Update Priority Levels                                            |
//+------------------------------------------------------------------+
enum ENUM_UPDATE_PRIORITY
{
   PRIORITY_CRITICAL = 0,   // Positions, current symbol - every tick
   PRIORITY_HIGH = 1,       // Top-ranked symbols - every 2 ticks
   PRIORITY_MEDIUM = 2,     // Active symbols - every 5 ticks
   PRIORITY_LOW = 3,        // Background symbols - every 10 ticks
   PRIORITY_IDLE = 4        // Inactive symbols - OnTimer only
};

//+------------------------------------------------------------------+
//| TEMPLATE: Ring Buffer for Efficient Circular Storage              |
//| O(1) insertion, O(1) access, fixed memory, no allocations         |
//+------------------------------------------------------------------+
template<typename T>
struct RingBuffer
{
   T           data[];
   int         head;        // Next write position
   int         count;       // Current items in buffer
   int         capacity;    // Maximum capacity

   void Init(int size)
   {
      capacity = size;
      if(ArrayResize(data, capacity) != capacity)
      {
         Print("ERROR: ArrayResize failed for ring buffer - capacity set to 0");
         capacity = 0;
         return;
      }
      head = 0;
      count = 0;
   }

   void Push(T value)
   {
      data[head] = value;
      head = (head + 1) % capacity;
      if(count < capacity) count++;
   }

   // Get item at position (0 = most recent, count-1 = oldest)
   T Get(int idx)
   {
      if(idx < 0 || idx >= count) return data[0];  // Safe default
      int actualIdx = (head - 1 - idx + capacity) % capacity;
      return data[actualIdx];
   }

   // Get oldest item
   T GetOldest()
   {
      if(count == 0) return data[0];
      return Get(count - 1);
   }

   // Get newest item
   T GetNewest()
   {
      if(count == 0) return data[0];
      return Get(0);
   }

   // Calculate average (for numeric types)
   double GetAverage()
   {
      if(count == 0) return 0;
      double sum = 0;
      for(int i = 0; i < count; i++)
         sum += (double)Get(i);
      return SafeDivide(sum, (double)count, 0.0);
   }

   // Calculate standard deviation
   double GetStdDev()
   {
      if(count < 2) return 0;
      double avg = GetAverage();
      double sumSq = 0;
      for(int i = 0; i < count; i++)
      {
         double diff = (double)Get(i) - avg;
         sumSq += diff * diff;
      }
      return MathSqrt(SafeDivide(sumSq, (double)(count - 1), 0.0));
   }

   // Get min value
   double GetMin()
   {
      if(count == 0) return 0;
      double minVal = (double)Get(0);
      for(int i = 1; i < count; i++)
         minVal = MathMin(minVal, (double)Get(i));
      return minVal;
   }

   // Get max value
   double GetMax()
   {
      if(count == 0) return 0;
      double maxVal = (double)Get(0);
      for(int i = 1; i < count; i++)
         maxVal = MathMax(maxVal, (double)Get(i));
      return maxVal;
   }

   int Count() { return count; }
   bool IsFull() { return count >= capacity; }
   void Clear() { head = 0; count = 0; }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Cached Value with TTL                                  |
//+------------------------------------------------------------------+
template<typename T>
struct CachedValue
{
   T           value;
   datetime    lastUpdate;
   int         ttlSeconds;
   bool        valid;

   void Init(int ttl = CACHE_TTL_MEDIUM)
   {
      ttlSeconds = ttl;
      lastUpdate = 0;
      valid = false;
   }

   bool IsValid()
   {
      if(!valid) return false;
      return (TimeCurrent() - lastUpdate) < ttlSeconds;
   }

   void Set(T newValue)
   {
      value = newValue;
      lastUpdate = TimeCurrent();
      valid = true;
   }

   T Get()
   {
      return value;
   }

   void Invalidate()
   {
      valid = false;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Symbol Performance Data with Ring Buffers              |
//+------------------------------------------------------------------+
struct SymbolPerfData
{
   // Price history ring buffers
   RingBuffer<double> priceHistory;     // Recent bid prices
   RingBuffer<double> velocityHistory;  // Recent velocity values
   RingBuffer<double> accelHistory;     // Recent acceleration values
   RingBuffer<double> atrHistory;       // Recent ATR values

   // Cached computed values
   CachedValue<double> cachedAvgATR;
   CachedValue<double> cachedVolatility;
   CachedValue<double> cachedMomentum;
   CachedValue<int>    cachedRegime;

   // Update scheduling
   ENUM_UPDATE_PRIORITY priority;
   datetime             lastUpdate;
   int                  updateCounter;
   bool                 needsUpdate;

   void Init()
   {
      priceHistory.Init(RINGBUF_SIZE_SMALL);
      velocityHistory.Init(RINGBUF_SIZE_SMALL);
      accelHistory.Init(RINGBUF_SIZE_SMALL);
      atrHistory.Init(RINGBUF_SIZE_MEDIUM);

      cachedAvgATR.Init(CACHE_TTL_MEDIUM);
      cachedVolatility.Init(CACHE_TTL_SHORT);
      cachedMomentum.Init(CACHE_TTL_SHORT);
      cachedRegime.Init(CACHE_TTL_SHORT);

      priority = PRIORITY_LOW;
      lastUpdate = 0;
      updateCounter = 0;
      needsUpdate = true;
   }

   void RecordPrice(double price)
   {
      priceHistory.Push(price);
      updateCounter++;
   }

   void RecordVelocity(double vel, double accel)
   {
      velocityHistory.Push(vel);
      accelHistory.Push(accel);
   }

   void RecordATR(double atr)
   {
      atrHistory.Push(atr);
      cachedAvgATR.Invalidate();  // Invalidate cache when new data arrives
   }

   double GetAvgATR()
   {
      if(cachedAvgATR.IsValid())
         return cachedAvgATR.Get();

      double avg = atrHistory.GetAverage();
      cachedAvgATR.Set(avg);
      return avg;
   }

   double GetVolatility()
   {
      if(cachedVolatility.IsValid())
         return cachedVolatility.Get();

      double vol = priceHistory.GetStdDev();
      cachedVolatility.Set(vol);
      return vol;
   }

   double GetMomentum()
   {
      if(cachedMomentum.IsValid())
         return cachedMomentum.Get();

      if(velocityHistory.Count() < 2)
         return 0;

      double recent = velocityHistory.GetNewest();
      double older = velocityHistory.Get(MathMin(10, velocityHistory.Count() - 1));
      double momentum = recent - older;
      cachedMomentum.Set(momentum);
      return momentum;
   }

   bool ShouldUpdate(int tickCount)
   {
      switch(priority)
      {
         case PRIORITY_CRITICAL: return true;
         case PRIORITY_HIGH:     return (tickCount % 2 == 0);
         case PRIORITY_MEDIUM:   return (tickCount % 5 == 0);
         case PRIORITY_LOW:      return (tickCount % 10 == 0);
         case PRIORITY_IDLE:     return false;  // OnTimer only
      }
      return true;
   }

   void SetPriority(bool hasPosition, bool isTopRanked, bool isCurrentSymbol)
   {
      if(isCurrentSymbol || hasPosition)
         priority = PRIORITY_CRITICAL;
      else if(isTopRanked)
         priority = PRIORITY_HIGH;
      else if(needsUpdate)
         priority = PRIORITY_MEDIUM;
      else
         priority = PRIORITY_LOW;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Async Update Queue                                     |
//| Non-blocking queue for deferring low-priority updates             |
//+------------------------------------------------------------------+
struct UpdateQueueItem
{
   int      symbolIdx;
   int      priority;
   datetime queuedTime;
   bool     active;
};

struct AsyncUpdateQueue
{
   UpdateQueueItem items[UPDATE_QUEUE_SIZE];
   int             head;
   int             tail;
   int             count;
   int             dropped;

   void Init()
   {
      head = 0;
      tail = 0;
      count = 0;
      dropped = 0;
      for(int i = 0; i < UPDATE_QUEUE_SIZE; i++)
         items[i].active = false;
   }

   bool Enqueue(int symbolIdx, int priority)
   {
      if(count >= UPDATE_QUEUE_SIZE)
      {
         dropped++;
         return false;  // Queue full
      }

      // Check if already in queue
      for(int i = 0; i < UPDATE_QUEUE_SIZE; i++)
      {
         if(items[i].active && items[i].symbolIdx == symbolIdx)
            return true;  // Already queued
      }

      items[tail].symbolIdx = symbolIdx;
      items[tail].priority = priority;
      items[tail].queuedTime = TimeCurrent();
      items[tail].active = true;

      tail = (tail + 1) % UPDATE_QUEUE_SIZE;
      count++;
      return true;
   }

   bool Dequeue(int &symbolIdx)
   {
      if(count == 0)
         return false;

      // Find highest priority (lowest number) item
      int bestIdx = -1;
      int bestPriority = 999;

      for(int i = 0; i < UPDATE_QUEUE_SIZE; i++)
      {
         if(items[i].active && items[i].priority < bestPriority)
         {
            bestPriority = items[i].priority;
            bestIdx = i;
         }
      }

      if(bestIdx < 0)
         return false;

      symbolIdx = items[bestIdx].symbolIdx;
      items[bestIdx].active = false;
      count--;
      return true;
   }

   int Count() { return count; }
   int Dropped() { return dropped; }
   bool IsEmpty() { return count == 0; }
   bool IsFull() { return count >= UPDATE_QUEUE_SIZE; }

   void Clear()
   {
      for(int i = 0; i < UPDATE_QUEUE_SIZE; i++)
         items[i].active = false;
      count = 0;
      dropped = 0;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: HUD Render Cache                                       |
//| Pre-compute HUD strings to avoid string operations in OnTick      |
//+------------------------------------------------------------------+
struct HUDRenderCache
{
   // Pre-rendered strings for each HUD section
   string  agentStatsSniper;
   string  agentStatsBerserker;
   string  circuitBreakerStatus;
   string  regimeDistribution;
   string  symbolRankings[10];

   // Cache validity
   datetime lastUpdate;
   int      ttlSeconds;
   bool     needsRefresh;

   void Init()
   {
      lastUpdate = 0;
      ttlSeconds = 1;  // Refresh every second
      needsRefresh = true;
   }

   bool NeedsRefresh()
   {
      if(needsRefresh) return true;
      return (TimeCurrent() - lastUpdate) >= ttlSeconds;
   }

   void MarkRefreshed()
   {
      lastUpdate = TimeCurrent();
      needsRefresh = false;
   }

   void Invalidate()
   {
      needsRefresh = true;
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Trade Result Ring Buffer                               |
//| For rolling statistics without array operations                   |
//+------------------------------------------------------------------+
struct TradeResultBuffer
{
   RingBuffer<double> pnlHistory;
   RingBuffer<int>    winHistory;     // 1 = win, 0 = loss

   // Cached rolling stats
   CachedValue<double> rollingWinRate;
   CachedValue<double> rollingPF;
   CachedValue<double> avgPnL;

   int totalTrades;
   int totalWins;
   double totalPnL;
   double totalUpside;
   double totalDownside;

   void Init(int bufferSize = RINGBUF_SIZE_MEDIUM)
   {
      pnlHistory.Init(bufferSize);
      winHistory.Init(bufferSize);

      rollingWinRate.Init(CACHE_TTL_SHORT);
      rollingPF.Init(CACHE_TTL_SHORT);
      avgPnL.Init(CACHE_TTL_SHORT);

      totalTrades = 0;
      totalWins = 0;
      totalPnL = 0;
      totalUpside = 0;
      totalDownside = 0;
   }

   void RecordTrade(double pnl)
   {
      pnlHistory.Push(pnl);
      winHistory.Push(pnl > 0 ? 1 : 0);

      totalTrades++;
      totalPnL += pnl;
      if(pnl > 0)
      {
         totalWins++;
         totalUpside += pnl;
      }
      else
      {
         totalDownside += MathAbs(pnl);
      }

      // Invalidate caches
      rollingWinRate.Invalidate();
      rollingPF.Invalidate();
      avgPnL.Invalidate();
   }

   double GetRollingWinRate()
   {
      if(rollingWinRate.IsValid())
         return rollingWinRate.Get();

      int count = winHistory.Count();
      if(count == 0) return 0.5;

      int wins = 0;
      for(int i = 0; i < count; i++)
         wins += winHistory.Get(i);

      double wr = SafeDivide((double)wins, (double)count, 0.5);
      rollingWinRate.Set(wr);
      return wr;
   }

   double GetRollingPF()
   {
      if(rollingPF.IsValid())
         return rollingPF.Get();

      int count = pnlHistory.Count();
      if(count == 0) return 1.0;

      double up = 0, down = 0;
      for(int i = 0; i < count; i++)
      {
         double pnl = pnlHistory.Get(i);
         if(pnl > 0) up += pnl;
         else down += MathAbs(pnl);
      }

      double pf = SafeDivide(up, down, 1.0);
      rollingPF.Set(pf);
      return pf;
   }

   double GetAvgPnL()
   {
      if(avgPnL.IsValid())
         return avgPnL.Get();

      double avg = pnlHistory.GetAverage();
      avgPnL.Set(avg);
      return avg;
   }

   double GetCumulativeWR()
   {
      return SafeDivide((double)totalWins, (double)totalTrades, 0.0);
   }

   double GetCumulativePF()
   {
      return SafeDivide(totalUpside, totalDownside, 0.0);
   }
};

//+------------------------------------------------------------------+
//| STRUCTURE: Performance Manager                                    |
//| Central coordinator for all performance optimizations             |
//+------------------------------------------------------------------+
struct PerformanceManager
{
   // Symbol-level performance data
   SymbolPerfData      symbolData[MAX_SYMBOLS];

   // Async update queue
   AsyncUpdateQueue    updateQueue;

   // HUD rendering cache
   HUDRenderCache      hudCache;

   // Trade result tracking
   TradeResultBuffer   sniperResults;
   TradeResultBuffer   berserkerResults;

   // Tick counting for update scheduling
   int                 tickCounter;
   datetime            lastTimerRun;

   // Performance metrics
   int                 ticksProcessed;
   int                 symbolsUpdated;
   int                 cacheHits;
   int                 cacheMisses;

   void Init()
   {
      for(int i = 0; i < MAX_SYMBOLS; i++)
         symbolData[i].Init();

      updateQueue.Init();
      hudCache.Init();
      sniperResults.Init();
      berserkerResults.Init();

      tickCounter = 0;
      lastTimerRun = 0;
      ticksProcessed = 0;
      symbolsUpdated = 0;
      cacheHits = 0;
      cacheMisses = 0;
   }

   void OnTickStart()
   {
      tickCounter++;
      ticksProcessed++;
   }

   void OnSymbolUpdated()
   {
      symbolsUpdated++;
   }

   void OnCacheHit()
   {
      cacheHits++;
   }

   void OnCacheMiss()
   {
      cacheMisses++;
   }

   double GetCacheHitRate()
   {
      int total = cacheHits + cacheMisses;
      if(total == 0) return 0;
      return SafeDivide((double)cacheHits, (double)total, 0.0) * 100;
   }

   // Process queued updates (call from OnTimer)
   int ProcessQueue(int maxUpdates = 3)
   {
      int processed = 0;
      int symbolIdx;

      while(processed < maxUpdates && updateQueue.Dequeue(symbolIdx))
      {
         // Caller should update the symbol
         processed++;
      }

      return processed;
   }

   // Update symbol priorities based on current state
   void UpdatePriorities(const int &positionSymbols[], int posCount,
                         const int &topRankedSymbols[], int topCount,
                         int currentSymbolIdx)
   {
      for(int i = 0; i < MAX_SYMBOLS; i++)
      {
         bool hasPos = false;
         bool isTop = false;

         for(int j = 0; j < posCount && !hasPos; j++)
            if(positionSymbols[j] == i) hasPos = true;

         for(int j = 0; j < topCount && !isTop; j++)
            if(topRankedSymbols[j] == i) isTop = true;

         symbolData[i].SetPriority(hasPos, isTop, i == currentSymbolIdx);
      }
   }

   // Get tick interval for priority level
   int GetUpdateInterval(ENUM_UPDATE_PRIORITY priority)
   {
      switch(priority)
      {
         case PRIORITY_CRITICAL: return 1;
         case PRIORITY_HIGH:     return 2;
         case PRIORITY_MEDIUM:   return 5;
         case PRIORITY_LOW:      return 10;
         case PRIORITY_IDLE:     return 0;  // Timer only
      }
      return 10;
   }
};

//+------------------------------------------------------------------+
//| GLOBAL: Performance Manager Instance                              |
//+------------------------------------------------------------------+
PerformanceManager g_perfManager;

//+------------------------------------------------------------------+
//| Helper: Initialize performance system                             |
//+------------------------------------------------------------------+
void InitPerformance()
{
   g_perfManager.Init();
   Print("Performance manager initialized");
   Print("  Ring buffer sizes: Small=", RINGBUF_SIZE_SMALL,
         " Medium=", RINGBUF_SIZE_MEDIUM, " Large=", RINGBUF_SIZE_LARGE);
   Print("  Cache TTLs: Short=", CACHE_TTL_SHORT, "s Medium=",
         CACHE_TTL_MEDIUM, "s Long=", CACHE_TTL_LONG, "s");
}

//+------------------------------------------------------------------+
//| Helper: Get performance stats string                              |
//+------------------------------------------------------------------+
string GetPerfStatsString()
{
   return StringFormat("Ticks:%d Updated:%d Queue:%d Dropped:%d CacheHit:%.1f%%",
                       g_perfManager.ticksProcessed,
                       g_perfManager.symbolsUpdated,
                       g_perfManager.updateQueue.Count(),
                       g_perfManager.updateQueue.Dropped(),
                       g_perfManager.GetCacheHitRate());
}

#endif // VT_PERFORMANCE_MQH
