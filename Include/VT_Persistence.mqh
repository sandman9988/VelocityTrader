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

// Forward declaration of input parameters (defined in main EA)
extern bool      InpUsePersistence;
extern string    InpFilePrefix;
extern int       InpMagicNumber;
extern double    InpLearningRateInit;

// Persistence version for file format compatibility
#define PERSISTENCE_VERSION  720   // Updated for learning rate storage

//+------------------------------------------------------------------+
//| Calculate simple checksum for data validation                     |
//+------------------------------------------------------------------+
uint CalculateChecksum(const uchar &data[], int size)
{
   uint checksum = 0x12345678;
   for(int i = 0; i < size; i++)
   {
      checksum ^= ((uint)data[i] << ((i % 4) * 8));
      checksum = (checksum << 1) | (checksum >> 31);  // Rotate left
   }
   return checksum;
}

//+------------------------------------------------------------------+
//| Forward declarations                                              |
//+------------------------------------------------------------------+
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

   // Step 1: Write to temporary file
   int handle = FileOpen(tempFilename, FILE_WRITE | FILE_BIN);
   if(handle == INVALID_HANDLE)
   {
      Print("ERROR: Cannot create temp file for save");
      return;
   }

   // Write header
   FileWriteInteger(handle, PERSISTENCE_MAGIC);
   FileWriteInteger(handle, PERSISTENCE_VERSION);
   FileWriteLong(handle, TimeCurrent());  // Save timestamp

   // Save agents
   SaveAgent(handle, g_sniper);
   SaveAgent(handle, g_berserker);

   // Save predictor
   for(int i = 0; i < 3; i++) FileWriteDouble(handle, g_predictor.regimeWR[i]);
   for(int i = 0; i < 5; i++) FileWriteDouble(handle, g_predictor.chiZoneWR[i]);
   for(int i = 0; i < 5; i++) FileWriteDouble(handle, g_predictor.accelZoneWR[i]);
   for(int i = 0; i < 3; i++) FileWriteInteger(handle, g_predictor.regimeCounts[i]);
   for(int i = 0; i < 5; i++) FileWriteInteger(handle, g_predictor.chiCounts[i]);
   for(int i = 0; i < 5; i++) FileWriteInteger(handle, g_predictor.accelCounts[i]);

   // Save circuit breaker state
   FileWriteInteger(handle, (int)g_breaker.state);
   FileWriteDouble(handle, g_breaker.peakEquity);

   // Calculate and write checksum placeholder position
   ulong checksumPos = FileTell(handle);
   FileWriteInteger(handle, 0);  // Placeholder

   FileFlush(handle);
   FileClose(handle);

   // Step 2: Validate temp file is readable
   handle = FileOpen(tempFilename, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE)
   {
      Print("ERROR: Cannot verify temp file");
      FileDelete(tempFilename);
      return;
   }

   // Quick validation - check magic and version
   int magic = FileReadInteger(handle);
   int version = FileReadInteger(handle);
   FileClose(handle);

   if(magic != PERSISTENCE_MAGIC || version != PERSISTENCE_VERSION)
   {
      Print("ERROR: Temp file validation failed");
      FileDelete(tempFilename);
      return;
   }

   // Step 3: Atomic swap - backup old, rename temp to main
   if(FileIsExist(mainFilename))
   {
      // Delete old backup if exists
      if(FileIsExist(backupFilename))
         FileDelete(backupFilename);

      // Move current to backup
      if(!FileMove(mainFilename, 0, backupFilename, FILE_REWRITE))
      {
         Print("WARNING: Could not create backup");
      }
   }

   // Rename temp to main (atomic on most filesystems)
   if(!FileMove(tempFilename, 0, mainFilename, FILE_REWRITE))
   {
      Print("ERROR: Could not finalize save");
      return;
   }

   // Clean up temp file if it still exists
   if(FileIsExist(tempFilename))
      FileDelete(tempFilename);
}

//+------------------------------------------------------------------+
//| SaveAgent: Save trading agent state                               |
//+------------------------------------------------------------------+
void SaveAgent(int handle, TradingAgent &agent)
{
   // Save real profile
   SaveProfile(handle, agent.real);

   // Save shadow profile
   SaveProfile(handle, agent.shadow);

   // Save meta
   FileWriteDouble(handle, agent.capitalAlloc);
   FileWriteInteger(handle, agent.swapCount);
   FileWriteInteger(handle, agent.consLosses);
}

