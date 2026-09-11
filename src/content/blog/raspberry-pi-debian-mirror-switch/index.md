---
title: 树莓派换源踩坑与脚本：Debian 12/13 deb822 新格式
description: 记录 Debian 12 与 13 采用 deb822 格式导致传统 sources.list 换源失效的问题，并提供自动兼容新旧格式的换源脚本。
publishDate: '2026-09-11'
tags:
  - linux
  - debian
  - raspberrypi
  - shell
draft: false
language: Chinese
comment: true
ai: assisted
---

新拿到一台树莓派，连上热点 SSH 进去准备换国内源。打开 `/etc/apt/sources.list` 时发现里面是空的，网上搜到的老换源教程写进去不仅不生效，甚至还会引发重复源警告。

排查后发现，Debian 自 12 (Bookworm) 引入并在 13 (Trixie) 中全面启用了 **deb822** 格式的源配置。

## 格式差异：传统格式 vs deb822

在 Debian 11 及更早版本中，软件源配置为单行文本格式：

- **Debian 基础源**：`/etc/apt/sources.list`
- **树莓派专属源**：`/etc/apt/sources.list.d/raspi.list`

```text
# 传统单行格式
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main contrib non-free non-free-firmware
```

而从 Debian 12 / 13 开始，APT 转向了类似 RFC 822 风格的 stanza 格式，文件后缀也改为了 `.sources`：

- **Debian 基础源**：`/etc/apt/sources.list.d/debian.sources`
- **树莓派专属源**：`/etc/apt/sources.list.d/raspi.sources`
- 原先的 `/etc/apt/sources.list` 默认保留为空文件。

新的 `debian.sources` 结构如下：

```text
Types: deb
URIs: https://mirrors.tuna.tsinghua.edu.cn/debian/
Suites: trixie trixie-updates
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp

Types: deb
URIs: https://mirrors.tuna.tsinghua.edu.cn/debian-security/
Suites: trixie-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp
```

树莓派专属的 `raspi.sources` 类似：

```text
Types: deb
URIs: https://mirrors.tuna.tsinghua.edu.cn/raspberrypi/
Suites: trixie
Components: main
Signed-By: /usr/share/keyrings/raspberrypi-archive-keyring.pgp
```

直接修改这些 `.sources` 文件中的 `URIs` 字段，换源才能真正生效。

## 自动化换源脚本

为了之后给新设备配置时不再手动翻文件改 URL，写了一个一键脚本：

- 自动判断系统是新版 deb822 (`.sources`) 还是旧版 (`.list` / `sources.list`)。
- 修改前自动为原配置生成时间戳备份（如 `.bak.20260911_140500`）。
- 同时替换 Debian 官方源与树莓派专属源为清华 TUNA 镜像站。
- 顺带将当前用户的 Python `pip` 配置指向清华源与阿里源。
- 自动执行 `apt update` 验证连通性。

完整脚本文件：[change_mirrors.sh](/scripts/change_mirrors.sh)

### 脚本代码

```bash
#!/bin/bash
# Script Name: change_mirrors.sh
# Description: Switch Raspberry Pi OS / Debian mirrors to Tsinghua (TUNA)
# Supported OS: Debian 11+ / Bookworm / Trixie (both deb822 and legacy formats)

set -e

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

# Modern Debian 12 / 13 (DEB822 format, .sources)
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

# Legacy format (/etc/apt/sources.list and raspi.list)
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

# 3. Configure Python pip mirror
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
```

### 使用方式

**本地执行**：
```bash
sudo bash change_mirrors.sh
```

**远程管道执行（无需拷贝文件）**：
```bash
ssh <user>@<host> 'sudo bash -s' < change_mirrors.sh
```
