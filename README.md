# Buddy Works Automation

Automates Buddy Works signup and sandbox setup using undetected Chrome.

## Features

- **Human-like behavior**: Random delays, typing patterns, mouse movements
- **Smart Captcha handling**: 
  - Clicks checkbox captcha
  - If image challenge appears → switches to audio
  - Downloads audio → transcribes with **faster-whisper** (local, fast)
  - Falls back to Hugging Face API if needed
  - Enters transcribed text automatically
- **Auto-retry**: Restarts automatically on captcha failure or flagged accounts
- **Proxy support**: Use free proxies from web (tested before use)
- **Full automation**: From temp email to sandbox setup

## Install

```bash
cd buddy-bot
pip install -r requirements.txt
```

This installs:
- selenium, undetected-chromedriver (browser automation)
- faster-whisper (local ASR for audio captcha)
- requests, gradio_client (API calls)

## Usage

### Full Automation (default)

```bash
python3 main.py
```

This will:
1. Open temp mail site
2. Grab temp email
3. Open buddy.works
4. Sign up with Bitbucket
5. **Handle captcha if it appears**:
   - Clicks checkbox
   - If image challenge → clicks audio button
   - Transcribes with faster-whisper
   - Clicks signup button again
6. **Wait for OTP inputs** before switching to temp mail
7. Switch to temp mail, get verification code
8. Complete signup
9. Handle Grant Access buttons
10. Create project with "None" provider
11. Create sandbox
12. Run setup commands in terminal

### With Proxy

```bash
# Use free proxies (tested before use)
python3 main.py --proxy

# Just see available proxies
python3 main.py --proxy-list
```

### With Tor

Route all traffic through Tor network:

```bash
# Install Tor first
sudo apt install tor
sudo service tor start

# Run with Tor
python3 main.py --tor
```

Features:
- **Random user agent** each run
- **Tor circuit** for anonymity
- **SOCKS5 proxy** through 127.0.0.1:9050

### With VPN

Best free VPNs (2025):

| VPN | Data Limit | Speed | Link |
|-----|------------|-------|------|
| **Proton VPN** | Unlimited | Medium | https://protonvpn.com |
| **Windscribe** | 10GB/month | Fast | https://windscribe.com |
| **PrivadoVPN** | 10GB/month | Fast | https://privadovpn.com |
| **Hide.me** | 10GB/month | Fast | https://hide.me |
| **Hotspot Shield** | Unlimited | Very Fast | https://hotspotshield.com |

```bash
# Install VPN (example: Proton VPN)
sudo apt install protonvpn

# Connect
protonvpn connect

# Run with VPN
python3 main.py --vpn
```

### With VPN Rotation (Recommended)

Automatically rotates VPNs on captcha failure or flagged accounts:

```bash
# Use VPN with default credentials
python3 main.py -v

# List available VPNs
python3 main.py --vpn-list
```

**VPN Configuration:**
- VPN configs location: `vpns/cmt/` (96 ProtonVPN servers)
- Default credentials: Built-in (ProtonVPN free tier)
- Custom: `python3 main.py -v --vpn-user USER --vpn-pass PASS`

**How it works:**
1. Picks random VPN from 96 configs
2. Runs automation
3. If captcha fails or account flagged:
   - Closes browser
   - Marks VPN as failed
   - Picks NEW VPN
   - NEW random user agent
   - Restarts
4. Failed VPNs saved and not reused

**VPN Countries Available:**
- 🇨🇦 Canada (CA)
- 🇨🇭 Switzerland (CH)
- 🇯🇵 Japan (JP)
- 🇲🇽 Mexico (MX)
- 🇳🇱 Netherlands (NL)
- 🇺🇸 United States (US)
- 🇬🇧 United Kingdom (UK)
- And more...

### Auto Mode

Automatically selects best anonymity method:

```bash
python3 main.py --auto
```

Priority: **Tor > VPN > Proxy**

### Other Options

```bash
# With existing email and code
python3 main.py --email "your@email.com" --code "ABC123"

# Headless mode
python3 main.py --headless

# Combine Tor + Headless
python3 main.py --tor --headless

# Max retries
python3 main.py --max-retries 20
```

## Captcha Handling

The bot handles captchas intelligently:

1. **Find and click signup button** (FIRST click)
2. **Wait 5 seconds for captcha**
3. **If checkbox captcha**: Just click it
4. **If image challenge**:
   - Clicks "Audio" button
   - Downloads the audio file
   - Transcribes with **faster-whisper** (runs locally, very fast)
   - Enters transcribed text
   - Clicks verify button
5. **CLICK SIGNUP BUTTON AGAIN** (2nd click - IMPORTANT!)
6. **Then** switch to temp mail for verification code
7. **If fails**: Restarts with new email

## Grant Access Handling

After signup, the bot handles "Grant Access" dialogs:

**`select_none_provider()`** loops and handles everything:
1. **Loop** (up to 30 attempts, ~90 seconds)
2. **Each iteration**:
   - Check for **"flagged"** text → restart if found
   - Check for **"None"** button → click and return if found
   - Check for **Grant Access** button → click, wait 3 sec
   - Wait 3 sec before next attempt