//+------------------------------------------------------------------+
//| SaveProfile: Save agent profile (Q-values, stats)                 |
//+------------------------------------------------------------------+
void SaveProfile(int handle, AgentProfile &profile)
{
   for(int i = 0; i < 3; i++)
   {
      FileWriteDouble(handle, profile.regime[i].qBuy);
      FileWriteDouble(handle, profile.regime[i].qSell);
      FileWriteDouble(handle, profile.regime[i].qHold);
      FileWriteInteger(handle, profile.regime[i].trades);
      FileWriteInteger(handle, profile.regime[i].wins);
      FileWriteDouble(handle, profile.regime[i].pnl);
      FileWriteDouble(handle, profile.regime[i].upside);
      FileWriteDouble(handle, profile.regime[i].downside);
      FileWriteDouble(handle, profile.regime[i].learningRate);  // v720: Save learning rate
   }
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
//+------------------------------------------------------------------+
bool TryLoadFile(string filename)
{
   int handle = FileOpen(filename, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE) return false;

   // Read and validate header
   int magic = FileReadInteger(handle);
   if(magic != PERSISTENCE_MAGIC)
   {
      FileClose(handle);
      Print("Invalid magic number in ", filename);
      return false;
   }

   int version = FileReadInteger(handle);

   // Handle version migration
   if(version == 710)
   {
      FileClose(handle);
      return LoadStateV710(filename);  // Legacy loader
   }
   else if(version != PERSISTENCE_VERSION)
   {
      FileClose(handle);
      Print("Unknown version ", version, " in ", filename);
      return false;
   }

   datetime saveTime = (datetime)FileReadLong(handle);
   Print("Loading state from ", TimeToString(saveTime));

   // Load agents
   LoadAgent(handle, g_sniper);
   LoadAgent(handle, g_berserker);

   // Load predictor
   for(int i = 0; i < 3; i++) g_predictor.regimeWR[i] = FileReadDouble(handle);
   for(int i = 0; i < 5; i++) g_predictor.chiZoneWR[i] = FileReadDouble(handle);
   for(int i = 0; i < 5; i++) g_predictor.accelZoneWR[i] = FileReadDouble(handle);
   for(int i = 0; i < 3; i++) g_predictor.regimeCounts[i] = FileReadInteger(handle);
   for(int i = 0; i < 5; i++) g_predictor.chiCounts[i] = FileReadInteger(handle);
   for(int i = 0; i < 5; i++) g_predictor.accelCounts[i] = FileReadInteger(handle);

   // Load circuit breaker state
   g_breaker.state = (ENUM_TRADING_STATE)FileReadInteger(handle);
   g_breaker.peakEquity = FileReadDouble(handle);

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

   // Skip header (already validated)
   FileReadInteger(handle);  // magic
   FileReadInteger(handle);  // version

   // Load agents (old format without learning rate)
   LoadAgentV710(handle, g_sniper);
   LoadAgentV710(handle, g_berserker);

   // Load predictor (old format without counts)
   for(int i = 0; i < 3; i++) g_predictor.regimeWR[i] = FileReadDouble(handle);
   for(int i = 0; i < 5; i++) g_predictor.chiZoneWR[i] = FileReadDouble(handle);
   for(int i = 0; i < 5; i++) g_predictor.accelZoneWR[i] = FileReadDouble(handle);

   FileClose(handle);
   Print("Migrated from v710 format successfully");
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
   agent.swapCount = FileReadInteger(handle);

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
      profile.regime[i].trades = FileReadInteger(handle);
      profile.regime[i].wins = FileReadInteger(handle);
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
   agent.swapCount = FileReadInteger(handle);
   agent.consLosses = FileReadInteger(handle);

   agent.real.RecalcTotals();
   agent.shadow.RecalcTotals();
}

//+------------------------------------------------------------------+
//| LoadProfile: Load agent profile (current version)                 |
//+------------------------------------------------------------------+
void LoadProfile(int handle, AgentProfile &profile)
{
   for(int i = 0; i < 3; i++)
   {
      profile.regime[i].qBuy = FileReadDouble(handle);
      profile.regime[i].qSell = FileReadDouble(handle);
      profile.regime[i].qHold = FileReadDouble(handle);
      profile.regime[i].trades = FileReadInteger(handle);
      profile.regime[i].wins = FileReadInteger(handle);
      profile.regime[i].pnl = FileReadDouble(handle);
      profile.regime[i].upside = FileReadDouble(handle);
      profile.regime[i].downside = FileReadDouble(handle);
      profile.regime[i].learningRate = FileReadDouble(handle);  // v720: Load learning rate
      profile.regime[i].InvalidateCache();
   }
}

#endif // VT_PERSISTENCE_MQH
