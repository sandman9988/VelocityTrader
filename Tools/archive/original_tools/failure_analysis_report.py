#!/usr/bin/env python3
"""
ProjectQuantum Failure Analysis Report
Deep dive analysis of critical failure points discovered during simulation
"""

import json
from typing import Dict, List

class FailureAnalyzer:
    def __init__(self):
        with open('/home/renier/ProjectQuantum-Full/trading_simulation_report.json', 'r') as f:
            self.simulation_data = json.load(f)
        
    def analyze_critical_failures(self):
        """Analyze all critical failures and identify patterns"""
        print("🚨 PROJECTQUANTUM CRITICAL FAILURE ANALYSIS")
        print("=" * 60)
        
        failures = self.simulation_data['analysis_report']['critical_failures']
        
        print(f"Total Critical Failures: {len(failures)}")
        print("=" * 40)
        
        # Group by failure type
        failure_patterns = {}
        for failure in failures:
            scenario = failure['scenario'] 
            if scenario not in failure_patterns:
                failure_patterns[scenario] = []
            failure_patterns[scenario].append(failure)
        
        # Analyze each pattern
        for pattern, pattern_failures in failure_patterns.items():
            print(f"\n💥 {pattern.upper()} FAILURES ({len(pattern_failures)} instances)")
            print("-" * 50)
            
            if pattern == 'black_swan_monday':
                self._analyze_black_swan_failures(pattern_failures)
            elif pattern == 'flash_crash_friday':
                self._analyze_flash_crash_failures(pattern_failures)
            else:
                self._analyze_generic_failures(pattern_failures)
        
        # Generate specific code fixes
        self._generate_code_fixes()
        
    def _analyze_black_swan_failures(self, failures: List[Dict]):
        """Analyze Black Swan Monday failure patterns"""
        print("📊 Black Swan Failure Analysis:")
        
        for failure in failures:
            instrument = failure['instrument']
            details = failure['failure_details']
            
            print(f"\n🎯 {instrument}:")
            print(f"   Price Shock: {details['price_shock_percent']:.1f}%")
            print(f"   Volatility Spike: {details['volatility_multiplier']:.1f}x")
            print(f"   Duration: {details['duration_hours']:.1f} hours")
            
            # Analyze component failures
            omega_failed = not details['omega_response']['survived']
            journey_failed = not details['journey_response']['survived']
            circuit_failed = not details['circuit_breaker_response']['activated_successfully']
            
            print(f"   Component Failures:")
            if omega_failed:
                print(f"     🚨 Omega Calculator: Failed")
                print(f"        - Initial failure: {details['omega_response']['initial_omega_failure']}")
                print(f"        - Convergence time: {details['omega_response']['convergence_time']:.1f}s")
                print(f"        - Final value: {details['omega_response']['final_omega_value']:.3f}")
            
            if journey_failed:
                print(f"     🚨 Journey Shaper: Failed")
                print(f"        - Penalty spike: {details['journey_response']['asymmetric_penalty_spike']:.1f}")
                print(f"        - Score collapse: {details['journey_response']['journey_score_collapse']:.3f}")
                print(f"        - Recovery cycles: {details['journey_response']['recovery_cycles']}")
            
            if circuit_failed:
                print(f"     🚨 Circuit Breaker: Failed")
                print(f"        - Activation time: {details['circuit_breaker_response']['activation_time_ms']:.0f}ms")
                print(f"        - Lockout duration: {details['circuit_breaker_response']['lockout_duration_minutes']:.1f}min")
    
    def _analyze_flash_crash_failures(self, failures: List[Dict]):
        """Analyze Flash Crash Friday failure patterns"""
        print("📊 Flash Crash Failure Analysis:")
        
        for failure in failures:
            instrument = failure['instrument']
            details = failure['failure_details']
            
            print(f"\n🎯 {instrument}:")
            print(f"   Crash Duration: {details['crash_duration_seconds']:.0f}s")
            print(f"   Crash Magnitude: {details['crash_magnitude_percent']:.1f}%")
            print(f"   Order Book Collapse: {details['order_book_collapse']:.1%}")
            print(f"   Spread Explosion: {details['spread_explosion']:.1f}x")
            
            # Analyze response failures
            slow_circuit = details['fast_circuit_response']['response_time_seconds'] >= 5.0
            omega_unstable = not details['omega_recalibration']['stabilized']
            rl_breakdown = details['rl_confusion']['complete_breakdown']
            
            print(f"   Response Failures:")
            if slow_circuit:
                print(f"     🚨 Circuit Response: Too slow ({details['fast_circuit_response']['response_time_seconds']:.1f}s)")
                print(f"        - Detection lag: {details['fast_circuit_response']['detection_lag_ms']:.0f}ms")
                print(f"        - Missed initial move: {details['fast_circuit_response']['missed_initial_move']}")
            
            if omega_unstable:
                print(f"     🚨 Omega Calculation: Unstable")
                print(f"        - Breakdown occurred: {details['omega_recalibration']['calculation_breakdown']}")
                print(f"        - Fallback used: {details['omega_recalibration']['emergency_fallback_used']}")
                print(f"        - Recalibration time: {details['omega_recalibration']['recalibration_time']:.0f}s")
            
            if rl_breakdown:
                print(f"     🚨 RL Agent: Complete breakdown")
                print(f"        - Exploration spike: {details['rl_confusion']['exploration_spike']}")
                print(f"        - Q-value oscillation: {details['rl_confusion']['q_value_oscillation']}")
                print(f"        - Action paralysis: {details['rl_confusion']['action_paralysis']}")
    
    def _analyze_generic_failures(self, failures: List[Dict]):
        """Analyze other failure patterns"""
        print("📊 Generic Failure Analysis:")
        
        for failure in failures:
            instrument = failure['instrument']
            scenario = failure['scenario']
            details = failure['failure_details']
            
            print(f"\n🎯 {instrument} - {scenario}:")
            print(f"   System survival: {details.get('system_survival', 'Unknown')}")
            
            # Print available failure details
            for key, value in details.items():
                if 'failure' in key.lower() or 'error' in key.lower():
                    print(f"   {key}: {value}")
    
    def _generate_code_fixes(self):
        """Generate specific code fixes for identified issues"""
        print("\n🔧 RECOMMENDED CODE FIXES")
        print("=" * 40)
        
        fixes = [
            {
                'component': 'Omega Calculator',
                'issue': 'Fails during extreme volatility spikes',
                'fix': 'Implement volatility-adaptive Omega calculation with emergency fallback',
                'code_location': 'COmegaJourneyCalculator::CalculateAdvancedOmega',
                'priority': 'CRITICAL'
            },
            {
                'component': 'Journey Reward Shaper', 
                'issue': 'Asymmetric penalty spikes causing system instability',
                'fix': 'Add penalty spike limiting and gradual recovery mechanism',
                'code_location': 'CJourneyRewardShaper::ShapeReward',
                'priority': 'HIGH'
            },
            {
                'component': 'Circuit Breaker',
                'issue': 'Response time too slow for flash crashes (<60s)',
                'fix': 'Implement sub-second price movement detection',
                'code_location': 'CCircuitBreaker::MonitorAndHeal',
                'priority': 'CRITICAL'
            },
            {
                'component': 'RL Agent',
                'issue': 'Q-table corruption during extreme market events',
                'fix': 'Add Q-table checkpointing and rollback mechanisms',
                'code_location': 'CRL_Agent::UpdateQ',
                'priority': 'HIGH'
            },
            {
                'component': 'Self-Healing System',
                'issue': 'Insufficient activation during multi-component failures',
                'fix': 'Enhance cascade failure detection and recovery',
                'code_location': 'CSelfHealingManager::MonitorAndHeal',
                'priority': 'HIGH'
            }
        ]
        
        for i, fix in enumerate(fixes, 1):
            print(f"\n{i}. {fix['component']} ({fix['priority']})")
            print(f"   Issue: {fix['issue']}")
            print(f"   Fix: {fix['fix']}")
            print(f"   Location: {fix['code_location']}")
        
        # Generate implementation suggestions
        self._generate_implementation_suggestions()
    
    def _generate_implementation_suggestions(self):
        """Generate specific implementation suggestions"""
        print("\n💡 IMPLEMENTATION SUGGESTIONS")
        print("=" * 40)
        
        suggestions = [
            {
                'area': 'Omega Stability Enhancement',
                'implementation': '''
// In COmegaJourneyCalculator
double CalculateAdvancedOmega(const double& returns[], double threshold = 0.0, double journey_factor = 1.0) {
    // Add volatility detection
    double volatility = CalculateVolatility(returns);
    
    // Emergency mode for extreme volatility
    if(volatility > m_volatility_emergency_threshold) {
        return CalculateEmergencyOmega(returns, threshold);
    }
    
    // Existing calculation with stability checks
    double omega = // ... existing logic
    
    // Validate result before returning
    if(!ValidateOmegaResult(omega, volatility)) {
        return m_last_stable_omega * m_stability_decay_factor;
    }
    
    m_last_stable_omega = omega;
    return omega;
}'''
            },
            {
                'area': 'Flash Crash Detection',
                'implementation': '''
// In CCircuitBreaker
class CFlashCrashDetector {
private:
    double m_price_buffer[FLASH_DETECTION_BUFFER_SIZE];
    datetime m_time_buffer[FLASH_DETECTION_BUFFER_SIZE];
    int m_buffer_index;
    
public:
    bool DetectFlashCrash(double current_price, datetime current_time) {
        UpdateBuffers(current_price, current_time);
        
        // Check for >5% move in <30 seconds
        for(int i = 1; i < FLASH_DETECTION_BUFFER_SIZE; i++) {
            double price_change = MathAbs(current_price - m_price_buffer[i]) / m_price_buffer[i];
            double time_diff = (double)(current_time - m_time_buffer[i]);
            
            if(price_change > 0.05 && time_diff < 30) {
                return true; // Flash crash detected
            }
        }
        return false;
    }
};'''
            },
            {
                'area': 'Journey Penalty Limiting',
                'implementation': '''
// In CJourneyRewardShaper
double ShapeReward(double raw_reward, double current_state, double previous_state, int step_count) {
    // Calculate base journey factor
    double journey_factor = CalculateJourneyFactor(step_count);
    
    // Asymmetric downside penalty with limiting
    if(raw_reward < 0) {
        double penalty_multiplier = MathMin(m_asymmetric_penalty, m_max_penalty_limit);
        
        // Gradual penalty increase instead of spike
        double current_penalty = m_current_penalty;
        double target_penalty = penalty_multiplier;
        
        // Smooth transition to avoid system shock
        m_current_penalty = current_penalty + (target_penalty - current_penalty) * m_penalty_adjustment_rate;
        
        journey_factor *= (1.0 - m_current_penalty);
    } else {
        // Gradual recovery for positive rewards
        m_current_penalty *= m_penalty_recovery_rate;
    }
    
    return raw_reward * journey_factor;
}'''
            }
        ]
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion['area']}:")
            print(suggestion['implementation'])

def main():
    """Run failure analysis"""
    print("🔍 Starting ProjectQuantum Failure Analysis...")
    
    analyzer = FailureAnalyzer()
    
    try:
        analyzer.analyze_critical_failures()
        print("\n✅ Failure analysis completed!")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)