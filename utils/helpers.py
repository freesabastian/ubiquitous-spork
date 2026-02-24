import time
import random
import string

def sleep(seconds):
    time.sleep(seconds)

def random_sleep(min_sec=0.5, max_sec=2.0):
    sleep(random.uniform(min_sec, max_sec))

def random_name():
    prefixes = ["Alpha", "Beta", "Gamma", "Delta", "Omega", "Sigma", "Zeta", "Theta"]
    return f"{random.choice(prefixes)}_{''.join(random.choices(string.digits, k=5))}"

def wait_for(condition, timeout=30, poll=0.5):
    start = time.time()
    while time.time() - start < timeout:
        result = condition()
        if result:
            return result
        sleep(poll)
    raise TimeoutError(f"Condition not met within {timeout}s")
