//+------------------------------------------------------------------+
//|                                                      VT_HUD.mqh  |
//|                         VelocityTrader v7.1: Duel Architecture   |
//|                     HUD (Heads-Up Display) Functions              |
//+------------------------------------------------------------------+
#property copyright "VelocityTrader v7.1"
#property link      "Kinematic Duel Architecture"

#ifndef VT_HUD_MQH
#define VT_HUD_MQH

#include "VT_Definitions.mqh"
#include "VT_Globals.mqh"

// Forward declaration of input parameters (defined in main EA)
extern bool      InpShowHUD;
extern int       InpHUD_X;
extern int       InpHUD_Y;
extern int       InpDefaultTab;
extern bool      InpAutoRotateTabs;
extern int       InpShadowTimeoutMin;
extern double    InpLearningRateInit;
extern double    InpMinProbability;
extern double    InpMaxDrawdown;
extern double    InpMaxDailyLoss;
extern int       InpCooldownMinutes;
extern int       InpRetrainMinTrades;
extern bool      InpUseOmegaSizing;
extern double    InpOmegaBaseline;
extern double    InpOmegaMaxScale;
extern double    InpRiskPercent;
extern double    InpMaxLot;
extern int       InpMaxPositions;

// Forward declarations - these are defined in main EA
int CountRealPositions();
int CountShadowPositions();

//+------------------------------------------------------------------+
//| HUD_Create: Create/Update Text Label                              |
//+------------------------------------------------------------------+
void HUD_Create(string name, int x, int y, string text, color clr, int size = 8)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
      ArrayResize(g_hudObjects, g_hudCount + 1);
      g_hudObjects[g_hudCount++] = name;
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetString(0, name, OBJPROP_FONT, "Consolas");
      ObjectSetInteger(0, name, OBJPROP_ZORDER, 10);
   }
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, size);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
}

//+------------------------------------------------------------------+
//| HUD_Rect: Create/Update Rectangle Background                      |
//+------------------------------------------------------------------+
void HUD_Rect(string name, int x, int y, int w, int h, color bg, color border)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
      ArrayResize(g_hudObjects, g_hudCount + 1);
      g_hudObjects[g_hudCount++] = name;
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_BACK, false);
      ObjectSetInteger(0, name, OBJPROP_ZORDER, 0);
   }
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, name, OBJPROP_YSIZE, h);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, border);
}

//+------------------------------------------------------------------+
//| CleanupHUD: Remove all HUD objects                                |
//+------------------------------------------------------------------+
void CleanupHUD()
{
   for(int i = 0; i < g_hudCount; i++)
      ObjectDelete(0, g_hudObjects[i]);
   g_hudCount = 0;
   ArrayResize(g_hudObjects, 0);
}

//+------------------------------------------------------------------+
//| Forward declarations for tab drawing functions                    |
//+------------------------------------------------------------------+
void DrawTab_Dashboard(int x, int &y, int h, int sec);
void DrawTab_Performance(int x, int &y, int h, int sec);
void DrawTab_Training(int x, int &y, int h, int sec);
void DrawTab_Probability(int x, int &y, int h, int sec);
void DrawTab_Risk(int x, int &y, int h, int sec);
void DrawTab_Instruments(int x, int &y, int h, int sec);

