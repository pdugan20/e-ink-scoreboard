#!/bin/bash
# E-Ink Scoreboard - Raspberry Pi Installation Script
#
# Usage:
#   ./scripts/install.sh                 # Full installation
#   ./scripts/install.sh --skip-update   # Skip apt update/upgrade
#   ./scripts/install.sh --check         # Run verification only
#   ./scripts/install.sh --help          # Show usage

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
VENV_PATH="$HOME/.virtualenvs/pimoroni"

SKIP_UPDATE=false
STEPS_PASSED=0
STEPS_FAILED=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --check)
            exec "$SCRIPT_DIR/verify-installation.sh"
            ;;
        --skip-update)
            SKIP_UPDATE=true
            ;;
        --help)
            echo "E-Ink Scoreboard - Installation Script"
            echo ""
            echo "Usage: ./scripts/install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-update   Skip apt update/upgrade (faster reinstall)"
            echo "  --check         Run verification only (no installation)"
            echo "  --help          Show this help message"
            echo ""
            echo "This script installs all dependencies for the e-ink scoreboard"
            echo "on a Raspberry Pi. It is safe to re-run -- completed steps are"
            echo "detected and skipped automatically."
            exit 0
            ;;
    esac
done

# Track step results
step_pass() {
    echo "[SUCCESS] $1"
    STEPS_PASSED=$((STEPS_PASSED + 1))
}

step_fail() {
    echo "[ERROR] $1"
    STEPS_FAILED=$((STEPS_FAILED + 1))
}

echo ""
echo "E-Ink Scoreboard Installation"
echo "===================================="
echo ""

# ── Step 1: Platform Check ───────────────────────────────────────────

echo "[Step 1/9] Checking platform..."

if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "[ERROR] This script is designed for Raspberry Pi only"
    exit 1
fi

step_pass "Detected Raspberry Pi"

# ── Step 2: System Packages ──────────────────────────────────────────

echo ""
echo "[Step 2/9] System packages..."

if [ "$SKIP_UPDATE" = true ]; then
    echo "[INFO] Skipping apt update/upgrade (--skip-update)"
else
    echo "[INFO] Updating system packages..."
    if sudo apt update && sudo apt upgrade -y; then
        step_pass "System packages updated"
    else
        step_fail "System package update failed"
    fi
fi

echo "[INFO] Installing dependencies..."
if sudo apt install -y python3-pip python3-venv git \
    libjpeg-dev libopenjp2-7 libtiff5-dev \
    libsystemd-dev pkg-config; then
    step_pass "System dependencies installed"
else
    step_fail "Some system dependencies failed to install"
fi

# ── Step 3: Hardware Interfaces ──────────────────────────────────────

echo ""
echo "[Step 3/9] Hardware interfaces..."

# Check if SPI is already enabled
if [ -e /dev/spidev0.0 ]; then
    step_pass "SPI already enabled"
else
    echo "[INFO] Enabling SPI..."
    sudo raspi-config nonint do_spi 0
    step_pass "SPI enabled (reboot required to activate)"
fi

# Check if I2C is already enabled
if [ -e /dev/i2c-1 ]; then
    step_pass "I2C already enabled"
else
    echo "[INFO] Enabling I2C..."
    sudo raspi-config nonint do_i2c 0
    step_pass "I2C enabled (reboot required to activate)"
fi

# Add SPI overlay configuration
if ! grep -q "dtoverlay=spi0-0cs" /boot/firmware/config.txt 2>/dev/null; then
    echo 'dtoverlay=spi0-0cs' | sudo tee -a /boot/firmware/config.txt
    step_pass "Added SPI overlay configuration"
else
    step_pass "SPI overlay configuration already present"
fi

# ── Step 4: Inky Display Library ─────────────────────────────────────

echo ""
echo "[Step 4/9] Inky display library..."

# Check if Inky is already functional in the venv
INKY_FUNCTIONAL=false
if [ -x "$VENV_PATH/bin/python" ]; then
    if "$VENV_PATH/bin/python" -c "import inky" 2>/dev/null; then
        INKY_FUNCTIONAL=true
    fi
fi

if [ "$INKY_FUNCTIONAL" = true ]; then
    step_pass "Inky library already installed and functional"
else
    echo "[INFO] Installing Inky display library..."
    if [ -d "$HOME/inky" ]; then
        echo "[INFO] Removing stale inky directory..."
        rm -rf ~/inky
    fi
    cd ~
    if git clone https://github.com/pimoroni/inky.git; then
        cd inky
        if echo "y" | ./install.sh; then
            step_pass "Inky library installed"
        else
            step_fail "Inky library install script failed"
        fi
    else
        step_fail "Failed to clone Inky repository"
    fi
fi

# Go back to project directory
cd "$PROJECT_DIR"

# ── Step 5: Python Dependencies ──────────────────────────────────────

echo ""
echo "[Step 5/9] Python dependencies..."

if [ ! -x "$VENV_PATH/bin/python" ]; then
    step_fail "Virtual environment not found at $VENV_PATH -- Inky install may have failed"
