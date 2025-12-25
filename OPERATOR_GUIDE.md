# VelocityTrader v7.1 - Operator Quick Reference

**Version:** 7.1  
**For:** Daily Operations and Monitoring

---

## Daily Checklist

### Morning Routine (Pre-Market or Market Open)

- [ ] Check MT5 terminal is running
- [ ] Verify EA is loaded and AutoTrading enabled
- [ ] Review overnight P&L
- [ ] Check circuit breaker state (should be LIVE or PENDING)
- [ ] Verify current drawdown < 5%
- [ ] Check log file for errors
- [ ] Review open positions count
- [ ] Confirm internet connection stable

### Mid-Day Check

- [ ] Review current trades
- [ ] Check drawdown status
- [ ] Verify win rate (last 20 trades)
- [ ] Monitor regime detection
- [ ] Check for WARNING entries in log

### Evening Routine (Market Close or EOD)

- [ ] Review daily P&L
- [ ] Check total trades executed
- [ ] Verify state file saved
- [ ] Review circuit breaker triggers (if any)
- [ ] Check agent performance comparison
- [ ] Export daily statement
- [ ] Document any anomalies

---

## HUD Dashboard Guide

### Tab Navigation
- Press **1-6** or **Tab** to switch between tabs
- **1 = DASH** - Main dashboard
- **2 = PERF** - Performance metrics
- **3 = RL** - Reinforcement learning stats
- **4 = PROB** - Probability predictor
- **5 = RISK** - Risk management
- **6 = INST** - Instrument rankings

### DASH Tab - Main Dashboard

```
┌─────────────────────────────────────┐
│ VelocityTrader v7.1 [LIVE]          │
├─────────────────────────────────────┤
│ Balance:  $10,500.00                │
│ Equity:   $10,450.00                │
│ P&L:      +$450.00 (+4.5%)          │
│ DD:       -0.5% (Max: -2.3%)        │
├─────────────────────────────────────┤
│ SNIPER   [REAL] 2W-1L  PF:2.1       │
│ BERSERKER[REAL] 3W-2L  PF:1.5       │
├─────────────────────────────────────┤
│ Regime: TREND    Chi: 0.85          │
│ Positions: 2/5                      │
└─────────────────────────────────────┘
```

**Key Indicators:**
- **State [LIVE]**: System operational (good)
- **State [HALTED]**: Circuit breaker triggered (investigate!)
- **DD**: Current drawdown percentage
- **PF**: Profit Factor (>1.0 is winning)

### RISK Tab - Circuit Breaker Status

```
┌─────────────────────────────────────┐
│ CIRCUIT BREAKER STATUS              │
├─────────────────────────────────────┤
│ State: LIVE ✓                       │
│ Daily Loss: -1.2% / -3.0% limit     │
│ Drawdown:   -2.1% / -10.0% limit    │
│ Consec Loss: 2 / 5 limit            │
│ Win Rate:   55% / 45% minimum       │
└─────────────────────────────────────┘
```

**Safe Operating Range:**
- Daily Loss: < -2.5%
- Drawdown: < -8%
- Consecutive Losses: < 4
- Win Rate: > 48%

---

## Circuit Breaker States

### LIVE (Green - Normal Operation)
- **Meaning**: System trading normally
- **Action**: Monitor as usual
- **Risk**: Low

### PENDING (Yellow - Cautionary)
- **Meaning**: Approaching limits, trading cautiously
- **Action**: Monitor closely, review recent trades
- **Risk**: Medium

### HALTED (Red - Trading Stopped)
- **Meaning**: Risk limit exceeded, no new trades
- **Action**: INVESTIGATE IMMEDIATELY
- **Risk**: High
- **Recovery**: 60-min cooldown, then RETRAINING

### RETRAINING (Orange - Recovery Mode)
- **Meaning**: System adapting after halt
- **Action**: Monitor convergence, no manual intervention
- **Risk**: Medium
- **Duration**: Until criteria met (typically 30+ trades)

---

## Common Scenarios & Actions

### Scenario 1: Circuit Breaker HALTED

**Symptoms:**
- State shows HALTED
- No new trades opening
- HUD shows red indicators

**Actions:**
1. **DO NOT** manually restart or reset
2. Check what triggered halt:
   - Daily loss exceeded?
   - Drawdown too high?
   - Consecutive losses?
