# WiFi Recovery Guide

## Overview

This guide provides procedures for recovering WiFi connectivity when working with AGISWARM's network bridge and mesh configurations. The system uses network namespaces and virtual interfaces that can sometimes interfere with host WiFi connectivity.

## Quick Recovery Scripts

### macOS: WiFi Fix Script

**Location**: `bridge/macos_wifi_fix.sh`

**Purpose**: Restore WiFi connectivity on macOS systems after network configuration changes.

**Usage**:
```bash
bash bridge/macos_wifi_fix.sh
```

**What it does**:
1. Detects your WiFi interface (usually `en0` or `en1`)
2. Cycles WiFi power (off → on)
3. Flushes DNS cache
4. Renews DHCP lease

**When to use**:
- WiFi stops working after bridge setup
- Cannot reach internet after mesh configuration
- DNS resolution fails
- DHCP issues (no IP address)

**Requirements**:
- macOS system
- May require `sudo` for DNS flush operations

### Linux: Network Cleanup Script

**Location**: `bridge/cleanup_network.sh`

**Purpose**: Remove network namespaces, bridges, and NFTables rules that might interfere with normal networking.

**Usage**:
```bash
sudo bash bridge/cleanup_network.sh
```

**What it does**:
1. Removes `mesh_ns` network namespace
2. Deletes NFTables filter tables (inet and bridge)
3. Removes `veth_mesh` virtual Ethernet pairs

**When to use**:
- After testing mesh configurations
- When host network becomes unreachable
- Before switching to normal network mode
- When virtual interfaces persist after testing

**Requirements**:
- Linux system with `ip` and `nft` utilities
- Root/sudo privileges
- systemd-based network management (optional)

## Manual Recovery Procedures

### macOS Manual WiFi Recovery

If the automated script doesn't work:

1. **Turn WiFi Off/On via System Preferences**:
   - Click WiFi icon in menu bar
   - Select "Turn Wi-Fi Off"
   - Wait 5 seconds
   - Select "Turn Wi-Fi On"

2. **Manually Renew DHCP Lease**:
   ```bash
   # Find your WiFi interface
   networksetup -listallhardwareports
   
   # Renew DHCP (replace en0 with your interface)
   sudo ipconfig set en0 DHCP
   ```

3. **Flush DNS Cache**:
   ```bash
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```

4. **Reset Network Location**:
   - System Preferences → Network
   - Click location dropdown → Edit Locations
   - Create new location, switch to it
   - Reconfigure WiFi

5. **Restart Network Services**:
   ```bash
   # Last resort - restart network stack
   sudo ifconfig en0 down
   sudo ifconfig en0 up
   ```

### Linux Manual Network Recovery

If the cleanup script doesn't work:

1. **List and Remove Network Namespaces**:
   ```bash
   # List all network namespaces
   ip netns list
   
   # Remove specific namespace
   sudo ip netns delete mesh_ns
   
   # Remove all (if needed)
   sudo ip -all netns delete
   ```

2. **Remove Virtual Interfaces**:
   ```bash
   # List interfaces
   ip link show
   
   # Delete veth pairs
   sudo ip link delete veth_mesh
   sudo ip link delete veth_host
   ```

3. **Clear NFTables Rules**:
   ```bash
   # List current tables
   sudo nft list tables
   
   # Delete specific tables
   sudo nft delete table inet filter
   sudo nft delete table bridge filter
   
   # Nuclear option - flush everything
   sudo nft flush ruleset
   ```

4. **Restart Network Manager**:
   ```bash
   # systemd-based systems
   sudo systemctl restart NetworkManager
   
   # Or restart networking service
   sudo systemctl restart networking
   ```

5. **Bring WiFi Interface Up**:
   ```bash
   # Find your WiFi interface
   ip link show
   
   # Bring it up (replace wlan0 with your interface)
   sudo ip link set wlan0 up
   
   # Request DHCP
   sudo dhclient wlan0
   ```

## Preventing WiFi Issues

### Best Practices

