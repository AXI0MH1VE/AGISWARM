# AGISWARM Troubleshooting Guide

## Table of Contents
1. [Diagnostic Tools](#diagnostic-tools)
2. [Common Issues](#common-issues)
3. [Installation Problems](#installation-problems)
4. [Network Issues](#network-issues)
5. [Performance Problems](#performance-problems)
6. [Security Issues](#security-issues)
7. [System-Specific Problems](#system-specific-problems)
8. [Debug Mode and Logging](#debug-mode-and-logging)
9. [Recovery Procedures](#recovery-procedures)

---

## Diagnostic Tools

### System Diagnostics Script

Create a comprehensive diagnostic script to identify issues:

```bash
#!/bin/bash
# AGISWARM Diagnostic Tool
# Usage: ./diagnose_agiswarm.sh

echo "=================================================="
echo "         AGISWARM System Diagnostics"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. System Information
echo -e "\n📋 SYSTEM INFORMATION"
echo "======================="
echo "OS: $(uname -a)"
echo "Python Version: $(python3 --version 2>&1 || echo 'Not found')"
echo "User: $(whoami)"
echo "Date: $(date)"

# 2. Python Environment
echo -e "\n🐍 PYTHON ENVIRONMENT"
echo "======================"
python3 -c "
import sys
import pkg_resources
required_packages = ['asyncio', 'cborg', 'cryptography', 'pynacl']
missing_packages = []
for package in required_packages:
    try:
        pkg_resources.get_distribution(package)
        print(f'✅ {package} installed')
    except pkg_resources.DistributionNotFound:
        print(f'❌ {package} missing')
        missing_packages.append(package)
if missing_packages:
    print(f'\nMissing packages: {missing_packages}')
" 2>/dev/null

# 3. Network Interfaces
echo -e "\n🌐 NETWORK INTERFACES"
echo "======================"
if command -v ip >/dev/null 2>&1; then
    ip link show | grep -E "^[0-9]+" | while read line; do
        echo "📡 $line"
    done
elif command -v ifconfig >/dev/null 2>&1; then
    ifconfig | grep -E "^[a-z]" | while read line; do
        interface=$(echo $line | cut -d: -f1)
        ifconfig $interface | grep -E "(flags|inet)" | while read subline; do
            echo "📡 $subline"
        done
    done
else
    echo "❌ Network tools not available"
fi

# 4. WiFi Status
echo -e "\n📶 WIFI STATUS"
echo "=============="
if command -v iwconfig >/dev/null 2>&1; then
    iwconfig 2>/dev/null | grep -E "(wlan|wireless|ESSID)" || echo "No WiFi interfaces found"
elif command -v networksetup >/dev/null 2>&1; then
    networksetup -listallhardwareports | grep -A 2 "Wi-Fi" || echo "WiFi not configured"
else
    echo "❌ WiFi tools not available"
fi

# 5. Network Namespace
echo -e "\n🔒 NETWORK NAMESPACES"
echo "======================"
if command -v ip >/dev/null 2>&1; then
    ip netns list 2>/dev/null || echo "Network namespace support not available"
else
    echo "❌ Network namespace tools not available"
fi

# 6. Firewall Status
echo -e "\n🔥 FIREWALL STATUS"
echo "==================="
if command -v nft >/dev/null 2>&1; then
    sudo nft list ruleset 2>/dev/null | head -10 || echo "No NFTables rules"
elif command -v iptables >/dev/null 2>&1; then
    sudo iptables -L 2>/dev/null | head -10 || echo "No iptables rules"
else
    echo "❌ Firewall tools not available"
fi

# 7. Process Status
echo -e "\n⚙️  AGISWARM PROCESSES"
echo "========================"
ps aux | grep -E "(aggregator|worker|operator)" | grep -v grep || echo "No AGISWARM processes running"

# 8. Port Status
echo -e "\n🔌 PORT STATUS"
echo "==============="
if command -v netstat >/dev/null 2>&1; then
    netstat -ulpn 2>/dev/null | grep 6000 || echo "Port 6000 not in use"
elif command -v ss >/dev/null 2>&1; then
    ss -ulpn 2>/dev/null | grep 6000 || echo "Port 6000 not in use"
else
    echo "❌ Network monitoring tools not available"
fi

# 9. Disk Space
echo -e "\n💾 DISK SPACE"
echo "=============="
df -h | grep -E "(/$|/home)" || df -h | head -3

# 10. Memory Usage
echo -e "\n🧠 MEMORY USAGE"
echo "==============="
free -h 2>/dev/null || echo "Memory information not available"

# 11. Load Average
echo -e "\n⚡ SYSTEM LOAD"
echo "==============="
uptime || echo "Load information not available"

echo -e "\n=================================================="
echo "           Diagnostics Complete"
echo "=================================================="
```

### Real-Time Monitoring

#### Network Traffic Monitor
```bash
#!/bin/bash
# Real-time AGISWARM network monitoring

INTERFACE="veth_host"
PORT="6000"
LOG_FILE="/var/log/agiswarm-monitor.log"

echo "Monitoring AGISWARM traffic on $INTERFACE:$PORT"
echo "Log file: $LOG_FILE"
echo "Press Ctrl+C to stop"

# Monitor UDP traffic
sudo tcpdump -i $INTERFACE -n udp port $PORT -tttt >> $LOG_FILE &
TCPDUMP_PID=$!

# Monitor interface statistics
watch -n 1 "ifconfig $INTERFACE | grep -E '(RX|TX) packets'" &
WATCH_PID=$!

# Cleanup on exit
trap "kill $TCPDUMP_PID $WATCH_PID; exit" INT
wait
```

#### System Resource Monitor
```bash
#!/bin/bash
# Monitor AGISWARM system resources

echo "=== AGISWARM Resource Monitor ==="
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "=== $(date) ==="
    echo ""
    
    echo "CPU Usage:"
    top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | awk '{printf "CPU: %.1f%%\n", 100-$1}'
    
    echo ""
    echo "Memory Usage:"
    free | grep Mem | awk '{printf "RAM: %.1f%%\n", $3/$2 * 100.0}'
    
    echo ""
    echo "Network Statistics:"
    ifconfig veth_host | grep -E "(RX|TX) packets" | head -2
    
    echo ""
    echo "AGISWARM Processes:"
    ps aux | grep -E "(aggregator|worker|operator)" | grep -v grep | awk '{printf "PID: %s, CPU: %s, MEM: %s, CMD: %s\n", $2, $3, $4, $11}'
    
    sleep 5
done
```

---

## Common Issues

### Quick Issue Resolution Matrix

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| WiFi not working | Network namespace isolation | Run `./bridge/macos_wifi_fix.sh` |
| Import errors | Missing dependencies | `pip install -r requirements.txt` |
| Permission denied | Need sudo for network ops | Use `sudo` for network scripts |
| Port already in use | Aggregator already running | `pkill -f aggregator/main_runner.py` |
| High latency | System load too high | Check `top`, reduce worker count |
| Key generation fails | Cryptography not installed | `pip install cryptography pynacl` |
| Tests fail | Python version mismatch | Ensure Python 3.8+ |

### Issue Classification

#### Critical Issues (System Down)
- Complete system failure
- No network connectivity
- Core components won't start

#### Major Issues (Reduced Functionality)
- Performance degradation
- Partial network isolation
- Some components failing

#### Minor Issues (Warning Messages)
- Non-critical errors
- Performance warnings
- Configuration issues

---

## Installation Problems

### Issue: Python Version Conflicts

**Symptoms**:
```
python: command not found
pip: command not found
ImportError: No module named 'asyncio'
```

**Diagnosis**:
```bash
# Check Python installation
which python3
python3 --version

# Check available Python versions
ls /usr/bin/python*

# Check pip installation
which pip3
pip3 --version
```

**Solutions**:

1. **Install Python 3.8+**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.8 python3.8-venv python3.8-dev python3-pip

# CentOS/RHEL
sudo yum install -y python38 python38-devel python38-pip

# macOS
brew install python@3.8
```

2. **Create Virtual Environment**:
```bash
# Use specific Python version
python3.8 -m venv .venv
source .venv/bin/activate

# Verify virtual environment
which python
python --version
```

3. **Fix PATH Issues**:
```bash
# Add Python to PATH (if needed)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Issue: Permission Denied Errors

**Symptoms**:
```
Permission denied: '/dev/net/tun'
Operation not permitted
Cannot open netlink socket
```

**Diagnosis**:
```bash
# Check user permissions
groups $USER

# Check if running as root (should not be for normal operations)
whoami

# Check file permissions
ls -la bridge/netns_setup.sh
```

**Solutions**:

1. **Make Scripts Executable**:
```bash
chmod +x bridge/*.sh
chmod +x scripts/*.sh
```

2. **Run Network Operations with Sudo**:
```bash
sudo ./bridge/netns_setup.sh
sudo ./bridge/openwrt_mesh_example.sh
```

3. **Add User to Required Groups**:
```bash
# Linux
sudo usermod -a -G netdev,networking,sudo $USER

# Log out and back in for group changes to take effect
```

### Issue: Dependency Installation Failures

**Symptoms**:
```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
Failed building wheel for cryptography
ModuleNotFoundError: No module named 'setuptools'
```

**Diagnosis**:
```bash
# Check pip version
pip --version

# Check virtual environment
which pip
echo $VIRTUAL_ENV

# Check system packages
pip list
```

**Solutions**:

1. **Upgrade pip and setuptools**:
```bash
pip install --upgrade pip setuptools wheel
```

2. **Install build dependencies**:
```bash
# Ubuntu/Debian
sudo apt install -y build-essential python3-dev libssl-dev libffi-dev

# CentOS/RHEL
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python38-devel openssl-devel libffi-devel

# macOS
xcode-select --install
```

3. **Use Virtual Environment**:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Network Issues

### Issue: WiFi Interface Not Found

**Symptoms**:
```
iwconfig: command not found
No wireless interfaces found
Interface wlan0 does not exist
```

**Diagnosis**:
```bash
# Check available network interfaces
ip link show
ifconfig

# Check for WiFi tools
which iwconfig
which iw

# List wireless interfaces
iw dev
```

**Solutions**:

1. **Install WiFi Tools**:
```bash
# Ubuntu/Debian
sudo apt install -y wireless-tools iw

# CentOS/RHEL
sudo yum install -y wireless-tools

# macOS
# WiFi tools are usually pre-installed
```

2. **Identify Correct Interface**:
```bash
# Common WiFi interface names:
# Linux: wlan0, wlan1, wlpx0, etc.
# macOS: en0, en1, etc.

# Update scripts with correct interface name
sed -i 's/wlan0/YOUR_INTERFACE_NAME/g' bridge/netns_setup.sh
```

3. **Enable WiFi Interface**:
```bash
# Linux
sudo ip link set wlan0 up

# macOS
sudo ifconfig en0 up
```

### Issue: Network Namespace Isolation Problems

**Symptoms**:
```
Cannot find device 'veth_h'
RTNETLINK answers: File exists
Cannot open network namespace
```

**Diagnosis**:
```bash
# Check existing namespaces
ip netns list

# Check existing interfaces
ip link show | grep veth

# Check NFTables rules
sudo nft list ruleset
```

**Solutions**:

1. **Clean Up Existing Setup**:
```bash
# Remove existing namespace
sudo ip netns del control_net 2>/dev/null || true

# Remove existing veth pairs
sudo ip link delete veth_h 2>/dev/null || true

# Clear NFTables rules
sudo nft delete table inet filter 2>/dev/null || true
```

2. **Recreate Network Setup**:
```bash
sudo ./bridge/cleanup_network.sh
sudo ./bridge/netns_setup.sh
```

3. **Check System Support**:
```bash
# Verify network namespace support
ls -la /proc/self/ns/net

# Verify veth support
sudo ip link add test_veth type veth peer name test_veth_peer
sudo ip link delete test_veth
```

### Issue: Mesh Network Formation Failures

**Symptoms**:
```
mesh join failed: Operation not supported
Cannot find mesh interface
Mesh peer link not established
```

**Diagnosis**:
```bash
# Check WiFi adapter mesh support
iw list | grep -i mesh

# Check mesh interface status
iw dev mesh0 mesh info

# Check mesh peer links
iw dev mesh0 mesh pe
```

**Solutions**:

1. **Verify Mesh Support**:
```bash
# Check if adapter supports mesh
iw list | grep -A 5 "mesh point"

# If not supported, consider:
# - Using different WiFi adapter
# - Using ad-hoc mode instead
# - Using Ethernet backhaul
```

2. **Reset Mesh Interface**:
```bash
# Remove and recreate mesh interface
sudo ip link set mesh0 down
sudo iw dev mesh0 del
sudo iw dev wlan0 interface add mesh0 type mesh

# Reconfigure mesh
sudo iw dev mesh0 mesh join EDGE_LATTICE_01
sudo ip link set mesh0 up
```

3. **Alternative Mesh Configuration**:
```bash
# Use ad-hoc mode as alternative
sudo iw dev wlan0 set type ibss
sudo iw dev wlan0 ibss join EDGE_LATTICE_01 2432
```

---

## Performance Problems

### Issue: High Latency and Jitter

**Symptoms**:
```
Control cycle exceeds timing requirements
High variance in message delivery
Real-time performance degradation
```

**Diagnosis**:
```bash
# Measure network latency
ping -c 100 192.168.100.2

# Check system load
top
htop

# Monitor interrupt load
cat /proc/interrupts | grep wlan

# Check CPU frequency scaling
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

**Solutions**:

1. **Optimize System Performance**:
```bash
# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Disable CPU idle states
echo 0 | sudo tee /sys/devices/system/cpu/cpu*/cpuidle/state*/disable

# Increase process priority
sudo nice -n -20 python3 aggregator/main_runner.py &
sudo nice -n -10 python3 worker/worker.py &
```

2. **Optimize Network Performance**:
```bash
# Increase UDP buffer sizes
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728

# Optimize interrupt handling
echo 2 | sudo tee /proc/irq/*/smp_affinity_list

# Disable interrupt coalescing
sudo ethtool -C wlan0 adaptive-rx off adaptive-tx off rx-usecs 0 tx-usecs 0
```

3. **Reduce System Load**:
```bash
# Kill unnecessary processes
sudo systemctl stop bluetooth
sudo systemctl stop avahi-daemon

# Disable services
sudo systemctl disable cups
sudo systemctl disable cups-browsed
```

### Issue: Memory Leaks and High Memory Usage

**Symptoms**:
```
Out of memory errors
System becomes unresponsive
High memory usage over time
```

**Diagnosis**:
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Monitor memory usage over time
watch -n 1 'free -h'

# Check for memory leaks in Python
python3 -m memory_profiler aggregator/main_runner.py
```

**Solutions**:

1. **Optimize Worker Configuration**:
```python
# Limit worker memory usage
class Worker:
    def __init__(self, memory_limit_mb: int = 64):
        self.memory_limit = memory_limit_mb * 1024 * 1024
        self.result_cache_size = 100  # Limit cached results
    
    async def process_task(self, task: Task):
        # Clear old results if memory usage high
        if self.get_memory_usage() > self.memory_limit * 0.8:
            await self.clear_old_results()
        return await self.compute_result(task)
```

2. **Configure Garbage Collection**:
```python
import gc

# Configure garbage collection for better performance
gc.set_threshold(700, 10, 10)  # More frequent collection
gc.enable()
```

3. **Monitor and Restart Services**:
```bash
# Create service restart script
cat > restart_agiswarm.sh << 'EOF'
#!/bin/bash
# Restart AGISWARM services if memory usage is too high

MEMORY_THRESHOLD=80  # Percentage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')

if [ "$MEMORY_USAGE" -gt "$MEMORY_THRESHOLD" ]; then
    echo "High memory usage detected: ${MEMORY_USAGE}%"
    echo "Restarting AGISWARM services..."
    
    # Restart services
    pkill -f "aggregator/main_runner.py"
    pkill -f "worker/worker.py"
    
    sleep 5
    
    # Restart services
    python3 aggregator/main_runner.py &
    python3 worker/worker.py --worker-id W001 &
    
    echo "Services restarted"
fi
EOF

chmod +x restart_agiswarm.sh

# Add to crontab for regular checks
echo "*/10 * * * * /path/to/restart_agiswarm.sh" | crontab -
```

---

## Security Issues

### Issue: Cryptographic Key Problems

**Symptoms**:
```
ImportError: No module named 'cryptography'
Ed25519 signature verification failed
Key generation produces invalid keys
```

**Diagnosis**:
```bash
# Check cryptography installation
python3 -c "import cryptography; print('Cryptography version:', cryptography.__version__)"

# Check key files
ls -la operator/operator_*.key

# Test key generation
python3 operator/keygen.py --test
```

**Solutions**:

1. **Install Cryptographic Libraries**:
```bash
pip install cryptography pynacl

# Install development headers if needed
sudo apt install -y libssl-dev libffi-dev python3-dev
```

2. **Verify Key Integrity**:
```bash
# Check key file permissions
chmod 600 operator/operator_private.key
chmod 644 operator/operator_public.key

# Regenerate keys if corrupted
python3 operator/keygen.py --force
```

3. **Test Cryptographic Functions**:
```python
# Test script
python3 -c "
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import os

# Generate test key pair
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Test signing and verification
message = b'test message'
signature = private_key.sign(message)
public_key.verify(signature, message)

print('✅ Cryptographic functions working correctly')
"
```

### Issue: Firewall and Access Control Problems

**Symptoms**:
```
Connection refused by firewall
NFTables rules not taking effect
Unauthorized access attempts
```

**Diagnosis**:
```bash
# Check current firewall rules
sudo nft list ruleset

# Check firewall service status
sudo systemctl status nftables

# Monitor firewall logs
sudo journalctl -u nftables -f
```

**Solutions**:

1. **Reset Firewall Rules**:
```bash
# Clear all rules
sudo nft flush ruleset

# Apply AGISWARM rules
sudo ./bridge/netns_setup.sh

# Verify rules
sudo nft list ruleset
```

2. **Fix Firewall Service**:
```bash
# Enable and start NFTables
sudo systemctl enable nftables
sudo systemctl start nftables

# Check service status
sudo systemctl status nftables
```

3. **Configure Log Monitoring**:
```bash
# Setup fail2ban for AGISWARM
sudo apt install fail2ban

# Configure AGISWARM jail
sudo tee /etc/fail2ban/jail.agiswarm << EOF
[agiswarm]
enabled = true
port = 6000
protocol = udp
filter = agisworm
logpath = /var/log/agiswarm.log
maxretry = 3
bantime = 3600
EOF

sudo systemctl restart fail2ban
```

---

## System-Specific Problems

### Linux-Specific Issues

#### Issue: Network Namespace Not Supported

**Symptoms**:
```
Cannot open network namespace: Function not implemented
RTNETLINK answers: Operation not supported
```

**Solution**:
```bash
# Check kernel support
grep CONFIG_NET_NS /boot/config-$(uname -r)

# Load network namespace module
sudo modprobe netns

# Or install necessary kernel modules
sudo apt install -y linux-image-extra-$(uname -r)
```

#### Issue: NFTables Not Available

**Symptoms**:
```
nft: command not found
Failed to apply firewall rules
NFTables support not found
```

**Solution**:
```bash
# Install NFTables
sudo apt install -y nftables

# Enable NFTables
sudo systemctl enable nftables
sudo systemctl start nftables

# Fallback to iptables if needed
sudo apt install -y iptables
sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
```

### macOS-Specific Issues

#### Issue: Network Namespace Not Available

**Symptoms**:
```
ip: command not found
Network namespace operations not supported
```

**Solution**:
```bash
# Install iproute2 via Homebrew
brew install iproute2mac

# Or use alternative approach
# Use pfctl for firewall rules instead of NFTables
# Use ifconfig for network interface management

# For WiFi issues, use macOS-specific script
./bridge/macos_wifi_fix.sh
```

#### Issue: Permission Issues with Network Services

**Symptoms**:
```
Operation not permitted
Cannot bind to privileged ports
Network configuration access denied
```

**Solution**:
```bash
# Grant necessary permissions
# Go to System Preferences > Security & Privacy > Privacy
# Add Terminal/iTerm to:
# - Full Disk Access
# - Network
# - Accessibility

# Use pfctl for firewall configuration instead of NFTables
sudo pfctl -f /etc/pf.conf
sudo pfctl -e
```

### OpenWRT-Specific Issues

#### Issue: Insufficient Memory

**Symptoms**:
```
Out of memory errors
Process killed by OOM
Slow performance
```

**Solution**:
```bash
# Optimize memory usage
# Edit /etc/sysctl.conf
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' >> /etc/sysctl.conf

# Optimize application memory usage
# Use C implementation instead of Python
# Reduce worker count
# Enable memory compression

# Monitor memory usage
free
cat /proc/meminfo
```

#### Issue: WiFi Mesh Not Forming

**Symptoms**:
```
mesh join failed
Mesh interface not found
Poor mesh performance
```

**Solution**:
```bash
# Check WiFi driver support
iw list | grep mesh

# Configure mesh properly
uci set wireless.radio0.channel='13'
uci set wireless.default_radio0.mode='mesh'
uci set wireless.default_radio0.mesh_id='EDGE_LATTICE_01'
uci set wireless.default_radio0.encryption='sae'
uci set wireless.default_radio0.key='StrongPassword123'
uci commit wireless
wifi reload

# Install necessary packages
opkg update
opkg install iw mesh-tools
```

---

## Debug Mode and Logging

### Enable Debug Logging

#### Application-Level Debugging
```python
# Enable debug logging in components
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agiswarm-debug.log'),
        logging.StreamHandler()
    ]
)

# Add debug logging to components
logger = logging.getLogger('agisworm')
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

#### Network Debugging
```bash
# Enable verbose network operations
export AGISWARM_DEBUG=1

# Monitor network traffic
sudo tcpdump -i any -n -v udp port 6000

# Enable kernel network debugging
echo 1 | sudo tee /proc/sys/net/ipv4/conf/all/log_martians
echo 1 | sudo tee /proc/sys/net/ipv4/conf/all/rp_filter
```

### Log Analysis Tools

#### Log Parser Script
```bash
#!/bin/bash
# Parse AGISWARM logs for common issues

LOG_FILE=${1:-"agiswarm-debug.log"}

echo "=== AGISWARM Log Analysis ==="
echo "Log file: $LOG_FILE"
echo ""

# Error count
echo "📊 ERROR SUMMARY"
echo "================"
grep -c "ERROR\|CRITICAL\|FATAL" "$LOG_FILE" | xargs echo "Total errors:"

# Common error patterns
echo ""
echo "🚨 COMMON ISSUES"
echo "================"
echo "Connection errors: $(grep -c "Connection.*refused\|timeout\|timed out" "$LOG_FILE")"
echo "Permission errors: $(grep -c "Permission denied\|Operation not permitted" "$LOG_FILE")"
echo "Import errors: $(grep -c "ImportError\|ModuleNotFoundError" "$LOG_FILE")"
echo "Network errors: $(grep -c "network\|NetworkError\|NET_" "$LOG_FILE")"

# Warning patterns
echo ""
echo "⚠️  WARNINGS"
echo "============"
grep -c "Warning\|Deprecation" "$LOG_FILE" | xargs echo "Total warnings:"

# Performance issues
echo ""
echo "⚡ PERFORMANCE ISSUES"
echo "====================="
grep -c "latency\|jitter\|timeout" "$LOG_FILE" | xargs echo "Performance-related messages:"

# Timeline analysis
echo ""
echo "📅 TIMELINE ANALYSIS"
echo "==================="
echo "First error: $(grep -E "ERROR|CRITICAL|FATAL" "$LOG_FILE" | head -1 | cut -d: -f1-2)"
echo "Last error: $(grep -E "ERROR|CRITICAL|FATAL" "$LOG_FILE" | tail -1 | cut -d: -f1-2)"
```

### Remote Debugging

#### SSH Tunneling for Remote Debugging
```bash
# Setup SSH tunnel for remote debugging
ssh -L 6000:localhost:6000 user@remote-host

# Forward logs via SSH
ssh user@remote-host "tail -f /var/log/agiswarm.log" | tee local-agiswarm.log

# Execute remote commands
ssh user@remote-host "cd /path/to/agiswarm && python3 aggregator/main_runner.py"
```

#### Network Packet Capture
```bash
# Capture AGISWARM traffic for analysis
sudo tcpdump -i any -w agiswarm-capture.pcap udp port 6000

# Analyze capture file
sudo tcpdump -r agiswarm-capture.pcap -n

# Use Wireshark for detailed analysis
wireshark agiswarm-capture.pcap
```

---

## Recovery Procedures

### System Recovery Script

```bash
#!/bin/bash
# AGISWARM System Recovery Script
# Usage: ./recover_agiswarm.sh

echo "=========================================="
echo "        AGISWARM Recovery Procedure"
echo "=========================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${YELLOW}[STEP] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Step 1: Stop all AGISWARM processes
print_step "Stopping all AGISWARM processes..."
pkill -f "aggregator/main_runner.py" || true
pkill -f "worker/worker.py" || true
pkill -f "operator/operator_cli.py" || true
sleep 2
print_success "AGISWARM processes stopped"

# Step 2: Clean up network namespaces
print_step "Cleaning up network namespaces..."
sudo ip netns del control_net 2>/dev/null || true
sudo ip link delete veth_h 2>/dev/null || true
sudo nft delete table inet filter 2>/dev/null || true
print_success "Network namespaces cleaned"

# Step 3: Reset WiFi interface
print_step "Resetting WiFi interface..."
if command -v ifconfig >/dev/null 2>&1; then
    sudo ifconfig en0 down
    sudo ifconfig en0 up
elif command -v ip >/dev/null 2>&1; then
    sudo ip link set wlan0 down
    sudo ip link set wlan0 up
fi
print_success "WiFi interface reset"

# Step 4: Clear temporary files
print_step "Clearing temporary files..."
rm -f /tmp/agiswarm-*.pid
rm -f /tmp/agiswarm-*.lock
rm -f /var/run/agiswarm-*.sock
print_success "Temporary files cleared"

# Step 5: Check and repair Python environment
print_step "Checking Python environment..."
source .venv/bin/activate
python3 -c "import asyncio, cbor, cryptography, nacl" || {
    print_error "Python dependencies missing, reinstalling..."
    pip install -r requirements.txt
}
print_success "Python environment verified"

# Step 6: Restore default configuration
print_step "Restoring default configuration..."
cp configs/app_config.yaml configs/app_config.yaml.backup 2>/dev/null || true
cp configs/example_matrix.json configs/example_matrix.json.backup 2>/dev/null || true
print_success "Configuration backed up"

# Step 7: Verify key integrity
print_step "Verifying cryptographic keys..."
if [ -f "operator/operator_private.key" ]; then
    python3 -c "
from cryptography.hazmat.primitives.asymmetric import ed25519
try:
    with open('operator/operator_private.key', 'rb') as f:
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(f.read())
    print('✅ Private key valid')
except Exception as e:
    print(f'❌ Private key invalid: {e}')
    print('Regenerating keys...')
    import subprocess
    subprocess.run(['python3', 'operator/keygen.py', '--force'])
"
else
    print_step "Generating new cryptographic keys..."
    python3 operator/keygen.py
fi

# Step 8: Run system diagnostics
print_step "Running system diagnostics..."
./diagnose_agiswarm.sh > /tmp/agiswarm-diagnostics.log 2>&1

# Step 9: Restart AGISWARM services
print_step "Restarting AGISWARM services..."
source .venv/bin/activate

# Start aggregator
python3 aggregator/main_runner.py > /tmp/aggregator.log 2>&1 &
AGGREGATOR_PID=$!
echo $AGGREGATOR_PID > /tmp/aggregator.pid
sleep 3

# Check if aggregator started successfully
if kill -0 $AGGREGATOR_PID 2>/dev/null; then
    print_success "Aggregator started (PID: $AGGREGATOR_PID)"
else
    print_error "Aggregator failed to start"
    cat /tmp/aggregator.log
fi

# Step 10: Verification
print_step "Performing system verification..."

# Check if aggregator is responding
sleep 2
if timeout 5 python3 -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)
try:
    sock.sendto(b'ping', ('127.0.0.1', 6000))
    data, addr = sock.recvfrom(1024)
    print('✅ Aggregator responding')
except Exception as e:
    print(f'❌ Aggregator not responding: {e}')
finally:
    sock.close()
" 2>/dev/null; then
    print_success "System recovery completed successfully"
else
    print_error "System recovery completed with issues"
fi

echo ""
echo "=========================================="
echo "           Recovery Complete"
echo "=========================================="
echo "Logs available at:"
echo "- Aggregator: /tmp/aggregator.log"
echo "- Diagnostics: /tmp/agiswarm-diagnostics.log"
echo ""
echo "To start using AGISWARM:"
echo "1. Source virtual environment: source .venv/bin/activate"
echo "2. Start worker: python3 worker/worker.py"
echo "3. Start operator: python3 operator/operator_cli.py"
```

### Emergency Procedures

#### Complete System Reset
```bash
#!/bin/bash
# Complete AGISWARM system reset (use with caution)

echo "⚠️  This will completely reset AGISWARM installation"
echo "Continue? (yes/no)"
read -r response

if [ "$response" != "yes" ]; then
    echo "Reset cancelled"
    exit 1
fi

# Backup user data
cp -r configs/ ~/agiswarm-config-backup/
cp -r operator/ ~/agiswarm-operator-backup/

# Stop all processes
pkill -f agiswarm || true

# Remove virtual environment
rm -rf .venv

# Clear all logs
rm -f *.log
rm -rf logs/

# Reinstall everything
git pull origin main
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Regenerate keys
python3 operator/keygen.py

echo "System reset complete"
echo "Your configurations are backed up in ~/agiswarm-*"
```

This comprehensive troubleshooting guide covers most common issues and provides detailed diagnostic and recovery procedures for the AGISWARM system.