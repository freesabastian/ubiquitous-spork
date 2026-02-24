#!/usr/bin/env python3
"""
Multi-Instance Runner
Spawns multiple main.py processes in parallel, each with its own VPN.
"""

import sys
import os
import time
import subprocess
import argparse
import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_multi_instance(num_instances=2, headless=True, max_retries=10, use_vpn=False, loops=1):
    """Spawn multiple main.py processes in parallel."""
    print("\n" + "=" * 60)
    print("  MULTI-INSTANCE RUNNER")
    print("=" * 60)
    print(f"  Instances: {num_instances}")
    print(f"  Headless:  {headless}")
    print(f"  VPN:       {'Yes' if use_vpn else 'No'}")
    print(f"  Loops:     {loops}")
    print("=" * 60 + "\n")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(script_dir, "main.py")

    processes = []
    start_time = time.time()

    def cleanup_all():
        """Kill all child processes and clean up VPN/network."""
        print("\n[*] Cleaning up all instances...")
        for inst_id, p in processes:
            try:
                p.terminate()
            except:
                pass
        for inst_id, p in processes:
            try:
                p.wait(timeout=5)
            except:
                try:
                    p.kill()
                except:
                    pass

        # Clean up zombie chrome processes
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe', '/T'], capture_output=True)
            else:
                subprocess.run(['pkill', '-f', 'chromedriver'], capture_output=True)
                subprocess.run(['pkill', '-f', 'chromium'], capture_output=True)
        except:
            pass

        # Full VPN + network cleanup to prevent zombie tun/iptables
        if use_vpn:
            try:
                from utils.openvpn import OpenVPNManager
                OpenVPNManager.full_cleanup()
            except Exception as e:
                print(f"[*] VPN cleanup error: {e}")

    for i in range(num_instances):
        # Build command for each instance
        cmd = [sys.executable, main_py]
        
        if headless:
            cmd.append("--headless")
        if use_vpn:
            cmd.append("-v")
        if loops > 1:
            cmd.extend(["-l", str(loops)])
        cmd.extend(["--max-retries", str(max_retries)])
        
        # Set a unique VPN instance ID via environment variable
        # Instance IDs start at 1 so tun0 stays free for manual use
        env = os.environ.copy()
        env["BUDDY_INSTANCE_ID"] = str(i + 1)
        
        print(f"[*] Starting instance {i + 1}: {' '.join(cmd)}")
        p = subprocess.Popen(
            cmd,
            cwd=script_dir,
            env=env,
        )
        processes.append((i + 1, p))
        
        # Stagger starts so VPN connections don't collide
        if i < num_instances - 1:
            wait_time = 30 if use_vpn else 10
            print(f"[*] Waiting {wait_time}s before next instance...")
            time.sleep(wait_time)

    print(f"\n[*] All {num_instances} instances running.")
    print("[*] Press Ctrl+C to stop all.\n")

    try:
        for inst_id, p in processes:
            p.wait()
            print(f"[*] Instance {inst_id} finished (exit code {p.returncode})")
    except KeyboardInterrupt:
        print("\n[!] Interrupted!")
        cleanup_all()
    else:
        # Normal exit — still clean up VPNs
        if use_vpn:
            try:
                from utils.openvpn import OpenVPNManager
                OpenVPNManager.full_cleanup()
            except:
                pass

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("  ALL INSTANCES COMPLETE")
    print(f"  Time: {elapsed/60:.1f} minutes")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Instance Buddy Bot")
    parser.add_argument("--instances", type=int, default=2, help="Number of parallel instances")
    parser.add_argument("--headless", action="store_true", default=False, help="Headless mode")
    parser.add_argument("--max-retries", type=int, default=10, help="Max retries per instance")
    parser.add_argument("-v", "--vpn", action="store_true", help="Use VPN rotation")
    parser.add_argument("-l", "--loops", type=int, default=1, help="Loops per instance")

    args = parser.parse_args()
    run_multi_instance(args.instances, args.headless, args.max_retries, args.vpn, args.loops)