3. Review recent trades for patterns
4. Wait for 60-min cooldown
5. System will enter RETRAINING automatically
6. Monitor RETRAINING phase closely
7. Document incident for review

**When to Intervene:**
- If HALTED persists > 4 hours: Check logs
- If drawdown > 12%: Consider stopping EA
- If repeated halts: Review parameters

### Scenario 2: Drawdown Increasing

**Early Warning (DD: -3% to -5%):**
- Monitor more frequently (hourly)
- Check regime distribution
- Review agent performance
- Verify circuit breaker armed

**Caution Zone (DD: -5% to -8%):**
- Check every 30 minutes
- Review Q-value trends
- Verify no system errors
- Be ready to intervene

**Danger Zone (DD: -8% to -10%):**
- Constant monitoring
- Review all open positions
- Consider manual close if appropriate
- Prepare incident report

**Critical (DD: > -10%):**
- Circuit breaker should trigger
- If not: MANUAL INTERVENTION REQUIRED
- Close all positions
- Disable AutoTrading
- Investigate immediately

### Scenario 3: Win Rate Declining

**Minor Decline (52% → 48%):**
- Normal variance
- Continue monitoring
- Check over larger sample

**Significant Decline (52% → 42%):**
- Review regime detection
- Check if market conditions changed
- Verify Q-values updating
- May need retraining period

**Critical Decline (<40%):**
- System may enter RETRAINING
- Review logs for errors
- Check if parameters need adjustment
- Consider reducing risk

### Scenario 4: No Trades for Extended Period

**Normal:**
- Low volatility periods
- Regime in CRITICAL state
- Waiting for high-conviction setups

**Investigate if:**
- No trades > 8 hours during active market
- Circuit breaker not in HALTED
- HUD shows active regime

**Possible Causes:**
- Signal thresholds too high
- Regime stuck in CALIBRATING
- Statistical gate blocking trades
- Physics engine data issue

**Actions:**
- Check HUD regime status
- Review probability predictor
- Verify spread not excessive
- Check logs for gate rejections

### Scenario 5: Excessive Trading

**Warning Signs:**
- >10 trades per day
- Multiple positions same symbol
- Rapid open/close cycles

**Possible Causes:**
- Berserker too aggressive
- Q-values not converged
- Regime oscillating
- Parameter misconfiguration

**Actions:**
- Check InpBerserkerThreshold
- Review regime stability
- Verify not in RETRAINING
- Consider increasing thresholds

---

## Warning Signs & Red Flags

### Immediate Action Required ⚠️

| Warning Sign | Severity | Action |
|-------------|----------|--------|
| Drawdown > 10% | CRITICAL | Disable EA, investigate |
| EA crashed | CRITICAL | Restart carefully, review logs |
| Circuit breaker not triggering | CRITICAL | Manual intervention, stop trading |
| Positions > configured max | CRITICAL | Close excess, fix bug |
| Win rate < 35% sustained | HIGH | Enter RETRAINING or stop |

### Monitor Closely 👁️

| Warning Sign | Severity | Action |
|-------------|----------|--------|
| Drawdown 5-8% | HIGH | Hourly monitoring |
| Win rate 40-45% | MEDIUM | Review strategy |
| Consecutive losses 4+ | MEDIUM | Watch for halt |
| Daily loss 2-3% | MEDIUM | Monitor closely |
| Regime stuck CRITICAL | LOW | Check physics engine |

### Normal Variance ✓

| Observation | Status | Notes |
|------------|--------|-------|
| Drawdown 0-3% | NORMAL | Expected variation |
| Win rate 48-55% | NORMAL | Statistical range |
| 1-3 consecutive losses | NORMAL | Part of trading |
| Daily loss 0-1.5% | NORMAL | Within limits |
| Regime changes | NORMAL | Market adaptation |

---

## Key Metrics Reference

### Profit Factor (PF)
- **> 2.0**: Excellent performance
- **1.5 - 2.0**: Good performance
- **1.2 - 1.5**: Acceptable performance
- **1.0 - 1.2**: Marginal (review needed)
- **< 1.0**: Losing (action required)

### Win Rate
- **> 55%**: Above expectation
- **50 - 55%**: Expected range
- **45 - 50%**: Acceptable with good PF
- **< 45%**: Below expectation (investigate)

