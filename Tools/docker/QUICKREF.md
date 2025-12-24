# Docker Quick Reference Card

## 🚀 Essential Commands

### Setup (One-Time)
```bash
./Tools/docker/mql5-docker.sh build
```

### Daily Development
```bash
# Terminal 1: Watch mode (auto-recompile on changes)
./Tools/docker/mql5-docker.sh watch

# Terminal 2: Real-time feedback
python3 Tools/docker/feedback_monitor.py --watch

# Terminal 3: Web viewer
./Tools/docker/mql5-docker.sh viewer
# Open http://localhost:8080
```

### Manual Operations
```bash
# Compile once
./Tools/docker/mql5-docker.sh compile

# Run all tests
./Tools/docker/mql5-docker.sh test

# Run specific test suite
./Tools/docker/mql5-docker.sh test core
./Tools/docker/mql5-docker.sh test intelligence
./Tools/docker/mql5-docker.sh test physics
```

### Debugging
```bash
# Interactive shell
./Tools/docker/mql5-docker.sh shell

# View logs
./Tools/docker/mql5-docker.sh logs

# Check status
./Tools/docker/mql5-docker.sh status
```

### Cleanup
```bash
# Remove containers and volumes
./Tools/docker/mql5-docker.sh clean
```

## 📊 Results Location

- **Compilation Report**: `ci-results/compilation-report.json`
- **Test Report**: `ci-results/test-report.json`
- **Logs**: `logs/`
- **Web Viewer**: http://localhost:8080

## 🎯 Common Workflows

### First-Time Setup
```bash
# 1. Build image
./Tools/docker/mql5-docker.sh build

# 2. Test compilation
./Tools/docker/mql5-docker.sh compile

# 3. Run tests
./Tools/docker/mql5-docker.sh test
```

### Active Development
```bash
# Start watch mode in background
./Tools/docker/mql5-docker.sh watch &

# Monitor in foreground
python3 Tools/docker/feedback_monitor.py --watch

# Edit your files - changes trigger automatic recompilation
```

### Pre-Commit Validation
```bash
# Quick compilation check
./Tools/docker/mql5-docker.sh compile

# Run all tests
./Tools/docker/mql5-docker.sh test

# Check results
cat ci-results/compilation-report.json | jq '.summary'
```

### CI/CD Pipeline Simulation
```bash
# Build
./Tools/docker/mql5-docker.sh build

# Compile
./Tools/docker/mql5-docker.sh compile

# Test (multiple suites)
for suite in core intelligence physics risk safety; do
    ./Tools/docker/mql5-docker.sh test $suite
done

# Generate report
python3 Tools/docker/feedback_monitor.py
```

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check Docker daemon
docker info

# Rebuild without cache
docker-compose build --no-cache mql5-ci
```

### Compilation Errors
```bash
# View detailed logs
cat ci-results/compilation-report.json | jq '.'

# Open shell for debugging
./Tools/docker/mql5-docker.sh shell
```

### Permission Issues
```bash
# Fix on Linux
sudo chown -R $USER:$USER ci-results logs

# Clean and restart
./Tools/docker/mql5-docker.sh clean
./Tools/docker/mql5-docker.sh build
```

## 📚 Documentation

- Full Docker Guide: `Tools/docker/README.md`
- Main README Docker Section: `README.md`
- CI/CD Guide: `.github/CI_CD_GUIDE.md`
- Dockerfile: `Dockerfile.mql5-ci`
- Compose File: `docker-compose.yml`

## 💡 Tips

- Use **watch mode** for instant feedback during development
- Run **feedback monitor** to see real-time compilation status
- Use **web viewer** to browse results visually
- Open **interactive shell** when debugging complex issues
- **Clean regularly** to free up disk space

## ⚙️ Environment Variables

```bash
# Control build
export BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
export VCS_REF=$(git rev-parse --short HEAD)
export BUILD_NUMBER=123

# Control runtime
export CI_MODE=true
export WATCH_MODE=true
export AUTO_COMPILE=true
```

## 🔗 Quick Links

- Docker Helper: `./Tools/docker/mql5-docker.sh help`
- Feedback Monitor: `python3 Tools/docker/feedback_monitor.py --help`
- Demo Workflow: `./Tools/docker/demo-workflow.sh`
