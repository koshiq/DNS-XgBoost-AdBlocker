#!/bin/bash
#
# DNS Ad Blocker - Simple Starter
# Easy way to start the blocker with proper permissions
#

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           DNS AD BLOCKER - STARTING...                            ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get user's Python package path
USER_PYTHON_PATH="$HOME/.local/lib/python3.14/site-packages"

if [ ! -d "$USER_PYTHON_PATH" ]; then
    echo -e "${YELLOW}[WARN]${NC} User Python path not found, trying system Python..."
    USER_PYTHON_PATH=""
fi

# Check if port 53 is already in use
if sudo lsof -i :53 >/dev/null 2>&1; then
    echo -e "${YELLOW}[WARN]${NC} Port 53 is already in use"
    echo -e "${YELLOW}[INFO]${NC} You may need to stop systemd-resolved first:"
    echo -e "${YELLOW}       sudo systemctl stop systemd-resolved${NC}"
    echo ""
    read -p "Try to stop systemd-resolved? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl stop systemd-resolved
        echo -e "${GREEN}[OK]${NC} Stopped systemd-resolved"
    else
        exit 1
    fi
fi

echo -e "${GREEN}[START]${NC} Starting DNS blocker on port 53..."
echo -e "${YELLOW}[INFO]${NC} Press Ctrl+C to stop"
echo -e "${YELLOW}[INFO]${NC} In another terminal, run: sudo tail -f dns_blocker.log"
echo ""

# Run with sudo, preserving user's Python environment
cd "$(dirname "$0")"
sudo PYTHONPATH="$USER_PYTHON_PATH" python3 dns_blocker_server.py
