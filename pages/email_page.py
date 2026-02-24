import random
from selenium.webdriver.common.by import By
from core.base_page import BasePage
import re
import time

class EmailPage(BasePage):
    URL = "https://cleantempmail.com"
    
    def __init__(self, driver):
        super().__init__(driver)
    
    def open(self):
        self.driver.get(self.URL)
        self.human.wait_like_human('page_load')
        self.human.random_page_interaction()
        return self
    
    def get_email(self):
        print("[Email] Getting email from display...")
        self.thinking_pause()
        
        selectors = [
            "#emailDisplay",
            ".email-display",
            "#email",
            "[id*='email']",
            ".email-address"
        ]
        
        for selector in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, selector)
                if el.is_displayed():
                    email = el.text or el.get_attribute("value") or ""
                    email = email.strip()
                    if email and "@" in email:
                        print(f"[Email] Got: {email}")
                        return email
            except:
                continue
        
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "input[type='text'][readonly]")
            email = el.get_attribute("value") or ""
            if email and "@" in email:
                print(f"[Email] Got from input: {email}")
                return email.strip()
        except:
            pass
        
        raise Exception("Could not find email on page")
    
    def get_verification_code(self, timeout=120):
        print("[Email] Waiting for verification code...")
        start = time.time()
        
        while time.time() - start < timeout:
            if random.random() < 0.1:
                self.human.random_mouse_movement()
            
            items = self.driver.find_elements(By.CSS_SELECTOR, ".email-item.unread")
            
            if not items:
                items = self.driver.find_elements(By.CSS_SELECTOR, ".email-item")
            
            for item in items:
                try:
                    subject_el = item.find_element(By.CSS_SELECTOR, ".subject")
                    sender_el = item.find_element(By.CSS_SELECTOR, ".sender")
                    subject = subject_el.text
                    sender = sender_el.text
                    
                    print(f"[Email] Checking: {sender} - {subject[:50]}...")
                    
                    if "atlassian" in sender.lower() or "verification" in subject.lower() or "code" in subject.lower():
                        print(f"[Email] Found verification email!")
                        
                        match = re.search(r'([A-Z0-9]{6})\s+is your verification code', subject, re.I)
                        if match:
                            code = match.group(1)
                            print(f"[Email] Code: {code}")
                            return code
                        
                        match = re.search(r'([A-Z0-9]{6})', subject)
                        if match:
                            code = match.group(1)
                            print(f"[Email] Code from subject: {code}")
                            return code
                        
                        try:
                            self.click_element(item)
                            self.human.wait_like_human('reading')
                            preview = item.find_element(By.CSS_SELECTOR, ".preview").text
                            match = re.search(r'([A-Z0-9]{6})', preview)
                            if match:
                                code = match.group(1)
                                print(f"[Email] Code from preview: {code}")
                                return code
                        except:
                            pass
                except Exception as e:
                    pass
            
            self.human.wait_like_human('general')
        
        raise TimeoutError("Verification code not received")
