# Docker-Based MQL5 Development Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ProjectQuantum Docker Architecture                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Developer Workstation                                                   │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Terminal 1 │  │   Terminal 2 │  │   Browser    │                  │
│  │              │  │              │  │              │                  │
│  │  Watch Mode  │  │   Feedback   │  │  Dashboard   │                  │
│  │    mql5-     │  │   Monitor    │  │  :8080       │                  │
│  │  docker.sh   │  │    .py       │  │              │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                  │                          │
└─────────┼─────────────────┼──────────────────┼──────────────────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Docker Compose Services                                                 │
│                                                                          │
│  ┌────────────────────┐  ┌────────────────┐  ┌─────────────────┐       │
│  │   mql5-ci          │  │   watcher      │  │  log-viewer     │       │
│  │  (Main Service)    │  │   (Optional)   │  │  (nginx)        │       │
│  │                    │  │                │  │                 │       │
│  │  • Compilation     │  │  • inotifywait │  │  • Dashboard    │       │
│  │  • Testing         │  │  • Auto-trigger│  │  • JSON viewer  │       │
│  │  • Validation      │  │  • File watch  │  │  • Logs         │       │
│  │                    │  │                │  │                 │       │
│  │  Wine + MT5        │  │  Triggers ────►│  │  Port 8080      │       │
│  │  Xvfb Display      │  │  Recompile     │  │                 │       │
│  └────────┬───────────┘  └────────────────┘  └─────────┬───────┘       │
│           │                                              │               │
└───────────┼──────────────────────────────────────────────┼───────────────┘
            │                                              │
            ▼                                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Volumes & Mounts                                                        │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Source Code    │  │  Results        │  │  Persistent     │         │
│  │  (Read-Only)    │  │  (Read-Write)   │  │  Volumes        │         │
│  │                 │  │                 │  │                 │         │
│  │  MQL5/          │  │  ci-results/    │  │  Wine Prefix    │         │
│  │  Tools/         │  │  logs/          │  │  MT5 Install    │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Feedback Loop Flow                                                      │
│                                                                          │
│  1. Developer edits MQL5 file                                           │
│                    ↓                                                     │
│  2. Watcher detects change (inotifywait)                                │
│                    ↓                                                     │
│  3. Triggers compilation in mql5-ci container                           │
│                    ↓                                                     │
│  4. Results written to ci-results/                                      │
│                    ↓                                                     │
│  5. Feedback monitor reads results                                      │
│                    ↓                                                     │
│  6. Terminal displays status                                            │
│                    ↓                                                     │
│  7. Web dashboard auto-refreshes                                        │
│                    ↓                                                     │
│  8. Developer sees instant feedback                                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Key Components                                                          │
│                                                                          │
│  Helper Scripts                  Configuration Files                    │
│  • mql5-docker.sh               • docker-compose.yml                    │
│  • feedback_monitor.py          • Dockerfile.mql5-ci                    │
│  • demo-workflow.sh             • nginx.conf                            │
│                                                                          │
│  Web Interface                   Output Files                           │
│  • index.html (dashboard)       • compilation-report.json               │
│  • nginx (server)               • test-report.json                      │
│  • Auto-refresh (10s)           • *.log files                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  CI/CD Integration                                                       │
│                                                                          │
│  GitHub Actions Workflow                                                │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  1. Trigger: Push/PR                                      │          │
│  │       ↓                                                   │          │
│  │  2. Build Docker Image                                    │          │
│  │       ↓                                                   │          │
│  │  3. Run Compilation (same container as local)            │          │
│  │       ↓                                                   │          │
│  │  4. Execute Tests (matrix: core, intelligence, etc.)     │          │
│  │       ↓                                                   │          │
│  │  5. Generate Reports                                      │          │
│  │       ↓                                                   │          │
│  │  6. Upload Artifacts                                      │          │
│  │       ↓                                                   │          │
│  │  7. Comment on PR with results                           │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                          │
│  Same Docker image → Consistent results local & CI                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Command Reference                                                       │
│                                                                          │
│  Setup                   Development              Utilities             │
│  • build                • watch                  • shell                │
│                         • compile                • logs                 │
│  Testing                                         • status               │
│  • test [suite]         Viewing                  • clean                │
│                         • viewer                                        │
└─────────────────────────────────────────────────────────────────────────┘
```
