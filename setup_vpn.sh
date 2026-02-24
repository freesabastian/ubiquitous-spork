#!/bin/bash
# Setup Free VPN on Linux
# Choose one of the following VPNs

echo "=============================================="
echo "  FREE VPN SETUP"
echo "=============================================="
echo ""
echo "Choose a VPN to install:"
echo ""
echo "1. Proton VPN (Unlimited free, recommended)"
echo "2. Windscribe (10GB/month)"
echo "3. PrivadoVPN (10GB/month)"
echo ""
echo "4. Check Tor status"
echo "5. Start Tor"
echo ""
echo "Enter choice (1-5): "
read choice

case $choice in
    1)
        echo ""
        echo "[*] Installing Proton VPN..."
        sudo apt update
        sudo apt install -y wget
        wget https://protonvpn.com/download/protonvpn-stable_1.0.0_amd64.deb
        sudo apt install -y ./protonvpn-stable_1.0.0_amd64.deb
        rm protonvpn-stable_1.0.0_amd64.deb
        echo ""
        echo "[+] Proton VPN installed!"
        echo "Run: protonvpn"
        ;;
    2)
        echo ""
        echo "[*] Installing Windscribe..."
        sudo apt update
        wget https://windscribe.com/install/desktop/gpt/3deb909/windscribe_2.4.11_amd64.deb
        sudo apt install -y ./windscribe_2.4.11_amd64.deb
        rm windscribe_2.4.11_amd64.deb
        echo ""
        echo "[+] Windscribe installed!"
        echo "Run: windscribe"
        ;;
    3)
        echo ""
        echo "[*] Installing PrivadoVPN..."
        echo "Download from: https://privadovpn.com/download"
        echo ""
        echo "For Linux CLI:"
        echo "  wget https://privado.io/install-cli.sh"
        echo "  chmod +x install-cli.sh"
        echo "  sudo ./install-cli.sh"
        ;;
    4)
        echo ""
        echo "[*] Checking Tor status..."
        systemctl status tor
        ;;
    5)
        echo ""
        echo "[*] Starting Tor..."
        sudo systemctl start tor
        sudo systemctl enable tor
        echo "[+] Tor started!"
        echo ""
        echo "Testing Tor connection..."
        curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
