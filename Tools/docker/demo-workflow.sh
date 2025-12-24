#!/bin/bash
# Docker Development Workflow Demo
# This script demonstrates a complete Docker-based development workflow

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ProjectQuantum Docker Workflow Demo${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not installed. Please install docker-compose first."
    exit 1
fi

echo -e "${GREEN}✅ Docker and docker-compose are available${NC}"
echo ""

# Step 2: Build the image
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
echo "This step creates the MQL5 compilation environment."
echo ""
echo "Command: ./Tools/docker/mql5-docker.sh build"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to actually build:
# cd "$PROJECT_ROOT"
# ./Tools/docker/mql5-docker.sh build

echo -e "${GREEN}✅ Image would be built here (skipped in demo)${NC}"
echo ""

# Step 3: Compile the code
echo -e "${YELLOW}Step 3: Compiling MQL5 code...${NC}"
echo "This step compiles all MQL5 files in a Docker container."
echo ""
echo "Command: ./Tools/docker/mql5-docker.sh compile"
echo ""
read -p "Press Enter to continue..."
echo ""

# Uncomment to actually compile:
# cd "$PROJECT_ROOT"
# ./Tools/docker/mql5-docker.sh compile

echo -e "${GREEN}✅ Code would be compiled here (skipped in demo)${NC}"
echo ""

# Step 4: Run tests
echo -e "${YELLOW}Step 4: Running unit tests...${NC}"
echo "This step executes the test suite in the Docker container."
echo ""
echo "Command: ./Tools/docker/mql5-docker.sh test core"
echo ""
read -p "Press Enter to continue..."
echo ""

# Uncomment to actually run tests:
# cd "$PROJECT_ROOT"
# ./Tools/docker/mql5-docker.sh test core

echo -e "${GREEN}✅ Tests would run here (skipped in demo)${NC}"
echo ""

# Step 5: Feedback monitoring
echo -e "${YELLOW}Step 5: Feedback Loop Monitoring${NC}"
echo "During development, you can monitor compilation feedback in real-time."
echo ""
echo "Terminal 1: Start watch mode"
echo "  ./Tools/docker/mql5-docker.sh watch"
echo ""
echo "Terminal 2: Monitor feedback"
echo "  python3 Tools/docker/feedback_monitor.py --watch"
echo ""
echo "Terminal 3: View in browser"
echo "  ./Tools/docker/mql5-docker.sh viewer"
echo "  Open http://localhost:8080"
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 6: Interactive shell
echo -e "${YELLOW}Step 6: Interactive Development${NC}"
echo "You can open an interactive shell in the container for debugging."
echo ""
echo "Command: ./Tools/docker/mql5-docker.sh shell"
echo ""
echo "Inside the shell, you have access to:"
echo "  - /workspace/MQL5 (your source code)"
echo "  - /opt/wine/drive_c/MT5 (MT5 installation)"
echo "  - /results (compilation results)"
echo ""
read -p "Press Enter to continue..."
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Workflow Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "1. One-time setup:"
echo "   ./Tools/docker/mql5-docker.sh build"
echo ""
echo "2. Daily development:"
echo "   ./Tools/docker/mql5-docker.sh watch       # Auto-recompile"
echo "   python3 Tools/docker/feedback_monitor.py --watch  # Monitor"
echo ""
echo "3. Testing:"
echo "   ./Tools/docker/mql5-docker.sh test [suite]"
echo ""
echo "4. Cleanup:"
echo "   ./Tools/docker/mql5-docker.sh clean"
echo ""
echo -e "${GREEN}✅ Demo complete!${NC}"
echo ""
echo "For more information:"
echo "  • Read Tools/docker/README.md"
echo "  • Run ./Tools/docker/mql5-docker.sh help"
echo "  • Check the main README.md Docker section"
echo ""
