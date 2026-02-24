#!/bin/bash
# Fix broken network after zombie VPN tunnels
echo "=== Cleaning up zombie VPN tunnels ==="

# Kill any openvpn processes
sudo killall openvpn 2>/dev/null
echo "Killed openvpn processes"

# Delete ALL tun interfaces
for i in $(ip -o link show | grep tun | awk -F': ' '{print $2}'); do
    sudo ip link delete "$i" 2>/dev/null
    echo "Deleted $i"
done

# Flush ALL iptables rules (VPN kill switches etc)
sudo iptables -F 2>/dev/null
sudo iptables -X 2>/dev/null
sudo iptables -t nat -F 2>/dev/null
sudo iptables -P INPUT ACCEPT 2>/dev/null
sudo iptables -P FORWARD ACCEPT 2>/dev/null
sudo iptables -P OUTPUT ACCEPT 2>/dev/null
echo "Flushed iptables"

# Fix routing
sudo ip route flush cache 2>/dev/null
sudo ip route replace default via 172.23.48.1 dev eth0 2>/dev/null
echo "Reset routing"

# Fix DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf > /dev/null
echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf > /dev/null
echo "Set DNS"

echo ""
echo "=== Testing ==="
ping -c 1 -W 3 8.8.8.8
echo ""
curl -s --max-time 5 https://api.ipify.org && echo "" || echo "curl failed"
