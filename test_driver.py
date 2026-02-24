#!/usr/bin/env python3
"""Quick smoke test for driver creation (headless + normal modes)."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.driver import create_driver

# ── Test 1: Headless ──────────────────────────────────────────
print("\n[TEST 1] Headless mode...")
try:
    d = create_driver(headless=True)
    d.get("https://www.google.com")
    print(f"[TEST 1] ✓ PASS — Title: {d.title}")
    d.quit()
except Exception as e:
    print(f"[TEST 1] ✗ FAIL — {e}")
    import traceback; traceback.print_exc()

# ── Test 2: Normal mode (needs DISPLAY / Xvfb) ───────────────
print("\n[TEST 2] Normal mode (with Xvfb)...")
display = os.environ.get("DISPLAY")
if not display:
    print("[TEST 2] No DISPLAY — starting Xvfb...")
    import subprocess, time
    xvfb = subprocess.Popen(
        ["Xvfb", ":99", "-screen", "0", "1920x1080x24"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    os.environ["DISPLAY"] = ":99"
    time.sleep(2)
else:
    xvfb = None
    print(f"[TEST 2] Using DISPLAY={display}")

try:
    d = create_driver(headless=False)
    d.get("https://www.google.com")
    print(f"[TEST 2] ✓ PASS — Title: {d.title}")
    d.quit()
except Exception as e:
    print(f"[TEST 2] ✗ FAIL — {e}")
    import traceback; traceback.print_exc()
finally:
    if xvfb:
        xvfb.terminate()

print("\n[DONE] All tests finished.")
