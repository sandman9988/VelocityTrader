#!/usr/bin/env python3
"""
ProjectQuantum MQL5 Financial Code Auditor
==========================================
Institutional-grade code auditing for algorithmic trading systems.

Checks based on:
- SEC/FINRA algorithmic trading requirements
- MiFID II algorithm testing standards
- Best practices from quantitative hedge funds
- OWASP security guidelines adapted for trading

Categories:
1. NUMERICAL SAFETY - Precision, overflow, underflow
2. MEMORY SAFETY - Buffers, arrays, allocation
3. EXECUTION SAFETY - Order handling, position management
4. RISK CONTROLS - Limits, circuit breakers, exposure
5. DATA INTEGRITY - Validation, sanitization, logging
6. DEFENSIVE PROGRAMMING - Error handling, edge cases
7. REGULATORY COMPLIANCE - Audit trails, timestamps

Author: ProjectQuantum Team
Version: 1.0.0
"""

import re
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class AuditCategory(Enum):
    """Financial audit categories"""
    NUMERICAL_SAFETY = "Numerical Safety"
    MEMORY_SAFETY = "Memory Safety"
    EXECUTION_SAFETY = "Execution Safety"
    RISK_CONTROLS = "Risk Controls"
    DATA_INTEGRITY = "Data Integrity"
    DEFENSIVE_PROGRAMMING = "Defensive Programming"
    REGULATORY_COMPLIANCE = "Regulatory Compliance"
    CODE_QUALITY = "Code Quality"


class Severity(Enum):
    """Issue severity - financial context"""
    CRITICAL = 1    # Could cause financial loss or system failure
    HIGH = 2        # Significant risk, must fix before production
    MEDIUM = 3      # Should fix, potential issues
    LOW = 4         # Best practice violation
    INFO = 5        # Informational, optimization opportunity


@dataclass
class AuditFinding:
    """A single audit finding"""
    file: str
    line: int
    category: AuditCategory
    severity: Severity
    rule_id: str
    title: str
    description: str
    recommendation: str
    code_context: str = ""
    references: List[str] = field(default_factory=list)