//+------------------------------------------------------------------+
//| DrawHUD: Main HUD rendering function                              |
//+------------------------------------------------------------------+
void DrawHUD()
{
   if(!InpShowHUD) return;

   // Track tab changes to clear old content
   static int lastTab = -1;

   // Initialize tab on first run
   static bool tabInit = false;
   if(!tabInit)
   {
      g_hudTab = InpDefaultTab;
      if(g_hudTab < 0 || g_hudTab >= TAB_COUNT) g_hudTab = 0;
      tabInit = true;
   }

   // Auto-rotate tabs
   if(InpAutoRotateTabs && TimeCurrent() - g_hudLastTabSwitch >= 5)
   {
      g_hudTab = (g_hudTab + 1) % TAB_COUNT;
      g_hudLastTabSwitch = TimeCurrent();
   }

   // Clear ALL HUD objects when tab changes
   if(lastTab != g_hudTab)
   {
      CleanupHUD();
      lastTab = g_hudTab;
   }

   // Update system status periodically
   static datetime lastStatusUpdate = 0;
   if(TimeCurrent() - lastStatusUpdate > 5)
   {
      g_status.Update();
      lastStatusUpdate = TimeCurrent();
   }

   int x = InpHUD_X;
   int yStart = InpHUD_Y;
   int y = yStart + 5;
   int h = 11;
   int sec = 3;

   // Wider panel to fit content
   int panelWidth = 480;
   int panelHeight = 420;

   // Draw background
   HUD_Rect("H_Bg", x, yStart, panelWidth, panelHeight, CLR_PANEL_BG, CLR_BORDER);

   // ===============================================================
   // HEADER (Always visible)
   // ===============================================================
   HUD_Create("H_Title", x+8, y, "══════════ VELOCITY v7.1 DUEL ══════════", CLR_HEADER, 9);
   y += 14;

   // Status traffic lights
   string brokerSt = g_status.brokerConnected ? "~" : "!";
   string netSt = g_status.networkOK ? "~" : "!";
   string rlSt = g_status.rlActive ? "~" : "o";
   string riskSt = g_status.riskOK ? "~" : "!";

   color brokerClr = g_status.brokerConnected ? CLR_POSITIVE : CLR_NEGATIVE;
   color netClr = g_status.networkOK ? CLR_POSITIVE : CLR_NEGATIVE;
   color rlClr = g_status.rlActive ? CLR_POSITIVE : CLR_NEUTRAL;
   color riskClr = g_status.riskOK ? CLR_POSITIVE : CLR_NEGATIVE;

   bool isBacktest = (MQLInfoInteger(MQL_TESTER) != 0);
   string modeStr = isBacktest ? "BACKTEST" : "LIVE";

   HUD_Create("H_Mode", x+8, y, StringFormat("[%s] BRK:%s NET:%s RL:%s RISK:%s",
      modeStr, brokerSt, netSt, rlSt, riskSt),
      (g_status.riskOK && g_status.networkOK) ? CLR_POSITIVE : CLR_NEGATIVE);
   y += h;

   // Quick account summary
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double floatingPnL = equity - balance;
   int realPos = CountRealPositions();
   int shadowPos = CountShadowPositions();

   color eqClr = (floatingPnL >= 0) ? CLR_POSITIVE : CLR_NEGATIVE;
   HUD_Create("H_Acc", x+8, y, StringFormat("Eq:$%.0f Bal:$%.0f Float:%+.0f | R:%d S:%d",
      equity, balance, floatingPnL, realPos, shadowPos), eqClr);
   y += h + 2;

   // ===============================================================
   // TAB BAR
   // ===============================================================
   string tabs[] = {"DASH", "PERF", "RL", "PROB", "RISK", "INST"};
   int tabWidth = 75;

   for(int i = 0; i < TAB_COUNT; i++)
   {
      string tabName = "H_Tab" + IntegerToString(i);
      color tabClr = (i == g_hudTab) ? CLR_HEADER : CLR_MUTED;
      string tabText = (i == g_hudTab) ? "[" + tabs[i] + "]" : " " + tabs[i] + " ";
      HUD_Create(tabName, x + 8 + (i * tabWidth), y, tabText, tabClr);
   }
   y += h + sec;

   // Separator
   HUD_Create("H_Sep", x+8, y, "-----------------------------------------------", CLR_BORDER);
   y += h;

   // ===============================================================
   // TAB CONTENT
   // ===============================================================
   switch(g_hudTab)
   {
      case TAB_OVERVIEW:    DrawTab_Dashboard(x, y, h, sec); break;
      case TAB_PERFORMANCE: DrawTab_Performance(x, y, h, sec); break;
      case TAB_TRAINING:    DrawTab_Training(x, y, h, sec); break;
      case TAB_PROBABILITY: DrawTab_Probability(x, y, h, sec); break;
      case TAB_RISK:        DrawTab_Risk(x, y, h, sec); break;
      case TAB_SIGNALS:     DrawTab_Instruments(x, y, h, sec); break;
   }

   // Navigation hint at bottom
   HUD_Create("H_Hint", x+8, panelHeight + yStart - 14,
      "Navigate: 1-6 | TAB | Arrows", CLR_MUTED);

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| TAB: DASHBOARD (Management Overview)                              |
//+------------------------------------------------------------------+
void DrawTab_Dashboard(int x, int &y, int h, int sec)
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   // P&L Summary
   HUD_Create("H_D1", x+8, y, "--- P&L SUMMARY ---", CLR_HEADER);
   y += h;

   color dayClr = (g_dayStats.pnl >= 0) ? CLR_POSITIVE : CLR_NEGATIVE;
   color weekClr = (g_weekStats.pnl >= 0) ? CLR_POSITIVE : CLR_NEGATIVE;
   color monthClr = (g_monthStats.pnl >= 0) ? CLR_POSITIVE : CLR_NEGATIVE;
   color totalClr = (g_totalStats.pnl >= 0) ? CLR_POSITIVE : CLR_NEGATIVE;

   HUD_Create("H_D2", x+8, y, StringFormat("Today: %+.0f (%d trd, %.0f%% WR)",
      g_dayStats.pnl, g_dayStats.trades, g_dayStats.GetWR()), dayClr);
   y += h;
   HUD_Create("H_D3", x+8, y, StringFormat("Week:  %+.0f (%d trd, %.0f%% WR)",
      g_weekStats.pnl, g_weekStats.trades, g_weekStats.GetWR()), weekClr);
   y += h;
   HUD_Create("H_D4", x+8, y, StringFormat("Month: %+.0f (%d trd, %.0f%% WR)",
      g_monthStats.pnl, g_monthStats.trades, g_monthStats.GetWR()), monthClr);
   y += h;
   HUD_Create("H_D5", x+8, y, StringFormat("Total: %+.0f (%d trd, %.0f%% WR)",
      g_totalStats.pnl, g_totalStats.trades, g_totalStats.GetWR()), totalClr);
   y += h + sec;

   // Agent Summary with traffic lights
   HUD_Create("H_D6", x+8, y, "--- AGENTS ---", CLR_HEADER);
   y += h;

   string sniEdge = g_sniper.hasEdge ? "[OK]" : "[--]";
   color sniClr = g_sniper.hasEdge ? CLR_POSITIVE : CLR_MUTED;
   double sniAlloc = g_sniper.capitalAlloc * 100;

   HUD_Create("H_D7", x+8, y, StringFormat("SNIPER   %s Alloc:%.0f%% PF:%.2f WR:%.0f%% $%+.0f",
      sniEdge, sniAlloc, g_sniper.shadow.GetPF(),
      g_sniper.shadow.GetWinRate()*100, g_sniper.shadow.totalPnL), sniClr);
   y += h;

   string berEdge = g_berserker.hasEdge ? "[OK]" : "[--]";
   color berClr = g_berserker.hasEdge ? CLR_POSITIVE : CLR_MUTED;
   double berAlloc = g_berserker.capitalAlloc * 100;

   HUD_Create("H_D8", x+8, y, StringFormat("BERSERKER %s Alloc:%.0f%% PF:%.2f WR:%.0f%% $%+.0f",
      berEdge, berAlloc, g_berserker.shadow.GetPF(),
      g_berserker.shadow.GetWinRate()*100, g_berserker.shadow.totalPnL), berClr);
   y += h + sec;

   // System State
   HUD_Create("H_D9", x+8, y, "--- SYSTEM STATE ---", CLR_HEADER);
   y += h;

   string stateStr = g_breaker.GetStateString();
   color stateClr = (g_breaker.state == STATE_LIVE) ? CLR_POSITIVE :
                    (g_breaker.state == STATE_PENDING) ? CLR_NEUTRAL : CLR_NEGATIVE;
   HUD_Create("H_D10", x+8, y, StringFormat("Circuit Breaker: %s", stateStr), stateClr);
   y += h;

   // Open positions status - find oldest
   int oldestAge = 0;
   int openCount = 0;
   for(int i = 0; i < g_posCount; i++)
   {
      if(g_positions[i].active && g_positions[i].isShadow)
      {
         openCount++;
         int age = (int)((TimeCurrent() - g_positions[i].openTime) / 60);
         if(age > oldestAge) oldestAge = age;
      }
   }

   int closedTrades = g_sniper.shadow.totalTrades + g_berserker.shadow.totalTrades;
   int timeToClose = MathMax(0, InpShadowTimeoutMin - oldestAge);

   color learnClr = (closedTrades > 0) ? CLR_POSITIVE : CLR_NEUTRAL;
   HUD_Create("H_D11", x+8, y, StringFormat("Open:%d Closed:%d | Oldest:%dmin (close in %dm)",
      openCount, closedTrades, oldestAge, timeToClose), learnClr);
   y += h;

   // Regime distribution
   int nBrk=0, nTrd=0, nMR=0;
   for(int i = 0; i < g_symbolCount; i++)
   {
      if(!g_symbols[i].initialized) continue;
      ENUM_REGIME reg = g_symbols[i].symc.GetRegime();
      if(reg == REGIME_BREAKOUT) nBrk++;
      else if(reg == REGIME_TREND) nTrd++;
      else if(reg == REGIME_MEANREV) nMR++;
   }

   HUD_Create("H_D12", x+8, y, StringFormat("Regimes: BRK:%d TRD:%d MR:%d | Ranked:%d/%d",
      nBrk, nTrd, nMR, g_rankCount, g_symbolCount), CLR_MUTED);
}

