#!/usr/bin/env python3
"""
Enhanced Main EA Updater
Updates ProjectQuantum_Main.mq5 with all advanced enhancements
"""

import re
from pathlib import Path

class EnhancedMainEAUpdater:
    def __init__(self):
        self.main_ea_path = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development/Experts/ProjectQuantum_Main.mq5")
        
    def update_main_ea(self):
        """Update main EA with all enhancements"""
        print("🔧 Updating ProjectQuantum Main EA with advanced enhancements...")
        
        with open(self.main_ea_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply comprehensive updates
        updated_content = content
        updated_content = self._update_input_parameters(updated_content)
        updated_content = self._add_enhanced_includes(updated_content)
        updated_content = self._replace_kelly_with_omega(updated_content)
        updated_content = self._add_journey_tracking(updated_content)
        updated_content = self._update_global_objects(updated_content)
        updated_content = self._enhance_ontick_function(updated_content)
        updated_content = self._add_self_healing_calls(updated_content)
        updated_content = self._update_version_info(updated_content)
        
        # Write updated content
        with open(self.main_ea_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✅ Main EA updated with all enhancements")
        return True
    
    def _update_input_parameters(self, content: str) -> str:
        """Update input parameters to use Omega instead of Kelly"""
        
        # Replace Kelly parameters with Omega parameters
        replacements = [
            (r'input double\s+InpKellyFraction.*?;.*', 
             'input double   InpOmegaThreshold = 0.0;          // Omega Threshold (0.0 = risk-free rate)'),
            (r'input double\s+InpShadowSwitchThreshold.*?Sortino.*?;',
             'input double   InpShadowSwitchThreshold = 0.5;    // Omega Gap for Shadow Switch'),
            (r'InpKellyFraction', 'InpOmegaThreshold'),
        ]
        
        enhanced = content
        for pattern, replacement in replacements:
            enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
        
        # Add new journey-based parameters
        journey_params = '''
input group "═══ JOURNEY REWARD SHAPING ═══"
input double   InpJourneyWeight = 0.7;             // Journey vs Destination Weight (0.7 = 70% journey)
input double   InpAsymmetricPenalty = 2.5;         // Downside Penalty Multiplier
input double   InpPathConsistencyBonus = 0.3;      // Consistency Reward Multiplier
input bool     InpAdaptiveJourney = true;          // Enable Adaptive Journey Shaping
input int      InpJourneyLookback = 50;            // Journey History Lookback (trades)

input group "═══ OMEGA RATIO SETTINGS ═══"
input double   InpOmegaPositionMultiplier = 1.0;   // Omega Position Size Multiplier
input bool     InpVolatilityAdjustOmega = true;    // Adjust Omega for Volatility
input int      InpOmegaCalculationPeriod = 30;     // Period for Omega Calculation
'''
        
        # Insert new parameters after existing risk management section
        risk_section_end = enhanced.find('input group "═══ SHADOW STRATEGIES ═══"')
        if risk_section_end != -1:
            enhanced = enhanced[:risk_section_end] + journey_params + '\n' + enhanced[risk_section_end:]
        
        return enhanced
    
    def _add_enhanced_includes(self, content: str) -> str:
        """Add includes for enhanced systems"""
        
        new_includes = '''
//--- Enhanced Systems Includes
#include "..\\\\Include\\\\Intelligence\\\\CJourneyReward.mqh"
#include "..\\\\Include\\\\Performance\\\\CLearningMetrics.mqh"
#include "..\\\\Include\\\\Physics\\\\CPhysicsMonitor.mqh"
'''
        
        # Insert after existing includes
        safety_include = content.find('#include "..\\\\Include\\\\Safety\\\\CCircuitBreaker.mqh"')
        if safety_include != -1:
            insertion_point = content.find('\n', safety_include) + 1
            content = content[:insertion_point] + new_includes + content[insertion_point:]
        
        return content
    
    def _replace_kelly_with_omega(self, content: str) -> str:
        """Replace all Kelly references with Omega equivalents"""
        
        # Global variable replacements
        kelly_replacements = [
            (r'InpKellyFraction', 'InpOmegaThreshold'),
            (r'kelly_fraction', 'omega_threshold'),
            (r'Kelly', 'Omega'),
            (r'KELLY', 'OMEGA'),
            (r'Sortino', 'Omega'),
            (r'sortino', 'omega'),
        ]
        
        enhanced = content
        for old, new in kelly_replacements:
            enhanced = re.sub(old, new, enhanced)
        
        return enhanced
    
    def _add_journey_tracking(self, content: str) -> str:
        """Add journey tracking global objects"""
        
        journey_globals = '''
//--- Journey Reward Shaping Objects
CJourneyRewardShaper*    g_journey_shaper = NULL;
COmegaJourneyCalculator* g_omega_calculator = NULL;
CPhysicsNormalizer*      g_physics_normalizer = NULL;
CSelfHealingManager*     g_self_healing = NULL;
CAsyncOperationManager*  g_async_manager = NULL;

//--- Journey Tracking State
double g_journey_history[];
double g_cumulative_journey_score = 0.0;
double g_path_volatility = 0.0;
int g_journey_trade_count = 0;
bool g_journey_initialized = false;
'''
        
        # Insert after existing global objects
        global_objects_end = content.find('CPersistence*        g_persistence = NULL;')
        if global_objects_end != -1:
            insertion_point = content.find('\n', global_objects_end) + 1
            content = content[:insertion_point] + journey_globals + content[insertion_point:]
        
        return content
    
    def _update_global_objects(self, content: str) -> str:
        """Update global object initialization"""
        
        # Find OnInit function and update object creation
        init_enhancements = '''
    // Initialize Journey Reward Shaping
    g_journey_shaper = new CJourneyRewardShaper();
    g_omega_calculator = new COmegaJourneyCalculator(InpOmegaThreshold);
    g_physics_normalizer = new CPhysicsNormalizer();
    g_self_healing = new CSelfHealingManager();
    g_async_manager = new CAsyncOperationManager();
    
    if(g_journey_shaper == NULL || g_omega_calculator == NULL || 
       g_physics_normalizer == NULL || g_self_healing == NULL) {
        CLogger::Error("Failed to initialize enhanced journey systems");
        return INIT_FAILED;
    }
    
    // Initialize journey tracking arrays
    ArrayResize(g_journey_history, InpJourneyLookback);
    ArrayInitialize(g_journey_history, 0.0);
    g_journey_initialized = true;
    
    CLogger::Info("Enhanced journey reward shaping systems initialized");
'''
        
        # Find existing initialization section and add enhancements
        monitor_init = content.find('g_monitor = new CPerformanceMonitor();')
        if monitor_init != -1:
            # Find end of initialization block
            next_section = content.find('CLogger::Info("Initialization complete");', monitor_init)
            if next_section != -1:
                content = content[:next_section] + init_enhancements + '\n    ' + content[next_section:]
        
        return content
    
    def _enhance_ontick_function(self, content: str) -> str:
        """Enhance OnTick function with journey processing"""
        
        # Find OnTick function
        ontick_start = content.find('void OnTick()')
        if ontick_start == -1:
            return content
        
        # Find the end of OnTick function
        brace_count = 0
        pos = content.find('{', ontick_start)
        start_pos = pos
        pos += 1
        
        while pos < len(content):
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                if brace_count == 0:
                    break
                brace_count -= 1
            pos += 1
        
        ontick_end = pos
        
        # Extract OnTick content
        ontick_content = content[start_pos+1:ontick_end]
        
        # Enhanced OnTick with journey processing
        enhanced_ontick = '''
    // === ENHANCED ONTICK WITH JOURNEY PROCESSING ===
    
    // Self-healing system check (high frequency)
    static int healing_tick_counter = 0;
    healing_tick_counter++;
    if(healing_tick_counter >= 10) { // Every 10 ticks
        g_self_healing.MonitorAndHeal();
        healing_tick_counter = 0;
    }
    
    // Async operations processing
    g_async_manager.ProcessAsyncOperations();
    
    // Early exit checks
    if(g_system_state != STATE_TRADING) {
        if(g_system_state == STATE_EMERGENCY) {
            CLogger::Warn("ONTICK", "Emergency state - trading suspended");
        }
        return;
    }
    
    if(!IsNewBar() && g_has_position) {
        UpdatePositionMetrics();
        return; // Skip processing if not new bar and we have position
    }
    
    // Circuit breaker check with self-healing
    if(g_circuit != NULL && g_circuit->IsLocked()) {
        if(g_self_healing.MonitorAndHeal()) {
            CLogger::Info("Self-healing attempted circuit breaker recovery");
        }
        return;
    }
    
    // === CORE MARKET ANALYSIS ===
    
    // Update market sensors with physics normalization
    if(g_sensors != NULL) {
        g_sensors->Update();
        
        // Normalize physics values
        if(g_physics_normalizer != NULL) {
            double momentum = g_sensors->GetMomentum();
            double force = g_sensors->GetForce();
            
            momentum = g_physics_normalizer.NormalizePhysicsValue(momentum, PHYSICS_MOMENTUM, 
                                                                 g_sensors->GetVolatility());
            force = g_physics_normalizer.NormalizePhysicsValue(force, PHYSICS_FORCE,
                                                              g_sensors->GetVolatility());
            
            g_sensors->SetNormalizedValues(momentum, force);
        }
    }
    
    // Update regime with enhanced detection
    if(g_judge != NULL) {
        ENUM_REGIME previous_regime = g_current_regime;
        g_current_regime = g_judge->GetCurrentRegime();
        
        if(previous_regime != g_current_regime) {
            CLogger::Info("REGIME CHANGE", StringFormat("From %s to %s", 
                         EnumToString(previous_regime), EnumToString(g_current_regime)));
            
            // Adaptive journey adjustment on regime change
            if(g_journey_shaper != NULL) {
                g_journey_shaper.OnRegimeChange(g_current_regime);
            }
        }
        
        g_regime_tick_count++;
    }
    
    // === STATE VECTOR CONSTRUCTION ===
    
    g_current_state = ConstructStateVector();
    
    // === OMEGA RATIO CALCULATION AND POSITION SIZING ===
    
    double current_omega = 0.0;
    double journey_adjusted_position = 0.0;
    
    if(g_omega_calculator != NULL && g_journey_shaper != NULL) {
        // Get recent returns for Omega calculation
        double returns[];
        if(GetRecentReturns(returns, InpOmegaCalculationPeriod)) {
            
            // Calculate advanced Omega with journey factors
            double journey_factor = g_journey_shaper.GetCurrentJourneyScore();
            current_omega = g_omega_calculator.CalculateAdvancedOmega(returns, 
                                                                     InpOmegaThreshold, 
                                                                     journey_factor);
            
            // Calculate journey-adjusted position size
            journey_adjusted_position = g_omega_calculator.CalculateOmegaPositionSize(
                current_omega,
                journey_factor,
                GetMarketRegimeFactor(),
                g_sensors != NULL ? g_sensors->GetVolatility() : 1.0
            );
        }
    }
    
    // === RL AGENT DECISION MAKING ===
    
    if(g_agent != NULL && g_replay != NULL) {
        // Get action from RL agent
        ENUM_TRADING_ACTION action = g_agent->SelectAction(g_current_state, g_current_regime);
        
        // Journey-based reward shaping for previous action
        if(g_has_position && g_journey_shaper != NULL) {
            double raw_reward = CalculateCurrentPositionReward();
            double shaped_reward = g_journey_shaper.ShapeReward(raw_reward, 
                                                               g_current_state.equity_curve_slope,
                                                               g_position.entry_state.equity_curve_slope,
                                                               g_journey_trade_count);
            
            // Update RL agent with shaped reward
            g_agent->UpdateQ(g_position.entry_state, g_position.direction, shaped_reward, g_current_state);
        }
        
        // Execute trading action if conditions met
        if(action != ACTION_HOLD) {
            double position_size = journey_adjusted_position * InpOmegaPositionMultiplier;
            
            if(ValidateTradeConditions(action, position_size, current_omega)) {
                ExecuteTradeAction(action, position_size, current_omega);
            }
        }
    }
    
    // === PERFORMANCE MONITORING ===
    
    if(g_monitor != NULL) {
        g_monitor->UpdateRealTimeMetrics(g_current_state, current_omega, 
                                        g_cumulative_journey_score);
    }
    
    // === SHADOW MANAGEMENT WITH OMEGA ===
    
    if(g_shadows != NULL) {
        g_shadows->UpdateShadowStrategies(g_current_state, current_omega);
        
        // Check for shadow promotion based on Omega performance
        double best_shadow_omega = g_shadows->GetBestShadowOmega();
        if(best_shadow_omega > current_omega + InpShadowSwitchThreshold) {
            if(g_shadows->PromoteBestShadow()) {
                CLogger::Info("Shadow promoted based on superior Omega ratio");
                
                // Reset journey tracking for new strategy
                if(g_journey_shaper != NULL) {
                    g_journey_shaper.ResetJourneyTracking();
                    g_cumulative_journey_score = 0.0;
                    g_journey_trade_count = 0;
                }
            }
        }
    }
    
    // === PERSISTENCE AND RECOVERY ===
    
    g_persistence_tick_counter++;
    if(g_persistence_tick_counter >= 100) { // Every 100 ticks
        if(g_persistence != NULL) {
            SaveEnhancedSystemState();
        }
        g_persistence_tick_counter = 0;
    }
    
    // Update journey tracking
    UpdateJourneyTracking(current_omega);
'''
        
        # Replace OnTick content
        content = content[:start_pos+1] + enhanced_ontick + content[ontick_end:]
        
        return content
    
    def _add_self_healing_calls(self, content: str) -> str:
        """Add self-healing system calls throughout the EA"""
        
        # Add healing to OnTimer function
        timer_enhancement = '''
    // Enhanced timer with self-healing and async processing
    if(g_self_healing != NULL) {
        bool healing_applied = g_self_healing.MonitorAndHeal();
        if(healing_applied) {
            CLogger::Info("TIMER", "Self-healing actions applied");
        }
    }
    
    // Process async operations
    if(g_async_manager != NULL) {
        g_async_manager.ProcessAsyncOperations();
    }
    
'''
        
        # Find OnTimer function and enhance it
        timer_start = content.find('void OnTimer()')
        if timer_start != -1:
            timer_brace = content.find('{', timer_start)
            content = content[:timer_brace+1] + timer_enhancement + content[timer_brace+1:]
        
        return content
    
    def _update_version_info(self, content: str) -> str:
        """Update version information to reflect enhancements"""
        
        # Update version and build info
        version_replacements = [
            (r'#property version\s+"[^"]*"', '#property version   "2.000.001"'),
            (r'// Build: \d+ \| Generated: [^\n]*', 
             f'// Build: 001 | Generated: Enhanced with Journey-Omega System'),
        ]
        
        enhanced = content
        for pattern, replacement in version_replacements:
            enhanced = re.sub(pattern, replacement, enhanced)
        
        return enhanced
    
    def add_helper_functions(self, content: str) -> str:
        """Add helper functions for enhanced functionality"""
        
        helper_functions = '''
//+------------------------------------------------------------------+
//| Enhanced Helper Functions for Journey-Omega System              |
//+------------------------------------------------------------------+

bool GetRecentReturns(double& returns[], int period) {
    if(period <= 0 || period > MAX_RECENT_RETURNS) return false;
    
    ArrayResize(returns, period);
    int copied = 0;
    
    for(int i = 0; i < period && i < g_recent_returns_count; i++) {
        int index = (g_recent_return_index - i - 1 + MAX_RECENT_RETURNS) % MAX_RECENT_RETURNS;
        returns[copied++] = g_recent_returns[index];
    }
    
    ArrayResize(returns, copied);
    return copied > 0;
}

double GetMarketRegimeFactor() {
    switch(g_current_regime) {
        case REGIME_LIQUID: return 1.0;
        case REGIME_VOLATILE: return 0.8;
        case REGIME_TRENDING: return 1.2;
        case REGIME_RANGING: return 0.9;
        default: return 1.0;
    }
}

double CalculateCurrentPositionReward() {
    if(!g_has_position) return 0.0;
    
    double current_price = (g_position.direction == ACTION_BUY) ? 
                          SymbolInfoDouble(g_symbol, SYMBOL_BID) :
                          SymbolInfoDouble(g_symbol, SYMBOL_ASK);
    
    double pnl = 0.0;
    if(g_position.direction == ACTION_BUY) {
        pnl = current_price - g_position.entry_price;
    } else {
        pnl = g_position.entry_price - current_price;
    }
    
    // Normalize PnL by initial risk
    return (g_position.initial_risk > 0) ? pnl / g_position.initial_risk : 0.0;
}

bool ValidateTradeConditions(ENUM_TRADING_ACTION action, double position_size, double omega_ratio) {
    // Enhanced trade validation with journey considerations
    if(position_size <= 0.0 || position_size > 0.5) return false;
    
    // Omega-based validation
    if(omega_ratio < 0.5) {
        CLogger::Warn("Trade validation failed: Low Omega ratio " + DoubleToString(omega_ratio, 3));
        return false;
    }
    
    // Journey quality check
    if(g_journey_shaper != NULL) {
        double journey_quality = g_journey_shaper.GetCurrentJourneyScore();
        if(journey_quality < -0.5) {
            CLogger::Warn("Trade validation failed: Poor journey quality " + DoubleToString(journey_quality, 3));
            return false;
        }
    }
    
    return true;
}

void ExecuteTradeAction(ENUM_TRADING_ACTION action, double position_size, double omega_ratio) {
    // Enhanced trade execution with journey tracking
    
    // Close existing position if any
    if(g_has_position) {
        ClosePosition("New signal");
    }
    
    // Calculate position size in lots
    double lot_size = CalculateLotSize(position_size);
    
    // Record journey state before trade
    if(g_journey_shaper != NULL) {
        g_journey_shaper.RecordPreTradeState(omega_ratio, g_cumulative_journey_score);
    }
    
    // Execute the trade
    bool trade_result = false;
    if(action == ACTION_BUY) {
        trade_result = OpenBuyPosition(lot_size, omega_ratio);
    } else if(action == ACTION_SELL) {
        trade_result = OpenSellPosition(lot_size, omega_ratio);
    }
    
    // Update journey tracking
    if(trade_result) {
        g_journey_trade_count++;
        UpdateJourneyTracking(omega_ratio);
        CLogger::Info("TRADE", StringFormat("Executed %s with Omega %.3f, Journey Score %.3f", 
                     EnumToString(action), omega_ratio, g_cumulative_journey_score));
    }
}

void UpdateJourneyTracking(double omega_ratio) {
    if(!g_journey_initialized || g_journey_shaper == NULL) return;
    
    // Update journey history
    int history_size = ArraySize(g_journey_history);
    if(history_size > 0) {
        // Shift array and add new value
        for(int i = history_size - 1; i > 0; i--) {
            g_journey_history[i] = g_journey_history[i-1];
        }
        g_journey_history[0] = omega_ratio;
    }
    
    // Update cumulative journey metrics
    g_cumulative_journey_score = g_journey_shaper.GetCurrentJourneyScore();
    g_path_volatility = g_journey_shaper.GetPathVolatility();
}

void SaveEnhancedSystemState() {
    if(g_persistence == NULL) return;
    
    // Save journey state
    g_persistence.SaveDouble("CumulativeJourneyScore", g_cumulative_journey_score);
    g_persistence.SaveDouble("PathVolatility", g_path_volatility);
    g_persistence.SaveInteger("JourneyTradeCount", g_journey_trade_count);
    
    // Save journey history
    for(int i = 0; i < ArraySize(g_journey_history); i++) {
        g_persistence.SaveDouble("JourneyHistory_" + IntegerToString(i), g_journey_history[i]);
    }
    
    CLogger::Verbose("PERSISTENCE", "Enhanced system state saved");
}
'''
        
        # Add helper functions before the last closing brace
        last_brace = content.rfind('}')
        if last_brace != -1:
            content = content[:last_brace] + helper_functions + '\n' + content[last_brace:]
        
        return content

def main():
    """Update the main EA with all enhancements"""
    print("🔧 Starting Enhanced Main EA Update...")
    
    updater = EnhancedMainEAUpdater()
    
    try:
        success = updater.update_main_ea()
        
        if success:
            print("✅ ProjectQuantum Main EA successfully updated with all enhancements!")
            print("🎯 Enhanced features:")
            print("   • Omega ratio replaces Kelly criterion")
            print("   • Journey-based reward shaping with asymmetric penalties")
            print("   • Self-healing system integration")
            print("   • Advanced physics normalization")
            print("   • Async operation support")
            print("   • Market-agnostic design patterns")
            
            return True
        else:
            print("❌ Failed to update Main EA")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)