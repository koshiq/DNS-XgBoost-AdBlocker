#!/bin/bash
#
# DNS Ad Blocker - Stop Script
# Stops the running DNS blocker server
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/dns_blocker.pid"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[STOP]${NC} Stopping DNS blocker server..."

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${RED}[ERROR]${NC} PID file not found. Server may not be running."
    exit 1
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ps -p "$PID" > /dev/null 2>&1; then
    # Kill the process
    kill "$PID"

    # Wait for process to stop
    for i in {1..5}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}[WARN]${NC} Process not responding, forcing shutdown..."
        kill -9 "$PID"
    fi

    echo -e "${GREEN}[SUCCESS]${NC} DNS blocker stopped (PID: $PID)"
else
    echo -e "${YELLOW}[WARN]${NC} Process not running (PID: $PID)"
fi

# Remove PID file
rm "$PID_FILE"
echo -e "${GREEN}[DONE]${NC} Cleanup complete"
