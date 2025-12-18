#!/bin/bash
# cleanup_network.sh - Clean up network namespaces, bridges, and NFTables rules
# Usage: sudo ./cleanup_network.sh

set -e

echo "=== Starting network cleanup ==="

# Remove network namespace if it exists
if ip netns list | grep -q "mesh_ns"; then
    echo "Removing network namespace mesh_ns..."
    ip netns delete mesh_ns || echo "Failed to remove mesh_ns, may not exist"
fi

# Remove NFTables rules
if nft list tables 2>/dev/null | grep -q "table inet filter"; then
    echo "Removing NFTables inet filter table..."
    nft delete table inet filter 2>/dev/null || echo "NFTables table already removed or doesn't exist"
fi

if nft list tables 2>/dev/null | grep -q "table bridge filter"; then
    echo "Removing NFTables bridge filter table..."
    nft delete table bridge filter 2>/dev/null || echo "NFTables bridge table already removed or doesn't exist"
fi

# Remove veth pair if it exists
if ip link show veth_mesh 2>/dev/null; then
    echo "Removing veth pair..."
    ip link delete veth_mesh 2>/dev/null || echo "veth_mesh already removed or doesn't exist"
fi

echo "=== Network cleanup complete ==="
