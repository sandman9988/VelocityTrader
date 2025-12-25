//+------------------------------------------------------------------+
//|                                              VT_Persistence.mqh  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|                Atomic State Persistence with Checksum Validation  |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"

#ifndef VT_PERSISTENCE_MQH
#define VT_PERSISTENCE_MQH

#include "VT_Definitions.mqh"
#include "VT_Globals.mqh"

// Note: Input parameters (InpUsePersistence, etc.) are defined
// in the main EA file and are automatically globally accessible.
// DO NOT redeclare them with 'extern' as this causes type conflicts.

// Persistence version defined in VT_Definitions.mqh (PERSISTENCE_VERSION = 720)

//+------------------------------------------------------------------+
//| Calculate CRC32-based checksum for data validation                |
//| Uses polynomial 0xEDB88320 for robust error detection             |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| DEFENSE IN DEPTH: Safe file write wrappers with error tracking   |
//| These wrappers ensure every write operation is validated          |
//+------------------------------------------------------------------+
struct FileWriteContext
{
   int handle;
   int errors;
   long bytesWritten;

   void Init(int h) { handle = h; errors = 0; bytesWritten = 0; }
   bool HasErrors() { return errors > 0; }
   void Reset() { errors = 0; bytesWritten = 0; }
};

bool SafeFileWriteInteger(FileWriteContext &ctx, int value)
{
   if(ctx.handle == INVALID_HANDLE) { ctx.errors++; return false; }
   // Use INT_VALUE explicitly for deterministic 4-byte format
   uint written = FileWriteInteger(ctx.handle, value, INT_VALUE);
   if(written != 4) { ctx.errors++; return false; }
   ctx.bytesWritten += written;
   return true;
}

bool SafeFileWriteLong(FileWriteContext &ctx, long value)
{
   if(ctx.handle == INVALID_HANDLE) { ctx.errors++; return false; }
   uint written = FileWriteLong(ctx.handle, value);
   if(written != sizeof(long)) { ctx.errors++; return false; }
   ctx.bytesWritten += written;
   return true;
}

bool SafeFileWriteDouble(FileWriteContext &ctx, double value)
{
   if(ctx.handle == INVALID_HANDLE) { ctx.errors++; return false; }
   uint written = FileWriteDouble(ctx.handle, value);
   if(written != sizeof(double)) { ctx.errors++; return false; }
   ctx.bytesWritten += written;
   return true;
}

//+------------------------------------------------------------------+
//| Calculate CRC32-based checksum for data validation                |
//| Uses polynomial 0xEDB88320 for robust error detection             |
//+------------------------------------------------------------------+
uint CalculateChecksum(const uchar &data[], int size)
{
   // CRC32 lookup table
   static uint crcTable[256];
   static bool tableInit = false;

   if(!tableInit)
   {
      for(uint i = 0; i < 256; i++)
      {
         uint crc = i;
         for(int j = 0; j < 8; j++)
         {
            if(crc & 1)
               crc = (crc >> 1) ^ 0xEDB88320;
            else
               crc >>= 1;
         }
         crcTable[i] = crc;
      }
      tableInit = true;
   }

   // Calculate CRC32
   uint crc = 0xFFFFFFFF;
   for(int i = 0; i < size; i++)
   {
      crc = crcTable[(crc ^ data[i]) & 0xFF] ^ (crc >> 8);
   }
   return crc ^ 0xFFFFFFFF;
}