class FinancialAuditRules:
    """
    Comprehensive financial code audit rules
    """

    RULES = {
        # ================================================================
        # NUMERICAL SAFETY
        # ================================================================
        'NUM001': {
            'category': AuditCategory.NUMERICAL_SAFETY,
            'severity': Severity.CRITICAL,
            'title': 'Unsafe Division Operation',
            'pattern': r'(?<!/)/(?!/|=|\*)\s*([a-zA-Z_]\w*)',
            'exclude_pattern': r'SafeDiv|SafeDivide|SafeMath::Divide|\.0\s*$|/\s*100\.0|/\s*1000\.0|/\s*2\.0|/\s*10\.0|/\s*60|/\s*32767|/\s*BYTES_TO_MB|string\s+|headers\s*\+=|msg\s*=\s*"|CLogger::|\".*\"|\'.*\'|// |/\*|MathSqrt\s*\(\s*2|MESO_WINDOW|MICRO_WINDOW|MACRO_WINDOW|KINEMATIC_STATES|numBins|_WINDOW|_SIZE|_COUNT|MathLog\s*\(|/\s*MathLog|/\s*point|/\s*Point|volumeStep|lotStep|spec\.|MathRand',
            'description': 'Division by variable without zero-check can crash or produce infinity',
            'recommendation': 'Use SafeDivide(numerator, denominator, default_value) or explicit zero-check',
            'check_denominator_validation': True,  # Special flag for checking nearby validation
            'check_ternary_guard': True,  # NEW: Check for ternary operator guards like (x > 0) ? a/x : 0
            'check_string_context': True  # NEW: Exclude string operations
        },
        'NUM002': {
            'category': AuditCategory.NUMERICAL_SAFETY,
            'severity': Severity.HIGH,
            'title': 'Direct Floating Point Comparison',
            'pattern': r'(?:==|!=)\s*(?:\d+\.\d+|[a-zA-Z_]\w*\s*[,)])',
            'context_pattern': r'double|float',
            # Exclude: int comparisons, ArrayResize returns, handles, strings, enums, zero checks
            'exclude_pattern': r'NULL|nullptr|true|false|\w+\s*==\s*\w+\s*\)|enum|int\s+\w+|long\s+\w+|ArrayResize|PositionGet|INVALID_HANDLE|symbol|Symbol|magic|Magic|type|Type|Handle|String|Integer|POSITION_|ORDER_|DEAL_|==\s*0\.0|!=\s*0\.0|denominator',
            'description': 'Direct equality comparison of floating point values is unreliable',
            'recommendation': 'Use MathAbs(a - b) < EPSILON or IsEqual(a, b)'
        },
        'NUM003': {
            'category': AuditCategory.NUMERICAL_SAFETY,
            'severity': Severity.HIGH,
            'title': 'Potential Integer Overflow',
            'pattern': r'\b(int|long)\s+\w+\s*=\s*\w+\s*\*\s*\w+',
            # Exclude multiplications by small constants (safe operations)
            'exclude_pattern': r'\*\s*[2-9]\s*;|\*\s*1[0-9]\s*;',
            'description': 'Integer multiplication without overflow check',
            'recommendation': 'Use SafeMul() or check bounds before multiplication'
        },
        'NUM004': {
            'category': AuditCategory.NUMERICAL_SAFETY,
            'severity': Severity.MEDIUM,
            'title': 'Hardcoded Numeric Constant',
            'pattern': r'(?<![\w.])(?:0\.0[0-9]{3,}|[1-9]\d{3,}(?:\.\d+)?)(?![\w.])',
            # Exclude: constants, FNV hash, time calculations, forex standards, scaling factors, error codes
            'exclude_pattern': r'#define|const\s+|FNV|2166136261|16777619|0\.0001|32768|1440|10080|43200|86400|/ 100\.0|tolerance|epsilon|100000|10000|1000000|0\.00001|1024|4200|4201|4202|4203|swapLong|swapShort|point\s*\*|lotMin|lotStep|contractSize|tickSize|lotMax',
            'description': 'Magic numbers should be defined as named constants',
            'recommendation': 'Define as const or #define with descriptive name'
        },
        'NUM005': {
            'category': AuditCategory.NUMERICAL_SAFETY,
            'severity': Severity.MEDIUM,
            'title': 'Unsafe Square Root',
            'pattern': r'MathSqrt\s*\(',
            'exclude_pattern': r'SafeSqrt|>\s*0|>=\s*0',
            'description': 'MathSqrt with negative input returns NaN',
            'recommendation': 'Use SafeSqrt() or validate input >= 0'
        },
        'NUM006': {
            'category': AuditCategory.NUMERICAL_SAFETY,
            'severity': Severity.MEDIUM,
            'title': 'Unsafe Logarithm',
            'pattern': r'MathLog\s*\(',
            'exclude_pattern': r'SafeLog|>\s*0',
            'description': 'MathLog with non-positive input is undefined',
            'recommendation': 'Use SafeLog() or validate input > 0'
        },
        'NUM007': {
            'category': AuditCategory.NUMERICAL_SAFETY,
            'severity': Severity.HIGH,
            'title': 'Unsafe Power Operation',
            'pattern': r'MathPow\s*\(',
            # Exclude squaring (power of 2) since it's always safe mathematically
            'exclude_pattern': r'SafePow|,\s*2\s*\)|,\s*2\.0\s*\)',
            'description': 'MathPow can overflow or return NaN with certain inputs',
            'recommendation': 'Use SafePow() with bounds checking'
        },

        # ================================================================
        # MEMORY SAFETY
        # ================================================================
        'MEM001': {
            'category': AuditCategory.MEMORY_SAFETY,
            'severity': Severity.CRITICAL,
            'title': 'Array Access Without Bounds Check',
            'pattern': r'(\w+)\s*\[\s*([a-zA-Z_]\w*(?:\s*[\+\-\*/]\s*\w+)*)\s*\]',
            'exclude_pattern': r'ArraySize|<\s*ArraySize|>=\s*0\s*&&|IsValidIndex|SafeArrayAccess|MathMin|safeCount|loopCount|actualSize|sampledCount|m_bufferCount|m_historyIdx|m_markedCount|regimeCount|for\s*\(\s*int\s+\w+\s*=\s*0',
            'description': 'Array access with computed index without bounds validation',
            'recommendation': 'Validate: if(index >= 0 && index < ArraySize(arr))',
            'check_loop_bounds': True,  # Special flag for smarter checking
            'check_array_declaration': True  # NEW: Exclude array declarations
        },
        'MEM002': {
            'category': AuditCategory.MEMORY_SAFETY,
            'severity': Severity.HIGH,
            'title': 'Dynamic Memory Without Null Check',
            # Match 'new ClassName(' for actual allocations, not "New" in strings
            'pattern': r'=\s*new\s+[A-Z]\w*\s*\(',
            'exclude_pattern': r'==\s*NULL|!=\s*NULL|if\s*\(',
            'description': 'Dynamic allocation may fail, returning NULL',
            'recommendation': 'Always check: if(ptr == NULL) { handle error }'
        },
        'MEM003': {
            'category': AuditCategory.MEMORY_SAFETY,
            'severity': Severity.HIGH,
            'title': 'Potential Memory Leak',
            # Match 'new ClassName(' for actual allocations, not "New" in strings
            'pattern': r'=\s*new\s+[A-Z]\w*\s*\(',
            'context_check': 'delete_tracking',
            'description': 'Dynamic allocation without corresponding delete',
            'recommendation': 'Ensure every new has matching delete or use RAII pattern'
        },
        'MEM004': {
            'category': AuditCategory.MEMORY_SAFETY,
            'severity': Severity.MEDIUM,
            'title': 'ArrayResize Without Error Check',
            'pattern': r'ArrayResize\s*\([^)]+\)',
            'exclude_pattern': r'if\s*\(|==\s*-1|<\s*0',
            'description': 'ArrayResize returns -1 on failure',
            'recommendation': 'Check return: if(ArrayResize(arr, size) < 0) { handle error }'
        },
        'MEM005': {
            'category': AuditCategory.MEMORY_SAFETY,
            'severity': Severity.MEDIUM,
            'title': 'Buffer Size Not Validated',
            'pattern': r'(?:Ring)?Buffer\s*\(\s*(\d+)\s*\)',
            'description': 'Fixed buffer sizes should be validated constants',
            'recommendation': 'Use named constants and validate buffer capacity'
        },

        # ================================================================
        # EXECUTION SAFETY (Trading Specific)
        # ================================================================
        'EXEC001': {
            'category': AuditCategory.EXECUTION_SAFETY,
            'severity': Severity.CRITICAL,
            'title': 'Order Without Validation',
            'pattern': r'OrderSend\s*\(',
            'exclude_pattern': r'Validate|Check|if\s*\(|Verify',
            'description': 'Order submission without pre-validation',
            'recommendation': 'Validate symbol, volume, prices, stops before OrderSend'
        },
        'EXEC002': {
            'category': AuditCategory.EXECUTION_SAFETY,
            'severity': Severity.CRITICAL,
            'title': 'Position Size Not Normalized',
            'pattern': r'(?:volume|lot|lots)\s*[=:]\s*(?!\s*Normalize)',
            'exclude_pattern': r'NormalizeVolume|NormalizeLot|NormalizeLotSize|NormalizeLots|SymbolInfo|lot_step|volumeStep|volumeMin|volumeMax|Clamp|ClampValue|MathFloor.*lot|MathRound.*lot|MathCeil.*lot|steps\s*\*|m_min_lot|m_max_lot|min_lot|max_lot|= 0\.|= 1\.|= 100\.|= 0;|base_lots|normalized_lots|final_lots|// |/\*|intermediate|calculation|input\s+|extern\s+|double\s+Normalize|bool\s+Normalize|void\s+Normalize|SafeDivide|GetAdaptiveLot|CalculateLot|ComputeLot|_lot\s*\(|Lots\s*\(|AccountInfo|GetLot|SetLot|initialLot|defaultLot|minLot|maxLot|StringFormat|".*[Ll]ot.*"|Max\s*Lot|Min\s*Lot|iVolume|PositionGetDouble|m_posInfo\.|Buckets|Bucket|\.Volume\(\)',
            'description': 'Lot size must be normalized to broker requirements before order submission',
            'recommendation': 'Use NormalizeVolume() or validate against SYMBOL_VOLUME_*',
            'check_return_normalization': True,  # Check if function returns normalized value
            'check_normalizer_context': True  # NEW: Check if within a normalizer function
        },
        'EXEC003': {
            'category': AuditCategory.EXECUTION_SAFETY,
            'severity': Severity.HIGH,
            'title': 'Stop Level Not Validated',
            'pattern': r'(?:stop|sl|tp)\s*[=:]\s*\w+\s*[\+\-]',
            # Exclude: calculations already using minDistance, trailing stop calculations, validated distances
            'exclude_pattern': r'SYMBOL_TRADE_STOPS_LEVEL|ValidateStop|minStop|minTP|minDistance|potentialSL|trailDist|atr\s*\*',
            'description': 'Stop/TP distance not checked against broker minimum',
            'recommendation': 'Validate against SymbolInfoInteger(SYMBOL_TRADE_STOPS_LEVEL)'
        },
        'EXEC004': {
            'category': AuditCategory.EXECUTION_SAFETY,
            'severity': Severity.HIGH,
            'title': 'Price Not Normalized',
            'pattern': r'(?:price|entry|exit)\s*=\s*(?!\s*NormalizeDouble)',
            # Exclude: API values, bid/ask, enums, booleans, member assignments, non-prices
            'exclude_pattern': r'NormalizeDouble|Bid|Ask|SymbolInfo|=\s*0|=\s*prices\[|=\s*GlobalVariable|z_score|slippage|Calculate|first_|last_|PositionGet|m_posInfo|m_dealInfo|DEAL_ENTRY|signal|minStop|minTP|PriceOpen|PriceCurrent|=\s*(?:true|false)|openPrice\s*=\s*Position|entryPrice\s*=\s*m_|regimeAt|pWinAt|m_lastPrice|currentPrice\s*=\s*\(|=\s*\([^)]+\?\s*(?:bid|ask)|\.entryPrice\s*=|\.exitPrice\s*=|currentSL',
            'description': 'Prices must be normalized to symbol digits',
            'recommendation': 'Use NormalizeDouble(price, _Digits)'
        },
        'EXEC005': {
            'category': AuditCategory.EXECUTION_SAFETY,
            'severity': Severity.MEDIUM,
            'title': 'Trade Result Not Checked',
            'pattern': r'OrderSend\s*\([^)]+\)\s*;',
            'exclude_pattern': r'if\s*\(|result|retcode',
            'description': 'Order result not checked for success/failure',
            'recommendation': 'Always check trade.ResultRetcode() after OrderSend'
        },
        'EXEC006': {
            'category': AuditCategory.EXECUTION_SAFETY,
            'severity': Severity.MEDIUM,
            'title': 'Spread Not Validated',
            'pattern': r'(?:Bid|Ask)',
            'context_pattern': r'OrderSend|trade\.',
            'exclude_pattern': r'spread|Spread|SPREAD',
            'description': 'Trade execution without spread check',
            'recommendation': 'Validate spread < max_spread before trading'
        },

        # ================================================================
        # RISK CONTROLS
        # ================================================================
        'RISK001': {
            'category': AuditCategory.RISK_CONTROLS,
            'severity': Severity.CRITICAL,
            'title': 'Missing Maximum Position Size Limit',
            'pattern': r'(?:volume|lot)\s*=',
            'context_pattern': r'class\s+\w*(?:Risk|Position|Size)',
            'exclude_pattern': r'max_lot|MAX_LOT|m_max|maxLot',
            'description': 'Position sizing without maximum limit check',
            'recommendation': 'Implement max position size limit: Math.min(calculated, max_allowed)'
        },
        'RISK002': {
            'category': AuditCategory.RISK_CONTROLS,
            'severity': Severity.CRITICAL,
            'title': 'Missing Drawdown Check',
            'pattern': r'\bvoid\s+OnTick\s*\(\s*\)|\bvoid\s+OnTimer\s*\(\s*\)',
            'context_check': 'drawdown_check',
            'exclude_pattern': r'GetSavedPositionTicket|NeedsPositionRecovery|Recovery|recovery|// Recovery|/\* Recovery|g_breaker|CircuitBreaker|CanTrade|breaker\.Update|drawdown|Drawdown|IsDrawdownExceeded|class\s+\w+',
            'description': 'Trading logic without drawdown limit check (excludes recovery methods)',
            'recommendation': 'Check drawdown before each trade decision (not needed for position recovery)',
            'check_function_body': True  # Check the function body, not just the line
        },
        'RISK003': {
            'category': AuditCategory.RISK_CONTROLS,
            'severity': Severity.HIGH,
            'title': 'Missing Account Equity Check',
            'pattern': r'OrderSend',
            'exclude_pattern': r'AccountInfoDouble|Equity|Balance|Margin',
            'description': 'Order without account state validation',
            'recommendation': 'Verify sufficient margin and equity before trading'
        },
        'RISK004': {
            'category': AuditCategory.RISK_CONTROLS,
            'severity': Severity.HIGH,
            'title': 'Missing Daily Loss Limit',
            'pattern': r'class\s+\w*(?:Risk|Circuit)',
            'context_check': 'daily_loss',
            'description': 'Risk management without daily loss limit',
            'recommendation': 'Implement daily P&L limit with circuit breaker'
        },
        'RISK005': {
            'category': AuditCategory.RISK_CONTROLS,
            'severity': Severity.MEDIUM,
            'title': 'Missing Correlation Check',
            'pattern': r'(?:portfolio|multi.*symbol|symbol.*array)',
            'exclude_pattern': r'correlation|Correlation',
            'description': 'Multi-symbol trading without correlation awareness',
            'recommendation': 'Track and limit correlated exposure'
        },

        # ================================================================
        # DATA INTEGRITY
        # ================================================================
        'DATA001': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.HIGH,
            'title': 'Unvalidated External Input',
            'pattern': r'input\s+(?:double|int|string)\s+\w+\s*=',
            'exclude_pattern': r'Validate|Check|if\s*\(',
            'description': 'User input parameters without validation',
            'recommendation': 'Validate all inputs in OnInit() with bounds checking',
            'check_file_for_validation': True  # Check if file has ValidateInputParameters
        },
        'DATA002': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.HIGH,
            'title': 'Missing Data Validity Check',
            'pattern': r'iClose|iOpen|iHigh|iLow|iVolume|iTime',
            'exclude_pattern': r'==\s*0|==\s*EMPTY_VALUE|if\s*\(|SafeOHLCV|GetSafeOHLCV|IsValid|\.valid|MathIsValidNumber|IsValidNumber|data\.|mc\.',
            'description': 'Historical data access without validity check',
            'recommendation': 'Check for EMPTY_VALUE or 0 before using data',
            'check_in_safe_function': True  # Exclude if inside GetSafeOHLCV function
        },
        'DATA003': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.MEDIUM,
            'title': 'File Operation Without Error Handling',
            'pattern': r'File(?:Open|ReadInteger|ReadDouble|ReadLong|ReadArray|ReadString|WriteInteger|WriteDouble|WriteLong|WriteArray|WriteString)',
            'exclude_pattern': r'if\s*\(|INVALID_HANDLE|==\s*-1|SafeFile|FileWriteContext|uint\s+written|written\s*[!=]|bytesRead|BytesRead|ctx\.|CalculateChecksum|CalculateFileChecksum',
            'description': 'File operations can fail',
            'recommendation': 'Always check file handles and operation results',
            'check_validated_handle': True  # Check if handle was validated earlier
        },
        'DATA004': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.MEDIUM,
            'title': 'JSON/String Parsing Without Validation',
            'pattern': r'StringTo(?:Integer|Double)|CharArrayToString',
            'exclude_pattern': r'try|catch|if\s*\(',
            'description': 'String parsing can fail with invalid data',
            'recommendation': 'Validate string format before parsing'
        },
        'DATA005': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.HIGH,
            'title': 'Missing Warmup Period Check',
            'pattern': r'\bvoid\s+OnTick\s*\(\s*\)|\bvoid\s+OnCalculate|\bvoid\s+OnTimer\s*\(\s*\)',
            'context_check': 'warmup_check',
            'exclude_pattern': r'warmup|WarmUp|warm_up|WARMUP|BarsCalculated|prev_calculated|initialized|IsReady|calibrat|Calibration|tickCount\s*<|class\s+\w+',
            'description': 'Trading logic should wait for indicator warmup before generating signals',
            'recommendation': 'Check for sufficient historical bars and indicator warmup period',
            'check_function_body': True  # Check function body for warmup logic
        },
        'DATA006': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.MEDIUM,
            'title': 'Missing Gap Detection',
            'pattern': r'iClose|iOpen|Close\[|Open\[|rates_total',
            'exclude_pattern': r'gap|Gap|GAP|TimeDiff|holiday|Holiday|rollover|Rollover|weekend|Weekend|HasPriceGap|SafeOHLCV|GetSafeOHLCV|Marked|Logger|Log\(',
            'description': 'Price data may have gaps from holidays, weekends, or rollovers',
            'recommendation': 'Detect and handle time gaps, especially around weekends and holidays'
        },
        'DATA007': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.HIGH,
            'title': 'Missing Jump/Spike Detection',
            'pattern': r'(?:price|Price)\s*[=:]\s*(?:Bid|Ask|iClose)',
            'exclude_pattern': r'spike|Spike|jump|Jump|outlier|Outlier|filter|Filter|zscore|ZScore|deviation|threshold',
            'description': 'Sudden price jumps may indicate bad data or extreme volatility',
            'recommendation': 'Filter price spikes using z-score or ATR-based thresholds'
        },
        'DATA008': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.MEDIUM,
            'title': 'Missing Session/Rollover Handling',
            'pattern': r'OrderSend|PositionOpen',
            'exclude_pattern': r'session|Session|SESSION|rollover|Rollover|ROLLOVER|swap|midnight|IsTradeAllowed',
            'description': 'Trading around session boundaries or rollover can cause issues',
            'recommendation': 'Check for session boundaries and handle daily rollovers properly'
        },
        'DATA009': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.HIGH,
            'title': 'Missing Rate Limit / Throttling',
            'pattern': r'for\s*\([^)]+\)\s*\{[^}]*(?:OrderSend|SymbolInfo|Copy(?:Rates|Buffer|Time))',
            'exclude_pattern': r'Sleep|throttle|Throttle|THROTTLE|rate_limit|RateLimit|batch|Batch|BATCH|delay|Delay|cooldown|Cooldown|AdaptiveThrottle|DynamicDelay',
            'description': 'Bulk operations in loops can hit broker rate limits or cause performance issues',
            'recommendation': 'Implement DYNAMIC rate limiting: (1) Start with min delay (1-5ms), (2) Increase delay on rate limit errors, (3) Decrease delay during low-activity periods, (4) Use adaptive batch sizes based on market conditions. Example: Sleep(MathMax(1, baseDelay * (1 + errorCount * 0.5)))'
        },
        'DATA010': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.MEDIUM,
            'title': 'Unbounded Loop Over Symbols',
            'pattern': r'for\s*\([^;]+;\s*\w+\s*<\s*(?:g_symbolCount|SymbolsTotal)',
            'exclude_pattern': r'batch|Batch|BATCH|chunk|Chunk|MAX_BATCH|MAX_SYMBOLS_PER_TICK|limit|Limit|priority|Priority|ranked|Ranked|&&\s*\w+\s*<\s*MAX_|initialized|typeAllowed|warmup|Warmup',
            'description': 'Processing all symbols each tick can cause performance issues with large watchlists',
            'recommendation': 'Process symbols in priority order: (1) Prioritize symbols with open positions, (2) Rank by trading signal strength, (3) Rotate through remaining symbols across ticks. Use adaptive batch sizes based on tick frequency.',
            'check_loop_body': True  # Check the loop body for bounded iteration patterns
        },
        'DATA011': {
            'category': AuditCategory.DATA_INTEGRITY,
            'severity': Severity.MEDIUM,
            'title': 'Missing Cooldown Between Orders',
            'pattern': r'OrderSend\s*\([^)]+\)[^}]*OrderSend\s*\(',
            'exclude_pattern': r'Sleep|cooldown|Cooldown|COOLDOWN|delay|Delay|wait|Wait|timer|Timer|lastOrderTime|g_lastOrder',
            'description': 'Multiple orders without cooldown can trigger broker anti-spam measures',
            'recommendation': 'Implement ADAPTIVE cooldown: (1) Track time since last order, (2) Use minimum 50-100ms between orders, (3) Increase cooldown after rejections, (4) Reset to minimum during favorable conditions. Track: static datetime g_lastOrderTime = 0; if(TimeCurrent() - g_lastOrderTime < minCooldown) return;'
        },

        # ================================================================
        # DEFENSIVE PROGRAMMING
        # ================================================================
        'DEF001': {
            'category': AuditCategory.DEFENSIVE_PROGRAMMING,
            'severity': Severity.HIGH,
            'title': 'Missing Null Pointer Check',
            'pattern': r'(\w+)\s*[.>]\s*\w+\s*\(',
            # Exclude: member objects, history/cache objects, local references, queues, MT5 built-ins
            'exclude_pattern': r'!=\s*NULL|==\s*NULL|if\s*\(\s*\w+\s*\)|\.Init\(|\.Reset\(|\.Clear\(|\.Update\(|\.Calculate\(|\.Detect\(|\.Normalize\(|\.GetVolatility\(|\.Get[A-Z]|\.Set[A-Z]|\.Is[A-Z]|\.Has[A-Z]|\.Add[A-Z]|\.Remove[A-Z]|\.Any|\.To[A-Z]|\.Recalc|\.Decay|\.Invalidate|result\.|state\.|config\.|cfg\.|micro\.|meso\.|macro\.|m_\w+\.|this\.|child\.|metrics\.|yz\.|cycle\.|physics\.|w\.|g_\w+\.|_trade\.|trade\.|profile\.|agent\.|stats\.|regime\[|spec\.|breaker\.|predictor\.|sniper\.|berserker\.|symc\.|History\.|cached\w*\.|rolling\w*\.|real\.|pnl\w*\.|win\w*\.|symbol\.|action\.|request\.|response\.|\.Push\(|\.Pop\(|\.Count\(|TimeCurrent|s1\.|s2\.|entry\.|exit\.|quality\.|avg\w+\.|update\w+\.|\.Dequeue\(|\.Enqueue\(|\.CalculateStats\(|\.CalculateOverall\(|Print\(',
            'description': 'Object method call without null check',
            'recommendation': 'Check: if(ptr != NULL) before dereferencing'
        },
        'DEF002': {
            'category': AuditCategory.DEFENSIVE_PROGRAMMING,
            'severity': Severity.MEDIUM,
            'title': 'Missing Error Code Check',
            'pattern': r'GetLastError\s*\(\s*\)',
            'exclude_pattern': r'if\s*\(|==\s*0|!=\s*0',
            'description': 'GetLastError called but result not used',
            'recommendation': 'Check error code: if(GetLastError() != 0) { handle }'
        },
        'DEF003': {
            'category': AuditCategory.DEFENSIVE_PROGRAMMING,
            'severity': Severity.MEDIUM,
            'title': 'Switch Without Default Case',
            'pattern': r'switch\s*\([^)]+\)\s*\{[^}]+\}',
            'exclude_pattern': r'default\s*:',
            'description': 'Switch statement missing default case',
            'recommendation': 'Always include default case for unexpected values'
        },
        'DEF004': {
            'category': AuditCategory.DEFENSIVE_PROGRAMMING,
            'severity': Severity.LOW,
            'title': 'Empty Catch/Exception Block',
            'pattern': r'catch\s*\([^)]*\)\s*\{\s*\}',
            'description': 'Empty catch block silently swallows errors',
            'recommendation': 'Log errors even if not re-throwing'
        },
        'DEF005': {
            'category': AuditCategory.DEFENSIVE_PROGRAMMING,
            'severity': Severity.MEDIUM,
            'title': 'Nested Loop Without Independent Bounds',
            'pattern': r'for\s*\([^)]+\)\s*\{[^}]*for\s*\([^)]+\)',
            'exclude_pattern': r'ArraySize|\.size\(|_size|_count|ARRAY_|MAX_|NUM_',
            'description': 'Nested loops should use independent bounds or explicit size checks',
            'recommendation': 'Use ArraySize() or size variables for each dimension',
            'check_nested_bounds': True
        },
        'DEF006': {
            'category': AuditCategory.DEFENSIVE_PROGRAMMING,
            'severity': Severity.HIGH,
            'title': 'Hardcoded Array Size in Loop',
            'pattern': r'for\s*\([^;]+;\s*\w+\s*<\s*[0-9]+\s*;',
            # Exclude small constants and well-known safe values (7=days, 8=bits, 10=retries, 256=bytes)
            'exclude_pattern': r'<\s*[0-9]\s*;|<\s*1[0-2]\s*;|<\s*256\s*;|ArraySize|REGIME|_COUNT|MAX_|NUM_',
            'description': 'Loop with hardcoded limit may break if array size changes',
            'recommendation': 'Use ArraySize(arr) or define a named constant for the size'
        },
        'DEF007': {
            'category': AuditCategory.DEFENSIVE_PROGRAMMING,
            'severity': Severity.MEDIUM,
            'title': 'Index Calculation Without Clamp',
            'pattern': r'\[\s*\w+\s*[+\-*/]\s*\d+\s*\]',
            # Exclude: clamp functions, modulo, small fixed offsets (0-9), feature index patterns
            'exclude_pattern': r'MathMin|MathMax|Clamp|%\s*\d+|%\s*\w+|SafeIndex|ClampIndex|IsValidIndex|\+\s*[0-9]\s*\]|startIdx|featureIdx|baseIdx',
            'description': 'Computed index without range clamping may go out of bounds',
            'recommendation': 'Use MathMax(0, MathMin(idx, size-1)) or modulo operator'
        },

        # ================================================================
        # REGULATORY COMPLIANCE
        # ================================================================
        'REG001': {
            'category': AuditCategory.REGULATORY_COMPLIANCE,
            'severity': Severity.HIGH,
            'title': 'Missing Audit Trail',
            'pattern': r'OrderSend|PositionClose|PositionModify',
            'exclude_pattern': r'Log|Print|FileWrite|Journal',
            'description': 'Trade operations without audit logging',
            'recommendation': 'Log all trade decisions with timestamp, reason, and parameters'
        },
        'REG002': {
            'category': AuditCategory.REGULATORY_COMPLIANCE,
            'severity': Severity.MEDIUM,
            'title': 'Missing Timestamp in Logs',
            'pattern': r'Print\s*\(',
            'exclude_pattern': r'TimeToString|TimeCurrent|timestamp|TimeLocal|CLogger|WARNING|ERROR|ARCHITECTURE|BuildFingerprint|TestFramework|message\)|log_line',
            'description': 'Log entries should include timestamps',
            'recommendation': 'Include timestamp in all log entries'
        },
        'REG003': {
            'category': AuditCategory.REGULATORY_COMPLIANCE,
            'severity': Severity.MEDIUM,
            'title': 'Hardcoded Trading Hours',
            'pattern': r'(?:Hour\s*[<>=]|TimeHour\s*\([^)]+\)\s*[<>=])\s*\d+',
            'description': 'Trading hours should be configurable',
            'recommendation': 'Use input parameters or symbol session info'
        },

        # ================================================================
        # CODE QUALITY
        # ================================================================
        'QUAL001': {
            'category': AuditCategory.CODE_QUALITY,
            'severity': Severity.LOW,
            'title': 'Function Too Long',
            'pattern': r'^\s*(?:void|int|double|bool|string)\s+\w+\s*\([^)]*\)\s*\{',
            'context_check': 'function_length',
            'description': 'Functions over 50 lines are harder to maintain',
            'recommendation': 'Break into smaller, focused functions'
        },
        'QUAL002': {
            'category': AuditCategory.CODE_QUALITY,
            'severity': Severity.LOW,
            'title': 'Deeply Nested Code',
            'pattern': r'\{\s*\{',
            'context_check': 'nesting_depth',
            'description': 'Deep nesting reduces readability',
            'recommendation': 'Refactor using early returns or separate functions'
        },
        'QUAL003': {
            'category': AuditCategory.CODE_QUALITY,
            'severity': Severity.INFO,
            'title': 'Missing Include Guard',
            'pattern': r'^#property',
            'exclude_pattern': r'#ifndef|#define\s+\w+_MQH',
            'file_type': '.mqh',
            'description': 'Header files should have include guards',
            'recommendation': 'Add #ifndef FILENAME_MQH / #define FILENAME_MQH / #endif'
        },
    }


