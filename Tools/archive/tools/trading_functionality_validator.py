#!/usr/bin/env python3
"""
ProjectQuantum Trading Functionality Validator
Checks if the EA can actually trade and analyzes core trading functions
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

class TradingFunctionalityValidator:
    def __init__(self):
        self.main_ea_path = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development/Experts/ProjectQuantum_Main.mq5")
        self.analysis_results = {
            'trading_functions_found': {},
            'order_execution_capabilities': {},
            'position_management': {},
            'risk_management': {},
            'decision_making': {},
            'overall_trading_readiness': 0.0
        }
        
    def validate_trading_functionality(self):
        """Validate complete trading functionality"""
        print("💰 TRADING FUNCTIONALITY VALIDATOR")
        print("🔍 Analyzing ProjectQuantum Main EA for actual trading capabilities...")
        print("=" * 70)
        
        if not self.main_ea_path.exists():
            print("❌ Main EA file not found!")
            return False
        
        with open(self.main_ea_path, 'r', encoding='utf-8') as f:
            ea_content = f.read()
        
        # Core trading analysis
        self._analyze_trading_functions(ea_content)
        self._analyze_order_execution(ea_content)
        self._analyze_position_management(ea_content) 
        self._analyze_risk_management(ea_content)
        self._analyze_decision_making(ea_content)
        
        # Generate comprehensive report
        self._generate_trading_readiness_report()
        
        return self.analysis_results
    
    def _analyze_trading_functions(self, content: str):
        """Analyze core trading function implementations"""
        print("🔧 Analyzing Core Trading Functions...")
        
        # Essential trading functions to check
        essential_functions = [
            'OnTick',
            'OnInit', 
            'OnDeinit',
            'OnTimer',
            'ExecuteTradeAction',
            'OpenBuyPosition',
            'OpenSellPosition',
            'ClosePosition',
            'OrderSend',
            'UpdatePositionMetrics'
        ]
        
        function_results = {}
        
        for func_name in essential_functions:
            # Look for function definition
            pattern = rf'\b{func_name}\s*\('
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            found = len(matches) > 0
            function_results[func_name] = {
                'found': found,
                'occurrences': len(matches),
                'is_essential': func_name in ['OnTick', 'OnInit', 'ExecuteTradeAction', 'OrderSend']
            }
            
            status = "✅ FOUND" if found else "❌ MISSING"
            essential_marker = " (ESSENTIAL)" if function_results[func_name]['is_essential'] else ""
            print(f"   {status} {func_name}: {len(matches)} occurrences{essential_marker}")
        
        self.analysis_results['trading_functions_found'] = function_results
        
        # Calculate function completeness score
        found_essential = sum(1 for f, data in function_results.items() 
                            if data['found'] and data['is_essential'])
        total_essential = sum(1 for f, data in function_results.items() 
                            if data['is_essential'])
        
        function_score = found_essential / total_essential if total_essential > 0 else 0.0
        print(f"   📊 Core Functions Score: {function_score:.1%}")
    
    def _analyze_order_execution(self, content: str):
        """Analyze order execution capabilities"""
        print("🔧 Analyzing Order Execution...")
        
        # Order execution patterns
        execution_patterns = [
            (r'OrderSend\s*\(', 'OrderSend calls'),
            (r'MqlTradeRequest\s+request', 'Trade request structures'),
            (r'MqlTradeResult\s+result', 'Trade result handling'),
            (r'request\.action\s*=\s*TRADE_ACTION', 'Action assignment'),
            (r'request\.symbol\s*=', 'Symbol assignment'),
            (r'request\.volume\s*=', 'Volume assignment'),
            (r'request\.type\s*=\s*ORDER_TYPE', 'Order type assignment'),
            (r'request\.price\s*=', 'Price assignment'),
            (r'request\.sl\s*=', 'Stop loss assignment'),
            (r'request\.tp\s*=', 'Take profit assignment'),
            (r'result\.retcode', 'Return code checking'),
        ]
        
        execution_capabilities = {}
        
        for pattern, description in execution_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found = len(matches) > 0
            
            execution_capabilities[description] = {
                'found': found,
                'count': len(matches)
            }
            
            status = "✅ IMPLEMENTED" if found else "❌ MISSING"
            print(f"   {status} {description}: {len(matches)} instances")
        
        # Check for specific order types
        order_types = ['ORDER_TYPE_BUY', 'ORDER_TYPE_SELL', 'ORDER_TYPE_CLOSE_BY']
        order_type_support = {}
        
        for order_type in order_types:
            found = order_type in content
            order_type_support[order_type] = found
            
            status = "✅ SUPPORTED" if found else "❌ NOT FOUND"
            print(f"   {status} {order_type}")
        
        self.analysis_results['order_execution_capabilities'] = {
            'execution_patterns': execution_capabilities,
            'order_type_support': order_type_support
        }
        
        # Calculate execution readiness score
        found_patterns = sum(1 for cap in execution_capabilities.values() if cap['found'])
        total_patterns = len(execution_capabilities)
        found_types = sum(1 for supported in order_type_support.values() if supported)
        total_types = len(order_type_support)
        
        execution_score = (found_patterns / total_patterns + found_types / total_types) / 2.0
        print(f"   📊 Order Execution Score: {execution_score:.1%}")
    
    def _analyze_position_management(self, content: str):
        """Analyze position management capabilities"""
        print("🔧 Analyzing Position Management...")
        
        # Position management patterns
        position_patterns = [
            (r'PositionSelect\s*\(', 'Position selection'),
            (r'PositionsTotal\s*\(\)', 'Position counting'),
            (r'PositionGetInteger\s*\(', 'Position info retrieval'),
            (r'PositionGetDouble\s*\(', 'Position metrics'),
            (r'POSITION_TICKET', 'Position ticket access'),
            (r'POSITION_VOLUME', 'Position volume access'),
            (r'POSITION_PROFIT', 'Position profit tracking'),
            (r'POSITION_SWAP', 'Position swap tracking'),
            (r'g_has_position', 'Position state tracking'),
            (r'UpdatePositionMetrics', 'Position metrics update'),
            (r'ClosePosition', 'Position closing'),
        ]
        
        position_capabilities = {}
        
        for pattern, description in position_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found = len(matches) > 0
            
            position_capabilities[description] = {
                'found': found,
                'count': len(matches)
            }
            
            status = "✅ IMPLEMENTED" if found else "❌ MISSING"
            print(f"   {status} {description}: {len(matches)} instances")
        
        # Check for position monitoring
        monitoring_patterns = [
            'MAE',  # Maximum Adverse Excursion
            'MFE',  # Maximum Favorable Excursion
            'unrealized_pnl',
            'position_age',
            'trailing'
        ]
        
        monitoring_support = {}
        for pattern in monitoring_patterns:
            found = pattern.lower() in content.lower()
            monitoring_support[pattern] = found
            
            status = "✅ TRACKED" if found else "❌ NOT TRACKED"
            print(f"   {status} {pattern} monitoring")
        
        self.analysis_results['position_management'] = {
            'position_capabilities': position_capabilities,
            'monitoring_support': monitoring_support
        }
        
        # Calculate position management score
        found_capabilities = sum(1 for cap in position_capabilities.values() if cap['found'])
        total_capabilities = len(position_capabilities)
        found_monitoring = sum(1 for supported in monitoring_support.values() if supported)
        total_monitoring = len(monitoring_support)
        
        position_score = (found_capabilities / total_capabilities + found_monitoring / total_monitoring) / 2.0
        print(f"   📊 Position Management Score: {position_score:.1%}")
    
    def _analyze_risk_management(self, content: str):
        """Analyze risk management implementation"""
        print("🔧 Analyzing Risk Management...")
        
        # Risk management components
        risk_components = [
            (r'CVaR|cvar', 'CVaR risk measurement'),
            (r'drawdown|DD', 'Drawdown monitoring'),
            (r'stop.*loss|sl\s*=', 'Stop loss implementation'),
            (r'take.*profit|tp\s*=', 'Take profit implementation'),
            (r'position.*size|lot.*size', 'Position sizing'),
            (r'risk.*management|CRiskManager', 'Risk management system'),
            (r'circuit.*breaker|emergency', 'Emergency controls'),
            (r'max.*loss|loss.*limit', 'Loss limits'),
            (r'correlation', 'Correlation risk'),
            (r'monte.*carlo', 'Monte Carlo simulation'),
            (r'ruin.*probability', 'Ruin probability'),
            (r'omega.*ratio|InpOmegaThreshold', 'Omega ratio risk assessment'),
        ]
        
        risk_capabilities = {}
        
        for pattern, description in risk_components:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found = len(matches) > 0
            
            risk_capabilities[description] = {
                'found': found,
                'count': len(matches)
            }
            
            status = "✅ IMPLEMENTED" if found else "❌ MISSING"
            print(f"   {status} {description}: {len(matches)} references")
        
        # Check for specific risk limits
        risk_limits = [
            'InpMaxDailyDD',
            'InpMaxConsecutiveLosses',
            'InpRuinThreshold',
            'InpMaxMonteCarloRuinProb',
            'InpMaxCVaR'
        ]
        
        limit_support = {}
        for limit in risk_limits:
            found = limit in content
            limit_support[limit] = found
            
            status = "✅ CONFIGURED" if found else "❌ MISSING"
            print(f"   {status} {limit} parameter")
        
        self.analysis_results['risk_management'] = {
            'risk_capabilities': risk_capabilities,
            'limit_support': limit_support
        }
        
        # Calculate risk management score
        found_capabilities = sum(1 for cap in risk_capabilities.values() if cap['found'])
        total_capabilities = len(risk_capabilities)
        found_limits = sum(1 for supported in limit_support.values() if supported)
        total_limits = len(limit_support)
        
        risk_score = (found_capabilities / total_capabilities + found_limits / total_limits) / 2.0
        print(f"   📊 Risk Management Score: {risk_score:.1%}")
    
    def _analyze_decision_making(self, content: str):
        """Analyze decision making and signal generation"""
        print("🔧 Analyzing Decision Making...")
        
        # Decision making components
        decision_patterns = [
            (r'SelectAction|GetAction', 'Action selection'),
            (r'RL.*Agent|CRL_Agent', 'RL agent decision making'),
            (r'ENUM_TRADING_ACTION', 'Trading action enumeration'),
            (r'ACTION_BUY|ACTION_SELL|ACTION_HOLD', 'Specific trading actions'),
            (r'market.*regime|CRegimeJudge', 'Market regime detection'),
            (r'state.*vector|ConstructStateVector', 'State vector construction'),
            (r'reward|journey.*shaping', 'Reward system'),
            (r'omega.*calculator', 'Omega calculation'),
            (r'probability|confidence', 'Probability assessment'),
            (r'signal.*generation', 'Signal generation'),
            (r'entry.*condition|exit.*condition', 'Entry/exit conditions'),
        ]
        
        decision_capabilities = {}
        
        for pattern, description in decision_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found = len(matches) > 0
            
            decision_capabilities[description] = {
                'found': found,
                'count': len(matches)
            }
            
            status = "✅ IMPLEMENTED" if found else "❌ MISSING"
            print(f"   {status} {description}: {len(matches)} references")
        
        # Check for specific decision logic
        decision_logic = [
            'if.*action.*!=.*ACTION_HOLD',
            'ValidateTradeConditions',
            'CalculateCurrentPositionReward',
            'GetCurrentRegime',
            'journey_adjusted_position',
        ]
        
        logic_support = {}
        for logic in decision_logic:
            matches = re.findall(logic, content, re.IGNORECASE)
            found = len(matches) > 0
            logic_support[logic] = {
                'found': found,
                'count': len(matches)
            }
            
            status = "✅ PRESENT" if found else "❌ MISSING"
            print(f"   {status} {logic}: {len(matches)} instances")
        
        self.analysis_results['decision_making'] = {
            'decision_capabilities': decision_capabilities,
            'logic_support': logic_support
        }
        
        # Calculate decision making score
        found_capabilities = sum(1 for cap in decision_capabilities.values() if cap['found'])
        total_capabilities = len(decision_capabilities)
        found_logic = sum(1 for logic in logic_support.values() if logic['found'])
        total_logic = len(logic_support)
        
        decision_score = (found_capabilities / total_capabilities + found_logic / total_logic) / 2.0
        print(f"   📊 Decision Making Score: {decision_score:.1%}")
    
    def _generate_trading_readiness_report(self):
        """Generate comprehensive trading readiness report"""
        print("\n🎯 TRADING READINESS ASSESSMENT")
        print("=" * 50)
        
        # Calculate component scores
        function_results = self.analysis_results['trading_functions_found']
        found_essential = sum(1 for f, data in function_results.items() 
                            if data['found'] and data['is_essential'])
        total_essential = sum(1 for f, data in function_results.items() 
                            if data['is_essential'])
        function_score = found_essential / total_essential if total_essential > 0 else 0.0
        
        # Order execution score
        exec_caps = self.analysis_results['order_execution_capabilities']['execution_patterns']
        order_types = self.analysis_results['order_execution_capabilities']['order_type_support']
        found_exec = sum(1 for cap in exec_caps.values() if cap['found'])
        total_exec = len(exec_caps)
        found_types = sum(1 for supported in order_types.values() if supported)
        total_types = len(order_types)
        execution_score = (found_exec / total_exec + found_types / total_types) / 2.0
        
        # Position management score
        pos_caps = self.analysis_results['position_management']['position_capabilities']
        pos_monitoring = self.analysis_results['position_management']['monitoring_support']
        found_pos = sum(1 for cap in pos_caps.values() if cap['found'])
        total_pos = len(pos_caps)
        found_monitoring = sum(1 for supported in pos_monitoring.values() if supported)
        total_monitoring = len(pos_monitoring)
        position_score = (found_pos / total_pos + found_monitoring / total_monitoring) / 2.0
        
        # Risk management score
        risk_caps = self.analysis_results['risk_management']['risk_capabilities']
        risk_limits = self.analysis_results['risk_management']['limit_support']
        found_risk = sum(1 for cap in risk_caps.values() if cap['found'])
        total_risk = len(risk_caps)
        found_limits = sum(1 for supported in risk_limits.values() if supported)
        total_limits = len(risk_limits)
        risk_score = (found_risk / total_risk + found_limits / total_limits) / 2.0
        
        # Decision making score
        decision_caps = self.analysis_results['decision_making']['decision_capabilities']
        decision_logic = self.analysis_results['decision_making']['logic_support']
        found_decision = sum(1 for cap in decision_caps.values() if cap['found'])
        total_decision = len(decision_caps)
        found_logic = sum(1 for logic in decision_logic.values() if logic['found'])
        total_logic = len(decision_logic)
        decision_score = (found_decision / total_decision + found_logic / total_logic) / 2.0
        
        # Overall trading readiness score
        overall_score = (function_score + execution_score + position_score + risk_score + decision_score) / 5.0
        self.analysis_results['overall_trading_readiness'] = overall_score
        
        print("📊 Component Readiness Scores:")
        print(f"   🔧 Core Functions: {function_score:.1%}")
        print(f"   📤 Order Execution: {execution_score:.1%}")
        print(f"   📊 Position Management: {position_score:.1%}")
        print(f"   🛡️  Risk Management: {risk_score:.1%}")
        print(f"   🧠 Decision Making: {decision_score:.1%}")
        
        print(f"\n🎯 Overall Trading Readiness: {overall_score:.1%}")
        
        # Assessment
        if overall_score >= 0.9:
            assessment = "EXCELLENT - Fully trading ready"
            trading_status = "✅ CAN TRADE"
        elif overall_score >= 0.8:
            assessment = "GOOD - Trading ready with minor gaps"
            trading_status = "✅ CAN TRADE"
        elif overall_score >= 0.7:
            assessment = "ACCEPTABLE - Basic trading capabilities"
            trading_status = "⚠️ LIMITED TRADING"
        elif overall_score >= 0.5:
            assessment = "PARTIAL - Missing key components"
            trading_status = "❌ CANNOT TRADE SAFELY"
        else:
            assessment = "INCOMPLETE - Major trading functions missing"
            trading_status = "❌ CANNOT TRADE"
        
        print(f"📋 Assessment: {assessment}")
        print(f"💰 Trading Status: {trading_status}")
        
        # Critical missing components
        critical_missing = []
        
        # Check essential functions
        for func_name, data in function_results.items():
            if data['is_essential'] and not data['found']:
                critical_missing.append(f"Missing {func_name} function")
        
        # Check order execution essentials
        if not order_types.get('ORDER_TYPE_BUY', False):
            critical_missing.append("Missing ORDER_TYPE_BUY support")
        if not order_types.get('ORDER_TYPE_SELL', False):
            critical_missing.append("Missing ORDER_TYPE_SELL support")
        
        if critical_missing:
            print(f"\n🚨 Critical Issues:")
            for issue in critical_missing:
                print(f"   • {issue}")
        else:
            print(f"\n✅ No critical trading issues found!")
        
        # Trading capability summary
        capabilities = []
        if function_score >= 0.8:
            capabilities.append("Core EA functions")
        if execution_score >= 0.8:
            capabilities.append("Order execution")
        if position_score >= 0.8:
            capabilities.append("Position management")
        if risk_score >= 0.8:
            capabilities.append("Risk management")
        if decision_score >= 0.8:
            capabilities.append("Intelligent decision making")
        
        if capabilities:
            print(f"\n💪 Strong Capabilities:")
            for cap in capabilities:
                print(f"   ✅ {cap}")
        
        # Save detailed analysis
        import json
        with open('/home/renier/ProjectQuantum-Full/trading_functionality_analysis.json', 'w') as f:
            json.dump({
                'analysis_results': self.analysis_results,
                'overall_assessment': assessment,
                'trading_status': trading_status,
                'critical_missing': critical_missing,
                'strong_capabilities': capabilities
            }, f, indent=2)
        
        print(f"\n📄 Detailed analysis saved: trading_functionality_analysis.json")

def main():
    """Validate trading functionality"""
    print("🚀 Starting Trading Functionality Validation...")
    
    validator = TradingFunctionalityValidator()
    
    try:
        results = validator.validate_trading_functionality()
        print("\n✅ Trading functionality validation completed!")
        return True
        
    except Exception as e:
        print(f"❌ Trading validation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)