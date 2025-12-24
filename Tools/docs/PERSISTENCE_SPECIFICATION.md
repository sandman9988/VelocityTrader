# Project Quantum - Persistence System Specification
## Comprehensive State Management with Power Failure Protection

**Version:** 1.0
**Date:** 2025-12-20
**Status:** Design Complete - Ready for Implementation

---

## 1. Overview

The persistence system ensures **zero data loss** and **graceful recovery** from power failures, crashes, and unexpected terminations at any point during system operation. This is critical for:

- Preserving learned Q-tables (months of training)
- Maintaining experience replay buffer (expensive samples)
- Protecting adversary neural network weights
- Ensuring continuous learning across EA restarts

### Design Principles

1. **Atomic Operations** - No partial state corruption
2. **Redundancy** - Multiple backup generations
3. **Verification** - HMAC-SHA256 tamper detection
4. **Graceful Degradation** - System continues with last valid state
5. **Minimal Latency** - Async saves don't block trading
6. **Forward Compatibility** - Version migration support

---

## 2. State Components to Persist

### 2.1 Entry Agent State (Critical)

**File:** `ProjectQuantum_EntryAgent.dat`

```cpp
struct SEntryAgentState {
    // Header
    int version;              // Schema version for migration
    datetime saved_at;        // Timestamp
    string hmac_signature;    // SHA256(all_data + secret_key)

    // Q-Table (Hash Table)
    int q_table_size;         // Number of entries
    SHashEntry q_entries[];   // Array of {state_hash, action, q_value}

    // Eligibility Traces
    int trace_size;
    STraceEntry traces[];     // {state_hash, action, eligibility}

    // Learning Parameters
    double epsilon;           // Current exploration rate
    double alpha;             // Current learning rate
    double lambda;            // Eligibility trace decay

    // Statistics
    long total_updates;       // Q-value updates performed
    long state_space_size;    // Unique states visited
    datetime training_start;  // First training timestamp
};
```

**Save Frequency:**
- Every 10 trades (configurable)
- On circuit breaker activation
- On OnDeinit() (clean shutdown)
- Force save every 60 minutes (safety net)

**Size Estimate:** ~10 MB for 10,000 states with traces

---

### 2.2 Exit Agent State (Critical)

**File:** `ProjectQuantum_ExitAgent.dat`

```cpp
struct SExitAgentState {
    int version;
    datetime saved_at;
    string hmac_signature;

    // Q-Table
    int q_table_size;
    SHashEntry q_entries[];

    // Eligibility Traces
    int trace_size;
    STraceEntry traces[];

    // Journey Reward State
    double ewma_capture_ratio;        // EWMA of MFE capture
    double ewma_flip_rate;            // EWMA of winner→loser flips
    double adaptive_giveback_scale;   // Current penalty scaling

    // Statistics
    long total_exits;
    double avg_mfe_capture;
    double avg_path_smoothness;
};
```

**Save Frequency:** Same as Entry Agent

**Size Estimate:** ~15 MB (larger state space with MFE/MAE bins)

---

### 2.3 Experience Replay Buffer (Critical)

**File:** `ProjectQuantum_ReplayBuffer.dat`

```cpp
struct SReplayBufferState {
    int version;
    datetime saved_at;
    string hmac_signature;

    // Buffer Contents
    int capacity;             // Max buffer size
    int current_size;         // Actual entries
    int next_index;           // Circular buffer position

    SExperience experiences[];    // Full SARS tuples
    double priorities[];          // TD-error based priorities
    double cdf[];                 // Cumulative distribution for sampling

    // Statistics
    double sum_priorities;        // For normalization
    long total_samples_taken;     // Replay sampling count
};

struct SExperience {
    ulong state_hash;             // Entry state hash
    ENUM_TRADING_ACTION action;   // Action taken
    SJourneyReward reward;        // Multi-component reward
    ulong next_state_hash;        // Exit state hash
    bool is_terminal;             // Episode ended
    datetime timestamp;           // Experience timestamp
    ENUM_REGIME regime;           // Market regime
};
```

**Save Frequency:**
- Every 50 new experiences added
- On buffer full (before oldest eviction)
- On OnDeinit()

**Size Estimate:** ~200 MB for 10,000 experiences with full reward structs

**Critical Notes:**
- Buffer is most expensive to rebuild (requires re-trading)
- Must preserve priorities and CDF for consistent sampling
- Circular buffer position critical for deterministic replay

---

### 2.4 Risk Adversary State (High Priority)

**File:** `ProjectQuantum_RiskAdversary.dat`

