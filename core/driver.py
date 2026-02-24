"""
Driver module — plain Selenium + Chrome/Chromium.
No undetected_chromedriver, no SSL patcher headaches.
"""

import os
import shutil
import subprocess
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from utils.human import StealthMode
from utils.tor import get_random_user_agent
from utils.vpn_proxy import check_tor_status


def _find_chrome_binary():
    """Find the Chrome/Chromium binary."""
    candidates = [
        'chromium-browser', 'chromium', 'google-chrome', 'google-chrome-stable',
    ]
    for name in candidates:
        path = shutil.which(name)
        if path:
            return path

    # Check absolute paths (WSL + Linux)
    for path in [
        "/usr/bin/chromium-browser", "/usr/bin/chromium",
        "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
        "/snap/bin/chromium",
        "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
    ]:
        if os.path.exists(path):
            return path
    return None


def _find_chromedriver():
    """Find chromedriver in PATH or common locations."""
    path = shutil.which("chromedriver")
    if path:
        return path
    for p in [
        "/usr/bin/chromedriver", "/usr/local/bin/chromedriver",
        os.path.expanduser("~/.local/share/undetected_chromedriver/chromedriver"),
        os.path.expanduser("~/.local/bin/chromedriver"),
    ]:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def create_driver(headless=False, proxy=None, use_tor=False, use_vpn=False, user_data_dir=None):
    """Create a Selenium Chrome driver with stealth settings."""
    user_agent = get_random_user_agent()
    print(f"[Driver] User Agent: {user_agent[:60]}...")

    options = Options()

    # Stealth flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=en-US")
    options.add_argument(f"--user-agent={user_agent}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

    if user_data_dir:
        os.makedirs(user_data_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={user_data_dir}")

    # Tor proxy
    if use_tor and check_tor_status():
        print("[Driver] ✓ Routing through Tor")
        options.add_argument("--proxy-server=socks5://127.0.0.1:9050")

    # Set binary location if not default
    chrome_bin = _find_chrome_binary()
    if chrome_bin:
        options.binary_location = chrome_bin
        print(f"[Driver] Chrome binary: {chrome_bin}")
    else:
        print("[Driver] ⚠ No Chrome binary found, hoping default works...")

    # Find chromedriver
    chromedriver = _find_chromedriver()
    if chromedriver:
        print(f"[Driver] Chromedriver: {chromedriver}")
        service = Service(executable_path=chromedriver)
    else:
        print("[Driver] Chromedriver not found, using selenium-manager auto-download...")
        service = Service()

    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)

    # Inject stealth JS
    StealthMode.inject_stealth_js(driver)

    return driver
