#!/bin/bash
# E-Ink Scoreboard - Uninstall Script
#
# Removes systemd services, cron jobs, and log directories.
# Does NOT remove the project directory or Python code.
#
# Usage:
#   ./scripts/uninstall.sh          # Uninstall with prompts
#   ./scripts/uninstall.sh --all    # Remove everything including venv
#   ./scripts/uninstall.sh --help   # Show usage

set -e

# Handle --help flag
if [ "${1:-}" = "--help" ]; then
    echo "E-Ink Scoreboard - Uninstall Script"
    echo ""
    echo "Usage: ./scripts/uninstall.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --all    Also remove the Pimoroni virtual environment"
    echo "  --help   Show this help message"
    echo ""
    echo "Removes:"
    echo "  - Systemd services (sports-server, sports-display, sports-watchdog)"
    echo "  - Daily reboot cron job"
    echo "  - Log directories"
    echo "  - Optionally: Pimoroni virtual environment"
    echo ""
    echo "Does NOT remove:"
    echo "  - This project directory or source code"
    echo "  - System packages installed via apt"
    echo "  - SPI/I2C hardware configuration"
    exit 0
fi

REMOVE_ALL=false
if [ "${1:-}" = "--all" ]; then
    REMOVE_ALL=true
fi

REMOVED=0

echo ""
echo "E-Ink Scoreboard - Uninstall"
echo "===================================="
echo ""

# ── Stop and disable services ────────────────────────────────────────

echo "[1/4] Stopping and removing services..."

for svc in sports-server sports-display sports-watchdog; do
    svc_name="${svc}.service"
    if systemctl is-active "$svc_name" &>/dev/null; then
        echo "[INFO] Stopping $svc_name..."
        sudo systemctl stop "$svc_name"
    fi
    if systemctl is-enabled "$svc_name" &>/dev/null; then
        echo "[INFO] Disabling $svc_name..."
        sudo systemctl disable "$svc_name"
    fi
    if [ -f "/etc/systemd/system/$svc_name" ]; then
        sudo rm "/etc/systemd/system/$svc_name"
        echo "[SUCCESS] Removed $svc_name"
        REMOVED=$((REMOVED + 1))
    else
        echo "[INFO] $svc_name not found (already removed)"
    fi
done

sudo systemctl daemon-reload

# ── Remove cron job ──────────────────────────────────────────────────

echo ""
echo "[2/4] Removing cron jobs..."

if crontab -l 2>/dev/null | grep -q "E-Ink Scoreboard"; then
    crontab -l 2>/dev/null | grep -v "E-Ink Scoreboard" | grep -v "shutdown -r now" | crontab - 2>/dev/null || true
    echo "[SUCCESS] Removed daily reboot cron job"
    REMOVED=$((REMOVED + 1))
else
    echo "[INFO] No cron jobs found"
fi

# ── Remove log directories ──────────────────────────────────────────

echo ""
echo "[3/4] Removing log directories..."

if [ -d /var/log/eink-display ]; then
    sudo rm -rf /var/log/eink-display
    echo "[SUCCESS] Removed /var/log/eink-display"
    REMOVED=$((REMOVED + 1))
fi

if [ -d /tmp/eink-logs ]; then
    rm -rf /tmp/eink-logs
    echo "[SUCCESS] Removed /tmp/eink-logs"
    REMOVED=$((REMOVED + 1))
fi

# ── Optional: remove virtual environment ─────────────────────────────

echo ""
echo "[4/4] Virtual environment..."

VENV_PATH="$HOME/.virtualenvs/pimoroni"
if [ "$REMOVE_ALL" = true ]; then
    if [ -d "$VENV_PATH" ]; then
        rm -rf "$VENV_PATH"
        echo "[SUCCESS] Removed Pimoroni virtual environment"
        REMOVED=$((REMOVED + 1))
    fi
    if [ -d "$HOME/inky" ]; then
        rm -rf "$HOME/inky"
        echo "[SUCCESS] Removed Inky library clone"
        REMOVED=$((REMOVED + 1))
    fi
else
    echo "[INFO] Virtual environment kept at $VENV_PATH"
    echo "       Use --all to also remove it"
fi

# ── Summary ──────────────────────────────────────────────────────────

echo ""
echo "===================================="
echo "Uninstall Summary"
echo "===================================="
echo "  Items removed: $REMOVED"
echo ""
echo "The project source code remains in this directory."
echo "To reinstall, run: ./scripts/install.sh"
