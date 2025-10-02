# SystemD Service Templates

This document describes the systemd service files used for the Sports E-Ink Display project.

## Service Files Location

Service templates are stored in the `services/` directory:

- `services/sports-display.service` - Main display service that runs the e-ink display
- `services/sports-watchdog.service` - Watchdog monitor service that ensures the display service stays healthy

The web server service is created dynamically during installation:

- `sports-server.service` - Web server that provides the display page and API endpoints

## Template Variables

The service files use template placeholders that are replaced during installation:

- `{{USER}}` - The username that will run the service
- `{{PROJECT_DIR}}` - The project installation directory
- `{{VENV_PATH}}` - Path to the Python virtual environment

## Installation

### Automated Installation

Use the setup script to automatically install and configure the services:

```bash
cd /path/to/sports-scores-plugin
./scripts/setup-services.sh
```

The script will:

1. Replace template variables with actual system values
2. Install services to `/etc/systemd/system/`
3. Enable them for automatic startup
4. Configure proper permissions

### Manual Installation

If you need to install manually:

```bash
# Navigate to project directory
cd /path/to/sports-scores-plugin

# Replace placeholders and install display service
sed -e "s|{{USER}}|$USER|g" \
    -e "s|{{PROJECT_DIR}}|$(pwd)|g" \
    -e "s|{{VENV_PATH}}|/path/to/venv|g" \
    services/sports-display.service | sudo tee /etc/systemd/system/sports-display.service

# Replace placeholders and install watchdog service
sed -e "s|{{USER}}|$USER|g" \
    -e "s|{{PROJECT_DIR}}|$(pwd)|g" \
    -e "s|{{VENV_PATH}}|/path/to/venv|g" \
    services/sports-watchdog.service | sudo tee /etc/systemd/system/sports-watchdog.service

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable sports-display.service
sudo systemctl enable sports-watchdog.service

# Start services
sudo systemctl start sports-display.service
sudo systemctl start sports-watchdog.service
```

## Service Management

### Starting Services

```bash
sudo systemctl start sports-server.service
sudo systemctl start sports-display.service
sudo systemctl start sports-watchdog.service
```

### Stopping Services

```bash
sudo systemctl stop sports-display.service
sudo systemctl stop sports-watchdog.service
sudo systemctl stop sports-server.service
```

### Checking Status

```bash
sudo systemctl status sports-server.service
sudo systemctl status sports-display.service
sudo systemctl status sports-watchdog.service
```

### Viewing Logs

```bash
# Real-time logs
sudo journalctl -u sports-server.service -f
sudo journalctl -u sports-display.service -f
sudo journalctl -u sports-watchdog.service -f

# Recent logs
sudo journalctl -u sports-display.service --since "1 hour ago"
sudo journalctl -u sports-server.service --since "1 hour ago"
```

## Service Features

### Sports Server Service

- **Type**: simple
- **Restart Policy**: Always restarts on failure
- **Restart Delay**: 10 seconds
- **Purpose**: Runs Flask web server on port 5001
- **Provides**: API endpoints and display page
- **Created**: Dynamically during installation (not a template file)

### Sports Display Service

- **Type**: notify (sends readiness notifications to systemd)
- **Restart Policy**: Always restarts on failure
- **Restart Delay**: 30 seconds
- **Watchdog**: 180 seconds (systemd restarts if no heartbeat)
- **Memory Limits**: 200M main, 100M swap
- **Timeout**: 30 seconds for graceful shutdown
- **Dependencies**: Requires sports-server.service

### Sports Watchdog Service

- **Type**: simple
- **Restart Policy**: Always restarts on failure
- **Restart Delay**: 60 seconds
- **Dependencies**: Starts after sports-display.service
- **Purpose**: Monitors display service health and can trigger restarts

## Troubleshooting

### Service Won't Start

1. Check logs: `sudo journalctl -u sports-display.service -n 50`
2. Verify paths are correct: `sudo systemctl cat sports-display.service`
3. Check permissions: `ls -la /path/to/project`

### Service Keeps Restarting

1. Check for errors in logs
2. Verify Python environment: `/path/to/venv/bin/python --version`
3. Test manually: `/path/to/venv/bin/python src/eink_display.py --config src/eink_config.json`

### Memory Issues

If service is killed due to memory limits:

1. Check current usage: `sudo systemctl show sports-display.service -p MemoryCurrent`
2. Adjust limits in service file if needed
3. Restart service after changes
