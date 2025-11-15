#!/bin/bash
#
# DNS Ad Blocker - Service Runner
# Runs the DNS blocker with proper permissions on port 53
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run Python as the actual user but bind to privileged port using setcap
python3 "$SCRIPT_DIR/dns_blocker_server.py"