else
    echo "[INFO] Activating virtual environment..."
    source "$VENV_PATH/bin/activate"

    echo "[INFO] Installing Python packages..."
    if pip install -r requirements.txt; then
        step_pass "Python packages installed"
    else
        step_fail "Some Python packages failed to install"
    fi

    # systemd-python is optional
    if pip install systemd-python 2>/dev/null; then
        step_pass "systemd-python installed (watchdog support enabled)"
    else
        echo "[WARN] systemd-python not available -- watchdog will be disabled"
    fi
fi

# ── Step 6: Log Directories ──────────────────────────────────────────

echo ""
echo "[Step 6/9] Log directories..."

# Primary log directory used by eink_config.json
LOG_DIR="$HOME/logs"
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
fi
step_pass "Log directory ready: $LOG_DIR"

# System log directory for service output
if [ ! -d /var/log/eink-display ]; then
    sudo mkdir -p /var/log/eink-display
    sudo chown "$(whoami):$(whoami)" /var/log/eink-display
fi
step_pass "System log directory ready: /var/log/eink-display"

# ── Step 7: Playwright / Chromium ────────────────────────────────────

echo ""
echo "[Step 7/9] Playwright and Chromium..."

# Check if Playwright Chromium is already installed
PLAYWRIGHT_OK=false
if "$VENV_PATH/bin/python" -c "
from playwright.sync_api import sync_playwright
p = sync_playwright().start()
b = p.chromium.launch(headless=True)
b.close()
p.stop()
" 2>/dev/null; then
    PLAYWRIGHT_OK=true
fi

if [ "$PLAYWRIGHT_OK" = true ]; then
    step_pass "Playwright Chromium already installed and functional"
else
    echo "[INFO] Installing Playwright dependencies..."
    if playwright install-deps chromium; then
        step_pass "Playwright system dependencies installed"
    else
        step_fail "Playwright system dependencies failed"
    fi

    echo "[INFO] Installing Playwright Chromium..."
    if playwright install chromium; then
        step_pass "Playwright Chromium installed"
    else
        step_fail "Playwright Chromium install failed -- screenshots won't work"
    fi
fi

# ── Step 8: Network Discovery (mDNS) ─────────────────────────────────

echo ""
echo "[Step 8/9] Network discovery (mDNS)..."

# Install avahi-daemon for scoreboard.local discovery
if systemctl is-active avahi-daemon &>/dev/null; then
    step_pass "Avahi (mDNS) already running"
else
    echo "[INFO] Installing avahi-daemon for local network discovery..."
    if sudo apt install -y avahi-daemon; then
        step_pass "Avahi daemon installed"
    else
        step_fail "Avahi daemon installation failed -- scoreboard.local won't work"
    fi
fi

# Set hostname to 'scoreboard' for scoreboard.local
CURRENT_HOSTNAME=$(hostname)
if [ "$CURRENT_HOSTNAME" = "scoreboard" ]; then
    step_pass "Hostname already set to 'scoreboard'"
else
    echo "[INFO] Setting hostname to 'scoreboard' (was: $CURRENT_HOSTNAME)..."
    if sudo hostnamectl set-hostname scoreboard; then
        # Update /etc/hosts to match
        if grep -q "127.0.1.1" /etc/hosts; then
            sudo sed -i "s/127.0.1.1.*/127.0.1.1\tscoreboard/" /etc/hosts
        else
            echo "127.0.1.1	scoreboard" | sudo tee -a /etc/hosts > /dev/null
        fi
        step_pass "Hostname set to 'scoreboard' (access via scoreboard.local)"
    else
        step_fail "Failed to set hostname"
    fi
fi

# Install Avahi service advertisement file
if [ -f "$PROJECT_DIR/services/scoreboard-avahi.service" ]; then
    sudo cp "$PROJECT_DIR/services/scoreboard-avahi.service" /etc/avahi/services/scoreboard.service
    step_pass "Avahi service file installed (advertising port 5001)"
else
    echo "[WARN] Avahi service file not found in services/ directory"
fi

# Ensure avahi-daemon is enabled and running
sudo systemctl enable avahi-daemon 2>/dev/null || true
sudo systemctl restart avahi-daemon 2>/dev/null || true

# ── Step 9: File Permissions ─────────────────────────────────────────

echo ""
echo "[Step 9/9] File permissions..."

chmod +x src/eink_display.py 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true
step_pass "Scripts marked executable"

# ── Summary ──────────────────────────────────────────────────────────

echo ""
echo "===================================="
echo "Installation Summary"
echo "===================================="
echo "  Passed: $STEPS_PASSED"
echo "  Failed: $STEPS_FAILED"
echo ""

if [ $STEPS_FAILED -gt 0 ]; then
    echo "[WARN] Some steps failed. Review output above."
    echo "       You can re-run this script safely -- completed steps will be skipped."
    echo ""
fi

# Run verification
echo "Running installation verification..."
echo ""
"$SCRIPT_DIR/verify-installation.sh" --quick || true

echo ""
echo "Next steps:"
echo "1. Run './scripts/configure.sh' to set preferences"
echo "2. Run './scripts/setup-services.sh' to configure auto-startup"
echo "3. Test with: 'python src/eink_display.py --once'"
echo "4. Reboot to apply all hardware changes"
echo ""
echo "Debugging tools:"
echo "  View logs: tail -f ~/logs/eink_display.log"
echo "  Analyze logs: ./scripts/analyze-logs.sh"
echo "  Service status: sudo systemctl status sports-display.service"
echo "  Verify install: ./scripts/install.sh --check"