1. **Use Separate Network Namespaces**: Always run mesh network in isolated namespace
   ```bash
   # Good: Isolated namespace
   sudo ip netns exec mesh_ns ./mesh_node
   
   # Bad: Running on host network
   sudo ./mesh_node
   ```

2. **Test with Ethernet First**: When developing bridge configurations, use Ethernet connection for host

3. **Document Interface Names**: Note your WiFi interface name before bridge setup
   ```bash
   # Save interface info
   ip link show > ~/network_before.txt
   ```

4. **Use Cleanup Scripts**: Always run cleanup scripts when done testing
   ```bash
   # At end of testing session
   sudo bash bridge/cleanup_network.sh
   ```

5. **Backup Network Configuration**:
   ```bash
   # macOS
   networksetup -listallhardwareports > ~/network_config_backup.txt
   
   # Linux
   ip addr show > ~/ip_addr_backup.txt
   ip route show > ~/ip_route_backup.txt
   ```

## Common Issues and Solutions

### Issue: "No WiFi Networks Found"

**Cause**: WiFi interface disabled or driver issue

**Solution**:
```bash
# macOS
sudo networksetup -setairportpower en0 on

# Linux
sudo ip link set wlan0 up
sudo rfkill unblock wifi
```

### Issue: "Connected but No Internet"

**Cause**: DNS or routing issue

**Solution**:
```bash
# macOS
sudo dscacheutil -flushcache
sudo route flush

# Linux
sudo systemctl restart systemd-resolved
sudo ip route flush cache
```

### Issue: "Cannot Delete Namespace: Device Busy"

**Cause**: Processes still running in namespace

**Solution**:
```bash
# List processes in namespace
sudo ip netns pids mesh_ns

# Kill processes
sudo ip netns pids mesh_ns | xargs sudo kill

# Then delete
sudo ip netns delete mesh_ns
```

### Issue: "NFTables Table Not Found"

**Cause**: Table already deleted or never existed

**Solution**: This is not an error. The cleanup script handles this gracefully with `|| echo "..."` fallback.

### Issue: "Permission Denied on Cleanup"

**Cause**: Missing root privileges

**Solution**:
```bash
# Always use sudo for cleanup
sudo bash bridge/cleanup_network.sh
```

## Emergency Network Reset

### macOS Complete Network Reset

```bash
# 1. Remove all network preferences (BACKUP FIRST!)
sudo rm /Library/Preferences/SystemConfiguration/NetworkInterfaces.plist
sudo rm /Library/Preferences/SystemConfiguration/preferences.plist

# 2. Reboot
sudo reboot

# After reboot, reconfigure WiFi in System Preferences
```

**Warning**: This removes all network configurations. Use only as last resort.

### Linux Complete Network Reset

```bash
# 1. Stop all network services
sudo systemctl stop NetworkManager
sudo systemctl stop networking

# 2. Remove all custom configurations
sudo ip link set dev lo up  # Keep loopback
# Carefully remove virtual interfaces

# 3. Restart services
sudo systemctl start NetworkManager
sudo systemctl start networking
```

## Getting Help

If these procedures don't resolve your issue:

1. **Check System Logs**:
   ```bash
   # macOS
   log show --predicate 'subsystem == "com.apple.wifi"' --last 1h
   
   # Linux
   sudo journalctl -u NetworkManager -n 100
   ```

2. **Hardware Test**:
   - Test WiFi on another network
   - Test with USB Ethernet adapter
   - Check if other devices can connect

3. **Report Issue**: Include:
   - Operating system and version
   - Output of `ip link show` (Linux) or `networksetup -listallhardwareports` (macOS)
   - Steps to reproduce
   - Error messages from scripts

## References

- [Linux Network Namespaces](https://man7.org/linux/man-pages/man8/ip-netns.8.html)
- [NFTables Documentation](https://wiki.nftables.org/)
- [macOS networksetup Manual](https://ss64.com/osx/networksetup.html)
- [NetworkManager Documentation](https://networkmanager.dev/)
