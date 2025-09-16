#!/bin/bash
# E-Ink Scoreboard - Raspberry Pi Installation Script

set -e  # Exit on any error

echo "E-Ink Scoreboard Installation"
echo "===================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "❌ This script is designed for Raspberry Pi only"
    exit 1
fi

echo "✅ Detected Raspberry Pi"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt install -y python3-pip python3-venv git
sudo apt install -y libjpeg-dev libopenjp2-7 libtiff5-dev

# Configure hardware interfaces
echo "⚙️  Configuring SPI and I2C..."
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0

# Add SPI configuration
if ! grep -q "dtoverlay=spi0-0cs" /boot/firmware/config.txt; then
    echo 'dtoverlay=spi0-0cs' | sudo tee -a /boot/firmware/config.txt
    echo "✅ Added SPI configuration"
else
    echo "✅ SPI configuration already present"
fi

# Install Inky library
echo "🖥️  Installing Inky display library..."
if [ ! -d "$HOME/inky" ]; then
    cd ~
    git clone https://github.com/pimoroni/inky.git
    cd inky
    echo "y" | ./install.sh
    echo "✅ Inky library installed"
else
    echo "✅ Inky library directory already exists"
    # Check if virtual environment exists
    if [ ! -d "$HOME/.virtualenvs/pimoroni" ]; then
        echo "⚠️  Virtual environment missing, recreating..."
        rm -rf ~/inky
        cd ~
        git clone https://github.com/pimoroni/inky.git
        cd inky
        echo "y" | ./install.sh
        echo "✅ Inky library installed fresh"
    else
        echo "✅ Inky virtual environment already present"
    fi
fi

# Go back to project directory
cd ~/e-ink-scoreboard

# Activate Pimoroni virtual environment
echo "🐍 Setting up Python environment..."
source ~/.virtualenvs/pimoroni/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Create log directory and set permissions
echo "📝 Setting up logging..."
sudo mkdir -p /var/log/eink-display
sudo chown $(whoami):$(whoami) /var/log/eink-display
mkdir -p /tmp/eink-logs
chmod 755 /tmp/eink-logs
echo "✅ Log directories created"

# Install Playwright and WebKit dependencies
echo "🌐 Installing Playwright..."
playwright install-deps webkit || echo "⚠️  Failed to install WebKit system dependencies"
playwright install webkit || echo "⚠️  Playwright WebKit install failed - screenshots won't work"

# Make scripts executable
chmod +x src/eink_display.py
chmod +x scripts/setup-services.sh
chmod +x scripts/configure.sh
chmod +x scripts/analyze-logs.sh

echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Run './scripts/configure.sh' to set preferences"
echo "2. Run './scripts/setup-services.sh' to configure auto-startup"
echo "3. Test with: 'python src/eink_display.py --once'"
echo "4. Reboot to apply all hardware changes"
echo ""
echo "📝 Debugging tools:"
echo "• View logs: tail -f ~/logs/eink_display.log"
echo "• Analyze logs: ./scripts/analyze-logs.sh"
echo "• Service status: sudo systemctl status sports-display.service"
echo ""
echo "🎉 Your sports scores display is ready!"