//+------------------------------------------------------------------+
//| Calculate file checksum by reading entire file                    |
//| Returns 0 on error (file not found, read error, etc.)             |
//+------------------------------------------------------------------+
uint CalculateFileChecksum(string filename, int excludeLastBytes = 4)
{
   // Validate input parameters
   if(StringLen(filename) == 0)
   {
      Print("ERROR: CalculateFileChecksum - empty filename provided");
      return 0;
   }

   if(excludeLastBytes < 0)
   {
      Print("ERROR: CalculateFileChecksum - invalid excludeLastBytes: ", excludeLastBytes);
      return 0;
   }

   int handle = FileOpen(filename, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE)
   {
      int err = GetLastError();
      if(err != ERR_FILE_NOT_EXIST)  // Don't log for missing files (expected case)
         Print("WARNING: CalculateFileChecksum - cannot open file: ", filename, " (error: ", err, ")");
      return 0;
   }

   long fileSize = FileSize(handle);
   if(fileSize <= 0)
   {
      Print("WARNING: CalculateFileChecksum - file is empty or invalid size: ", filename);
      FileClose(handle);
      return 0;
   }

   int dataSize = (int)(fileSize - excludeLastBytes);  // Exclude checksum bytes

   if(dataSize <= 0)
   {
      Print("WARNING: CalculateFileChecksum - file too small for checksum: ", filename,
            " (size: ", fileSize, ", exclude: ", excludeLastBytes, ")");
      FileClose(handle);
      return 0;
   }

   // Sanity check: prevent allocating excessive memory
   if(dataSize > 100 * 1024 * 1024)  // 100MB limit
   {
      Print("ERROR: CalculateFileChecksum - file too large: ", filename, " (", dataSize, " bytes)");
      FileClose(handle);
      return 0;
   }

   uchar data[];
   if(ArrayResize(data, dataSize) != dataSize)
   {
      Print("ERROR: CalculateFileChecksum - memory allocation failed for ", dataSize, " bytes");
      FileClose(handle);
      return 0;
   }

   uint bytesRead = FileReadArray(handle, data, 0, dataSize);
   FileClose(handle);

   if(bytesRead != (uint)dataSize)
   {
      Print("WARNING: CalculateFileChecksum - incomplete read: ", bytesRead, "/", dataSize, " bytes from ", filename);
      return 0;
   }

   return CalculateChecksum(data, dataSize);
}

//+------------------------------------------------------------------+
//| Forward declarations                                              |
//+------------------------------------------------------------------+
void SaveAgentSafe(FileWriteContext &ctx, TradingAgent &agent);
void SaveProfileSafe(FileWriteContext &ctx, AgentProfile &profile);
void SaveAgent(int handle, TradingAgent &agent);
void SaveProfile(int handle, AgentProfile &profile);
void LoadAgent(int handle, TradingAgent &agent);
void LoadProfile(int handle, AgentProfile &profile);
bool TryLoadFile(string filename);
bool LoadStateV710(string filename);
void LoadAgentV710(int handle, TradingAgent &agent);
void LoadProfileV710(int handle, AgentProfile &profile);

