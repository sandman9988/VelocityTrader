#!/usr/bin/env python3
"""
ProjectQuantum Unified Code Enhancer
Consolidated code enhancement and improvement functionality

Combines:
- advanced_enhancement_engine.py
- enhanced_main_ea_updater.py
- error_handling_enhancer.py
- infrastructure_enhancer.py
- intelligent_code_generator.py

Author: Renier De Jager
Version: 1.216
"""

import os
import re
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Set


class OmegaReplacementEngine:
    """Replaces Sortino/Kelly calculations with advanced Omega ratio"""
    
    def __init__(self):
        self.omega_config = {
            'threshold': 0.0,  # Minimum acceptable return threshold
            'journey_weight': 0.7,  # Weight for journey vs destination
            'asymmetric_penalty': 2.5,  # Downside penalty multiplier
            'path_dependence': True,  # Consider path taken to reach result
            'volatility_normalization': True  # Normalize for volatility
        }
    
    def replace_sortino_kelly_with_omega(self, content: str) -> str:
        """Replace Sortino and Kelly calculations with advanced Omega ratio"""
        
        # Replace Sortino ratio calculations
        sortino_patterns = [
            (r'Sortino\s*=\s*[^;]+;', self._generate_omega_calculation),
            (r'sortino_ratio\s*=\s*[^;]+;', self._generate_omega_calculation),
            (r'CalculateSortino\([^)]*\)', 'CalculateOmega($1)'),
            (r'SortinoRatio\([^)]*\)', 'OmegaRatio($1)'),
        ]
        
        # Replace Kelly criterion calculations  
        kelly_patterns = [
            (r'Kelly\s*=\s*[^;]+;', self._generate_omega_position_sizing),
            (r'kelly_fraction\s*=\s*[^;]+;', self._generate_omega_position_sizing),
            (r'CalculateKelly\([^)]*\)', 'CalculateOmegaPosition($1)'),
            (r'KellyFraction\([^)]*\)', 'OmegaPositionSize($1)'),
        ]
        
        enhanced_content = content
        
        # Apply Sortino replacements
        for pattern, replacement in sortino_patterns:
            if callable(replacement):
                enhanced_content = re.sub(pattern, replacement(), enhanced_content)
            else:
                enhanced_content = re.sub(pattern, replacement, enhanced_content)
        
        # Apply Kelly replacements
        for pattern, replacement in kelly_patterns:
            if callable(replacement):
                enhanced_content = re.sub(pattern, replacement(), enhanced_content)
            else:
                enhanced_content = re.sub(pattern, replacement, enhanced_content)
        
        return enhanced_content
    
    def _generate_omega_calculation(self) -> str:
        """Generate advanced Omega ratio calculation"""
        return '''
        // Advanced Omega Ratio Calculation with Journey Shaping
        double omega_threshold = {threshold};
        double journey_weight = {journey_weight};
        double asymmetric_penalty = {asymmetric_penalty};
        
        double returns_above_threshold = 0.0;
        double returns_below_threshold = 0.0;
        
        for(int i = 0; i < returns_array_size; i++) {{
            double return_value = returns_array[i];
            if(return_value > omega_threshold) {{
                returns_above_threshold += (return_value - omega_threshold);
            }} else {{
                returns_below_threshold += (omega_threshold - return_value) * asymmetric_penalty;
            }}
        }}
        
        double omega_ratio = (returns_below_threshold > 0) ? 
            (returns_above_threshold / returns_below_threshold) : 
            (returns_above_threshold > 0 ? 10.0 : 1.0);
        
        // Journey-based adjustment
        double journey_consistency = CalculateJourneyConsistency();
        omega_ratio = omega_ratio * (1.0 + journey_weight * journey_consistency);
        '''.format(**self.omega_config)
    
    def _generate_omega_position_sizing(self) -> str:
        """Generate Omega-based position sizing"""
        return '''
        // Omega-Based Position Sizing with Dynamic Adjustment
        double omega_ratio = CalculateOmegaRatio();
        double base_position_size = (omega_ratio - 1.0) / omega_ratio;
        
        // Dynamic volatility adjustment
        double volatility_multiplier = 1.0;
        if({volatility_normalization}) {{
            double current_volatility = CalculateVolatility();
            double baseline_volatility = 0.15; // 15% baseline
            volatility_multiplier = MathSqrt(baseline_volatility / MathMax(current_volatility, 0.01));
        }}
        
        // Journey-based position adjustment
        double journey_score = GetCurrentJourneyScore();
        double journey_multiplier = 1.0 + ({journey_weight} * journey_score);
        
        double final_position_size = base_position_size * volatility_multiplier * journey_multiplier;
        final_position_size = MathMax(0.01, MathMin(final_position_size, 0.25)); // Cap at 1-25%
        '''.format(**self.omega_config)


