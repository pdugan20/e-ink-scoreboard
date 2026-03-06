#!/bin/bash
# E-Ink Scoreboard - Diagnostics Script
#
# Collects system information, service status, and recent logs
# for debugging and bug reports.
#
# Usage:
#   ./scripts/diagnostics.sh              # Print to terminal
#   ./scripts/diagnostics.sh --save       # Save to file
#   ./scripts/diagnostics.sh --help       # Show usage

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$HOME/.virtualenvs/pimoroni"

SAVE_MODE=false
OUTPUT_FILE=""

if [ "${1:-}" = "--help" ]; then
    echo "E-Ink Scoreboard - Diagnostics"
    echo ""
    echo "Usage: ./scripts/diagnostics.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --save   Save output to a timestamped file in ~/logs/"
    echo "  --help   Show this help message"
    echo ""
    echo "Collects system info, service status, and recent logs"
    echo "for debugging. Share the output file when reporting issues."
    exit 0
fi

if [ "${1:-}" = "--save" ]; then
    SAVE_MODE=true
    mkdir -p "$HOME/logs"
    OUTPUT_FILE="$HOME/logs/diagnostics-$(date +%Y%m%d-%H%M%S).txt"
fi

# If saving, redirect all output to file AND terminal
if [ "$SAVE_MODE" = true ]; then
    exec > >(tee "$OUTPUT_FILE") 2>&1
fi

echo ""
echo "E-Ink Scoreboard - Diagnostics Report"
echo "======================================"
echo "Generated: $(date)"
echo ""

# ── System Information ───────────────────────────────────────────────

echo "--- System Information ---"
echo ""

if [ -f /proc/cpuinfo ]; then
    PI_MODEL=$(grep "Model" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | xargs || echo "Unknown")
    echo "Pi Model:    $PI_MODEL"
fi

echo "Hostname:    $(hostname)"
echo "Kernel:      $(uname -r)"

if [ -f /etc/os-release ]; then
    OS_NAME=$(grep "PRETTY_NAME" /etc/os-release | cut -d= -f2 | tr -d '"')
    echo "OS:          $OS_NAME"
else
    echo "OS:          $(uname -s) $(uname -m)"
fi

echo "Uptime:      $(uptime -p 2>/dev/null || uptime | awk '{print $3,$4}' | sed 's/,//')"
echo ""

# ── Memory and Disk ──────────────────────────────────────────────────

echo "--- Memory ---"
echo ""
free -h 2>/dev/null || echo "free command not available"
echo ""

echo "--- Disk ---"
echo ""
df -h / 2>/dev/null | head -2
echo ""

# ── Network ──────────────────────────────────────────────────────────

echo "--- Network ---"
echo ""
echo "IP Address:  $(hostname -I 2>/dev/null | awk '{print $1}' || echo 'Unknown')"
echo "Gateway:     $(ip route 2>/dev/null | grep default | awk '{print $3}' | head -1 || echo 'Unknown')"
echo "Interface:   $(ip route 2>/dev/null | grep default | awk '{print $5}' | head -1 || echo 'Unknown')"

# Check DNS
if host google.com &>/dev/null; then
    echo "DNS:         Working"
else
    echo "DNS:         Not resolving"
fi

# Check internet
if curl -s --max-time 5 -o /dev/null https://www.google.com; then
    echo "Internet:    Connected"
else
    echo "Internet:    Not reachable"
fi

echo ""

# ── Hardware Interfaces ──────────────────────────────────────────────

echo "--- Hardware Interfaces ---"
echo ""

if [ -e /dev/spidev0.0 ]; then
    echo "SPI:         Enabled (/dev/spidev0.0 present)"
else
    echo "SPI:         Not detected"
fi

if [ -e /dev/i2c-1 ]; then
    echo "I2C:         Enabled (/dev/i2c-1 present)"
else
    echo "I2C:         Not detected"
fi

echo ""

# ── Python Environment ───────────────────────────────────────────────