```cpp
struct SRiskAdversaryState {
    int version;
    datetime saved_at;
    string hmac_signature;

    // Neural Network Weights (if used instead of Q-table)
    int network_layers;           // Number of layers
    SLayerWeights weights[];      // Per-layer weight matrices
    SLayerWeights biases[];       // Per-layer bias vectors

    // OR Q-Table (if tabular)
    int q_table_size;
    SHashEntry q_entries[];

    // Prediction History (for calibration)
    int history_size;
    SPredictionRecord history[];  // {predicted_danger, actual_crash, timestamp}

    // Performance Metrics
    double f1_score;              // Classification F1
    double calibration_error;     // Brier score
    double true_positive_rate;
    double false_positive_rate;

    // Training State
    long total_predictions;
    long correct_predictions;
    datetime last_calibration;
};

struct SPredictionRecord {
    double danger_score;          // 0.0 to 1.0 prediction
    bool crash_occurred;          // Actual outcome (5-bar lookforward)
    datetime prediction_time;
    ENUM_REGIME regime;
};
```

**Save Frequency:**
- Every 20 predictions
- After calibration updates
- On crash prediction (danger > 0.7)

**Size Estimate:** ~5 MB for network weights + 1 MB for history

**Critical Notes:**
- Neural network weights cannot be retrained easily
- Prediction history required for online calibration
- Must preserve performance metrics for self-healing triggers

---

### 2.5 Learning Metrics State (Medium Priority)

**File:** `ProjectQuantum_LearningMetrics.dat`

```cpp
struct SLearningMetricsState {
    int version;
    datetime saved_at;
    string hmac_signature;

    // Historical Tracking Buffers
    int buffer_size;              // Lookback window (e.g., 100 trades)
    double td_error_history[];    // For convergence trend
    double q_stability_history[]; // For catastrophic forgetting detection
    double coverage_history[];    // State space coverage over time

    // Cumulative Statistics
    long total_trades;
    long unique_states_visited;
    long novel_states_last_100;   // For diversity tracking

    // Physics Predictive Power
    double vpin_accuracy_history[];    // VPIN → crash correlation
    double kurtosis_pred_history[];    // Kurtosis → tail event correlation
    double fractal_trend_history[];    // FD → trend accuracy

    // Self-Healing State
    bool needs_genetic_refresh;
    bool needs_q_table_reset;
    bool needs_exploration_boost;
    bool needs_reward_rebalancing;
    bool needs_physics_recalibration;
    datetime last_self_heal;
};
```

**Save Frequency:**
- Every 25 trades
- On self-healing trigger activation
- On OnDeinit()

**Size Estimate:** ~2 MB for 100-trade rolling windows

---

### 2.6 Portfolio Risk State (Medium Priority)

**File:** `ProjectQuantum_RiskState.dat`

```cpp
struct SPortfolioRiskState {
    int version;
    datetime saved_at;
    string hmac_signature;

    // Correlation Matrix
    int num_symbols;
    string symbols[];             // Symbol list
    double correlation_matrix[];  // Flattened NxN matrix
    datetime correlation_updated;

    // System Entropy History
    int entropy_history_size;
    SEntropyRecord entropy_history[];

    // Asset Class Exposure
    int num_asset_classes;
    SAssetClassExposure exposures[];  // Per-class risk tracking

    // Circuit Breaker State
    ENUM_DEFCON_LEVEL current_level;
    string release_codes[];       // Active release codes
    datetime level_changed;
    int consecutive_violations;

    // Three-Level Risk Cache
    double micro_danger_scores[];     // Per-symbol danger
    double meso_correlation_energy[]; // Per-asset-class crystallization
    double macro_system_entropy;      // Portfolio-wide entropy
};

struct SEntropyRecord {
    datetime timestamp;
    double system_entropy;
    double correlation_energy;
    ENUM_REGIME regime;
};

struct SAssetClassExposure {
    ENUM_ASSET_CLASS asset_class;
    double total_exposure_usd;
    double num_positions;
    double avg_correlation;
    double volatility_estimate;
};
```

**Save Frequency:**
- Every correlation matrix update (every 24 hours)
- On circuit breaker level change
- Every 10 trades

**Size Estimate:** ~1 MB for 20 symbols + entropy history

---

### 2.7 Shadow Agents State (Low Priority)

**File:** `ProjectQuantum_ShadowAgents.dat`

```cpp
struct SShadowAgentsState {
    int version;
    datetime saved_at;
    string hmac_signature;

    int num_shadows;              // Number of parallel shadow agents
    SShadowAgent shadows[];       // Per-shadow state
};

struct SShadowAgent {
    int agent_id;
    string strategy_name;         // "Aggressive", "Conservative", etc.

    // Q-Table
    int q_table_size;
    SHashEntry q_entries[];

    // Performance vs Primary
    double sharpe_ratio;
    double sortino_ratio;
    double max_drawdown;
    long total_trades;

    // Divergence Tracking
    double action_divergence;     // % different actions vs primary
    datetime last_outperformed;   // When shadow beat primary
};
```

**Save Frequency:**
- Every 50 trades
- On shadow outperformance event

**Size Estimate:** ~3 MB per shadow agent

---

## 3. Atomic Save Mechanism

### 3.1 Two-Phase Commit Pattern

**Prevents partial file corruption from power failures mid-write**

