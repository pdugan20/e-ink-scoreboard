# Raspberry Pi Setup Instructions

## Prerequisites

- Raspberry Pi 4 (recommended) or Pi 3B+
- MicroSD card (16GB+)
- Pimoroni Inky display (tested with Inky wHAT/pHAT)
- Internet connection

## 1. Raspberry Pi OS Setup

1. Flash Raspberry Pi OS Lite (64-bit) to your SD card
2. Enable SSH before first boot (add empty `ssh` file to boot partition)
3. Boot the Pi and SSH in:
   ```bash
   ssh pi@raspberrypi.local
   # Default password: raspberry (change this!)
   ```

## 2. System Updates & Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and development tools
sudo apt install -y python3-pip python3-venv git

# Install Chromium for screenshots
sudo apt install -y chromium-browser

# Install system libraries for PIL/graphics
sudo apt install -y libjpeg-dev libopenjp2-7 libtiff5-dev
```

## 3. Enable SPI for Inky Display

```bash
# Enable SPI interface
sudo raspi-config
# Navigate to: Interfacing Options > SPI > Enable

# Or edit config directly:
echo 'dtparam=spi=on' | sudo tee -a /boot/config.txt
sudo reboot
```

## 4. Install Inky Library

```bash
# Install Inky display library
pip3 install inky

# Test installation
python3 -c "from inky import Inky; print('Inky library installed successfully')"
```

## 5. Project Setup

```bash
# Clone your project
git clone [YOUR_REPO_URL]
cd eink-sports-scores/sports-scores-plugin

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright and browser (for high-quality screenshots)
playwright install chromium

# Make scripts executable
chmod +x eink_display.py
```

## 6. Configuration

Create/edit `eink_config.json`:

```json
{
  "web_server_url": "http://localhost:5001/display",
  "screenshot_path": "/tmp/sports_display.png",
  "display_width": 800,
  "display_height": 400,
  "refresh_interval": 300,
  "max_retries": 3,
  "retry_delay": 5
}
```

## 7. Test the Setup

```bash
# Start the web server in background
nohup python dev_server.py --port 5001 > server.log 2>&1 &

# Test single display update (uses high-quality Playwright screenshots)
python eink_display.py --once

# If successful, you should see your eink display update with crisp, live MLB scores!
```

**Screenshot Quality:**
- Uses Playwright for precise viewport control and 2x DPI rendering
- Takes 1600x800 screenshot, downsamples to 800x400 for crisp text/logos
- Falls back to Chromium if Playwright unavailable

## 8. Automatic Startup (Systemd Services)

### Create Web Server Service

```bash
sudo nano /etc/systemd/system/sports-server.service
```

```ini
[Unit]
Description=Sports Scores Web Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/eink-sports-scores/sports-scores-plugin
Environment=PATH=/home/pi/eink-sports-scores/sports-scores-plugin/venv/bin
ExecStart=/home/pi/eink-sports-scores/sports-scores-plugin/venv/bin/python dev_server.py --port 5001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Create Display Update Service

```bash
sudo nano /etc/systemd/system/sports-display.service
```

```ini
[Unit]
Description=Sports Scores Eink Display
After=network.target sports-server.service
Requires=sports-server.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/eink-sports-scores/sports-scores-plugin
Environment=PATH=/home/pi/eink-sports-scores/sports-scores-plugin/venv/bin
ExecStart=/home/pi/eink-sports-scores/sports-scores-plugin/venv/bin/python eink_display.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

### Enable Services

```bash
# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable sports-server.service
sudo systemctl enable sports-display.service
sudo systemctl start sports-server.service
sudo systemctl start sports-display.service

# Check status
sudo systemctl status sports-server.service
sudo systemctl status sports-display.service

# View logs
sudo journalctl -u sports-server.service -f
sudo journalctl -u sports-display.service -f
```

## 9. Refresh Rate Configuration

You can adjust the refresh rate by modifying `eink_config.json`:

```json
{
  "refresh_interval": 300,  // 5 minutes
  "_intervals": {
    "1_minute": 60,
    "5_minutes": 300,
    "15_minutes": 900,
    "30_minutes": 1800,
    "1_hour": 3600,
    "2_hours": 7200
  }
}
```

**Recommended intervals:**
- **5-15 minutes** during active game times
- **30-60 minutes** for general use
- **2+ hours** to preserve eink display lifespan

## 10. Manual Control Commands

```bash
# Update display once
python eink_display.py --once

# Update with custom interval (in seconds)
python eink_display.py --interval 600  # 10 minutes

# Use custom config file
python eink_display.py --config my_config.json

# Update with custom server URL
python eink_display.py --url http://localhost:5002/display
```

## 11. Troubleshooting

### Display Not Updating
```bash
# Check if services are running
sudo systemctl status sports-server.service
sudo systemctl status sports-display.service

# Test server manually
curl http://localhost:5001/display

# Test display script manually
python eink_display.py --once
```

### Screenshot Issues
```bash
# Test Chromium manually
chromium-browser --headless --screenshot=/tmp/test.png --window-size=800,400 http://localhost:5001/display

# Check screenshot was created
ls -la /tmp/test.png
```

### SPI/Display Issues
```bash
# Check SPI is enabled
lsmod | grep spi

# Test Inky library
python3 -c "from inky import Inky; inky = Inky(); print(f'Display: {inky.width}x{inky.height}')"
```

### Permission Issues
```bash
# Fix ownership
sudo chown -R pi:pi /home/pi/eink-sports-scores/

# Fix permissions for temp files
sudo chmod 777 /tmp
```

## 12. Performance Optimization

### Reduce Memory Usage
```bash
# Edit /boot/config.txt
sudo nano /boot/config.txt

# Add these lines:
gpu_mem=16
disable_camera=1
```

### Faster Boot (Optional)
```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-powersave@wlan0.service
```

## 13. Monitoring & Logs

```bash
# View real-time logs
sudo journalctl -u sports-display.service -f

# Check system resources
htop

# Monitor display updates
tail -f /var/log/syslog | grep sports
```

## Notes

- **Eink Display Lifespan**: Avoid refreshing more than once every 5 minutes to preserve display
- **Power**: Consider a UPS for uninterrupted operation
- **Network**: Ensure stable internet connection for live sports data
- **Storage**: Use a high-quality SD card (Class 10+) for reliability

## Support

If you encounter issues:

1. Check the logs: `sudo journalctl -u sports-display.service`
2. Test components individually: server, screenshot, display
3. Verify all dependencies are installed
4. Ensure SPI is properly enabled for the Inky display