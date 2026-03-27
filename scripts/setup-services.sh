#!/bin/bash
# Setup systemd services for E-Ink Scoreboard
#
# Usage:
#   ./scripts/setup-services.sh          # Install and enable services
#   ./scripts/setup-services.sh --help   # Show usage

set -e

# Handle --help flag
if [ "${1:-}" = "--help" ]; then
    echo "E-Ink Scoreboard - Service Setup Script"
    echo ""
    echo "Usage: ./scripts/setup-services.sh"
    echo ""
    echo "Creates and enables systemd services:"
    echo "  - sports-server.service   (Flask web server on port 5001)"
    echo "  - sports-display.service  (E-ink display controller)"
    echo "  - sports-watchdog.service (Process monitor)"
    echo ""
    echo "Also sets up a daily reboot cron job at 4:00 AM for"
    echo "memory management."
    echo ""
    echo "This script is safe to re-run -- existing services will"
    echo "be updated in place."
    exit 0
fi

echo "[SETUP] Setting up systemd services..."

# Get current user and project directory
USER=$(whoami)
PROJECT_DIR=$(pwd)
VENV_PATH="$HOME/.virtualenvs/pimoroni"

# Make scripts executable
echo "[SETUP] Making scripts executable..."
chmod +x src/display/screenshot_worker.py 2>/dev/null || true
chmod +x src/watchdog_monitor.py 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

# Create sports-server.service
if [ -f /etc/systemd/system/sports-server.service ]; then
    echo "[INFO] Updating existing web server service..."
else
    echo "[INFO] Creating web server service..."
fi
if [ -f "services/sports-server.service" ]; then
    sed -e "s|{{USER}}|$USER|g" \
        -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
        -e "s|{{VENV_PATH}}|$VENV_PATH|g" \
        services/sports-server.service | sudo tee /etc/systemd/system/sports-server.service > /dev/null
    echo "[SUCCESS] Web server service installed with correct paths"
else
    echo "[WARN] Server service template not found, creating inline..."
    sudo tee /etc/systemd/system/sports-server.service > /dev/null <<EOF
[Unit]
Description=E-Ink Scoreboard Web Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$VENV_PATH/bin
ExecStart=$VENV_PATH/bin/python src/dev_server.py --port 5001 --production
Restart=always
RestartSec=10
MemoryMax=150M

[Install]
WantedBy=multi-user.target
EOF
fi

# Copy sports-display.service file
if [ -f /etc/systemd/system/sports-display.service ]; then
    echo "[INFO] Updating existing display service..."
else
    echo "[INFO] Installing display service..."
fi
if [ -f "services/sports-display.service" ]; then
    # Replace template placeholders with actual values
    sed -e "s|{{USER}}|$USER|g" \
        -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
        -e "s|{{VENV_PATH}}|$VENV_PATH|g" \
        services/sports-display.service | sudo tee /etc/systemd/system/sports-display.service > /dev/null
    echo "[SUCCESS] Display service installed with correct paths"
else
    echo "[WARN] Warning: sports-display.service file not found in services directory"
    echo "Creating basic service file..."
    sudo tee /etc/systemd/system/sports-display.service > /dev/null <<EOF
[Unit]
Description=Sports E-Ink Display Service
After=network.target sports-server.service
Requires=sports-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$VENV_PATH/bin/python src/eink_display.py --config src/eink_config.json

# Restart policy
Restart=always
RestartSec=30

# Resource limits to prevent runaway memory usage
MemoryMax=200M
MemorySwapMax=100M

# Kill timeout - if service doesn't stop gracefully in 30s, force kill
TimeoutStopSec=30
KillMode=mixed
KillSignal=SIGTERM
FinalKillSignal=SIGKILL

[Install]
WantedBy=multi-user.target
EOF
fi

# Install watchdog monitor service
if [ -f /etc/systemd/system/sports-watchdog.service ]; then
    echo "[INFO] Updating existing watchdog service..."
else
    echo "[INFO] Installing watchdog monitor service..."
