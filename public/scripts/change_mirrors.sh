#!/bin/bash
# ==============================================================================
# Script Name: change_mirrors.sh
# Description: One-click script to switch Raspberry Pi OS / Debian mirrors to
#              Tsinghua University (TUNA) domestic mirrors in China.
# Supported OS: Debian 11 (Bullseye) / Debian 12 (Bookworm) / Debian 13 (Trixie)+
# Supported Formats: DEB822 (.sources) and legacy sources.list (.list)
# ==============================================================================

set -e

# Ensure running with root or sudo privileges
if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run this script with sudo: sudo bash $0"
    exit 1
fi

echo "=================================================="
echo "    Raspberry Pi / Debian Mirror Switch Script    "
echo "=================================================="

# 1. Detect OS version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    CODENAME=${VERSION_CODENAME:-trixie}
    echo "[+] Detected OS: $PRETTY_NAME ($CODENAME)"
else
    echo "[-] Unable to read /etc/os-release, defaulting to trixie"
    CODENAME="trixie"
fi

BACKUP_SUFFIX=".bak.$(date +%Y%m%d_%H%M%S)"

# 2. Configure APT repository mirrors
echo "[+] Configuring APT package mirrors..."

# --- Case A: Modern Debian 12 / 13 (DEB822 format, .sources) ---
if [ -f /etc/apt/sources.list.d/debian.sources ]; then
    echo "    -> Found DEB822 configuration (/etc/apt/sources.list.d/debian.sources)"
    cp -v /etc/apt/sources.list.d/debian.sources "/etc/apt/sources.list.d/debian.sources${BACKUP_SUFFIX}"
    sed -i 's|http[s]*://deb.debian.org/debian/|https://mirrors.tuna.tsinghua.edu.cn/debian/|g' /etc/apt/sources.list.d/debian.sources
    sed -i 's|http[s]*://deb.debian.org/debian-security/|https://mirrors.tuna.tsinghua.edu.cn/debian-security/|g' /etc/apt/sources.list.d/debian.sources
fi

if [ -f /etc/apt/sources.list.d/raspi.sources ]; then
    echo "    -> Found Raspberry Pi archive DEB822 configuration (/etc/apt/sources.list.d/raspi.sources)"
    cp -v /etc/apt/sources.list.d/raspi.sources "/etc/apt/sources.list.d/raspi.sources${BACKUP_SUFFIX}"
    sed -i 's|http[s]*://archive.raspberrypi.com/debian/|https://mirrors.tuna.tsinghua.edu.cn/raspberrypi/|g' /etc/apt/sources.list.d/raspi.sources
fi

# --- Case B: Legacy format (/etc/apt/sources.list and raspi.list) ---
if [ -f /etc/apt/sources.list ] && [ -s /etc/apt/sources.list ]; then
    echo "    -> Found legacy sources configuration (/etc/apt/sources.list)"
    cp -v /etc/apt/sources.list "/etc/apt/sources.list${BACKUP_SUFFIX}"
    sed -i 's|http[s]*://deb.debian.org/debian/|https://mirrors.tuna.tsinghua.edu.cn/debian/|g' /etc/apt/sources.list
    sed -i 's|http[s]*://security.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security/|g' /etc/apt/sources.list
    sed -i 's|http[s]*://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security/|g' /etc/apt/sources.list
fi

if [ -f /etc/apt/sources.list.d/raspi.list ]; then
    echo "    -> Found legacy Raspberry Pi archive configuration (/etc/apt/sources.list.d/raspi.list)"
    cp -v /etc/apt/sources.list.d/raspi.list "/etc/apt/sources.list.d/raspi.list${BACKUP_SUFFIX}"
    sed -i 's|http[s]*://archive.raspberrypi.org/debian/|https://mirrors.tuna.tsinghua.edu.cn/raspberrypi/|g' /etc/apt/sources.list.d/raspi.list
    sed -i 's|http[s]*://archive.raspberrypi.com/debian/|https://mirrors.tuna.tsinghua.edu.cn/raspberrypi/|g' /etc/apt/sources.list.d/raspi.list
fi

# 3. Configure Python pip mirror (Tsinghua + Aliyun backup)
echo "[+] Configuring Python pip mirror..."
TARGET_USER=${SUDO_USER:-$USER}
USER_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)

if [ -d "$USER_HOME" ]; then
    PIP_CONF_DIR="$USER_HOME/.config/pip"
    mkdir -p "$PIP_CONF_DIR"
    cat << 'EOF' > "$PIP_CONF_DIR/pip.conf"
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
extra-index-url = https://mirrors.aliyun.com/pypi/simple/
trusted-host =
    pypi.tuna.tsinghua.edu.cn
    mirrors.aliyun.com
EOF
    chown -R "$TARGET_USER:$TARGET_USER" "$USER_HOME/.config"
    echo "    -> Saved pip configuration to: $PIP_CONF_DIR/pip.conf"
fi

# 4. Verify and update package index
echo "[+] Running 'apt update' to verify new mirror connectivity..."
apt update

echo "=================================================="
echo "  [OK] Mirror setup complete! Update succeeded.   "
echo "=================================================="
