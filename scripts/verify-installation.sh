#!/bin/bash
# E-Ink Scoreboard - Installation Verification Script
#
# Checks that all components are properly installed and functional.
# Run after install.sh, configure.sh, and setup-services.sh to confirm
# the installation is ready.
#
# Usage:
#   ./scripts/verify-installation.sh          # Run all checks
#   ./scripts/verify-installation.sh --quick   # Skip service checks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$HOME/.virtualenvs/pimoroni"

PASS=0
FAIL=0
WARN=0
SKIP=0

QUICK_MODE=false
if [ "${1:-}" = "--quick" ]; then
    QUICK_MODE=true
fi

# Output helpers
check_pass() {
    echo "  [PASS] $1"
    PASS=$((PASS + 1))
}

check_fail() {
    echo "  [FAIL] $1"
    FAIL=$((FAIL + 1))
}

check_warn() {
    echo "  [WARN] $1"
    WARN=$((WARN + 1))
}

check_skip() {
    echo "  [SKIP] $1"
    SKIP=$((SKIP + 1))
}

echo ""
echo "E-Ink Scoreboard - Installation Verification"
echo "============================================="
echo ""

# ── Section 1: Hardware ──────────────────────────────────────────────

echo "[1/7] Hardware Interfaces"

# Check if running on Raspberry Pi
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    check_pass "Running on Raspberry Pi"
else
    check_warn "Not running on Raspberry Pi (expected for dev machines)"
fi

# Check SPI
if [ -e /dev/spidev0.0 ]; then
    check_pass "SPI device available (/dev/spidev0.0)"
elif grep -q "dtoverlay=spi0-0cs" /boot/firmware/config.txt 2>/dev/null; then
    check_warn "SPI configured in config.txt but device not loaded (reboot needed?)"
else
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        check_fail "SPI not configured -- run install.sh or enable via raspi-config"
    else
        check_skip "SPI check (not on Raspberry Pi)"
    fi
fi

# Check I2C
if [ -e /dev/i2c-1 ]; then
    check_pass "I2C device available (/dev/i2c-1)"
else
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        check_warn "I2C device not found -- may need reboot after install"
    else
        check_skip "I2C check (not on Raspberry Pi)"
    fi
fi

echo ""

# ── Section 2: Python Environment ────────────────────────────────────

echo "[2/7] Python Environment"

# Check virtual environment
if [ -d "$VENV_PATH" ]; then
    check_pass "Virtual environment exists ($VENV_PATH)"
else
    check_fail "Virtual environment not found at $VENV_PATH"
fi

# Check Python binary in venv
if [ -x "$VENV_PATH/bin/python" ]; then
    check_pass "Python binary exists in venv"
    PYTHON="$VENV_PATH/bin/python"
else
    check_fail "Python binary not found in venv"
    # Fallback to system python for remaining checks
    PYTHON="python3"
fi

# Check core Python packages
for pkg in flask requests playwright psutil pytz feedparser; do
    if $PYTHON -c "import $pkg" 2>/dev/null; then
        check_pass "Python package: $pkg"
    else
        check_fail "Python package missing: $pkg"
    fi
done

# Pillow's import name is PIL, not pillow
if $PYTHON -c "import PIL" 2>/dev/null; then
    check_pass "Python package: pillow"
else
    check_fail "Python package missing: pillow"
fi

# Check inky (only expected on Pi)
if $PYTHON -c "import inky" 2>/dev/null; then
    check_pass "Python package: inky"
else
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        check_fail "Python package missing: inky"
    else
        check_skip "Python package: inky (not on Raspberry Pi)"
    fi
fi

# Check systemd-python (optional)
if $PYTHON -c "import systemd" 2>/dev/null; then
    check_pass "Python package: systemd-python (watchdog support)"
else
    check_warn "Python package missing: systemd-python (watchdog will be disabled)"
fi

echo ""

# ── Section 3: Playwright / Chromium ─────────────────────────────────

echo "[3/7] Playwright and Chromium"

if $PYTHON -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    check_pass "Playwright Python module available"
else
    check_fail "Playwright Python module not importable"
fi

