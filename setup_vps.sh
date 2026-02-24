#!/bin/bash
# VPS Setup Script for Buddy-Bot
# For 2 vCPU / 4GB RAM VPS

echo "=== VPS SETUP FOR BUDDY-BOT ==="

# Update
sudo apt update && sudo apt upgrade -y

# Install Chrome
echo "[*] Installing Chrome..."
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# Install Python & pip
echo "[*] Installing Python..."
sudo apt install -y python3 python3-pip python3-venv

# Install dependencies for Chrome
sudo apt install -y \
    fonts-liberation \
    libasound2 \
    libatk-adapter-gtk2-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils

# Add swap (4GB) for memory headroom
echo "[*] Adding 4GB swap..."
sudo fallocate -l 4G /swapfile || true
sudo chmod 600 /swapfile || true
sudo mkswap /swapfile || true
sudo swapon /swapfile || true

# Add to fstab for persist
if ! grep -q "/swapfile" /etc/fstab; then
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# Optimize swappiness
sudo sysctl vm.swappiness=10
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf

# Create virtual environment
echo "[*] Creating virtual environment..."
cd /opt
sudo git clone <your-repo> buddy-bot || true
cd buddy-bot
sudo python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Download whisper model (do once)
echo "[*] Downloading whisper model..."
python3 -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')"

echo ""
echo "=== SETUP COMPLETE ==="
echo ""
echo "Memory info:"
free -h
echo ""
echo "Run:"
echo "  cd /opt/buddy-bot"
echo "  source venv/bin/activate"
echo "  python3 multi_run.py --sequential 5 --headless"
echo ""
echo "For parallel (2-3 instances max on 4GB):"
echo "  python3 multi_run.py --instances 2 --headless"