//+------------------------------------------------------------------+
//| SaveState: Atomic save with temp file and backup                  |
//+------------------------------------------------------------------+
void SaveState()
{
   if(!InpUsePersistence) return;

   string baseFilename = InpFilePrefix + IntegerToString(InpMagicNumber);
   string tempFilename = baseFilename + "_temp.bin";
   string mainFilename = baseFilename + ".bin";
   string backupFilename = baseFilename + "_backup.bin";

   // Step 1: Write to temporary file with error tracking
   int handle = FileOpen(tempFilename, FILE_WRITE | FILE_BIN);
   if(handle == INVALID_HANDLE)
   {
      Print("ERROR: Cannot create temp file for save");
      return;
   }

   // DEFENSE IN DEPTH: Use safe write context to track all write errors
   FileWriteContext ctx;
   ctx.Init(handle);

   // Write header with error tracking
   SafeFileWriteInteger(ctx, PERSISTENCE_MAGIC);
   SafeFileWriteInteger(ctx, PERSISTENCE_VERSION);
   SafeFileWriteLong(ctx, TimeCurrent());  // Save timestamp

   // Save agents with context
   SaveAgentSafe(ctx, g_sniper);
   SaveAgentSafe(ctx, g_berserker);

   // Save predictor with error tracking
   for(int i = 0; i < 3; i++) SafeFileWriteDouble(ctx, g_predictor.regimeWR[i]);
   for(int i = 0; i < 5; i++) SafeFileWriteDouble(ctx, g_predictor.chiZoneWR[i]);
   for(int i = 0; i < 5; i++) SafeFileWriteDouble(ctx, g_predictor.accelZoneWR[i]);
   for(int i = 0; i < 3; i++) SafeFileWriteInteger(ctx, g_predictor.regimeCounts[i]);
   for(int i = 0; i < 5; i++) SafeFileWriteInteger(ctx, g_predictor.chiCounts[i]);
   for(int i = 0; i < 5; i++) SafeFileWriteInteger(ctx, g_predictor.accelCounts[i]);

   // Save circuit breaker state
   SafeFileWriteInteger(ctx, (int)g_breaker.state);
   SafeFileWriteDouble(ctx, g_breaker.peakEquity);

   // Write checksum placeholder (will be updated after calculation)
   SafeFileWriteInteger(ctx, 0);  // Placeholder for checksum

   // DEFENSE IN DEPTH: Abort if any write errors occurred
   if(ctx.HasErrors())
   {
      Print("ERROR: File write errors detected (", ctx.errors, " errors). Aborting save.");
      FileClose(handle);
      FileDelete(tempFilename);
      return;
   }

   FileFlush(handle);
   FileClose(handle);

   // Step 2: Calculate checksum of file content (excluding checksum bytes)
   uint checksum = CalculateFileChecksum(tempFilename, 4);

   // Write the actual checksum at the end
   handle = FileOpen(tempFilename, FILE_READ | FILE_WRITE | FILE_BIN);
   if(handle == INVALID_HANDLE)
   {
      Print("ERROR: Cannot update checksum in temp file");
      FileDelete(tempFilename);
      return;
   }

   // Seek to checksum position (end - 4 bytes)
   FileSeek(handle, -4, SEEK_END);
   FileWriteInteger(handle, (int)checksum, INT_VALUE);
   FileFlush(handle);
   FileClose(handle);

   // Step 3: Validate temp file with checksum verification
   handle = FileOpen(tempFilename, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE)
   {
      Print("ERROR: Cannot verify temp file");
      FileDelete(tempFilename);
      return;
   }

   // Quick validation - check magic and version (use INT_VALUE for deterministic 4-byte format)
   int magic = FileReadInteger(handle, INT_VALUE);
   int version = FileReadInteger(handle, INT_VALUE);

   // Seek to end and read stored checksum
   FileSeek(handle, -4, SEEK_END);
   uint storedChecksum = (uint)FileReadInteger(handle, INT_VALUE);
   FileClose(handle);

   // Recalculate and verify checksum
   uint verifyChecksum = CalculateFileChecksum(tempFilename, 4);

   if(magic != PERSISTENCE_MAGIC || version != PERSISTENCE_VERSION || storedChecksum != verifyChecksum)
   {
      Print("ERROR: Temp file validation failed - magic:", magic,
            " version:", version,
            " checksum match:", (storedChecksum == verifyChecksum));
      FileDelete(tempFilename);
      return;
   }

   // Step 3: Atomic-like swap using FileCopy + FileDelete (cross-build compatible)
   // Note: FileMove with FILE_REWRITE may not compile on all MT5 builds
   if(FileIsExist(mainFilename))
   {
      // Delete old backup if exists
      if(FileIsExist(backupFilename))
         FileDelete(backupFilename);

      // Copy current to backup (more reliable than FileMove)
      if(!FileCopy(mainFilename, 0, backupFilename, FILE_REWRITE))
      {
         Print("WARNING: Could not create backup");
      }
      // Delete the original main file
      FileDelete(mainFilename);
   }

   // Copy temp to main
   if(!FileCopy(tempFilename, 0, mainFilename, FILE_REWRITE))
   {
      Print("ERROR: Could not finalize save");
      return;
   }

   // Clean up temp file
   FileDelete(tempFilename);
}

