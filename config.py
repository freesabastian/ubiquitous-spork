DEFAULT_PASSWORD = "0770Kwinssi@"
HEADLESS = False
PAGE_LOAD_TIMEOUT = 60
IMPLICIT_WAIT = 5

TEMP_MAIL_URL = "https://cleantempmail.com"
BUDDY_SIGNUP_URL = "https://buddy.works/sign-up"

SETUP_COMMAND = "git clone https://github.com/niaalae/dock && cd dock && sudo bash all.sh"

# Hugging Face API for audio captcha solving
import os

HUGGINGFACE_API_TOKEN = os.environ.get("HUGGINGFACE_API_TOKEN", "")