//+------------------------------------------------------------------+
//| TAB: PERFORMANCE (Detailed Stats)                                 |
//+------------------------------------------------------------------+
void DrawTab_Performance(int x, int &y, int h, int sec)
{
   HUD_Create("H_P1", x+8, y, "--- SESSION / CUMULATIVE ---", CLR_HEADER);
   y += h;

   HUD_Create("H_P2", x+8, y, "         Sess  WR%  PnL   Omega | Cum   WR%    PnL    PF", CLR_MUTED);
   y += h;

   // SNIPER Shadow
   double sniSO = (g_sniper.shadow.sessTotalDownside > 0.01) ?
      g_sniper.shadow.sessTotalUpside / g_sniper.shadow.sessTotalDownside : 1.0;
   color sniSC = (g_sniper.shadow.sessTotalPnL >= 0) ? CLR_SHADOW : clrDarkGray;
   HUD_Create("H_PSS", x+8, y, StringFormat("SNI.S   %4d %4.0f%% %+5.0f  %4.1f |%4d %4.0f%% %+6.0f %5.2f",
      g_sniper.shadow.sessTotalTrades, g_sniper.shadow.GetSessWinRate()*100,
      g_sniper.shadow.sessTotalPnL, sniSO,
      g_sniper.shadow.totalTrades, g_sniper.shadow.GetWinRate()*100,
      g_sniper.shadow.totalPnL, g_sniper.shadow.GetPF()), sniSC);
   y += h;

   // SNIPER Real
   double sniRO = (g_sniper.real.sessTotalDownside > 0.01) ?
      g_sniper.real.sessTotalUpside / g_sniper.real.sessTotalDownside : 1.0;
   color sniRC = (g_sniper.real.totalPnL >= 0) ? CLR_SNIPER : CLR_NEGATIVE;
   HUD_Create("H_PSR", x+8, y, StringFormat("SNI.R   %4d %4.0f%% %+5.0f  %4.1f |%4d %4.0f%% %+6.0f %5.2f",
      g_sniper.real.sessTotalTrades, g_sniper.real.GetSessWinRate()*100,
      g_sniper.real.sessTotalPnL, sniRO,
      g_sniper.real.totalTrades, g_sniper.real.GetWinRate()*100,
      g_sniper.real.totalPnL, g_sniper.real.GetPF()), sniRC);
   y += h;

   // BERSERKER Shadow
   double berSO = (g_berserker.shadow.sessTotalDownside > 0.01) ?
      g_berserker.shadow.sessTotalUpside / g_berserker.shadow.sessTotalDownside : 1.0;
   color berSC = (g_berserker.shadow.sessTotalPnL >= 0) ? CLR_SHADOW : clrDarkGray;
   HUD_Create("H_PBS", x+8, y, StringFormat("BER.S   %4d %4.0f%% %+5.0f  %4.1f |%4d %4.0f%% %+6.0f %5.2f",
      g_berserker.shadow.sessTotalTrades, g_berserker.shadow.GetSessWinRate()*100,
      g_berserker.shadow.sessTotalPnL, berSO,
      g_berserker.shadow.totalTrades, g_berserker.shadow.GetWinRate()*100,
      g_berserker.shadow.totalPnL, g_berserker.shadow.GetPF()), berSC);
   y += h;

   // BERSERKER Real
   double berRO = (g_berserker.real.sessTotalDownside > 0.01) ?
      g_berserker.real.sessTotalUpside / g_berserker.real.sessTotalDownside : 1.0;
   color berRC = (g_berserker.real.totalPnL >= 0) ? CLR_BERSERKER : CLR_NEGATIVE;
   HUD_Create("H_PBR", x+8, y, StringFormat("BER.R   %4d %4.0f%% %+5.0f  %4.1f |%4d %4.0f%% %+6.0f %5.2f",
      g_berserker.real.sessTotalTrades, g_berserker.real.GetSessWinRate()*100,
      g_berserker.real.sessTotalPnL, berRO,
      g_berserker.real.totalTrades, g_berserker.real.GetWinRate()*100,
      g_berserker.real.totalPnL, g_berserker.real.GetPF()), berRC);
   y += h + sec;

   // MAE/MFE Analysis
   HUD_Create("H_P3", x+8, y, "--- MAE/MFE (Trade Quality) ---", CLR_HEADER);
   y += h;

   HUD_Create("H_P4", x+8, y, "         AvgMAE  MaxMAE  AvgMFE  MaxMFE   ETD", CLR_MUTED);
   y += h;

   double sniAvgPnL = (g_sniper.shadow.totalTrades > 0) ?
      g_sniper.shadow.totalPnL / g_sniper.shadow.totalTrades : 0;
   double sniETD = g_sniperExcursion.GetAvgETD(sniAvgPnL);

   HUD_Create("H_P5", x+8, y, StringFormat("SNIPER  %6.0f  %6.0f  %6.0f  %6.0f  %5.0f",
      g_sniperExcursion.avgMAE, g_sniperExcursion.maxMAE,
      g_sniperExcursion.avgMFE, g_sniperExcursion.maxMFE, sniETD), CLR_SNIPER);
   y += h;

   double berAvgPnL = (g_berserker.shadow.totalTrades > 0) ?
      g_berserker.shadow.totalPnL / g_berserker.shadow.totalTrades : 0;
   double berETD = g_berserkerExcursion.GetAvgETD(berAvgPnL);

   HUD_Create("H_P6", x+8, y, StringFormat("BERSER  %6.0f  %6.0f  %6.0f  %6.0f  %5.0f",
      g_berserkerExcursion.avgMAE, g_berserkerExcursion.maxMAE,
      g_berserkerExcursion.avgMFE, g_berserkerExcursion.maxMFE, berETD), CLR_BERSERKER);
   y += h + sec;

   // Consecutive stats
   HUD_Create("H_P7", x+8, y, "--- STREAKS ---", CLR_HEADER);
   y += h;

   HUD_Create("H_P8", x+8, y, StringFormat("ConsLoss: SNI:%d BER:%d | Rolling20WR: SNI:%.0f%% BER:%.0f%%",
      g_sniper.consLosses, g_berserker.consLosses,
      g_sniper.GetRollingWR()*100, g_berserker.GetRollingWR()*100), CLR_MUTED);
}