```cpp
bool CPersistence::AtomicSave(string filename, const SStateData &state) {
    string temp_file = filename + ".tmp";
    string backup_file = filename + ".bak";

    // Phase 1: Write to temporary file
    int handle = FileOpen(temp_file, FILE_WRITE|FILE_BIN);
    if(handle == INVALID_HANDLE) {
        CLogger::Error("Failed to open temp file: " + temp_file);
        return false;
    }

    // Write data
    if(!WriteStateData(handle, state)) {
        FileClose(handle);
        FileDelete(temp_file);
        return false;
    }

    // Calculate and write HMAC signature
    string hmac = CalculateHMAC(state);
    FileWriteString(handle, hmac);
    FileClose(handle);

    // Phase 2: Verify integrity, then atomic rename
    if(!VerifyFileIntegrity(temp_file)) {
        CLogger::Error("Integrity check failed for: " + temp_file);
        FileDelete(temp_file);
        return false;
    }

    // Backup existing file (if exists)
    if(FileIsExist(filename)) {
        if(!FileMove(filename, backup_file, FILE_REWRITE)) {
            CLogger::Warning("Failed to backup: " + filename);
            // Continue anyway - new data more important
        }
    }

    // Atomic rename (OS-level atomic operation)
    if(!FileMove(temp_file, filename, FILE_REWRITE)) {
        CLogger::Error("Failed to rename temp file");
        return false;
    }

    CLogger::Debug("Atomic save complete: " + filename);
    return true;
}
```

**Key Properties:**
- **Atomicity**: OS rename is atomic - file appears complete or not at all
- **Isolation**: Temp file isolated from main file until verified
- **Durability**: FileClose() flushes to disk before rename
- **Backup**: Previous state preserved in .bak file

---

### 3.2 HMAC-SHA256 Verification

**Prevents silent data corruption and tampering**

```cpp
string CPersistence::CalculateHMAC(const SStateData &state) {
    // Serialize state to byte array
    uchar data[];
    SerializeState(state, data);

    // Get secret key from terminal (unique per installation)
    string secret_key = GetSecretKey();
    uchar key[];
    StringToCharArray(secret_key, key);

    // Calculate HMAC-SHA256
    uchar hash[];
    CryptEncode(CRYPT_HASH_SHA256, data, key, hash);

    // Convert to hex string
    return ByteArrayToHex(hash);
}

bool CPersistence::VerifyFileIntegrity(string filename) {
    int handle = FileOpen(filename, FILE_READ|FILE_BIN);
    if(handle == INVALID_HANDLE) return false;

    // Read state data
    SStateData state;
    if(!ReadStateData(handle, state)) {
        FileClose(handle);
        return false;
    }

    // Read stored HMAC
    string stored_hmac = FileReadString(handle);
    FileClose(handle);

    // Calculate expected HMAC
    string calculated_hmac = CalculateHMAC(state);

    // Compare
    if(stored_hmac != calculated_hmac) {
        CLogger::Error(StringFormat("HMAC mismatch: %s vs %s", stored_hmac, calculated_hmac));
        return false;
    }

    return true;
}
```

---

### 3.3 Rotating Backup Generations

**Keeps last 3 saves - protects against cascading corruption**

```cpp
void CPersistence::RotateBackups(string filename) {
    // Rotate: file.bak2 <- file.bak1 <- file.bak <- file

    string bak2 = filename + ".bak2";
    string bak1 = filename + ".bak1";
    string bak = filename + ".bak";

    // Delete oldest
    if(FileIsExist(bak2)) {
        FileDelete(bak2);
    }

    // Rotate
    if(FileIsExist(bak1)) {
        FileMove(bak1, bak2, FILE_REWRITE);
    }

    if(FileIsExist(bak)) {
        FileMove(bak, bak1, FILE_REWRITE);
    }

    // Current backup created by AtomicSave()
}
```

**Recovery Priority:**
1. Load `filename` (most recent)
2. If corrupted, load `filename.bak` (previous generation)
3. If corrupted, load `filename.bak1` (2 generations back)
4. If corrupted, load `filename.bak2` (3 generations back)
5. If all corrupted, start fresh with warning

---

## 4. Load and Recovery

### 4.1 Graceful Recovery Flow

```cpp
template<typename T>
bool CPersistence::Load(string filename, T &state) {
    string files[] = {
        filename,
        filename + ".bak",
        filename + ".bak1",
        filename + ".bak2"
    };

    for(int i = 0; i < ArraySize(files); i++) {
        if(!FileIsExist(files[i])) continue;

        CLogger::Info(StringFormat("Attempting to load: %s (generation %d)", files[i], i));

        if(LoadFromFile(files[i], state)) {
            if(i > 0) {
                CLogger::Warning(StringFormat("Recovered from backup generation %d", i));
            }
            return true;
        }
    }

    CLogger::Error("All recovery attempts failed - starting fresh");
    return false;
}

bool CPersistence::LoadFromFile(string filename, T &state) {
    int handle = FileOpen(filename, FILE_READ|FILE_BIN);
    if(handle == INVALID_HANDLE) return false;

    // Verify integrity first
    if(!VerifyFileIntegrity(filename)) {
        FileClose(handle);
        return false;
    }

    // Read data
    FileSeek(handle, 0, SEEK_SET);  // Rewind after verify
    bool success = ReadStateData(handle, state);
    FileClose(handle);

    return success;
}
```

