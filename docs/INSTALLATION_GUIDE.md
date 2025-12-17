# AGISWARM Installation Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Installation](#step-by-step-installation)
4. [Platform-Specific Instructions](#platform-specific-instructions)
5. [Verification](#verification)
6. [Common Installation Issues](#common-installation-issues)

---

## System Requirements

### Minimum Requirements
- **Operating System**: Linux (Ubuntu 18.04+, CentOS 7+) or macOS 10.14+
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **CPU**: 1 core minimum, 2+ cores recommended
- **Storage**: 1GB free space
- **Network**: WiFi adapter supporting access point mode

### Recommended Requirements
- **Operating System**: Ubuntu 20.04 LTS or macOS 12.0+
- **Python**: 3.9 or higher
- **RAM**: 8GB
- **CPU**: 4+ cores
- **Storage**: 5GB SSD
- **Network**: Dedicated WiFi adapter for mesh networking

### Hardware Compatibility

#### Linux-Compatible WiFi Adapters
- **Recommended**: Intel AX200, AX201, Killer AX1650
- **Compatible**: Most USB WiFi adapters with Linux drivers
- **Avoid**: Some older Broadcom adapters (driver issues)

#### macOS-Compatible WiFi
- **Built-in**: Most MacBook Air/Pro models
- **USB**: Alfa AWUS036ACS, AWUS036NHA
- **Thunderbolt**: CalDigit AV Adapter

---

## Prerequisites

### Python Environment

#### Install Python 3.8+
**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install -y python3.8 python3.8-venv python3.8-dev python3-pip
```

**CentOS/RHEL**:
```bash
sudo yum install -y python38 python38-devel python38-pip
```

**macOS**:
```bash
# Using Homebrew
brew install python@3.8

# Or download from python.org
# https://www.python.org/downloads/
```

#### Verify Python Installation
```bash
python3 --version
pip3 --version
```

Should output Python 3.8+ and pip version.

### System Dependencies

#### Linux Dependencies
**Ubuntu/Debian**:
```bash
sudo apt install -y \
    build-essential \
    cmake \
    pkg-config \
    libssl-dev \
    libffi-dev \
    python3-dev \
    iproute2 \
    nftables \
    wireless-tools \
    bridge-utils \
    tcpdump \
    net-tools
```

**CentOS/RHEL**:
```bash
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
    python38-devel \
    openssl-devel \
    libffi-devel \
    iproute \
    nftables \
    wireless-tools \
    bridge-utils \
    tcpdump \
    net-tools
```

#### macOS Dependencies
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Network Tools

#### Linux Network Tools
```bash
# Install network namespace support
sudo modprobe bridge
sudo modprobe veth

# Verify network namespace support
ip netns list
```

#### WiFi Configuration Tools
**Linux**:
```bash
# Install WiFi tools
sudo apt install -y iw wireless-tools wpasupplicant

# Verify WiFi interface
iwconfig
```

**macOS**:
```bash
# macOS typically has WiFi tools pre-installed
# Verify WiFi interface
ifconfig | grep -E "^[a-z]"
```

---

## Step-by-Step Installation

### Step 1: Clone Repository

```bash
# Clone the AGISWARM repository
git clone https://github.com/AXI0MH1VE/AGISWARM.git
cd AGISWARM

# Verify repository contents
ls -la
```

Expected output:
```
README.md
requirements.txt
aggregator/
bridge/
configs/
operator/
scripts/
tests/
worker/
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Verify activation (prompt should change)
which python
which pip
```

**Note**: Always activate the virtual environment before working with AGISWARM.

### Step 3: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

**Expected dependencies**:
```
asyncio-mqtt==0.16.1
cborg==0.5.0
cryptography==3.4.8
pynacl==1.4.0
pytest==6.2.4
pytest-asyncio==0.15.1
python-socketio==5.4.0
```

### Step 4: Install System Dependencies

#### Linux Installation
```bash
# Install system packages
sudo apt update
sudo apt install -y \
    iproute2 \
    nftables \
    wireless-tools \
    bridge-utils

# Enable NFTables
sudo systemctl enable nftables
sudo systemctl start nftables

# Verify installation
sudo nft list ruleset
```

#### macOS Installation
```bash
# macOS typically has required tools pre-installed
# Verify network tools
ifconfig --help
networksetup --help
```

### Step 5: Generate Cryptographic Keys

```bash
# Generate operator keys
python operator/keygen.py
```

**Output files created**:
```
operator/
├── __init__.py
├── keygen.py
├── operator_cli.py
├── operator_private.key    # Keep secure!
└── operator_public.key     # Can be shared
```

**⚠️ CRITICAL SECURITY WARNING**:
- Never commit `operator_private.key` to version control
- Keep private key secure and backed up
- Use separate keys for different environments

### Step 6: Configure Network (Optional)

#### For Mesh Networking
```bash
# Make network setup scripts executable
chmod +x bridge/*.sh

# Check available WiFi interfaces
iwconfig
# or on macOS
ifconfig | grep -E "^[a-z]"

# Update interface name in scripts if needed
sed -i 's/wlan0/YOUR_INTERFACE_NAME/g' bridge/netns_setup.sh
```

#### For Local Testing (No Network Isolation)
```bash
# Skip network setup for local simulation
# The system will work without network isolation
echo "Network isolation skipped for local testing"
```

### Step 7: Verify Installation

```bash
# Run basic tests
python -m pytest tests/ -v

# Test component imports
python -c "
from aggregator.aggregator import Aggregator
from worker.worker import Worker  
from operator.operator_cli import Operator
print('All components imported successfully')
"

# Test key generation
python operator/keygen.py --test
```

---

## Platform-Specific Instructions

### Ubuntu 20.04 LTS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.8 python3.8-venv python3.8-dev python3-pip

# Install network tools
sudo apt install -y iproute2 nftables wireless-tools

# Create user group for network operations
sudo groupadd agiswarm
sudo usermod -a -G agiswarm $USER

# Log out and back in for group changes to take effect
```

### CentOS 8

```bash
# Update system
sudo dnf update -y

# Enable EPEL repository
sudo dnf install -y epel-release

# Install Python and development tools
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y python38 python38-devel python38-pip

# Install network tools
sudo dnf install -y iproute nftables wireless-tools

# Configure firewall for AGISWARM
sudo firewall-cmd --permanent --add-port=6000/udp
sudo firewall-cmd --reload
```

### macOS Big Sur (11.0+)

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.9

# Verify installation
python3 --version
pip3 --version

# Install network tools (usually pre-installed)
brew install iproute2qt5  # If needed

# Grant necessary permissions
# Go to System Preferences > Security & Privacy > Privacy
# Add Terminal/iTerm to "Full Disk Access" and "Network"
```

### Raspberry Pi (Raspberry OS)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.8 python3.8-venv python3-dev python3-pip

# Install network tools
sudo apt install -y iproute2 nftables wireless-tools

# Configure WiFi for mesh networking
sudo apt install -y hostapd

# Enable WiFi interface
sudo raspi-config
# Navigate to: Interface Options > WiFi > Enable
```

---

## Verification

### Basic Functionality Test

```bash
# Test 1: Component imports
python3 -c "
try:
    from aggregator.aggregator import Aggregator
    from worker.worker import Worker
    from operator.operator_cli import Operator
    print('✅ All components imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Test 2: Key generation
python3 operator/keygen.py --output /tmp/test_keys
if [ -f /tmp/test_keys/operator_private.key ]; then
    echo "✅ Key generation successful"
    rm -rf /tmp/test_keys
else
    echo "❌ Key generation failed"
    exit(1)
fi

# Test 3: Configuration loading
python3 -c "
import yaml
with open('configs/app_config.yaml') as f:
    config = yaml.safe_load(f)
print('✅ Configuration loading successful')
print(f'Aggregator port: {config[\"aggregator\"][\"udp_port\"]}')
"

# Test 4: Network tools
if command -v ip >/dev/null 2>&1; then
    echo "✅ Network tools available"
else
    echo "❌ Network tools missing"
    exit(1)
fi

echo "🎉 All verification tests passed!"
```

### Network Interface Test

```bash
# Test WiFi interface availability
echo "=== WiFi Interface Test ==="

# Check for WiFi interfaces
if command -v iwconfig >/dev/null 2>&1; then
    iwconfig 2>/dev/null | grep -E "wlan|wireless"
    if [ $? -eq 0 ]; then
        echo "✅ WiFi interface detected"
    else
        echo "⚠️  No WiFi interface found"
    fi
elif command -v ifconfig >/dev/null 2>&1; then
    ifconfig | grep -E "en[0-9]+.*flags.*up.*broadcast.*running"
    if [ $? -eq 0 ]; then
        echo "✅ Network interface detected"
    else
        echo "⚠️  No active network interface found"
    fi
else
    echo "❌ Network tools not available"
fi
```

### Simulation Test

```bash
# Test local simulation (basic connectivity)
echo "=== Simulation Test ==="

# Test aggregator can start
timeout 5s python3 aggregator/main_runner.py &
AGGREGATOR_PID=$!
sleep 2

if kill -0 $AGGREGATOR_PID 2>/dev/null; then
    echo "✅ Aggregator can start"
    kill $AGGREGATOR_PID
else
    echo "❌ Aggregator failed to start"
    exit(1)
fi

# Test worker can start
timeout 5s python3 worker/worker.py --test &
WORKER_PID=$!
sleep 2

if kill -0 $WORKER_PID 2>/dev/null; then
    echo "✅ Worker can start"
    kill $WORKER_PID
else
    echo "❌ Worker failed to start"
    exit(1)
fi

echo "🎉 Simulation test passed!"
```

---

## Common Installation Issues

### Issue 1: Python Version Mismatch

**Symptoms**:
- `python3: command not found`
- `pip3: command not found`
- Version errors during dependency installation

**Solution**:
```bash
# Check available Python versions
ls /usr/bin/python*

# Install specific Python version
sudo apt install -y python3.8 python3.8-venv

# Use specific version
python3.8 -m venv .venv
source .venv/bin/activate
python3.8 -m pip install -r requirements.txt
```

### Issue 2: Permission Denied Errors

**Symptoms**:
- `Permission denied` when running scripts
- Network namespace operations fail
- Cannot bind to privileged ports

**Solution**:
```bash
# Make scripts executable
chmod +x bridge/*.sh
chmod +x scripts/*.sh

# Run with sudo for network operations
sudo ./bridge/netns_setup.sh

# Add user to necessary groups
sudo usermod -a -G netdev,sudo $USER
# Log out and back in
```

### Issue 3: Network Interface Not Found

**Symptoms**:
- `iwconfig: command not found`
- No WiFi interfaces detected
- Network setup scripts fail

**Linux Solution**:
```bash
# Install wireless tools
sudo apt install -y wireless-tools iw

# Check available interfaces
ip link show
iwconfig

# Enable WiFi interface
sudo ip link set wlan0 up
```

**macOS Solution**:
```bash
# Check available interfaces
ifconfig

# Common macOS WiFi interfaces: en0, en1
# Usually no additional setup needed

# Verify WiFi is enabled
networksetup -getairportpower en0
```

### Issue 4: NFTables Configuration Fails

**Symptoms**:
- `nft: command not found`
- Firewall setup fails
- Network isolation doesn't work

**Solution**:
```bash
# Install NFTables
sudo apt install -y nftables

# Enable NFTables
sudo systemctl enable nftables
sudo systemctl start nftables

# Verify installation
sudo nft list ruleset
```

### Issue 5: Cryptographic Library Errors

**Symptoms**:
- `ImportError: No module named 'cryptography'`
- Key generation fails
- Signature verification errors

**Solution**:
```bash
# Install cryptographic libraries
pip install cryptography pynacl

# Install development headers
sudo apt install -y libssl-dev libffi-dev python3-dev

# Verify installation
python3 -c "import cryptography; print('Cryptography installed')"
python3 -c "import nacl; print('NaCl installed')"
```

### Issue 6: Virtual Environment Issues

**Symptoms**:
- `pip: command not found`
- Dependencies install in wrong location
- Python modules not found

**Solution**:
```bash
# Create virtual environment with explicit Python
python3.8 -m venv .venv
source .venv/bin/activate

# Verify virtual environment
which python
which pip
pip --version

# If issues persist, recreate virtual environment
rm -rf .venv
python3.8 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue 7: Test Failures

**Symptoms**:
- `pytest: command not found`
- Import errors during testing
- Test timeouts

**Solution**:
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests with verbose output
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_coding.py -v

# Run tests with longer timeout
python -m pytest tests/ --timeout=30
```

---

## Post-Installation Steps

### 1. Create Project Shortcuts

```bash
# Create convenient aliases
echo "alias agiswarm-start='cd /path/to/AGISWARM && source .venv/bin/activate'" >> ~/.bashrc
echo "alias agiswarm-test='cd /path/to/AGISWARM && python -m pytest tests/ -v'" >> ~/.bashrc
source ~/.bashrc
```

### 2. Setup Log Rotation

```bash
# Create log directory
mkdir -p logs

# Setup log rotation
sudo tee /etc/logrotate.d/agiswarm << EOF
/path/to/AGISWARM/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

### 3. Create Systemd Service (Optional)

**Linux only**:
```bash
# Create aggregator service
sudo tee /etc/systemd/system/agiswarm-aggregator.service << EOF
[Unit]
Description=AGISWARM Aggregator
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/path/to/AGISWARM
ExecStart=/path/to/AGISWARM/.venv/bin/python aggregator/main_runner.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable agiswarm-aggregator
sudo systemctl start agiswarm-aggregator
```

### 4. Configure Monitoring

```bash
# Create monitoring script
cat > monitor_agiswarm.sh << 'EOF'
#!/bin/bash
# Monitor AGISWARM system health

LOG_FILE="/var/log/agiswarm-monitor.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Check if aggregator is running
if ! pgrep -f "aggregator/main_runner.py" > /dev/null; then
    echo "[$TIMESTAMP] ERROR: Aggregator not running" >> $LOG_FILE
    # Restart aggregator if desired
    # systemctl restart agiswarm-aggregator
fi

# Check network connectivity
if ! ping -c 1 127.0.0.1 > /dev/null 2>&1; then
    echo "[$TIMESTAMP] ERROR: Network connectivity issue" >> $LOG_FILE
fi

echo "[$TIMESTAMP] INFO: System check completed" >> $LOG_FILE
EOF

chmod +x monitor_agiswarm.sh

# Add to crontab for regular monitoring
echo "*/5 * * * * /path/to/monitor_agiswarm.sh" | crontab -
```

### 5. Backup Configuration

```bash
# Create backup script
cat > backup_config.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/agiswarm/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup configuration files
cp configs/*.yaml $BACKUP_DIR/
cp operator/operator_public.key $BACKUP_DIR/

# Backup custom scripts
cp -r scripts/custom $BACKUP_DIR/ 2>/dev/null || true

echo "Configuration backed up to $BACKUP_DIR"
EOF

chmod +x backup_config.sh
```

---

## Next Steps

After successful installation:

1. **Read the [Comprehensive Guide](COMPREHENSIVE_GUIDE.md)** for detailed usage instructions
2. **Start with [Quick Start Guide](COMPREHENSIVE_GUIDE.md#quick-start-guide)** to run your first simulation
3. **Review [Network Configuration](NETWORK_CONFIG.md)** for production deployment
4. **Check [Troubleshooting Guide](TROUBLESHOOTING.md)** if you encounter issues

For additional help, visit the project repository or contact the development team.