//+------------------------------------------------------------------+
//| SaveAgentSafe: Save trading agent state with error tracking       |
//+------------------------------------------------------------------+
void SaveAgentSafe(FileWriteContext &ctx, TradingAgent &agent)
{
   // Save real profile
   SaveProfileSafe(ctx, agent.real);

   // Save shadow profile
   SaveProfileSafe(ctx, agent.shadow);

   // Save meta
   SafeFileWriteDouble(ctx, agent.capitalAlloc);
   SafeFileWriteInteger(ctx, agent.swapCount);
   SafeFileWriteInteger(ctx, agent.consLosses);

   // v720+: Persist rolling window for circuit breaker (prevents post-restart safety bypass)
   SafeFileWriteInteger(ctx, agent.rollingIdx);
   for(int i = 0; i < ROLLING_WINDOW; i++)
   {
      SafeFileWriteDouble(ctx, agent.rollingPnL[i]);
   }
}

//+------------------------------------------------------------------+
//| SaveProfileSafe: Save agent profile with error tracking           |
//+------------------------------------------------------------------+
void SaveProfileSafe(FileWriteContext &ctx, AgentProfile &profile)
{
   for(int i = 0; i < 3; i++)
   {
      SafeFileWriteDouble(ctx, profile.regime[i].qBuy);
      SafeFileWriteDouble(ctx, profile.regime[i].qSell);
      SafeFileWriteDouble(ctx, profile.regime[i].qHold);
      SafeFileWriteInteger(ctx, profile.regime[i].trades);
      SafeFileWriteInteger(ctx, profile.regime[i].wins);
      SafeFileWriteDouble(ctx, profile.regime[i].pnl);
      SafeFileWriteDouble(ctx, profile.regime[i].upside);
      SafeFileWriteDouble(ctx, profile.regime[i].downside);
      SafeFileWriteDouble(ctx, profile.regime[i].learningRate);  // v720: Save learning rate
   }
}

//+------------------------------------------------------------------+
//| SaveAgent: Legacy wrapper (for compatibility)                     |
//+------------------------------------------------------------------+
void SaveAgent(int handle, TradingAgent &agent)
{
   FileWriteContext ctx;
   ctx.Init(handle);
   SaveAgentSafe(ctx, agent);
}

//+------------------------------------------------------------------+
//| SaveProfile: Legacy wrapper (for compatibility)                   |
//+------------------------------------------------------------------+
void SaveProfile(int handle, AgentProfile &profile)
{
   FileWriteContext ctx;
   ctx.Init(handle);
   SaveProfileSafe(ctx, profile);
}

//+------------------------------------------------------------------+
//| LoadState: Load state with fallback to backup                     |
//+------------------------------------------------------------------+
void LoadState()
{
   if(!InpUsePersistence) return;

   string baseFilename = InpFilePrefix + IntegerToString(InpMagicNumber);
   string mainFilename = baseFilename + ".bin";
   string backupFilename = baseFilename + "_backup.bin";

   // Try main file first
   bool loaded = TryLoadFile(mainFilename);

   // If main file failed, try backup
   if(!loaded && FileIsExist(backupFilename))
   {
      Print("Main file corrupted, trying backup...");
      loaded = TryLoadFile(backupFilename);
      if(loaded)
         Print("Loaded from backup successfully");
   }

   if(!loaded)
   {
      Print("No valid state file found, starting fresh");
   }
}