echo "--- Python Environment ---"
echo ""

if [ -x "$VENV_PATH/bin/python" ]; then
    echo "Venv:        $VENV_PATH"
    echo "Python:      $($VENV_PATH/bin/python --version 2>&1)"

    echo "Key packages:"
    for pkg in flask inky playwright pillow psutil; do
        version=$($VENV_PATH/bin/python -c "import $pkg; print($pkg.__version__)" 2>/dev/null || echo "not installed")
        printf "  %-12s %s\n" "$pkg:" "$version"
    done
else
    echo "Venv:        NOT FOUND at $VENV_PATH"
fi

echo ""

# ── Systemd Services ────────────────────────────────────────────────

echo "--- Services ---"
echo ""

if command -v systemctl &>/dev/null; then
    for svc in sports-server sports-display sports-watchdog; do
        svc_name="${svc}.service"
        status=$(systemctl is-active "$svc_name" 2>/dev/null || echo "not found")
        enabled=$(systemctl is-enabled "$svc_name" 2>/dev/null || echo "not found")
        printf "%-28s active=%-10s enabled=%s\n" "$svc_name:" "$status" "$enabled"
    done
else
    echo "systemctl not available"
fi

echo ""

# ── Cron Jobs ────────────────────────────────────────────────────────

echo "--- Cron Jobs ---"
echo ""

if crontab -l 2>/dev/null | grep -q "eink\|scoreboard\|sports" 2>/dev/null; then
    crontab -l 2>/dev/null | grep -i "eink\|scoreboard\|sports"
else
    echo "No scoreboard-related cron jobs found"
fi

echo ""

# ── Configuration ────────────────────────────────────────────────────

echo "--- Configuration ---"
echo ""

CONFIG_FILE="$PROJECT_DIR/src/eink_config.json"
if [ -f "$CONFIG_FILE" ]; then
    echo "eink_config.json:"
    cat "$CONFIG_FILE" 2>/dev/null | head -20
else
    echo "eink_config.json: NOT FOUND"
fi

echo ""

# ── Recent Logs ──────────────────────────────────────────────────────

echo "--- Recent Logs (last 30 lines) ---"
echo ""

LOG_FILE="$HOME/logs/eink_display.log"
if [ -f "$LOG_FILE" ]; then
    tail -30 "$LOG_FILE"
else
    echo "No log file found at $LOG_FILE"
fi

echo ""

# ── Journal Logs ─────────────────────────────────────────────────────

echo "--- Journal Logs (last 20 lines per service) ---"
echo ""

if command -v journalctl &>/dev/null; then
    for svc in sports-server sports-display; do
        echo "[$svc.service]"
        journalctl -u "${svc}.service" --no-pager -n 20 2>/dev/null || echo "  No journal entries"
        echo ""
    done
else
    echo "journalctl not available"
fi

# ── Screenshot Status ────────────────────────────────────────────────

echo "--- Screenshot Status ---"
echo ""

SCREENSHOT="/tmp/sports_display.png"
if [ -f "$SCREENSHOT" ]; then
    AGE_SECONDS=$(( $(date +%s) - $(stat -c %Y "$SCREENSHOT" 2>/dev/null || stat -f %m "$SCREENSHOT" 2>/dev/null) ))
    AGE_MINUTES=$((AGE_SECONDS / 60))
    SIZE=$(ls -lh "$SCREENSHOT" | awk '{print $5}')
    echo "Screenshot:  $SCREENSHOT"
    echo "Size:        $SIZE"
    echo "Age:         ${AGE_MINUTES} minutes (${AGE_SECONDS} seconds)"
else
    echo "Screenshot:  Not found at $SCREENSHOT"
fi

echo ""

# ── Summary ──────────────────────────────────────────────────────────

echo "======================================"

if [ "$SAVE_MODE" = true ]; then
    echo ""
    echo "Report saved to: $OUTPUT_FILE"
    echo "Share this file when reporting issues."
fi