class FinancialCodeAuditor:
    """
    Main auditor implementing financial-grade checks
    """

    def __init__(self, project_root: Path, use_impact_scoring: bool = True):
        self.project_root = project_root
        self.findings: List[AuditFinding] = []
        self.file_hashes: Dict[str, str] = {}
        self._display_limit = None  # Optional limit for detailed findings display
        self._impact_analyzer = None
        self._use_impact_scoring = use_impact_scoring
        self._impact_scores: Dict[str, float] = {}  # file -> impact multiplier

    def audit_file(self, file_path: Path) -> List[AuditFinding]:
        """Audit a single file against all rules"""
        findings = []

        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                lines = content.split('\n')
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return findings
        except PermissionError:
            logger.warning(f"Permission denied reading: {file_path}")
            return findings
        except UnicodeDecodeError:
            # Try fallback encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                    lines = content.split('\n')
                logger.info(f"Read '{file_path}' with fallback encoding (latin-1)")
            except Exception as e:
                logger.error(f"Failed to read {file_path} with fallback encoding: {e}")
                return findings
        except (IOError, OSError) as e:
            logger.error(f"I/O error reading '{file_path}': {e}")
            return findings

        # Compute hash
        try:
            with open(file_path, 'rb') as f:
                self.file_hashes[str(file_path)] = hashlib.sha256(f.read()).hexdigest()
        except (IOError, OSError) as e:
            logger.warning(f"Could not compute hash for '{file_path}': {e}")
            self.file_hashes[str(file_path)] = "error"

        # Apply each rule
        for rule_id, rule in FinancialAuditRules.RULES.items():
            # Check file type filter
            if 'file_type' in rule:
                if not str(file_path).endswith(rule['file_type']):
                    continue

            pattern = re.compile(rule['pattern'], re.MULTILINE | re.IGNORECASE)
            exclude = re.compile(rule.get('exclude_pattern', r'$^'))

            # Track multi-line comment state
            in_multiline_comment = False

            for i, line in enumerate(lines, 1):
                stripped = line.strip()

                # Handle multi-line comment state
                if in_multiline_comment:
                    if '*/' in stripped:
                        in_multiline_comment = False
                        # Process part of line after comment ends
                        line = line.split('*/', 1)[1] if '*/' in line else ''
                        stripped = line.strip()
                        if not stripped:
                            continue
                    else:
                        continue

                # Skip single-line comments and preprocessor directives
                if not stripped or stripped.startswith('//') or stripped.startswith('#'):
                    continue

                # Strip single-line comments from the line
                if '//' in line:
                    line_before_comment = line.split('//', 1)[0]
                    if not line_before_comment.strip():
                        continue
                    line = line_before_comment

                # Check for multi-line comment start
                if '/*' in line:
                    if '*/' not in line[line.index('/*')+2:]:
                        in_multiline_comment = True
                    # Process part of line before comment
                    line_before_comment = line.split('/*', 1)[0]
                    if not line_before_comment.strip():
                        continue
                    line = line_before_comment

                # Check pattern
                if pattern.search(line):
                    # Check exclusion
                    if not exclude.search(line):
                        # Special handling for MEM001 - check for array declarations and loop bounds
                        if rule.get('check_array_declaration', False) or rule.get('check_loop_bounds', False):
                            # Extract the array and index from the match
                            match = pattern.search(line)
                            if match:
                                array_name = match.group(1)
                                index_expr = match.group(2).strip()

                                # Check if this is an array DECLARATION (not access)
                                # Pattern: TypeName array_name[SIZE] or TypeName array_name[SIZE] = {...}
                                # These have a type before the array name
                                declaration_pattern = rf'(?:^|\s)(?:static\s+)?(?:const\s+)?(?:\w+)\s+{array_name}\s*\[\s*{index_expr}\s*\]'
                                if re.search(declaration_pattern, line):
                                    continue  # Skip array declarations

                                # Also check for common constant size patterns in declarations
                                const_size_patterns = [
                                    r'MAX_\w+', r'ARRAY_SIZE', r'BUFFER_SIZE', r'SIZE_\w+',
                                    r'ROLLING_WINDOW', r'NUM_\w+', r'COUNT_\w+', r'\d+'
                                ]
                                is_const_declaration = any(re.match(p, index_expr) for p in const_size_patterns)
                                # If it looks like a declaration with constant size, check context
                                if is_const_declaration:
                                    # Check if this line has a type before array (declaration)
                                    if re.search(rf'\b(?:int|double|string|bool|uchar|datetime|color|long|ulong|short|ushort|char|float)\s+{array_name}\s*\[', line):
                                        continue
                                    # Check for struct/class member declarations
                                    if re.search(rf'^\s*(?:\w+)\s+{array_name}\s*\[\s*{index_expr}\s*\]\s*;', line):
                                        continue

                                index_var = index_expr.split()[0]  # Get first part of index expression
                                
                                # Look back up to 20 lines for bounds checking (increased from 15)
                                context_start = max(0, i - 20)
                                context_lines = lines[context_start:i]
                                context_str = '\n'.join(context_lines)
                                found_bounds_check = False
                                
                                # Pattern 1: Check for: for(int index_var = 0; index_var < CONSTANT; ...)
                                # This handles loops with fixed bounds like for(int i = 0; i < 4; ...)
                                if re.search(rf'for\s*\(\s*int\s+{index_var}\s*=\s*0\s*;\s*{index_var}\s*<\s*\d+', context_str):
                                    # Verify the constant matches the expected array size
                                    # For m_regime_stats[i], the constant should be 4
                                    const_match = re.search(rf'for\s*\(\s*int\s+{index_var}\s*=\s*0\s*;\s*{index_var}\s*<\s*(\d+)', context_str)
                                    if const_match:
                                        const_val = int(const_match.group(1))
                                        # Known fixed-size arrays
                                        if ('regime_stats' in array_name and const_val == 4) or \
                                           ('clusters' in array_name and const_val <= 20) or \
                                           (const_val <= 10):  # Small constant loops are generally safe
                                            found_bounds_check = True
                                
                                # Pattern 2: Check for: for(int index_var = ...; index_var < size_var; ...)
                                if not found_bounds_check and re.search(rf'for\s*\([^;]*{index_var}\s*=.*;\s*{index_var}\s*<\s*\w+', context_str):
                                    found_bounds_check = True
                                
                                # Pattern 3: Check for: if(index_var >= 0 && index_var < size) or if(index_var < 0 || index_var >= size) return
                                if not found_bounds_check:
                                    # Positive check: if(idx >= 0 && idx < 4) { ... use idx ... }
                                    if re.search(rf'if\s*\([^)]*{index_var}\s*>=\s*0\s*&&\s*{index_var}\s*<', context_str):
                                        found_bounds_check = True
                                    # Negative check with early return: if(idx < 0 || idx >= N) return
                                    # Matches both constants and variables: >= 4 or >= priorities_size
                                    elif re.search(rf'if\s*\(\s*{index_var}\s*<\s*0\s*\|\|\s*{index_var}\s*>=\s*\w+\s*\)\s*return', context_str):
                                        found_bounds_check = True
                                    # Also match: if(idx < 0 || idx > N) return (using > instead of >=)
                                    elif re.search(rf'if\s*\(\s*{index_var}\s*<\s*0\s*\|\|\s*{index_var}\s*>\s*\d+\s*\)\s*return', context_str):
                                        found_bounds_check = True
                                    # Check for enclosing if with size comparison: if(m_size > 0 && m_size <= array_size)
                                    # This handles: if(m_size > 0 && m_size <= cdf_size) { cdf[m_size - 1] = ... }
                                    elif re.search(rf'if\s*\([^)]*\w+\s*>\s*0\s*&&\s*\w+\s*<=\s*{array_name}_size', context_str):
                                        # Check if the index uses that variable minus 1
                                        if '-' in index_expr and '1' in index_expr:
                                            found_bounds_check = True

                                # Pattern 3b: More flexible early return patterns
                                if not found_bounds_check:
                                    # Look for early return on out of bounds in function context (100 lines)
                                    func_context = '\n'.join(lines[max(0, i-100):i])
                                    # Pattern: if(idx < 0 || idx > N) return; where N is a constant
                                    if re.search(rf'if\s*\(\s*{index_var}\s*<\s*0\s*\|\|\s*{index_var}\s*>\s*\d+\s*\)', func_context):
                                        found_bounds_check = True
                                    # Pattern: if(idx < 0 || idx >= N) return;
                                    elif re.search(rf'if\s*\(\s*{index_var}\s*<\s*0\s*\|\|\s*{index_var}\s*>=\s*\d+\s*\)', func_context):
                                        found_bounds_check = True
                                
                                # Pattern 4: Check for index_var with modulo (wraps around)
                                if not found_bounds_check and '%' in index_expr:
                                    # Modulo operations ensure index is within bounds
                                    found_bounds_check = True

                                # Pattern 4a: Check if index_var was ASSIGNED using modulo earlier
                                # e.g., idx = m_historyIdx % m_historySize; ... array[idx]
                                if not found_bounds_check:
                                    prev_lines = '\n'.join(lines[max(0, i-30):i])  # Extended lookback for function scope
                                    # Check for: index_var = expr % size
                                    if re.search(rf'\b{index_var}\s*=\s*[^;]+%', prev_lines):
                                        found_bounds_check = True

                                # Pattern 4b: Check for IsValidIndex calls - expanded to find validation anywhere in function
                                if not found_bounds_check:
                                    # Look back to function start (up to 150 lines) for IsValidIndex on this or related variable
                                    func_context_start = max(0, i - 150)
                                    func_context = '\n'.join(lines[func_context_start:i])

                                    # Direct IsValidIndex check on the index variable
                                    if re.search(rf'IsValidIndex\s*\(\s*{index_var}', func_context):
                                        found_bounds_check = True
                                    # Check for inline validation with early return: if(!IsValidIndex(idx, size)) return;
                                    elif re.search(rf'if\s*\(\s*!IsValidIndex\s*\(\s*{index_var}', func_context):
                                        found_bounds_check = True
                                    # Check for any IsValidIndex with early return before this line
                                    elif re.search(rf'if\s*\(\s*!IsValidIndex[^)]+\)\s*return', func_context):
                                        found_bounds_check = True

                                # Pattern 4c: Check for known safe zone calculations
                                # Variables like chiZone, accelZone are computed by functions that clamp to valid range
                                if not found_bounds_check:
                                    zone_patterns = ['Zone', 'zone', 'Idx', 'idx', 'Index', 'index']
                                    if any(p in index_var for p in zone_patterns):
                                        # Check if the zone was computed with clamping or known safe function
                                        if re.search(rf'{index_var}\s*=\s*(?:Get\w*Zone|MathMax|MathMin|Clamp)', context_str):
                                            found_bounds_check = True
                                
                                # Pattern 5: Loop bounded by array size that was just resized
                                # Check for: ArrayResize(array, size); ... for(i < size) ... array[i]
                                if not found_bounds_check:
                                    # Look for ArrayResize of this array
                                    if re.search(rf'ArrayResize\s*\(\s*{array_name}\s*,', context_str):
                                        # And loop bounded by same variable
                                        if re.search(rf'for\s*\([^;]*{index_var}.*{index_var}\s*<\s*(\w+)', context_str):
                                            found_bounds_check = True

                                # Pattern 5b: ArrayResize immediately before access with count/size variable
                                # e.g., ArrayResize(arr, count + 1); arr[count] = x;
                                if not found_bounds_check:
                                    # Check if previous 30 lines have ArrayResize with count+1 pattern
                                    prev_lines = '\n'.join(lines[max(0, i-30):i])
                                    # ArrayResize(array, count + 1) followed by array[count]
                                    if re.search(rf'ArrayResize\s*\(\s*{array_name}\s*,\s*{index_var}\s*\+\s*1', prev_lines):
                                        found_bounds_check = True
                                    # ArrayResize(array, size); followed by array[size - 1] or array[size]
                                    elif re.search(rf'ArrayResize\s*\(\s*{array_name}\s*,', prev_lines):
                                        # The resize makes access at new size-1 or incremented counter safe
                                        found_bounds_check = True
                                    # Pattern: if(count >= ArraySize(arr)) ArrayResize(arr, ...); arr[count] = x;
                                    elif re.search(rf'if\s*\(\s*{index_var}\s*>=\s*ArraySize\s*\(\s*{array_name}\s*\)', prev_lines) and \
                                         re.search(rf'ArrayResize\s*\(\s*{array_name}\s*,', prev_lines):
                                        found_bounds_check = True
                                
                                # Pattern 6: Check if the array is a known fixed-size member variable
                                # e.g., m_regime_stats[4] is always size 4
                                if not found_bounds_check:
                                    # Check if variable is validated earlier in the function
                                    # Look for the function start and check for early return validation
                                    func_start = max(0, i - 80)
                                    for j in range(func_start, i):
                                        # Look for function declaration
                                        if re.match(r'\s*(int|double|bool|void|string)\s+\w+\s*\(', lines[j]):
                                            # Found function start, now look for validation
                                            func_body = '\n'.join(lines[j:i])
                                            # Check for early return pattern: if(idx < 0 || idx >= N) return;
                                            if re.search(rf'if\s*\(\s*{index_var}\s*<\s*0\s*\|\|\s*{index_var}\s*>=\s*\w+\s*\)\s*return', func_body):
                                                found_bounds_check = True
                                            # Check for early return with continue pattern in loop context
                                            elif re.search(rf'if\s*\(\s*!IsValidIndex\s*\(\s*{index_var}', func_body):
                                                found_bounds_check = True
                                            # Check for bounds check on different but related variable (e.g., slot after slot = count++)
                                            elif re.search(rf'if\s*\(\s*!IsValidIndex\s*\([^)]+\)\s*\)', func_body):
                                                # If there's ANY IsValidIndex check with return/continue, likely safe
                                                if re.search(r'if\s*\(\s*!IsValidIndex[^)]+\)\s*(?:return|\{[^}]*return|continue)', func_body):
                                                    found_bounds_check = True
                                            break

                                # Pattern 6b: Check for slot = count++ pattern followed by IsValidIndex(slot)
                                if not found_bounds_check:
                                    prev_lines = '\n'.join(lines[max(0, i-10):i])
                                    # Pattern: slot = g_posCount++; if(!IsValidIndex(slot, ...)) { g_posCount--; return; }
                                    if re.search(rf'{index_var}\s*=\s*\w+\+\+', prev_lines) and \
                                       re.search(rf'IsValidIndex\s*\(\s*{index_var}', prev_lines):
                                        found_bounds_check = True
                                
                                # Pattern 7: Check for if(index_var < size_var) wrapping array access
                                # This handles: if(m_cluster_count < clusters_size) { ... m_clusters[m_cluster_count] ... }
                                if not found_bounds_check:
                                    # Look for pattern: if(index_var < size_var) where size_var relates to array_name
                                    # Common patterns: clusters_size for m_clusters, array_size for array, etc.
                                    size_var_patterns = [
                                        f'{array_name}_size',  # exact match: m_clusters_size
                                        f'{array_name.lstrip("m_")}_size',  # without m_ prefix
                                        'size',  # generic size variable
                                        'Size',  # capitalized
                                        rf'\w+_size',  # any *_size variable
                                    ]
                                    for size_pattern in size_var_patterns:
                                        # Check for: if(index_var < size_var)
                                        if re.search(rf'if\s*\(\s*{index_var}\s*<\s*{size_pattern}\s*\)', context_str):
                                            found_bounds_check = True
                                            break

                                # Pattern 8: Counter guard - if(cnt < N) { arr[cnt] = x; cnt++; }
                                # The guard cnt < N ensures arr[cnt] is valid for fixed-size array of N
                                if not found_bounds_check:
                                    # Check for if(index_var < constant) in recent context
                                    if re.search(rf'if\s*\([^)]*{index_var}\s*<\s*\d+', context_str):
                                        found_bounds_check = True
                                    # Also check with && in the condition
                                    elif re.search(rf'&&\s*{index_var}\s*<\s*\d+', context_str):
                                        found_bounds_check = True

                                # Pattern 8b: Index from validated function - if(idx >= 0 && array[idx].something)
                                # This pattern is used when idx comes from FindXxxIndex() which returns -1 on failure
                                if not found_bounds_check:
                                    # Look for if(index_var >= 0 && ...) in recent context
                                    if re.search(rf'if\s*\(\s*{index_var}\s*>=\s*0\s*&&', context_str):
                                        found_bounds_check = True
                                    # Also: if(idx >= 0) { ... access idx ... }
                                    elif re.search(rf'if\s*\(\s*{index_var}\s*>=\s*0\s*\)', context_str):
                                        found_bounds_check = True

                                # Pattern 9: Offset guard - if(base + max_offset < size) { arr[base + 0..max_offset] }
                                # e.g., if(startIdx + 8 < size) { features[startIdx + 0] = ...; }
                                if not found_bounds_check:
                                    # Check if index_expr contains addition like "startIdx + N"
                                    offset_match = re.match(r'(\w+)\s*\+\s*(\d+)', index_expr)
                                    if offset_match:
                                        base_var = offset_match.group(1)
                                        offset_val = int(offset_match.group(2))
                                        # Look for guard: if(base_var + max_offset < size)
                                        # where max_offset >= offset_val
                                        guard_pattern = rf'if\s*\(\s*{base_var}\s*\+\s*(\d+)\s*<\s*\w+'
                                        guard_match = re.search(guard_pattern, context_str)
                                        if guard_match:
                                            max_offset = int(guard_match.group(1))
                                            if offset_val <= max_offset:
                                                found_bounds_check = True

                                # Pattern 10: Bubble sort inner loop - for(j = 0; j < count - i - 1; j++) arr[j], arr[j+1]
                                # Both j and j+1 are bounded by the loop condition
                                if not found_bounds_check:
                                    # Extended lookback for nested loops (bubble sort inner loop may be far from outer)
                                    ext_context = '\n'.join(lines[max(0, i-50):i])
                                    # Check for nested loop pattern with j+1 in index
                                    if '+' in index_expr and '1' in index_expr:
                                        # Extract base var (j from j+1)
                                        base_idx = index_var.replace('+1', '').replace('+ 1', '').strip()
                                        # Look for for(j < count - ... - 1) pattern - flexible format
                                        if re.search(rf'for\s*\([^;]*\b{base_idx}\b[^;]*;[^;]*\b{base_idx}\b\s*<[^;]*-\s*1\s*;', ext_context):
                                            found_bounds_check = True
                                    # Also check simple j in bubble sort (j < count - i - 1)
                                    if re.search(rf'for\s*\([^;]*\b{index_var}\b[^;]*;[^;]*\b{index_var}\b\s*<[^;]*-\s*\w+\s*-\s*1\s*;', ext_context):
                                        found_bounds_check = True
                                    # Bubble sort comment indicates safe pattern
                                    if re.search(r'bubble\s*sort', ext_context, re.IGNORECASE):
                                        if '+1' in index_expr or '+ 1' in index_expr:
                                            found_bounds_check = True

                                # Pattern 11: Ring buffer with capacity check - if(count >= SIZE) return; ... items[tail]
                                # The capacity check ensures tail is always within bounds
                                if not found_bounds_check:
                                    # Look for capacity check pattern protecting this function
                                    capacity_check = re.search(rf'if\s*\(\s*\w+\s*>=\s*\w+_SIZE\s*\)\s*return', context_str) or \
                                                    re.search(rf'if\s*\(\s*count\s*>=\s*\w+\s*\)\s*return', context_str)
                                    if capacity_check:
                                        # Index is a queue pointer (head, tail) or counter (count, cnt, idx)
                                        queue_idx = re.search(r'\b(head|tail|front|rear|ptr|idx|pos)\b', index_var, re.IGNORECASE)
                                        if queue_idx:
                                            found_bounds_check = True
                                        # Also look ahead for modulo wrap: idx = (idx + 1) % SIZE
                                        lookahead = '\n'.join(lines[i:min(i+10, len(lines))])
                                        if re.search(rf'{index_var}\s*=\s*\([^)]+\)\s*%', lookahead):
                                            found_bounds_check = True
                                    # Pattern: if(bufferSize > 0) { idx = head; buffer[idx] = x; head = (head+1) % size; }
                                    if re.search(rf'if\s*\(\s*\w*[Ss]ize\s*>\s*0\s*\)', context_str):
                                        # Check if idx assigned from head/tail before access
                                        if re.search(rf'{index_var}\s*=\s*\w*[Hh]ead', context_str) or \
                                           re.search(rf'{index_var}\s*=\s*\w*[Tt]ail', context_str):
                                            found_bounds_check = True

                                # Pattern 12: Capacity guard then access at count index
                                # e.g., if(m_symbolCount >= MAX_SYMBOLS) return; ... arr[m_symbolCount] = x; count++;
                                if not found_bounds_check:
                                    # Look for capacity check on the index variable (or related Count var)
                                    idx_count = index_var.replace('m_', '').replace('g_', '')  # Normalize
                                    cap_patterns = [
                                        rf'if\s*\(\s*{index_var}\s*>=\s*\w+\s*\)\s*return',
                                        rf'if\s*\(\s*{index_var}\s*>=\s*MAX_',
                                        rf'if\s*\(\s*\w*[Cc]ount\s*>=\s*\w+\s*\)\s*return',
                                        rf'if\s*\(\s*\w*[Cc]ount\s*>=\s*MAX_',
                                        # Pattern: if(count < ArraySize(arr)) { arr[count] = x; }
                                        rf'if\s*\(\s*{index_var}\s*<\s*ArraySize\s*\(\s*{array_name}\s*\)',
                                    ]
                                    for cap_pat in cap_patterns:
                                        if re.search(cap_pat, context_str):
                                            found_bounds_check = True
                                            break

                                # Pattern 13: Array shift pattern - returns[count - 1] after shift loop
                                # for(i = 0; i < count - 1; i++) arr[i] = arr[i+1]; arr[count-1] = x;
                                if not found_bounds_check:
                                    if re.search(r'-\s*1\s*\]', index_expr):  # Index like count-1
                                        # Look for shift loop before
                                        if re.search(r'for\s*\([^)]*<\s*\w+\s*-\s*1\s*;[^)]*\)\s*\w+\[\w+\]\s*=\s*\w+\[\w+\s*\+\s*1\]', context_str):
                                            found_bounds_check = True
                                        # Or simpler: if count > 0 implied by shift logic
                                        if re.search(r'Shift|shift|// Shift', context_str):
                                            found_bounds_check = True
                                        # Pattern: else block after if(count < ArraySize) - we're at full capacity
                                        if re.search(rf'if\s*\(\s*{index_var.replace("-1", "").replace("- 1", "").strip()}\s*<\s*ArraySize\s*\(', context_str):
                                            if re.search(r'\belse\b', context_str):
                                                found_bounds_check = True

                                # Pattern 14: Post-increment assignment from bounded counter
                                # for(...; count < MAX; ...) { idx = count++; arr[idx] = x; }
                                if not found_bounds_check:
                                    ext_context = '\n'.join(lines[max(0, i-50):i])
                                    # Check if idx was assigned from a post-increment
                                    assign_match = re.search(rf'{index_var}\s*=\s*(\w+)\s*\+\+', ext_context)
                                    if assign_match:
                                        counter_var = assign_match.group(1)
                                        # Look for loop bounding that counter
                                        if re.search(rf'for\s*\([^;]*;[^;]*{counter_var}\s*<\s*\w+', ext_context) or \
                                           re.search(rf'while\s*\([^)]*{counter_var}\s*<\s*\w+', ext_context):
                                            found_bounds_check = True

                                # Pattern 15: Direct use of loop-bounded counter - for(... && count < MAX) arr[count]++
                                if not found_bounds_check:
                                    ext_context = '\n'.join(lines[max(0, i-30):i])
                                    # Direct loop bound on the index variable
                                    if re.search(rf'for\s*\([^)]*{index_var}\s*<\s*\w+', ext_context) or \
                                       re.search(rf'&&\s*{index_var}\s*<\s*\w+', ext_context):
                                        found_bounds_check = True
                                    # Common pattern: rankCount < MAX_SYMBOLS in loop, arr[rankCount]
                                    if re.search(rf'[Cc]ount\s*<\s*MAX_', ext_context) and 'Count' in index_var:
                                        found_bounds_check = True
                                
                                if found_bounds_check:
                                    continue
                        
                        # Special handling for NUM001 - check for denominator validation
                        if rule.get('check_denominator_validation', False):
                            # Extract the denominator variable from the division
                            match = pattern.search(line)
                            if match:
                                denominator = match.group(1).strip()
                                found_validation = False

                                # Pattern 1: Ternary guard on the SAME LINE
                                # e.g., (atr > 0) ? x / atr : 0  OR  denom > 0 ? num / denom : default
                                if re.search(rf'\(\s*{denominator}\s*[>!]=?\s*0\s*\)\s*\?[^:]*/', line) or \
                                   re.search(rf'{denominator}\s*[>!]=?\s*0\s*\?[^:]*/', line):
                                    found_validation = True

                                # Pattern 2: Check same line for conditional like if(x > 0) or (x != 0)
                                if not found_validation:
                                    if re.search(rf'\b{denominator}\s*[>!]=?\s*0', line):
                                        found_validation = True

                                # Pattern 3: Look back up to 30 lines for validation of this denominator
                                if not found_validation:
                                    context_start = max(0, i - 30)
                                    for ctx_line in lines[context_start:i]:
                                        # Check for various validation patterns:
                                        # if(denominator != 0), if(MathAbs(denominator) < epsilon), etc.
                                        if re.search(rf'\b{denominator}\b.*[<>!=]', ctx_line) and \
                                           ('if' in ctx_line or 'return' in ctx_line):
                                            found_validation = True
                                            break
                                        # Pattern: if(MathAbs(denominator) < epsilon) return;
                                        if re.search(rf'if\s*\(\s*MathAbs\s*\(\s*{denominator}\s*\)\s*<', ctx_line) and 'return' in ctx_line:
                                            found_validation = True
                                            break
                                        # Check if denominator was assigned from SafeDiv or similar
                                        if re.search(rf'{denominator}\s*=.*Safe', ctx_line):
                                            found_validation = True
                                            break
                                        # Check for early return on invalid denominator
                                        if re.search(rf'if\s*\(\s*{denominator}\s*<=\s*0\s*\)\s*return', ctx_line):
                                            found_validation = True
                                            break
                                        # Check for fallback assignment: if(x <= 0) x = default
                                        if re.search(rf'if\s*\(\s*{denominator}\s*<=\s*0\s*\)\s*{denominator}\s*=', ctx_line):
                                            found_validation = True
                                            break

                                if found_validation:
                                    continue

                        # Special handling for EXEC002 - check if within a normalizer function
                        if rule.get('check_normalizer_context', False):
                            # Look back to find the enclosing function
                            func_start = max(0, i - 100)
                            in_normalizer = False
                            for j in range(i - 1, func_start, -1):
                                func_line = lines[j]
                                # Check if this is a function that normalizes lots
                                if re.search(r'(?:double|void)\s+(?:Normalize|Calculate|Compute|Get\w*)?(?:Lot|Volume|Position)', func_line, re.IGNORECASE):
                                    in_normalizer = True
                                    break
                                # Check for function name containing "normaliz" or "lotsize"
                                if re.search(r'(?:double|void)\s+\w*(?:normaliz|lotsize|positionsize)\w*\s*\(', func_line, re.IGNORECASE):
                                    in_normalizer = True
                                    break
                                # Stop if we hit another function definition
                                if re.match(r'\s*(?:void|int|double|bool|string|long|datetime)\s+\w+\s*\([^)]*\)\s*$', func_line):
                                    break
                            if in_normalizer:
                                continue

                        # Context check if needed
                        if 'context_pattern' in rule:
                            context_pattern = re.compile(rule['context_pattern'])
                            context_start = max(0, i - 10)
                            context = '\n'.join(lines[context_start:i+5])
                            if not context_pattern.search(context):
                                continue

                        # Special handling for rules that need function body analysis
                        if rule.get('check_function_body', False):
                            # First check if this is a class method (not main event handler)
                            # Look back up to 200 lines to find enclosing class
                            context_back = '\n'.join(lines[max(0, i-200):i])
                            if re.search(r'^\s*class\s+\w+', context_back, re.MULTILINE):
                                # If OnTick inside a class, it's a method not main event handler
                                continue

                            # Look ahead 100 lines in the function body
                            func_body = '\n'.join(lines[i:min(i+100, len(lines))])

                            # RISK002: Check for drawdown patterns
                            if rule_id == 'RISK002':
                                drawdown_patterns = [
                                    r'IsDrawdownExceeded',
                                    r'drawdown\s*>',
                                    r'g_breaker',
                                    r'CircuitBreaker',
                                    r'CanTrade',
                                    r'breaker\.Update',
                                    r'Drawdown.*return',
                                ]
                                found_check = False
                                for dp in drawdown_patterns:
                                    if re.search(dp, func_body, re.IGNORECASE):
                                        found_check = True
                                        break
                                if found_check:
                                    continue

                            # DATA005: Check for warmup/calibration patterns
                            if rule_id == 'DATA005':
                                warmup_patterns = [
                                    r'warmup',
                                    r'WarmUp',
                                    r'calibrat',
                                    r'Calibration',
                                    r'tickCount\s*<',
                                    r'InpCalibrationTicks',
                                    r'warmupComplete',
                                    r'!initialized',
                                    r'prev_calculated',
                                ]
                                found_check = False
                                for wp in warmup_patterns:
                                    if re.search(wp, func_body, re.IGNORECASE):
                                        found_check = True
                                        break
                                if found_check:
                                    continue

                        # Special handling for DATA010 - check loop body for bounded iteration
                        if rule.get('check_loop_body', False):
                            # Look ahead 10 lines in the loop body
                            loop_body = '\n'.join(lines[i:min(i+10, len(lines))])
                            bounded_patterns = [
                                r'priority|Priority',
                                r'initialized',
                                r'typeAllowed',
                                r'warmup|Warmup',
                                r'ShouldUpdate',
                                r'continue',  # Early continue means bounded iteration
                            ]
                            found_bounded = False
                            for bp in bounded_patterns:
                                if re.search(bp, loop_body):
                                    found_bounded = True
                                    break
                            if found_bounded:
                                continue

                        # Special handling for DATA003 - check if file handle was validated earlier
                        if rule.get('check_validated_handle', False):
                            # Look back up to 50 lines for handle validation
                            context_start = max(0, i - 50)
                            context = '\n'.join(lines[context_start:i])
                            # Pattern: handle = FileOpen(...); if(handle == INVALID_HANDLE) return;
                            # If we find this pattern, the file operations after it are safe
                            handle_validated = False
                            if re.search(r'FileOpen\s*\([^)]+\)', context):
                                if re.search(r'if\s*\(\s*\w+\s*==\s*INVALID_HANDLE\s*\)', context) or \
                                   re.search(r'if\s*\(\s*handle\s*==\s*INVALID_HANDLE\s*\)', context) or \
                                   re.search(r'INVALID_HANDLE\s*\)\s*return', context):
                                    handle_validated = True
                            if handle_validated:
                                continue

                        # Special handling for DATA001 - check if file has ValidateInputParameters
                        if rule.get('check_file_for_validation', False):
                            # Check if the entire file content has input validation
                            if re.search(r'ValidateInputParameters|ValidateInput|InputValidation', content):
                                continue

                        # Special handling for DATA002 - check if inside a safe validation function
                        if rule.get('check_in_safe_function', False):
                            # Look back to find enclosing function
                            context_back = '\n'.join(lines[max(0, i-30):i])
                            if re.search(r'GetSafeOHLCV|SafeOHLCV|IsValid|HasPriceGap|ValidateData', context_back):
                                continue

                        try:
                            rel_file = str(file_path.relative_to(self.project_root))
                        except ValueError:
                            rel_file = str(file_path)

                        finding = AuditFinding(
                            file=rel_file,
                            line=i,
                            category=rule['category'],
                            severity=rule['severity'],
                            rule_id=rule_id,
                            title=rule['title'],
                            description=rule['description'],
                            recommendation=rule['recommendation'],
                            code_context=line.strip()[:100]
                        )
                        findings.append(finding)

        return findings

    def _init_impact_analyzer(self):
        """Initialize impact analyzer for severity weighting"""
        if not self._use_impact_scoring:
            return

        try:
            # Import the impact analyzer
            import sys
            sys.path.insert(0, str(self.project_root / "Tools"))
            from mql5_impact_analyzer import MQL5ImpactAnalyzer

            self._impact_analyzer = MQL5ImpactAnalyzer(self.project_root)
            report = self._impact_analyzer.analyze()

            if report is None:
                logger.warning("Impact analyzer returned no report")
                self._use_impact_scoring = False
                return

            # Build impact scores from file metrics
            for file_data in report.get('top_impact_files', []):
                path = file_data.get('path')
                if not path:
                    continue
                # Normalize impact to 1.0 - 3.0 range
                impact = file_data.get('impact_score', 0)
                # Use log scale to prevent extreme values
                import math
                try:
                    normalized = 1.0 + min(2.0, math.log10(max(1, impact)) / 3)
                except (ValueError, ZeroDivisionError):
                    normalized = 1.0
                self._impact_scores[path] = normalized

            logger.info(f"Impact analysis: {len(self._impact_scores)} files scored")
        except ImportError:
            logger.info("Impact analyzer module not available, using default scoring")
            self._use_impact_scoring = False
        except Exception as e:
            logger.warning(f"Impact analysis unavailable: {e}")
            self._use_impact_scoring = False

    def audit_project(self) -> Dict:
        """Audit entire project"""
        logger.info(f"Starting financial audit of {self.project_root}")

        # Initialize impact analyzer for severity weighting
        self._init_impact_analyzer()

        # Find all MQL5 files
        mql5_dir = self.project_root / "MQL5"
        files = []
        files_with_errors = 0

        try:
            if mql5_dir.exists():
                try:
                    files.extend(mql5_dir.rglob("*.mqh"))
                except (OSError, PermissionError) as e:
                    logger.warning(f"Error scanning for .mqh files: {e}")
                try:
                    files.extend(mql5_dir.rglob("*.mq5"))
                except (OSError, PermissionError) as e:
                    logger.warning(f"Error scanning for .mq5 files: {e}")
                files = [f for f in files if '.backup' not in str(f)]
            else:
                logger.warning(f"MQL5 directory not found: {mql5_dir}")
        except (OSError, PermissionError) as e:
            logger.error(f"Cannot access MQL5 directory: {e}")

        if not files:
            logger.warning("No MQL5 files found to audit")

        logger.info(f"Found {len(files)} files to audit")

        # Audit each file
        all_findings = []
        for file_path in files:
            try:
                findings = self.audit_file(file_path)
                all_findings.extend(findings)
                if findings:
                    logger.info(f"  {file_path.name}: {len(findings)} findings")
            except Exception as e:
                files_with_errors += 1
                logger.error(f"Error auditing '{file_path}': {e}")

        if files_with_errors > 0:
            logger.warning(f"{files_with_errors} file(s) could not be audited")

        self.findings = all_findings

        # Generate summary
        summary = self._generate_summary()
        return summary

    def _generate_summary(self) -> Dict:
        """Generate audit summary"""
        by_category = defaultdict(list)
        by_severity = defaultdict(list)
        by_file = defaultdict(list)

        for finding in self.findings:
            by_category[finding.category.value].append(finding)
            by_severity[finding.severity.name].append(finding)
            by_file[finding.file].append(finding)

        # Calculate weighted severity scores per file
        file_weighted_scores = {}
        for file_path, findings in by_file.items():
            impact_multiplier = self._impact_scores.get(file_path, 1.0)
            weighted_score = sum(
                (6 - f.severity.value) * impact_multiplier  # Higher for CRITICAL
                for f in findings
            )
            file_weighted_scores[file_path] = round(weighted_score, 1)

        return {
            'timestamp': datetime.now().isoformat(),
            'project': str(self.project_root),
            'total_findings': len(self.findings),
            'by_category': {k: len(v) for k, v in by_category.items()},
            'by_severity': {k: len(v) for k, v in by_severity.items()},
            'by_file': {k: len(v) for k, v in sorted(by_file.items(),
                                                     key=lambda x: len(x[1]),
                                                     reverse=True)[:20]},
            'weighted_by_file': dict(sorted(file_weighted_scores.items(),
                                           key=lambda x: x[1],
                                           reverse=True)[:20]),
            'impact_scores': self._impact_scores,
            'critical_count': len(by_severity.get('CRITICAL', [])),
            'high_count': len(by_severity.get('HIGH', [])),
            'file_hashes': self.file_hashes
        }

    def print_report(self):
        """Print detailed audit report"""
        summary = self._generate_summary()

        print("\n" + "=" * 70)
        print("FINANCIAL CODE AUDIT REPORT")
        print("=" * 70)
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Project:   {summary['project']}")
        print("-" * 70)
        print(f"Total Findings: {summary['total_findings']}")
        print(f"  CRITICAL: {summary['critical_count']}")
        print(f"  HIGH:     {summary['high_count']}")
        print("-" * 70)

        print("\nFindings by Category:")
        for cat, count in sorted(summary['by_category'].items()):
            print(f"  {cat:30} : {count}")

        print("\nFindings by Severity:")
        for sev, count in sorted(summary['by_severity'].items()):
            print(f"  {sev:12} : {count}")

        print("\nTop Files by Finding Count:")
        for file, count in list(summary['by_file'].items())[:10]:
            print(f"  {count:3} : {file}")

        if summary.get('weighted_by_file'):
            print("\nTop Files by Weighted Impact Score:")
            print("  (Score = Findings * Severity * Impact Multiplier)")
            for file, score in list(summary['weighted_by_file'].items())[:10]:
                impact = summary.get('impact_scores', {}).get(file, 1.0)
                from pathlib import Path
                fname = Path(file).name
                print(f"  {score:6.1f} : {fname} (impact: {impact:.2f}x)")

        # Print critical findings
        critical = [f for f in self.findings if f.severity == Severity.CRITICAL]
        if critical:
            print("\n" + "=" * 70)
            print(f"CRITICAL FINDINGS (Must Fix) - {len(critical)} total")
            print("=" * 70)
            
            # Group by file for better readability
            from collections import defaultdict
            by_file = defaultdict(list)
            for f in critical:
                by_file[f.file].append(f)
            
            # Print summary by file
            print("\nCRITICAL Violations by File:")
            for file_path, findings in sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True):
                from pathlib import Path
                fname = Path(file_path).name
                print(f"  {len(findings):3d} : {fname}")
            
            # Print detailed findings (with optional limit)
            display_limit = self._display_limit if hasattr(self, '_display_limit') and self._display_limit else len(critical)
            print(f"\nDetailed CRITICAL Findings (showing {min(display_limit, len(critical))} of {len(critical)}):\n")
            for i, f in enumerate(critical[:display_limit], 1):
                print(f"[{i}/{len(critical)}] [{f.rule_id}] {f.title}")
                print(f"  File: {f.file}:{f.line}")
                print(f"  Code: {f.code_context}")
                print(f"  Fix:  {f.recommendation}")
                print()

        print("\n" + "=" * 70)

    def save_report(self, output_path: Path):
        """Save detailed report to JSON"""
        report = {
            'summary': self._generate_summary(),
            'findings': [
                {
                    'file': f.file,
                    'line': f.line,
                    'category': f.category.value,
                    'severity': f.severity.name,
                    'rule_id': f.rule_id,
                    'title': f.title,
                    'description': f.description,
                    'recommendation': f.recommendation,
                    'code_context': f.code_context
                }
                for f in self.findings
            ]
        }

        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_path}")
        except PermissionError:
            logger.error(f"Permission denied writing to: {output_path}")
            raise
        except (IOError, OSError) as e:
            logger.error(f"Failed to save report to '{output_path}': {e}")
            raise
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize report to JSON: {e}")
            raise


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Financial-grade MQL5 Code Auditor'
    )
    parser.add_argument('--project', type=Path, default=Path('.'))
    parser.add_argument('--output', type=Path, help='Save report to JSON')
    parser.add_argument('--critical-only', action='store_true', help='Show only CRITICAL severity')
    parser.add_argument('--limit', type=int, help='Limit number of detailed findings to display')

    args = parser.parse_args()

    # Validate project path
    try:
        project_path = args.project.resolve()
    except (OSError, ValueError) as e:
        logger.error(f"Invalid project path '{args.project}': {e}")
        return 2

    if not project_path.exists():
        logger.error(f"Project directory does not exist: {project_path}")
        return 2
    if not project_path.is_dir():
        logger.error(f"Project path is not a directory: {project_path}")
        return 2

    try:
        auditor = FinancialCodeAuditor(project_path)
        auditor.audit_project()

        # If limit specified, temporarily modify print_report to use it
        if args.limit:
            auditor._display_limit = args.limit

        auditor.print_report()

        if args.output:
            try:
                auditor.save_report(args.output)
            except (PermissionError, IOError, OSError) as e:
                logger.error(f"Failed to save report: {e}")
                return 2

        # Exit with error if critical issues
        critical_count = len([f for f in auditor.findings
                              if f.severity == Severity.CRITICAL])
        return 1 if critical_count > 0 else 0

    except KeyboardInterrupt:
        logger.info("Audit interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error during audit: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
