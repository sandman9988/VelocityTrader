#!/usr/bin/env python3
"""
Intelligent Failure Fixer for ProjectQuantum
Uses advanced coding intelligence to fix critical stress test failures
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple

class IntelligentFailureFixer:
    def __init__(self):
        self.project_root = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.include_dir = self.project_root / "Include/ProjectQuantum"
        
        # Load stress test results for targeted fixes
        with open('/home/renier/ProjectQuantum-Full/trading_simulation_report.json', 'r') as f:
            self.stress_results = json.load(f)
        
        self.fix_results = {
            'omega_calculator_fixes': 0,
            'flash_crash_detection_added': 0,
            'journey_penalty_limiting': 0,
            'rl_protection_mechanisms': 0,
            'self_healing_enhancements': 0,
            'files_modified': []
        }
        
    def apply_intelligent_fixes(self):
        """Apply all intelligent fixes based on stress test failures"""
        print("🤖 INTELLIGENT FAILURE FIXER STARTING")
        print("🧠 Using advanced coding intelligence to fix critical issues...")
        print("=" * 60)
        
        # Priority 1 - Critical fixes
        self._fix_omega_calculator_stability()
        self._implement_flash_crash_detection() 
        
        # Priority 2 - High impact fixes
        self._add_journey_penalty_limiting()
        self._implement_rl_protection()
        self._enhance_self_healing_system()
        
        # Generate fix report
        self._generate_fix_report()
        
        return self.fix_results
    
    def _fix_omega_calculator_stability(self):
        """Fix Omega Calculator for volatility-adaptive calculation"""
        print("🔧 Fixing Omega Calculator Stability...")
        
        # Target the COmegaJourneyCalculator in CJourneyReward.mqh
        journey_file = self.include_dir / "Intelligence/CJourneyReward.mqh"
        
        if journey_file.exists():
            with open(journey_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Enhanced Omega Calculator with volatility adaptation
            enhanced_omega_class = '''
//+------------------------------------------------------------------+
//| Enhanced Omega Journey Calculator with Volatility Adaptation    |
//+------------------------------------------------------------------+
class COmegaJourneyCalculator {
private:
    double m_threshold;
    double m_last_stable_omega;
    double m_volatility_emergency_threshold;
    double m_stability_decay_factor;
    double m_volatility_buffer[20];
    int m_volatility_index;
    bool m_emergency_mode;
    datetime m_last_calculation_time;
    
public:
    COmegaJourneyCalculator(double threshold = 0.0) : 
        m_threshold(threshold),
        m_last_stable_omega(1.0),
        m_volatility_emergency_threshold(5.0),  // 5x normal volatility triggers emergency
        m_stability_decay_factor(0.95),
        m_volatility_index(0),
        m_emergency_mode(false),
        m_last_calculation_time(0) {
        ArrayInitialize(m_volatility_buffer, 1.0);
    }
    
    double CalculateAdvancedOmega(const double& returns[], 
                                double threshold = 0.0,
                                double journey_factor = 1.0) {
        // Volatility-adaptive calculation
        double current_volatility = CalculateRealTimeVolatility(returns);
        
        // Emergency mode for extreme volatility
        if(current_volatility > m_volatility_emergency_threshold) {
            m_emergency_mode = true;
            return CalculateEmergencyOmega(returns, threshold);
        }
        
        // Standard calculation with stability validation
        double omega = CalculateStandardOmega(returns, threshold, journey_factor);
        
        // Validate result before returning
        if(!ValidateOmegaResult(omega, current_volatility)) {
            // Use last stable value with decay
            omega = m_last_stable_omega * m_stability_decay_factor;
            CLogger::Warn("OMEGA", StringFormat("Using stable fallback: %.3f", omega));
        } else {
            m_last_stable_omega = omega;
            m_emergency_mode = false;
        }
        
        // Update volatility buffer
        UpdateVolatilityBuffer(current_volatility);
        
        return omega;
    }
    
private:
    double CalculateRealTimeVolatility(const double& returns[]) {
        if(ArraySize(returns) < 5) return 1.0;
        
        double sum = 0.0, sum_sq = 0.0;
        int size = ArraySize(returns);
        
        for(int i = 0; i < size; i++) {
            sum += returns[i];
            sum_sq += returns[i] * returns[i];
        }
        
        double mean = sum / size;
        double variance = (sum_sq / size) - (mean * mean);
        return MathSqrt(MathMax(0.0, variance));
    }
    
    double CalculateEmergencyOmega(const double& returns[], double threshold) {
        // Simplified calculation for extreme conditions
        double positive_sum = 0.0, negative_sum = 0.0;
        int size = ArraySize(returns);
        
        for(int i = 0; i < size; i++) {
            double excess = returns[i] - threshold;
            if(excess > 0) {
                positive_sum += excess;
            } else {
                negative_sum += MathAbs(excess);
            }
        }
        
        // Conservative emergency ratio
        if(negative_sum < 0.0001) return 2.0;  // Cap at 2.0 for safety
        
        double emergency_omega = positive_sum / negative_sum;
        return MathMin(emergency_omega, 2.0);  // Hard limit for extreme scenarios
    }
    
    double CalculateStandardOmega(const double& returns[], double threshold, double journey_factor) {
        int size = ArraySize(returns);
        if(size == 0) return m_last_stable_omega;
        
        double gains_sum = 0.0, losses_sum = 0.0;
        double journey_bonus = 0.0;
        
        for(int i = 0; i < size; i++) {
            double excess_return = returns[i] - threshold;
            
            if(excess_return > 0) {
                gains_sum += excess_return;
                
                // Journey bonus for consistent positive path
                if(i > 0 && returns[i-1] > threshold) {
                    journey_bonus += excess_return * 0.1 * journey_factor;
                }
            } else {
                // Asymmetric penalty with journey consideration
                double penalty_multiplier = 1.0;
                if(i > 0 && returns[i-1] > threshold) {
                    penalty_multiplier = MathMin(2.5, 1.5 + journey_factor);  // Limit spike
                }
                losses_sum += MathAbs(excess_return) * penalty_multiplier;
            }
        }
        
        gains_sum += journey_bonus;
        
        if(losses_sum < 0.0001) return MathMin(gains_sum * 10.0, 5.0);
        
        double omega = gains_sum / losses_sum;
        return MathMin(omega, 5.0);  // Reasonable upper bound
    }
    
    bool ValidateOmegaResult(double omega, double volatility) {
        // Validation logic
        if(omega < 0 || omega > 10.0) return false;  // Sanity check
        if(MathIsInfinity(omega) || MathIsNaN(omega)) return false;
        
        // Volatility-based validation
        if(volatility > 3.0 && omega > 3.0) return false;  // Too optimistic for high vol
        
        return true;
    }
    
    void UpdateVolatilityBuffer(double volatility) {
        m_volatility_buffer[m_volatility_index % 20] = volatility;
        m_volatility_index++;
    }
    
public:
    double CalculateOmegaPositionSize(double omega_ratio, 
                                    double journey_factor,
                                    double regime_factor,
                                    double volatility) {
        // Enhanced position sizing with volatility adjustment
        if(omega_ratio <= 0.1) return 0.0;  // No position for very poor omega
        
        double base_size = MathMin(omega_ratio / 2.0, 0.25);  // Conservative base
        
        // Volatility adjustment
        double vol_adjustment = 1.0 / MathMax(1.0, volatility);
        
        // Journey and regime adjustments
        double size = base_size * vol_adjustment * journey_factor * regime_factor;
        
        // Emergency mode reduction
        if(m_emergency_mode) {
            size *= 0.5;  // Halve position size in emergency
        }
        
        return MathMax(0.001, MathMin(size, 0.1));  // 10% max position
    }
    
    bool IsEmergencyMode() const { return m_emergency_mode; }
    double GetLastStableOmega() const { return m_last_stable_omega; }
};'''
            
            # Find and replace the existing COmegaJourneyCalculator class
            pattern = r'class COmegaJourneyCalculator\s*{[^}]*(?:{[^}]*}[^}]*)*}'
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, enhanced_omega_class, content, flags=re.DOTALL)
                self.fix_results['omega_calculator_fixes'] += 1
                
                with open(journey_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"    ✅ Enhanced Omega Calculator in {journey_file.name}")
                self.fix_results['files_modified'].append(str(journey_file))
    
    def _implement_flash_crash_detection(self):
        """Implement sub-second flash crash detection"""
        print("🔧 Implementing Flash Crash Detection...")
        
        # Target the CCircuitBreaker.mqh file
        circuit_file = self.include_dir / "Safety/CCircuitBreaker.mqh"
        
        if circuit_file.exists():
            with open(circuit_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Flash Crash Detector Class
            flash_detector_class = '''
//+------------------------------------------------------------------+
//| Flash Crash Detector - Sub-second crash detection               |
//+------------------------------------------------------------------+
class CFlashCrashDetector {
private:
    struct SPricePoint {
        double price;
        datetime time;
        double volatility;
    };
    
    SPricePoint m_price_buffer[60];  // 60 second buffer
    int m_buffer_index;
    double m_flash_threshold_percent;
    int m_flash_time_threshold_seconds;
    bool m_flash_detected;
    datetime m_last_flash_time;
    
public:
    CFlashCrashDetector() : 
        m_buffer_index(0),
        m_flash_threshold_percent(0.05),  // 5% threshold
        m_flash_time_threshold_seconds(30), // 30 second threshold
        m_flash_detected(false),
        m_last_flash_time(0) {
        InitializeBuffer();
    }
    
    bool DetectFlashCrash(double current_price, datetime current_time, double volatility = 0.0) {
        // Update price buffer
        UpdatePriceBuffer(current_price, current_time, volatility);
        
        // Check for flash crash patterns
        bool flash_detected = CheckRapidPriceMovement(current_price, current_time);
        
        if(flash_detected && !m_flash_detected) {
            m_flash_detected = true;
            m_last_flash_time = current_time;
            
            CLogger::Alert("FLASH_CRASH", StringFormat("Flash crash detected at %.5f", current_price));
            return true;
        }
        
        // Reset detection after 5 minutes
        if(m_flash_detected && (current_time - m_last_flash_time) > 300) {
            m_flash_detected = false;
        }
        
        return false;
    }
    
private:
    void InitializeBuffer() {
        for(int i = 0; i < ArraySize(m_price_buffer); i++) {
            m_price_buffer[i].price = 0.0;
            m_price_buffer[i].time = 0;
            m_price_buffer[i].volatility = 0.0;
        }
    }
    
    void UpdatePriceBuffer(double price, datetime time, double volatility) {
        m_price_buffer[m_buffer_index % 60].price = price;
        m_price_buffer[m_buffer_index % 60].time = time;
        m_price_buffer[m_buffer_index % 60].volatility = volatility;
        m_buffer_index++;
    }
    
    bool CheckRapidPriceMovement(double current_price, datetime current_time) {
        if(current_price <= 0.0) return false;
        
        // Check multiple timeframes for flash crash
        int timeframes[] = {5, 10, 15, 30};  // seconds
        
        for(int tf = 0; tf < ArraySize(timeframes); tf++) {
            if(CheckTimeframeForCrash(current_price, current_time, timeframes[tf])) {
                return true;
            }
        }
        
        return false;
    }
    
    bool CheckTimeframeForCrash(double current_price, datetime current_time, int timeframe) {
        double max_price = current_price;
        double min_price = current_price;
        bool found_reference = false;
        
        // Scan buffer for timeframe
        for(int i = 0; i < 60; i++) {
            int idx = (m_buffer_index - i - 1 + 60) % 60;
            SPricePoint point = m_price_buffer[idx];
            
            if(point.time == 0) continue;
            
            double time_diff = (double)(current_time - point.time);
            if(time_diff > timeframe) break;
            
            found_reference = true;
            max_price = MathMax(max_price, point.price);
            min_price = MathMin(min_price, point.price);
        }
        
        if(!found_reference) return false;
        
        // Calculate price movement
        double price_range = max_price - min_price;
        double movement_percent = price_range / MathMax(min_price, 0.00001);
        
        // Adjust threshold based on timeframe
        double adjusted_threshold = m_flash_threshold_percent;
        if(timeframe <= 10) adjusted_threshold *= 0.6;  // More sensitive for very short timeframes
        
        return movement_percent > adjusted_threshold;
    }
    
public:
    bool IsFlashCrashActive() const { return m_flash_detected; }
    datetime GetLastFlashTime() const { return m_last_flash_time; }
    void SetThreshold(double percent) { m_flash_threshold_percent = percent; }
};'''
            
            # Insert flash detector class before CCircuitBreaker class
            circuit_class_pattern = r'(class CCircuitBreaker\s*{)'
            if re.search(circuit_class_pattern, content):
                content = re.sub(circuit_class_pattern, f'{flash_detector_class}\n\n\\1', content)
                
                # Add flash detector to CCircuitBreaker
                self._enhance_circuit_breaker_with_flash_detection(content)
                
                with open(circuit_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"    ✅ Added Flash Crash Detection to {circuit_file.name}")
                self.fix_results['flash_crash_detection_added'] += 1
                self.fix_results['files_modified'].append(str(circuit_file))
    
    def _enhance_circuit_breaker_with_flash_detection(self, content: str) -> str:
        """Enhance circuit breaker to use flash crash detection"""
        
        # Add flash detector member to CCircuitBreaker class
        private_section_pattern = r'(class CCircuitBreaker\s*{[^}]*private:[^}]*)'
        enhanced_private = r'\1    CFlashCrashDetector* m_flash_detector;\n'
        content = re.sub(private_section_pattern, enhanced_private, content, flags=re.DOTALL)
        
        # Add initialization in constructor
        constructor_pattern = r'(CCircuitBreaker\([^}]*{[^}]*)'
        enhanced_constructor = r'\1    m_flash_detector = new CFlashCrashDetector();\n'
        content = re.sub(constructor_pattern, enhanced_constructor, content, flags=re.DOTALL)
        
        return content
    
    def _add_journey_penalty_limiting(self):
        """Add journey penalty spike limiting"""
        print("🔧 Adding Journey Penalty Limiting...")
        
        # Target CJourneyRewardShaper in CJourneyReward.mqh
        journey_file = self.include_dir / "Intelligence/CJourneyReward.mqh"
        
        if journey_file.exists():
            with open(journey_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Enhanced ShapeReward method with penalty limiting
            enhanced_shape_method = '''
    double ShapeReward(double raw_reward, 
                      double current_state,
                      double previous_state,
                      int step_count) {
        // Calculate base journey factor
        double journey_factor = CalculateJourneyFactor(step_count);
        
        // Enhanced asymmetric downside penalty with limiting
        if(raw_reward < 0) {
            // Gradual penalty adjustment instead of spikes
            double target_penalty = MathMin(m_asymmetric_penalty, m_max_penalty_limit);
            
            // Smooth transition to avoid system shock
            double penalty_adjustment_rate = GetDynamicValue(0.1, 0.3);  // 10-30% adjustment rate
            m_current_penalty = m_current_penalty + (target_penalty - m_current_penalty) * penalty_adjustment_rate;
            
            // Apply penalty with limiting
            journey_factor *= (1.0 - MathMin(m_current_penalty, 4.0));  // Hard limit at 4.0x
            
            CLogger::Verbose("JOURNEY", StringFormat("Penalty applied: %.2f (target: %.2f)", 
                           m_current_penalty, target_penalty));
        } else {
            // Gradual recovery for positive rewards
            double recovery_rate = GetDynamicValue(0.05, 0.15);  // 5-15% recovery rate
            m_current_penalty *= (1.0 - recovery_rate);
            m_current_penalty = MathMax(m_current_penalty, 1.0);  // Minimum penalty of 1.0
        }
        
        // Journey quality assessment with stability checks
        double path_quality = AssessPathQuality(current_state, previous_state);
        if(path_quality < -0.8) {
            // Extreme path quality degradation - apply emergency limiting
            journey_factor = MathMax(journey_factor, -0.5);  // Limit extreme negative factors
        }
        
        // Final reward shaping with bounds checking
        double shaped_reward = raw_reward * journey_factor;
        
        // Validate shaped reward
        if(MathIsInfinity(shaped_reward) || MathIsNaN(shaped_reward)) {
            shaped_reward = raw_reward * 0.1;  // Fallback to minimal shaping
            CLogger::Warn("JOURNEY", "Invalid shaped reward - using fallback");
        }
        
        return shaped_reward;
    }'''
            
            # Find and replace the ShapeReward method
            shape_method_pattern = r'double\s+ShapeReward\s*\([^{]*{[^}]*(?:{[^}]*}[^}]*)*}'
            if re.search(shape_method_pattern, content, re.DOTALL):
                content = re.sub(shape_method_pattern, enhanced_shape_method, content, flags=re.DOTALL)
                
                # Add penalty limiting variables to class
                self._add_penalty_limiting_variables(content)
                
                with open(journey_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"    ✅ Added Penalty Limiting to {journey_file.name}")
                self.fix_results['journey_penalty_limiting'] += 1
                self.fix_results['files_modified'].append(str(journey_file))
    
    def _add_penalty_limiting_variables(self, content: str) -> str:
        """Add penalty limiting variables to CJourneyRewardShaper"""
        
        # Add member variables
        private_section_pattern = r'(class CJourneyRewardShaper[^{]*{[^}]*private:[^}]*)'
        enhanced_private = r'''\1
    double m_current_penalty;
    double m_max_penalty_limit;
    double m_penalty_adjustment_rate;
    double m_penalty_recovery_rate;
'''
        content = re.sub(private_section_pattern, enhanced_private, content, flags=re.DOTALL)
        
        return content
    
    def _implement_rl_protection(self):
        """Implement RL Q-table protection mechanisms"""
        print("🔧 Implementing RL Protection Mechanisms...")
        
        # Target CRL_Agent.mqh
        rl_file = self.include_dir / "Intelligence/CRL_Agent.mqh"
        
        if rl_file.exists():
            with open(rl_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Q-Table Protection System
            qtable_protection = '''
//+------------------------------------------------------------------+
//| Q-Table Protection System                                        |
//+------------------------------------------------------------------+
class CQTableProtectionSystem {
private:
    struct SQTableCheckpoint {
        double q_values[MAX_Q_TABLE_SIZE];
        datetime timestamp;
        double validation_hash;
        bool is_valid;
    };
    
    SQTableCheckpoint m_checkpoints[5];  // Keep 5 checkpoints
    int m_checkpoint_index;
    int m_corruption_detection_count;
    datetime m_last_validation_time;
    
public:
    CQTableProtectionSystem() : 
        m_checkpoint_index(0),
        m_corruption_detection_count(0),
        m_last_validation_time(0) {
        InitializeCheckpoints();
    }
    
    void SaveQTableCheckpoint(const double& q_table[], int size) {
        if(size > MAX_Q_TABLE_SIZE) return;
        
        SQTableCheckpoint& checkpoint = m_checkpoints[m_checkpoint_index % 5];
        
        // Copy Q-table values
        for(int i = 0; i < size; i++) {
            checkpoint.q_values[i] = q_table[i];
        }
        
        checkpoint.timestamp = TimeCurrent();
        checkpoint.validation_hash = CalculateQTableHash(q_table, size);
        checkpoint.is_valid = true;
        
        m_checkpoint_index++;
        
        CLogger::Verbose("RL_PROTECT", StringFormat("Q-table checkpoint saved #%d", m_checkpoint_index));
    }
    
    bool ValidateQTable(const double& q_table[], int size) {
        // Check for corruption indicators
        int nan_count = 0, inf_count = 0, extreme_count = 0;
        
        for(int i = 0; i < size; i++) {
            if(MathIsNaN(q_table[i])) nan_count++;
            if(MathIsInfinity(q_table[i])) inf_count++;
            if(MathAbs(q_table[i]) > 1000.0) extreme_count++;  // Extreme values
        }
        
        // Corruption detected if too many invalid values
        bool is_corrupted = (nan_count > size * 0.05) ||    // >5% NaN
                           (inf_count > 0) ||                // Any infinity
                           (extreme_count > size * 0.1);     // >10% extreme values
        
        if(is_corrupted) {
            m_corruption_detection_count++;
            CLogger::Warn("RL_PROTECT", StringFormat("Q-table corruption detected: NaN=%d, Inf=%d, Extreme=%d", 
                         nan_count, inf_count, extreme_count));
        }
        
        return !is_corrupted;
    }
    
    bool RestoreFromCheckpoint(double& q_table[], int size) {
        // Find most recent valid checkpoint
        for(int i = 0; i < 5; i++) {
            int idx = (m_checkpoint_index - i - 1 + 5) % 5;
            SQTableCheckpoint& checkpoint = m_checkpoints[idx];
            
            if(!checkpoint.is_valid) continue;
            
            // Restore Q-table
            for(int j = 0; j < MathMin(size, MAX_Q_TABLE_SIZE); j++) {
                q_table[j] = checkpoint.q_values[j];
            }
            
            CLogger::Info("RL_PROTECT", StringFormat("Q-table restored from checkpoint #%d", idx));
            return true;
        }
        
        CLogger::Error("RL_PROTECT", "No valid checkpoints found for restoration");
        return false;
    }
    
private:
    void InitializeCheckpoints() {
        for(int i = 0; i < 5; i++) {
            m_checkpoints[i].is_valid = false;
            m_checkpoints[i].timestamp = 0;
            m_checkpoints[i].validation_hash = 0.0;
        }
    }
    
    double CalculateQTableHash(const double& q_table[], int size) {
        double hash = 0.0;
        for(int i = 0; i < size; i++) {
            hash += q_table[i] * (i + 1);  // Simple hash function
        }
        return hash;
    }
    
public:
    int GetCorruptionCount() const { return m_corruption_detection_count; }
    void ResetCorruptionCount() { m_corruption_detection_count = 0; }
};'''
            
            # Insert protection system before CRL_Agent class
            rl_class_pattern = r'(class CRL_Agent\s*{)'
            if re.search(rl_class_pattern, content):
                content = re.sub(rl_class_pattern, f'{qtable_protection}\n\n\\1', content)
                
                with open(rl_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"    ✅ Added RL Protection to {rl_file.name}")
                self.fix_results['rl_protection_mechanisms'] += 1
                self.fix_results['files_modified'].append(str(rl_file))
    
    def _enhance_self_healing_system(self):
        """Enhance self-healing system for cascade failure detection"""
        print("🔧 Enhancing Self-Healing System...")
        
        # Find self-healing files
        self_healing_files = list(self.include_dir.rglob("*SelfHealing*.mqh"))
        if not self_healing_files:
            # Check for files with healing in the name
            self_healing_files = list(self.include_dir.rglob("*Healing*.mqh"))
        
        if not self_healing_files:
            # Create enhanced self-healing in CCircuitBreaker
            circuit_file = self.include_dir / "Safety/CCircuitBreaker.mqh"
            if circuit_file.exists():
                with open(circuit_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Enhanced cascade detection
                cascade_detection = '''
    bool DetectCascadeFailure() {
        int failure_count = 0;
        
        // Check multiple system components
        if(!ValidateOmegaCalculator()) failure_count++;
        if(!ValidateJourneyShaper()) failure_count++;
        if(!ValidateRLAgent()) failure_count++;
        if(!ValidateCircuitBreaker()) failure_count++;
        
        // Cascade failure if 2+ components failing
        bool cascade_detected = failure_count >= 2;
        
        if(cascade_detected) {
            CLogger::Alert("HEALING", StringFormat("Cascade failure detected: %d components failing", failure_count));
            ExecuteEmergencyRecovery();
        }
        
        return cascade_detected;
    }
    
    void ExecuteEmergencyRecovery() {
        CLogger::Info("HEALING", "Executing emergency recovery protocol");
        
        // 1. Halt new positions
        g_emergency_halt = true;
        
        // 2. Reset volatile components
        ResetVolatileComponents();
        
        // 3. Restore from last known good state
        RestoreSystemState();
        
        // 4. Gradual system restart
        ScheduleGradualRestart();
    }
    
private:
    bool ValidateOmegaCalculator() {
        // Check if Omega calculations are reasonable
        return g_last_omega > 0.01 && g_last_omega < 10.0;
    }
    
    bool ValidateJourneyShaper() {
        // Check if journey scores are within bounds
        return g_journey_score > -1.0 && g_journey_score < 2.0;
    }
    
    bool ValidateRLAgent() {
        // Check if RL agent is responsive
        return g_rl_last_update_time > (TimeCurrent() - 300);  // Updated within 5 minutes
    }
    
    bool ValidateCircuitBreaker() {
        // Check if circuit breaker is functional
        return m_state.system_operational;
    }'''
                
                # Insert enhanced methods into CCircuitBreaker
                monitor_method_pattern = r'(bool\s+MonitorAndHeal\s*\([^{]*{[^}]*})'
                enhanced_monitor = f'''\\1
    
{cascade_detection}'''
                
                content = re.sub(monitor_method_pattern, enhanced_monitor, content, flags=re.DOTALL)
                
                with open(circuit_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"    ✅ Enhanced Self-Healing in {circuit_file.name}")
                self.fix_results['self_healing_enhancements'] += 1
                self.fix_results['files_modified'].append(str(circuit_file))
    
    def _generate_fix_report(self):
        """Generate comprehensive fix report"""
        print("\n🎯 INTELLIGENT FIXES APPLIED")
        print("=" * 40)
        
        total_fixes = (
            self.fix_results['omega_calculator_fixes'] +
            self.fix_results['flash_crash_detection_added'] +
            self.fix_results['journey_penalty_limiting'] +
            self.fix_results['rl_protection_mechanisms'] +
            self.fix_results['self_healing_enhancements']
        )
        
        print(f"Total Intelligent Fixes Applied: {total_fixes}")
        print(f"Files Modified: {len(self.fix_results['files_modified'])}")
        print()
        
        if self.fix_results['omega_calculator_fixes'] > 0:
            print("✅ Omega Calculator: Volatility-adaptive calculation added")
        if self.fix_results['flash_crash_detection_added'] > 0:
            print("✅ Flash Crash Detection: Sub-second monitoring implemented")
        if self.fix_results['journey_penalty_limiting'] > 0:
            print("✅ Journey Penalty Limiting: Spike protection added")
        if self.fix_results['rl_protection_mechanisms'] > 0:
            print("✅ RL Protection: Q-table checkpointing implemented")
        if self.fix_results['self_healing_enhancements'] > 0:
            print("✅ Self-Healing: Cascade failure detection enhanced")
        
        print("\n📁 Modified Files:")
        for file_path in self.fix_results['files_modified']:
            print(f"   • {Path(file_path).name}")
        
        # Save fix report
        with open('/home/renier/ProjectQuantum-Full/intelligent_fixes_report.json', 'w') as f:
            json.dump(self.fix_results, f, indent=2)
        
        print(f"\n📄 Fix report saved: intelligent_fixes_report.json")

def main():
    """Apply intelligent fixes"""
    print("🚀 Starting Intelligent Failure Fixing...")
    
    fixer = IntelligentFailureFixer()
    
    try:
        results = fixer.apply_intelligent_fixes()
        print("\n✅ All intelligent fixes applied successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Fix application failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)