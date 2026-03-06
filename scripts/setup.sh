#!/bin/bash
# E-Ink Scoreboard - Full Setup
#
# Runs all three setup scripts in order:
#   1. install.sh    - System dependencies and libraries
#   2. configure.sh  - Interactive preferences
#   3. setup-services.sh - Systemd services
#
# Usage:
#   ./scripts/setup.sh          # Full setup
#   ./scripts/setup.sh --help   # Show usage

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "${1:-}" = "--help" ]; then
    echo "E-Ink Scoreboard - Full Setup"
    echo ""
    echo "Usage: ./scripts/setup.sh"
    echo ""
    echo "Runs all setup steps in order:"
    echo "  1. install.sh      - Install system dependencies"
    echo "  2. configure.sh    - Configure preferences"
    echo "  3. setup-services.sh - Set up auto-startup"
    echo ""
    echo "After completion, reboot to apply hardware changes."
    echo ""
    echo "For individual steps, run each script separately."
    echo "Run './scripts/install.sh --help' for more options."
    exit 0
fi

echo ""
echo "E-Ink Scoreboard - Full Setup"
echo "===================================="
echo ""
echo "This will run all three setup steps:"
echo "  1. Install dependencies"
echo "  2. Configure preferences"
echo "  3. Set up auto-startup services"
echo ""
read -p "Continue? (Y/n): " confirm
if [ "$confirm" = "n" ] || [ "$confirm" = "N" ]; then
    echo "Setup cancelled."
    exit 0
fi

echo ""
echo "===================================="
echo "Step 1 of 3: Installation"
echo "===================================="
echo ""

"$SCRIPT_DIR/install.sh"

echo ""
echo "===================================="
echo "Step 2 of 3: Configuration"
echo "===================================="
echo ""

"$SCRIPT_DIR/configure.sh"

echo ""
echo "===================================="
echo "Step 3 of 3: Service Setup"
echo "===================================="
echo ""

"$SCRIPT_DIR/setup-services.sh"

echo ""
echo "===================================="
echo "Setup Complete"
echo "===================================="
echo ""
echo "Reboot to apply hardware changes:"
echo "  sudo reboot"
echo ""
echo "After reboot, your scoreboard will start automatically."
echo "Access the display at: http://$(hostname -I 2>/dev/null | awk '{print $1}'):5001"
