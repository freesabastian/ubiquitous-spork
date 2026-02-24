#!/usr/bin/env python3
"""
VPN & Proxy Manager
Integrates free VPNs and proxy sources
"""

import requests
import random
import time
import subprocess
import os
import socket
from concurrent.futures import ThreadPoolExecutor
try:
    from concurrent.futures import as_completed
except ImportError:
    as_completed = None, as_completed

# Free VPN configurations
FREE_VPNS = {
    'proton': {
        'name': 'Proton VPN',
        'type': 'vpn',
        'install': 'https://protonvpn.com/download',
        'linux_cmd': 'protonvpn',
        'free_tier': True,
        'data_limit': 'unlimited',
        'speed': 'medium',
    },
    'windscribe': {
        'name': 'Windscribe',
        'type': 'vpn',
        'install': 'https://windscribe.com/download',
        'linux_cmd': 'windscribe',
        'free_tier': True,
        'data_limit': '10GB/month',
        'speed': 'fast',
    },
    'privado': {
        'name': 'PrivadoVPN',
        'type': 'vpn', 
        'install': 'https://privadovpn.com/download',
        'linux_cmd': 'privado',
        'free_tier': True,
        'data_limit': '10GB/month',
        'speed': 'fast',
    },
}

# Free proxy sources
PROXY_SOURCES = {
    'github_speedx': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    'github_geonode': 'https://raw.githubusercontent.com/geonode/free-proxy-list/main/data/proxies.txt',
    'github_clarketm': 'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
    'github_shifty': 'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
    'github_proxy_list': 'https://raw.githubusercontent.com/proxy-list/proxy-list/master/proxy-list.txt',
    'github_mmpx': 'https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt',
    'github_rooster': 'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS.txt',
}

# Backup static proxy list (quality tested proxies)
BACKUP_PROXIES = [
    # These are example - replace with working ones
    "185.199.228.220:8888",
    "159.89.195.232:3128",
    "167.114.96.13:9300",
    "165.225.38.68:10605",
    "185.162.231.246:80",
]


class VPNProxyManager:
    """Manages VPNs and proxies for anonymity"""
    
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.current_vpn = None
        self.current_proxy = None
    
    def check_vpn_running(self):
        """Check if any VPN is running"""
        vpn_processes = [
            'protonvpn', 'windscribe', 'privado', 
            'openvpn', 'nordvpn', 'expressvpn',
            'surfshark', 'cyberghost', 'mullvad'
        ]
        
        for vpn in vpn_processes:
            try:
                result = subprocess.run(
                    ['pgrep', '-f', vpn],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"[VPN] Detected running: {vpn}")
                    return vpn
            except:
                continue
        
        return None
    
    def get_vpn_status(self):
        """Get detailed VPN status"""
        vpn = self.check_vpn_running()
        if vpn:
            return {
                'running': True,
                'name': vpn,
                'ip': self.get_current_ip()
            }
        return {'running': False}
    
    def get_current_ip(self):
        """Get current public IP"""
        try:
            resp = requests.get('https://api.ipify.org?format=json', timeout=5)
            if resp.status_code == 200:
                return resp.json().get('ip')
        except:
            pass
        
        try:
            resp = requests.get('http://httpbin.org/ip', timeout=5)
            if resp.status_code == 200:
                return resp.json().get('origin')
        except:
            pass
        
        return None
    
    def fetch_proxies_from_source(self, source_name, url):
        """Fetch proxies from a single source"""
        try:
            print(f"[Proxy] Fetching from {source_name}...")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                proxies = []
                for line in resp.text.strip().split('\n'):
                    line = line.strip()
                    if ':' in line and len(line) < 30:
                        parts = line.split(':')
                        if len(parts) == 2:
                            try:
                                int(parts[1])  # Validate port
                                proxies.append(line)
                            except:
                                continue
                print(f"[Proxy] Got {len(proxies)} from {source_name}")
                return proxies
        except Exception as e:
            print(f"[Proxy] Error {source_name}: {str(e)[:30]}")
        
        return []
    
    def fetch_all_proxies(self, max_sources=5):
        """Fetch from all sources in parallel"""
        print("[Proxy] Fetching from multiple sources...")
        
        all_proxies = set()
        sources = list(PROXY_SOURCES.items())[:max_sources]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for name, url in sources:
                futures.append(executor.submit(self.fetch_proxies_from_source, name, url))
            
            for future in futures:
                proxies = future.result()
                all_proxies.update(proxies)
        
        self.proxies = list(all_proxies)
        random.shuffle(self.proxies)
        
        print(f"[Proxy] Total fetched: {len(self.proxies)}")
        return self.proxies
    
    def test_proxy(self, proxy_str, timeout=8):
        """Test if a proxy is working"""
        try:
            proxies = {
                'http': f'http://{proxy_str}',
                'https': f'http://{proxy_str}'
            }
            
            start = time.time()
            resp = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=timeout
            )
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                return (True, elapsed)
        except:
            pass
        
        return (False, 999)
    
    def test_proxies_parallel(self, max_workers=100, max_to_test=300):
        """Test proxies in parallel"""
        if not self.proxies:
            self.fetch_all_proxies()
        
        to_test = self.proxies[:max_to_test]
        print(f"[Proxy] Testing {len(to_test)} proxies...")
        
        working = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.test_proxy, p): p for p in to_test}
            
            done = 0
            for future in futures.as_completed():
                done += 1
                proxy_str = futures[future]
                is_working, elapsed = future.result()
                
                if is_working:
                    working.append((proxy_str, elapsed))
                    print(f"[Proxy] ✓ {proxy_str} ({elapsed:.2f}s)")
                
                if done % 50 == 0:
                    print(f"[Proxy] Progress: {done}/{len(to_test)}, working: {len(working)}")
        
        # Sort by speed
        working.sort(key=lambda x: x[1])
        self.working_proxies = [p[0] for p in working]
        
        print(f"[Proxy] Found {len(self.working_proxies)} working proxies")
        return self.working_proxies
    
    def get_next_proxy(self):
        """Get next working proxy"""
        if not self.working_proxies:
            self.test_proxies_parallel()
        
        if self.working_proxies:
            return self.working_proxies.pop(0)
        
        return None
    
    def get_fastest_proxy(self):
        """Get the fastest proxy"""
        if not self.working_proxies:
            self.test_proxies_parallel()
        
        if self.working_proxies:
            return self.working_proxies[0]
        
        return None
    
    def use_backup_proxies(self):
        """Use backup static proxy list"""
        print(f"[Proxy] Using backup list ({len(BACKUP_PROXIES)} proxies)")
        self.proxies = BACKUP_PROXIES.copy()
        self.test_proxies_parallel(max_to_test=len(BACKUP_PROXIES))
        return self.working_proxies


