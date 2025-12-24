# Project Quantum v3.0 - API Reference

## Table of Contents

1. [Core Utilities](#core-utilities)
2. [Physics Layer](#physics-layer)
3. [Intelligence Layer](#intelligence-layer)
4. [Risk Layer](#risk-layer)
5. [Performance Layer](#performance-layer)
6. [Safety Layer](#safety-layer)
7. [Architecture Types](#architecture-types)

---

## Core Utilities

### SafeMath Namespace

**File:** `Include/Core/SafeMath.mqh`

Safe mathematical operations with graceful fallbacks.

| Function | Signature | Description |
|----------|-----------|-------------|
| `Divide` | `double Divide(double num, double denom, double fallback=0.0)` | Division with zero protection |
| `Log` | `double Log(double x, double fallback=0.0)` | Log with negative/zero protection |
| `Sqrt` | `double Sqrt(double x, double fallback=0.0)` | Sqrt with negative protection |
| `Power` | `double Power(double base, double exp, double fallback=0.0)` | Power with singularity protection |
| `Clamp` | `double Clamp(double value, double min, double max)` | Range limiting |
| `Normalize` | `double Normalize(double value, double min, double max)` | Normalize to [0,1] |
| `IsFinite` | `bool IsFinite(double value)` | Check for NaN/Inf |
| `IsEqual` | `bool IsEqual(double a, double b, double eps=1e-10)` | Float comparison with epsilon |

### ArrayUtils Namespace

**File:** `Include/Core/ArrayUtils.mqh`

Statistical array operations.

| Function | Signature | Description |
|----------|-----------|-------------|
| `MeanStdDev` | `void MeanStdDev(const double &arr[], double &mean, double &std)` | Welford's algorithm |
| `Median` | `double Median(double &arr[])` | Linear interpolation median |
| `Percentile` | `double Percentile(double &arr[], double p)` | P-th percentile |
| `MinMax` | `void MinMax(const double &arr[], double &min, double &max)` | Find range |
| `ZScoreNormalize` | `void ZScoreNormalize(double &arr[])` | In-place z-score |
| `MinMaxNormalize` | `void MinMaxNormalize(double &arr[], double min, double max)` | In-place [0,1] |
| `IsValidArray` | `bool IsValidArray(const double &arr[])` | Check for NaN/Inf |
| `SafeResize` | `bool SafeResize(double &arr[], int new_size)` | Resize with validation |
| `SafeCopy` | `void SafeCopy(const double &src[], double &dst[])` | Bounds-checked copy |

### SymbolUtils Namespace

**File:** `Include/Core/SymbolUtils.mqh`

Safe broker information retrieval.

| Function | Signature | Description |
|----------|-----------|-------------|
| `GetBid` | `double GetBid(string symbol, double fallback=0.0)` | Safe bid price |
| `GetAsk` | `double GetAsk(string symbol, double fallback=0.0)` | Safe ask price |
| `GetSpread` | `double GetSpread(string symbol)` | Spread in points |
| `GetTickValue` | `double GetTickValue(string symbol, double fallback=0.0)` | Per lot tick value |
| `GetContractSize` | `double GetContractSize(string symbol, double fallback=100000)` | Lot size |
| `NormalizeVolume` | `double NormalizeVolume(string symbol, double lots)` | Respect min/max/step |
| `PriceToDeposit` | `double PriceToDeposit(string symbol, double dist, double lots)` | Risk calculation |
| `DepositToPrice` | `double DepositToPrice(string symbol, double deposit, double lots)` | Stop distance |
| `GetStopLevel` | `int GetStopLevel(string symbol)` | Min stop distance |
| `IsMarketOpen` | `bool IsMarketOpen(string symbol)` | Trading session check |

### CCore Class

**File:** `Include/Core/Core.mqh`

Foundational utilities and data structures.

```cpp
class CCore {
public:
    // Math safety
    static double SafeDiv(double num, double denom, double fallback=0.0);
    static double SafeLog(double x, double fallback=0.0);
    static double SafeSqrt(double x, double fallback=0.0);
    static double SafePow(double base, double exp, double fallback=0.0);
    static double Clamp(double value, double min, double max);
    static double ClampSigma(double value, double sigma);

    // Statistics
    static double ArrayMean(const double &arr[]);
    static void ArrayMeanStdDev(const double &arr[], double &mean, double &std);
    static double ArrayPercentile(const double &arr[], double p);
    static double CalculateZScore(const double &arr[], int size, double value);
    static double CalculateSharpe(const double &returns[], double risk_free=0.0);
    static double CalculateSortino(const double &returns[], double risk_free=0.0);
    static double CalculateCorrelation(const double &x[], const double &y[]);
    static double WassersteinDistance(const double &p[], const double &q[]);

    // Comparisons
    static bool IsEqual(double a, double b);
    static bool IsGreater(double a, double b);
    static bool IsLess(double a, double b);
    static bool IsZero(double a);
    static bool IsRetryableError(uint retcode);

    // Utility
    double RMultipleToDollars(double r_multiple, double risk_amount);
};
```

---

## Physics Layer

### CFractalAnalyzer Class

**File:** `Include/Physics/CFractalAnalyzer.mqh`

Fractal and chaos analysis.

```cpp
class CFractalAnalyzer {
public:
    CFractalAnalyzer(string symbol, ENUM_TIMEFRAMES tf);
    ~CFractalAnalyzer();

    // Core analysis
    double CalculateKatzFractalDimension(int period=50);
    double CalculateSampleEntropy(int m=2, double r=0.2, int n=100);
    double CalculateFTLE(int period=30);
    double CalculateHurstExponent(int period=100);

    // Regime detection
    bool IsTrending();
    bool IsMeanReverting();
    bool IsRandom();

    // State
    void Update();
    SFractalState GetState();
};
```

### CPortfolioPhysics Class

**File:** `Include/Physics/CPortfolioPhysics.mqh`

Portfolio-level physics metrics.

```cpp
class CPortfolioPhysics {
public:
    CPortfolioPhysics();
    ~CPortfolioPhysics();

    // Portfolio metrics
    double CalculateCorrelationEnergy(const string &symbols[], int count);
    double CalculateSystemEntropy(const double &positions[]);
    double CalculateVPIN(const double &volumes[], const double &prices[], int n=50);
    double CalculateBifurcationProximity();

    // Correlation matrix
    void UpdateCorrelationMatrix(const string &symbols[], int lookback=100);
    double GetCorrelation(string sym1, string sym2);
    double GetAverageCorrelation();

    // Risk indicators
    bool IsCrystallizing();
    bool IsChaoticRegime();
    double GetSystemStress();
};
```

### CMarketAgnostic Class

**File:** `Include/Sensing/CMarketAgnostic.mqh`

Core market sensing.

```cpp
class CMarketAgnostic {
public:
    CMarketAgnostic(string symbol, ENUM_TIMEFRAMES tf);
    ~CMarketAgnostic();

    // State generation
    SStateVector GetStateVector();
    void Update();

    // Individual metrics
    double GetHurstExponent();
    double GetEntropyScore();
    double GetYangZhangVolatility();
    double GetMERScore();
    double GetKurtosis();
    double GetVPIN();
    ENUM_REGIME GetRegime();

    // Normalization
    double NormalizeToUnit(double value, double min, double max);
};
```

---

## Intelligence Layer

### CRL_Agent Class

**File:** `Include/Intelligence/CRL_Agent.mqh`

Entry Q-learning agent.

```cpp
class CRL_Agent {
public:
    CRL_Agent(string identifier);
    ~CRL_Agent();

    // Action selection
    ENUM_TRADING_ACTION ChooseAction(const SStateVector &state);
    ENUM_TRADING_ACTION GetBestAction(const SStateVector &state);

    // Learning
    void UpdateQValue(const SStateVector &state, ENUM_TRADING_ACTION action,
                      double reward, const SStateVector &next_state);
    void UpdateWithTrace(const SStateVector &state, ENUM_TRADING_ACTION action,
                         double reward, bool terminal);
    void DecayTraces();
    void ResetTraces();

    // Q-table management
    double GetQValue(const SStateVector &state, ENUM_TRADING_ACTION action);
    void SetQValue(const SStateVector &state, ENUM_TRADING_ACTION action, double value);
    int GetQTableSize();

    // Parameters
    void SetAlpha(double alpha);
    void SetGamma(double gamma);
    void SetEpsilon(double epsilon);
    void SetLambda(double lambda);
    double GetEpsilon();
    double GetAlpha();

    // Persistence
    bool SaveBrain(string filename);
    bool LoadBrain(string filename);

    // Maintenance
    void Heal(double intensity=0.1);
    void GeneticRefresh(double mutation_rate=0.05);
    void CloneFrom(const CRL_Agent *source);
};
```

### CRLExitAgent Class

**File:** `Include/Intelligence/CRLExitAgent.mqh`

Exit management Q-learning agent.

```cpp
class CRLExitAgent {
public:
    CRLExitAgent(string identifier);
    ~CRLExitAgent();

    // State building
    SExitState BuildState(const SPositionContext &pos, ENUM_REGIME regime, double vol_z);

    // Action selection
    ENUM_EXIT_ACTION ChooseAction(const SExitState &state);
    ENUM_EXIT_ACTION GetBestAction(const SExitState &state);

    // Learning
    void Update(const SExitState &state, ENUM_EXIT_ACTION action,
                double reward, const SExitState &next_state, bool terminal);

    // Parameters
    void SetAlpha(double alpha);
    void SetGamma(double gamma);
    void SetEpsilon(double epsilon);
    void SetLambda(double lambda);
    void SetPartialClosePct(double pct);

    // State space info
    int GetStateSpaceSize();
    int GetActionCount();
    int GetQTableSize();

    // Persistence
    bool SaveState(string filename);
    bool LoadState(string filename);
};
```

### CRiskAdversary Class

**File:** `Include/Intelligence/CRiskAdversary.mqh`

Crash prediction adversarial agent.

```cpp
class CRiskAdversary {
public:
    CRiskAdversary(string identifier);
    ~CRiskAdversary();

    // Prediction
    double PredictDangerScore(const SStateVector &state);
    SCrashPrediction Predict(const SStateVector &state);

    // Learning
    void Update(const SStateVector &state, bool crash_occurred, double actual_drawdown);
    void RecordOutcome(double predicted_danger, bool crash_occurred);

    // Metrics
    double GetF1Score();
    double GetPrecision();
    double GetRecall();
    double GetBrierScore();
    double GetCalibrationError();
    SAdversaryMetrics GetMetrics();

    // Configuration
    void SetCrashThreshold(double threshold);
    void SetLookbackPeriod(int periods);

    // Persistence
    bool SaveState(string filename);
    bool LoadState(string filename);
};
```

### CJourneyReward Class

**File:** `Include/Intelligence/CJourneyReward.mqh`

Multi-component reward shaping.

```cpp
class CJourneyReward {
public:
    CJourneyReward();
    ~CJourneyReward();

    // Reward calculation
    SRewardBreakdown CalculateReward(const STradeMetrics &trade);
    double GetTotalReward(const STradeMetrics &trade);

    // Weight configuration
    void SetWeights(const SRewardWeights &weights);
    void GetWeights(SRewardWeights &weights);
    void SetMFEWeight(double w);
    void SetMAEWeight(double w);
    void SetSortinoWeight(double w);
    void SetPathWeight(double w);
    void SetProfitWeight(double w);
    void SetGivebackWeight(double w);

    // Adaptive scaling
    void UpdateEWMA(double mfe_capture, double flip_rate);
    double GetAdaptiveGivebackScale();

    // Normalization
    void SetRMultipleRange(double min_r, double max_r);
};
```

### CReplayBuffer Class

**File:** `Include/Intelligence/CReplayBuffer.mqh`

Prioritized experience replay.

```cpp
class CReplayBuffer {
public:
    CReplayBuffer(int capacity=10000);
    ~CReplayBuffer();

    // Experience management
    void AddExperience(const SJourneyTrade &trade);
    bool GetRandomSample(SJourneyTrade &trade);
    bool GetPrioritizedSample(SJourneyTrade &trade, double &sampling_weight);
    int GetPrioritizedBatch(SJourneyTrade &trades[], double &weights[], int batch_size);

    // Statistics
    int Size();
    int Capacity();
    double GetDrawdown();
    double GetWinRate();
    double GetSortino();
    int GetFailingRegime();
    double GetAverageR();

    // Priority management
    void UpdatePriorities();
    double CalculatePriority(const SJourneyTrade &trade);

    // Persistence
    bool SaveBuffer(string filename);
    bool LoadBuffer(string filename);

    // Maintenance
    void Clear();
};
```

---

## Risk Layer

### CThreeLevelRisk Class

**File:** `Include/Risk/CThreeLevelRisk.mqh`

Three-level risk validation pipeline.

```cpp
class CThreeLevelRisk {
public:
    CThreeLevelRisk();
    ~CThreeLevelRisk();

    // Main validation
    SValidationResult Validate(string symbol, ENUM_TRADING_ACTION action,
                               double proposed_lots, const SStateVector &state,
                               const SPortfolioPhysics &phys);

    // Individual level checks
    SValidationResult ValidateMicro(string symbol, const SStateVector &state);
    SValidationResult ValidateMeso(string symbol, const SPortfolioPhysics &phys);
    SValidationResult ValidateMacro(const SPortfolioPhysics &phys);

    // Danger score integration
    void SetDangerScore(double danger);
    double GetDangerScore();

    // Threshold configuration
    void SetSpreadPercentileMax(double pct);
    void SetMaxCorrelation(double corr);
    void SetMaxExposure(double exp);
    void SetEntropyBounds(double min, double max);
    void SetCorrelationEnergyMax(double max);
};
```

### CAssetClassRisk Class

**File:** `Include/Risk/CAssetClassRisk.mqh`

Asset class correlation and exposure management.

```cpp
class CAssetClassRisk {
public:
    CAssetClassRisk();
    ~CAssetClassRisk();

    // Asset classification
    ENUM_ASSET_CLASS ClassifySymbol(string symbol);
    void SetSymbolClass(string symbol, ENUM_ASSET_CLASS cls);

    // Exposure tracking
    void UpdateExposure(string symbol, double lots, ENUM_TRADING_ACTION action);
    double GetClassExposure(ENUM_ASSET_CLASS cls);
    double GetTotalExposure();
    bool IsOverconcentrated(ENUM_ASSET_CLASS cls);

    // Correlation analysis
    void UpdateCorrelations(int lookback=100);
    double GetCorrelationWith(string symbol, const string &existing[]);
    double GetAverageClassCorrelation(ENUM_ASSET_CLASS cls);

    // Limits
    void SetMaxClassExposure(ENUM_ASSET_CLASS cls, double max);
    void SetMaxCorrelation(double max);

    // State
    void ClearExposures();
};
```

### CPositionSizer Class

**File:** `Include/Risk/CPositionSizer.mqh`

Unified position sizing logic.

```cpp
class CPositionSizer {
public:
    CPositionSizer(string symbol);
    ~CPositionSizer();

    // Size calculation
    double Calculate(double stop_distance, double risk_amount,
                     double danger_score, ENUM_REGIME regime,
                     double circuit_multiplier);

    // Component adjustments
    double ApplyVolatilityAdjustment(double base_size, double yang_zhang_vol);
    double ApplyDangerModulation(double size, double danger_score);
    double ApplyRegimeAdjustment(double size, ENUM_REGIME regime);
    double ApplyCircuitMultiplier(double size, double multiplier);

    // Normalization
    double NormalizeToLotStep(double size);
    double ClampToLimits(double size);

    // Configuration
    void SetMaxLots(double max);
    void SetMinLots(double min);
    void SetDangerSensitivity(double sensitivity);
    void SetRegimeMultipliers(double liquid, double volatile_, double plasma);
};
```

---

## Performance Layer

### CLearningMetrics Class

**File:** `Include/Performance/CLearningMetrics.mqh`

Learning quality tracking.

```cpp
class CLearningMetrics {
public:
    CLearningMetrics();
    ~CLearningMetrics();

    // Recording
    void RecordTDError(double td_error);
    void RecordQChange(double old_q, double new_q);
    void RecordStateVisit(bool is_novel);
    void RecordAction(int action_idx);
    void RecordExplorationRate(double epsilon);
    void RecordMFECapture(double capture_rate);
    void RecordReward(double reward);

    // Physics predictions
    void RecordVPINPrediction(bool predicted_adverse, bool was_adverse);
    void RecordKurtosisPrediction(bool predicted_tail, bool had_tail);
    void RecordFractalPrediction(bool predicted_trend, bool was_trend);
    void RecordEntropyPrediction(ENUM_REGIME predicted, ENUM_REGIME actual);

    // Regime tracking
    void RecordRegimeTrade(ENUM_REGIME regime, double profit_r);
    void RecordRegimeDetection(int detected_bar, int actual_bar, bool false_transition);

    // Adversary tracking
    void RecordAdversaryPrediction(double predicted_danger, bool crash_occurred);
    void RecordSizingBenefit(double benefit_pct);

    // Replay tracking
    void RecordReplaySample(int state_bucket, int buffer_index);

    // Calculate all metrics
    SLearningMetrics Calculate();

    // Dashboard
    string GenerateDashboard();

    // Configuration
    void SetStateSpaceSize(int size);
    void SetThresholds(const SLearningThresholds &thresholds);
    void GetThresholds(SLearningThresholds &thresholds);

    // Reset
    void Reset();
};
```

### CRiskIntelligence Class

**File:** `Include/Performance/CRiskIntelligence.mqh`

Physics-informed risk monitoring.

```cpp
class CRiskIntelligence {
public:
    CRiskIntelligence();
    ~CRiskIntelligence();

    // Updates
    void UpdatePhysics(double kurtosis, double correlation_energy,
                       double vpin, double system_entropy, double bifurcation);
    void UpdateEquity(double equity);
    void UpdateRegime(ENUM_REGIME regime);
    void UpdateExposure(double total_exposure, int open_positions);
    void RecordTrade(double mfe, double realized_pnl, bool is_winner);
    void UpdateModelPerformance(double is_sharpe, double oos_sharpe);
    void UpdateQStatistics(double q_mean);

    // Calculate all metrics
    SRiskIntelligence Calculate();

    // Risk recommendations
    double GetPositionScalar();
    bool ShouldTriggerCircuitBreaker(ENUM_DEFCON_ALERT &level);

    // Dashboard
    string GenerateDashboard();

    // Configuration
    void SetThresholds(const SRiskThresholds &thresholds);
    void GetThresholds(SRiskThresholds &thresholds);
    void SetMaxExposure(double max);
    void SetBaseVaR(double var);

    // Reset
    void Reset();
};
```

### CPerformanceMonitor Class

**File:** `Include/Performance/CPerformanceMonitor.mqh`

Session metrics and HUD rendering.

```cpp
class CPerformanceMonitor {
public:
    CPerformanceMonitor(string symbol);
    ~CPerformanceMonitor();

    // Session management
    void StartSession();
    void EndSession();
    void RecordTrade(const SProjectQuantumTrade &trade);

    // Metrics
    double GetWinRate();
    double GetSortinoRatio();
    double GetSharpeRatio();
    double GetProfitFactor();
    double GetAverageR();
    double GetMaxDrawdown();
    int GetTotalTrades();
    int GetWinningTrades();

    // Health tracking
    void UpdateHealth();
    void StartTickTimer();
    void StopTickTimer();
    double GetAverageLatency();

    // HUD
    void DrawHUD(int x=10, int y=30);
    void ClearHUD();
    void SetHUDVisible(bool visible);

    // Reset
    void Reset();
};
```

---

## Safety Layer

### CCircuitBreaker Class

**File:** `Include/Safety/CCircuitBreaker.mqh`

DEFCON level management.

```cpp
class CCircuitBreaker {
public:
    CCircuitBreaker();
    ~CCircuitBreaker();

    // Level management
    ENUM_DEFCON_LEVEL GetLevel();
    void SetLevel(ENUM_DEFCON_LEVEL level);
    void ActivateLevel(ENUM_DEFCON_LEVEL level);

    // Updates
    void UpdateThresholds(double drawdown, int consecutive_losses, double sortino);
    void CheckAndUpdate(double danger_score, double correlation_energy,
                        double system_entropy, double drawdown);

    // Actions based on level
    bool ShouldBlockNewTrades();
    bool ShouldClosePositions();
    bool ShouldHalt();
    double GetPositionMultiplier();

    // Release
    bool AttemptManualRelease(string code);
    string GenerateReleaseCode();
    bool IsAwaitingRelease();

    // Retraining
    void TriggerRetraining();
    bool IsRetraining();
    void CompleteRetraining();

    // References
    void SetAgentRef(CRL_Agent *agent);
    void SetBufferRef(CReplayBuffer *buffer);
};
```

---

## Architecture Types

### Core Enumerations

**File:** `Include/Architecture/Project_Quantum.mqh`

```cpp
// Market regimes
enum ENUM_REGIME {
    REGIME_LIQUID = 0,     // Normal, low volatility
    REGIME_VOLATILE = 1,   // High volatility
    REGIME_TRENDING = 2,   // Strong directional movement
    REGIME_PLASMA = 3,     // Chaotic, high uncertainty
    REGIME_UNKNOWN = 4     // Insufficient data
};

// Trading actions
enum ENUM_TRADING_ACTION {
    ACTION_HOLD = 0,
    ACTION_BUY = 1,
    ACTION_SELL = 2,
    ACTION_CLOSE = 3
};

// Exit actions
enum ENUM_EXIT_ACTION {
    EXIT_HOLD = 0,
    EXIT_PARTIAL = 1,
    EXIT_FULL = 2,
    EXIT_TRAIL_TIGHT = 3,
    EXIT_TRAIL_WIDE = 4
};

// System states
enum ENUM_SYSTEM_STATE {
    STATE_INITIALIZING = 0,
    STATE_TRADING = 1,
    STATE_DEGRADED = 2,
    STATE_LOCKED = 3,
    STATE_RETRAINING = 4,
    STATE_AWAITING_RELEASE = 5,
    STATE_READY = 6,
    STATE_EMERGENCY = 7,
    STATE_DISCONNECTED = 8
};

// DEFCON levels
enum ENUM_DEFCON_LEVEL {
    DEFCON_GREEN = 0,
    DEFCON_YELLOW = 1,
    DEFCON_ORANGE = 2,
    DEFCON_RED = 3,
    DEFCON_BLACK = 4
};

// Asset classes
enum ENUM_ASSET_CLASS {
    ASSET_FX_MAJOR = 0,
    ASSET_FX_MINOR = 1,
    ASSET_COMMODITY = 2,
    ASSET_INDEX = 3,
    ASSET_CRYPTO = 4,
    ASSET_UNKNOWN = 5
};
```

### Core Structures

```cpp
// State vector (40+ fields)
struct SStateVector {
    ENUM_REGIME current_regime;
    double regime_confidence;
    double z_score_momentum;
    double volatility_z;
    double entropy_score;
    double kurtosis;
    double vpin;
    double mer_score;
    double yang_zhang_vol;
    double hurst_exponent;
    double katz_fractal_dim;
    double sample_entropy;
    double ftle;
    double trend_signal;
    double correlation_energy;
    double system_entropy;
    double bifurcation_proximity;
    double avg_correlation;
    double danger_score;
    double session_progress;
    int volatility_regime;
    datetime timestamp;

    void Init();
    string ToKey(int precision=1) const;
};

// Trade metrics
struct STradeMetrics {
    double entry_price;
    double exit_price;
    double mfe;
    double mae;
    double realized_pnl;
    double r_multiple;
    double path_efficiency;
    double smoothness;
    int bars_held;
    ENUM_REGIME entry_regime;
    ENUM_REGIME exit_regime;
    datetime entry_time;
    datetime exit_time;
};

// Validation result
struct SValidationResult {
    bool passed;
    string reason;
    double final_risk_scalar;
    bool micro_passed;
    bool meso_passed;
    bool macro_passed;
};

// Learning metrics
struct SLearningMetrics {
    double trades_to_convergence;
    double learning_velocity;
    double sample_efficiency_score;
    double state_space_coverage;
    double exploration_diversity;
    double novel_state_discovery_rate;
    double q_value_stability;
    double td_error_trend;
    double bellman_residual;
    double reward_signal_clarity;
    double mfe_capture_improvement;
    double vpin_predictive_accuracy;
    double kurtosis_tail_prediction;
    double fractal_trend_accuracy;
    double entropy_regime_accuracy;
    double adversary_f1_score;
    double adversary_calibration_error;
    double adversary_value_add;
    double replay_diversity;
    double overall_health;
    SSelfHealingTriggers healing;
};

// Risk intelligence
struct SRiskIntelligence {
    double kurtosis_adjusted_var;
    double tail_event_preparedness;
    double correlation_energy;
    double crystallization_proximity;
    double vpin_toxicity_exposure;
    double exit_difficulty_score;
    double regime_stability;
    double system_entropy;
    double bifurcation_proximity;
    double conditional_drawdown_risk;
    double recovery_capacity;
    double underwater_duration;
    double mfe_capture_efficiency;
    double overfitting_score;
    double catastrophic_forgetting_alert;
    double risk_budget_utilization;
    double reserve_capacity;
    ENUM_DEFCON_ALERT defcon_level;
    double overall_risk;
    SRiskAlert alerts[];
};
```

---

## Usage Examples

### Basic Trading Flow

```cpp
#include "Include/Intelligence/CRL_Agent.mqh"
#include "Include/Risk/CThreeLevelRisk.mqh"
#include "Include/Sensing/CMarketAgnostic.mqh"

// Initialize components
CMarketAgnostic* g_sensor = new CMarketAgnostic(_Symbol, _Period);
CRL_Agent* g_agent = new CRL_Agent("main");
CThreeLevelRisk* g_risk = new CThreeLevelRisk();

// In OnTick
void OnTick() {
    // 1. Get state
    SStateVector state = g_sensor->GetStateVector();

    // 2. Choose action
    ENUM_TRADING_ACTION action = g_agent->ChooseAction(state);

    // 3. Validate through risk hierarchy
    SValidationResult result = g_risk->Validate(_Symbol, action, proposed_lots, state, phys);

    if(result.passed) {
        // 4. Execute with adjusted size
        double final_lots = proposed_lots * result.final_risk_scalar;
        ExecuteTrade(action, final_lots);
    }
}
```

### Learning Metrics Monitoring

```cpp
#include "Include/Performance/CLearningMetrics.mqh"

CLearningMetrics* g_metrics = new CLearningMetrics();

// After each trade
void OnTradeComplete(double td_error, double old_q, double new_q) {
    g_metrics->RecordTDError(td_error);
    g_metrics->RecordQChange(old_q, new_q);

    // Check self-healing triggers
    SLearningMetrics m = g_metrics->Calculate();
    if(m.healing.needs_exploration_boost) {
        g_agent->SetEpsilon(0.3);
    }
    if(m.healing.needs_genetic_refresh) {
        g_agent->GeneticRefresh(0.1);
    }

    // Display dashboard
    Print(g_metrics->GenerateDashboard());
}
```

---

*Document prepared by: Project Quantum Development Team*
*Last updated: 2024-12-21*
