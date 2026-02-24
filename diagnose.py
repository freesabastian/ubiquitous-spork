#!/usr/bin/env python3
"""Quick diagnostic: Is the network actually working through the VPN?"""
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.openvpn import OpenVPNManager

def run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=isinstance(cmd, str))
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

print("=" * 60)
print("  NETWORK DIAGNOSTIC")
print("=" * 60)

# 1. Check if any VPN/tun is up
print("\n[1] Checking tun interfaces...")
rc, out, _ = run("ip addr show | grep -E 'tun[0-9]'")
if out:
    print(f"  ✓ Found tun interfaces:\n{out}")
else:
    print("  ✗ No tun interfaces found")

# 2. Check default route
print("\n[2] Default route...")
rc, out, _ = run("ip route show default")
print(f"  {out}")

# 3. Check DNS
print("\n[3] DNS resolution...")
for host in ["google.com", "cleantempmail.com"]:
    rc, out, err = run(f"nslookup {host}")
    if rc == 0 and "Address" in out:
        # Get the resolved IP
        lines = out.split("\n")
        ips = [l for l in lines if "Address" in l and "Server" not in l]
        print(f"  {host}: {ips[0].strip() if ips else 'resolved'}")
    else:
        print(f"  {host}: FAILED ({err[:50]})")

# 4. Ping test
print("\n[4] Ping test...")
for host in ["8.8.8.8", "1.1.1.1"]:
    rc, out, _ = run(f"ping -c 1 -W 3 {host}")
    if rc == 0:
        ms = [l for l in out.split("\n") if "time=" in l]
        print(f"  {host}: ✓ {ms[0].split('time=')[1] if ms else 'OK'}")
    else:
        print(f"  {host}: ✗ FAILED")

# 5. HTTP test (curl, no proxy)
print("\n[5] HTTP connectivity (curl)...")
for url in ["https://api.ipify.org", "https://cleantempmail.com", "https://google.com"]:
    rc, out, err = run(f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 5 {url}")
    if rc == 0 and out and out != "000":
        print(f"  {url}: ✓ HTTP {out}")
    else:
        print(f"  {url}: ✗ FAILED (code={out}, err={err[:60]})")

# 6. Check what IP we're showing
print("\n[6] Current public IP...")
rc, out, _ = run("curl -s --max-time 5 https://api.ipify.org")
if out:
    print(f"  IP: {out}")
else:
    print("  ✗ Could not determine IP")

# 7. Check if openvpn is running
print("\n[7] OpenVPN processes...")
rc, out, _ = run("ps aux | grep openvpn | grep -v grep")
if out:
    for line in out.split("\n"):
        parts = line.split()
        if len(parts) > 10:
            print(f"  PID {parts[1]}: {' '.join(parts[10:])}")
else:
    print("  ✗ No openvpn processes running")

# 8. Check iptables / firewall
print("\n[8] Firewall rules (iptables)...")
rc, out, _ = run("sudo iptables -L -n --line-numbers 2>/dev/null | head -20")
if out:
    print(f"  {out[:200]}")
else:
    print("  (no rules or no sudo)")

print("\n" + "=" * 60)
print("  DONE")
print("=" * 60)
