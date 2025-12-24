//+------------------------------------------------------------------+
//| MQL5 Mock Header for C++ Linting                                 |
//| This file mocks MQL5 types and functions for use with C++ linters|
//| like clang-tidy and cppcheck                                     |
//+------------------------------------------------------------------+

#ifndef MQL5_MOCK_H
#define MQL5_MOCK_H

#include <cstdint>
#include <string>

// MQL5 Basic Types
typedef int64_t datetime;
typedef uint32_t color;

// MQL5 Storage Classes
#define input
#define sinput static
#define extern

// MQL5 Common Constants
#define PERIOD_CURRENT 0
#define PERIOD_M1 1
#define OP_BUY 0
#define OP_SELL 1

// MQL5 Built-in Functions (Mock)
inline double SymbolInfoDouble(const std::string& symbol, int prop_id) { return 0.0; }
inline bool OrderSend(const std::string& symbol, int cmd, double volume, double price, 
                     int slippage, double stoploss, double takeprofit) { return true; }
inline void Print(const std::string& msg) {}
inline int GetLastError() { return 0; }

// Event Handlers
inline int OnInit() { return 0; }
inline void OnDeinit(const int reason) {}
inline void OnTick() {}

#endif // MQL5_MOCK_H
