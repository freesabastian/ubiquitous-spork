#!/bin/bash
# Setup script for GitHub Actions Runner
# Installs Python, Chrome, OpenVPN, ffmpeg, and bot dependencies

echo "========================================="
echo "Buddy Bot Setup for GitHub Actions"
echo "========================================="

# Update package lists
sudo apt-get update

# Install System Dependencies
echo "[*] Installing system dependencies..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    wget \
    unzip \
    xvfb \
    openvpn \
    iptables \
    iproute2 \
    ffmpeg \
    procps \
    psmisc

# Install Chromium & Chromedriver
echo "[*] Installing Chromium..."
sudo apt-get install -y chromium-browser chromium-chromedriver

# Setup Python environment
echo "[*] Setting up Python dependencies..."
# Use pip to install the requirements file
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Pre-download Whisper model
echo "[*] Pre-downloading Whisper AI model..."
python3 -c "
try:
    from faster_whisper import WhisperModel
    print('Downloading model...')
    WhisperModel('tiny', device='cpu', compute_type='int8')
    print('Model downloaded successfully!')
except Exception as e:
    print(f'Error downloading model: {e}')
"

echo "========================================="
echo "✓ Setup Complete! Ready to run main.py"
echo "========================================="