class JourneyShapingEngine:
    """Implements journey-based reward shaping"""
    
    def implement_journey_reward_shaping(self, content: str, file_path: str) -> str:
        """Add journey-based reward shaping to MQL5 content"""
        
        # Skip if journey shaping already exists
        if 'Journey' in content and 'reward' in content.lower():
            return content
        
        # Identify the file type and apply appropriate enhancements
        if 'Intelligence' in file_path or 'RL_' in file_path:
            return self._add_rl_journey_shaping(content)
        elif 'Risk' in file_path:
            return self._add_risk_journey_shaping(content)
        elif 'Physics' in file_path:
            return self._add_physics_journey_shaping(content)
        else:
            return self._add_generic_journey_shaping(content)
    
    def _add_rl_journey_shaping(self, content: str) -> str:
        """Add RL-specific journey shaping"""
        journey_shaping_code = '''
        
        //+------------------------------------------------------------------+
        //| Journey-Based Reward Shaping for Reinforcement Learning        |
        //+------------------------------------------------------------------+
        class CJourneyRewardShaper {
        private:
            double m_journey_history[100];
            int m_history_index;
            double m_consistency_weight;
            double m_path_penalty;
            
        public:
            CJourneyRewardShaper() : 
                m_history_index(0),
                m_consistency_weight(0.7),
                m_path_penalty(2.5) {
                ArrayInitialize(m_journey_history, 0.0);
            }
            
            double ShapeReward(double base_reward, double current_state, double previous_state) {
                // Calculate path consistency
                double path_consistency = CalculatePathConsistency(current_state, previous_state);
                
                // Journey momentum factor
                double momentum = CalculateJourneyMomentum();
                
                // Asymmetric penalty for negative paths
                double path_factor = (base_reward >= 0) ? 
                    1.0 + (m_consistency_weight * path_consistency) :
                    1.0 - (m_path_penalty * MathAbs(path_consistency));
                
                // Store in journey history
                m_journey_history[m_history_index % 100] = base_reward * path_factor;
                m_history_index++;
                
                return base_reward * path_factor * (1.0 + momentum * 0.1);
            }
            
            double CalculatePathConsistency(double current, double previous) {
                double direction_consistency = 0.0;
                int lookback = MathMin(m_history_index, 20);
                
                for(int i = 1; i < lookback; i++) {
                    int idx1 = (m_history_index - i) % 100;
                    int idx2 = (m_history_index - i - 1) % 100;
                    
                    if(m_journey_history[idx1] * m_journey_history[idx2] > 0) {
                        direction_consistency += 0.05; // 5% per consistent step
                    }
                }
                
                return MathMax(-1.0, MathMin(1.0, direction_consistency));
            }
            
            double CalculateJourneyMomentum() {
                if(m_history_index < 5) return 0.0;
                
                double recent_sum = 0.0;
                for(int i = 0; i < 5; i++) {
                    recent_sum += m_journey_history[(m_history_index - 1 - i) % 100];
                }
                
                return MathTanh(recent_sum / 5.0); // Normalize momentum
            }
        };
        '''
        
        # Insert before class definitions or at end if no class found
        class_pos = content.find('class C')
        if class_pos != -1:
            return content[:class_pos] + journey_shaping_code + '\n' + content[class_pos:]
        else:
            return content + journey_shaping_code
    
    def _add_risk_journey_shaping(self, content: str) -> str:
        """Add risk-specific journey shaping"""
        return content + '''
        
        //+------------------------------------------------------------------+
        //| Risk-Aware Journey Shaping                                      |
        //+------------------------------------------------------------------+
        double CalculateRiskAdjustedJourneyScore() {
            double base_score = GetCurrentJourneyScore();
            double volatility_penalty = CalculateVolatilityPenalty();
            double drawdown_penalty = CalculateDrawdownPenalty();
            
            return base_score * (1.0 - volatility_penalty) * (1.0 - drawdown_penalty);
        }
        
        double CalculateVolatilityPenalty() {
            double current_vol = CalculateRecentVolatility(20);
            double baseline_vol = 0.15; // 15% baseline
            return MathMax(0.0, (current_vol - baseline_vol) / baseline_vol);
        }
        
        double CalculateDrawdownPenalty() {
            double max_dd = GetMaxDrawdownPercent();
            return MathMax(0.0, MathMin(0.8, max_dd / 20.0)); // Cap at 80% penalty
        }
        '''
    
    def _add_physics_journey_shaping(self, content: str) -> str:
        """Add physics-specific journey shaping"""
        return content + '''
        
        //+------------------------------------------------------------------+
        //| Physics-Based Journey Dynamics                                  |
        //+------------------------------------------------------------------+
        double CalculatePhysicsJourneyForce() {
            double momentum = CalculateMarketMomentum();
            double friction = CalculateMarketFriction();
            double gravity = CalculateMarketGravity();
            
            return momentum - friction - gravity;
        }
        
        double CalculateMarketMomentum() {
            // Price momentum with volume confirmation
            double price_momentum = (Close[0] - Close[20]) / Close[20];
            double volume_factor = Volume[0] / Average(Volume, 20);
            return price_momentum * MathMin(volume_factor, 2.0);
        }
        
        double CalculateMarketFriction() {
            // Spread and slippage costs
            double spread_cost = (Ask - Bid) / ((Ask + Bid) / 2.0);
            double liquidity_friction = 1.0 / MathMax(Volume[0], 1);
            return spread_cost + liquidity_friction * 0.001;
        }
        
        double CalculateMarketGravity() {
            // Mean reversion force
            double deviation_from_mean = (Close[0] - SimpleMA(20)) / SimpleMA(20);
            return MathAbs(deviation_from_mean) * 0.1; // 10% gravity coefficient
        }
        '''
    
    def _add_generic_journey_shaping(self, content: str) -> str:
        """Add generic journey shaping"""
        return content + '''
        
        //+------------------------------------------------------------------+
        //| Generic Journey Tracking                                        |
        //+------------------------------------------------------------------+
        double g_journey_score = 0.0;
        datetime g_last_journey_update = 0;
        
        void UpdateJourneyScore(double performance_delta) {
            double time_weight = 1.0 / MathMax(1, (TimeCurrent() - g_last_journey_update) / 3600); // Hour decay
            g_journey_score = g_journey_score * 0.95 + performance_delta * time_weight;
            g_last_journey_update = TimeCurrent();
        }
        
        double GetCurrentJourneyScore() {
            return MathTanh(g_journey_score); // Normalized between -1 and 1
        }
        '''