//+------------------------------------------------------------------+
//| TAB: RL TRAINING                                                  |
//+------------------------------------------------------------------+
void DrawTab_Training(int x, int &y, int h, int sec)
{
   int totalClosed = g_sniper.shadow.totalTrades + g_berserker.shadow.totalTrades;

   // Show waiting message if no trades closed yet
   if(totalClosed == 0)
   {
      HUD_Create("H_T0", x+8, y, "*** WAITING FOR TRADES TO CLOSE ***", CLR_NEUTRAL);
      y += h;
      HUD_Create("H_T0a", x+8, y, StringFormat("Shadow timeout: %d minutes", InpShadowTimeoutMin), CLR_MUTED);
      y += h;
      HUD_Create("H_T0b", x+8, y, "Q-values update when trades complete", CLR_MUTED);
      y += h + sec;
   }

   HUD_Create("H_T1", x+8, y, "--- Q-VALUES (Buy/Sell) ---", CLR_HEADER);
   y += h;

   HUD_Create("H_T2", x+8, y, "            BREAKOUT      TREND       MEANREV", CLR_MUTED);
   y += h;

   HUD_Create("H_T3", x+8, y, StringFormat("SNIPER    %+5.1f/%+5.1f  %+5.1f/%+5.1f  %+5.1f/%+5.1f",
      g_sniper.shadow.regime[0].qBuy, g_sniper.shadow.regime[0].qSell,
      g_sniper.shadow.regime[1].qBuy, g_sniper.shadow.regime[1].qSell,
      g_sniper.shadow.regime[2].qBuy, g_sniper.shadow.regime[2].qSell), CLR_SNIPER);
   y += h;

   HUD_Create("H_T4", x+8, y, StringFormat("BERSERKER %+5.1f/%+5.1f  %+5.1f/%+5.1f  %+5.1f/%+5.1f",
      g_berserker.shadow.regime[0].qBuy, g_berserker.shadow.regime[0].qSell,
      g_berserker.shadow.regime[1].qBuy, g_berserker.shadow.regime[1].qSell,
      g_berserker.shadow.regime[2].qBuy, g_berserker.shadow.regime[2].qSell), CLR_BERSERKER);
   y += h + sec;

   // Learning rates
   HUD_Create("H_T5", x+8, y, "--- LEARNING RATES ---", CLR_HEADER);
   y += h;

   double sniAvg = (g_sniper.shadow.regime[0].learningRate +
                    g_sniper.shadow.regime[1].learningRate +
                    g_sniper.shadow.regime[2].learningRate) / 3.0;
   HUD_Create("H_T6", x+8, y, StringFormat("SNIPER    %.4f    %.4f    %.4f   Avg:%.4f",
      g_sniper.shadow.regime[0].learningRate,
      g_sniper.shadow.regime[1].learningRate,
      g_sniper.shadow.regime[2].learningRate, sniAvg), CLR_SNIPER);
   y += h;

   double berAvg = (g_berserker.shadow.regime[0].learningRate +
                    g_berserker.shadow.regime[1].learningRate +
                    g_berserker.shadow.regime[2].learningRate) / 3.0;
   HUD_Create("H_T7", x+8, y, StringFormat("BERSERKER %.4f    %.4f    %.4f   Avg:%.4f",
      g_berserker.shadow.regime[0].learningRate,
      g_berserker.shadow.regime[1].learningRate,
      g_berserker.shadow.regime[2].learningRate, berAvg), CLR_BERSERKER);
   y += h + sec;

   // Convergence
   double convSni = (1.0 - sniAvg / InpLearningRateInit) * 100;
   double convBer = (1.0 - berAvg / InpLearningRateInit) * 100;
   string status = (convSni > 80 && convBer > 80) ? "CONVERGED" :
                   (convSni > 50 || convBer > 50) ? "LEARNING" : "EXPLORING";
   color statClr = (convSni > 80 && convBer > 80) ? CLR_POSITIVE :
                   (convSni > 50 || convBer > 50) ? CLR_NEUTRAL : CLR_SHADOW;

   HUD_Create("H_T8", x+8, y, StringFormat("Convergence: SNI:%.0f%% BER:%.0f%% [%s]",
      convSni, convBer, status), statClr);
   y += h + sec;

   // Reward shaping params - now RL-tunable
   HUD_Create("H_T9", x+8, y, "--- RL PARAMETERS (0-1 normalized) ---", CLR_HEADER);
   y += h;
   HUD_Create("H_T10", x+8, y, StringFormat("LossPen:%.2f(x%.1f) TimeDecay:%.2f(%.3f/m) Surprise:%.2f(x%.1f)",
      g_rlParams.n_lossPenalty, g_rlParams.GetLossPenalty(),
      g_rlParams.n_timeDecay, g_rlParams.GetTimeDecay(),
      g_rlParams.n_surpriseBoost, g_rlParams.GetSurpriseBoost()), CLR_MUTED);
   y += h;
   HUD_Create("H_T11", x+8, y, StringFormat("Trail:%.2f(%.1fATR) SL:%.2f(%.1fATR) TP:%.2f(%.1fATR)",
      g_rlParams.n_trailATR, g_rlParams.GetTrailATR(),
      g_rlParams.n_slATR, g_rlParams.GetSL_ATR(),
      g_rlParams.n_tpATR, g_rlParams.GetTP_ATR()), CLR_MUTED);
   y += h;
   HUD_Create("H_T12", x+8, y, StringFormat("Vel:%.2f(%.2f) MeanRev:%.2f(%.1fs) ZExt:%.2f(%.1fs)",
      g_rlParams.n_velocityThresh, g_rlParams.GetVelocityThresh(),
      g_rlParams.n_meanRevThresh, g_rlParams.GetMeanRevThresh(),
      g_rlParams.n_zScoreExtreme, g_rlParams.GetZScoreExtreme()), CLR_MUTED);
}

