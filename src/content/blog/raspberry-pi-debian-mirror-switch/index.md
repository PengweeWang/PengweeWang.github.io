---
title: 树莓派换源踩坑与脚本：Debian 12/13 deb822 新格式
description: 记录 Debian 12 与 13 改用 deb822 格式导致老方法换源失效的坑，以及兼容新旧格式的换源脚本。
publishDate: '2026-09-11'
tags:
  - linux
  - debian
  - raspberrypi
  - shell
draft: false
language: Chinese
comment: true
ai: ai
---

新搞了台树莓派，连上热点 SSH 准备换国内源。习惯性打开 `/etc/apt/sources.list`，发现里面居然是空的。按照老习惯把清华源贴进去，跑 `apt update` 却冒出一堆重复源（duplicate sources）警告，源也没真正换成。

排查后发现，从 Debian 12 (Bookworm) 开始引入、Debian 13 (Trixie) 全面落地，APT 默认改用了 deb822 格式的 stanza 配置，不再使用传统的单行 `sources.list`。

## 为什么 sources.list 不管用了？

在 Debian 11 及更早版本中，软件源配置是单行格式：Debian 源在 `/etc/apt/sources.list`，树莓派专属源在 `/etc/apt/sources.list.d/raspi.list`。

```text
# 传统单行格式
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main contrib non-free non-free-firmware
```

而新版系统里，原来的 `/etc/apt/sources.list` 默认直接留空，真正的配置挪到了 `/etc/apt/sources.list.d/*.sources`，采用多行的 RFC 822 stanza 风格。

实际生效的文件有两个：
- Debian 系统源：`/etc/apt/sources.list.d/debian.sources`
- 树莓派专属源：`/etc/apt/sources.list.d/raspi.sources`

`debian.sources` 的结构长这样：

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

树莓派专用的 `raspi.sources` 也是同样的多行结构：

```text
Types: deb
URIs: https://mirrors.tuna.tsinghua.edu.cn/raspberrypi/
Suites: trixie
Components: main
Signed-By: /usr/share/keyrings/raspberrypi-archive-keyring.pgp
```

换源只要把对应配置块里的 `URIs` 改成镜像站地址即可。

## 自动化换源脚本

新设备多了每次手动找 `.sources` 改 `URIs` 挺繁琐的，顺手写了个脚本：

1. 兼容新旧格式：优先检测并替换 deb822（`.sources`），没有就兜底处理旧版的 `sources.list` / `raspi.list`。
2. 自动备份：改之前带时间戳备份原文件（比如 `.sources.bak.20260911_xxx`），改挂了随时能拷回去。
3. 把 Debian 系统源和树莓派官方源都切到清华 TUNA，顺带给当前用户配好 pip 镜像（清华主源 + 阿里备用）。
4. 跑一次 `apt update` 验证连通性。

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

如果脚本在本地，直接跑：
```bash
sudo bash change_mirrors.sh
```

如果刚 SSH 连上新板子不想把脚本传过去，也可以从本地通过管道直接送过去执行：
```bash
ssh <user>@<host> 'sudo bash -s' < change_mirrors.sh
```