class ErrorHandlingEnhancer:
    """Enhances error handling throughout the codebase"""
    
    def assess_error_handling(self, content: str) -> Dict[str, Any]:
        """Assess current error handling in content"""
        assessment = {
            'has_try_catch': 'try' in content and 'catch' in content,
            'has_getlasterror': 'GetLastError()' in content,
            'has_null_checks': 'NULL' in content and '!=' in content,
            'has_array_bounds': 'ArraySize(' in content,
            'has_validation': any(pattern in content for pattern in ['Validate', 'Check', 'IsValid']),
            'has_logging_errors': any(pattern in content for pattern in ['LOG_ERROR', 'CLogger::Error']),
            'error_handling_patterns': 0
        }
        
        # Count error handling patterns
        patterns = [
            assessment['has_try_catch'],
            assessment['has_getlasterror'], 
            assessment['has_null_checks'],
            assessment['has_array_bounds'],
            assessment['has_validation'],
            assessment['has_logging_errors']
        ]
        
        assessment['error_handling_patterns'] = sum(patterns)
        assessment['has_error_handling'] = assessment['error_handling_patterns'] >= 2
        assessment['error_handling_score'] = (assessment['error_handling_patterns'] / 6) * 100
        
        return assessment
    
    def add_error_handling(self, content: str, file_path: str) -> str:
        """Add comprehensive error handling to content"""
        
        assessment = self.assess_error_handling(content)
        
        # Skip if already has good error handling
        if assessment['error_handling_score'] >= 75:
            return content
        
        enhanced_content = content
        
        # Add null pointer checks
        if not assessment['has_null_checks']:
            enhanced_content = self._add_null_checks(enhanced_content)
        
        # Add array bounds checking
        if not assessment['has_array_bounds']:
            enhanced_content = self._add_array_bounds_checks(enhanced_content)
        
        # Add validation functions
        if not assessment['has_validation']:
            enhanced_content = self._add_validation_functions(enhanced_content)
        
        # Add error logging
        if not assessment['has_logging_errors']:
            enhanced_content = self._add_error_logging(enhanced_content)
        
        return enhanced_content
    
    def _add_null_checks(self, content: str) -> str:
        """Add null pointer checks"""
        null_check_template = '''
        //+------------------------------------------------------------------+
        //| Enhanced Null Safety Checks                                     |
        //+------------------------------------------------------------------+
        template<typename T>
        bool IsValidPointer(T* ptr) {
            return (ptr != NULL && CheckPointer(ptr) == POINTER_VALID);
        }
        
        #define SAFE_DELETE(ptr) if(IsValidPointer(ptr)) { delete ptr; ptr = NULL; }
        #define SAFE_CALL(ptr, method) if(IsValidPointer(ptr)) ptr.method
        '''
        
        return null_check_template + '\n' + content
    
    def _add_array_bounds_checks(self, content: str) -> str:
        """Add array bounds checking"""
        bounds_check_template = '''
        //+------------------------------------------------------------------+
        //| Array Bounds Safety                                             |
        //+------------------------------------------------------------------+
        template<typename T>
        bool IsValidArrayIndex(T& array[], int index) {
            return (index >= 0 && index < ArraySize(array));
        }
        
        template<typename T>
        T SafeArrayGet(T& array[], int index, T default_value = 0) {
            return IsValidArrayIndex(array, index) ? array[index] : default_value;
        }
        '''
        
        return bounds_check_template + '\n' + content
    
    def _add_validation_functions(self, content: str) -> str:
        """Add validation functions"""
        validation_template = '''
        //+------------------------------------------------------------------+
        //| Input Validation Framework                                      |
        //+------------------------------------------------------------------+
        bool ValidatePrice(double price) {
            return (price > 0.0 && price < 100000.0 && !MathIsInf(price) && !MathIsNaN(price));
        }
        
        bool ValidateVolume(double volume) {
            return (volume > 0.0 && volume <= MarketInfo(Symbol(), MODE_MAXLOT));
        }
        
        bool ValidateTimeframe(int timeframe) {
            return (timeframe > 0 && timeframe <= PERIOD_MN1);
        }
        
        bool ValidateRange(double value, double min_val, double max_val) {
            return (value >= min_val && value <= max_val && !MathIsInf(value) && !MathIsNaN(value));
        }
        '''
        
        return validation_template + '\n' + content
    
    def _add_error_logging(self, content: str) -> str:
        """Add error logging capabilities"""
        logging_template = '''
        //+------------------------------------------------------------------+
        //| Enhanced Error Logging                                          |
        //+------------------------------------------------------------------+
        void LogError(string function_name, string error_message, int error_code = 0) {
            string full_message = StringFormat("[ERROR] %s: %s", function_name, error_message);
            if(error_code != 0) {
                full_message += StringFormat(" (Code: %d)", error_code);
            }
            Print(full_message);
            // TODO: Add file logging or external notification
        }
        
        void LogWarning(string function_name, string warning_message) {
            string full_message = StringFormat("[WARNING] %s: %s", function_name, warning_message);
            Print(full_message);
        }
        '''
        
        return logging_template + '\n' + content