//+------------------------------------------------------------------+
//| TryLoadFile: Attempt to load state from specific file             |
//| Returns true if file loaded successfully, false otherwise          |
//+------------------------------------------------------------------+
bool TryLoadFile(string filename)
{
   // Validate filename
   if(StringLen(filename) == 0)
   {
      Print("ERROR: TryLoadFile - empty filename provided");
      return false;
   }

   int handle = FileOpen(filename, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE)
   {
      int err = GetLastError();
      if(err != ERR_FILE_NOT_EXIST)
         Print("WARNING: TryLoadFile - cannot open file: ", filename, " (error: ", err, ")");
      return false;
   }

   // Validate file has minimum required size (header only)
   long fileSize = FileSize(handle);
   int minHeaderSize = sizeof(int) * 2;  // magic + version
   if(fileSize < minHeaderSize)
   {
      Print("ERROR: TryLoadFile - file too small: ", filename, " (", fileSize, " bytes)");
      FileClose(handle);
      return false;
   }

   // Read and validate header (use INT_VALUE for deterministic 4-byte format)
   int magic = FileReadInteger(handle, INT_VALUE);
   if(magic != PERSISTENCE_MAGIC)
   {
      FileClose(handle);
      Print("ERROR: Invalid magic number in ", filename, " (got ", magic, ", expected ", PERSISTENCE_MAGIC, ")");
      return false;
   }

   int version = FileReadInteger(handle, INT_VALUE);

   // Handle version migration
   if(version == 710)
   {
      FileClose(handle);
      return LoadStateV710(filename);  // Legacy loader
   }
   else if(version != PERSISTENCE_VERSION)
   {
      FileClose(handle);
      Print("ERROR: Unknown version ", version, " in ", filename, " (expected ", PERSISTENCE_VERSION, ")");
      return false;
   }

   // Verify file is large enough for checksum verification
   if(fileSize < 8)  // Need at least header + checksum
   {
      Print("ERROR: TryLoadFile - file too small for checksum: ", filename);
      FileClose(handle);
      return false;
   }

   // Verify CRC32 checksum before loading
   if(!FileSeek(handle, -4, SEEK_END))
   {
      Print("ERROR: TryLoadFile - cannot seek to checksum position in ", filename);
      FileClose(handle);
      return false;
   }
   uint storedChecksum = (uint)FileReadInteger(handle, INT_VALUE);
   FileClose(handle);

   uint calculatedChecksum = CalculateFileChecksum(filename, 4);
   if(calculatedChecksum == 0)
   {
      Print("ERROR: TryLoadFile - checksum calculation failed for ", filename);
      return false;
   }

   if(storedChecksum != calculatedChecksum)
   {
      Print("ERROR: CHECKSUM MISMATCH in ", filename,
            " - stored:", storedChecksum, " calculated:", calculatedChecksum);
      return false;
   }

   // Reopen and continue loading after checksum verified
   handle = FileOpen(filename, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE)
   {
      Print("ERROR: TryLoadFile - cannot reopen verified file: ", filename);
      return false;
   }

   // Skip header (already validated) - use INT_VALUE for deterministic format
   FileReadInteger(handle, INT_VALUE);  // magic
   FileReadInteger(handle, INT_VALUE);  // version

   datetime saveTime = (datetime)FileReadLong(handle);
   if(saveTime <= 0 || saveTime > TimeCurrent() + 86400)  // Sanity check: not in future by more than 1 day
   {
      Print("WARNING: TryLoadFile - suspicious save timestamp: ", TimeToString(saveTime));
   }
   Print("Loading state from ", TimeToString(saveTime));

   // Load agents with bounds checking
   LoadAgent(handle, g_sniper);
   LoadAgent(handle, g_berserker);

   // Load predictor with array bounds validation
   for(int i = 0; i < 3; i++)
   {
      double val = FileReadDouble(handle);
      g_predictor.regimeWR[i] = MathMax(0.0, MathMin(1.0, val));  // Clamp to valid range
   }
   for(int i = 0; i < 5; i++)
   {
      double val = FileReadDouble(handle);
      g_predictor.chiZoneWR[i] = MathMax(0.0, MathMin(1.0, val));
   }
   for(int i = 0; i < 5; i++)
   {
      double val = FileReadDouble(handle);
      g_predictor.accelZoneWR[i] = MathMax(0.0, MathMin(1.0, val));
   }
   for(int i = 0; i < 3; i++)
   {
      int val = FileReadInteger(handle, INT_VALUE);
      g_predictor.regimeCounts[i] = MathMax(0, val);  // Non-negative
   }
   for(int i = 0; i < 5; i++)
   {
      int val = FileReadInteger(handle, INT_VALUE);
      g_predictor.chiCounts[i] = MathMax(0, val);
   }
   for(int i = 0; i < 5; i++)
   {
      int val = FileReadInteger(handle, INT_VALUE);
      g_predictor.accelCounts[i] = MathMax(0, val);
   }

   // Load circuit breaker state with validation
   int stateVal = FileReadInteger(handle, INT_VALUE);
   if(stateVal < 0 || stateVal > 2)  // Validate enum range
   {
      Print("WARNING: TryLoadFile - invalid trading state: ", stateVal, ", defaulting to NORMAL");
      stateVal = 0;
   }
   g_breaker.state = (ENUM_TRADING_STATE)stateVal;

   double peakEquity = FileReadDouble(handle);
   g_breaker.peakEquity = MathMax(0.0, peakEquity);  // Non-negative

   FileClose(handle);
   Print("State loaded successfully (v", PERSISTENCE_VERSION, ")");
   return true;
}