### Drawdown
- **0 - 3%**: Excellent control
- **3 - 5%**: Normal trading
- **5 - 8%**: Elevated risk (monitor)
- **8 - 10%**: High risk (prepare intervention)
- **> 10%**: Circuit breaker territory

### Sharpe Ratio
- **> 2.0**: Outstanding
- **1.5 - 2.0**: Very good
- **1.0 - 1.5**: Good
- **0.5 - 1.0**: Fair
- **< 0.5**: Poor risk/reward

---

## Log File Locations

```
[MT5 Data Folder]/MQL5/Files/
├── VelDuel_[MagicNumber].bin      # State persistence
├── VelDuel_[MagicNumber]_backup.bin  # Backup state
├── VT_TradeLog_[Date].csv         # Trade history
├── VT_MarkedCandles_[Symbol].json # Trade markers
└── Logs/
    └── VelTrader_[Date].log       # System log
```

**Daily Review Files:**
- State file: Check modified timestamp is recent
- Trade log: Review all trades
- System log: Check for ERROR/WARNING

---

## Quick Commands

### MetaTrader 5 Terminal

| Action | Method |
|--------|--------|
| Enable AutoTrading | Click "AutoTrading" button or Alt+A |
| Disable AutoTrading | Click "AutoTrading" button or Alt+A |
| Open Strategy Tester | Ctrl+R |
| Open Navigator | Ctrl+N |
| Open Journal | Ctrl+J |

### HUD Dashboard

| Action | Key |
|--------|-----|
| Switch to DASH tab | 1 |
| Switch to PERF tab | 2 |
| Switch to RL tab | 3 |
| Switch to PROB tab | 4 |
| Switch to RISK tab | 5 |
| Switch to INST tab | 6 |
| Cycle tabs | Tab |

---

## Emergency Contacts

**System Issues:**
- Check documentation: README.md
- Review troubleshooting: TESTING_DEPLOYMENT_GUIDE.md
- Production status: PRODUCTION_READINESS.md

**Critical Incidents:**
1. Stop EA (disable AutoTrading)
2. Document issue (screenshots, logs)
3. Review recent changes
4. Escalate if safety concern

---

## Performance Reporting

### Daily Report Template

```
Date: [YYYY-MM-DD]
Operator: [Name]

Summary:
- Starting Balance: $X,XXX.XX
- Ending Balance: $X,XXX.XX
- P&L: $±XXX.XX (±X.X%)
- Trades: X
- Win Rate: XX%
- Max DD: -X.X%

Circuit Breaker:
- State: [LIVE/PENDING/HALTED/RETRAINING]
- Triggers: [None/List any]

Agents:
- Sniper: XW-XL, PF:X.X
- Berserker: XW-XL, PF:X.X

Issues/Notes:
- [Any anomalies or observations]

Actions Taken:
- [Any interventions or adjustments]
```

### Weekly Report Template

```
Week: [Date Range]

Performance:
- Net P&L: $±XXX.XX
- ROI: ±X.X%
- Total Trades: XX
- Win Rate: XX%
- Profit Factor: X.X
- Max Drawdown: -X.X%
- Sharpe Ratio: X.X

Agent Comparison:
- Sniper: [Stats]
- Berserker: [Stats]
- Swaps: X times

Circuit Breaker Events:
- HALTED: X times
- RETRAINING: X times
- Reasons: [Summary]

Regime Distribution:
- BREAKOUT: XX%
- TREND: XX%
- MEANREV: XX%

Summary & Outlook:
[Brief analysis and forward-looking notes]
```

---

## Troubleshooting Quick Reference

| Problem | Quick Fix |
|---------|-----------|
| EA not loading | Check file in Experts folder, recompile |
| No trades | Check AutoTrading enabled, verify signals |
| HUD not showing | Check allow DLL imports, restart EA |
| State not saving | Check disk space, file permissions |
| Excessive drawdown | Verify circuit breaker, reduce risk |
| Circuit breaker stuck | Wait cooldown, check logs, may need reset |
| Regime stuck | Check physics engine, verify tick data |
| Low win rate | Normal variance or retraining needed |

---

**Document Version:** 1.0  
**Last Updated:** 2024-12-24  
**Keep this guide accessible during operations**
