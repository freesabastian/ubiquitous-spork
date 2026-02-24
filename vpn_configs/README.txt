OpenVPN Config Files
====================

Put your .ovpn files in this folder. The script will randomly pick one on each run.

How to Get Free OpenVPN Configs
===============================

1. VPNBook (FREE - No Registration)
   https://www.vpnbook.com/freevpn
   - Download the OpenVPN config bundle
   - Extract .ovpn files here
   - Password is on their website

2. ProtonVPN OpenVPN Configs
   https://protonvpn.com/vpn-resources/protonvpn-openvpn-config-files/
   - Free tier available
   - Download config files
   - Put them here

3. VPNGate (FREE)
   https://www.vpngate.net/en/
   - Download OpenVPN config files
   - Community maintained

4. FreeOpenVPN
   https://freeopenvpn.org/
   - Free accounts
   - Download .ovpn files

Format
======
Files should be named: country_location.ovpn
Example: us_new_york.ovpn

How It Works
============
- Script picks random VPN on start
- If captcha fails or account flagged:
  1. Closes browser
  2. Marks VPN as failed
  3. Picks new VPN
  4. Restarts with new user agent
- Failed VPNs are saved and not reused

Setup
=====
1. Put .ovpn files in this folder
2. Make sure openvpn is installed: sudo apt install openvpn
3. Run: python3 main.py --vpn

Tips
====
- More VPN configs = less chance of flagged IPs
- VPNBook updates their configs regularly
- Use configs from different countries
- Premium VPNs work better than free ones
