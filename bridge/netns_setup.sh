#!/bin/bash
# Must be run as root
set -e

NS="control_net"
PHY_IF="wlan1" # Adjust to your mesh interface
VETH_HOST="veth_h"
VETH_NS="veth_n"

echo "Creating Network Namespace: $NS"
ip netns add $NS

echo "Moving Mesh Interface to $NS"
ip link set $PHY_IF netns $NS

echo "Creating VETH Pair"
ip link add $VETH_HOST type veth peer name $VETH_NS
ip link set $VETH_NS netns $NS

echo "Configuring IPs"
ip addr add 192.168.100.1/24 dev $VETH_HOST
ip link set $VETH_HOST up

ip netns exec $NS ip addr add 192.168.100.2/24 dev $VETH_NS
ip netns exec $NS ip link set $VETH_NS up
ip netns exec $NS ip link set $PHY_IF up
# Bring up mesh (simplified)
# ip netns exec $NS iw dev $PHY_IF mesh join "lat_mesh"

echo "Applying Firewall (NFTables) - Air Gap Enforced"
# Drop everything by default, allow established, and specific UDP port for Operator
nft add table inet filter
nft add chain inet filter input { type filter hook input priority 0 \; policy drop \; }
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input iifname "$VETH_HOST" udp dport 6000 accept

echo "Isolation Complete."

