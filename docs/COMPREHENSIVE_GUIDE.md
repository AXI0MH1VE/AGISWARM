# AGISWARM - Comprehensive User Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [Installation Guide](#installation-guide)
4. [Quick Start Guide](#quick-start-guide)
5. [Detailed Component Documentation](#detailed-component-documentation)
6. [Network Configuration](#network-configuration)
7. [Use Cases and Scenarios](#use-cases-and-scenarios)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [API Reference](#api-reference)
10. [Advanced Configuration](#advanced-configuration)
11. [Security Considerations](#security-considerations)
12. [Performance Optimization](#performance-optimization)

---

## Project Overview

AGISWARM (Advanced Grid Infrastructure Swarm) is a **Secure, Real-Time Distributed Edge-Lattice Control Fabric** - a distributed deterministic control compute mesh that's robust to unreliable networks. It's designed for OpenWRT wireless routers and simulation on standard systems.

### Key Characteristics
- **Fixed Point Arithmetic**: Q1.31 saturating operations, no FPU/emulation required
- **Coded Computing**: Rateless block design (fountain-style) to tolerate dropped/slow workers
- **LLFT (Leader/Follower Fault Tolerance)**: Primary/Backup Leader with fast failover and strong message order
- **PoA (Proof-of-Authority)**: Every state commit requires Ed25519 signature
- **Zero-Bridge**: Mesh network air-gapped via kernel network namespaces, firewall, veth bridge

### Why Use AGISWARM?

**Problem**: Traditional distributed systems fail in unreliable network environments, especially in edge computing scenarios where:
- Network connectivity is intermittent
- Real-time deterministic behavior is required
- Security and isolation are critical
- Resource constraints exist (no FPU)

**Solution**: AGISWARM provides:
- ✅ Deterministic real-time control with fixed-point arithmetic
- ✅ Fault tolerance through coded computing and leader redundancy
- ✅ Security through cryptographic signatures and network isolation
- ✅ Resource efficiency through fixed-point operations
- ✅ Mesh networking capabilities for edge deployments

---

## Architecture Deep Dive

### System Architecture

```
         +-------------------+          (Air Gap: netns/veth)         +-------------------+
         |   Operator CLI    |<---------[Bridge Node]<===============>|   Aggregator LB   |
         +-------------------+             |                     /-\  +-------------------+
                  ^                         |                     | (Primary+Backup)
       CommitToken |                 +------+--+           Task/Result |
                  |                  |  veth  |        |      ^        |
                  |                  +---/----+        |      |        |
           Human-in-loop                   |           |      |        |
                 (Ed25519 PoA)             |      +----+---+--+--+-----+------+
                                 [802.11s Mesh]   |       |     |     |      |
                                                 (UDP/CBOR)|    |     |      |
                                                  |      (Worker Nodes x N)
                                                  |      [ID, Q1.31 only]
                                                 \|/
   +-------------+   +--------------+   +--------------+   +--------------+
   |  Worker 1   |   |  Worker 2    |...|  Worker N    |
   +-------------+   +--------------+   +--------------+
```

### Component Breakdown

#### 1. **Operator CLI**
- **Purpose**: Human-in-the-loop control interface
- **Responsibilities**:
  - Generate and manage Ed25519 keys
  - Sign state commits (PoA)
  - Monitor system status
  - Issue control commands
- **Technology**: Python CLI with Ed25519 cryptography

#### 2. **Aggregator Load Balancer**
- **Purpose**: Central coordination and task distribution
- **Responsibilities**:
  - Task distribution to workers
  - Result aggregation
  - Leader election and failover
  - Message ordering and consistency
- **Technology**: UDP/CBOR communication, Python asyncio

#### 3. **Worker Nodes**
- **Purpose**: Execute computational tasks
- **Responsibilities**:
  - Process assigned tasks
  - Return results to aggregator
  - Handle network interruptions gracefully
- **Technology**: Q1.31 fixed-point arithmetic, optional C implementation for OpenWRT

#### 4. **Bridge Node**
- **Purpose**: Network isolation and security
- **Responsibilities**:
  - Create network namespaces
  - Establish veth pairs
  - Configure firewall rules
  - Manage mesh networking
- **Technology**: Linux network namespaces, NFTables, 802.11s mesh

---

## Installation Guide

### Prerequisites

#### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+, CentOS 8+) or macOS
- **Python**: 3.8 or higher
- **Network**: WiFi capability for mesh networking
- **Privileges**: Root/sudo access for network namespace manipulation

#### Hardware Requirements
- **Minimum**: 2GB RAM, 1 CPU core
- **Recommended**: 4GB RAM, 2+ CPU cores
- **Network**: WiFi adapter supporting access point mode

### Installation Steps

#### 1. Clone Repository
```bash
git clone https://github.com/AXI0MH1VE/AGISWARM.git
cd AGISWARM
```

#### 2. Install Python Dependencies
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

#### 3. Install System Dependencies (Linux)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y iproute2 nftables wireless-tools

# CentOS/RHEL
sudo yum install -y iproute nftables wireless-tools
```

#### 4. Install System Dependencies (macOS)
```bash
# macOS typically has most tools pre-installed
# Ensure Xcode command line tools are installed
xcode-select --install
```

#### 5. Generate Cryptographic Keys
```bash
python operator/keygen.py
```

This creates:
- `operator/operator_private.key` - Private key for signing
- `operator/operator_public.key` - Public key for verification

**⚠️ CRITICAL**: Keep your private key secure and never commit it to version control!

---

## Quick Start Guide

### Scenario 1: Local Simulation (Single Machine)

This is the fastest way to test the system locally:

```bash
# 1. Start the simulation
./scripts/run_simulation.sh

# 2. In a new terminal, start the operator
source .venv/bin/activate
python operator/operator_cli.py
```

**Expected Output**:
- Simulation starts multiple worker processes
- Aggregator binds to UDP port 6000
- Operator connects and can issue commands
- Metrics are written to `metrics.csv`

### Scenario 2: Multi-Machine Deployment

For testing across multiple machines:

#### Machine 1 (Aggregator):
```bash
# Configure aggregator
python aggregator/main_runner.py
```

#### Machine 2+ (Workers):
```bash
# Configure worker
python worker/worker.py --aggregator-ip 192.168.1.100 --aggregator-port 6000
```

#### Operator Machine:
```bash
# Connect to aggregator
python operator/operator_cli.py --aggregator-ip 192.168.1.100
```

### Scenario 3: OpenWRT Router Deployment

For production deployment on OpenWRT routers:

```bash
# 1. Copy worker binary to router
scp worker/c_worker root@192.168.1.1:/usr/bin/

# 2. Configure mesh networking
ssh root@192.168.1.1
./bridge/openwrt_mesh_example.sh

# 3. Start worker
ssh root@192.168.1.1 "c_worker --mesh-id EDGE_LATTICE_01"
```

---

## Detailed Component Documentation

### Aggregator Component

**File**: `aggregator/aggregator.py`

#### Core Responsibilities
1. **Task Distribution**: Split computational tasks across worker pool
2. **Result Aggregation**: Collect and combine results using fountain codes
3. **Leader Election**: Maintain primary/backup leader hierarchy
4. **Message Ordering**: Ensure deterministic message processing

#### Key Classes and Methods

```python
class Aggregator:
    def __init__(self, config_path: str, matrix_path: str):
        """Initialize aggregator with configuration"""
        
    async def run_cycle(self):
        """Execute one control cycle"""
        
    def distribute_task(self, task: Task) -> List[Worker]:
        """Distribute task to workers using fountain coding"""
        
    def aggregate_results(self, results: List[Result]) -> Result:
        """Aggregate results using rateless decoding"""
```

#### Configuration Example
```yaml
# configs/app_config.yaml
aggregator:
  udp_port: 6000
  max_workers: 16
  cycle_time_ms: 100
  fault_tolerance: 2  # Number of redundant workers
  
leader:
  primary: true
  backup_aggregators:
    - 192.168.1.101
    - 192.168.1.102
```

### Worker Component

**File**: `worker/worker.py`

#### Core Responsibilities
1. **Task Execution**: Process tasks using Q1.31 arithmetic
2. **Result Reporting**: Send results back to aggregator
3. **Fault Detection**: Detect and report failures
4. **Resource Management**: Efficient CPU and memory usage

#### Key Classes and Methods

```python
class Worker:
    def __init__(self, worker_id: str, aggregator_addr: tuple):
        """Initialize worker with ID and aggregator address"""
        
    async def process_task(self, task: Task) -> Result:
        """Process task using Q1.31 fixed-point arithmetic"""
        
    def q1_31_multiply(self, a: Q1_31, b: Q1_31) -> Q1.31:
        """Perform Q1.31 multiplication with saturation"""
```

#### Worker Configuration
```bash
# Command line options
python worker/worker.py \
    --worker-id W001 \
    --aggregator-ip 192.168.1.100 \
    --aggregator-port 6000 \
    --mesh-interface wlan0 \
    --log-level INFO
```

### Operator Component

**File**: `operator/operator_cli.py`

#### Core Responsibilities
1. **Key Management**: Generate and manage Ed25519 keys
2. **Command Interface**: Human-in-the-loop control
3. **State Signing**: Cryptographically sign state commits
4. **System Monitoring**: Real-time status monitoring

#### Operator Commands

```bash
# Generate new keys
python operator/keygen.py --output ./keys/

# Connect to aggregator
python operator/operator_cli.py --aggregator 192.168.1.100:6000

# Interactive commands
> status                    # Show system status
> commit "state_data"      # Commit signed state
> workers list             # List active workers
> metrics last 100         # Show last 100 metrics
> fault inject worker W001 # Test fault tolerance
```

---

## Network Configuration

### Network Namespace Setup

**File**: `bridge/netns_setup.sh`

The system uses network namespaces to create isolated network environments:

```bash
#!/bin/bash
# Create isolated network namespace
NS="control_net"
PHY_IF="wlan1"

# Create namespace and move interface
ip netns add $NS
ip link set $PHY_IF netns $NS

# Create veth pair for communication
ip link add veth_host type veth peer name veth_ns
ip link set veth_ns netns $NS

# Configure IP addresses
ip addr add 192.168.100.1/24 dev veth_host
ip netns exec $NS ip addr add 192.168.100.2/24 dev veth_ns

# Apply firewall rules
nft add table inet filter
nft add chain inet filter input { type filter hook input priority 0 \; policy drop \; }
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input iifname "veth_host" udp dport 6000 accept
```

### WiFi Mesh Configuration

**File**: `bridge/openwrt_mesh_example.sh`

For OpenWRT deployments:

```bash
#!/bin/sh
# Configure 802.11s mesh networking

# Set mesh parameters
uci set wireless.radio0.channel='13'  # Non-overlapping channel
uci set wireless.default_radio0.mode='mesh'
uci set wireless.default_radio0.mesh_id='EDGE_LATTICE_01'
uci set wireless.default_radio0.encryption='sae'
uci set wireless.default_radio0.key='SuperSecureSecretKey'
uci set wireless.default_radio0.mesh_fwding='1'

# Apply configuration
uci commit wireless
wifi reload

# Install telemetry tools
opkg update
opkg install twamp-light
```

### WiFi Troubleshooting

If you experience WiFi connectivity issues after running the network setup:

#### Quick Fix (macOS):
```bash
chmod +x bridge/macos_wifi_fix.sh
./bridge/macos_wifi_fix.sh
```

#### Manual Fix (Linux):
```bash
# Check network namespaces
ip netns list

# Remove problematic namespace
sudo ip netns del control_net

# Restore WiFi interface
sudo ip link set wlan1 up
sudo systemctl restart NetworkManager
```

#### Manual Fix (macOS):
```bash
# Reset WiFi interface
sudo ifconfig en0 down
sudo ifconfig en0 up

# Restart WiFi service
networksetup -setairportpower en0 off
sleep 2
networksetup -setairportpower en0 on
```

---

## Use Cases and Scenarios

### Use Case 1: Industrial Control Systems

**Scenario**: Manufacturing plant with multiple CNC machines requiring real-time coordination.

**Problem**: 
- Machines need deterministic control cycles
- Network reliability is critical
- Latency must be < 10ms
- Safety requires cryptographic authentication

**AGISWARM Solution**:
```
CNC1 (Worker) ─┐
CNC2 (Worker) ─┼─ Mesh Network ─┐
CNC3 (Worker) ─┘                 ├─ Aggregator ─ Operator (Human Safety Override)
                                  │
                           Emergency Stop Button
```

**Benefits**:
- ✅ Deterministic Q1.31 arithmetic for precise control
- ✅ Fault tolerance through redundant workers
- ✅ Cryptographic PoA for safety-critical operations
- ✅ Mesh networking for robust connectivity

### Use Case 2: Smart Grid Control

**Scenario**: Electrical grid with distributed renewable energy sources and storage.

**Problem**:
- Distributed energy resources need coordination
- Network partitions can occur during storms
- Real-time balancing is required
- Security against tampering is essential

**AGISWARM Solution**:
```
Solar Farm 1 ──┐
Wind Farm 2   ─┼─ 802.11s Mesh ─┐
Battery Bank  ─┘                ├─ Grid Aggregator ─ Utility Operator
                                 │
                         Weather/Load Forecasting
```

**Benefits**:
- ✅ Graceful handling of network partitions
- ✅ Fixed-point arithmetic for precise power calculations
- ✅ Ed25519 signatures prevent unauthorized control
- ✅ Mesh networking adapts to changing topology

### Use Case 3: Autonomous Vehicle Coordination

**Scenario**: Fleet of delivery robots in a warehouse requiring coordination.

**Problem**:
- Robots need to avoid collisions
- Network can be congested
- Real-time path planning required
- Safety is paramount

**AGISWARM Solution**:
```
Robot 1 ──┐
Robot 2 ─┼─ WiFi Mesh ─┐
Robot 3 ─┘            ├─ Central Coordinator ─ Human Operator
                      │
                 Collision Avoidance System
```

**Benefits**:
- ✅ Fast failover if robots lose connectivity
- ✅ Coded computing tolerates slow/lost robots
- ✅ Fixed-point arithmetic for precise navigation
- ✅ Cryptographic authentication prevents hijacking

### Use Case 4: Edge Computing in Smart Cities

**Scenario**: Traffic light coordination across a city.

**Problem**:
- Hundreds of intersections need coordination
- Network infrastructure varies by neighborhood
- Emergency vehicles need priority
- Vandalism resistance required

**AGISWARM Solution**:
```
Intersection 1 ──┐
Intersection 2   ─┼─ Mixed WiFi/Cellular ─┐
Intersection N   ─┘                       ├─ City Traffic Center
                                          │
                                   Emergency Vehicle Detection
```

**Benefits**:
- ✅ Works with mixed network infrastructure
- ✅ Graceful degradation during network issues
- ✅ PoA prevents unauthorized traffic control
- ✅ Fixed-point arithmetic ensures precise timing

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: "WiFi Interface Not Found"

**Symptoms**:
- Network setup scripts fail
- `ip link show` doesn't show WiFi interface
- `networksetup -getairportpower en0` returns errors

**Solutions**:

**Linux**:
```bash
# Check available interfaces
ip link show

# Common WiFi interface names
# wlan0, wlan1, wlpx0, etc.

# Update scripts with correct interface name
sed -i 's/wlan0/YOUR_INTERFACE_NAME/g' bridge/netns_setup.sh
```

**macOS**:
```bash
# List all network interfaces
ifconfig | grep -E "^[a-z]"

# Common macOS WiFi interface names
# en0, en1, etc.

# Run macOS fix script
./bridge/macos_wifi_fix.sh
```

#### Issue 2: "Permission Denied" Errors

**Symptoms**:
- Network namespace operations fail
- Firewall configuration fails
- "Operation not permitted" errors

**Solutions**:
```bash
# Run scripts with sudo
sudo ./bridge/netns_setup.sh

# Or run interactive shell as root
sudo su -
./bridge/netns_setup.sh
exit

# Check if user is in required groups (Linux)
groups $USER
# Should include: netdev, wheel, or sudo
```

#### Issue 3: "Aggregator Connection Refused"

**Symptoms**:
- Workers cannot connect to aggregator
- Operator shows "connection refused"
- UDP port 6000 not responding

**Solutions**:
```bash
# Check if aggregator is running
netstat -ulpn | grep 6000
# or
ss -ulpn | grep 6000

# Start aggregator if not running
python aggregator/main_runner.py

# Check firewall rules
sudo iptables -L -n
sudo nft list ruleset

# Verify aggregator configuration
cat configs/app_config.yaml
```

#### Issue 4: "Key Generation Fails"

**Symptoms**:
- `python operator/keygen.py` fails
- "Permission denied" or "File exists" errors
- Cryptographic library errors

**Solutions**:
```bash
# Install cryptography library
pip install cryptography

# Check Python version
python --version  # Should be 3.8+

# Generate keys in clean directory
mkdir -p ~/keys
python operator/keygen.py --output ~/keys

# Check file permissions
ls -la operator/
```

#### Issue 5: "High Latency or Jitter"

**Symptoms**:
- Control cycles exceed timing requirements
- Metrics show high jitter values
- Real-time performance is degraded

**Solutions**:
```bash
# Check system load
top
htop

# Optimize network settings
echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Reduce process priority for workers
nice -n -10 python worker/worker.py

# Check WiFi signal strength
iwconfig
```

### Diagnostic Commands

#### System Status Check
```bash
#!/bin/bash
echo "=== AGISWARM System Diagnostics ==="

echo "System Information:"
uname -a
python --version

echo -e "\nNetwork Status:"
ip addr show | grep -E "(inet|flags)"
netstat -ulpn 2>/dev/null | grep 6000 || echo "Port 6000 not in use"

echo -e "\nProcess Status:"
ps aux | grep -E "(aggregator|worker|operator)" | grep -v grep

echo -e "\nWiFi Status:"
ifconfig | grep -E "^[a-z]" | head -5
```

#### Network Namespace Check
```bash
#!/bin/bash
echo "=== Network Namespace Status ==="

echo "Active namespaces:"
ip netns list

echo -e "\nInterfaces in main namespace:"
ip link show | grep -E "^[0-9]"

echo -e "\nNFTables rules:"
nft list ruleset 2>/dev/null || echo "NFTables not configured"

echo -e "\nVeth pairs:"
ip link show type veth 2>/dev/null || echo "No veth pairs found"
```

---

## API Reference

### Aggregator API

#### UDP Message Format
All messages use CBOR (Concise Binary Object Representation) encoding.

**Task Distribution Message**:
```json
{
    "type": "task",
    "task_id": "unique_task_identifier",
    "worker_id": "target_worker_id",
    "data": {
        "operation": "multiply_matrix",
        "matrix_a": [[1,2],[3,4]],
        "matrix_b": [[5,6],[7,8]]
    },
    "timestamp": 1640995200.123
}
```

**Result Message**:
```json
{
    "type": "result",
    "task_id": "unique_task_identifier",
    "worker_id": "worker_id",
    "result": [[19,22],[43,50]],
    "signature": "base64_encoded_ed25519_signature",
    "timestamp": 1640995200.456
}
```

#### Python API

```python
from aggregator.aggregator import Aggregator
import asyncio

# Initialize aggregator
agg = Aggregator("configs/app_config.yaml", "configs/example_matrix.json")

# Start aggregator
async def start_aggregator():
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: agg, 
        local_addr=('127.0.0.1', 6000)
    )
    
    # Run control cycles
    while True:
        await agg.run_cycle()
        await asyncio.sleep(0.1)  # 10Hz control frequency

# Run aggregator
asyncio.run(start_aggregator())
```

### Worker API

#### Command Line Interface

```bash
python worker/worker.py [OPTIONS]

Options:
    --worker-id WORKER_ID          Unique worker identifier
    --aggregator-ip IP            Aggregator IP address
    --aggregator-port PORT        Aggregator UDP port (default: 6000)
    --mesh-interface INTERFACE    WiFi interface for mesh networking
    --log-level LEVEL             Log level (DEBUG, INFO, WARNING, ERROR)
    --help                        Show this message and exit.
```

#### Python API

```python
from worker.worker import Worker

# Initialize worker
worker = Worker(
    worker_id="W001",
    aggregator_addr=("192.168.1.100", 6000)
)

# Start worker
async def start_worker():
    await worker.connect()
    await worker.run()

# Run worker
asyncio.run(start_worker())
```

### Operator API

#### Key Management

```bash
# Generate new key pair
python operator/keygen.py --output ./keys/

# Output files:
# ./keys/operator_private.key    - Private key (keep secret!)
# ./keys/operator_public.key     - Public key (can be shared)
```

#### Command Interface

```python
from operator.operator_cli import Operator

# Initialize operator
op = Operator(
    aggregator_addr=("192.168.1.100", 6000),
    private_key_path="./keys/operator_private.key"
)

# Connect and issue commands
async def operator_session():
    await op.connect()
    
    # Check system status
    status = await op.get_status()
    print(f"Active workers: {status['worker_count']}")
    
    # Commit signed state
    await op.commit_state("control_state_data")
    
    # Monitor metrics
    async for metric in op.stream_metrics():
        print(f"Latency: {metric['latency_ms']}ms")

# Run operator
asyncio.run(operator_session())
```

---

## Advanced Configuration

### Performance Tuning

#### Optimizing Control Cycle Timing

**File**: `configs/app_config.yaml`
```yaml
aggregator:
  cycle_time_ms: 50        # 20Hz control frequency
  max_workers: 32          # Scale with available CPU cores
  timeout_ms: 40           # Worker timeout (80% of cycle time)
  
optimization:
  use_fountain_codes: true # Enable coded computing
  redundancy_factor: 2     # Number of redundant workers
  batch_size: 8            # Tasks per cycle
```

#### Memory Optimization

```python
# For memory-constrained environments (OpenWRT routers)
# File: worker/worker.py

class Worker:
    def __init__(self, memory_limit_mb: int = 64):
        """Initialize worker with memory constraints"""
        self.memory_limit = memory_limit_mb * 1024 * 1024
        
    async def process_task(self, task: Task) -> Result:
        """Process task with memory monitoring"""
        if self.get_memory_usage() > self.memory_limit:
            await self.cleanup_old_results()
        return await self.compute_result(task)
```

### Security Hardening

#### Network Isolation

```bash
# Enhanced firewall rules for production
#!/bin/bash

# Drop all traffic by default
nft add table inet agiswarm
nft add chain inet agiswarm input { type filter hook input priority 0 \; policy drop \; }
nft add chain inet agiswarm output { type filter hook output priority 0 \; policy drop \; }

# Allow only specific traffic
nft add rule inet agiswarm input ct state established,related accept
nft add rule inet agiswarm input iifname "veth_host" udp dport 6000 accept
nft add rule inet agiswarm input iifname "lo" accept

# Log dropped packets
nft add rule inet agiswarm input log prefix "AGISWARM_DROP: "
```

#### Cryptographic Configuration

```yaml
# Enhanced security configuration
security:
  signature_algorithm: "Ed25519"
  key_rotation_interval_hours: 24
  require_signature_verification: true
  allowed_operators:
    - "operator_public_key_hash_1"
    - "operator_public_key_hash_2"
  
  network_isolation:
    enable_firewall: true
    allowed_ports: [6000]
    allowed_interfaces: ["veth_host"]
```

### Multi-Aggregator Configuration

For high availability, configure multiple aggregators:

```yaml
# configs/ha_config.yaml
aggregators:
  primary:
    ip: "192.168.1.100"
    port: 6000
    priority: 1
    
  backup_1:
    ip: "192.168.1.101"
    port: 6000
    priority: 2
    
  backup_2:
    ip: "192.168.1.102"
    port: 6000
    priority: 3

failover:
  heartbeat_interval_ms: 1000
  failure_threshold: 3
  auto_promotion: true
```

---

## Security Considerations

### Threat Model

#### Identified Threats
1. **Network Eavesdropping**: Attackers monitoring mesh traffic
2. **Man-in-the-Middle**: Attackers intercepting and modifying messages
3. **Unauthorized Control**: Attackers issuing malicious commands
4. **Denial of Service**: Attackers overwhelming the system
5. **Key Compromise**: Private keys being stolen or leaked

#### Defense Mechanisms

1. **Network Isolation**:
   - Network namespaces create air gaps
   - NFTables firewall restricts traffic
   - Only specific UDP ports are accessible

2. **Cryptographic Authentication**:
   - Ed25519 signatures on all state commits
   - Public key infrastructure for operators
   - Message integrity verification

3. **Access Control**:
   - Only authorized operators can commit states
   - Worker authentication via shared secrets
   - Role-based permissions

### Security Best Practices

#### Key Management
```bash
# Generate keys offline on secure system
python operator/keygen.py --output /secure/location/

# Store private keys in hardware security modules when possible
# Use separate keys for different environments (dev/staging/prod)

# Implement key rotation
python operator/keygen.py --rotate --current-key ./current_private.key

# Backup encrypted private keys
gpg --symmetric --cipher-algo AES256 operator_private.key
```

#### Network Security
```bash
# Monitor network traffic
tcpdump -i veth_host -w agiswarm_traffic.pcap

# Check firewall rules regularly
nft list ruleset > firewall_rules.txt
diff firewall_rules.txt previous_rules.txt

# Monitor for unauthorized access
tail -f /var/log/kern.log | grep AGISWARM
```

#### System Hardening
```bash
# Disable unnecessary services
systemctl disable bluetooth
systemctl disable avahi-daemon

# Enable automatic security updates
echo 'Unattended-Upgrade::Automatic-Reboot-Time "02:00";' >> /etc/apt/apt.conf.d/50unattended-upgrades

# Monitor system integrity
aide --init
cron0 5 * * * /usr/bin/aide --check
```

---

## Performance Optimization

### Benchmarking and Monitoring

#### Metrics Collection

The system automatically collects performance metrics:

```python
# View collected metrics
cat metrics.csv

# Sample metrics output:
timestamp,cycle_id,latency_ms,jitter_ms,worker_count,task_count,error_rate
1640995200.123,1,12.3,1.2,8,16,0.0
1640995200.223,2,11.8,0.9,8,16,0.0
1640995200.323,3,15.1,2.1,7,14,0.05
```

#### Performance Analysis

```bash
# Analyze latency trends
python scripts/analyze_metrics.py metrics.csv --plot latency

# Identify performance bottlenecks
python scripts/profile_system.py

# Test network throughput
python scripts/network_benchmark.py --duration 300
```

### Optimization Strategies

#### 1. Fixed-Point Arithmetic Optimization

```python
# Use lookup tables for common operations
class OptimizedQ1_31:
    def __init__(self):
        # Pre-compute multiplication table for common values
        self.mul_table = self._build_multiplication_table()
    
    def multiply(self, a: Q1_31, b: Q1_31) -> Q1_31:
        # Use lookup table for faster multiplication
        index = (a.value << 8) | (b.value & 0xFF)
        return self.mul_table.get(index, a.value * b.value)
```

#### 2. Network Optimization

```python
# Optimize UDP buffer sizes
import socket

# Set optimal buffer sizes
socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)
socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8 * 1024 * 1024)

# Enable packet timestamping for precise latency measurement
socket.setsockopt(socket.SOL_SOCKET, socket.SO_TIMESTAMPING, 
                  socket.SOF_TIMESTAMPING_RX_SOFTWARE |
                  socket.SOF_TIMESTAMPING_RAW_HARDWARE)
```

#### 3. CPU Optimization

```bash
# Set CPU governor to performance mode
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Pin processes to specific CPU cores
taskset -c 0,1 python aggregator/main_runner.py
taskset -c 2,3 python worker/worker.py --worker-id W001

# Reduce system interrupts
echo 2 > /proc/sys/kernel/timer_migration
```

### Scalability Considerations

#### Horizontal Scaling

```yaml
# Scale workers based on load
scaling:
  min_workers: 4
  max_workers: 64
  scale_up_threshold: 80.0  # CPU utilization %
  scale_down_threshold: 20.0
  scale_check_interval_sec: 30
```

#### Load Balancing

```python
# Implement intelligent task distribution
class LoadBalancedAggregator(Aggregator):
    def distribute_task(self, task: Task) -> List[Worker]:
        # Distribute based on worker load and capabilities
        available_workers = self.get_healthy_workers()
        selected_workers = self.select_workers_by_load(available_workers)
        
        # Consider network latency
        workers_by_latency = self.sort_by_latency(selected_workers)
        
        return workers_by_latency[:self.redundancy_factor]
```

---

This comprehensive guide covers all aspects of the AGISWARM system. Each section provides detailed explanations, code examples, and practical solutions for real-world deployment scenarios.

For additional support or questions not covered in this guide, please refer to the project repository or contact the development team.