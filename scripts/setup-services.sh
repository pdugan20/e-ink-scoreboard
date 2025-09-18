#!/bin/bash
# Setup systemd services for E-Ink Scoreboard

set -e

echo "🔧 Setting up systemd services..."

# Get current user and project directory
USER=$(whoami)
PROJECT_DIR=$(pwd)
VENV_PATH="$HOME/.virtualenvs/pimoroni"

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x src/display/screenshot_worker.py 2>/dev/null || true
chmod +x src/watchdog_monitor.py 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

# Create sports-server.service
echo "📝 Creating web server service..."
sudo tee /etc/systemd/system/sports-server.service > /dev/null <<EOF
[Unit]
Description=E-Ink Scoreboard Web Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$VENV_PATH/bin
ExecStart=$VENV_PATH/bin/python src/dev_server.py --port 5001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Copy sports-display.service file
echo "📝 Installing display service..."
if [ -f "sports-display.service" ]; then
    # Update paths in service file before copying
    sed "s|/home/patdugan/sports-display|$PROJECT_DIR|g; s|/home/patdugan/.virtualenvs/pimoroni|$VENV_PATH|g" sports-display.service | sudo tee /etc/systemd/system/sports-display.service > /dev/null
    echo "✅ Service file installed with correct paths"
else
    echo "⚠️ Warning: sports-display.service file not found in project root"
    echo "Creating basic service file..."
    sudo tee /etc/systemd/system/sports-display.service > /dev/null <<EOF
[Unit]
Description=E-Ink Scoreboard Display
After=network.target sports-server.service
Requires=sports-server.service

[Service]
Type=notify
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$VENV_PATH/bin/python src/eink_display.py --config src/eink_config.json

# Restart policy
Restart=always
RestartSec=30

# Watchdog - systemd will restart if no heartbeat in 3 minutes
WatchdogSec=180

# Resource limits
MemoryLimit=200M
MemorySwapMax=100M

# Kill timeout
TimeoutStopSec=30
KillMode=mixed

[Install]
WantedBy=multi-user.target
EOF
fi

# Install watchdog monitor service
echo "🐕 Installing watchdog monitor service..."
if [ -f "sports-watchdog.service" ]; then
    sed "s|/home/patdugan/sports-display|$PROJECT_DIR|g; s|/home/patdugan/.virtualenvs/pimoroni|$VENV_PATH|g" sports-watchdog.service | sudo tee /etc/systemd/system/sports-watchdog.service > /dev/null
    echo "✅ Watchdog service installed"
else
    echo "⚠️ Creating basic watchdog service..."
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

# Enable and start services
echo "🚀 Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable sports-server.service
sudo systemctl enable sports-display.service
sudo systemctl enable sports-watchdog.service

# Setup daily reboot for memory management
echo "⏰ Setting up daily reboot schedule..."
CRON_JOB="0 4 * * * /sbin/shutdown -r now"
CRON_COMMENT="# E-Ink Scoreboard: Daily reboot at 4 AM for memory management"

# Check if cron job already exists
if ! (crontab -l 2>/dev/null | grep -q "E-Ink Scoreboard.*Daily reboot"); then
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_COMMENT"; echo "$CRON_JOB") | crontab -
    echo "✅ Daily reboot scheduled for 4:00 AM"
else
    echo "✅ Daily reboot schedule already configured"
fi

echo "✅ Services created and enabled!"
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