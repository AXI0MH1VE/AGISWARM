#!/bin/bash
# Cleanup script to restore normal network connectivity
# Run this to reverse the netns_setup.sh changes

set -e

NS="control_net"
PHY_IF="wlan1"  # Adjust to your mesh interface
VETH_HOST="veth_h"
VETH_NS="veth_n"

echo "Cleaning up network namespace setup..."

# Remove NFTables rules and table
echo "Removing NFTables rules..."
if nft list tables 2>/dev/null | grep -q "table inet filter"; then
    nft delete table inet filter 2>/dev/null || echo "NFTables table already removed or doesn't exist"
fi

# Move interface back to main namespace
echo "Moving $PHY_IF back to main namespace..."
if ip netns exec $NS ip link show $PHY_IF >/dev/null 2>&1; then
    ip netns exec $NS ip link set $PHY_IF down
    ip link set $PHY_IF netns 1 || ip link set $PHY_IF netns $$
fi

# Remove veth pair
echo "Removing veth pair..."
if ip link show $VETH_HOST >/dev/null 2>&1; then
    ip link delete $VETH_HOST 2>/dev/null || echo "veth pair already removed"
fi

# Remove network namespace
echo "Removing network namespace..."
if ip netns show $NS >/dev/null 2>&1; then
    ip netns del $NS
fi

# Bring up WiFi interface
echo "Bringing up WiFi interface..."
if ip link show $PHY_IF >/dev/null 2>&1; then
    ip link set $PHY_IF up
    echo "WiFi interface $PHY_IF is back online"
else
    echo "Warning: $PHY_IF interface not found"
    echo "Your WiFi interface might have a different name"
    echo "Available interfaces:"
    ip link show | grep -E "^[0-9]+" | cut -d: -f2 | sed 's/^ *//'
fi

echo "Network cleanup complete. Your WiFi should be restored."