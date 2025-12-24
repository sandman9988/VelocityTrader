#!/usr/bin/env python3
"""
Generate sample log data for testing the log analysis tools.
Simulates a Project Quantum EA session with various log levels.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_session_logs(output_dir: Path, session_id: str, symbol: str,
                          duration_minutes: int = 60, entries_per_minute: int = 5):
    """Generate a realistic log session."""

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"quantum_{symbol}_{session_id}_test.jsonl"

    start_time = datetime.now() - timedelta(minutes=duration_minutes)
    session_start = start_time.strftime("%Y.%m.%d %H:%M:%S")

    logs = []
    current_time = start_time

    # OnInit sequence
    logs.extend([
        make_log(current_time, "TRACE", f">>> ENTER OnInit()", symbol, session_id, session_start),
        make_log(current_time, "INFO", "═══════════════════════════════════════════════", symbol, session_id, session_start),
        make_log(current_time, "INFO", "       PROJECT QUANTUM v2.0 INITIALIZING       ", symbol, session_id, session_start),
        make_log(current_time, "INFO", "═══════════════════════════════════════════════", symbol, session_id, session_start),
        make_log(current_time, "INFO", f"Symbol: {symbol}", symbol, session_id, session_start),
        make_log(current_time, "VERBOSE", f"[INIT] MagicNumber=20241218 LearningRate=0.100 Epsilon=0.10", symbol, session_id, session_start),
        make_log(current_time, "VERBOSE", "[INIT] Creating system optimizer...", symbol, session_id, session_start),
        make_log(current_time, "INFO", "System optimization completed", symbol, session_id, session_start),
        make_log(current_time, "VERBOSE", "[INIT] Creating core components...", symbol, session_id, session_start),
    ])

    # Component creation traces
    components = ["CMarketAgnostic", "CInstrumentProfiler", "CRegimeJudge", "CRL_Agent",
                  "CReplayBuffer", "CProbabilityPredictor", "CCircuitBreaker", "CShadowManager",
                  "CRiskManager", "CPerformanceMonitor", "CAgnosticClock", "CMarketProbability", "CPersistence"]

    for comp in components:
        logs.append(make_log(current_time, "TRACE", f"OnInit() {comp} created", symbol, session_id, session_start))

    logs.extend([
        make_log(current_time, "VERBOSE", "[INIT] All 13 components created successfully", symbol, session_id, session_start),
        make_log(current_time, "INFO", "Initialization complete", symbol, session_id, session_start),
        make_log(current_time, "INFO", "Instrument class: FOREX_MAJOR", symbol, session_id, session_start),
        make_log(current_time, "INFO", f"Daily volatility: {random.uniform(0.5, 1.5):.2f}%", symbol, session_id, session_start),
        make_log(current_time, "VERBOSE", "[INIT] State=STATE_TRADING WarmupBars=0 CircuitLocked=NO", symbol, session_id, session_start),
        make_log(current_time, "TRACE", "<<< EXIT OnInit() => INIT_SUCCEEDED", symbol, session_id, session_start),
    ])

    current_time += timedelta(seconds=5)

    # Trading session simulation
    regimes = ["REGIME_LIQUID", "REGIME_VOLATILE", "REGIME_QUIET", "REGIME_TRENDING"]
    trade_count = 0

    for minute in range(duration_minutes):
        current_time += timedelta(minutes=1)
        uptime = int((current_time - start_time).total_seconds())

        # Regular tick processing
        for _ in range(random.randint(2, entries_per_minute)):
            regime = random.choice(regimes)
            z_score = random.gauss(0, 1)
            mer = random.uniform(0.3, 0.7)
            entropy = random.uniform(0.4, 0.9)
            vpin = random.uniform(0.2, 0.8)
            hurst = random.uniform(0.3, 0.7)

            # State logs
            logs.append(make_log(current_time, "STATE",
                f"Tick | Z:{z_score:.2f} MER:{mer:.3f} Ent:{entropy:.3f} VPIN:{vpin:.3f} H:{hurst:.3f} | {regime}",
                symbol, session_id, session_start, uptime))

            # Verbose risk checks
            if random.random() < 0.3:
                logs.append(make_log(current_time, "VERBOSE",
                    f"[RISK] CVaR={random.uniform(0.01, 0.03):.4f} Kelly={random.uniform(0.1, 0.3):.3f}",
                    symbol, session_id, session_start, uptime))

            # Occasional trades
            if random.random() < 0.05:
                trade_count += 1
                action = random.choice(["BUY", "SELL"])
                lots = random.uniform(0.01, 0.1)
                price = 1.0850 + random.uniform(-0.01, 0.01) if "USD" in symbol else 150.0 + random.uniform(-1, 1)

                logs.append(make_log(current_time, "TRADE",
                    f"{action} {lots:.2f} lots @ {price:.5f} | SL: {price - 0.005:.5f} | TP: {price + 0.01:.5f}",
                    symbol, session_id, session_start, uptime))

                logs.append(make_log(current_time, "VERBOSE",
                    f"[TRADE] Signal confidence={random.uniform(0.6, 0.95):.3f} regime={regime}",
                    symbol, session_id, session_start, uptime))

                # Audit log for trade
                logs.append(make_audit_log(current_time, "TRADE", f"OP_{trade_count:04d}",
                    action, "EXECUTED", symbol, session_id, session_start, uptime))

        # Occasional warnings/errors
        if random.random() < 0.02:
            logs.append(make_log(current_time, "WARN",
                f"High correlation detected: {random.uniform(0.7, 0.95):.3f}",
                symbol, session_id, session_start, uptime))

        if random.random() < 0.005:
            logs.append(make_log(current_time, "ERROR",
                f"Order failed: Error code {random.randint(4000, 4100)}",
                symbol, session_id, session_start, uptime))

    # OnDeinit sequence
    logs.extend([
        make_log(current_time, "TRACE", ">>> ENTER OnDeinit()", symbol, session_id, session_start),
        make_log(current_time, "INFO", "Deinitializing...", symbol, session_id, session_start),
        make_log(current_time, "VERBOSE", "[DEINIT] Reason=0", symbol, session_id, session_start),
        make_log(current_time, "TRACE", "OnDeinit() Timer killed", symbol, session_id, session_start),
        make_log(current_time, "INFO", "Agent brain saved", symbol, session_id, session_start),
        make_log(current_time, "INFO", "Replay buffer saved", symbol, session_id, session_start),
        make_audit_log(current_time, "PERSISTENCE", "SAVE_001", "SaveState", "SUCCESS",
                       symbol, session_id, session_start),
        make_log(current_time, "VERBOSE", "[DEINIT] Deleting components (reverse order)...", symbol, session_id, session_start),
        make_log(current_time, "VERBOSE", "[DEINIT] All components deleted", symbol, session_id, session_start),
        make_log(current_time, "INFO", "Deinitialization complete. Reason: 0 (Program removed)", symbol, session_id, session_start),
        make_log(current_time, "TRACE", "<<< EXIT OnDeinit()", symbol, session_id, session_start),
        make_log(current_time, "INFO", "event=session_end", symbol, session_id, session_start),
    ])

    # Write to file
    with open(filename, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')

    print(f"Generated {len(logs)} log entries to {filename}")
    print(f"  - Trades: {trade_count}")
    print(f"  - Duration: {duration_minutes} minutes")
    return filename


def make_log(ts: datetime, level: str, message: str, symbol: str,
             session: str, session_start: str, uptime: int = 0) -> dict:
    return {
        "ts": ts.strftime("%Y.%m.%d %H:%M:%S"),
        "level": level,
        "symbol": symbol,
        "timeframe": 60,
        "session_start": session_start,
        "session": session,
        "uptime_sec": uptime,
        "message": message
    }


def make_audit_log(ts: datetime, event: str, op_id: str, action: str,
                   outcome: str, symbol: str, session: str,
                   session_start: str, uptime: int = 0) -> dict:
    return {
        "ts": ts.strftime("%Y.%m.%d %H:%M:%S"),
        "level": "AUDIT",
        "symbol": symbol,
        "timeframe": 60,
        "session_start": session_start,
        "session": session,
        "uptime_sec": uptime,
        "audit": {
            "event": event,
            "op_id": op_id,
            "action": action,
            "outcome": outcome
        }
    }


if __name__ == "__main__":
    output_dir = Path(__file__).parent.parent / "logs"

    # Generate sample sessions
    generate_session_logs(output_dir, "A1B2C3D4", "EURUSD", duration_minutes=30, entries_per_minute=3)
    generate_session_logs(output_dir, "E5F6G7H8", "USDJPY", duration_minutes=15, entries_per_minute=4)

    print(f"\nSample logs generated in: {output_dir}")
    print("Run analysis with: python tools/log_analyzer.py logs/*.jsonl")