3. **If not found**: Raises `RestartException`

## Flow After Signup

```
[Fill password + Continue]
        ↓
[click_primary_if_exists()]
        ↓
[select_none_provider()]:
   ↓
   LOOP (30 attempts):
     - Flagged text? → RESTART
     - None button? → CLICK, DONE
     - Grant Access? → CLICK, wait 3s
     - Wait 3s
   END LOOP
   ↓
   Not found? → RESTART
        ↓
[Continue to project creation]
```

## Captcha Flow

```
[Find signup button]
        ↓
[CLICK BUTTON - 1st click]
        ↓
[Wait 5 sec for captcha]
        ↓
[Image challenge?]
        ↓ Yes
[Click Audio button]
        ↓
[Download audio]
        ↓
[faster-whisper transcribes]
        ↓
[Enter text + Verify]
        ↓
[CLICK BUTTON - 2nd click]  ← MUST DO THIS!
        ↓
[Switch to temp mail]
        ↓
[OTP input page]
```

## Audio Transcription

Uses **faster-whisper** with the `tiny` model:
- Runs locally on CPU
- Very fast (~1-2 seconds for captcha audio)
- No API limits
- Falls back to Hugging Face Whisper API if needed

## Multiple Instances

Run multiple instances in parallel:

```bash
# 2 parallel instances with VPN
python3 multi_run.py --instances 2 -v

# 5 sequential runs (saves RAM)
python3 multi_run.py --sequential 5 -v

# Headless mode
python3 multi_run.py --instances 3 -v --headless
```

**Resource Requirements:**

| Instances | RAM Needed | VPNs Needed |
|-----------|------------|-------------|
| 1 | ~1.2GB | 1 |
| 2 | ~2.5GB | 2 |
| 3 | ~3.5GB | 3 |
| 5 | ~6GB | 5 |

**Each Instance:**
- Gets its own random VPN
- Own browser with random user agent
- Writes to shared accounts.json (file locked)
- Restarts with new VPN on failure

**Process:**
```
Instance 1 → VPN 1 (us-free-3) → Browser 1 → Account 1
Instance 2 → VPN 2 (jp-free-10) → Browser 2 → Account 2
Instance 3 → VPN 3 (nl-free-101) → Browser 3 → Account 3
```

If instance 2 fails → New VPN → Restart

## Auto-Retry

The script automatically retries when:
- **Captcha solving fails**
- **Account gets flagged**

On retry:
1. Refreshes temp mail page for new email
2. Starts fresh signup process
3. Continues until success or max retries

## Running on VPS (2 vCPU / 4GB RAM)

### Resource Requirements

| Instances | RAM Needed | Status |
|-----------|------------|--------|
| 1 | ~1.2GB | ✅ OK |
| 2-3 | ~2.5-3.5GB | ✅ OK |
| 4 | ~4-5GB | ⚠️ Needs swap |
| 5+ | 6GB+ | ❌ Not recommended |

### VPS Setup

```bash
# 1. Run setup script
chmod +x setup_vps.sh
sudo ./setup_vps.sh

# 2. Sequential (recommended for 4GB)
python3 multi_run.py --sequential 5 --headless

# 3. Parallel (2-3 max)
python3 multi_run.py --instances 2 --headless

# 4. Monitor resources
python3 monitor.py
```

### Multi-Instance Options

**Sequential** (saves RAM):
```bash
# Run 10 times, one after another
python3 multi_run.py --sequential 10 --headless
```

**Parallel** (faster, needs more RAM):
```bash
# Run 2 instances at once
python3 multi_run.py --instances 2 --headless
```

### Swap for Extra Memory

If running 4+ instances, add swap:
```bash
# Add 4GB swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Reduce swappiness
sudo sysctl vm.swappiness=10
```

## Project Structure

```
buddy-bot/
├── main.py              # Main entry point
├── config.py            # Configuration (password, API tokens)
├── requirements.txt     # Dependencies
├── core/
│   ├── driver.py        # Browser driver setup
│   └── base_page.py     # Base page class
├── pages/
│   ├── email_page.py    # Temp mail page
│   └── buddy_page.py    # Buddy works + captcha handling
├── utils/
│   ├── storage.py       # Account storage (JSON)
│   ├── human.py         # Human behavior simulation
│   ├── proxy.py         # Free proxy manager
│   └── audio_captcha.py # Audio captcha solver (faster-whisper)
└── data/
    └── accounts.json    # Saved accounts
```

## Saved Accounts

Accounts are saved to `data/accounts.json`:

```json
[
  {
    "email": "xxx@cleantempmail.com",
    "password": "0770Kwinssi@",
    "project": "Alpha_12345",
    "sandbox": "dev_1234567890",
    "date": "2024-01-15",
    "created": "2024-01-15T10:30:00"
  }
]
```

## Configuration

Edit `config.py`:

```python
DEFAULT_PASSWORD = "0770Kwinssi@"
HUGGINGFACE_API_TOKEN = "your_token_here"
```

## Default Password

`0770Kwinssi@`

## Requirements

- Python 3.8+
- Chrome browser
- ChromeDriver (auto-managed)
- ~500MB disk space (for whisper tiny model)
