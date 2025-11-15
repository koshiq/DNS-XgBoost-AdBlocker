#!/bin/bash
#
# DNS Ad Blocker - Startup Script
# Starts the DNS blocker server in the background
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="$SCRIPT_DIR/dns_blocker_server.py"
PID_FILE="$SCRIPT_DIR/dns_blocker.pid"
LOG_FILE="$SCRIPT_DIR/dns_blocker.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           DNS AD BLOCKER - STARTUP SCRIPT                         ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}[WARNING]${NC} DNS blocker is already running (PID: $PID)"
        echo -e "${YELLOW}[INFO]${NC} To stop it, run: ./stop_blocker.sh"
        exit 1
    else
        # PID file exists but process is not running
        rm "$PID_FILE"
    fi
fi

# Check if Python script exists
if [ ! -f "$SERVER_SCRIPT" ]; then
    echo -e "${RED}[ERROR]${NC} Server script not found: $SERVER_SCRIPT"
    exit 1
fi

# Get the user who invoked sudo (if applicable)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)

# Check Python dependencies (use user's environment if running as sudo)
echo -e "${GREEN}[CHECK]${NC} Verifying dependencies..."
if [ -n "$SUDO_USER" ]; then
    # Running with sudo - check user's Python environment
    sudo -u "$SUDO_USER" python3 -c "import xgboost, pandas, tldextract" 2>/dev/null
else
    python3 -c "import xgboost, pandas, tldextract" 2>/dev/null
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Missing Python dependencies in user environment"
    echo -e "${YELLOW}[INFO]${NC} Install with: pip3 install xgboost pandas tldextract"
    if [ -n "$SUDO_USER" ]; then
        echo -e "${YELLOW}[INFO]${NC} Or run as user: sudo -u $SUDO_USER pip3 install xgboost pandas tldextract"
    fi
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Dependencies verified"

# Start the server in background
echo -e "${GREEN}[START]${NC} Starting DNS blocker server..."

# Use sudo -E to preserve environment if running as sudo, otherwise run normally
if [ -n "$SUDO_USER" ]; then
    # Preserve user's Python path when running with sudo
    sudo -u "$SUDO_USER" PYTHONPATH="$ACTUAL_HOME/.local/lib/python3.14/site-packages:$PYTHONPATH" nohup python3 "$SERVER_SCRIPT" > "$LOG_FILE" 2>&1 &
else
    nohup python3 "$SERVER_SCRIPT" > "$LOG_FILE" 2>&1 &
fi
SERVER_PID=$!

# Save PID
echo $SERVER_PID > "$PID_FILE"

# Wait a moment to check if it started successfully
sleep 2

if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo -e "${GREEN}[SUCCESS]${NC} DNS blocker started successfully!"
    echo -e "${GREEN}[INFO]${NC} PID: $SERVER_PID"
    echo -e "${GREEN}[INFO]${NC} Log file: $LOG_FILE"
    echo -e "${GREEN}[INFO]${NC} Running on: 127.0.0.1:9053"
    echo ""
    echo -e "${YELLOW}[NEXT STEPS]${NC}"
    echo "  1. Monitor logs: tail -f $LOG_FILE"
    echo "  2. Test blocking: dig @127.0.0.1 -p 9053 googleads.g.doubleclick.net"
    echo "  3. Stop server: ./stop_blocker.sh"
    echo ""
else
    echo -e "${RED}[ERROR]${NC} Failed to start DNS blocker"
    echo -e "${YELLOW}[INFO]${NC} Check log file: $LOG_FILE"
    rm "$PID_FILE"
    exit 1
fi
