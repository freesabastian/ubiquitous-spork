#!/usr/bin/env python3
"""
Buddy Works Full Automation
With VPN rotation on captcha/flag failures
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.driver import create_driver
from pages.email_page import EmailPage
from pages.buddy_page import BuddySignupPage, RestartException, CaptchaFailedException
from utils.storage import add_account
from utils.human import HumanBehavior
from utils.proxy import ProxyManager
from utils.openvpn import OpenVPNManager
from utils.tor import get_random_user_agent
from config import DEFAULT_PASSWORD


def run_single_attempt(driver, email_page, buddy_page, email):
    """Run a single signup attempt. Returns result or raises exception."""
    human = HumanBehavior(driver)
    
    # Switch to email tab
    driver.switch_to.window(driver.window_handles[0])
    
    print(f"\n[*] Using email: {email}")
    
    # Switch to buddy tab
    driver.switch_to.window(driver.window_handles[1])
    
    # Start signup
    print("[*] Clicking Bitbucket button...")
    buddy_page.click_bitbucket()
    
    print("[*] Filling email on Atlassian page...")
    buddy_page.fill_atlassian_email(email)
    
    print("[*] Clicking login/continue...")
    buddy_page.click_login_submit()
    
    # This handles captcha AND clicks button again after captcha
    # Raises CaptchaFailedException if OTP inputs don't appear (VPN flagged or captcha failed)
    print("[*] Checking for signup button (and captcha)...")
    buddy_page.click_signup_submit()
    
    # ONLY NOW switch to temp mail - OTP inputs confirmed visible
    print("\n[*] Switching to temp mail tab...")
    driver.switch_to.window(driver.window_handles[0])
    
    human.random_page_interaction()
    
    print("[*] Monitoring for verification email (up to 2 minutes)...")
    code = email_page.get_verification_code(timeout=120)
    print(f"\n[+] Code: {code}\n")
    
    # Go back to buddy and enter code
    print("[*] Switching back to buddy.works...")
    driver.switch_to.window(driver.window_handles[1])
    
    print("[*] Filling OTP code...")
    buddy_page.fill_otp(code)
    
    print("[*] Clicking verify...")
    buddy_page.click_verify()
    
    print("[*] Filling display name...")
    buddy_page.fill_display_name()
    
    print("[*] Filling password...")
    buddy_page.fill_password(DEFAULT_PASSWORD)
    
    print("[*] Clicking continue...")
    buddy_page.click_continue()
    
    print("[*] Signup complete!")
    
    human.thinking_pause()
    
    # Create project with None provider (handles Grant Access)
    print("\n[*] Selecting None provider...")
    buddy_page.select_none_provider()
    
    print("[*] Filling project name...")
    buddy_page.fill_project_name()
    
    print("[*] Creating project...")
    buddy_page.click_create_project()
    
    # Create sandbox
    print("\n[*] Going to Sandboxes...")
    buddy_page.go_to_sandboxes()
    
    print("[*] Creating new sandbox...")
    buddy_page.click_new_sandbox()
    
    print("[*] Filling sandbox name...")
    buddy_page.fill_sandbox_name()
    
    print("[*] Submitting sandbox...")
    buddy_page.submit_sandbox()
    
    # Setup terminal
    print("\n[*] Opening terminal...")
    buddy_page.click_terminal_button()
    
    print("[*] Running setup commands...")
    buddy_page.setup_sandbox()
    
    # Save
    result = {
        "email": email,
        "password": DEFAULT_PASSWORD,
        "project": buddy_page.project_name,
        "sandbox": buddy_page.sandbox_name
    }
    add_account(**result)
    
    return result


def run_automation(headless=False, max_retries=10, use_vpn=False, use_tor=False, use_proxy=False, 
                   vpn_user=None, vpn_pass=None, loop_mode=False):
    print("\n" + "=" * 60)
    print("  BUDDY WORKS AUTOMATION")
    print("  VPN Rotation on Failure")
    print("=" * 60)
    
    if use_vpn:
        print("  Mode: VPN rotation (changes VPN on failure)")
    elif use_tor:
        print("  Mode: Tor")
    elif use_proxy:
        print("  Mode: Proxy")
    else:
        print("  Mode: Direct (no VPN)")
    
    print("=" * 60 + "\n")
    
    driver = None
    vpn_mgr = None
    proxy = None
    
    # Setup VPN if requested
    if use_vpn:
        instance_id = int(os.environ.get("BUDDY_INSTANCE_ID", "0"))
        vpn_mgr = OpenVPNManager(username=vpn_user, password=vpn_pass, instance_id=instance_id)
        vpns = vpn_mgr.get_available_vpns()
        
        if not vpns:
            print("[!] No VPN configs found!")
            print(f"[!] Add .ovpn files to: {vpn_mgr.config_dir}")
            print("[!] Continuing without VPN...")
            use_vpn = False
        else:
            print(f"[*] Available VPNs: {len(vpns)}")
    
    # Setup proxy if requested
    if use_proxy:
        pm = ProxyManager()
        proxy = pm.get_working_proxy()
        if not proxy:
            print("[!] No working proxy found")
            use_proxy = False
    
    total_attempts = 0
    vpn_attempts = 0
    max_vpn_attempts = 3  # Max attempts per VPN
    
    while total_attempts < max_retries:
        total_attempts += 1
        vpn_attempts += 1
        
        print(f"\n{'='*60}")
        print(f"  TOTAL ATTEMPT #{total_attempts}/{max_retries}")
        if use_vpn and vpn_mgr and vpn_mgr.current_vpn:
            print(f"  VPN: {vpn_mgr.current_vpn} (attempt {vpn_attempts}/{max_vpn_attempts})")
        print(f"{'='*60}\n")
        
        # Connect to VPN if needed
        if use_vpn and vpn_mgr:
            # Always ensure VPN is connected before browsing
            if not vpn_mgr.is_connected():
                if vpn_attempts > max_vpn_attempts:
                    print("\n[!] Max attempts on this VPN, switching to new one...")
                    if vpn_mgr.current_vpn:
                        vpn_mgr.mark_failed(vpn_mgr.current_vpn)
                    vpn_mgr.disconnect()
                    vpn_attempts = 0
                
                print("[*] Connecting to VPN...")
                if not vpn_mgr.connect():
                    print("[!] Failed to connect to VPN!")
                    continue
                
                print(f"[*] VPN IP: {vpn_mgr.get_ip()}")
        
        try:
            # Close existing browser
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
            
            # Create new browser with new user agent
            print("\n[*] Creating browser instance...")
            user_agent = get_random_user_agent()
            print(f"[*] User Agent: {user_agent[:50]}...")
            
            driver = create_driver(
                headless=headless,
                proxy=proxy,
                use_tor=use_tor,
                use_vpn=use_vpn
            )
            driver.implicitly_wait(5)
            
            # Open pages
            print("\n[*] Opening temp mail...")
            email_page = EmailPage(driver)
            email_page.open()
            
            print("[*] Opening buddy.works...")
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            
            buddy_page = BuddySignupPage(driver)
            buddy_page.open()
            
            # Get email
            driver.switch_to.window(driver.window_handles[0])
            email = email_page.get_email()
            
            if not email:
                print("[!] Failed to get email, retrying...")
                driver.refresh()
                time.sleep(3)
                continue
            
            # Run signup attempt
            result = run_single_attempt(driver, email_page, buddy_page, email)
            
            # SUCCESS!
            print("\n" + "=" * 60)
            print("  AUTOMATION COMPLETE!")
            print("=" * 60)
            print(f"  Email:    {result['email']}")
            print(f"  Password: {result['password']}")
            print(f"  Project:  {result['project']}")
            print(f"  Sandbox:  {result['sandbox']}")
            print(f"  Attempts: {total_attempts}")
            if vpn_mgr and vpn_mgr.current_vpn:
                print(f"  VPN:      {vpn_mgr.current_vpn}")
            
            if loop_mode:
                print("\n  Loop mode: Closing browser for next iteration...")
                print("=" * 60 + "\n")
                if driver:
                    driver.quit()
                return result
            
            print("\n  Browser left open. Press Enter to close...")
            print("=" * 60 + "\n")
            
            input()
            
            if driver:
                driver.quit()
            
            return result
        
        except CaptchaFailedException as e:
            print(f"\n[!] CAPTCHA FAILED: {e}")
            print("[!] This VPN/IP is flagged or captcha didn't work")
            print("[!] Switching to NEW VPN and restarting...")
            
            # Mark VPN as failed
            if use_vpn and vpn_mgr and vpn_mgr.current_vpn:
                vpn_mgr.mark_failed(vpn_mgr.current_vpn)
                vpn_mgr.disconnect()
            
            # Reset for new VPN attempt
            vpn_attempts = max_vpn_attempts + 1  # Force new VPN
            continue
        
        except RestartException as e:
            print(f"\n[!] Restart needed: {e}")
            print("[*] Retrying with same VPN...")
            # Don't change VPN, just retry
            continue
        
        except Exception as e:
            error_msg = str(e)
            print(f"\n[!] Error: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if this is a critical error that needs new VPN
            critical_errors = [
                "NoSuchElementException",
                "TimeoutError",
                "NoSuchWindowException",
                "NoSuchFrameException",
                "StaleElementReferenceException",
                "ElementNotInteractableException",
            ]
            
            is_critical = any(err in error_msg for err in critical_errors)
            
            if is_critical:
                print(f"\n[!] Critical error detected - switching to NEW VPN!")
                if use_vpn and vpn_mgr and vpn_mgr.current_vpn:
                    vpn_mgr.mark_failed(vpn_mgr.current_vpn)
                    vpn_mgr.disconnect()
                vpn_attempts = max_vpn_attempts + 1  # Force new VPN
            
            print(f"\n[*] Retrying...")
            continue
    
    # Max retries reached
    print("\n" + "=" * 60)
    print("  MAX RETRIES REACHED")
    print("=" * 60)
    
    # ALWAYS clean up on exit
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    if vpn_mgr:
        vpn_mgr.disconnect()
    
    return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Buddy Works Automation")
    parser.add_argument("--headless", action="store_true", default=False, help="Headless mode")
    parser.add_argument("--email", type=str, help="Existing email")
    parser.add_argument("--code", type=str, help="Verification code")
    parser.add_argument("--max-retries", type=int, default=10, help="Max retries")
    parser.add_argument("-v", "--vpn", action="store_true", help="Use VPN (rotates on failure)")
    parser.add_argument("--tor", action="store_true", help="Use Tor")
    parser.add_argument("--proxy", action="store_true", help="Use free proxy")
    parser.add_argument("--vpn-list", action="store_true", help="List available VPNs")
    parser.add_argument("--vpn-user", type=str, help="VPN username")
    parser.add_argument("--vpn-pass", type=str, help="VPN password")
    parser.add_argument("-l", "--loops", type=int, help="Number of loops to run")
    
    args = parser.parse_args()
    
    if args.vpn_list:
        # List available VPNs
        from utils.openvpn import list_available_vpns
        list_available_vpns()
    
    elif args.email and args.code:
        # Run with existing email/code
        driver = None
        try:
            driver = create_driver(headless=args.headless, use_tor=args.tor)
            driver.implicitly_wait(5)
            
            buddy_page = BuddySignupPage(driver)
            buddy_page.open()
            
            buddy_page.click_bitbucket()
            buddy_page.fill_atlassian_email(args.email)
            buddy_page.click_login_submit()
            buddy_page.click_signup_submit()
            buddy_page.fill_otp(args.code)
            buddy_page.click_verify()
            buddy_page.fill_display_name()
            buddy_page.fill_password(DEFAULT_PASSWORD)
            buddy_page.click_continue()
            buddy_page.select_none_provider()
            buddy_page.fill_project_name()
            buddy_page.click_create_project()
            buddy_page.go_to_sandboxes()
            buddy_page.click_new_sandbox()
            buddy_page.fill_sandbox_name()
            buddy_page.submit_sandbox()
            buddy_page.click_terminal_button()
            buddy_page.setup_sandbox()
            
            result = {
                "email": args.email,
                "password": DEFAULT_PASSWORD,
                "project": buddy_page.project_name,
                "sandbox": buddy_page.sandbox_name
            }
            add_account(**result)
            
            print("\nSuccess!")
            input("Press Enter to close...")
            
        except Exception as e:
            print(f"Error: {e}")
            input("Press Enter to close...")
        finally:
            if driver:
                driver.quit()
    
    else:
        # Run full automation
        loop_count = 0
        max_loops = args.loops or 1
        is_looping = args.loops is not None
        
        success_count = 0
        
        while loop_count < max_loops:
            loop_count += 1
            if max_loops > 1:
                print(f"\n{'='*60}")
                print(f"  LOOP ITERATION #{loop_count}/{max_loops}")
                print(f"{'='*60}\n")
            
            result = run_automation(
                headless=args.headless,
                max_retries=args.max_retries,
                use_vpn=args.vpn,
                use_tor=args.tor,
                use_proxy=args.proxy,
                vpn_user=args.vpn_user,
                vpn_pass=args.vpn_pass,
                loop_mode=is_looping
            )
            
            if result:
                success_count += 1
            
            if loop_count < max_loops:
                print(f"\n[*] Loop {loop_count} finished. Waiting 25 seconds before next...")
                time.sleep(25)
            else:
                print(f"\n[*] Finished {max_loops} loops. Successes: {success_count}/{max_loops}")
                
        import sys
        if success_count > 0:
            print("[*] Completed successfully.")
            sys.exit(0)
        else:
            print("[!] All attempts failed.")
            sys.exit(1)

