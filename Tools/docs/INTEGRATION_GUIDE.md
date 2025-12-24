# ProjectQuantum v2.1 - Integration Guide

## Manual Integration Required

Due to the complexity of the codebase, some enhancements require manual integration to ensure no regressions. Follow these steps carefully:

### Step 1: Backup Current System

```bash
# Backup your current ProjectQuantum files
cp -r [MT5]/MQL5/Include/ProjectQuantum* ~/ProjectQuantum_Backup/
cp [MT5]/MQL5/Experts/ProjectQuantum_Main.mq5 ~/ProjectQuantum_Backup/
```

### Step 2: Apply CLogger Enhancement (Already Complete)

✅ The enhanced CLogger.mqh is ready to use.

Simply copy: `Include/CLogger.mqh` → `[MT5]/MQL5/Include/CLogger.mqh`

### Step 3: Apply ProjectQuantum_Main.mq5 Enhancements

Position reconciliation and persistence are now built into `ProjectQuantum_Main.mq5` using `CPersistence`. Deploy the updated file directly—no manual paste is required.

**What changed:**
- `LoadPositionState()` and `ReconcileExistingPositions()` run during `OnInit()` to restore broker-aligned state.
- `SavePositionState()` writes snapshots every 10 ticks while a position is open and on deinit/close.
- Compatibility shims `Include/Project_Quantum.mqh` and `Include/Journey_Architecture.mqh` remove legacy include failures.

### Step 4: Apply CCircuitBreaker Enhancement

`CCircuitBreaker.mqh` still uses a placeholder release-code hash (simple storage in-memory). For production, replace `GenerateReleaseCode()`/`ValidateReleaseCode()` with a cryptographically hashed implementation (e.g., SHA256 of a random seed + expiry) and persist the hash, not the raw code. Keep expiry and retraining checks intact.

### Step 5: Copy All Other Files

All other .mqh files are ready to use as-is:

```bash
cp Include/*.mqh [MT5]/MQL5/Include/
```

These files have no code changes, just improved documentation.

### Step 6: Compile and Test

1. Open MetaEditor
2. Open ProjectQuantum_Main.mq5
3. Click Compile (F7)
4. Verify 0 errors, 0 warnings
5. Close MetaEditor

### Step 7: Test on Demo Account

**Critical Tests:**

1. **Position Reconciliation Test:**
   - Open a position
   - Note ticket number and price
   - Restart EA (Ctrl+R on chart)
   - Verify position recognized in logs
   - Verify MAE/MFE continue tracking

2. **Position Persistence Test:**
   - Open a position
   - Wait 1 minute (for file save)
   - Close MT5 completely
   - Restart MT5 and EA
   - Verify position fully restored
   - Check log for "Position state restored from file"

3. **Circuit Breaker Test:**
   - Trigger BLACK level (artificially lower thresholds if needed)
   - Note release code in logs
   - Input code via EA input parameter
   - Verify code validates
   - Verify system resumes

### Step 8: Monitor for 1 Week

Before live deployment:
- Run on demo for minimum 1 week
- Monitor all log files daily
- Verify no errors or warnings
- Check position state files are being created/updated
- Test restart scenarios multiple times

### Step 9: Deploy to Live

Only after successful demo testing:
1. Copy enhanced files to live MT5
2. Start with minimum position sizes
3. Monitor closely for first 48 hours
4. Keep manual override available

## Quick Reference

| File | Enhancement | Status |
|------|-------------|--------|
| CLogger.mqh | Log levels, performance tracking | ✅ Complete |
| ProjectQuantum_Main.mq5 | Position reconciliation & persistence | ✅ Included (no manual paste) |
| CCircuitBreaker.mqh | Enhanced release code security | ⚠️ Hardening pending (replace placeholder hashing) |
| Project_Quantum.mqh / Journey_Architecture.mqh | Compatibility shims for legacy includes | ✅ Included |
| All other .mqh files | Documentation improvements | ✅ Ready to use |

## Rollback Procedure

If issues occur:
1. Stop EA immediately
2. Close all positions manually
3. Restore from backup:
   ```bash
   cp ~/ProjectQuantum_Backup/* [MT5]/MQL5/Include/
   ```
4. Restart EA with previous version
5. Report issue with full logs

## Support

Check these locations for diagnostic information:
- `[Terminal]/MQL5/Logs/[DATE].log` - Expert log
- `[Terminal]/MQL5/Files/ProjectQuantum_[SYMBOL]_*.log` - ProjectQuantum log
- `[Terminal]/MQL5/Files/ProjectQuantum_Position_*.dat` - Position state
- `[Terminal]/MQL5/Files/ProjectQuantum_QTable_*.bin` - Q-learning brain

## Version Info

- Original: v2.0
- Enhanced: v2.1
- Integration Date: [YOUR DATE]
- Tested On: Demo Account [YES/NO]
- Live Deployed: [DATE] or [PENDING]
