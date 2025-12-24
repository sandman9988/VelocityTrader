# Docker-Based MQL5 Development Environment

This directory contains Docker-based tooling for ProjectQuantum MQL5 development, compilation, testing, and backtesting.

## 🎯 Overview

The Docker-based development environment provides:

- **Isolated Build Environment**: Consistent compilation across different machines
- **Continuous Integration**: Automated testing and validation
- **Backtesting Infrastructure**: Run strategy backtests with performance analysis
- **Feedback Loops**: Real-time compilation, test results, and performance metrics
- **Watch Mode**: Auto-recompilation on file changes
- **Web-Based Viewer**: Browse compilation results and logs in your browser
- **Rate Limit Prevention**: Optimized CI/CD to avoid GitHub/Docker rate limits

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- At least 4GB of available RAM
- 10GB of free disk space

### Basic Commands

```bash
# Build the Docker image
./Tools/docker/mql5-docker.sh build

# Compile all MQL5 files
./Tools/docker/mql5-docker.sh compile

# Run unit tests
./Tools/docker/mql5-docker.sh test

# Run backtests
./Tools/docker/mql5-docker.sh backtest Project_Quantum

# Start watch mode (auto-recompile on changes)
./Tools/docker/mql5-docker.sh watch

# Open interactive shell
./Tools/docker/mql5-docker.sh shell

# View results in browser
./Tools/docker/mql5-docker.sh viewer
# Then open http://localhost:8080
```

## 📋 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `build` | Build the Docker image | `./mql5-docker.sh build` |
| `compile` | Compile all MQL5 files | `./mql5-docker.sh compile` |
| `test` | Run unit tests | `./mql5-docker.sh test core` |
| `backtest` | Run backtests | `./mql5-docker.sh backtest Project_Quantum` |
| `watch` | Auto-recompile on file changes | `./mql5-docker.sh watch` |
| `shell` | Open interactive shell | `./mql5-docker.sh shell` |
| `logs` | View container logs | `./mql5-docker.sh logs` |
| `viewer` | Start web-based log viewer | `./mql5-docker.sh viewer` |
| `status` | Show container status | `./mql5-docker.sh status` |
| `clean` | Remove containers & volumes | `./mql5-docker.sh clean` |

## 🔄 Development Workflow

### Local Development with Feedback Loop

1. **Start the environment:**
   ```bash
   ./Tools/docker/mql5-docker.sh build
   ```

2. **Enable watch mode:**
   ```bash
   ./Tools/docker/mql5-docker.sh watch
   ```

3. **Monitor feedback (in another terminal):**
   ```bash
   python3 Tools/docker/feedback_monitor.py --watch
   ```

4. **Edit your MQL5 files** - Changes will trigger automatic recompilation

5. **View results** at http://localhost:8080 (if log viewer is running)

### Backtesting Workflow

1. **Run a backtest with default configuration:**
   ```bash
   ./Tools/docker/mql5-docker.sh backtest Project_Quantum
   ```

2. **Run a backtest with specific configuration:**
   ```bash
   ./Tools/docker/mql5-docker.sh backtest Project_Quantum fast
   ```

3. **View backtest results:**
   - Results saved to `ci-results/backtests/`
   - Feedback report at `ci-results/backtests/feedback_report.md`
   - Performance metrics in JSON format

### Manual Compilation

```bash
# Compile once
./Tools/docker/mql5-docker.sh compile

# View results
cat ci-results/compilation-report.json | jq '.'
```

### Running Specific Test Suites

```bash
# Run core tests
./Tools/docker/mql5-docker.sh test core

# Run intelligence tests
./Tools/docker/mql5-docker.sh test intelligence

# Run all tests
./Tools/docker/mql5-docker.sh test all
```

## 🐳 Docker Compose Services

### mql5-ci

Main compilation and testing service.

**Volumes:**
- `./MQL5` → `/workspace/MQL5` (read-only)
- `./Tools` → `/workspace/Tools` (read-only)
- `./ci-results` → `/results` (read-write)
- `./logs` → `/workspace/logs` (read-write)

**Environment Variables:**
- `CI_MODE`: Set to `true` for CI pipelines
- `WATCH_MODE`: Enable auto-recompilation
- `AUTO_COMPILE`: Auto-compile on startup

### log-viewer

Web-based viewer for compilation results and logs with a modern dashboard interface.

**Access:** http://localhost:8080

**Features:**
- 📊 Real-time status dashboard
- 🔄 Auto-refresh every 10 seconds
- 📁 Directory browsing for logs and results
- 📄 JSON report viewing

**Endpoints:**
- `/` - Dashboard (index.html)
- `/results/` - Compilation results and reports
- `/logs/` - Compilation and test logs

### watcher

File watcher service for auto-recompilation.

**Usage:**
```bash
docker-compose --profile watch up watcher
```

## 📊 Feedback Loop Monitor

The feedback monitor provides real-time updates on compilation and test status.

### One-Time Status Check

```bash
python3 Tools/docker/feedback_monitor.py
```

### Continuous Monitoring

```bash
python3 Tools/docker/feedback_monitor.py --watch
```

### Custom Interval

```bash
python3 Tools/docker/feedback_monitor.py --watch --interval 10
```

## 🎨 Output and Results

### Compilation Results

**Location:** `ci-results/compilation-report.json`

