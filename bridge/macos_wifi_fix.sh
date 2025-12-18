#!/bin/bash
# macos_wifi_fix.sh - Fix WiFi connectivity issues on macOS
# Usage: ./macos_wifi_fix.sh

set -e

echo "=== macOS WiFi Recovery Script ==="
echo "This script will attempt to fix common WiFi issues on macOS"
echo ""

# Get the WiFi interface name (usually en0 or en1)
WIFI_INTERFACE=$(networksetup -listallhardwareports | awk '/Wi-Fi|AirPort/{getline; print $2}' | head -n 1)

if [ -z "$WIFI_INTERFACE" ]; then
    echo "Error: Could not detect WiFi interface"
    exit 1
fi

echo "Detected WiFi interface: $WIFI_INTERFACE"
echo ""

# Turn WiFi off
echo "Turning WiFi off..."
networksetup -setairportpower "$WIFI_INTERFACE" off
sleep 2

# Turn WiFi on
echo "Turning WiFi on..."
networksetup -setairportpower "$WIFI_INTERFACE" on
sleep 3

# Flush DNS cache
echo "Flushing DNS cache..."
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder 2>/dev/null || true

# Renew DHCP lease
echo "Renewing DHCP lease..."
sudo ipconfig set "$WIFI_INTERFACE" DHCP

echo ""
echo "=== WiFi recovery complete ==="
echo "Please wait a moment for WiFi to reconnect"