class InfrastructureEnhancer:
    """Enhances infrastructure components"""
    
    def enhance_persistence_system(self, content: str) -> str:
        """Add intelligent persistence capabilities"""
        if 'CPersistence' not in content:
            return content
        
        enhanced_persistence = '''
        //+------------------------------------------------------------------+
        //| Intelligent Persistence Enhancement                             |
        //+------------------------------------------------------------------+
        class CIntelligentPersistence : public CPersistence {
        private:
            datetime m_last_checkpoint_time;
            double m_system_health_threshold;
            int m_checkpoint_frequency_seconds;
            
        public:
            CIntelligentPersistence() : 
                m_last_checkpoint_time(0),
                m_system_health_threshold(0.8),
                m_checkpoint_frequency_seconds(300) {} // 5 minutes
            
            bool ShouldCreateCheckpoint() {
                datetime current_time = TimeCurrent();
                double system_health = CalculateSystemHealth();
                
                // Time-based checkpointing
                if(current_time - m_last_checkpoint_time >= m_checkpoint_frequency_seconds) {
                    return true;
                }
                
                // Health-based checkpointing
                if(system_health < m_system_health_threshold) {
                    return true;
                }
                
                // Event-based checkpointing (major market events)
                if(IsVolatilitySpike() || IsNewsEvent()) {
                    return true;
                }
                
                return false;
            }
            
            double CalculateSystemHealth() {
                double omega_health = GetOmegaRatioHealth();
                double journey_health = GetJourneyScoreHealth();
                double performance_health = GetPerformanceHealth();
                
                return (omega_health + journey_health + performance_health) / 3.0;
            }
            
            bool CreateIntelligentCheckpoint(string checkpoint_name = "") {
                if(!ShouldCreateCheckpoint()) return false;
                
                if(checkpoint_name == "") {
                    checkpoint_name = StringFormat("auto_checkpoint_%s", TimeToString(TimeCurrent()));
                }
                
                bool success = SaveState(checkpoint_name);
                if(success) {
                    m_last_checkpoint_time = TimeCurrent();
                    LogInfo("CreateIntelligentCheckpoint", StringFormat("Created checkpoint: %s", checkpoint_name));
                } else {
                    LogError("CreateIntelligentCheckpoint", "Failed to create checkpoint");
                }
                
                return success;
            }
        };
        '''
        
        # Insert enhancement into the content
        class_end = content.rfind("};")
        if class_end != -1:
            return content[:class_end] + enhanced_persistence + '\n' + content[class_end:]
        else:
            return content + enhanced_persistence
    
    def add_performance_monitoring(self, content: str) -> str:
        """Add performance monitoring capabilities"""
        performance_monitor = '''
        //+------------------------------------------------------------------+
        //| Advanced Performance Monitoring                                 |
        //+------------------------------------------------------------------+
        class CPerformanceMonitor {
        private:
            struct SPerformanceMetrics {
                datetime timestamp;
                double execution_time_ms;
                double memory_usage_mb;
                double cpu_usage_percent;
                int operations_count;
                double throughput_ops_per_sec;
            };
            
            SPerformanceMetrics m_metrics_history[100];
            int m_metrics_index;
            datetime m_monitoring_start_time;
            
        public:
            CPerformanceMonitor() : 
                m_metrics_index(0),
                m_monitoring_start_time(TimeCurrent()) {
                ArrayInitialize(m_metrics_history, 0);
            }
            
            void StartMeasurement(string operation_name) {
                m_current_operation = operation_name;
                m_operation_start_time = GetMicrosecondCount();
            }
            
            void EndMeasurement() {
                ulong execution_time_us = GetMicrosecondCount() - m_operation_start_time;
                double execution_time_ms = execution_time_us / 1000.0;
                
                // Store metrics
                SPerformanceMetrics& metrics = m_metrics_history[m_metrics_index % 100];
                metrics.timestamp = TimeCurrent();
                metrics.execution_time_ms = execution_time_ms;
                metrics.memory_usage_mb = GetMemoryUsage();
                metrics.operations_count = 1;
                
                m_metrics_index++;
            }
            
            double GetAverageExecutionTime(int lookback_periods = 20) {
                double total_time = 0.0;
                int count = MathMin(lookback_periods, m_metrics_index);
                
                for(int i = 0; i < count; i++) {
                    int idx = (m_metrics_index - 1 - i) % 100;
                    total_time += m_metrics_history[idx].execution_time_ms;
                }
                
                return (count > 0) ? total_time / count : 0.0;
            }
            
            double GetThroughput() {
                int count = MathMin(10, m_metrics_index);
                if(count < 2) return 0.0;
                
                datetime start_time = m_metrics_history[(m_metrics_index - count) % 100].timestamp;
                datetime end_time = m_metrics_history[(m_metrics_index - 1) % 100].timestamp;
                
                double time_span_seconds = end_time - start_time;
                return (time_span_seconds > 0) ? count / time_span_seconds : 0.0;
            }
            
        private:
            string m_current_operation;
            ulong m_operation_start_time;
            
            double GetMemoryUsage() {
                // Placeholder - MQL5 doesn't have direct memory usage functions
                return 0.0; // Would need to implement memory tracking
            }
        };
        '''
        
        return content + performance_monitor


