import requests
import random
import time
import concurrent.futures

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
]

TEST_URLS = [
    "http://httpbin.org/ip",
    "http://ip-api.com/json",
    "https://api.ipify.org?format=json",
]

TIMEOUT = 5


class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.current_index = 0
    
    def fetch_proxies(self):
        """Fetch free proxies from multiple sources"""
        print("[Proxy] Fetching proxy lists...")
        all_proxies = set()
        
        for source in PROXY_SOURCES:
            try:
                resp = requests.get(source, timeout=10)
                if resp.status_code == 200:
                    lines = resp.text.strip().split('\n')
                    count = 0
                    for line in lines:
                        line = line.strip()
                        if ':' in line and len(line) < 25:
                            parts = line.split(':')
                            if len(parts) == 2:
                                try:
                                    int(parts[1])  # Validate port is number
                                    all_proxies.add(line)
                                    count += 1
                                except:
                                    pass
                    print(f"[Proxy] Got {count} from {source.split('/')[-1]}")
            except Exception as e:
                print(f"[Proxy] Error {source.split('/')[-1]}: {str(e)[:30]}")
        
        self.proxies = list(all_proxies)
        random.shuffle(self.proxies)
        print(f"[Proxy] Total fetched: {len(self.proxies)}")
        return self.proxies
    
    def test_single_proxy(self, proxy_str):
        """Test if a single proxy is working"""
        try:
            proxies = {
                'http': f'http://{proxy_str}',
                'https': f'http://{proxy_str}'
            }
            test_url = random.choice(TEST_URLS)
            start = time.time()
            resp = requests.get(test_url, proxies=proxies, timeout=TIMEOUT)
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                return (proxy_str, True, elapsed)
        except:
            pass
        return (proxy_str, False, 999)
    
    def test_proxies_parallel(self, max_workers=100, max_to_test=300):
        """Test proxies in parallel, return working ones sorted by speed"""
        if not self.proxies:
            self.fetch_proxies()
        
        to_test = self.proxies[:max_to_test]
        print(f"[Proxy] Testing {len(to_test)} proxies in parallel...")
        
        working = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.test_single_proxy, p): p for p in to_test}
            
            done = 0
            for future in concurrent.futures.as_completed(futures):
                done += 1
                proxy_str, is_working, elapsed = future.result()
                
                if is_working:
                    working.append((proxy_str, elapsed))
                    print(f"[Proxy] ✓ {proxy_str} ({elapsed:.2f}s)")
                
                if done % 50 == 0:
                    print(f"[Proxy] Progress: {done}/{len(to_test)}, working: {len(working)}")
        
        # Sort by speed (fastest first)
        working.sort(key=lambda x: x[1])
        self.working_proxies = [p[0] for p in working]
        
        print(f"[Proxy] ✓ Found {len(self.working_proxies)} working proxies")
        return self.working_proxies
    
    def get_working_proxy(self):
        """Get next working proxy from tested list"""
        if not self.working_proxies:
            self.test_proxies_parallel()
        
        if self.current_index >= len(self.working_proxies):
            print("[Proxy] Ran out of proxies, fetching new ones...")
            self.working_proxies = []
            self.test_proxies_parallel()
            self.current_index = 0
        
        if self.working_proxies:
            proxy = self.working_proxies[self.current_index]
            self.current_index += 1
            print(f"[Proxy] Using: {proxy}")
            return proxy
        
        print("[Proxy] No working proxies available!")
        return None
    
    def get_fastest_proxy(self):
        """Get the fastest working proxy"""
        if not self.working_proxies:
            self.test_proxies_parallel()
        
        if self.working_proxies:
            return self.working_proxies[0]
        return None
    
    def remove_bad_proxy(self, proxy):
        """Remove a proxy that failed during use"""
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            print(f"[Proxy] Removed bad: {proxy}")
    
    def list_working(self):
        """List all working proxies"""
        if not self.working_proxies:
            self.test_proxies_parallel()
        
        print(f"\n[Proxy] Working proxies ({len(self.working_proxies)}):")
        for i, p in enumerate(self.working_proxies[:20]):
            print(f"  {i+1}. {p}")
        if len(self.working_proxies) > 20:
            print(f"  ... and {len(self.working_proxies) - 20} more")
        
        return self.working_proxies


def get_good_proxy():
    """Get a single tested working proxy"""
    pm = ProxyManager()
    return pm.get_working_proxy()


def get_fastest_proxy():
    """Get the fastest working proxy"""
    pm = ProxyManager()
    return pm.get_fastest_proxy()


def get_multiple_proxies(count=5):
    """Get multiple working proxies"""
    pm = ProxyManager()
    pm.test_proxies_parallel()
    return pm.working_proxies[:count]
