# Troubleshooting Guide

This guide covers common issues and their solutions for the E-Ink Scoreboard.

## Display Not Updating

### Understanding Display Update Logic

The display uses smart update logic to minimize e-ink wear:

**Automatic Updates:**

- ✅ **New game day**: Updates once to show "Games start at X:XX"
- ✅ **Games active**: Regular updates while games are in progress
- ❌ **Games scheduled only**: Skips updates to preserve e-ink display

**Update Schedule:**

1. **Daily**: One update when new games are detected for the day
2. **During games**: Updates every 6 minutes (configurable) while games are active
3. **Between games**: No updates until next active game

### Force a Display Update

If you need to manually update the display:

```bash
# Force immediate update (bypasses active game check)
python src/eink_display.py --once --config src/eink_config.json

# Or restart the display service to trigger new day detection
sudo systemctl restart sports-display.service
```

### Check Services Status

```bash
# Check if services are running
sudo systemctl status sports-server.service
sudo systemctl status sports-display.service

# Test server manually
curl http://localhost:5001/display

# Test display script manually (will respect active game logic)
python src/eink_display.py --once --config src/eink_config.json
```

### Restart Services

```bash
sudo systemctl restart sports-server.service
sudo systemctl restart sports-display.service
```

## Screenshot Issues

### Test Screenshot Generation

```bash
# Test Playwright manually
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(headless=True); page = browser.new_page(); page.goto('http://localhost:5001/display'); page.screenshot(path='/tmp/test.png'); browser.close(); p.stop()"

# Check screenshot was created
ls -la /tmp/test.png
```

### Playwright Issues

```bash
# Test if Playwright is working
python3 -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# Reinstall Playwright if needed
./venv/bin/playwright install chromium
```

## SPI/Display Issues

### Check Hardware Configuration

```bash
# Check SPI and I2C are enabled
lsmod | grep spi
lsmod | grep i2c

# Check config file
cat /boot/firmware/config.txt | grep -E "(spi|i2c|dtoverlay)"
```

### Test Inky Library

```bash
# Test Inky library connection
python3 -c "from inky import Inky; inky = Inky(); print(f'Display: {inky.width}x{inky.height}')"

# If auto-detection fails, try manual initialization
python3 -c "from inky.impression import Inky; inky = Inky(); print('Manual init OK')"
```

### Enable SPI/I2C (if not working)

```bash
# Edit config file
sudo nano /boot/firmware/config.txt

# Ensure these lines are present:
dtparam=spi=on
dtparam=i2c_arm=on
dtoverlay=spi1-3cs

# Reboot after changes
sudo reboot
```

## Permission Issues

### Fix File Ownership

```bash
# Fix ownership of project files
sudo chown -R pi:pi /home/pi/eink-sports-scores/

# Fix permissions for temp files
sudo chmod 777 /tmp
```

### Service User Issues

```bash
# Check what user services are running as
sudo systemctl show sports-server.service -p User
sudo systemctl show sports-display.service -p User

# Both should show: User=pi
```

## Network/API Issues

### Test Internet Connection

```bash
# Test general connectivity
ping -c 3 google.com

# Test ESPN API directly
curl -s "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard" | jq .
```

### Firewall Issues

```bash
# Check if local server is accessible
netstat -tlnp | grep :5001
curl -v http://localhost:5001/display
```

## Performance Issues

### Memory Problems

```bash
# Check memory usage
free -h
htop

# Check for memory leaks in services
sudo systemctl status sports-server.service
sudo systemctl status sports-display.service
```

### CPU/Temperature

```bash
# Check CPU temperature
vcgencmd measure_temp

# Check CPU usage
top -p $(pgrep -f "sports")
```

## Log Analysis

### Application Logs

The system now includes comprehensive application logging with resource monitoring:

