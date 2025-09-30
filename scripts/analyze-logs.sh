#!/bin/bash
# Log analysis script for debugging e-ink display issues

set -e

LOG_FILE="$HOME/logs/eink_display.log"
SYSTEM_LOG_TIME_RANGE="1 hour ago"

echo "🔍 E-Ink Display Log Analysis"
echo "============================"

# Check if log file exists
if [[ ! -f "$LOG_FILE" ]]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "💡 Make sure the display service is running and has write permissions to ~/logs/"
    exit 1
fi

echo "📄 Log file: $LOG_FILE"
echo "📊 File size: $(du -h "$LOG_FILE" | cut -f1)"
echo "🕐 Last modified: $(stat -c %y "$LOG_FILE" 2>/dev/null || stat -f %m "$LOG_FILE")"
echo ""

# Show recent errors
echo "🚨 Recent Errors (last 50 lines):"
echo "--------------------------------"
tail -n 1000 "$LOG_FILE" | grep -E " - ERROR - | - CRITICAL - | - WARNING - " | tail -n 50 || echo "No recent errors found"
echo ""

# Show memory snapshots
echo "💾 Memory Usage Snapshots:"
echo "-------------------------"
tail -n 1000 "$LOG_FILE" | grep "RESOURCE_SNAPSHOT" | tail -n 10 || echo "No resource snapshots found"
echo ""

# Show browser process info
echo "🌐 Browser Process Information:"
echo "------------------------------"
tail -n 1000 "$LOG_FILE" | grep -E "browser|Browser|\[WORKER\].*browser" | tail -n 20 || echo "No browser process info found"
echo ""

# Show screenshot activity
echo "📸 Screenshot Activity:"
echo "----------------------"
tail -n 1000 "$LOG_FILE" | grep -E "screenshot|\[WORKER\]|playwright|chromium" | tail -n 20 || echo "No screenshot activity found"
echo ""

# Show worker subprocess logs
echo "👷 Worker Subprocess Activity:"
echo "-----------------------------"
tail -n 1000 "$LOG_FILE" | grep "\[WORKER\]" | tail -n 30 || echo "No worker subprocess logs found"
echo ""

# Show recent startup/shutdown
echo "🔄 Service Restarts:"
echo "-------------------"
tail -n 1000 "$LOG_FILE" | grep -E "STARTING|Shutting down|Cleaning up" | tail -n 10 || echo "No recent restarts found"
echo ""

# Check system memory and process status
echo "🖥️  Current System Status:"
echo "-------------------------"
if command -v free &> /dev/null; then
    echo "Memory usage:"
    free -h
    echo ""
fi

if command -v ps &> /dev/null; then
    echo "E-ink related processes:"
    ps aux | grep -E "eink_display|sports-|chromium|chrome|playwright" | grep -v grep || echo "No related processes found"
    echo ""
fi

# Check for hanging browser processes
echo "🌐 Browser Processes:"
echo "-------------------"
if command -v ps &> /dev/null; then
    ps aux | grep -E "chromium|chrome|playwright" | grep -v grep | head -n 10 || echo "No browser processes found"
fi

echo ""
echo "📋 Analysis Tips:"
echo "-----------------"
echo "• Look for MEMORY_ERROR or MemoryError in recent errors"
echo "• Check if browser process count keeps increasing"
echo "• Monitor resource snapshots for memory/CPU trends"
echo "• Use 'sudo journalctl -u sports-display.service -f' for real-time system logs"
echo "• Check disk space with 'df -h' if logs aren't being written"
echo ""

# Optional: Check system logs for Out of Memory kills
if command -v journalctl &> /dev/null; then
    echo "🔍 Checking system logs for OOM kills in last hour:"
    echo "------------------------------------------------"
    sudo journalctl --since "$SYSTEM_LOG_TIME_RANGE" | grep -i "killed\|oom\|out of memory" | tail -n 10 || echo "No OOM kills found in system logs"
    echo ""
fi

echo "✅ Analysis complete!"
echo "💡 For real-time monitoring: tail -f $LOG_FILE | grep -E 'ERROR|CRITICAL|RESOURCE_SNAPSHOT|\[WORKER\]'"