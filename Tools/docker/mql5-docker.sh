#!/bin/bash
# ProjectQuantum Docker Helper Script
# Provides easy commands for Docker-based MQL5 development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Command functions
cmd_build() {
    print_header "Building MQL5 CI Docker Image"
    
    export BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    export VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export BUILD_NUMBER=${BUILD_NUMBER:-0}
    
    docker-compose build mql5-ci
    
    print_success "Docker image built successfully"
}

cmd_compile() {
    print_header "Running MQL5 Compilation"
    
    # Create results directory
    mkdir -p "${PROJECT_ROOT}/ci-results"
    
    # Run compilation
    docker-compose run --rm mql5-ci /opt/mql5-ci/run-ci.sh
    
    # Display results
    if [[ -f "${PROJECT_ROOT}/ci-results/compilation-report.json" ]]; then
        print_success "Compilation completed"
        
        # Parse and display summary
        if command -v jq &> /dev/null; then
            STATUS=$(jq -r '.main_ea.status' "${PROJECT_ROOT}/ci-results/compilation-report.json")
            ERRORS=$(jq -r '.summary.total_errors' "${PROJECT_ROOT}/ci-results/compilation-report.json")
            WARNINGS=$(jq -r '.summary.total_warnings' "${PROJECT_ROOT}/ci-results/compilation-report.json")
            
            echo ""
            echo "Status:   $STATUS"
            echo "Errors:   $ERRORS"
            echo "Warnings: $WARNINGS"
            
            if [[ "$STATUS" == "success" ]]; then
                print_success "All files compiled successfully!"
            else
                print_error "Compilation failed with errors"
                exit 1
            fi
        fi
    else
        print_error "Compilation report not found"
        exit 1
    fi
}

cmd_test() {
    print_header "Running MQL5 Unit Tests"
    
    TEST_SUITE=${1:-all}
    
    mkdir -p "${PROJECT_ROOT}/ci-results"
    
    docker-compose run --rm \
        -e TEST_FILTER="${TEST_SUITE}" \
        mql5-ci /opt/mql5-ci/run-tests.sh
    
    # Display test results
    if [[ -f "${PROJECT_ROOT}/ci-results/test-report.json" ]]; then
        print_success "Tests completed"
        
        if command -v jq &> /dev/null; then
            TOTAL=$(jq -r '.summary.total' "${PROJECT_ROOT}/ci-results/test-report.json")
            PASSED=$(jq -r '.summary.passed' "${PROJECT_ROOT}/ci-results/test-report.json")
            FAILED=$(jq -r '.summary.failed' "${PROJECT_ROOT}/ci-results/test-report.json")
            
            echo ""
            echo "Total:  $TOTAL"
            echo "Passed: $PASSED"
            echo "Failed: $FAILED"
            
            if [[ "$FAILED" -eq 0 ]]; then
                print_success "All tests passed!"
            else
                print_error "$FAILED test(s) failed"
                exit 1
            fi
        fi
    fi
}

cmd_watch() {
    print_header "Starting Watch Mode"
    print_info "Auto-recompilation enabled. Press Ctrl+C to stop."
    
    mkdir -p "${PROJECT_ROOT}/ci-results"
    mkdir -p "${PROJECT_ROOT}/logs"
    
    # Start with watch profile
    docker-compose --profile watch up watcher
}

cmd_shell() {
    print_header "Opening Interactive Shell"
    
    docker-compose run --rm mql5-ci /bin/bash
}

cmd_logs() {
    print_header "Viewing Docker Logs"
    
    docker-compose logs -f mql5-ci
}

cmd_clean() {
    print_header "Cleaning Docker Resources"
    
    read -p "This will remove containers, volumes, and results. Continue? (y/N) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        rm -rf "${PROJECT_ROOT}/ci-results"
        rm -rf "${PROJECT_ROOT}/logs"
        
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

cmd_viewer() {
    print_header "Starting Log Viewer"
    
    mkdir -p "${PROJECT_ROOT}/ci-results"
    mkdir -p "${PROJECT_ROOT}/logs"
    
    docker-compose up -d log-viewer
    
    print_success "Log viewer started at http://localhost:8080"
    print_info "Press Ctrl+C to stop"
    
    # Wait for Ctrl+C
    trap "docker-compose stop log-viewer; exit 0" INT TERM
    
    while true; do
        sleep 1
    done
}

cmd_backtest() {
    print_header "Running Backtests"
    
    EXPERT=${1:-Project_Quantum}
    CONFIG=${2:-}
    
    mkdir -p "${PROJECT_ROOT}/ci-results/backtests"
    
    # Build command
    CMD="/opt/mql5-ci/run-backtest.sh $EXPERT"
    if [[ -n "$CONFIG" ]]; then
        CMD="$CMD $CONFIG"
    fi
    
    docker-compose --profile backtest run --rm backtest bash -c "$CMD"
    
    # Display backtest results
    if [[ -f "${PROJECT_ROOT}/ci-results/backtests/feedback_report.md" ]]; then
        print_success "Backtest completed"
        echo ""
        cat "${PROJECT_ROOT}/ci-results/backtests/feedback_report.md"
    else
        print_error "Backtest report not found"
        exit 1
    fi
}

cmd_status() {
    print_header "Docker Container Status"
    
    docker-compose ps
    
    echo ""
    
    # Check for results
    if [[ -f "${PROJECT_ROOT}/ci-results/compilation-report.json" ]]; then
        print_info "Latest compilation report available"
    fi
    
    if [[ -f "${PROJECT_ROOT}/ci-results/test-report.json" ]]; then
        print_info "Latest test report available"
    fi
}

cmd_help() {
    cat << 'EOFHELP'
ProjectQuantum Docker Helper

Usage: $0 <command> [options]

Commands:
  build       Build the Docker image
  compile     Run MQL5 compilation
  test        Run unit tests [suite_name]
  backtest    Run backtests [expert_name] [config_file]
  watch       Start auto-recompilation on file changes
  shell       Open interactive shell in container
  logs        View container logs
  viewer      Start web-based log viewer
  status      Show container and build status
  clean       Remove containers, volumes, and results
  help        Show this help message

Examples:
  $0 build                           # Build the Docker image
  $0 compile                         # Compile all MQL5 files
  $0 test core                       # Run core test suite
  $0 backtest Project_Quantum        # Run backtest with default config
  $0 backtest Project_Quantum fast   # Run backtest with fast config
  $0 watch                           # Start watch mode
  $0 shell                           # Interactive development shell
  $0 viewer                          # Open log viewer at http://localhost:8080

For more information, see Tools/docker/README.md
EOFHELP
}

# Main command dispatcher
main() {
    cd "$PROJECT_ROOT"
    
    case "${1:-help}" in
        build)
            cmd_build
            ;;
        compile)
            cmd_compile
            ;;
        test)
            cmd_test "${2:-all}"
            ;;
        backtest)
            cmd_backtest "${2:-Project_Quantum}" "${3:-}"
            ;;
        watch)
            cmd_watch
            ;;
        shell)
            cmd_shell
            ;;
        logs)
            cmd_logs
            ;;
        viewer)
            cmd_viewer
            ;;
        status)
            cmd_status
            ;;
        clean)
            cmd_clean
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