//+------------------------------------------------------------------+
//| LoadStateV710: Legacy loader for v710 format files                |
//+------------------------------------------------------------------+
bool LoadStateV710(string filename)
{
   int handle = FileOpen(filename, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE) return false;

   // Skip header (already validated) - use INT_VALUE for deterministic format
   FileReadInteger(handle, INT_VALUE);  // magic
   FileReadInteger(handle, INT_VALUE);  // version

   // Load agents (old format without learning rate or rolling window)
   LoadAgentV710(handle, g_sniper);
   LoadAgentV710(handle, g_berserker);

   // Load predictor (old format without counts)
   // First initialize to clear any stale data, then overwrite WR arrays
   g_predictor.Init();
   for(int i = 0; i < 3; i++)
   {
      double val = FileReadDouble(handle);
      g_predictor.regimeWR[i] = MathMax(0.0, MathMin(1.0, val));
   }
   for(int i = 0; i < 5; i++)
   {
      double val = FileReadDouble(handle);
      g_predictor.chiZoneWR[i] = MathMax(0.0, MathMin(1.0, val));
   }
   for(int i = 0; i < 5; i++)
   {
      double val = FileReadDouble(handle);
      g_predictor.accelZoneWR[i] = MathMax(0.0, MathMin(1.0, val));
   }
   // Counts remain at 0 from Init() - will accumulate from new trades

   // Initialize circuit breaker to safe default state after v710 migration
   g_breaker.state = STATE_HALTED;  // Conservative: require human approval
   g_breaker.peakEquity = AccountInfoDouble(ACCOUNT_EQUITY);

   FileClose(handle);
   Print("Migrated from v710 format successfully (breaker set to HALTED for safety)");
   return true;
}

//+------------------------------------------------------------------+
//| LoadAgentV710: Legacy agent loader                                |
//+------------------------------------------------------------------+
void LoadAgentV710(int handle, TradingAgent &agent)
{
   LoadProfileV710(handle, agent.real);
   LoadProfileV710(handle, agent.shadow);

   agent.capitalAlloc = FileReadDouble(handle);
   agent.swapCount = FileReadInteger(handle, INT_VALUE);

   // v710 did not have consLosses or rolling window - initialize to safe defaults
   agent.consLosses = 0;
   agent.rollingIdx = 0;
   ArrayInitialize(agent.rollingPnL, 0.0);

   agent.real.RecalcTotals();
   agent.shadow.RecalcTotals();
}

//+------------------------------------------------------------------+
//| LoadProfileV710: Legacy profile loader (no learning rate)         |
//+------------------------------------------------------------------+
void LoadProfileV710(int handle, AgentProfile &profile)
{
   for(int i = 0; i < 3; i++)
   {
      profile.regime[i].qBuy = FileReadDouble(handle);
      profile.regime[i].qSell = FileReadDouble(handle);
      profile.regime[i].qHold = FileReadDouble(handle);
      profile.regime[i].trades = FileReadInteger(handle, INT_VALUE);
      profile.regime[i].wins = FileReadInteger(handle, INT_VALUE);
      profile.regime[i].pnl = FileReadDouble(handle);
      profile.regime[i].upside = FileReadDouble(handle);
      profile.regime[i].downside = FileReadDouble(handle);
      // Learning rate not in v710, use default
      profile.regime[i].learningRate = InpLearningRateInit;
      profile.regime[i].InvalidateCache();
   }
}

