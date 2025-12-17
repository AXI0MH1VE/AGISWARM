#!/bin/bash
# macOS WiFi Fix Script for Edge-Lattice System
# This script restores WiFi connectivity on macOS after netns_setup.sh interference

set -e

WIFI_INTERFACE="en0"

echo "=== macOS WiFi Restoration Script ==="
echo "Interface: $WIFI_INTERFACE"

# Check if interface exists
if ! ifconfig $WIFI_INTERFACE >/dev/null 2>&1; then
    echo "Error: WiFi interface $WIFI_INTERFACE not found"
    echo "Available interfaces:"
    ifconfig | grep -E "^[a-z]" | cut -d: -f1
    exit 1
fi

# Step 1: Ensure WiFi power is on
echo "Step 1: Enabling WiFi power..."
networksetup -setairportpower $WIFI_INTERFACE on

# Step 2: Bring interface down and up
echo "Step 2: Resetting WiFi interface..."
ifconfig $WIFI_INTERFACE down
sleep 1
ifconfig $WIFI_INTERFACE up

# Step 3: Wait for interface to be ready
echo "Step 3: Waiting for interface to initialize..."
sleep 3

# Step 4: Check WiFi status
echo "Step 4: Checking WiFi status..."
WIFI_STATUS=$(networksetup -getairportpower $WIFI_INTERFACE 2>/dev/null || echo "WiFi Status: Unknown")
echo "$WIFI_STATUS"

# Step 5: Get current network
echo "Step 5: Current WiFi network:"
CURRENT_NETWORK=$(networksetup -getairportnetwork $WIFI_INTERFACE 2>/dev/null || echo "No network connected")
echo "$CURRENT_NETWORK"

# Step 6: Restart WiFi service if needed
if echo "$CURRENT_NETWORK" | grep -q "No network connected"; then
    echo "Step 6: WiFi appears disconnected, attempting to restart WiFi service..."
    
    # Turn WiFi off and on
    networksetup -setairportpower $WIFI_INTERFACE off
    sleep 2
    networksetup -setairportpower $WIFI_INTERFACE on
    sleep 3
    
    echo "WiFi service restarted. You may need to reconnect to your network manually."
else
    echo "WiFi appears to be functioning normally."
fi

echo ""
echo "=== VERIFICATION ==="
echo "WiFi Power Status:"
networksetup -getairportpower $WIFI_INTERFACE
echo ""
echo "WiFi Network Status:"
networksetup -getairportnetwork $WIFI_INTERFACE
echo ""
echo "Interface Status:"
ifconfig $WIFI_INTERFACE | grep -E "(flags|inet)"