//+------------------------------------------------------------------+
//| TAB: PROBABILITY                                                  |
//+------------------------------------------------------------------+
void DrawTab_Probability(int x, int &y, int h, int sec)
{
   HUD_Create("H_Pb1", x+8, y, "--- REGIME P(WIN) ---", CLR_HEADER);
   y += h;

   color brk = (g_predictor.regimeWR[0] >= 0.55) ? CLR_POSITIVE : CLR_MUTED;
   color trd = (g_predictor.regimeWR[1] >= 0.55) ? CLR_POSITIVE : CLR_MUTED;
   color mr = (g_predictor.regimeWR[2] >= 0.55) ? CLR_POSITIVE : CLR_MUTED;

   HUD_Create("H_Pb2", x+8, y, StringFormat("BREAKOUT:  %.0f%% (n=%d)",
      g_predictor.regimeWR[0]*100, g_predictor.regimeCounts[0]), brk);
   y += h;
   HUD_Create("H_Pb3", x+8, y, StringFormat("TREND:     %.0f%% (n=%d)",
      g_predictor.regimeWR[1]*100, g_predictor.regimeCounts[1]), trd);
   y += h;
   HUD_Create("H_Pb4", x+8, y, StringFormat("MEANREV:   %.0f%% (n=%d)",
      g_predictor.regimeWR[2]*100, g_predictor.regimeCounts[2]), mr);
   y += h + sec;

   HUD_Create("H_Pb5", x+8, y, "--- CHI ZONES P(WIN) ---", CLR_HEADER);
   y += h;
   HUD_Create("H_Pb6", x+8, y, "   <-2s     -1s      0      +1s    >+2s", CLR_MUTED);
   y += h;
   HUD_Create("H_Pb7", x+8, y, StringFormat("   %.0f%%     %.0f%%    %.0f%%    %.0f%%    %.0f%%",
      g_predictor.chiZoneWR[0]*100, g_predictor.chiZoneWR[1]*100,
      g_predictor.chiZoneWR[2]*100, g_predictor.chiZoneWR[3]*100,
      g_predictor.chiZoneWR[4]*100), CLR_NEUTRAL);
   y += h + sec;

   HUD_Create("H_Pb8", x+8, y, "--- ACCEL ZONES P(WIN) ---", CLR_HEADER);
   y += h;
   HUD_Create("H_Pb9", x+8, y, "   <-2s     -1s      0      +1s    >+2s", CLR_MUTED);
   y += h;
   HUD_Create("H_Pb10", x+8, y, StringFormat("   %.0f%%     %.0f%%    %.0f%%    %.0f%%    %.0f%%",
      g_predictor.accelZoneWR[0]*100, g_predictor.accelZoneWR[1]*100,
      g_predictor.accelZoneWR[2]*100, g_predictor.accelZoneWR[3]*100,
      g_predictor.accelZoneWR[4]*100), CLR_NEUTRAL);
   y += h + sec;

   HUD_Create("H_Pb11", x+8, y, StringFormat("Min P(Win) Gate: %.0f%% (Real trades only)",
      InpMinProbability * 100), CLR_MUTED);
}

