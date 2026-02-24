import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


class CaptchaHandler:
    """Handles simple captcha checkboxes"""
    
    def __init__(self, driver, api_key=None):
        self.driver = driver
    
    def detect_captcha(self, timeout=3):
        """Detect if any captcha checkbox is present"""
        selectors = [
            # reCAPTCHA checkbox
            ".g-recaptcha",
            "#recaptcha",
            "div[data-sitekey]",
            "iframe[src*='recaptcha']",
            
            # hCaptcha
            ".h-captcha",
            "#h-captcha",
            
            # Atlassian captcha
            "#captcha-container",
            ".captcha-container",
            "[data-testid*='captcha']",
            
            # Generic checkbox captcha
            "input[type='checkbox'][name*='captcha']",
            "div[role='checkbox'][aria-checked='false']"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed():
                        return True
            except:
                continue
        
        return False
    
    def click_captcha_checkbox(self, timeout=10):
        """Click the captcha checkbox if present"""
        print("[Captcha] Checking for captcha checkbox...")
        
        # Try reCAPTCHA checkbox first
        selectors = [
            # reCAPTCHA iframe container
            ".g-recaptcha",
            "#recaptcha",
            "div[data-sitekey]",
            
            # reCAPTCHA checkbox inside iframe
            "div.recaptcha-checkbox",
            ".recaptcha-checkbox-border",
            
            # Atlassian
            "#captcha-container",
            ".captcha-container"
        ]
        
        for selector in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, selector)
                if el.is_displayed():
                    print(f"[Captcha] Found: {selector}")
                    
                    # Try clicking directly
                    try:
                        el.click()
                        print("[Captcha] Clicked!")
                        time.sleep(2)
                        return True
                    except:
                        pass
                    
                    # Try clicking via iframe
                    try:
                        # Switch to recaptcha iframe if exists
                        iframes = self.driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
                        for iframe in iframes:
                            if iframe.is_displayed():
                                self.driver.switch_to.frame(iframe)
                                
                                checkbox = self.driver.find_element(By.CSS_SELECTOR, ".recaptcha-checkbox")
                                checkbox.click()
                                
                                self.driver.switch_to.default_content()
                                print("[Captcha] Clicked via iframe!")
                                time.sleep(2)
                                return True
                    except Exception as e:
                        try:
                            self.driver.switch_to.default_content()
                        except:
                            pass
            except:
                continue
        
        return False
    
    def handle_simple_captcha(self):
        """Handle simple checkbox captcha"""
        if self.detect_captcha():
            print("[Captcha] Captcha detected! Clicking checkbox...")
            self.click_captcha_checkbox()
            time.sleep(2)
            return True
        return False
    
    def check_and_click(self):
        """Check and click captcha if present"""
        return self.handle_simple_captcha()


def setup_captcha_handler(driver, api_key=None):
    """Factory function to create captcha handler"""
    return CaptchaHandler(driver, api_key)
