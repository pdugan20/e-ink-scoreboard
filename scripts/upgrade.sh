#!/bin/bash
# E-Ink Scoreboard - Upgrade Script
#
# Updates an existing installation to the latest version.
# Pulls code, reinstalls dependencies, and restarts services.
#
# Usage:
#   ./scripts/upgrade.sh          # Upgrade to latest
#   ./scripts/upgrade.sh --help   # Show usage

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$HOME/.virtualenvs/pimoroni"

# Handle --help flag
if [ "${1:-}" = "--help" ]; then
    echo "E-Ink Scoreboard - Upgrade Script"
    echo ""
    echo "Usage: ./scripts/upgrade.sh"
    echo ""
    echo "Steps performed:"
    echo "  1. Pull latest code from git"
    echo "  2. Update Python dependencies and Playwright browser"
    echo "  3. Re-install service files and sudoers rules"
    echo "  4. Restart all services"
    echo "  5. Run installation verification"
    echo ""
    echo "Your configuration (config.js, eink_config.json) is preserved."
    exit 0
fi

echo ""
echo "E-Ink Scoreboard - Upgrade"
echo "===================================="
echo ""

cd "$PROJECT_DIR"

# ── Step 1: Pull latest code ─────────────────────────────────────────

echo "[Step 1/5] Pulling latest code..."

# Check for uncommitted changes
if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
    echo "[WARN] You have uncommitted changes. Stashing them..."
    git stash
    STASHED=true
else
    STASHED=false
fi

BEFORE=$(git rev-parse HEAD)
git pull --ff-only origin main
AFTER=$(git rev-parse HEAD)

if [ "$BEFORE" = "$AFTER" ]; then
    echo "[SUCCESS] Already up to date"
else
    echo "[SUCCESS] Updated from ${BEFORE:0:7} to ${AFTER:0:7}"
    echo ""
    echo "Changes:"
    git log --oneline "$BEFORE..$AFTER" | head -20
fi

if [ "$STASHED" = true ]; then
    echo ""
    echo "[INFO] Restoring stashed changes..."
    git stash pop || echo "[WARN] Could not restore stashed changes -- resolve manually with 'git stash pop'"
fi

# ── Step 2: Update dependencies ──────────────────────────────────────

echo ""
echo "[Step 2/5] Updating dependencies..."

if [ -x "$VENV_PATH/bin/python" ]; then
    source "$VENV_PATH/bin/activate"
    pip install -r requirements.txt --quiet
    echo "[SUCCESS] Python packages updated"

    # Update Playwright browser if version changed
    if command -v playwright &>/dev/null; then
        echo "[INFO] Updating Playwright browser..."
        playwright install chromium --with-deps 2>/dev/null || playwright install chromium
        echo "[SUCCESS] Playwright browser updated"
    fi
else
    echo "[WARN] Virtual environment not found -- run install.sh first"
fi

# ── Step 3: Update service files ─────────────────────────────────────

echo ""
echo "[Step 3/5] Updating service files..."

if command -v systemctl &>/dev/null; then
    USER_NAME=$(whoami)

    # Re-template all three service files to pick up any changes
    for svc_file in sports-server sports-display sports-watchdog; do
        if [ -f "services/${svc_file}.service" ]; then
            sed -e "s|{{USER}}|$USER_NAME|g" \
                -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
                -e "s|{{VENV_PATH}}|$VENV_PATH|g" \
                "services/${svc_file}.service" | sudo tee "/etc/systemd/system/${svc_file}.service" > /dev/null
            echo "[SUCCESS] Updated ${svc_file}.service"
        fi
    done

    # Update sudoers rules
    if [ -f "services/scoreboard-sudoers" ]; then
        sed -e "s|{{USER}}|$USER_NAME|g" \
            services/scoreboard-sudoers | sudo tee /etc/sudoers.d/scoreboard > /dev/null
        sudo chmod 0440 /etc/sudoers.d/scoreboard
        if sudo visudo -c -f /etc/sudoers.d/scoreboard &>/dev/null; then
            echo "[SUCCESS] Updated sudoers rules"
        else
            echo "[ERROR] Invalid sudoers rule -- removing to prevent lockout"
            sudo rm -f /etc/sudoers.d/scoreboard
        fi
    fi

    sudo systemctl daemon-reload
else
    echo "[INFO] systemctl not available -- restart services manually"
fi

# ── Step 4: Restart services ─────────────────────────────────────────

echo ""
echo "[Step 4/5] Restarting services..."

if command -v systemctl &>/dev/null; then
    for svc in sports-server sports-display sports-watchdog; do
        if systemctl is-active "${svc}.service" &>/dev/null; then
            sudo systemctl restart "${svc}.service"
            echo "[SUCCESS] Restarted ${svc}.service"
        else
            echo "[INFO] ${svc}.service not running (start manually if needed)"
        fi
    done
else
    echo "[INFO] systemctl not available -- restart services manually"
fi

# ── Step 5: Verify ───────────────────────────────────────────────────

echo ""
echo "[Step 5/5] Verifying installation..."
echo ""

"$SCRIPT_DIR/verify-installation.sh" --quick || true

echo ""
echo "[SUCCESS] Upgrade complete!"