---

### 4.2 Version Migration

**Handles schema changes between EA versions**

```cpp
bool CPersistence::MigrateVersion(SStateData &state) {
    int current_version = 1;

    if(state.version == current_version) {
        return true;  // No migration needed
    }

    CLogger::Info(StringFormat("Migrating state from v%d to v%d", state.version, current_version));

    // Migration chain
    if(state.version == 0) {
        MigrateV0ToV1(state);
    }

    // Future migrations
    // if(state.version == 1) MigrateV1ToV2(state);

    state.version = current_version;
    return true;
}

void CPersistence::MigrateV0ToV1(SStateData &state) {
    // Example: Add new field with default value
    state.adaptive_giveback_scale = 1.0;

    // Example: Recalculate derived field
    RecalculateCDF(state.replay_buffer);

    CLogger::Info("Migration v0→v1 complete");
}
```

---

## 5. Power Failure Scenarios

### 5.1 Mid-Trade Crash

**Scenario:** Power loss while position is open

**Protection:**
- Position state saved every tick (lightweight)
- Includes: Entry price, MFE, MAE, bars_held, regime_at_entry
- On restart: Detect orphaned position, reconstruct state
- Exit agent uses reconstructed MFE/MAE for exit decision

```cpp
void CPersistence::SavePositionState(const SPositionState &pos) {
    // Ultra-fast save - no rotation, direct overwrite
    string filename = "ProjectQuantum_ActivePosition.dat";

    int handle = FileOpen(filename, FILE_WRITE|FILE_BIN);
    if(handle == INVALID_HANDLE) return;

    FileWriteInteger(handle, pos.ticket);
    FileWriteDouble(handle, pos.entry_price);
    FileWriteDouble(handle, pos.mfe);
    FileWriteDouble(handle, pos.mae);
    FileWriteInteger(handle, pos.bars_held);
    FileWriteInteger(handle, pos.regime_at_entry);
    FileWriteInteger(handle, TimeCurrent());

    FileClose(handle);
}

bool CPersistence::RecoverOrphanedPosition(SPositionState &pos) {
    // Called in OnInit()
    if(!FileIsExist("ProjectQuantum_ActivePosition.dat")) return false;

    // Load saved position state
    int handle = FileOpen("ProjectQuantum_ActivePosition.dat", FILE_READ|FILE_BIN);
    pos.ticket = FileReadInteger(handle);
    pos.entry_price = FileReadDouble(handle);
    pos.mfe = FileReadDouble(handle);
    pos.mae = FileReadDouble(handle);
    pos.bars_held = FileReadInteger(handle);
    pos.regime_at_entry = (ENUM_REGIME)FileReadInteger(handle);
    datetime saved_time = (datetime)FileReadInteger(handle);
    FileClose(handle);

    // Verify position still exists
    if(!PositionSelectByTicket(pos.ticket)) {
        CLogger::Info("Orphaned position already closed by broker");
        FileDelete("ProjectQuantum_ActivePosition.dat");
        return false;
    }

    CLogger::Info(StringFormat("Recovered orphaned position #%d", pos.ticket));
    return true;
}
```

---

### 5.2 Mid-Batch Training Crash

**Scenario:** Power loss during experience replay training

**Protection:**
- Batch training runs in chunks of 100 experiences
- Checkpoint after each chunk
- On restart: Resume from last checkpoint
- Minimal loss: At most 100 experience replays

```cpp
void CRLAgent::TrainFromReplay(int num_batches) {
    int checkpoint_interval = 100;

    for(int i = 0; i < num_batches; i++) {
        // Sample and train
        SExperience exp = m_replay_buffer.SamplePrioritized();
        UpdateQValue(exp);

        // Checkpoint every N batches
        if((i + 1) % checkpoint_interval == 0) {
            CPersistence::SaveCheckpoint(*this);
            CLogger::Debug(StringFormat("Training checkpoint at batch %d/%d", i+1, num_batches));
        }
    }

    // Final save
    CPersistence::SaveFull(*this);
}
```

---

### 5.3 Mid-Save Crash

**Scenario:** Power loss while writing state file

**Protection:**
- Two-phase commit ensures main file never corrupted
- Power loss during Phase 1: .tmp file incomplete, main file intact
- Power loss during Phase 2: .tmp complete, rename atomic (OS-guaranteed)
- Result: Either old state (main file) or new state (renamed .tmp), never partial

**Recovery:**
```cpp
void CPersistence::OnInit() {
    // Clean up stale temp files from aborted saves
    string files[];
    int count = FileFindFirst("*.tmp", files);

    for(int i = 0; i < count; i++) {
        CLogger::Warning("Deleting stale temp file: " + files[i]);
        FileDelete(files[i]);
    }
}
```

---

### 5.4 Disk Full

**Scenario:** No space left during save

**Protection:**
- Pre-flight space check before save
- Reserve 100 MB minimum free space
- If disk full: Warning to user, continue with old state
- Gradual degradation: Skip low-priority saves (shadow agents, metrics)

