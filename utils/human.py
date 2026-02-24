import random
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


class HumanBehavior:
    """Simulates human-like interactions to avoid detection"""
    
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)
    
    def random_sleep(self, min_sec=0.5, max_sec=2.0):
        sleep_time = random.uniform(min_sec, max_sec)
        sleep_time += random.gauss(0, 0.1)
        sleep_time = max(0.1, sleep_time)
        time.sleep(sleep_time)
    
    def thinking_pause(self):
        pauses = [0.3, 0.5, 0.8, 1.2, 1.5, 2.0]
        weights = [0.3, 0.25, 0.2, 0.15, 0.07, 0.03]
        time.sleep(random.choices(pauses, weights=weights)[0])
    
    def human_type(self, element, text, mistakes=True):
        element.click()
        self.random_sleep(0.1, 0.3)
        
        for char in text:
            base_delay = random.uniform(0.05, 0.15)
            
            if char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                base_delay *= 1.5
            elif char in '!@#$%^&*()':
                base_delay *= 1.8
            
            if random.random() < 0.05:
                time.sleep(random.uniform(0.5, 1.5))
            
            if mistakes and random.random() < 0.02:
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                element.send_keys(wrong_char)
                time.sleep(random.uniform(0.1, 0.3))
                element.send_keys('\b')
                time.sleep(random.uniform(0.1, 0.2))
            
            element.send_keys(char)
            time.sleep(base_delay)
        
        self.random_sleep(0.2, 0.5)
    
    def human_click(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element
        )
        self.random_sleep(0.3, 0.8)
        
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        self.random_sleep(0.1, 0.3)
        
        if random.random() < 0.3:
            actions.move_by_offset(random.randint(-3, 3), random.randint(-3, 3)).perform()
            self.random_sleep(0.05, 0.15)
        
        element.click()
        self.random_sleep(0.2, 0.5)
    
    def natural_scroll(self, direction='down', amount=300):
        if direction == 'down':
            scroll_amount = amount
        else:
            scroll_amount = -amount
        
        steps = random.randint(3, 7)
        per_step = scroll_amount // steps
        
        for _ in range(steps):
            self.driver.execute_script(
                f"window.scrollBy(0, {per_step + random.randint(-20, 20)});"
            )
            time.sleep(random.uniform(0.05, 0.15))
        
        self.random_sleep(0.2, 0.5)
    
    def random_mouse_movement(self):
        try:
            body = self.driver.find_element(By.TAG_NAME, 'body')
            actions = ActionChains(self.driver)
            
            for _ in range(random.randint(1, 3)):
                actions.move_to_element(body).perform()
                actions.move_by_offset(
                    random.randint(-100, 100),
                    random.randint(-100, 100)
                ).perform()
                time.sleep(random.uniform(0.1, 0.3))
        except:
            pass
    
    def random_page_interaction(self):
        actions = random.choice(['scroll', 'move', 'pause', 'none'])
        
        if actions == 'scroll':
            self.natural_scroll('down', random.randint(100, 400))
        elif actions == 'move':
            self.random_mouse_movement()
        elif actions == 'pause':
            self.thinking_pause()
    
    def human_fill_form(self, field_element, text, clear_first=True):
        if clear_first:
            field_element.click()
            self.random_sleep(0.1, 0.3)
            field_element.send_keys('\ue009' + 'a')
            field_element.send_keys('\ue003')
            self.random_sleep(0.1, 0.2)
        
        self.human_type(field_element, text)
    
    def wait_like_human(self, action_type='general'):
        wait_times = {
            'page_load': (1.0, 3.0),
            'form_submit': (0.8, 2.0),
            'button_click': (0.3, 1.0),
            'typing': (0.05, 0.15),
            'navigation': (1.5, 4.0),
            'general': (0.5, 1.5),
            'reading': (2.0, 5.0),
            'captcha': (1.0, 2.0)
        }
        
        min_wait, max_wait = wait_times.get(action_type, (0.5, 1.5))
        self.random_sleep(min_wait, max_wait)