# Check if Chromium browser is installed for Playwright
CHROMIUM_PATH=$($PYTHON -c "
try:
    from playwright._impl._driver import compute_driver_executable
    import os
    driver_dir = os.path.dirname(compute_driver_executable())
    # Look for chromium in the playwright browsers directory
    browsers_dir = os.path.join(os.path.dirname(driver_dir), '.local-browsers')
    if os.path.isdir(browsers_dir):
        for d in os.listdir(browsers_dir):
            if 'chromium' in d.lower():
                print(os.path.join(browsers_dir, d))
                break
except Exception:
    pass
" 2>/dev/null)

if [ -n "$CHROMIUM_PATH" ]; then
    check_pass "Playwright Chromium browser installed"
else
    # Try the simpler check
    if $PYTHON -c "
from playwright.sync_api import sync_playwright
p = sync_playwright().start()
b = p.chromium.launch(headless=True)
b.close()
p.stop()
" 2>/dev/null; then
        check_pass "Playwright Chromium browser functional"
    else
        check_fail "Playwright Chromium not found -- run: playwright install chromium"
    fi
fi

echo ""

# ── Section 4: Configuration Files ───────────────────────────────────

echo "[4/7] Configuration Files"

# Check eink_config.json
CONFIG_FILE="$PROJECT_DIR/src/eink_config.json"
if [ -f "$CONFIG_FILE" ]; then
    if $PYTHON -c "import json; json.load(open('$CONFIG_FILE'))" 2>/dev/null; then
        check_pass "eink_config.json exists and is valid JSON"
    else
        check_fail "eink_config.json exists but is not valid JSON"
    fi
else
    check_fail "eink_config.json not found"
fi

# Check config.js
JS_CONFIG="$PROJECT_DIR/src/static/js/config.js"
if [ -f "$JS_CONFIG" ]; then
    check_pass "config.js exists"
    # Basic syntax check -- look for expected exports
    if grep -q "export const FEATURE_FLAGS" "$JS_CONFIG" 2>/dev/null; then
        check_pass "config.js contains FEATURE_FLAGS export"
    else
        check_warn "config.js missing FEATURE_FLAGS export"
    fi
    if grep -q "export const favoriteTeams" "$JS_CONFIG" 2>/dev/null; then
        check_pass "config.js contains favoriteTeams export"
    else
        check_warn "config.js missing favoriteTeams export"
    fi
else
    check_fail "config.js not found"
fi

echo ""

# ── Section 5: Project Files ─────────────────────────────────────────

echo "[5/7] Project Files"

# Check key source files exist
for f in \
    "src/dev_server.py" \
    "src/eink_display.py" \
    "src/display.html" \
    "src/api/scores_api.py" \
    "src/display/screenshot_controller.py" \
    "src/display/game_checker.py" \
    "src/watchdog_monitor.py"; do
    if [ -f "$PROJECT_DIR/$f" ]; then
        check_pass "Source file: $f"
    else
        check_fail "Source file missing: $f"
    fi
done

# Check scripts are executable
for f in \
    "scripts/install.sh" \
    "scripts/configure.sh" \
    "scripts/setup-services.sh"; do
    if [ -x "$PROJECT_DIR/$f" ]; then
        check_pass "Executable: $f"
    else
        check_warn "Not executable: $f (run chmod +x)"
    fi
done

echo ""

# ── Section 6: Systemd Services ──────────────────────────────────────

echo "[6/7] Systemd Services"

if [ "$QUICK_MODE" = true ]; then
    check_skip "Service checks skipped (--quick mode)"
elif ! command -v systemctl &>/dev/null; then
    check_skip "systemctl not available (not on a systemd system)"
else
    for svc in sports-server sports-display sports-watchdog; do
        svc_file="/etc/systemd/system/${svc}.service"
        if [ -f "$svc_file" ]; then
            check_pass "Service file installed: ${svc}.service"
        else
            check_warn "Service file not found: ${svc}.service (run setup-services.sh)"
        fi

        if systemctl is-enabled "${svc}.service" &>/dev/null; then
            check_pass "Service enabled: ${svc}.service"
        else
            if [ -f "$svc_file" ]; then
                check_warn "Service not enabled: ${svc}.service"
            fi
        fi
    done

    # Check cron job
    if crontab -l 2>/dev/null | grep -q "E-Ink Scoreboard.*Daily reboot"; then
        check_pass "Daily reboot cron job configured"
    else
        check_warn "Daily reboot cron job not found"
    fi
fi

echo ""

# ── Section 7: Log Directories ───────────────────────────────────────

echo "[7/7] Log Directories"

LOG_DIR="$HOME/logs"
if [ -d "$LOG_DIR" ]; then
    check_pass "Log directory exists: $LOG_DIR"
else
    check_warn "Log directory not found: $LOG_DIR (will be created on first run)"
fi

VAR_LOG="/var/log/eink-display"
if [ -d "$VAR_LOG" ]; then
    if [ -w "$VAR_LOG" ]; then
        check_pass "Log directory writable: $VAR_LOG"
    else
        check_warn "Log directory not writable: $VAR_LOG"
    fi
else
    check_warn "Log directory not found: $VAR_LOG"
fi

echo ""

# ── Summary ──────────────────────────────────────────────────────────

echo "============================================="
echo "Verification Summary"
echo "============================================="
echo "  Passed:  $PASS"
echo "  Failed:  $FAIL"
echo "  Warnings: $WARN"
echo "  Skipped: $SKIP"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "[SUCCESS] All critical checks passed."
    if [ $WARN -gt 0 ]; then
        echo "          Review warnings above for optional improvements."
    fi
    exit 0
else
    echo "[ERROR] $FAIL critical check(s) failed. Review output above."
    echo "        Re-run install.sh to fix missing components."
    exit 1
fi