```cpp
bool CPersistence::HasSufficientSpace(long required_bytes) {
    long free_disk = TerminalInfoInteger(TERMINAL_DISK_SPACE);
    long reserve = 100 * 1024 * 1024;  // 100 MB reserve

    if(free_disk < required_bytes + reserve) {
        CLogger::Error(StringFormat("Insufficient disk space: %d MB free", free_disk / (1024*1024)));
        return false;
    }

    return true;
}

void CPersistence::SaveWithDegradation() {
    // Priority 1: Q-tables (critical)
    if(HasSufficientSpace(10 * 1024 * 1024)) {
        SaveEntryAgent();
        SaveExitAgent();
        SaveRiskAdversary();
    }

    // Priority 2: Experience replay
    if(HasSufficientSpace(200 * 1024 * 1024)) {
        SaveReplayBuffer();
    } else {
        CLogger::Warning("Skipping replay buffer save - disk space low");
    }

    // Priority 3: Metrics (can be recalculated)
    if(HasSufficientSpace(5 * 1024 * 1024)) {
        SaveLearningMetrics();
    }
}
```

---

## 6. Integration Points

### 6.1 OnInit() - Load State

```cpp
int OnInit() {
    // Initialize persistence system
    CPersistence::Initialize();

    // Recover orphaned positions first
    SPositionState orphan;
    if(CPersistence::RecoverOrphanedPosition(orphan)) {
        g_position_tracker.RestorePosition(orphan);
    }

    // Load agent states
    SEntryAgentState entry_state;
    if(CPersistence::Load("ProjectQuantum_EntryAgent.dat", entry_state)) {
        g_entry_agent.RestoreState(entry_state);
        CLogger::Info(StringFormat("Entry agent restored: %d states, %d updates",
                     entry_state.state_space_size, entry_state.total_updates));
    } else {
        CLogger::Info("Starting with fresh entry agent");
    }

    // Load exit agent
    SExitAgentState exit_state;
    if(CPersistence::Load("ProjectQuantum_ExitAgent.dat", exit_state)) {
        g_exit_agent.RestoreState(exit_state);
    }

    // Load replay buffer
    SReplayBufferState replay_state;
    if(CPersistence::Load("ProjectQuantum_ReplayBuffer.dat", replay_state)) {
        g_replay_buffer.RestoreState(replay_state);
        CLogger::Info(StringFormat("Replay buffer restored: %d experiences",
                     replay_state.current_size));
    }

    // Load risk adversary
    SRiskAdversaryState adversary_state;
    if(CPersistence::Load("ProjectQuantum_RiskAdversary.dat", adversary_state)) {
        g_risk_adversary.RestoreState(adversary_state);
    }

    // Load metrics and risk state
    CPersistence::Load("ProjectQuantum_LearningMetrics.dat", g_learning_metrics_state);
    CPersistence::Load("ProjectQuantum_RiskState.dat", g_risk_state);

    return INIT_SUCCEEDED;
}
```

---

### 6.2 OnTick() - Lightweight Position Save

```cpp
void OnTick() {
    // If position open, save lightweight state every tick
    if(PositionSelect(_Symbol)) {
        SPositionState pos = g_position_tracker.GetCurrentState();
        CPersistence::SavePositionState(pos);  // Fast: ~1ms
    }

    // ... rest of OnTick logic
}
```

---

### 6.3 OnTradeClose() - Immediate Full Save

```cpp
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result) {
    if(trans.type == TRADE_TRANSACTION_DEAL_ADD) {
        // Trade closed - save everything immediately
        CLogger::Info("Trade closed - performing full save");

        CPersistence::SaveAll();  // Priority: Q-tables, replay, metrics

        // Delete orphaned position file
        FileDelete("ProjectQuantum_ActivePosition.dat");
    }
}
```

---

### 6.4 TrainBatch() - Periodic Checkpoints

```cpp
void CRLAgent::TrainFromReplay(int num_batches) {
    int checkpoint_interval = 100;

    for(int i = 0; i < num_batches; i++) {
        // Train
        SExperience exp = m_replay_buffer.SamplePrioritized();
        UpdateQValue(exp);

        // Checkpoint
        if((i + 1) % checkpoint_interval == 0) {
            CPersistence::SaveCheckpoint(*this);
        }
    }

    CPersistence::SaveFull(*this);
}
```

---

### 6.5 OnDeinit() - Clean Shutdown Save

```cpp
void OnDeinit(const int reason) {
    CLogger::Info(StringFormat("OnDeinit called: %s", GetDeinitReasonText(reason)));

    // Don't save if terminal crashed (data may be corrupt)
    if(reason == REASON_CLOSE ||
       reason == REASON_CHARTCHANGE ||
       reason == REASON_CHARTCLOSE ||
       reason == REASON_PARAMETERS ||
       reason == REASON_RECOMPILE ||
       reason == REASON_REMOVE ||
       reason == REASON_ACCOUNT) {

        CLogger::Info("Performing clean shutdown save");
        CPersistence::SaveAll();

        // Rotate backups
        CPersistence::RotateBackups("ProjectQuantum_EntryAgent.dat");
        CPersistence::RotateBackups("ProjectQuantum_ExitAgent.dat");
        CPersistence::RotateBackups("ProjectQuantum_ReplayBuffer.dat");
    } else {
        CLogger::Warning("Abnormal termination - skipping save to preserve last good state");
    }
}
```

