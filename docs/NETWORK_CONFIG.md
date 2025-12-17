# AGISWARM Network Configuration Guide

## Table of Contents
1. [Network Architecture Overview](#network-architecture-overview)
2. [Network Isolation Setup](#network-isolation-setup)
3. [Mesh Networking Configuration](#mesh-networking-configuration)
4. [Production Deployment](#production-deployment)
5. [WiFi Configuration](#wifi-configuration)
6. [Firewall and Security](#firewall-and-security)
7. [Network Troubleshooting](#network-troubleshooting)
8. [Performance Optimization](#performance-optimization)

---

## Network Architecture Overview

### AGISWARM Network Model

AGISWARM uses a **dual-network architecture**:
1. **Management Network**: Standard network for operator access
2. **Control Network**: Isolated network for AGISWARM traffic

### Network Topology

```
                    ┌─────────────────┐
                    │   Internet      │
                    └─────────┬───────┘
                              │
                    ┌─────────▼───────┐
                    │  Home Router    │
                    │  (192.168.1.1)  │
                    └─────────┬───────┘
                              │
                    ┌─────────▼───────┐
                    │   Management    │
                    │   Network       │
                    │  (192.168.1.x)  │
                    └─────────┬───────┘
                              │
                    ┌─────────▼───────┐
                    │  Bridge Node    │
                    │ (Air Gap Setup) │
                    └─────────┬───────┘
                              │
                    ┌─────────▼───────┐
                    │  Control Net    │
                    │  (192.168.100.x)│
                    │  (Isolated)     │
                    └─────────┬───────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐    ┌────────▼──────┐    ┌────────▼──────┐
│  Aggregator  │    │    Worker     │    │    Worker     │
│  192.168.100.1│   │  192.168.100.2│   │  192.168.100.3│
└──────────────┘    └───────────────┘    └───────────────┘
```

### Network Components

#### 1. Network Namespace (`control_net`)
- **Purpose**: Isolated network environment
- **Isolation**: Complete separation from management network
- **Security**: Prevents unauthorized access to control traffic

#### 2. Virtual Ethernet Pair (veth)
- **Purpose**: Communication bridge between namespaces
- **Components**: `veth_host` (management) + `veth_ns` (control)
- **IP Range**: 192.168.100.0/24

#### 3. WiFi Mesh Network
- **Purpose**: Wireless communication between AGISWARM nodes
- **Standard**: IEEE 802.11s (mesh)
- **Security**: SAE (Simultaneous Authentication of Equals)

---

## Network Isolation Setup

### Automated Setup Script

**File**: `bridge/netns_setup.sh`

This script creates the isolated network environment:

```bash
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

echo "Applying Firewall (NFTables) - Air Gap Enforced"
nft add table inet filter
nft add chain inet filter input { type filter hook input priority 0 \; policy drop \; }
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input iifname "$VETH_HOST" udp dport 6000 accept

echo "Isolation Complete."
```

### Manual Setup Process

#### Step 1: Create Network Namespace
```bash
# Create isolated namespace
sudo ip netns add control_net

# Verify creation
ip netns list
```

#### Step 2: Identify WiFi Interface
```bash
# List all network interfaces
ip link show

# Common WiFi interface names:
# Linux: wlan0, wlan1, wlpx0
# macOS: en0, en1
```

#### Step 3: Create VETH Pair
```bash
# Create virtual ethernet pair
sudo ip link add veth_host type veth peer name veth_ns

# Assign interfaces to namespaces
sudo ip link set veth_ns netns control_net
```

#### Step 4: Configure IP Addresses
```bash
# Configure host side
sudo ip addr add 192.168.100.1/24 dev veth_host
sudo ip link set veth_host up

# Configure namespace side
sudo ip netns exec control_net ip addr add 192.168.100.2/24 dev veth_ns
sudo ip netns exec control_net ip link set veth_ns up
```

#### Step 5: Setup Firewall Rules
```bash
# Create NFTables rules
sudo nft add table inet filter
sudo nft add chain inet filter input { type filter hook input priority 0 \; policy drop \; }
sudo nft add rule inet filter input ct state established,related accept
sudo nft add rule inet filter input iifname "veth_host" udp dport 6000 accept

# Verify rules
sudo nft list ruleset
```

---

## Mesh Networking Configuration

### OpenWRT Mesh Setup

**File**: `bridge/openwrt_mesh_example.sh`

For production deployment on OpenWRT routers:

```bash
#!/bin/sh
# /etc/config/wireless snippet for OpenWRT

# Enable 802.11s Mesh
uci set wireless.radio0.channel='13'  # Non-overlapping channel
uci set wireless.default_radio0.mode='mesh'
uci set wireless.default_radio0.mesh_id='EDGE_LATTICE_01'
uci set wireless.default_radio0.encryption='sae'
uci set wireless.default_radio0.key='SuperSecureSecretKey'  # SAE Password
uci set wireless.default_radio0.mesh_fwding='1'

# Apply configuration
uci commit wireless
wifi reload

# Install TWAMP for telemetry
opkg update
opkg install twamp-light
```

### Manual Mesh Configuration

#### Linux Mesh Setup

```bash
# Enable mesh mode on WiFi interface
iw dev wlan0 interface add mesh0 type mesh

# Set mesh parameters
iw mesh0 mesh join EDGE_LATTICE_01
iw mesh0 mesh auth sae SuperSecureSecretKey

# Bring up mesh interface
ip link set mesh0 up

# Assign IP address in control network
ip addr add 192.168.100.10/24 dev mesh0
```

#### macOS Mesh Setup

```bash
# macOS doesn't support 802.11s mesh natively
# Alternative: Use WiFi ad-hoc mode or dedicated mesh hardware

# Create ad-hoc network (alternative to mesh)
sudo networksetup -createnetworkservice "AGISWARM-Mesh" "Wi-Fi"
sudo networksetup -setnetworkserviceenabled "AGISWARM-Mesh" on

# Configure ad-hoc network
sudo networksetup -setmanual "AGISWARM-Mesh" 192.168.100.10 255.255.255.0
```

### Mesh Network Security

#### SAE Authentication
```bash
# Configure SAE password
sudo iw mesh0 mesh auth sae "StrongMeshPassword123!"

# Verify mesh configuration
iw dev mesh0 mesh info
```

#### Network Isolation Verification
```bash
# Test isolation between networks
ping 192.168.1.1  # Should fail (management network)
ping 192.168.100.1  # Should work (control network)

# Verify firewall rules
sudo nft list ruleset | grep -E "(drop|accept)"
```

---

## Production Deployment

### Multi-Node Deployment

#### Aggregator Node Configuration
```bash
#!/bin/bash
# Setup aggregator node

# Configure aggregator IP
AGGREGATOR_IP="192.168.100.1"

# Setup network namespace
./bridge/netns_setup.sh

# Configure aggregator in namespace
sudo ip netns exec control_net python3 aggregator/main_runner.py \
    --ip $AGGREGATOR_IP \
    --port 6000 \
    --mesh-interface wlan0
```

#### Worker Node Configuration
```bash
#!/bin/bash
# Setup worker node

# Configure worker parameters
WORKER_ID="W001"
AGGREGATOR_IP="192.168.100.1"

# Setup network namespace
./bridge/netns_setup.sh

# Start worker in namespace
sudo ip netns exec control_net python3 worker/worker.py \
    --worker-id $WORKER_ID \
    --aggregator-ip $AGGREGATOR_IP \
    --aggregator-port 6000 \
    --mesh-interface wlan0
```

#### Operator Node Configuration
```bash
#!/bin/bash
# Setup operator node (no isolation needed)

# Start operator in management network
python3 operator/operator_cli.py \
    --aggregator-ip 192.168.100.1 \
    --aggregator-port 6000 \
    --private-key operator_private.key
```

### Cluster Configuration

#### High Availability Setup
```yaml
# configs/ha_config.yaml
cluster:
  aggregator_nodes:
    primary:
      ip: "192.168.100.1"
      port: 6000
      priority: 1
      health_check_interval: 5s
      
    backup_1:
      ip: "192.168.100.2"
      port: 6000
      priority: 2
      health_check_interval: 5s
      
    backup_2:
      ip: "192.168.100.3"
      port: 6000
      priority: 3
      health_check_interval: 5s

failover:
  detection_timeout: 15s
  promotion_delay: 5s
  heartbeat_interval: 2s
```

#### Load Balancer Configuration
```python
# aggregator/load_balancer.py
class LoadBalancer:
    def __init__(self, config):
        self.aggregators = config['cluster']['aggregator_nodes']
        self.current_primary = 0
        self.health_checker = HealthChecker()
        
    async def route_request(self, request):
        # Route to healthy aggregator
        for i in range(len(self.aggregators)):
            idx = (self.current_primary + i) % len(self.aggregators)
            if await self.health_checker.is_healthy(self.aggregators[idx]):
                return await self.send_to_aggregator(request, self.aggregators[idx])
        raise NoHealthyAggregatorError()
```

---

## WiFi Configuration

### WiFi Adapter Selection

#### Recommended Adapters
| Adapter | Driver | Performance | OpenWRT Support |
|---------|--------|-------------|-----------------|
| Intel AX200 | iwlwifi | Excellent | ✅ Full |
| Intel AX201 | iwlwifi | Excellent | ✅ Full |
| Alfa AWUS036ACS | mt7610u | Good | ✅ Good |
| TP-Link AC600 | rtl8812au | Fair | ⚠️ Limited |

#### Adapter Configuration
```bash
# Check adapter capabilities
iw list

# Enable monitor mode (for testing)
sudo ip link set wlan0 down
sudo iw wlan0 interface add mon0 type monitor
sudo ip link set mon0 up

# Return to managed mode
sudo ip link set mon0 down
sudo iw dev mon0 del
sudo ip link set wlan0 up
```

### Performance Optimization

#### WiFi Performance Tuning
```bash
# Optimize WiFi settings for mesh networking

# Set channel width
sudo iw dev wlan0 set channel 13 HT40

# Set transmit power (adjust based on regulations)
sudo iw dev wlan0 set txpower fixed 20

# Enable mesh peer link
sudo iw dev wlan0 mesh join EDGE_LATTICE_01 \
    mesh_param:mesh_retry_timeout=40 \
    mesh_param:mesh_confirm_timeout=40 \
    mesh_param:mesh_holding_timeout=40
```

#### Network Interface Optimization
```bash
# Optimize network interface settings
sudo ethtool -K wlan0 gro on
sudo ethtool -K wlan0 lro on
sudo ethtool -K wlan0 gso on
sudo ethtool -K wlan0 tso on

# Set ring buffer sizes
sudo ethtool -G wlan0 rx 4096 tx 4096

# Disable interrupts coalescing for real-time performance
sudo ethtool -C wlan1 adaptive-rx off adaptive-tx off
```

### Multi-BSS Configuration

#### Access Point + Mesh
```bash
# Create separate interfaces for AP and mesh
sudo iw dev wlan0 interface add ap0 type __ap
sudo iw dev wlan0 interface add mesh0 type mesh

# Configure access point
sudo hostapd_cli -i ap0 -p /var/run/hostapd ap0 << EOF
set ssid AGISWARM-AP
set wpa_passphrase SecurePassword123
set wpa 2
set rsn_pairwise CCMP
enable
EOF

# Configure mesh
sudo iw dev mesh0 mesh join EDGE_LATTICE_01
sudo ip addr add 192.168.100.10/24 dev mesh0
```

---

## Firewall and Security

### NFTables Configuration

#### Complete Firewall Ruleset
```bash
#!/bin/bash
# Complete NFTables configuration for AGISWARM

# Create tables
nft add table inet agiswarm_filter
nft add table inet agiswarm_nat

# Filter table
nft add chain inet agiswarm_filter input { type filter hook input priority 0 \; policy drop \; }
nft add chain inet agiswarm_filter output { type filter hook output priority 0 \; policy drop \; }
nft add chain inet agiswarm_filter forward { type filter hook forward priority 0 \; policy drop \; }

# Allow established connections
nft add rule inet agiswarm_filter input ct state established,related accept
nft add rule inet agiswarm_filter output ct state established,related accept

# Allow loopback
nft add rule inet agiswarm_filter input iifname lo accept
nft add rule inet agiswarm_filter output oifname lo accept

# Allow AGISWARM UDP traffic
nft add rule inet agiswarm_filter input iifname veth_host udp dport 6000 accept
nft add rule inet agiswarm_filter output oifname veth_host udp sport 6000 accept

# Allow mesh networking
nft add rule inet agiswarm_filter input iifname mesh0 accept
nft add rule inet agiswarm_filter output oifname mesh0 accept

# Log dropped packets
nft add rule inet agiswarm_filter input log prefix "AGISWARM_DROP: " limit rate 1/second
nft add rule inet agiswarm_filter output log prefix "AGISWARM_DROP: " limit rate 1/second

# NAT table (if needed for internet access)
nft add chain inet agiswarm_nat postrouting { type nat hook postrouting priority 100 \; }
nft add rule inet agiswarm_nat postrouting oifname eth0 masquerade
```

#### Security Hardening
```bash
# Disable IP forwarding by default
echo 0 | sudo tee /proc/sys/net/ipv4/ip_forward

# Enable reverse path filtering
echo 1 | sudo tee /proc/sys/net/ipv4/conf/all/rp_filter
echo 1 | sudo tee /proc/sys/net/ipv4/conf/default/rp_filter

# Disable ICMP redirects
echo 0 | sudo tee /proc/sys/net/ipv4/conf/all/accept_redirects
echo 0 | sudo tee /proc/sys/net/ipv4/conf/default/accept_redirects

# Disable source packet routing
echo 0 | sudo tee /proc/sys/net/ipv4/conf/all/accept_source_route
```

### Network Monitoring

#### Traffic Analysis
```bash
# Monitor AGISWARM traffic
sudo tcpdump -i veth_host -w agiswarm_traffic.pcap

# Analyze traffic in real-time
sudo tcpdump -i veth_host -n -v

# Monitor specific UDP port
sudo tcpdump -i any udp port 6000 -n
```

#### Intrusion Detection
```bash
# Setup fail2ban for AGISWARM
sudo tee /etc/fail2ban/jail.agiswarm << EOF
[agiswarm]
enabled = true
port = 6000
protocol = udp
filter = agisworm
logpath = /var/log/agiswarm.log
maxretry = 3
bantime = 3600
findtime = 600
EOF

# Create filter
sudo tee /etc/fail2ban/filter.d/agisworm.conf << EOF
[Definition]
failregex = .*AGISWARM.*IP.*<HOST>.*rejected
ignoreregex =
EOF

# Restart fail2ban
sudo systemctl restart fail2ban
```

---

## Network Troubleshooting

### Diagnostic Commands

#### Network Namespace Diagnostics
```bash
#!/bin/bash
# Comprehensive network diagnostics

echo "=== Network Namespace Status ==="
ip netns list

echo -e "\n=== Interface Status ==="
ip link show

echo -e "\n=== IP Address Assignment ==="
ip addr show

echo -e "\n=== Routing Table ==="
ip route show

echo -e "\n=== NFTables Rules ==="
sudo nft list ruleset

echo -e "\n=== Active Connections ==="
sudo ss -tulpn | grep -E "(6000|mesh)"
```

#### WiFi Diagnostics
```bash
#!/bin/bash
# WiFi specific diagnostics

echo "=== WiFi Interface Status ==="
iwconfig 2>/dev/null || echo "iwconfig not available"

echo -e "\n=== Available Wireless Networks ==="
sudo iwlist scan | grep -E "(ESSID|Quality|Encryption)"

echo -e "\n=== Mesh Network Status ==="
iw dev mesh0 mesh info 2>/dev/null || echo "Mesh interface not active"

echo -e "\n=== Signal Strength ==="
cat /proc/net/wireless | tail -n +3
```

### Common Issues and Solutions

#### Issue: Network Namespace Isolation Not Working

**Symptoms**:
- Traffic flows between management and control networks
- Firewall rules not taking effect
- Network isolation ineffective

**Diagnosis**:
```bash
# Check namespace isolation
sudo ip netns exec control_net ping 8.8.8.8
# Should fail if isolation is working

# Check firewall rules
sudo nft list ruleset

# Check interface placement
ip link show | grep -E "(control_net|veth|mesh)"
```

**Solution**:
```bash
# Recreate network namespace
sudo ip netns del control_net
sudo ./bridge/netns_setup.sh

# Verify isolation
sudo ip netns exec control_net ping -c 1 192.168.1.1
# Should return "Network is unreachable"
```

#### Issue: Mesh Network Not Forming

**Symptoms**:
- Workers cannot discover each other
- High latency between nodes
- Frequent disconnections

**Diagnosis**:
```bash
# Check mesh peer links
iw dev mesh0 mesh pe

# Check signal strength
iw dev mesh0 scan | grep -A 5 "EDGE_LATTICE_01"

# Check mesh parameters
iw dev mesh0 mesh param
```

**Solution**:
```bash
# Reset mesh interface
sudo ip link set mesh0 down
sudo iw dev mesh0 del
sudo iw dev wlan0 interface add mesh0 type mesh

# Reconfigure mesh
sudo iw dev mesh0 mesh join EDGE_LATTICE_01
sudo ip link set mesh0 up

# Check peer connections
iw dev mesh0 mesh pe
```

#### Issue: High Latency and Jitter

**Symptoms**:
- Control cycles exceed timing requirements
- High variance in message delivery times
- Real-time performance degradation

**Diagnosis**:
```bash
# Measure network latency
ping -c 100 192.168.100.2

# Check system load
top
htop

# Monitor CPU usage
sar -u 1 10

# Check interrupt load
cat /proc/interrupts | grep wlan
```

**Solution**:
```bash
# Optimize interrupt handling
echo 2 | sudo tee /proc/irq/*/smp_affinity

# Increase process priority
sudo nice -n -10 python3 worker/worker.py &

# Optimize network buffers
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728

# Disable power management
sudo ethtool -s wlan0 wol d
```

---

## Performance Optimization

### Network Performance Tuning

#### System-Level Optimizations
```bash
#!/bin/bash
# Optimize system for real-time networking

# Increase UDP buffer sizes
echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_default = 65536' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_default = 65536' | sudo tee -a /etc/sysctl.conf

# Optimize UDP packet processing
echo 'net.core.netdev_max_backlog = 5000' | sudo tee -a /etc/sysctl.conf
echo 'net.core.netdev_budget = 600' | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p

# Disable transparent huge pages (can cause latency)
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
```

#### Application-Level Optimizations
```python
# Optimize AGISWARM application settings
AGISWARM_CONFIG = {
    'network': {
        'udp_buffer_size': 8 * 1024 * 1024,  # 8MB
        'tcp_nodelay': True,
        'keep_alive': True,
        'so_broadcast': True,
    },
    'performance': {
        'use_epoll': True,  # Linux
        'use_kqueue': True,  # BSD/macOS
        'thread_pool_size': 4,
        'io_timeout': 0.1,  # 100ms
    }
}
```

### Latency Optimization

#### Real-Time Kernel Configuration
```bash
# Install real-time kernel (Ubuntu)
sudo apt install linux-rt-generic-hwe-20.04

# Configure CPU governor for performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Disable CPU idle states
echo 0 | sudo tee /sys/devices/system/cpu/cpu*/cpuidle/state*/disable

# Set process priorities
sudo nice -n -20 python3 aggregator/main_runner.py
sudo nice -n -10 python3 worker/worker.py
```

#### Network Latency Optimization
```bash
# Optimize interrupt processing
echo 'irqbalance=off' | sudo tee -a /etc/default/irqbalance

# Pin network interrupts to specific CPUs
echo 2 | sudo tee /proc/irq/*/smp_affinity_list

# Disable interrupt coalescing
sudo ethtool -C wlan0 adaptive-rx off adaptive-tx off rx-usecs 0 tx-usecs 0
```

### Bandwidth Optimization

#### Traffic Shaping
```bash
# Limit bandwidth to ensure fair sharing
sudo tc qdisc add dev mesh0 root handle 1: htb default 12
sudo tc class add dev mesh0 parent 1: classid 1:1 htb rate 50mbit
sudo tc class add dev mesh0 parent 1:1 classid 1:10 htb rate 30mbit ceil 50mbit
sudo tc class add dev mesh0 parent 1:1 classid 1:12 htb rate 20mbit ceil 50mbit
sudo tc filter add dev mesh0 protocol ip parent 1:0 prio 1 u32 match ip dport 6000 flowid 1:10
```

#### Quality of Service (QoS)
```bash
# Prioritize AGISWARM traffic
sudo tc qdisc add dev mesh0 root handle 1: htb
sudo tc class add dev mesh0 parent 1: classid 1:1 htb rate 100mbit
sudo tc class add dev mesh0 parent 1:1 classid 1:10 htb rate 80mbit ceil 100mbit prio 1
sudo tc class add dev mesh0 parent 1:1 classid 1:20 htb rate 20mbit ceil 100mbit prio 2

# Mark AGISWARM packets
sudo iptables -A OUTPUT -p udp --dport 6000 -j MARK --set-mark 1
sudo tc filter add dev mesh0 protocol ip parent 1:0 prio 1 handle 1 fw flowid 1:10
```

This comprehensive network configuration guide provides all the necessary information to deploy and optimize AGISWARM networks for various scenarios, from development testing to production deployments.