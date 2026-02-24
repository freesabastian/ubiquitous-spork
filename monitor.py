#!/usr/bin/env python3
"""
Resource Monitor for VPS
Shows memory and CPU usage while running instances
"""

import time
import os

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def monitor(refresh=2):
    """Monitor resources"""
    
    try:
        import psutil
        has_psutil = True
    except ImportError:
        has_psutil = False
        print("Install psutil for monitoring: pip install psutil")
        return
    
    print("Resource Monitor - Press Ctrl+C to stop\n")
    
    try:
        while True:
            clear()
            
            # CPU
            cpu = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(percpu=True)
            
            # Memory
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Display
            print("=" * 50)
            print("  RESOURCE MONITOR")
            print("=" * 50)
            print()
            
            print(f"CPU Usage:    {cpu:.1f}%")
            print(f"CPU Cores:    {len(cpu_per_core)}")
            print(f"  " + " ".join([f"{c:4.0f}%" for c in cpu_per_core]))
            print()
            
            print(f"RAM:          {mem.used/(1024**3):.1f} / {mem.total/(1024**3):.1f} GB ({mem.percent}%)")
            print(f"  Available:  {mem.available/(1024**3):.1f} GB")
            print()
            
            print(f"Swap:         {swap.used/(1024**3):.1f} / {swap.total/(1024**3):.1f} GB ({swap.percent}%)")
            print()
            
            # Chrome processes
            chrome_count = 0
            chrome_mem = 0
            for proc in psutil.process_iter(['name', 'memory_info']):
                try:
                    if 'chrome' in proc.info['name'].lower():
                        chrome_count += 1
                        chrome_mem += proc.info['memory_info'].rss
                except:
                    pass
            
            print(f"Chrome:       {chrome_count} processes")
            print(f"  Memory:     {chrome_mem/(1024**3):.2f} GB")
            print()
            
            # Python processes
            python_count = 0
            python_mem = 0
            for proc in psutil.process_iter(['name', 'memory_info', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower():
                        python_count += 1
                        python_mem += proc.info['memory_info'].rss
                except:
                    pass
            
            print(f"Python:       {python_count} processes")
            print(f"  Memory:     {python_mem/(1024**3):.2f} GB")
            print()
            
            # Recommendations
            print("=" * 50)
            
            if mem.percent > 85:
                print("  ⚠️  HIGH RAM USAGE - Consider reducing instances")
            elif mem.percent > 70:
                print("  ⚠️  Moderate RAM usage - Monitor closely")
            else:
                print("  ✅ RAM usage OK")
            
            if swap.percent > 50:
                print("  ⚠️  High swap usage - May slow down")
            
            print("=" * 50)
            print("\n  Refreshing in {} seconds...".format(refresh))
            
            time.sleep(refresh)
            
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", type=int, default=2, help="Refresh interval")
    args = parser.parse_args()
    
    monitor(args.refresh)