---

### 6.6 Circuit Breaker Emergency Save

```cpp
void CCircuitBreaker::ActivateLevel(ENUM_DEFCON_LEVEL level) {
    if(level >= DEFCON_ORANGE) {
        CLogger::Warning("Circuit breaker ORANGE/RED - emergency save");

        // Save all critical state before potential freeze
        CPersistence::SaveAll();

        if(level == DEFCON_BLACK) {
            // Freeze all trading - save final state
            CLogger::Error("DEFCON BLACK - system frozen");
            CPersistence::SaveAll();
        }
    }
}
```

---

## 7. Performance Optimization

### 7.1 Async Save Queue (Future Enhancement)

**Problem:** Full save takes ~500ms, blocks trading

**Solution:** Background save thread

```cpp
class CAsyncSaveQueue {
private:
    SSaveTask m_queue[];
    bool m_worker_running;

public:
    void EnqueueSave(string filename, const SStateData &state) {
        SSaveTask task;
        task.filename = filename;
        task.state = state;  // Copy
        task.priority = GetPriority(filename);

        ArrayResize(m_queue, ArraySize(m_queue) + 1);
        m_queue[ArraySize(m_queue) - 1] = task;

        // Start worker if not running
        if(!m_worker_running) {
            StartWorker();
        }
    }

    void StartWorker() {
        // MQL5 limitation: No real threads
        // Alternative: Save in OnTimer() callback
        EventSetTimer(1);  // Process queue every 1 second
        m_worker_running = true;
    }

    void OnTimer() {
        if(ArraySize(m_queue) == 0) {
            EventKillTimer();
            m_worker_running = false;
            return;
        }

        // Process highest priority task
        SortByPriority(m_queue);
        SSaveTask task = m_queue[0];

        // Perform save
        CPersistence::AtomicSave(task.filename, task.state);

        // Remove from queue
        ArrayRemove(m_queue, 0, 1);
    }
};
```

**Trade-off:**
- **Pro:** No blocking during save
- **Con:** More complex, risk of queue overflow
- **Decision:** Implement in Phase 6 if profiling shows >100ms save latency

---

### 7.2 Incremental Q-Table Saves

**Problem:** Q-table grows to 10,000+ entries, full save is slow

**Solution:** Save only dirty entries

```cpp
class CQTableIncremental {
private:
    bool m_dirty_flags[];  // Per-entry dirty bit
    int m_dirty_count;

public:
    void MarkDirty(int index) {
        if(!m_dirty_flags[index]) {
            m_dirty_flags[index] = true;
            m_dirty_count++;
        }
    }

    void SaveIncremental(string filename) {
        if(m_dirty_count == 0) return;

        // Open in append mode
        int handle = FileOpen(filename + ".delta", FILE_WRITE|FILE_BIN);

        // Write only dirty entries
        FileWriteInteger(handle, m_dirty_count);
        for(int i = 0; i < ArraySize(m_dirty_flags); i++) {
            if(m_dirty_flags[i]) {
                FileWriteInteger(handle, i);  // Index
                FileWriteDouble(handle, m_q_values[i]);  // Value
            }
        }

        FileClose(handle);

        // Clear dirty flags
        ArrayFill(m_dirty_flags, 0, ArraySize(m_dirty_flags), false);
        m_dirty_count = 0;
    }

    void LoadIncremental(string filename) {
        // Load base Q-table first
        LoadFull(filename);

        // Apply delta if exists
        if(FileIsExist(filename + ".delta")) {
            ApplyDelta(filename + ".delta");
        }
    }
};
```

---

## 8. Testing and Validation

### 8.1 Unit Tests

