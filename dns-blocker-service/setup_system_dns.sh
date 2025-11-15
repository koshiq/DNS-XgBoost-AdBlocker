#!/bin/bash
#
# DNS Ad Blocker - System DNS Setup
# Configures your system to use the local DNS blocker
#

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           DNS AD BLOCKER - SYSTEM DNS SETUP                       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} This script must be run with sudo"
    echo -e "${YELLOW}[INFO]${NC} Usage: sudo ./setup_system_dns.sh"
    exit 1
fi

echo -e "${YELLOW}[WARNING]${NC} This will modify your system DNS settings"
echo -e "${YELLOW}[INFO]${NC} Your current DNS servers will be backed up"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted"
    exit 0
fi

# Backup current resolv.conf
if [ -f /etc/resolv.conf ]; then
    cp /etc/resolv.conf /etc/resolv.conf.backup
    echo -e "${GREEN}[BACKUP]${NC} Created /etc/resolv.conf.backup"
fi

# Check if systemd-resolved is active
if systemctl is-active --quiet systemd-resolved; then
    echo -e "${YELLOW}[INFO]${NC} systemd-resolved is active"
    echo -e "${YELLOW}[INFO]${NC} Configuring via systemd-resolved..."

    # Stop systemd-resolved from managing /etc/resolv.conf
    systemctl stop systemd-resolved
    systemctl disable systemd-resolved

    # Remove symlink if it exists
    if [ -L /etc/resolv.conf ]; then
        rm /etc/resolv.conf
    fi
fi

# Create new resolv.conf
cat > /etc/resolv.conf << EOF
# DNS Ad Blocker - Local DNS Server
# Backup available at /etc/resolv.conf.backup
nameserver 127.0.0.1
# Fallback to Google DNS if local blocker is down
nameserver 8.8.8.8
nameserver 8.8.4.4
EOF

# Make it immutable to prevent NetworkManager from overwriting
chattr +i /etc/resolv.conf 2>/dev/null || true

echo -e "${GREEN}[SUCCESS]${NC} System DNS configured to use local blocker"
echo ""
echo -e "${GREEN}[NEXT STEPS]${NC}"
echo "  1. Start the blocker with: sudo ./start_blocker.sh"
echo "  2. Browse the web normally"
echo "  3. Watch ads get blocked: sudo tail -f dns_blocker.log"
echo ""
echo -e "${YELLOW}[RESTORE]${NC} To restore original DNS:"
echo "  sudo chattr -i /etc/resolv.conf"
echo "  sudo cp /etc/resolv.conf.backup /etc/resolv.conf"
echo "  sudo systemctl enable systemd-resolved"
echo "  sudo systemctl start systemd-resolved"
