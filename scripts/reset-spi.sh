#!/bin/bash
# Reset SPI bus and e-ink display to recover from hangs

echo "🔄 Resetting SPI bus and e-ink display..."

# Kill any processes using the display
echo "📍 Stopping display service..."
sudo systemctl stop sports-display.service 2>/dev/null

# Kill any Python processes that might be holding SPI
echo "🔪 Killing Python processes..."
sudo pkill -9 -f "eink_display.py"
sudo pkill -9 -f "inky"

# Unload and reload SPI modules
echo "🔧 Resetting SPI kernel modules..."
sudo modprobe -r spi_bcm2835
sleep 1
sudo modprobe spi_bcm2835

# Reset GPIO pins used by Inky display
echo "📌 Resetting GPIO pins..."
# Inky typically uses GPIO 17 (busy), 27 (reset), 22 (DC)
for pin in 17 27 22; do
    echo $pin > /sys/class/gpio/export 2>/dev/null
    echo "out" > /sys/class/gpio/gpio${pin}/direction 2>/dev/null
    echo "0" > /sys/class/gpio/gpio${pin}/value 2>/dev/null
    sleep 0.1
    echo "1" > /sys/class/gpio/gpio${pin}/value 2>/dev/null
    echo $pin > /sys/class/gpio/unexport 2>/dev/null
done

# Clear any stuck SPI transactions
echo "🧹 Clearing SPI buffers..."
sudo dd if=/dev/zero of=/dev/spidev0.0 bs=1 count=1 2>/dev/null

echo "⏳ Waiting for SPI to stabilize..."
sleep 2

# Restart the service
echo "▶️ Restarting display service..."
sudo systemctl start sports-display.service

echo "✅ SPI reset complete!"
echo "📊 Check status with: sudo systemctl status sports-display.service"