fi
if [ -f "services/sports-watchdog.service" ]; then
    # Replace template placeholders with actual values
    sed -e "s|{{USER}}|$USER|g" \
        -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
        -e "s|{{VENV_PATH}}|$VENV_PATH|g" \
        services/sports-watchdog.service | sudo tee /etc/systemd/system/sports-watchdog.service > /dev/null
    echo "[SUCCESS] Watchdog service installed"
else
    echo "[WARN] Creating basic watchdog service..."
    sudo tee /etc/systemd/system/sports-watchdog.service > /dev/null <<EOF
[Unit]
Description=Sports Display Watchdog Monitor
After=network.target sports-display.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$VENV_PATH/bin/python src/watchdog_monitor.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF
fi

# Reload systemd to pick up any changes
sudo systemctl daemon-reload

# Enable services
echo "[INFO] Enabling services..."
sudo systemctl enable sports-server.service
sudo systemctl enable sports-display.service
sudo systemctl enable sports-watchdog.service

# Install update check timer
echo "[INFO] Installing update check timer..."
if [ -f "services/scoreboard-update-check.service" ] && [ -f "services/scoreboard-update-check.timer" ]; then
    sed -e "s|{{USER}}|$USER|g" \
        -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
        services/scoreboard-update-check.service | sudo tee /etc/systemd/system/scoreboard-update-check.service > /dev/null
    sed -e "s|{{USER}}|$USER|g" \
        -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
        services/scoreboard-update-check.timer | sudo tee /etc/systemd/system/scoreboard-update-check.timer > /dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable scoreboard-update-check.timer
    sudo systemctl start scoreboard-update-check.timer
    echo "[SUCCESS] Update check timer installed (runs every 6 hours)"
else
    echo "[WARN] Update check timer templates not found, skipping"
fi

# Install sudoers rule for web config panel service management
echo "[INFO] Installing sudoers rule for web config panel..."
if [ -f "services/scoreboard-sudoers" ]; then
    sed -e "s|{{USER}}|$USER|g" \
        services/scoreboard-sudoers | sudo tee /etc/sudoers.d/scoreboard > /dev/null
    sudo chmod 0440 /etc/sudoers.d/scoreboard
    # Validate the sudoers file
    if sudo visudo -c -f /etc/sudoers.d/scoreboard &>/dev/null; then
        echo "[SUCCESS] Sudoers rule installed (web panel can restart services)"
    else
        echo "[ERROR] Invalid sudoers rule -- removing to prevent lockout"
        sudo rm -f /etc/sudoers.d/scoreboard
    fi
else
    echo "[WARN] Sudoers template not found, skipping"
fi

# Setup daily reboot for memory management
echo "[INFO] Setting up daily reboot schedule..."
CRON_JOB="0 4 * * * /sbin/shutdown -r now"
CRON_COMMENT="# E-Ink Scoreboard: Daily reboot at 4 AM for memory management"

# Check if cron job already exists
if ! (crontab -l 2>/dev/null | grep -q "E-Ink Scoreboard.*Daily reboot"); then
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_COMMENT"; echo "$CRON_JOB") | crontab -
    echo "[SUCCESS] Daily reboot scheduled for 4:00 AM"
else
    echo "[SUCCESS] Daily reboot schedule already configured"
fi

echo ""
echo "[SUCCESS] Services created and enabled!"
echo ""
echo "To start services now:"
echo "  sudo systemctl start sports-server.service"
echo "  sudo systemctl start sports-display.service"
echo ""
echo "To check status:"
echo "  sudo systemctl status sports-server.service"
echo "  sudo systemctl status sports-display.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u sports-display.service -f"
echo "  tail -f ~/logs/eink_display.log"
echo ""
echo "To analyze logs for debugging:"
echo "  ./scripts/analyze-logs.sh"
echo ""
echo "Scheduled maintenance:"
echo "  Daily reboot at 4:00 AM for memory management"
echo "  View cron jobs: crontab -l"
