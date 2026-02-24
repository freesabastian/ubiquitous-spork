import json
import os
import time
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
LOCK_FILE = os.path.join(DATA_DIR, ".accounts.lock")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump([], f)

def acquire_lock():
    """Acquire file lock for thread/process safety (cross-platform)."""
    ensure_data_dir()
    lock_file = open(LOCK_FILE, 'a+')
    lock_file.seek(0)
    # Windows compatibility
    if os.name == 'nt':
        import msvcrt
        size = os.path.getsize(LOCK_FILE)
        if size == 0:
            size = 1
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, size)
        return lock_file
    else:
        import fcntl
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        return lock_file

def release_lock(lock_file):
    """Release file lock"""
    try:
        if os.name == 'nt':
            import msvcrt
            lock_file.seek(0)
            size = os.path.getsize(LOCK_FILE)
            if size == 0:
                size = 1
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, size)
        else:
            import fcntl
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    finally:
        lock_file.close()

def load_accounts():
    """Load accounts with lock"""
    lock = acquire_lock()
    try:
        ensure_data_dir()
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    finally:
        release_lock(lock)

def save_accounts(accounts):
    """Save accounts with lock"""
    lock = acquire_lock()
    try:
        ensure_data_dir()
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(accounts, f, indent=2)
    finally:
        release_lock(lock)

def add_account(email, password, project=None, sandbox=None):
    """Add account with lock (thread/process safe)"""
    lock = acquire_lock()
    try:
        ensure_data_dir()
        # Load existing
        with open(ACCOUNTS_FILE, "r") as f:
            accounts = json.load(f)
        # Create new account
        account = {
            "email": email,
            "password": password,
            "project": project,
            "sandbox": sandbox,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "created": datetime.now().isoformat()
        }
        # Add to list
        accounts.append(account)
        # Save
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(accounts, f, indent=2)
        print(f"[Storage] Saved account: {email}")
        return account
    finally:
        release_lock(lock)

def get_account_count():
    """Get number of accounts"""
    lock = acquire_lock()
    try:
        ensure_data_dir()
        with open(ACCOUNTS_FILE, "r") as f:
            accounts = json.load(f)
            return len(accounts)
    finally:
        release_lock(lock)