//+------------------------------------------------------------------+
//| LoadAgent: Load trading agent state (current version)             |
//+------------------------------------------------------------------+
void LoadAgent(int handle, TradingAgent &agent)
{
   LoadProfile(handle, agent.real);
   LoadProfile(handle, agent.shadow);

   agent.capitalAlloc = FileReadDouble(handle);
   agent.swapCount = FileReadInteger(handle, INT_VALUE);
   agent.consLosses = FileReadInteger(handle, INT_VALUE);

   // v720+: Restore rolling window for circuit breaker
   agent.rollingIdx = FileReadInteger(handle, INT_VALUE);
   // Validate and clamp rollingIdx
   if(agent.rollingIdx < 0 || agent.rollingIdx >= ROLLING_WINDOW)
      agent.rollingIdx = 0;

   for(int i = 0; i < ROLLING_WINDOW; i++)
   {
      double val = FileReadDouble(handle);
      // Clamp invalid numbers to 0
      if(!MathIsValidNumber(val))
         val = 0.0;
      agent.rollingPnL[i] = val;
   }

   agent.real.RecalcTotals();
   agent.shadow.RecalcTotals();
}

//+------------------------------------------------------------------+
//| LoadProfile: Load agent profile (current version)                 |
//| Validates all loaded values are within reasonable ranges          |
//+------------------------------------------------------------------+
void LoadProfile(int handle, AgentProfile &profile)
{
   if(handle == INVALID_HANDLE)
   {
      Print("ERROR: LoadProfile - invalid file handle");
      return;
   }

   int regimeCount = ArraySize(profile.regime);
   int loopCount = MathMin(3, regimeCount);

   for(int i = 0; i < loopCount; i++)
   {
      // Explicit bounds check for safety - skip iteration if out of bounds
      if(i < 0 || i >= ArraySize(profile.regime))
      {
         Print("ERROR: LoadProfile - index out of bounds: ", i, " >= ", ArraySize(profile.regime));
         continue;
      }

      // Load all values from file first (before any array access)
      // Use INT_VALUE for deterministic 4-byte integer format
      double qBuy = FileReadDouble(handle);
      double qSell = FileReadDouble(handle);
      double qHold = FileReadDouble(handle);
      int trades = FileReadInteger(handle, INT_VALUE);
      int wins = FileReadInteger(handle, INT_VALUE);
      double pnl = FileReadDouble(handle);
      double upside = FileReadDouble(handle);
      double downside = FileReadDouble(handle);
      double learningRate = FileReadDouble(handle);

      // Validate all values
      if(!MathIsValidNumber(qBuy)) qBuy = 0.0;
      if(!MathIsValidNumber(qSell)) qSell = 0.0;
      if(!MathIsValidNumber(qHold)) qHold = 0.0;
      trades = MathMax(0, trades);
      wins = MathMax(0, MathMin(wins, trades));
      if(!MathIsValidNumber(pnl)) pnl = 0.0;
      if(!MathIsValidNumber(upside)) upside = 0.0;
      upside = MathMax(0.0, upside);
      if(!MathIsValidNumber(downside)) downside = 0.0;
      downside = MathMax(0.0, downside);
      if(!MathIsValidNumber(learningRate) || learningRate <= 0.0 || learningRate > 1.0)
         learningRate = InpLearningRateInit;

      // Now perform all array assignments with bounds-checked index
      // Using ArraySize check immediately before access satisfies static analysis
      if(i >= 0 && i < ArraySize(profile.regime))
      {
         profile.regime[i].qBuy = qBuy;
         profile.regime[i].qSell = qSell;
         profile.regime[i].qHold = qHold;
         profile.regime[i].trades = trades;
         profile.regime[i].wins = wins;
         profile.regime[i].pnl = pnl;
         profile.regime[i].upside = upside;
         profile.regime[i].downside = downside;
         profile.regime[i].learningRate = learningRate;
         profile.regime[i].InvalidateCache();
      }
   }
}

#endif // VT_PERSISTENCE_MQH
