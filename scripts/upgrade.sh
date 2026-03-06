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
    echo "  2. Reinstall Python dependencies"
    echo "  3. Restart all services"
    echo "  4. Run installation verification"
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

echo "[Step 1/4] Pulling latest code..."

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
echo "[Step 2/4] Updating Python dependencies..."

if [ -x "$VENV_PATH/bin/python" ]; then
    source "$VENV_PATH/bin/activate"
    pip install -r requirements.txt --quiet
    echo "[SUCCESS] Python packages updated"
else
    echo "[WARN] Virtual environment not found -- run install.sh first"
fi

# ── Step 3: Restart services ─────────────────────────────────────────

echo ""
echo "[Step 3/4] Restarting services..."

if command -v systemctl &>/dev/null; then
    # Re-run service setup to pick up any template changes
    if [ -f "services/sports-display.service" ]; then
        USER_NAME=$(whoami)
        sed -e "s|{{USER}}|$USER_NAME|g" \
            -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
            -e "s|{{VENV_PATH}}|$VENV_PATH|g" \
            services/sports-display.service | sudo tee /etc/systemd/system/sports-display.service > /dev/null
    fi
    if [ -f "services/sports-watchdog.service" ]; then
        USER_NAME=$(whoami)
        sed -e "s|{{USER}}|$USER_NAME|g" \
            -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
            -e "s|{{VENV_PATH}}|$VENV_PATH|g" \
            services/sports-watchdog.service | sudo tee /etc/systemd/system/sports-watchdog.service > /dev/null
    fi

    sudo systemctl daemon-reload

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

# ── Step 4: Verify ───────────────────────────────────────────────────

echo ""
echo "[Step 4/4] Verifying installation..."
echo ""

"$SCRIPT_DIR/verify-installation.sh" --quick || true

echo ""
echo "[SUCCESS] Upgrade complete!"