class CaptchaHandler:
    """Handle simple checkbox captchas - just clicks them"""
    
    # Common captcha iframe selectors
    IFRAME_SELECTORS = [
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']",
        "iframe[src*='captcha']",
        "iframe[title*='reCAPTCHA']",
        "iframe[title*='recaptcha']",
        "iframe[title*='captcha']",
        "iframe[title*='security']",
        "iframe[name*='captcha']",
        "iframe[id*='captcha']",
    ]
    
    # Checkbox selectors inside iframes
    CHECKBOX_IN_IFRAME = [
        ".recaptcha-checkbox-border",
        "#recaptcha-anchor",
        ".recaptcha-checkbox",
        "#checkbox",
        ".checkbox",
        "#hcaptcha-checkbox",
        ".hcaptcha-checkbox",
        ".check",
        "[role='checkbox']",
        "span[class*='checkbox']",
        "div[class*='checker']",
        "div[class*='check']",
    ]
    
    # Direct captcha elements (not in iframe)
    DIRECT_CAPTCHA = [
        ".g-recaptcha",
        ".h-captcha",
        "#recaptcha",
        "#captcha",
        "input[type='checkbox'][name*='captcha']",
        "input[type='checkbox'][id*='captcha']",
        "input[type='checkbox'][class*='captcha']",
        "input[type='checkbox'][class*='verify']",
        ".captcha-box",
        ".verify-checkbox",
        "#terms",
        "#privacy",
    ]
    
    def __init__(self, driver):
        self.driver = driver
        self.human = HumanBehavior(driver)
    
    def find_and_click_captcha(self, timeout=5):
        """Find and click any captcha checkbox"""
        print("[Captcha] Scanning for captcha...")
        
        start = time.time()
        while time.time() - start < timeout:
            # Check iframe captchas
            if self._try_iframe_captcha():
                return True
            
            # Check direct checkboxes
            if self._try_direct_captcha():
                return True
            
            time.sleep(0.3)
        
        print("[Captcha] No captcha found")
        return False
    
    def _try_iframe_captcha(self):
        """Try to find and click captcha in iframe"""
        for selector in self.IFRAME_SELECTORS:
            try:
                iframes = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for iframe in iframes:
                    if not iframe.is_displayed():
                        continue
                    
                    print(f"[Captcha] Found iframe: {selector}")
                    
                    # Switch to iframe
                    self.driver.switch_to.frame(iframe)
                    time.sleep(0.5)
                    
                    # Find checkbox
                    for cb_selector in self.CHECKBOX_IN_IFRAME:
                        try:
                            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, cb_selector)
                            
                            for checkbox in checkboxes:
                                if checkbox.is_displayed() and checkbox.is_enabled():
                                    print(f"[Captcha] Found checkbox: {cb_selector}")
                                    
                                    # Click it
                                    self.human.human_click(checkbox)
                                    print("[Captcha] Clicked checkbox!")
                                    
                                    # Wait and switch back
                                    time.sleep(1.0)
                                    self.driver.switch_to.default_content()
                                    return True
                        except:
                            continue
                    
                    # Switch back if no checkbox found
                    self.driver.switch_to.default_content()
                    
            except Exception as e:
                # Make sure we're back in main content
                try:
                    self.driver.switch_to.default_content()
                except:
                    pass
                continue
        
        return False
    
    def _try_direct_captcha(self):
        """Try to find and click direct captcha element"""
        for selector in self.DIRECT_CAPTCHA:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for el in elements:
                    if not el.is_displayed():
                        continue
                    
                    tag = el.tag_name.lower()
                    
                    # For input checkboxes
                    if tag == 'input' and el.get_attribute('type') == 'checkbox':
                        if not el.is_selected():
                            print(f"[Captcha] Found checkbox: {selector}")
                            self.human.human_click(el)
                            print("[Captcha] Clicked checkbox!")
                            time.sleep(0.5)
                            return True
                    
                    # For divs/spans that act as checkboxes
                    elif tag in ['div', 'span', 'button']:
                        print(f"[Captcha] Found clickable captcha: {selector}")
                        self.human.human_click(el)
                        print("[Captcha] Clicked!")
                        time.sleep(0.5)
                        return True
                        
            except:
                continue
        
        return False
    
    def check_and_handle(self):
        """Quick check and handle - call this at key points"""
        return self.find_and_click_captcha(timeout=3)


class StealthMode:
    """Stealth measures to avoid detection"""
    
    @staticmethod
    def inject_stealth_js(driver):
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' }
            ]
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'es']
        });
        
        window.chrome = { runtime: {} };
        
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
        
        try:
            driver.execute_script(stealth_js)
        except:
            pass
    
    @staticmethod
    def randomize_viewport(driver, width=None, height=None):
        common_sizes = [
            (1920, 1080),
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (1280, 720)
        ]
        
        if width and height:
            driver.set_window_size(width, height)
        else:
            w, h = random.choice(common_sizes)
            driver.set_window_size(w, h)
