# Manual WiFi Fix Commands

If the cleanup script doesn't work, run these commands individually:

## 1. Check current network namespaces
```bash
ip netns list
```

## 2. Remove NFTables rules
```bash
sudo nft delete table inet filter 2>/dev/null || true
```

## 3. Move WiFi interface back to main namespace
```bash
# Find your WiFi interface name (usually wlan0, wlan1, or en0)
ip link show | grep -E "^[0-9]+"

# Replace wlan1 with your actual interface name
sudo ip netns exec control_net ip link set wlan1 netns 1
```

## 4. Remove veth pair
```bash
sudo ip link delete veth_h 2>/dev/null || true
```

## 5. Remove network namespace
```bash
sudo ip netns del control_net 2>/dev/null || true
```

## 6. Bring up WiFi interface
```bash
# Replace wlan1 with your actual interface name
sudo ip link set wlan1 up
```

## 7. Restart WiFi service (if needed)
```bash
# For macOS:
sudo ifconfig en0 down
sudo ifconfig en0 up

# For Linux:
sudo systemctl restart NetworkManager
# or
sudo systemctl restart networking
```

## 8. macOS Automated Fix
If you're on macOS, you can use the automated script:
```bash
chmod +x bridge/macos_wifi_fix.sh
./bridge/macos_wifi_fix.sh