```cpp
bool TestAtomicSave() {
    // Test 1: Normal save/load
    SEntryAgentState state;
    state.total_updates = 12345;
    state.epsilon = 0.15;

    bool saved = CPersistence::AtomicSave("test.dat", state);
    ASSERT_TRUE(saved, "Save should succeed");

    SEntryAgentState loaded;
    bool loaded_ok = CPersistence::Load("test.dat", loaded);
    ASSERT_TRUE(loaded_ok, "Load should succeed");
    ASSERT_EQUAL(loaded.total_updates, 12345, "Data should match");

    // Test 2: Corruption detection
    // Manually corrupt file
    int handle = FileOpen("test.dat", FILE_WRITE|FILE_BIN|FILE_ANSI);
    FileWriteString(handle, "CORRUPTED");
    FileClose(handle);

    bool corrupted_load = CPersistence::Load("test.dat", loaded);
    ASSERT_FALSE(corrupted_load, "Corrupted file should fail integrity check");

    return true;
}

bool TestPowerFailureRecovery() {
    // Simulate power failure during save
    SEntryAgentState state;
    state.total_updates = 999;

    // Save initial state
    CPersistence::AtomicSave("test.dat", state);

    // Simulate aborted save (temp file left behind)
    int handle = FileOpen("test.dat.tmp", FILE_WRITE|FILE_BIN);
    FileWriteString(handle, "INCOMPLETE");
    FileClose(handle);

    // Recovery should clean up temp file
    CPersistence::OnInit();
    ASSERT_FALSE(FileIsExist("test.dat.tmp"), "Temp file should be deleted");

    // Original file should still be valid
    SEntryAgentState loaded;
    bool ok = CPersistence::Load("test.dat", loaded);
    ASSERT_TRUE(ok, "Original file should be intact");
    ASSERT_EQUAL(loaded.total_updates, 999, "Data should be preserved");

    return true;
}

bool TestBackupRotation() {
    SEntryAgentState state;

    // Save generation 0
    state.total_updates = 100;
    CPersistence::AtomicSave("test.dat", state);
    CPersistence::RotateBackups("test.dat");

    // Save generation 1
    state.total_updates = 200;
    CPersistence::AtomicSave("test.dat", state);
    CPersistence::RotateBackups("test.dat");

    // Save generation 2
    state.total_updates = 300;
    CPersistence::AtomicSave("test.dat", state);
    CPersistence::RotateBackups("test.dat");

    // Verify backup chain
    ASSERT_TRUE(FileIsExist("test.dat"), "Current should exist");
    ASSERT_TRUE(FileIsExist("test.dat.bak"), "Gen 1 should exist");
    ASSERT_TRUE(FileIsExist("test.dat.bak1"), "Gen 2 should exist");

    // Load each generation
    SEntryAgentState gen0, gen1, gen2;
    CPersistence::LoadFromFile("test.dat", gen0);
    CPersistence::LoadFromFile("test.dat.bak", gen1);
    CPersistence::LoadFromFile("test.dat.bak1", gen2);

    ASSERT_EQUAL(gen0.total_updates, 300, "Gen 0 should be newest");
    ASSERT_EQUAL(gen1.total_updates, 200, "Gen 1 should be middle");
    ASSERT_EQUAL(gen2.total_updates, 100, "Gen 2 should be oldest");

    return true;
}
```

---

### 8.2 Stress Tests

```cpp
bool StressTestFrequentSaves() {
    // Simulate 1000 rapid saves (worst case: every tick)
    SEntryAgentState state;

    ulong start = GetMicrosecondCount();

    for(int i = 0; i < 1000; i++) {
        state.total_updates = i;
        CPersistence::AtomicSave("stress_test.dat", state);
    }

    ulong elapsed = GetMicrosecondCount() - start;
    double avg_ms = (elapsed / 1000.0) / 1000.0;

    CLogger::Info(StringFormat("1000 saves took %.2f ms average", avg_ms));
    ASSERT_TRUE(avg_ms < 10.0, "Average save should be <10ms");

    // Verify final state
    SEntryAgentState loaded;
    CPersistence::Load("stress_test.dat", loaded);
    ASSERT_EQUAL(loaded.total_updates, 999, "Final state should be correct");

    return true;
}

bool StressTestLargeBuffer() {
    // Test with 10,000 experience buffer
    SReplayBufferState buffer;
    ArrayResize(buffer.experiences, 10000);
    ArrayResize(buffer.priorities, 10000);
    ArrayResize(buffer.cdf, 10000);

    // Fill with data
    for(int i = 0; i < 10000; i++) {
        buffer.experiences[i].state_hash = i * 12345;
        buffer.experiences[i].action = (ENUM_TRADING_ACTION)(i % 3);
        buffer.priorities[i] = MathRand() / 32768.0;
    }
    buffer.current_size = 10000;

    // Save
    ulong start = GetMicrosecondCount();
    CPersistence::AtomicSave("large_buffer.dat", buffer);
    ulong save_time = GetMicrosecondCount() - start;

    // Load
    start = GetMicrosecondCount();
    SReplayBufferState loaded;
    CPersistence::Load("large_buffer.dat", loaded);
    ulong load_time = GetMicrosecondCount() - start;

    CLogger::Info(StringFormat("Large buffer: Save=%.2f ms, Load=%.2f ms",
                 save_time / 1000.0, load_time / 1000.0));

    ASSERT_TRUE(save_time < 1000000, "Save should be <1 second");
    ASSERT_TRUE(load_time < 1000000, "Load should be <1 second");
    ASSERT_EQUAL(loaded.current_size, 10000, "All experiences should load");

    return true;
}
```

---

## 9. Phase Integration Timeline

### Phase 1-2: Foundation + Physics
**Persistence Scope:**
- Entry Agent (basic Q-table)
- Physics metrics state (VPIN history, kurtosis buffer)
- System optimizer state

**Files:**
- `ProjectQuantum_EntryAgent.dat`
- `ProjectQuantum_PhysicsState.dat`