**Structure:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "main_ea": {
    "file": "Project_Quantum.mq5",
    "status": "success",
    "errors": 0,
    "warnings": 0
  },
  "summary": {
    "total_files": 50,
    "compiled_files": 50,
    "total_errors": 0,
    "total_warnings": 2,
    "compilation_time": 45,
    "status": "success"
  }
}
```

### Test Results

**Location:** `ci-results/test-report.json`

**Structure:**
```json
{
  "timestamp": "2024-01-01T12:05:00Z",
  "suite": "core",
  "summary": {
    "total": 15,
    "passed": 14,
    "failed": 1,
    "skipped": 0
  },
  "tests": [
    {
      "name": "Test_SafeMath",
      "status": "passed",
      "duration": 0.1
    }
  ]
}
```

## 🔧 Advanced Usage

### Interactive Development Shell

```bash
# Open shell in the container
./Tools/docker/mql5-docker.sh shell

# Inside the container:
cd /opt/wine/drive_c/MT5/MQL5
ls -la Experts/ProjectQuantum_CI/
```

### Custom Docker Commands

```bash
# Run with custom environment
docker-compose run --rm \
  -e CI_MODE=true \
  -e WATCH_MODE=false \
  mql5-ci /opt/mql5-ci/run-ci.sh

# Run with custom mount
docker-compose run --rm \
  -v $(pwd)/custom-scripts:/scripts:ro \
  mql5-ci bash -c "/scripts/my-script.sh"
```

### Direct Docker Usage

```bash
# Build image directly
docker build -t projectquantum/mql5-ci:latest -f Dockerfile.mql5-ci .

# Run container directly
docker run --rm \
  -v $(pwd)/MQL5:/workspace/MQL5:ro \
  -v $(pwd)/ci-results:/results:rw \
  projectquantum/mql5-ci:latest \
  /opt/mql5-ci/run-ci.sh
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check Docker daemon
docker info

# Check available resources
docker system df

# Rebuild without cache
docker-compose build --no-cache mql5-ci
```

### Compilation Errors

```bash
# View detailed logs
./Tools/docker/mql5-docker.sh logs

# Check results
cat ci-results/compilation-report.json | jq '.main_ea'

# Open shell and debug
./Tools/docker/mql5-docker.sh shell
```

### Volume Permission Issues

```bash
# Fix permissions on Linux
sudo chown -R $USER:$USER ci-results logs

# On Windows, run Docker Desktop as administrator
```

### Clean Start

```bash
# Remove all containers and volumes
./Tools/docker/mql5-docker.sh clean

# Rebuild from scratch
./Tools/docker/mql5-docker.sh build
```

## 🔐 Security Considerations

- Source code is mounted **read-only** to prevent accidental modifications
- Results and logs are written to designated output directories only
- Container runs with minimal privileges
- No secrets or credentials are stored in the image

## 🏗️ Architecture

```
ProjectQuantum/
├── Dockerfile.mql5-ci          # Main Docker image definition
├── docker-compose.yml          # Service orchestration
├── Tools/docker/
│   ├── mql5-docker.sh         # Helper script
│   ├── feedback_monitor.py    # Feedback loop monitor
│   ├── nginx.conf             # Log viewer configuration
│   └── README.md              # This file
├── MQL5/                       # Source code (read-only mount)
├── ci-results/                 # Compilation results (output)
└── logs/                       # Logs (output)
```

## 📚 Additional Resources

- [Main CI/CD Guide](../../.github/CI_CD_GUIDE.md)
- [Dockerfile Reference](../../Dockerfile.mql5-ci)
- [GitHub Workflow](../../.github/workflows/docker-mql5-ci.yml)
- [ProjectQuantum README](../../README.md)

## 🤝 Contributing

When adding Docker-related features:

1. Update this README
2. Test with `./Tools/docker/mql5-docker.sh build`
3. Verify all commands work
4. Update docker-compose.yml if needed
5. Document any new environment variables

## ⚡ Rate Limiting Prevention

The Docker CI implementation includes comprehensive rate limiting prevention strategies:

- **Workflow Concurrency**: Automatic cancellation of duplicate runs
- **Path-Based Triggers**: Only runs on relevant file changes (MQL5, Tools, Docker files)
- **Timeout Controls**: All jobs have timeouts to prevent runaway processes
- **Artifact Optimization**: Reduced retention periods and compression enabled
- **Parallel Execution Limits**: Max 3 concurrent test jobs
- **Backtesting**: Manual trigger only, not automatic on every commit
- **GHCR Usage**: GitHub Container Registry has no pull rate limits

**For detailed information**, see [RATE_LIMITING.md](RATE_LIMITING.md) which covers:
- All rate limit types and solutions
- Monitoring commands
- Emergency mitigation strategies
- Best practices for CI/CD

## 📝 Notes

- **Wine Limitation**: The Docker image uses Wine to run Windows-based MetaEditor. Full compilation may not work without a licensed MetaEditor installation.
- **Syntax Checking**: The current implementation focuses on syntax validation and basic checks.
- **Production Use**: For production compilation, use the self-hosted Windows runner with actual MetaEditor.
- **Backtesting**: Backtests simulate results until actual MT5 terminal integration is added.

## 🎯 Future Enhancements

- [ ] Actual MetaEditor integration (requires licensing)
- [ ] Real MT5 terminal backtesting with historical data
- [ ] Parallel test execution
- [ ] Performance benchmarking
- [ ] Coverage reporting
- [ ] Integration with VS Code Dev Containers
- [ ] ARM64 support for Apple Silicon