//+------------------------------------------------------------------+
//| TAB: RISK MANAGEMENT                                              |
//+------------------------------------------------------------------+
void DrawTab_Risk(int x, int &y, int h, int sec)
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   HUD_Create("H_R1", x+8, y, "--- DRAWDOWN ---", CLR_HEADER);
   y += h;

   double dd = 0;
   if(g_breaker.peakEquity > 0)
      dd = (g_breaker.peakEquity - equity) / g_breaker.peakEquity * 100;

   color ddClr = (dd < InpMaxDrawdown * 50) ? CLR_POSITIVE :
                 (dd < InpMaxDrawdown * 100) ? CLR_NEUTRAL : CLR_NEGATIVE;

   HUD_Create("H_R2", x+8, y, StringFormat("Current: %.2f%% / %.0f%% max | Peak: $%.0f",
      dd, InpMaxDrawdown * 100, g_breaker.peakEquity), ddClr);
   y += h + sec;

   HUD_Create("H_R3", x+8, y, "--- DAILY LIMITS ---", CLR_HEADER);
   y += h;

   double sessionPnL = equity - g_sessionEquity;
   double dailyLossPct = (g_sessionEquity > 0) ? MathMin(0, sessionPnL) / g_sessionEquity * 100 : 0;

   color dayClr = (MathAbs(dailyLossPct) < InpMaxDailyLoss * 50) ? CLR_POSITIVE :
                  (MathAbs(dailyLossPct) < InpMaxDailyLoss * 100) ? CLR_NEUTRAL : CLR_NEGATIVE;

   HUD_Create("H_R4", x+8, y, StringFormat("Daily Loss: %.2f%% / %.0f%% max",
      MathAbs(dailyLossPct), InpMaxDailyLoss * 100), dayClr);
   y += h + sec;

   HUD_Create("H_R5", x+8, y, "--- CIRCUIT BREAKER ---", CLR_HEADER);
   y += h;

   string stateStr = g_breaker.GetStateString();
   color cbClr = (g_breaker.state == STATE_LIVE) ? CLR_POSITIVE :
                 (g_breaker.state == STATE_PENDING) ? CLR_NEUTRAL : CLR_NEGATIVE;
   HUD_Create("H_R6", x+8, y, StringFormat("State: %s", stateStr), cbClr);
   y += h;

   if(g_breaker.state == STATE_HALTED)
   {
      int rem = InpCooldownMinutes - (int)((TimeCurrent() - g_breaker.haltTime) / 60);
      HUD_Create("H_R7", x+8, y, StringFormat("Reason: %s | %dmin remaining",
         g_breaker.haltReason, MathMax(0, rem)), CLR_NEGATIVE);
      y += h;
   }
   else if(g_breaker.state == STATE_RETRAINING)
   {
      double wr = (g_breaker.retrainTrades > 0) ?
                 ((double)g_breaker.retrainWins / g_breaker.retrainTrades * 100) : 0;
      HUD_Create("H_R7", x+8, y, StringFormat("Retrain: %d/%d trades WR:%.0f%%",
         g_breaker.retrainTrades, InpRetrainMinTrades, wr), CLR_NEUTRAL);
      y += h;
   }
   y += sec;

   HUD_Create("H_R8", x+8, y, "--- POSITION SIZING ---", CLR_HEADER);
   y += h;
   HUD_Create("H_R9", x+8, y, StringFormat("Risk: %.1f%% | Max Lot: %.2f | Max Pos: %d",
      InpRiskPercent, InpMaxLot, InpMaxPositions), CLR_MUTED);
   y += h;
   HUD_Create("H_R10", x+8, y, StringFormat("Omega Sizing: %s | Base:%.1f MaxScale:%.1fx",
      InpUseOmegaSizing ? "ON" : "OFF", InpOmegaBaseline, InpOmegaMaxScale), CLR_MUTED);
}

