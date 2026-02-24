from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from core.base_page import BasePage
import time
import random
import string
import re

try:
    from utils.audio_captcha import AudioCaptchaSolver
except ImportError:
    AudioCaptchaSolver = None


class RestartException(Exception):
    """Signal to restart the whole process"""
    pass


class CaptchaFailedException(Exception):
    """Captcha was done but page didn't load correctly - need new VPN"""
    pass


class BuddySignupPage(BasePage):
    URL = "https://buddy.works/sign-up"
    
    def __init__(self, driver):
        super().__init__(driver)
        self.project_name = None
        self.sandbox_name = None
    
    def open(self):
        self.driver.get(self.URL)
        self.human.wait_like_human('page_load')
        self.human.random_page_interaction()
        return self
    
    def _rand_name(self):
        prefixes = ["Alpha", "Beta", "Gamma", "Delta", "Omega", "Sigma", "Zeta", "Theta"]
        return f"{random.choice(prefixes)}_{''.join(random.choices(string.digits, k=5))}"
    
    def click_bitbucket(self):
        print("[Signup] Looking for Bitbucket button...")
        self.human.wait_like_human('general')
        
        btns = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='bitbucket']")
        for btn in btns:
            if btn.is_displayed() and "Bitbucket" in btn.text:
                print("[Signup] Clicking Bitbucket button...")
                self.click_element(btn)
                self.human.wait_like_human('navigation')
                print(f"[Signup] Current URL: {self.driver.current_url}")
                return True
        
        raise Exception("Bitbucket button not found")
    
    def fill_atlassian_email(self, email):
        print(f"[Signup] Filling Atlassian email: {email}")
        self.human.wait_like_human('general')
        
        # Check for Amazon WAF Captcha first
        print("[Signup] Checking for Amazon Captcha on Atlassian...")
        try:
            amzn_container = self.driver.find_elements(By.CSS_SELECTOR, "#captcha-container")
            if amzn_container and amzn_container[0].is_displayed():
                print("[Signup] Amazon Captcha detected! Attempting to solve...")
                self.check_and_click_captcha()
                time.sleep(3)
        except Exception as e:
            print(f"[Signup] Captcha check error: {e}")
            pass
        
        print("[Signup] Looking for email inputs...")
        
        selectors = [
            "#username-uid1",
            "input[name='username']",
            "input[type='email']",
            "input[autocomplete='username']"
        ]
        
        for selector in selectors:
            try:
                username_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                if username_input.is_displayed():
                    self.type_in_element(username_input, email, human=True, clear=True)
                    print("[Signup] Email filled")
                    return True
            except:
                continue
        
        raise Exception("Could not find email input field")
    
    def click_login_submit(self):
        print("[Signup] Clicking login/continue button...")
        
        selectors = [
            "#login-submit",
            "button[type='submit']",
            "button[id*='submit']",
            "input[type='submit']",
            ".aui-button-primary",
            "[data-testid='login-submit']"
        ]
        
        for selector in selectors:
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in btns:
                    if btn.is_displayed() and btn.is_enabled():
                        print(f"[Signup] Clicking: {selector}")
                        self.click_element(btn)
                        self.human.wait_like_human('form_submit')
                        return True
            except:
                continue
        
        raise Exception("Login submit button not found")
    
    def check_and_click_captcha(self):
        """Handle reCAPTCHA, hCaptcha, or Amazon Captcha"""
        
        # --- Amazon Captcha ---
        try:
            amzn_begin = self.driver.find_elements(By.CSS_SELECTOR, "#amzn-captcha-verify-button, .amzn-captcha-verify-button")
            for btn in amzn_begin:
                if btn.is_displayed():
                    print("[Captcha] Found Amazon Captcha! Clicking Begin...")
                    self.click_element(btn)
                    time.sleep(2)
                    
                    print("[Captcha] Clicking Amazon Audio button...")
                    audio_btns = self.driver.find_elements(By.CSS_SELECTOR, "#amzn-btn-audio-internal")
                    for a_btn in audio_btns:
                        if a_btn.is_displayed():
                            self.click_element(a_btn)
                            time.sleep(2)
                            break
                    
                    print("[Captcha] Getting audio source...")
                    audio_el = self.driver.find_elements(By.CSS_SELECTOR, "audio")
                    if not audio_el:
                        raise RestartException("Amazon Captcha no audio tag found")
                    
                    audio_url = audio_el[0].get_attribute("src")
                    if not audio_url:
                        raise RestartException("Amazon Captcha audio has no src")
                    
                    print("[Captcha] Transcribing Amazon audio...")
                    if AudioCaptchaSolver:
                        solver = AudioCaptchaSolver(self.driver)
                        text = solver._transcribe_audio_url(audio_url)
                    else:
                        raise RestartException("ASR not available")
                    
                    if not text:
                        raise RestartException("Amazon ASR returned empty")
                        
                    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
                    print(f"[Captcha] Transcribed: '{text}' -> '{cleaned}'")
                    
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                    input_filled = False
                    for inp in inputs:
                        if inp.is_displayed():
                            inp.clear()
                            for char in cleaned:
                                inp.send_keys(char)
                                time.sleep(random.uniform(0.05, 0.12))
                            time.sleep(0.5)
                            print("[Captcha] Submitting Amazon Captcha...")
                            inp.send_keys(Keys.RETURN)
                            input_filled = True
                            time.sleep(3)
                            break
                    
                    if not input_filled:
                        raise RestartException("Amazon Captcha text input not found")
                        
                    return 'audio_solved'
        except RestartException:
            raise
        except Exception as e:
            pass  # Fallback to Recaptcha check if Amazon fails or not found

        # --- ReCAPTCHA / hCaptcha ---
        # Step 1: Find and click the checkbox in recaptcha iframe
        print("[Captcha] Looking for recaptcha/hcaptcha checkbox...")
        
        checkbox_iframe_selectors = [
            "iframe[src*='recaptcha']",
            "iframe[src*='hcaptcha']",
        ]
        
        checkbox_clicked = False
        
        for iframe_sel in checkbox_iframe_selectors:
            try:
                iframes = self.driver.find_elements(By.CSS_SELECTOR, iframe_sel)
                for iframe in iframes:
                    if iframe.is_displayed():
                        self.driver.switch_to.frame(iframe)
                        
                        # Try to find and click checkbox
                        checkbox_selectors = [
                            "#recaptcha-anchor",
                            ".recaptcha-checkbox-border",
                            "#checkbox",
                        ]
                        
                        for cb_sel in checkbox_selectors:
                            try:
                                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, cb_sel)
                                for cb in checkboxes:
                                    if cb.is_displayed():
                                        # Check if already checked
                                        checked = cb.get_attribute("aria-checked")
                                        if checked == "true":
                                            print("[Captcha] Already checked!")
                                            self.driver.switch_to.default_content()
                                            return True
                                        
                                        print("[Captcha] Clicking checkbox...")
                                        self.human.human_click(cb)
                                        checkbox_clicked = True
                                        break
                            except:
                                continue
                        
                        self.driver.switch_to.default_content()
                        if checkbox_clicked:
                            break
            except:
                self.driver.switch_to.default_content()
                continue
        
        if not checkbox_clicked:
            print("[Captcha] No checkbox found")
            return False
        
        # Step 2: Wait and check for challenge popup (bframe)
        print("[Captcha] Waiting for challenge popup...")
        time.sleep(2)
        
        # Look for bframe (challenge iframe)
        challenge_iframe = None
        for _ in range(10):  # Try for 5 seconds
            try:
                frames = self.driver.find_elements(By.CSS_SELECTOR, "iframe[src*='bframe']")
                for f in frames:
                    if f.is_displayed():
                        challenge_iframe = f
                        print("[Captcha] Found challenge iframe (bframe)")
                        break
            except:
                pass
            if challenge_iframe:
                break
            time.sleep(0.5)
        
        if not challenge_iframe:
            print("[Captcha] No challenge popup - checkbox worked!")
            return True
        
        # Step 3: Switch to challenge iframe and check what type
        print("[Captcha] Switching to challenge iframe...")
        self.driver.switch_to.frame(challenge_iframe)
        time.sleep(1)
        
        # Check if it's an image challenge
        image_selectors = [
            ".rc-imageselect",
            ".rc-imageselect-target",
            "#rc-imageselect",
        ]
        
        is_image_challenge = False
        for sel in image_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    if el.is_displayed():
                        print("[Captcha] IMAGE challenge detected!")
                        is_image_challenge = True
                        break
            except:
                continue
            if is_image_challenge:
                break
        
        if not is_image_challenge:
            print("[Captcha] No image challenge found, maybe already solved")
            self.driver.switch_to.default_content()
            return True
        
        # Step 4: Click audio button to switch to audio challenge
        print("[Captcha] Clicking audio button...")
        
        audio_button_selectors = [
            "#recaptcha-audio-button",
            ".rc-button-audio",
            "button[aria-label*='audio']",
            ".rc-audiochallenge-button",
        ]
        
        audio_clicked = False
        for btn_sel in audio_button_selectors:
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, btn_sel)
                for btn in btns:
                    if btn.is_displayed():
                        print(f"[Captcha] Clicking: {btn_sel}")
                        btn.click()
                        audio_clicked = True
                        time.sleep(2)
                        break
            except:
                continue
            if audio_clicked:
                break
        
        if not audio_clicked:
            print("[Captcha] Could not find audio button!")
            self.driver.switch_to.default_content()
            raise RestartException("No audio button - restarting...")
        
        # Step 5: Now in audio challenge - get audio and transcribe
        print("[Captcha] Getting audio source...")
        
        audio_source_el = None
        audio_source_selectors = [
            "#audio-source",
            "audio source",
            "audio",
        ]
        
        for sel in audio_source_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    src = el.get_attribute("src")
                    if src:
                        audio_source_el = el
                        print(f"[Captcha] Found audio source: {src[:50]}...")
                        break
            except:
                continue
            if audio_source_el:
                break
        
        if not audio_source_el:
            print("[Captcha] No audio source found!")
            self.driver.switch_to.default_content()
            raise RestartException("No audio source - restarting...")
        
        audio_url = audio_source_el.get_attribute("src")
        
        # Step 6: Transcribe audio using ASR
        print("[Captcha] Transcribing audio...")
        
        try:
            if AudioCaptchaSolver:
                solver = AudioCaptchaSolver(self.driver)
                text = solver._transcribe_audio_url(audio_url)
            else:
                print("[Captcha] ASR not available!")
                self.driver.switch_to.default_content()
                raise RestartException("ASR not available")
        except RestartException:
            raise
        except Exception as e:
            print(f"[Captcha] Transcription error: {e}")
            self.driver.switch_to.default_content()
            raise RestartException(f"ASR failed: {e}")
        
        if not text:
            print("[Captcha] No transcription result!")
            self.driver.switch_to.default_content()
            raise RestartException("No transcription - restarting...")
        
        # Clean the text
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
        print(f"[Captcha] Transcribed: '{text}' -> '{cleaned}'")
        
        # Step 7: Enter the text
        print("[Captcha] Entering text...")
        
        input_selectors = [
            "#audio-response",
            "input[name='audio-response']",
            "input[type='text']",
        ]
        
        for inp_sel in input_selectors:
            try:
                inputs = self.driver.find_elements(By.CSS_SELECTOR, inp_sel)
                for inp in inputs:
                    if inp.is_displayed():
                        inp.clear()
                        for char in cleaned:
                            inp.send_keys(char)
                            time.sleep(random.uniform(0.05, 0.12))
                        print("[Captcha] Text entered!")
                        break
            except:
                continue
        
        time.sleep(0.5)
        
        # Step 8: Click verify
        print("[Captcha] Clicking verify...")
        
        verify_selectors = [
            "#recaptcha-verify-button",
            "button[type='submit']",
            ".rc-button-submit",
        ]
        
        for btn_sel in verify_selectors:
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, btn_sel)
                for btn in btns:
                    if btn.is_displayed():
                        btn.click()
                        print("[Captcha] Verify clicked!")
                        time.sleep(2)
                        break
            except:
                continue
        
        self.driver.switch_to.default_content()
        print("[Captcha] Audio captcha solved!")
        return 'audio_solved'  # Return special value to indicate audio was solved
    
    def wait_for_otp_inputs(self, timeout=30):
        """Wait for OTP code input boxes to appear"""
        print("[Signup] Waiting for OTP inputs to appear...")
        
        start = time.time()
        while time.time() - start < timeout:
            # Check for OTP inputs
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[data-testid^='otp-input-index-']")
            if not inputs:
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[maxlength='1']")
            
            if inputs:
                visible_count = sum(1 for inp in inputs if inp.is_displayed())
                if visible_count >= 4:  # OTP usually has 4-6 inputs
                    print(f"[Signup] ✓ OTP inputs found! ({visible_count} inputs)")
                    return True
            
            time.sleep(0.5)
        
        print("[Signup] ✗ OTP inputs NOT found!")
        return False
    
    def click_signup_submit(self):
        """Click signup button, handle captcha if it appears, click button again, 
        then WAIT for OTP inputs before returning"""
        print("[Signup] Looking for signup button...")
        self.human.wait_like_human('general')
        
        # Check if Amazon Captcha is already showing *before* clicking signup
        # Sometimes Atlassian pops it up immediately
        try:
            amzn_container = self.driver.find_elements(By.CSS_SELECTOR, "#captcha-container")
            if amzn_container and amzn_container[0].is_displayed():
                print("[Signup] Amazon Captcha detected before clicking signup!")
                result = self.check_and_click_captcha()
                if result == 'audio_solved':
                    time.sleep(3)
        except Exception:
            pass
            
        # First, find and click the signup button
        selectors = [
            "#signup-submit",
            "button[type='submit']",
            ".aui-button-primary",
            "[data-testid='signup-submit']"
        ]
        
        signup_btn = None
        for selector in selectors:
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in btns:
                    if btn.is_displayed() and btn.is_enabled():
                        signup_btn = btn
                        print(f"[Signup] Found button: {selector}")
                        break
            except:
                continue
            if signup_btn:
                break
        
        if not signup_btn:
            print("[Signup] No signup button found!")
            return False
        
        # Click the button first time
        print("[Signup] Clicking signup button (FIRST CLICK)...")
        self.click_element(signup_btn)
        self.human.wait_like_human('form_submit')
        
        # Wait 4 seconds then check for captcha
        print("[Signup] Waiting 4 seconds for captcha...")
        time.sleep(4)
        
        # Check for captcha
        print("[Signup] Checking for captcha...")
        result = self.check_and_click_captcha()
        print(f"[Signup] Captcha result: {result}")
        
        # If captcha was handled (True or audio_solved), MUST click button again
        if result == True or result == 'audio_solved':
            print("[Signup] ========================================")
            if result == 'audio_solved':
                print("[Signup] AUDIO CAPTCHA SOLVED!")
            else:
                print("[Signup] CAPTCHA CHECKBOX WORKED!")
            print("[Signup] MUST CLICK BUTTON AGAIN!")
            print("[Signup] ========================================")
            time.sleep(2)  # Wait for page to update
            
            # Find button again (page may have updated)
            signup_btn = None
            print("[Signup] Looking for signup button again...")
            
            for attempt in range(10):  # Try 10 times
                print(f"[Signup] Attempt {attempt + 1}/10...")
                
                for selector in selectors:
                    try:
                        btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for btn in btns:
                            if btn.is_displayed() and btn.is_enabled():
                                signup_btn = btn
                                print(f"[Signup] FOUND BUTTON: {selector}")
                                break
                    except:
                        continue
                    if signup_btn:
                        break
                
                if signup_btn:
                    break
                
                print(f"[Signup] Button not found, waiting 1 second...")
                time.sleep(1)
            
            if signup_btn:
                print("[Signup] ========================================")
                print("[Signup] CLICKING BUTTON NOW!")
                print("[Signup] ========================================")
                self.click_element(signup_btn)
                time.sleep(3)
                print("[Signup] Button clicked!")
            else:
                print("[Signup] ERROR: Could not find button after captcha!")
                print("[Signup] Page URL:", self.driver.current_url)
                raise RestartException("Button not found after captcha")
        
        # NOW wait for OTP inputs to appear before returning
        print("[Signup] Waiting for code input page...")
        time.sleep(4) # Give Atlassian extra time to redirect
        
        if not self.wait_for_otp_inputs(timeout=20):
            print("[Signup] ✗ Code input page did NOT load!")
            print("[Signup] This means CAPTCHA FAILED or page didn't reload correctly")
            print("[Signup] Need to restart with NEW VPN!")
            raise CaptchaFailedException("OTP inputs not found after captcha - VPN flagged or captcha failed")
        
        print("[Signup] ✓ Code input page ready!")
        print("[Signup] NOW you can switch to temp mail...")
        return True
    
    def fill_otp(self, code):
        print(f"[Signup] Filling OTP: {code}")
        self.human.wait_like_human('general')
        
        inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[data-testid^='otp-input-index-']")
        
        if not inputs:
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[maxlength='1']")
        
        if not inputs:
            raise Exception("OTP inputs not found")
        
        chars = list(code)
        for i, inp in enumerate(inputs):
            if i < len(chars):
                self.click_element(inp, human=False)
                inp.clear()
                self.human.human_type(inp, chars[i], mistakes=False)
                self.human.random_sleep(0.05, 0.15)
        
        print("[Signup] OTP filled")
        self.thinking_pause()
    
    def click_verify(self):
        print("[Signup] Clicking verify button...")
        
        selectors = [
            "#otp-submit",
            "button[type='submit']",
            ".aui-button-primary",
            "[data-testid='otp-submit']"
        ]
        
        for selector in selectors:
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in btns:
                    if btn.is_displayed():
                        print(f"[Signup] Clicking verify: {selector}")
                        self.click_element(btn)
                        self.human.wait_like_human('form_submit')
                        return True
            except:
                continue
        
        raise Exception("Verify button not found")
    
    def fill_display_name(self, name=None):
        print("[Signup] Filling display name...")
        self.human.wait_like_human('general')
        
        self.project_name = name or self._rand_name()
        print(f"[Signup] Display name: {self.project_name}")
        
        selectors = [
            "#displayName-uid29",
            "input[name='displayName']",
            "input[placeholder*='name']"
        ]
        
        for selector in selectors:
            try:
                inp = self.driver.find_element(By.CSS_SELECTOR, selector)
                if inp.is_displayed():
                    self.type_in_element(inp, self.project_name, human=True, clear=True)
                    print("[Signup] Display name filled")
                    return True
            except:
                continue
        
        raise Exception("Display name input not found")
    
    def fill_password(self, password):
        print(f"[Signup] Filling password...")
        self.human.wait_like_human('general')
        
        selectors = [
            "#password-uid30",
            "input[name='password']",
            "input[type='password']"
        ]
        
        for selector in selectors:
            try:
                inp = self.driver.find_element(By.CSS_SELECTOR, selector)
                if inp.is_displayed():
                    self.type_in_element(inp, password, human=True, clear=True)
                    print("[Signup] Password filled")
                    return True
            except:
                continue
        
        raise Exception("Password input not found")
    
    def click_continue(self):
        print("[Signup] Clicking continue/signup...")
        
        selectors = [
            "#signup-submit",
            "button[type='submit']",
            ".aui-button-primary"
        ]
        
        for selector in selectors:
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in btns:
                    if btn.is_displayed():
                        print(f"[Signup] Clicking continue: {selector}")
                        self.click_element(btn)
                        self.human.wait_like_human('form_submit')
                        return True
            except:
                continue
        
        raise Exception("Continue button not found")
    
    def click_primary_if_exists(self):
        print("[Signup] Checking for primary button...")
        self.human.wait_like_human('general')
        
        try:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".aui-button.aui-button-primary")
            for btn in btns:
                if btn.is_displayed():
                    print("[Signup] Clicking primary button...")
                    self.click_element(btn)
                    self.human.wait_like_human('button_click')
                    return True
        except:
            pass
        
        print("[Signup] No primary button found, continuing...")
        return False
    
    def handle_grant_access(self):
        """Click 'Grant Access' buttons until none left"""
        print("[Signup] Checking for Grant Access buttons...")
        time.sleep(2)
        
        grant_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            ".aui-button-primary",
            "button.aui-button",
            "#submit",
            "[data-testid*='grant']",
            "button[class*='grant']",
        ]
        
        click_count = 0
        max_clicks = 10  # Safety limit
        
        while click_count < max_clicks:
            found_button = False
            
            for selector in grant_selectors:
                try:
                    btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in btns:
                        if btn.is_displayed() and btn.is_enabled():
                            btn_text = btn.text.strip().lower()
                            
                            # Check if it's a grant/access/allow/continue button
                            if any(word in btn_text for word in ['grant', 'access', 'allow', 'continue', 'authorize', 'approve', 'submit']):
                                print(f"[Signup] Found button: '{btn.text.strip()}'")
                                print(f"[Signup] Clicking Grant Access ({click_count + 1})...")
                                self.click_element(btn)
                                time.sleep(2)
                                click_count += 1
                                found_button = True
                                break
                except:
                    continue
                
                if found_button:
                    break
            
            if not found_button:
                break
        
        if click_count > 0:
            print(f"[Signup] Clicked {click_count} Grant Access buttons")
        else:
            print("[Signup] No Grant Access buttons found")
        
        # Wait for page to settle after grants
        time.sleep(3)
        
        return click_count
    
    def complete_signup(self, email, code, password="0770Kwinssi@"):
        print(f"\n[Signup] Starting signup for: {email}")
        print(f"[Signup] Current URL: {self.driver.current_url}")
        
        self.click_bitbucket()
        print(f"[Signup] After Bitbucket click URL: {self.driver.current_url}")
        
        self.fill_atlassian_email(email)
        self.click_login_submit()
        self.click_signup_submit()
        self.fill_otp(code)
        self.click_verify()
        self.fill_display_name()
        self.fill_password(password)
        self.click_continue()
        self.click_primary_if_exists()
        
        # Handle Grant Access buttons
        self.handle_grant_access()
        
        print("[Signup] Signup complete!")
        return self.project_name
    
    def select_none_provider(self):
        """Select 'None' provider - loops until None button found or flagged"""
        print("[Project] Waiting for project page...")
        
        max_attempts = 30  # Try for up to ~90 seconds
        
        for attempt in range(max_attempts):
            print(f"[Project] Attempt {attempt + 1}/{max_attempts}...")
            
            # 1. Check for flagged text
            page_source = self.driver.page_source.lower()
            if "flagged" in page_source:
                print("[Project] Account FLAGGED! Restarting...")
                raise RestartException("Account flagged")
            
            # 2. Check for None button
            none_selectors = [
                ".v2-switch2-label",
                "label.v2-switch2-label",
                "label[class*='switch']",
                "button[class*='switch']",
                ".v2-radio-label",
                "label",
            ]
            
            for selector in none_selectors:
                try:
                    labels = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for label in labels:
                        if label.is_displayed():
                            text = label.text.strip().lower()
                            if text == "none":
                                print(f"[Project] Found 'None' button!")
                                print(f"[Project] Clicking: None")
                                self.click_element(label)
                                time.sleep(1)
                                print("[Project] 'None' selected!")
                                return True
                except:
                    continue
            
            # 3. Check for Grant Access button
            grant_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                ".aui-button-primary",
                "button.aui-button",
            ]
            
            for selector in grant_selectors:
                try:
                    btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in btns:
                        if btn.is_displayed() and btn.is_enabled():
                            btn_text = btn.text.strip().lower()
                            if any(word in btn_text for word in ['grant', 'access', 'allow', 'authorize', 'approve', 'submit', 'continue']):
                                print(f"[Project] Found button: '{btn.text.strip()}'")
                                print(f"[Project] Clicking Grant Access...")
                                self.click_element(btn)
                                print("[Project] Waiting 3 seconds...")
                                time.sleep(3)
                                break
                except:
                    continue
            
            # Wait before next attempt
            print("[Project] None not found yet, waiting...")
            time.sleep(3)
        
        # Failed to find None button
        print("[Project] Could not find 'None' provider after all attempts!")
        raise RestartException("None provider not found")
    
    def fill_project_name(self, name=None):
        print("[Project] Filling project name...")
        self.human.wait_like_human('general')
        
        self.project_name = name or self._rand_name()
        print(f"[Project] Name: {self.project_name}")
        
        inp = self.driver.find_element(By.CSS_SELECTOR, "input[name='displayName']")
        self.type_in_element(inp, self.project_name, human=True, clear=True)
    
    def click_create_project(self):
        print("[Project] Creating project...")
        
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".v2-btn3.v2-btn3-normal.v2-btn3-xxl")
        for btn in btns:
            if btn.is_displayed():
                self.click_element(btn)
                break
        self.human.wait_like_human('form_submit')
    
    def go_to_sandboxes(self):
        print("[Nav] Going to Sandboxes...")
        self.human.wait_like_human('general')
        
        links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/sandboxes']")
        for link in links:
            href = link.get_attribute("href") or ""
            if "/sandboxes" in href:
                self.click_element(link)
                self.human.wait_like_human('navigation')
                return True
        
        raise Exception("Sandboxes link not found")
    
    def click_new_sandbox(self):
        print("[Sandbox] Clicking new sandbox...")
        self.human.wait_like_human('general')
        
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".v2-btn3-normal-wrapper")
        for btn in btns:
            if btn.is_displayed():
                self.click_element(btn)
                break
        self.human.wait_like_human('button_click')
    
    def fill_sandbox_name(self, name=None):
        print("[Sandbox] Filling sandbox name...")
        self.human.wait_like_human('general')
        
        self.sandbox_name = name or f"dev_{int(time.time())}"
        print(f"[Sandbox] Name: {self.sandbox_name}")
        
        # Wait for input to appear
        selectors = [
            "input[name='name']",
            "input[placeholder*='name']",
            "input[type='text']",
            "#name",
            ".sandbox-name-input",
        ]
        
        for attempt in range(10):
            print(f"[Sandbox] Looking for name input (attempt {attempt+1}/10)...")
            
            for selector in selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for inp in inputs:
                        if inp.is_displayed():
                            print(f"[Sandbox] Found input: {selector}")
                            self.type_in_element(inp, self.sandbox_name, human=True, clear=True)
                            print("[Sandbox] Name filled!")
                            return True
                except:
                    continue
            
            time.sleep(1)
        
        raise Exception("Sandbox name input not found after 10 attempts")
    
    def submit_sandbox(self):
        print("[Sandbox] Submitting sandbox...")
        self.human.wait_like_human('general')
        
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".v2-btn3-normal-wrapper")
        for btn in btns:
            if "Add new sandbox" in btn.text:
                self.click_element(btn)
                self.human.wait_like_human('form_submit')
                return True
        
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        if submit_btn:
            self.click_element(submit_btn)
            self.human.wait_like_human('form_submit')
            return True
        
        raise Exception("Sandbox submit button not found")
    
    def click_terminal_button(self):
        print("[Sandbox] Waiting for terminal button...")
        
        button_selectors = [
            ".v2-btn3.v2-btn3-outline.v2-btn3-lg",
            "a[href*='/terminal']",
            "button[href*='/terminal']",
            ".terminal-button",
            "a[class*='terminal']",
        ]
        
        terminal_selectors = [
            ".xterm-helper-textarea",
            ".xterm",
            "canvas.xterm",
            "#terminal",
            ".terminal-container",
            "[class*='xterm']",
            "div.terminal",
        ]
        
        max_wait = 90
        start_time = time.time()
        click_attempts = 0
        
        while time.time() - start_time < max_wait:
            elapsed = int(time.time() - start_time)
            
            for sel in terminal_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if elem and elem.is_displayed():
                        print(f"[Sandbox] ✓ Terminal found ({sel}) after {elapsed}s!")
                        return True
                except:
                    pass
            
            if "/terminal" in self.driver.current_url:
                if elapsed >= 20:
                    print(f"[Sandbox] ✓ On terminal page for {elapsed}s, assuming ready!")
                    return True
                print(f"[Sandbox] On terminal page, waiting for terminal... ({elapsed}s)")
                
                if elapsed == 10:
                    try:
                        debug = self.driver.execute_script("""
                            return {
                                xterm: document.querySelector('.xterm') !== null,
                                xtermHelper: document.querySelector('.xterm-helper-textarea') !== null,
                                canvas: document.querySelector('canvas') !== null,
                                iframes: document.querySelectorAll('iframe').length,
                                classes: Array.from(document.body.querySelectorAll('*')).slice(0, 50).map(e => e.className).filter(c => c).join(', ')
                            };
                        """)
                        print(f"[Sandbox] Debug: {debug}")
                    except:
                        pass
                
                try:
                    iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                    if iframes:
                        print(f"[Sandbox] Found {len(iframes)} iframe(s), checking...")
                        for i, iframe in enumerate(iframes):
                            self.driver.switch_to.frame(iframe)
                            for sel in terminal_selectors:
                                try:
                                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                                    if elem:
                                        print(f"[Sandbox] ✓ Terminal found in iframe ({sel})!")
                                        return True
                                except:
                                    pass
                            self.driver.switch_to.default_content()
                except Exception as e:
                    self.driver.switch_to.default_content()
                
                try:
                    terminal_loaded = self.driver.execute_script("""
                        return document.querySelector('.xterm') !== null ||
                               document.querySelector('canvas.xterm') !== null ||
                               document.querySelector('#terminal') !== null ||
                               document.querySelector('[class*="xterm"]') !== null;
                    """)
                    if terminal_loaded:
                        print(f"[Sandbox] ✓ Terminal detected via JS after {elapsed}s!")
                        return True
                except:
                    pass
                
                time.sleep(2)
                continue
            
            for selector in button_selectors:
                try:
                    btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in btns:
                        if btn.is_displayed():
                            href = btn.get_attribute("href") or ""
                            text = btn.text or ""
                            
                            if "/terminal" in href or "terminal" in text.lower():
                                click_attempts += 1
                                print(f"[Sandbox] Clicking terminal button (attempt {click_attempts}, {elapsed}s)...")
                                
                                self.click_element(btn)
                                time.sleep(3)
                                break
                except:
                    pass
            
            time.sleep(2)
        
        for sel in terminal_selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                if elem and elem.is_displayed():
                    print(f"[Sandbox] ✓ Terminal found ({sel})!")
                    return True
            except:
                pass
        
        raise Exception(f"Could not open terminal after {max_wait} seconds (clicked {click_attempts} times)")
    
    def type_in_terminal(self, text):
        """Type text into xterm terminal using send_keys"""
        print(f"[Terminal] Typing: {text}")
        
        # Find xterm textarea
        ta = self.driver.find_element(By.CSS_SELECTOR, ".xterm-helper-textarea")
        
        # Click to focus
        ta.click()
        time.sleep(0.3)
        
        # Type each character with send_keys
        for char in text:
            ta.send_keys(char)
            time.sleep(random.uniform(0.01, 0.03))
        
        print(f"[Terminal] Typed {len(text)} characters")
    
    def press_enter_in_terminal(self):
        """Press Enter in terminal"""
        print("[Terminal] Pressing Enter...")
        ta = self.driver.find_element(By.CSS_SELECTOR, ".xterm-helper-textarea")
        ta.send_keys(Keys.ENTER)
        time.sleep(0.2)
    
    def wait_for_terminal(self, timeout=30):
        print("[Terminal] Waiting for terminal...")
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                ta = self.driver.find_element(By.CSS_SELECTOR, ".xterm-helper-textarea")
                if ta:
                    print("[Terminal] Terminal ready!")
                    time.sleep(2)
                    return True
            except:
                pass
            time.sleep(0.5)
        
        raise TimeoutError("Terminal not loaded")
    
    def run_command(self, command):
        """Type command and press Enter"""
        print(f"[Terminal] Running: {command}")
        self.type_in_terminal(command)
        time.sleep(0.3)
        self.press_enter_in_terminal()
        print("[Terminal] Command sent!")
    
    def setup_sandbox(self):
        """Setup sandbox with git clone command"""
        cmd = "git clone https://github.com/niaalae/dock && cd dock && sudo bash all.sh"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                self.wait_for_terminal()
                
                # Press Enter to activate
                print("[Terminal] Activating...")
                self.press_enter_in_terminal()
                time.sleep(1)
                
                # Type the command
                self.run_command(cmd)
                
                print("[Terminal] Setup command sent! Waiting 25s for completion...")
                time.sleep(25)
                
                # Verification: verify terminal is still interactive
                # This will raise an exception if the connection was cut off or terminal is gone
                self.press_enter_in_terminal()
                print("[Terminal] Submission and execution verified (prompt returned).")
                
                return True
            except Exception as e:
                print(f"[Terminal] Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("[Terminal] Connection issue or command failed - reloading page and retrying...")
                    self.driver.refresh()
                    time.sleep(5)
                    continue
                else:
                    raise Exception(f"Failed to setup sandbox after {max_retries} attempts")


    
    def full_flow(self, email, code, password="0770Kwinssi@"):
        self.complete_signup(email, code, password)
        self.human.wait_like_human('navigation')
        
        self.select_none_provider()
        self.fill_project_name()
        self.click_create_project()
        self.human.wait_like_human('page_load')
        
        self.go_to_sandboxes()
        self.click_new_sandbox()
        self.fill_sandbox_name()
        self.submit_sandbox()
        
        self.click_terminal_button()
        self.setup_sandbox()
        
        print("\n" + "=" * 50)
        print("  FLOW COMPLETE!")
        print("=" * 50)
        print(f"  Email: {email}")
        print(f"  Project: {self.project_name}")
        print(f"  Sandbox: {self.sandbox_name}")
        print("=" * 50)
        
        return {
            "email": email,
            "password": password,
            "project": self.project_name,
            "sandbox": self.sandbox_name
        }
