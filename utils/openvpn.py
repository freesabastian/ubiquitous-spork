#!/usr/bin/env python3
"""
OpenVPN Manager with Credentials
Manages VPN pool with username/password
"""

import os
import random
import subprocess
import time
import tempfile
import shutil
from collections import deque

VPN_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vpns", "cmt")
FAILED_VPNS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "failed_vpns.txt")
RECENT_VPNS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "recent_vpns.txt")
RECENT_VPNS_MAX = 10

DEFAULT_CREDENTIALS = {
    'username': '0yqflkJmsb5Xr6Rz',
    'password': 'Z1zZ0ikBbZJ5IE5imnJwbWFvOneuYINO'
}


class OpenVPNManager:
    
    def __init__(self, config_dir=None, username=None, password=None, instance_id=0):
        self.config_dir = config_dir or VPN_CONFIG_DIR
        self.username = username or DEFAULT_CREDENTIALS['username']
        self.password = password or DEFAULT_CREDENTIALS['password']
        self.instance_id = instance_id
        self.dev = f"tun{instance_id}"
        self.failed_vpns = set()
        self.recent_vpns = deque(maxlen=RECENT_VPNS_MAX)
        self.current_vpn = None
        self.current_process = None
        self.cred_file = None
        self.current_config = None
        
        self._load_failed_vpns()
        self._load_recent_vpns()
    
    def _load_failed_vpns(self):
        try:
            if os.path.exists(FAILED_VPNS_FILE):
                with open(FAILED_VPNS_FILE, 'r') as f:
                    for line in f:
                        vpn = line.strip()
                        if vpn:
                            self.failed_vpns.add(vpn)
        except:
            pass
    
    def _save_failed_vpn(self, vpn_name):
        self.failed_vpns.add(vpn_name)
        try:
            os.makedirs(os.path.dirname(FAILED_VPNS_FILE), exist_ok=True)
            with open(FAILED_VPNS_FILE, 'a') as f:
                f.write(f"{vpn_name}\n")
        except:
            pass
    
    def _load_recent_vpns(self):
        try:
            if os.path.exists(RECENT_VPNS_FILE):
                with open(RECENT_VPNS_FILE, 'r') as f:
                    for line in f:
                        vpn = line.strip()
                        if vpn and vpn not in self.recent_vpns:
                            self.recent_vpns.append(vpn)
        except:
            pass
    
    def _save_recent_vpns(self):
        try:
            os.makedirs(os.path.dirname(RECENT_VPNS_FILE), exist_ok=True)
            with open(RECENT_VPNS_FILE, 'w') as f:
                for vpn in self.recent_vpns:
                    f.write(f"{vpn}\n")
        except:
            pass
    
    def _add_recent_vpn(self, vpn_name):
        if vpn_name in self.recent_vpns:
            self.recent_vpns.remove(vpn_name)
        self.recent_vpns.append(vpn_name)
        self._save_recent_vpns()
    
    def get_available_vpns(self, exclude_recent=True):
        if not os.path.exists(self.config_dir):
            print(f"[VPN] Config dir not found: {self.config_dir}")
            return []
        
        vpns = []
        for f in os.listdir(self.config_dir):
            if f.endswith('.ovpn'):
                if f not in self.failed_vpns:
                    if exclude_recent and f in self.recent_vpns:
                        continue
                    vpns.append(f)
        
        return vpns
    
    def pick_random_vpn(self):
        vpns = self.get_available_vpns(exclude_recent=True)
        
        if not vpns:
            vpns = self.get_available_vpns(exclude_recent=False)
            if vpns:
                print("[VPN] Only recent VPNs available, reusing one...")
        
        if not vpns:
            print("[VPN] All VPNs have failed! Resetting failed list...")
            self.failed_vpns.clear()
            if os.path.exists(FAILED_VPNS_FILE):
                os.remove(FAILED_VPNS_FILE)
            vpns = self.get_available_vpns(exclude_recent=True)
        
        if vpns:
            return random.choice(vpns)
        
        return None
    
    def _create_credentials_file(self):
        """Create temporary credentials file"""
        fd, path = tempfile.mkstemp(suffix='.txt', prefix='vpn_creds_')
        with os.fdopen(fd, 'w') as f:
            f.write(f"{self.username}\n")
            f.write(f"{self.password}\n")
        
        # Ensure root/openvpn can read it
        os.chmod(path, 0o644) 
        self.cred_file = path
        return path
    
    def _cleanup_credentials(self):
        """Remove credentials file"""
        if self.cred_file and os.path.exists(self.cred_file):
            try:
                # Use sudo to remove in case it was modified by root
                subprocess.run(['sudo', 'rm', '-f', self.cred_file], capture_output=True)
            except:
                pass
            self.cred_file = None
    
    def _prepare_config(self, vpn_file):
        """Prepare config file with credentials and unique device"""
        vpn_path = os.path.join(self.config_dir, vpn_file)
        
        # Read original config
        with open(vpn_path, 'r') as f:
            config = f.read()
        
        # Create credentials file
        cred_path = self._create_credentials_file()
        
        # Modify config
        import re
        
        # Replace auth-user-pass line
        config = re.sub(
            r'^auth-user-pass\s*$',
            f'auth-user-pass {cred_path}',
            config,
            flags=re.MULTILINE
        )
        
        # If no auth-user-pass, add it
        if 'auth-user-pass' not in config:
            config += f"\nauth-user-pass {cred_path}\n"
            
        # Add unique device to avoid conflict
        # Remove any existing dev line and add our specific one
        config = re.sub(r'^dev\s+.*$', '', config, flags=re.MULTILINE)
        config += f"\ndev {self.dev}\n"
        
        # Disable route-delay to speed up
        if 'route-delay' not in config:
            config += "\nroute-delay 0\n"
        
        # Create temp config file
        fd, temp_config = tempfile.mkstemp(suffix='.ovpn', prefix='vpn_config_')
        with os.fdopen(fd, 'w') as f:
            f.write(config)
        
        # Ensure root/openvpn can read it
        os.chmod(temp_config, 0o644)
        
        self.current_config = temp_config
        return temp_config
    
    def connect(self, vpn_file=None):
        """Connect to OpenVPN"""
        if vpn_file is None:
            vpn_file = self.pick_random_vpn()
        
        if not vpn_file:
            print("[VPN] No VPN configs available!")
            return False
        
        vpn_path = os.path.join(self.config_dir, vpn_file)
        
        if not os.path.exists(vpn_path):
            print(f"[VPN] Config not found: {vpn_file}")
            return False
        
        # Disconnect any existing VPN for THIS instance
        self.disconnect()
        
        print(f"[VPN Instance {self.instance_id}] Connecting to: {vpn_file} using {self.dev}")
        
        temp_config = None
        
        try:
            # Prepare config with credentials
            temp_config = self._prepare_config(vpn_file)
            
            # Start OpenVPN with unique pid file
            pid_file = f"/tmp/openvpn_instance_{self.instance_id}.pid"
            self.current_process = subprocess.Popen(
                ['sudo', 'openvpn', '--config', temp_config, '--writepid', pid_file, '--daemon']
            )
            
            # Wait for connection
            print(f"[VPN Instance {self.instance_id}] Waiting for connection...")
            
            for _ in range(45): # Wait up to 45s
                if self.is_connected():
                    self.current_vpn = vpn_file
                    self._add_recent_vpn(vpn_file)
                    print(f"[VPN Instance {self.instance_id}] ✓ Connected!")
                    return True
                time.sleep(1)
            
            # Timeout is NOT a permanent failure — server might just be slow
            print(f"[VPN Instance {self.instance_id}] ✗ Timeout connecting to: {vpn_file}")
            self.disconnect()  # Clean up, but DON'T mark as failed
            return False
                
        except Exception as e:
            print(f"[VPN Instance {self.instance_id}] Error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect OpenVPN for THIS instance only"""
        pid_file = f"/tmp/openvpn_instance_{self.instance_id}.pid"
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                if pid:
                    print(f"[VPN Instance {self.instance_id}] Killing PID {pid}...")
                    subprocess.run(['sudo', 'kill', pid], capture_output=True)
                    time.sleep(1)
                    # Force kill if still alive
                    subprocess.run(['sudo', 'kill', '-9', pid], capture_output=True)
                os.remove(pid_file)
            except:
                pass
        
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process = None
            except:
                pass
        
        # Remove tun interface to prevent zombie tunnels
        try:
            subprocess.run(
                ['sudo', 'ip', 'link', 'delete', self.dev],
                capture_output=True, timeout=5
            )
        except:
            pass
        
        # Cleanup credentials file
        self._cleanup_credentials()
        
        # Cleanup temporary config file
        if self.current_config and os.path.exists(self.current_config):
            try:
                os.remove(self.current_config)
            except:
                pass
            self.current_config = None
            
        self.current_vpn = None
    
    @staticmethod
    def full_cleanup():
        """Nuclear cleanup — kill ALL openvpn, remove ALL tun, flush iptables.
        Call this on script exit to prevent zombie VPNs from killing network."""
        print("[VPN] Full cleanup...")
        # Kill all openvpn
        subprocess.run(['sudo', 'killall', 'openvpn'], capture_output=True)
        # Remove all tun interfaces
        try:
            result = subprocess.run(
                ['ip', '-o', 'link', 'show'], capture_output=True, text=True
            )
            for line in result.stdout.split('\n'):
                if 'tun' in line:
                    dev = line.split(':')[1].strip().split('@')[0]
                    subprocess.run(['sudo', 'ip', 'link', 'delete', dev], capture_output=True)
                    print(f"[VPN] Removed {dev}")
        except:
            pass
        # Flush iptables to remove VPN kill-switch rules
        subprocess.run(['sudo', 'iptables', '-F'], capture_output=True)
        subprocess.run(['sudo', 'iptables', '-X'], capture_output=True)
        subprocess.run(['sudo', 'iptables', '-t', 'nat', '-F'], capture_output=True)
        subprocess.run(['sudo', 'iptables', '-P', 'INPUT', 'ACCEPT'], capture_output=True)
        subprocess.run(['sudo', 'iptables', '-P', 'FORWARD', 'ACCEPT'], capture_output=True)
        subprocess.run(['sudo', 'iptables', '-P', 'OUTPUT', 'ACCEPT'], capture_output=True)
        # Clean up pid files
        for f in os.listdir('/tmp'):
            if f.startswith('openvpn_instance_') and f.endswith('.pid'):
                try:
                    os.remove(os.path.join('/tmp', f))
                except:
                    pass
        print("[VPN] Cleanup done.")
    
    def is_connected(self):
        """Check if THIS instance's VPN is connected"""
        try:
            # Check for our specific interface
            result = subprocess.run(
                ['ip', 'addr', 'show', self.dev],
                capture_output=True,
                text=True
            )
            if self.dev in result.stdout and 'inet ' in result.stdout:
                return True
        except:
            pass
        return False
    
    def mark_failed(self, vpn_file):
        """Mark a VPN as failed"""
        print(f"[VPN Instance {self.instance_id}] Marking as failed: {vpn_file}")
        self._save_failed_vpn(vpn_file)
        self.failed_vpns.add(vpn_file)
        self.disconnect()
    
    def get_ip(self):
        """Get current public IP through this VPN interface"""
        # This is tricky because requests will use the default route.
        # To truly test THIS VPN, we'd need to use 'curl --interface tunX'
        try:
            result = subprocess.run(
                ['curl', '--silent', '--interface', self.dev, 'https://api.ipify.org?format=json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            import json
            return json.loads(result.stdout).get('ip')
        except:
            pass
        return None

    
    def status(self):
        return {
            'connected': self.is_connected(),
            'current_vpn': self.current_vpn,
            'available': len(self.get_available_vpns(exclude_recent=True)),
            'failed': len(self.failed_vpns),
            'recent': len(self.recent_vpns),
            'ip': self.get_ip() if self.is_connected() else None
        }


def list_available_vpns():
    mgr = OpenVPNManager()
    vpns = mgr.get_available_vpns(exclude_recent=True)
    
    print(f"\nAvailable VPNs: {len(vpns)} (excluding {len(mgr.recent_vpns)} recent)")
    print("-" * 50)
    
    for i, vpn in enumerate(vpns, 1):
        print(f"  {i:3d}. {vpn}")
    
    if mgr.recent_vpns:
        print(f"\nRecent VPNs (skipped): {', '.join(mgr.recent_vpns)}")
    
    if mgr.failed_vpns:
        print(f"\nFailed VPNs: {len(mgr.failed_vpns)}")
    
    return vpns


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenVPN Manager")
    parser.add_argument('--list', action='store_true', help='List available VPNs')
    parser.add_argument('--connect', type=str, help='Connect to specific VPN')
    parser.add_argument('--disconnect', action='store_true', help='Disconnect VPN')
    parser.add_argument('--status', action='store_true', help='Show VPN status')
    parser.add_argument('--username', type=str, help='VPN username')
    parser.add_argument('--password', type=str, help='VPN password')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_vpns()
    
    elif args.connect:
        mgr = OpenVPNManager(username=args.username, password=args.password)
        if mgr.connect(args.connect):
            print("\nConnected! Press Ctrl+C to disconnect...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                mgr.disconnect()
    
    elif args.disconnect:
        mgr = OpenVPNManager()
        mgr.disconnect()
    
    elif args.status:
        mgr = OpenVPNManager()
        status = mgr.status()
        print(f"\nVPN Status:")
        print(f"  Connected: {status['connected']}")
        print(f"  Current:   {status['current_vpn']}")
        print(f"  Available: {status['available']}")
        print(f"  Recent:    {status['recent']} (excluded)")
        print(f"  Failed:    {status['failed']}")
        if status['ip']:
            print(f"  IP:        {status['ip']}")
    
    else:
        parser.print_help()