class UnifiedCodeEnhancer:
    """Main code enhancer combining all enhancement engines"""
    
    def __init__(self):
        self.project_root = Path("/home/renier/ProjectQuantum-Full")
        self.mt5_dev = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.include_dir = self.mt5_dev / "Include/ProjectQuantum"
        
        # Initialize enhancement engines
        self.omega_replacer = OmegaReplacementEngine()
        self.journey_shaper = JourneyShapingEngine()
        self.error_enhancer = ErrorHandlingEnhancer()
        self.infrastructure_enhancer = InfrastructureEnhancer()
        
        # Enhancement tracking
        self.enhancement_results = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.216',
            'files_processed': 0,
            'files_enhanced': 0,
            'omega_replacements': 0,
            'journey_implementations': 0,
            'error_handling_upgrades': 0,
            'infrastructure_enhancements': 0,
            'enhanced_files': [],
            'error_log': []
        }
    
    def enhance_project_comprehensive(self, 
                                    enable_omega_replacement: bool = True,
                                    enable_journey_shaping: bool = True,
                                    enable_error_handling: bool = True,
                                    enable_infrastructure: bool = True,
                                    max_files: Optional[int] = None) -> Dict[str, Any]:
        """Run comprehensive code enhancement across the project"""
        
        print("🚀 ProjectQuantum Comprehensive Code Enhancement")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Options: Omega={enable_omega_replacement}, Journey={enable_journey_shaping}")
        print(f"         ErrorHandling={enable_error_handling}, Infrastructure={enable_infrastructure}")
        if max_files:
            print(f"         Max Files: {max_files}")
        print()
        
        # Discover MQL5 files
        print("🔍 Discovering MQL5 files...")
        mqh_files = list(self.include_dir.rglob("*.mqh"))
        mq5_files = list((self.mt5_dev / "Scripts/ProjectQuantum").rglob("*.mq5"))
        mq5_files.extend(list((self.mt5_dev / "Experts").rglob("*ProjectQuantum*.mq5")))
        
        all_files = mqh_files + mq5_files
        
        # Limit files if requested
        if max_files:
            all_files = all_files[:max_files]
        
        print(f"   Found {len(mqh_files)} .mqh files")
        print(f"   Found {len(mq5_files)} .mq5 files")
        print(f"   Processing {len(all_files)} total files")
        
        # Process each file
        for file_path in all_files:
            self._enhance_single_file(
                file_path,
                enable_omega_replacement,
                enable_journey_shaping,
                enable_error_handling,
                enable_infrastructure
            )
        
        # Generate comprehensive report
        self._generate_enhancement_report()
        
        # Save detailed results
        report_path = self._save_enhancement_results()
        
        print(f"\n💾 Enhancement report saved: {report_path}")
        
        return self.enhancement_results
    
    def _enhance_single_file(self, 
                           file_path: Path,
                           enable_omega: bool,
                           enable_journey: bool, 
                           enable_error: bool,
                           enable_infrastructure: bool):
        """Enhance a single file with all enabled enhancements"""
        
        relative_path = file_path.relative_to(self.mt5_dev)
        self.enhancement_results['files_processed'] += 1
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            enhanced_content = original_content
            
            # Apply enhancements in order
            if enable_omega:
                enhanced_content = self.omega_replacer.replace_sortino_kelly_with_omega(enhanced_content)
            
            if enable_journey:
                enhanced_content = self.journey_shaper.implement_journey_reward_shaping(enhanced_content, str(relative_path))
            
            if enable_error:
                enhanced_content = self.error_enhancer.add_error_handling(enhanced_content, str(relative_path))
            
            if enable_infrastructure:
                enhanced_content = self.infrastructure_enhancer.enhance_persistence_system(enhanced_content)
                enhanced_content = self.infrastructure_enhancer.add_performance_monitoring(enhanced_content)
            
            # Check if file was actually enhanced
            if enhanced_content != original_content:
                # Write enhanced file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_content)
                
                self.enhancement_results['files_enhanced'] += 1
                self.enhancement_results['enhanced_files'].append(str(relative_path))
                
                # Count specific enhancements
                if 'Omega' in enhanced_content and 'Omega' not in original_content:
                    self.enhancement_results['omega_replacements'] += 1
                
                if 'Journey' in enhanced_content and 'Journey' not in original_content:
                    self.enhancement_results['journey_implementations'] += 1
                
                if ('ValidatePrice' in enhanced_content or 'LogError' in enhanced_content) and 'ValidatePrice' not in original_content:
                    self.enhancement_results['error_handling_upgrades'] += 1
                
                if 'CIntelligentPersistence' in enhanced_content and 'CIntelligentPersistence' not in original_content:
                    self.enhancement_results['infrastructure_enhancements'] += 1
                
                print(f"   ✅ Enhanced: {relative_path}")
            else:
                print(f"   ℹ️  No changes: {relative_path}")
        
        except Exception as e:
            error_msg = f"Error enhancing {relative_path}: {e}"
            print(f"   ❌ {error_msg}")
            self.enhancement_results['error_log'].append(error_msg)
    
    def _generate_enhancement_report(self):
        """Generate human-readable enhancement report"""
        print(f"\n" + "=" * 80)
        print("🎯 CODE ENHANCEMENT SUMMARY")
        print("=" * 80)
        
        results = self.enhancement_results
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Files Processed: {results['files_processed']}")
        print(f"   Files Enhanced: {results['files_enhanced']}")
        print(f"   Enhancement Rate: {(results['files_enhanced']/results['files_processed']*100):.1f}%")
        
        print(f"\n🔧 Enhancement Breakdown:")
        print(f"   Omega Replacements: {results['omega_replacements']}")
        print(f"   Journey Implementations: {results['journey_implementations']}")
        print(f"   Error Handling Upgrades: {results['error_handling_upgrades']}")
        print(f"   Infrastructure Enhancements: {results['infrastructure_enhancements']}")
        
        if results['error_log']:
            print(f"\n⚠️  Errors Encountered ({len(results['error_log'])}):")
            for error in results['error_log'][:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(results['error_log']) > 5:
                print(f"   • ... and {len(results['error_log']) - 5} more errors")
        
        # Success assessment
        success_rate = (results['files_enhanced'] / results['files_processed'] * 100) if results['files_processed'] > 0 else 0
        
        if success_rate >= 80:
            print(f"\n🎉 EXCELLENT! Enhancement process highly successful!")
        elif success_rate >= 60:
            print(f"\n✅ GOOD! Most files successfully enhanced.")
        elif success_rate >= 40:
            print(f"\n⚠️  PARTIAL SUCCESS: Some files enhanced, but improvements needed.")
        else:
            print(f"\n❌ LOW SUCCESS: Enhancement process needs attention.")
        
        total_enhancements = (results['omega_replacements'] + 
                            results['journey_implementations'] + 
                            results['error_handling_upgrades'] + 
                            results['infrastructure_enhancements'])
        
        print(f"\n📈 Total Enhancements Applied: {total_enhancements}")
    
    def _save_enhancement_results(self) -> Path:
        """Save detailed enhancement results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure reports directory exists
        reports_dir = self.project_root / "enhancement_reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_path = reports_dir / f"code_enhancement_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.enhancement_results, f, indent=2)
        
        return report_path
    
    def enhance_main_ea_specifically(self) -> bool:
        """Specifically enhance the main EA file"""
        main_ea_path = self.mt5_dev / "Experts/ProjectQuantum_Main.mq5"
        
        if not main_ea_path.exists():
            print(f"❌ Main EA not found at {main_ea_path}")
            return False
        
        print("🔧 Enhancing ProjectQuantum Main EA specifically...")
        
        try:
            with open(main_ea_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply comprehensive EA enhancements
            enhanced_content = self._enhance_ea_parameters(content)
            enhanced_content = self._enhance_ea_includes(enhanced_content)
            enhanced_content = self._enhance_ea_globals(enhanced_content)
            enhanced_content = self._enhance_ea_functions(enhanced_content)
            
            # Write enhanced EA
            with open(main_ea_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_content)
            
            print("   ✅ Main EA enhancement completed")
            return True
            
        except Exception as e:
            print(f"   ❌ Error enhancing Main EA: {e}")
            return False
    
    def _enhance_ea_parameters(self, content: str) -> str:
        """Enhance EA input parameters"""
        # Add Omega-based parameters
        omega_params = '''
input group "═══ OMEGA RATIO SETTINGS ═══"
input double   InpOmegaThreshold = 0.0;             // Omega Threshold (0.0 = risk-free rate)
input double   InpOmegaPositionMultiplier = 1.0;    // Omega Position Size Multiplier
input bool     InpVolatilityAdjustOmega = true;     // Adjust Omega for Volatility
input int      InpOmegaCalculationPeriod = 30;      // Period for Omega Calculation

input group "═══ JOURNEY REWARD SHAPING ═══"
input double   InpJourneyWeight = 0.7;              // Journey vs Destination Weight (0.7 = 70% journey)
input double   InpAsymmetricPenalty = 2.5;          // Downside Penalty Multiplier
input double   InpPathConsistencyBonus = 0.3;       // Consistency Reward Multiplier
input bool     InpAdaptiveJourney = true;           // Enable Adaptive Journey Shaping
input int      InpJourneyLookback = 50;             // Journey History Lookback (trades)
'''
        
        # Insert after existing input parameters
        input_end = content.rfind('input ')
        if input_end != -1:
            line_end = content.find('\n', input_end)
            next_line_end = content.find('\n', line_end + 1)
            return content[:next_line_end] + omega_params + content[next_line_end:]
        
        return content
    
    def _enhance_ea_includes(self, content: str) -> str:
        """Add enhanced system includes"""
        enhanced_includes = '''
//--- Enhanced Systems Includes
#include "..\\Include\\Intelligence\\CJourneyReward.mqh"
#include "..\\Include\\Performance\\CLearningMetrics.mqh"
#include "..\\Include\\Physics\\CPhysicsMonitor.mqh"
'''
        
        # Insert after last include
        last_include = content.rfind('#include')
        if last_include != -1:
            line_end = content.find('\n', last_include)
            return content[:line_end] + enhanced_includes + content[line_end:]
        
        return content
    
    def _enhance_ea_globals(self, content: str) -> str:
        """Add global objects for enhanced systems"""
        enhanced_globals = '''
//--- Enhanced System Objects
CJourneyRewardShaper*    g_journey_shaper = NULL;
CPerformanceMonitor*     g_performance_monitor = NULL;
CIntelligentPersistence* g_intelligent_persistence = NULL;
'''
        
        # Insert after existing global declarations
        globals_section = content.find('//--- Global Variables')
        if globals_section == -1:
            # Find first function and insert before it
            first_func = content.find('int OnInit(')
            if first_func != -1:
                return content[:first_func] + enhanced_globals + '\n' + content[first_func:]
        
        return content
    
    def _enhance_ea_functions(self, content: str) -> str:
        """Enhance EA functions with new capabilities"""
        # Enhance OnInit
        oninit_pattern = r'(int OnInit\(\)\s*\{[^}]*)'
        oninit_replacement = r'''\1
   
   // Initialize enhanced systems
   g_journey_shaper = new CJourneyRewardShaper();
   g_performance_monitor = new CPerformanceMonitor();
   g_intelligent_persistence = new CIntelligentPersistence();
   
   if(!IsValidPointer(g_journey_shaper) || 
      !IsValidPointer(g_performance_monitor) || 
      !IsValidPointer(g_intelligent_persistence)) {
      Print("ERROR: Failed to initialize enhanced systems");
      return INIT_FAILED;
   }
   
   Print("Enhanced ProjectQuantum systems initialized successfully");'''
        
        content = re.sub(oninit_pattern, oninit_replacement, content, flags=re.DOTALL)
        
        # Enhance OnDeinit
        ondeinit_pattern = r'(void OnDeinit\(const int reason\)\s*\{[^}]*)'
        ondeinit_replacement = r'''\1
   
   // Cleanup enhanced systems
   SAFE_DELETE(g_journey_shaper);
   SAFE_DELETE(g_performance_monitor);
   SAFE_DELETE(g_intelligent_persistence);
   
   Print("Enhanced ProjectQuantum systems cleaned up");'''
        
        content = re.sub(ondeinit_pattern, ondeinit_replacement, content, flags=re.DOTALL)
        
        return content


def main():
    """Main entry point for code enhancer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ProjectQuantum Unified Code Enhancer')
    parser.add_argument('--no-omega', action='store_true', help='Skip Omega ratio replacements')
    parser.add_argument('--no-journey', action='store_true', help='Skip journey shaping')
    parser.add_argument('--no-error', action='store_true', help='Skip error handling enhancements')
    parser.add_argument('--no-infrastructure', action='store_true', help='Skip infrastructure enhancements')
    parser.add_argument('--max-files', type=int, help='Maximum number of files to process')
    parser.add_argument('--main-ea-only', action='store_true', help='Enhance only the main EA file')
    
    args = parser.parse_args()
    
    enhancer = UnifiedCodeEnhancer()
    
    if args.main_ea_only:
        # Enhance only main EA
        success = enhancer.enhance_main_ea_specifically()
        return 0 if success else 1
    else:
        # Run comprehensive enhancement
        results = enhancer.enhance_project_comprehensive(
            enable_omega_replacement=not args.no_omega,
            enable_journey_shaping=not args.no_journey,
            enable_error_handling=not args.no_error,
            enable_infrastructure=not args.no_infrastructure,
            max_files=args.max_files
        )
        
        # Determine success
        success_rate = (results['files_enhanced'] / results['files_processed']) if results['files_processed'] > 0 else 0
        success = success_rate >= 0.5  # 50% threshold for success
        
        return 0 if success else 1


if __name__ == "__main__":
    exit(main())