def check_tor_status():
    """Check if Tor is running and working"""
    try:
        # Check if Tor service is running
        result = subprocess.run(
            ['systemctl', 'is-active', 'tor'],
            capture_output=True,
            text=True
        )
        
        if 'active' in result.stdout:
            print("[Tor] Tor service is running")
            
            # Test Tor connection
            try:
                proxies = {
                    'http': 'socks5://127.0.0.1:9050',
                    'https': 'socks5://127.0.0.1:9050'
                }
                resp = requests.get(
                    'https://check.torproject.org/api/ip',
                    proxies=proxies,
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('IsTor'):
                        print(f"[Tor] ✓ Working! IP: {data.get('IP')}")
                        return True
            except:
                pass
        
        return False
    except:
        return False


def get_best_anonymity_method():
    """Determine best anonymity method available"""
    methods = []
    
    # Check Tor
    if check_tor_status():
        methods.append({
            'name': 'Tor',
            'type': 'tor',
            'proxy': 'socks5://127.0.0.1:9050',
            'priority': 1
        })
    
    # Check VPN
    vpn_mgr = VPNProxyManager()
    vpn = vpn_mgr.check_vpn_running()
    if vpn:
        methods.append({
            'name': vpn,
            'type': 'vpn',
            'priority': 2
        })
    
    # Fetch working proxies
    print("[*] Fetching working proxies...")
    proxy_mgr = VPNProxyManager()
    proxy_mgr.test_proxies_parallel(max_to_test=200)
    
    if proxy_mgr.working_proxies:
        methods.append({
            'name': 'Proxy',
            'type': 'proxy',
            'proxy': proxy_mgr.working_proxies[0],
            'priority': 3,
            'manager': proxy_mgr
        })
    
    if methods:
        methods.sort(key=lambda x: x['priority'])
        print(f"\n[+] Available anonymity methods:")
        for m in methods:
            print(f"    {m['priority']}. {m['name']} ({m['type']})")
        
        return methods[0]
    
    return None


if __name__ == "__main__":
    print("="*60)
    print("  VPN & PROXY MANAGER")
    print("="*60)
    
    # Check what's available
    print("\n[*] Checking available methods...")
    
    # Check Tor
    print("\n1. Checking Tor...")
    if check_tor_status():
        print("   ✓ Tor is working")
    else:
        print("   ✗ Tor not available")
        print("   Install: sudo apt install tor && sudo service tor start")
    
    # Check VPN
    print("\n2. Checking VPN...")
    vpn_mgr = VPNProxyManager()
    vpn = vpn_mgr.check_vpn_running()
    if vpn:
        print(f"   ✓ VPN detected: {vpn}")
    else:
        print("   ✗ No VPN detected")
        print("   Recommended free VPNs:")
        for vpn_id, vpn_info in FREE_VPNS.items():
            print(f"     - {vpn_info['name']}: {vpn_info['install']} (Free: {vpn_info['data_limit']})")
    
    # Test proxies
    print("\n3. Testing proxies...")
    proxy_mgr = VPNProxyManager()
    working = proxy_mgr.test_proxies_parallel(max_to_test=100)
    print(f"   ✓ Found {len(working)} working proxies")
    
    print("\n" + "="*60)
    print("  Ready to use!")
    print("="*60)
