import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from utils.human import HumanBehavior, CaptchaHandler


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
        self.human = HumanBehavior(driver)
        self.captcha = CaptchaHandler(driver)
    
    def find(self, by, selector, timeout=30):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    
    def find_all(self, by, selector, timeout=30):
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return self.driver.find_elements(by, selector)
    
    def find_clickable(self, by, selector, timeout=30):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
    
    def click(self, by, selector, human=True):
        el = self.find_clickable(by, selector)
        if human:
            self.human.human_click(el)
        else:
            el.click()
        self.human.random_sleep(0.3, 0.8)
    
    def click_element(self, element, human=True):
        if human:
            self.human.human_click(element)
        else:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.2)
            element.click()
        self.human.random_sleep(0.3, 0.8)
    
    def type_text(self, by, selector, text, human=True, clear=True):
        el = self.find(by, selector)
        if human:
            self.human.human_fill_form(el, text, clear_first=clear)
        else:
            if clear:
                el.clear()
            el.send_keys(text)
        self.human.random_sleep(0.2, 0.5)
    
    def type_in_element(self, element, text, human=True, clear=True):
        if human:
            self.human.human_fill_form(element, text, clear_first=clear)
        else:
            if clear:
                element.clear()
            element.send_keys(text)
        self.human.random_sleep(0.2, 0.5)
    
    def wait_for_url_change(self, current_url, timeout=30):
        start = 0
        while start < timeout:
            if self.driver.current_url != current_url:
                return True
            self.human.random_sleep(0.3, 0.7)
            start += 0.5
        return False
    
    def get_text(self, by, selector):
        return self.find(by, selector).text
    
    def get_value(self, by, selector):
        return self.find(by, selector).get_attribute("value")
    
    def is_visible(self, by, selector):
        try:
            el = self.find(by, selector, timeout=2)
            return el.is_displayed()
        except:
            return False
    
    def scroll_to(self, by, selector):
        el = self.find(by, selector)
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", el)
        self.human.random_sleep(0.3, 0.8)
    
    def scroll_page(self, direction='down', amount=300):
        self.human.natural_scroll(direction, amount)
    
    def execute_script(self, script, *args):
        return self.driver.execute_script(script, *args)
    
    def random_interaction(self):
        self.human.random_page_interaction()
    
    def thinking_pause(self):
        self.human.thinking_pause()
    
    def check_captcha(self):
        """Check and click captcha if present"""
        return self.captcha.check_and_handle()