### Phase 3-4: Adversary + Three-Level
**Persistence Scope:**
- Risk Adversary neural network weights
- Correlation matrix
- Asset class exposure tracking
- Circuit breaker state

**Files:**
- `ProjectQuantum_RiskAdversary.dat`
- `ProjectQuantum_RiskState.dat`

### Phase 5: Journey RL Integration
**Persistence Scope:**
- Exit Agent Q-table
- Experience replay buffer (critical!)
- Journey reward adaptive parameters

**Files:**
- `ProjectQuantum_ExitAgent.dat`
- `ProjectQuantum_ReplayBuffer.dat`

### Phase 6: Testing & Optimization
**Persistence Scope:**
- Learning metrics historical buffers
- Shadow agents state
- Performance benchmarks

**Files:**
- `ProjectQuantum_LearningMetrics.dat`
- `ProjectQuantum_ShadowAgents.dat`

**Testing:**
- All unit tests for persistence
- Stress tests with 10,000 buffer
- Power failure simulation (kill MT5 process mid-save)

### Phase 7-8: Documentation + Deployment
**Persistence Scope:**
- Production monitoring
- Backup verification scripts

---

## 10. Critical Success Criteria

✅ **Zero Data Loss**
- Q-table preserved across unexpected shutdowns
- Experience replay buffer never corrupted
- Neural network weights recoverable

✅ **Fast Recovery**
- OnInit() completes in <5 seconds even with 10,000 states
- No manual intervention required

✅ **Tamper Detection**
- HMAC verification catches silent corruption
- Multiple backup generations prevent cascading failures

✅ **Minimal Latency**
- Position state save: <1ms per tick
- Full save: <500ms (doesn't block trading if async)
- Checkpoint during training: <100ms per 100 batches

✅ **Forward Compatibility**
- Version migration allows upgrading EA without losing history
- Schema changes documented and tested

---

## 11. Implementation Checklist

### Core Files to Create/Modify:

- [ ] `Include/CPersistence.mqh` - Main persistence class
  - [ ] `AtomicSave()` with two-phase commit
  - [ ] `Load()` with graceful recovery
  - [ ] `VerifyFileIntegrity()` with HMAC-SHA256
  - [ ] `RotateBackups()` for 3-generation backup
  - [ ] `SaveAll()` coordinator

- [ ] `Include/Structures/SEntryAgentState.mqh` - Entry agent state struct
- [ ] `Include/Structures/SExitAgentState.mqh` - Exit agent state struct
- [ ] `Include/Structures/SReplayBufferState.mqh` - Replay buffer state struct
- [ ] `Include/Structures/SRiskAdversaryState.mqh` - Adversary state struct
- [ ] `Include/Structures/SLearningMetricsState.mqh` - Metrics state struct
- [ ] `Include/Structures/SPortfolioRiskState.mqh` - Risk state struct

### Modified Classes:

- [ ] `CRLAgent` - Add `RestoreState()` and `GetState()` methods
- [ ] `CReplayBuffer` - Add serialization/deserialization
- [ ] `CRiskAdversary` - Add neural network weight save/load
- [ ] `CLearningMetrics` - Add state export/import

### Main EA Integration:

- [ ] `OnInit()` - Load all state on startup
- [ ] `OnTick()` - Save position state if open
- [ ] `OnTradeTransaction()` - Full save on trade close
- [ ] `OnDeinit()` - Clean shutdown save
- [ ] `OnTimer()` - Periodic safety save every 60 minutes

### Unit Tests:

- [ ] `TestAtomicSave()` - Normal save/load
- [ ] `TestCorruptionDetection()` - HMAC mismatch
- [ ] `TestPowerFailureRecovery()` - Temp file cleanup
- [ ] `TestBackupRotation()` - 3-generation chain
- [ ] `StressTestFrequentSaves()` - 1000 rapid saves
- [ ] `StressTestLargeBuffer()` - 10,000 experience buffer

---

## 12. Final Notes

**Critical Design Decisions:**

1. **HMAC-SHA256 over CRC32** - Stronger integrity protection
2. **Atomic rename over in-place write** - OS-guaranteed atomicity
3. **3 backup generations** - Balance between safety and disk usage
4. **Separate files per component** - Faster partial saves, easier debugging
5. **Version field in every struct** - Future-proof schema evolution

**Trade-offs:**

- **Disk Space vs Safety** - 200 MB for full backup chain (acceptable for multi-month Q-tables)
- **Latency vs Completeness** - Full save every trade close (500ms acceptable, happens infrequently)
- **Complexity vs Robustness** - Two-phase commit adds code, eliminates corruption risk

**User Commitment:**

"Persistence dealt with properly throughout all the phases - no power failures etc" ✅

This specification ensures your months of RL training are **never lost**, even if:
- Power fails mid-tick
- Disk fills up
- MT5 crashes
- User accidentally deletes files (backups exist)
- Data gets corrupted (HMAC catches it, backups restore)

---

**Next Step:** Implement `CPersistence.mqh` in Phase 1 as foundation for all subsequent phases.
