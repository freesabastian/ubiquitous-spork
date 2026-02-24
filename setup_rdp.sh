#!/bin/bash
# Buddy Works Automation - Server Setup Script
# Installs Python, Chrome, XRDP (RDP), and App Dependencies

set -e

echo "=============================================="
echo "  BUDDY BOT SERVER SETUP"
echo "=============================================="

# 1. Update system and Fix GPG
echo "[*] Fixing potential GPG issues and updating system..."
# Fix Yarn GPG key if it's causing issues
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 62D54FD4003F6525 || true

# Run the broader start.sh dependency installer
if [ -f "start.sh" ]; then
    echo "[*] Running start.sh for comprehensive dependency setup..."
    chmod +x start.sh
    bash start.sh
else
    echo "[!] Warning: start.sh not found, falling back to manual system update."
    sudo apt update && sudo apt upgrade -y
fi

# 2. Additional Core Dependencies for Undetected Chrome & GitHub Actions
echo "[*] Ensuring core dependencies for Chrome (stealth mode)..."
sudo apt install -y python3-pip python3-venv wget curl unzip fonts-liberation \
    libappindicator3-1 libayatana-appindicator3-1 libasound2t64 libasound2 \
    libatk-bridge2.0-0t64 libatk-bridge2.0-0 libatk1.0-0t64 libatk1.0-0 \
    libc6 libcairo2 libcups2t64 libcups2 libdbus-1-3 libexpat1 libfontconfig1 \
    libgbm1 libgcc-s1 libgcc1 libgdk-pixbuf2.0-0 libglib2.0-0t64 libglib2.0-0 \
    libgtk-3-0t64 libgtk-3-0 libnspr4 libnss3 libpango-1-0-0 libpangocairo-1.0-0 \
    libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 \
    libxtst6 lsb-release xdg-utils openvpn xvfb ffmpeg scrot python3-tk python3-dev

# 3. Setup Python Virtual Environment and Requirements
echo "[*] Setting up Python environment..."
# Ensure pip is upgraded globally first
sudo python3 -m pip install --upgrade pip

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install requirements
source venv/bin/activate
echo "[*] Upgrading pip in virtual environment..."
python3 -m pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    echo "[*] Installing requirements from requirements.txt..."
    python3 -m pip install -r requirements.txt
fi

echo ""
echo "=============================================="
echo "  SETUP & INITIALIZATION COMPLETE!"
echo "=============================================="
echo "All core dependencies, RDP, Chrome, and Python"
echo "environment have been configured."
echo ""
echo "To run the bot:"
echo "1. source venv/bin/activate"
echo "2. python main.py"
echo "=============================================="