```bash
# View application logs (new detailed logging)
tail -f ~/logs/eink_display.log

# Filter for errors and resource information
tail -f ~/logs/eink_display.log | grep -E 'ERROR|CRITICAL|RESOURCE_SNAPSHOT'

# Quick log analysis tool
./scripts/analyze-logs.sh
```

**The log analysis script provides:**

- Recent errors and memory issues
- Browser process tracking and cleanup
- Resource usage snapshots
- System memory analysis
- Out-of-memory (OOM) kill detection

### View Service Logs

```bash
# View real-time logs
sudo journalctl -u sports-display.service -f
sudo journalctl -u sports-server.service -f

# View recent logs
sudo journalctl -u sports-display.service --since "1 hour ago"

# View logs with more detail
sudo journalctl -u sports-display.service -n 50 --no-pager
```

### Check System Logs

```bash
# Monitor display updates
tail -f /var/log/syslog | grep sports

# Check for errors
grep -i error /var/log/syslog | tail -20

# Check for out-of-memory kills
sudo journalctl --since "1 hour ago" | grep -i "oom\|killed"
```

### Debug Browser Process Issues

```bash
# Check for hanging browser processes
ps aux | grep -E "chromium|chrome|playwright" | grep -v grep

# Monitor browser process count during screenshot
watch -n 2 "ps aux | grep -E 'chromium|chrome|playwright' | grep -v grep | wc -l"
```

## Configuration Issues

### Validate Config File

```bash
# Check config file syntax
python3 -c "import json; print(json.load(open('src/eink_config.json')))"

# Reset to defaults
cp src/eink_config.json.example src/eink_config.json
```

### Web Server Issues

```bash
# Test if web server responds
curl -v http://localhost:5001/display

# Check if port is in use
sudo lsof -i :5001

# Test with different port
python src/dev_server.py --port 5002
```

## Hardware Diagnostics

### Display Connection

```bash
# Check if display is detected
dmesg | grep -i inky
dmesg | grep -i spi

# Check GPIO connections
gpio readall  # If wiringPi is installed
```

### Power Issues

```bash
# Check power supply voltage
vcgencmd measure_volts

# Check throttling
vcgencmd get_throttled
```

## Recovery Steps

### Complete Service Reset

```bash
# Stop all services
sudo systemctl stop sports-display.service
sudo systemctl stop sports-server.service

# Clear any stuck processes
sudo pkill -f "dev_server.py"
sudo pkill -f "eink_display.py"

# Restart services
sudo systemctl start sports-server.service
sleep 5
sudo systemctl start sports-display.service
```

### Scheduled Maintenance

The system includes a daily reboot at 4:00 AM for memory management:

```bash
# View scheduled reboots
crontab -l | grep reboot

# Disable daily reboot (if needed)
crontab -e
# Comment out or remove the reboot line

# Manual reboot
sudo reboot
```

### Factory Reset

```bash
# Backup current config
cp src/eink_config.json src/eink_config.json.backup

# Reset to defaults
git checkout src/eink_config.json

# Restart services
sudo systemctl restart sports-server.service
sudo systemctl restart sports-display.service
```

## Getting Help

If none of these solutions work:

1. **Check logs first**: `sudo journalctl -u sports-display.service --since "1 hour ago"`
2. **Test components individually**: server → screenshot → display
3. **Document the error**: Copy exact error messages
4. **Check hardware**: Ensure all connections are secure
5. **Try a reboot**: Sometimes fixes intermittent issues

### Common Error Messages

| Error                       | Likely Cause               | Solution                              |
| --------------------------- | -------------------------- | ------------------------------------- |
| `ModuleNotFoundError: inky` | Inky library not installed | Run installation script               |
| `Permission denied`         | File ownership issues      | Fix with `sudo chown -R pi:pi`        |
| `Connection refused`        | Web server not running     | Check/restart services                |
| `SPI device not found`      | SPI not enabled            | Enable in `/boot/firmware/config.txt` |
| `Display timeout`           | Hardware connection        | Check physical connections            |