//+------------------------------------------------------------------+
//| TAB: INSTRUMENTS (By Regime)                                      |
//+------------------------------------------------------------------+
void DrawTab_Instruments(int x, int &y, int h, int sec)
{
   // Collect top symbols by regime
   int trdIdx[5], brkIdx[5], mrIdx[5];
   double trdScore[5], brkScore[5], mrScore[5];
   int trdCnt = 0, brkCnt = 0, mrCnt = 0;

   ArrayInitialize(trdIdx, -1);
   ArrayInitialize(brkIdx, -1);
   ArrayInitialize(mrIdx, -1);
   ArrayInitialize(trdScore, -999);
   ArrayInitialize(brkScore, -999);
   ArrayInitialize(mrScore, -999);

   for(int i = 0; i < g_rankCount && i < 50; i++)
   {
      int idx = g_ranking[i].symbolIdx;
      if(idx < 0 || idx >= g_symbolCount) continue;
      if(!g_symbols[idx].initialized) continue;

      ENUM_REGIME regime = g_symbols[idx].symc.GetRegime();
      double accel = g_symbols[idx].physics.GetAcceleration();
      double score = MathAbs(accel);

      if(regime == REGIME_TREND && trdCnt < 5)
      {
         trdIdx[trdCnt] = idx;
         trdScore[trdCnt] = accel;
         trdCnt++;
      }
      else if(regime == REGIME_BREAKOUT && brkCnt < 5)
      {
         brkIdx[brkCnt] = idx;
         brkScore[brkCnt] = accel;
         brkCnt++;
      }
      else if(regime == REGIME_MEANREV && mrCnt < 5)
      {
         mrIdx[mrCnt] = idx;
         mrScore[mrCnt] = accel;
         mrCnt++;
      }
   }

   // TREND
   HUD_Create("H_I1", x+8, y, "--- TRENDING ---", clrDodgerBlue);
   y += h;
   for(int i = 0; i < 5; i++)
   {
      if(trdIdx[i] >= 0)
      {
         string dir = (trdScore[i] > 0) ? "^" : "v";
         double chi = g_symbols[trdIdx[i]].symc.GetChi();
         HUD_Create("H_IT" + IntegerToString(i), x+8, y,
            StringFormat("%s %-7s Chi:%.1f Acc:%+.1f", dir, g_symbols[trdIdx[i]].name, chi, trdScore[i]),
            (trdScore[i] > 0) ? clrLime : clrOrangeRed);
      }
      else
         HUD_Create("H_IT" + IntegerToString(i), x+8, y, "  ---", CLR_MUTED);
      y += h;
   }
   y += sec;

   // BREAKOUT
   HUD_Create("H_I2", x+8, y, "--- BREAKOUT ---", clrMagenta);
   y += h;
   for(int i = 0; i < 3; i++)  // Just 3 for space
   {
      if(brkIdx[i] >= 0)
      {
         string dir = (brkScore[i] > 0) ? "^" : "v";
         double chi = g_symbols[brkIdx[i]].symc.GetChi();
         HUD_Create("H_IB" + IntegerToString(i), x+8, y,
            StringFormat("%s %-7s Chi:%.1f Acc:%+.1f", dir, g_symbols[brkIdx[i]].name, chi, brkScore[i]),
            (brkScore[i] > 0) ? clrLime : clrOrangeRed);
      }
      else
         HUD_Create("H_IB" + IntegerToString(i), x+8, y, "  ---", CLR_MUTED);
      y += h;
   }
   y += sec;

   // MEANREV
   HUD_Create("H_I3", x+8, y, "--- MEAN REV ---", clrGold);
   y += h;
   for(int i = 0; i < 3; i++)  // Just 3 for space
   {
      if(mrIdx[i] >= 0)
      {
         string dir = (mrScore[i] > 0) ? "^" : "v";
         double chi = g_symbols[mrIdx[i]].symc.GetChi();
         HUD_Create("H_IM" + IntegerToString(i), x+8, y,
            StringFormat("%s %-7s Chi:%.1f Acc:%+.1f", dir, g_symbols[mrIdx[i]].name, chi, mrScore[i]),
            (mrScore[i] > 0) ? clrLime : clrOrangeRed);
      }
      else
         HUD_Create("H_IM" + IntegerToString(i), x+8, y, "  ---", CLR_MUTED);
      y += h;
   }
}

//+------------------------------------------------------------------+
//| HandleChartEvent: Process keyboard input for tab navigation       |
//| Note: Call this from main EA's OnChartEvent                       |
//+------------------------------------------------------------------+
void HandleHUDChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   if(id == CHARTEVENT_KEYDOWN)
   {
      // Keys 1-6 switch tabs directly
      if(lparam >= 49 && lparam <= 54)  // '1' to '6'
      {
         g_hudTab = (int)(lparam - 49);
         g_hudLastTabSwitch = TimeCurrent();
      }
      // TAB key cycles forward
      else if(lparam == 9)  // TAB
      {
         g_hudTab = (g_hudTab + 1) % TAB_COUNT;
         g_hudLastTabSwitch = TimeCurrent();
      }
      // Left arrow - previous tab
      else if(lparam == 37)
      {
         g_hudTab = (g_hudTab - 1 + TAB_COUNT) % TAB_COUNT;
         g_hudLastTabSwitch = TimeCurrent();
      }
      // Right arrow - next tab
      else if(lparam == 39)
      {
         g_hudTab = (g_hudTab + 1) % TAB_COUNT;
         g_hudLastTabSwitch = TimeCurrent();
      }
   }
}

#endif // VT_HUD_MQH
