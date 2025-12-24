# Rate Limiting Prevention Strategies for ProjectQuantum Docker CI

## Overview

This document outlines strategies implemented to prevent hitting various rate limits in the Docker CI/CD pipeline.

## Rate Limit Types

### 1. Docker Hub Rate Limits

**Problem:**
- Docker Hub limits anonymous users to 100 pulls per 6 hours per IP
- Authenticated users get 200 pulls per 6 hours
- CI/CD pipelines can quickly exhaust these limits

**Solutions Implemented:**

#### A. Use GitHub Container Registry (GHCR)
```yaml
# In docker-mql5-ci.yml
env:
  REGISTRY: ghcr.io  # Using GHCR instead of Docker Hub
  IMAGE_NAME: ${{ toLower(github.repository_owner) }}/mql5-ci
```

**Benefits:**
- No pull rate limits for public images
- Authenticated access via GITHUB_TOKEN
- Better integration with GitHub Actions

#### B. Docker Build Cache
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha  # Use GitHub Actions cache
    cache-to: type=gha,mode=max
```

**Benefits:**
- Reuses layers across builds
- Reduces image pulls
- Faster build times

#### C. Conditional Image Building
```yaml
# Only build on specific branches
on:
  push:
    branches: [main, develop, feature/*]
  pull_request:
    branches: [main, develop]
```

**Benefits:**
- Reduces unnecessary builds
- Conserves rate limits

### 2. GitHub Actions Rate Limits

**Problem:**
- GitHub API has rate limits (5,000 requests/hour for authenticated users)
- Workflow runs consume API quota
- Artifact downloads count toward limits

**Solutions Implemented:**

#### A. Workflow Concurrency Control
```yaml
# Add to workflow files
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

**Benefits:**
- Prevents duplicate workflow runs
- Automatically cancels outdated runs on new pushes
- Reduces API consumption

#### B. Selective Artifact Downloads
```yaml
- name: Download compilation artifacts
  uses: actions/download-artifact@v4
  with:
    name: mql5-compilation-results-${{ github.run_id }}
    path: ./ci-results
  # Only download what's needed, not all artifacts
```

**Benefits:**
- Reduces download bandwidth
- Faster workflow execution
- Lower API usage

#### C. Conditional Job Execution
```yaml
run-tests:
  if: needs.compile-mql5.outputs.compilation-status == 'success'
  needs: [compile-mql5]
```

**Benefits:**
- Skip unnecessary jobs
- Save API quota
- Faster failure feedback

### 3. Backtesting Rate Limits

**Problem:**
- Frequent backtests can consume resources
- May trigger workflow timeout limits
- Can exhaust runner minutes

**Solutions Implemented:**

#### A. Backtest Profiles
```yaml
# In docker-compose.yml
profiles:
  - backtest  # Only run when explicitly requested
```

**Usage:**
```bash
# Manual trigger only
docker-compose --profile backtest up backtest

# Or via GitHub Actions workflow_dispatch
```

**Benefits:**
- Backtests only run on-demand
- No automatic triggering
- Resource conservation

#### B. Backtest Timeouts
```yaml
# In workflow
- name: Run backtest
  timeout-minutes: 15  # Prevent runaway backtests
```

**Benefits:**
- Prevents hanging jobs
- Protects runner minutes
- Fails fast on issues

#### C. Backtest Result Caching
```python
# In backtest_runner.py
class FeedbackLoopManager:
    def _load_history(self):
        """Load historical feedback to avoid redundant runs"""
        if self.feedback_file.exists():
            with open(self.feedback_file, 'r') as f:
                return json.load(f)
        return []
```

**Benefits:**
- Reuse previous results
- Skip redundant backtests
- Historical trend analysis

### 4. GitHub Container Registry Rate Limits

**Problem:**
- While GHCR has generous limits, excessive pulls can still hit quotas
- Private repositories have different limits

**Solutions Implemented:**

#### A. Image Reuse
```yaml
compile-mql5:
  needs: build-ci-container
  run:
    # Reuse the image built in previous job
    ${{ needs.build-ci-container.outputs.image-tag }}
```

**Benefits:**
- Single build, multiple uses
- No redundant pulls
- Consistent image across jobs

#### B. Layer Caching
```dockerfile
# In Dockerfile.mql5-ci
# Order layers from least to most frequently changing
RUN apt-get update && apt-get install -y ...  # Rarely changes
COPY requirements.txt ...                      # Changes occasionally
COPY . /workspace                              # Changes frequently
```

**Benefits:**
- Efficient layer reuse
- Faster builds
- Reduced bandwidth

### 5. Wine/MT5 Download Rate Limits

**Problem:**
- Downloading Wine and MT5 in every build is slow and bandwidth-intensive
- External download servers may have rate limits

**Solutions Implemented:**

#### A. Persistent Volumes
```yaml
volumes:
  mql5-wine-prefix:
    driver: local
    name: projectquantum-wine-prefix
  
  mql5-installation:
    driver: local
    name: projectquantum-mt5
```

**Benefits:**
- One-time installation
- Persistent across container restarts
- No repeated downloads

#### B. Dockerfile Layer Optimization
```dockerfile
# Install Wine once in base layer
RUN apt-get update && apt-get install -y wine64 winetricks
# This layer is cached and reused
```

**Benefits:**
- Cached installation
- Faster subsequent builds
- Reduced external downloads

## Best Practices

### 1. Workflow Triggers

**Minimize Trigger Events:**
```yaml
# Be selective about triggers
on:
  push:
    branches: [main, develop]  # Not feature/*
    paths:
      - 'MQL5/**'              # Only on relevant changes
      - 'Tools/**'
      - 'Dockerfile.mql5-ci'
```

### 2. Manual Triggers for Expensive Operations

**Use workflow_dispatch for backtests:**
```yaml
on:
  workflow_dispatch:
    inputs:
      run_backtest:
        description: 'Run backtest?'
        required: false
        default: false
        type: boolean
```

### 3. Scheduled Cleanup

**Periodic artifact cleanup:**
```yaml
- name: Upload artifacts
  with:
    retention-days: 7  # Auto-delete after 7 days
```

### 4. Monitoring

**Track usage:**
```bash
# Check GitHub API rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit
```

## Configuration Recommendations

### For Development

```bash
# Use local Docker builds
./Tools/docker/mql5-docker.sh build

# Run compilation locally
./Tools/docker/mql5-docker.sh compile

# Only push to CI when ready
git push origin feature-branch
```

### For CI/CD

```yaml
# Recommended workflow settings
env:
  CACHE_KEY: ${{ runner.os }}-docker-${{ hashFiles('Dockerfile.mql5-ci') }}

jobs:
  build:
    timeout-minutes: 30  # Prevent runaway jobs
    concurrency:
      group: build-${{ github.ref }}
      cancel-in-progress: true
```

### For Backtesting

```bash
# Run backtests locally first
docker-compose --profile backtest up backtest

# Only run in CI for major releases
# Use workflow_dispatch for manual triggering
```

## Monitoring Rate Limits

### GitHub Actions

```bash
# Check workflow usage
gh api /repos/:owner/:repo/actions/billing/usage

# Check package (Docker) usage
gh api /users/:owner/settings/billing/packages
```

### Docker Registry

```bash
# Check GHCR rate limit (none for public images)
# Private images: check GitHub billing page
```

## Emergency Mitigation

If rate limits are hit:

1. **Pause non-critical workflows**
   ```bash
   # Disable workflow
   gh workflow disable "Workflow Name"
   ```

2. **Use workflow concurrency**
   ```yaml
   concurrency:
     group: emergency-${{ github.ref }}
     cancel-in-progress: true
   ```

3. **Switch to on-demand execution**
   - Change all workflows to `workflow_dispatch`
   - Remove automatic triggers temporarily

4. **Reduce artifact retention**
   ```yaml
   retention-days: 1  # Minimum retention
   ```

5. **Use self-hosted runners** (if applicable)
   - No GitHub Actions minutes consumed
   - Local Docker registry caching

## Summary

The implemented rate limiting prevention strategies include:

✅ **GHCR instead of Docker Hub** - No pull rate limits  
✅ **Docker build caching** - Reduced rebuilds  
✅ **Workflow concurrency control** - Prevent duplicate runs  
✅ **Selective job execution** - Only run when needed  
✅ **Backtest profiles** - On-demand execution only  
✅ **Persistent volumes** - One-time installations  
✅ **Artifact retention policies** - Auto-cleanup  
✅ **Conditional triggers** - Minimize unnecessary runs  

These strategies ensure the Docker CI pipeline remains efficient and avoids hitting rate limits while maintaining full functionality.
