---
title: Linux 无桌面环境下用 Cage + Foot 打造现代终端
description: 记录在 Linux（服务器、迷你主机、树莓派等）无桌面环境下，用 Cage 与 Foot 快速配出一套支持中文、Nerd Font、Emoji 和隐藏鼠标的全屏现代终端。
publishDate: '2026-09-14'
tags:
  - linux
  - terminal
  - wayland
  - raspberrypi
draft: false
language: Chinese
comment: true
ai: assisted
---

给没有安装图形桌面的 Linux 机器（服务器、迷你主机、开发板等）接上显示器时，原生 TTY 字符终端无法显示中文、Nerd Font 图标和 Emoji，遇到这些字符全是一堆方块或问号。

要解决这个问题，并不需要去安装臃肿的完整桌面环境（如 GNOME、XFCE）。通过 **Cage（极简 Wayland Kiosk）+ Foot（轻量终端）**，可以在纯命令行系统下直接拉起一个全屏、硬件加速、字库完整的现代终端。

---

## 快速配置

### 1. 安装软件包

**Debian / Ubuntu / Raspberry Pi OS：**

```bash
sudo apt update
sudo apt install -y cage foot fontconfig fonts-noto-cjk fonts-noto-color-emoji
```

**Arch Linux：**

```bash
sudo pacman -S cage foot fontconfig noto-fonts-cjk noto-fonts-emoji
```

确保系统已启用 UTF-8 中文字符集：

```bash
sudo sed -i 's/^# *zh_CN.UTF-8 UTF-8/zh_CN.UTF-8 UTF-8/' /etc/locale.gen
sudo locale-gen
```

### 2. 补齐 Nerd Font 图标字体

中文字体（`Noto Sans Mono CJK SC`）和彩色 Emoji（`Noto Color Emoji`）在上面一步已经装好。终端里常用的 Git 分支、文件类型等特殊图标，需要再补一个 Nerd Font（比如 `FiraCode Nerd Font Mono`）：

```bash
sudo mkdir -p /usr/local/share/fonts/nerd
# 把 FiraCodeNerdFontMono_Regular.ttf 放入此目录
sudo fc-cache -f
```

检查字体是否全部就绪：

```bash
fc-list : family | grep -E 'FiraCode|Noto Sans Mono CJK|Noto Color Emoji'
```

### 3. 配置 Foot 终端

创建或编辑配置文件 `~/.config/foot/foot.ini`。关键是配置好字体回退链（英文图标 → 中文 → Emoji）以及打字时自动隐藏鼠标：

```ini
[main]
# 字体回退链：优先英文和图标，缺字回退到中文，再缺回退到彩色 Emoji
font=FiraCode Nerd Font Mono:size=14,Noto Sans Mono CJK SC:size=14,Noto Color Emoji:size=14
dpi-aware=no

[mouse]
# 打字时自动隐藏鼠标指针
hide-when-typing=yes

[scrollback]
lines=10000

[cursor]
style=block
blink=yes

[colors]
alpha=1.0
background=1e1e2e
foreground=cdd6f4

regular0=45475a
regular1=f38ba8
regular2=a6e3a1
regular3=f9e2af
regular4=89b4fa
regular5=f5c2e7
regular6=94e2d5
regular7=bac2de

bright0=585b70
bright1=f38ba8
bright2=a6e3a1
bright3=f9e2af
bright4=89b4fa
bright5=f5c2e7
bright6=94e2d5
bright7=a6adc8

[key-bindings]
# 无鼠标时的滚屏按键（支持逐行与半页滚动）
scrollback-up-line=Control+Shift+Up
scrollback-down-line=Control+Shift+Down
scrollback-up-half-page=Control+Shift+k
scrollback-down-half-page=Control+Shift+j
```

### 4. 运行与配置快捷别名

在物理屏幕的 TTY 登录后，直接输入：

```bash
cage foot
```

屏幕会瞬间切入全屏终端。使用完毕在里面输入 `exit`，即可退出回到原生 TTY。

如果嫌每次敲两个单词麻烦，在 `~/.bashrc` 里加个别名：

```bash
echo "alias term='cage foot'" >> ~/.bashrc
source ~/.bashrc
```

后续直接输入 `term` 就能启动。

### 5. （可选）彻底隐藏鼠标指针

上面的配置开启了 `hide-when-typing=yes`，键盘敲字时光标会自动隐藏，晃动鼠标时会重新出现。

如果你根本不接鼠标，或者讨厌屏幕正中偶尔冒出来的鼠标箭头，可以用一段 Python 脚本在系统里生成一个 1 像素的全透明空白光标主题：

```bash
sudo python3 - << 'EOF'
import os, struct

theme_dir = '/usr/share/icons/blank'
cursors_dir = os.path.join(theme_dir, 'cursors')
os.makedirs(cursors_dir, exist_ok=True)

with open(os.path.join(theme_dir, 'index.theme'), 'w') as f:
    f.write('[Icon Theme]\nName=Blank\nComment=Invisible Cursor Theme\n')

# 构造 1x1 全透明 Xcursor 二进制结构
magic = b'Xcur'
header_size = 16
version = 0x00010000
ntoc = 1
toc_type = 0xfffd0002
toc_subtype = 16
toc_pos = 28
chunk_header_size = 36
chunk_type = 0xfffd0002
chunk_subtype = 16
chunk_ver = 1
width = 1
height = 1
xhot = 0
yhot = 0
delay = 0
pixels = struct.pack('<I', 0)

data = struct.pack('<4s15I',
    magic, header_size, version, ntoc,
    toc_type, toc_subtype, toc_pos,
    chunk_header_size, chunk_type, chunk_subtype, chunk_ver,
    width, height, xhot, yhot, delay
) + pixels

cursor_names = [
    'default', 'left_ptr', 'right_ptr', 'hand', 'pointer',
    'text', 'xterm', 'cross', 'wait', 'watch', 'move'
]

with open(os.path.join(cursors_dir, 'default'), 'wb') as f:
    f.write(data)

for name in cursor_names:
    target = os.path.join(cursors_dir, name)
    if not os.path.exists(target):
        os.symlink('default', target)
EOF
```

生成后，通过指定环境变量启动：

```bash
XCURSOR_THEME=blank cage foot
```

此时不管怎么晃动鼠标，屏幕上都绝对不会出现任何指针。想一劳永逸的话，直接把别名改成 `alias term='XCURSOR_THEME=blank cage foot'` 即可。

---

## 原理解析与常见疑问

### 为什么原生 TTY 会乱码？

Linux 内核自带的虚拟控制台（fbcon）是一个非常早期的文字界面设计：

- **字形槽位限制**：它使用的是点阵位图字体，内核显存中为字符表预留的槽位上限只有 256 到 512 个。
- **Unicode 缺字**：常用汉字上千个，加上终端主题里丰富的特殊图标（分支、箭头、各类状态符号），根本不可能塞进这区区几百个槽位里，超出部分自然只能显示为方块或菱形问号。
- **渲染机制陈旧**：内核控制台不支持 FreeType 矢量字体抗锯齿，也不支持真彩色与彩色 Emoji 渲染。

### 为什么选择 Cage + Foot？

很多人的第一直觉是“要终端窗口就得先装桌面（Desktop Environment）”。其实桌面环境（如 GNOME、XFCE、PIXEL）主要负责的是窗口管理器、任务栏、桌面图标、系统托盘和后台各种服务守护进程。如果我们仅仅为了看命令输出，装这整套东西纯属浪费系统资源。

- **Cage**：一个体积仅几百 KB 的 Wayland Kiosk 合成器。它的唯一职责就是直接接管显卡 DRM/KMS 接口，全屏运行你指定的某一个应用程序，不提供任何多余的桌面元素。
- **Foot**：用 C 编写的轻量终端模拟器，内存占用通常只有十几兆，毫秒级启动。更重要的是它完整支持 HarfBuzz 文本塑形、GPU 加速渲染以及灵活的多字体回退。

两者结合，在视觉体验上完全等同于一个“高清、平滑、全彩色的终极版 TTY”，但系统开销几乎可以忽略不计。

### 字体回退链是如何工作的？

在 `foot.ini` 中配置的这一行：

```ini
font=FiraCode Nerd Font Mono:size=14,Noto Sans Mono CJK SC:size=14,Noto Color Emoji:size=14
```

Foot 会按顺序查找字形：

1. 先在 `FiraCode Nerd Font Mono` 中寻找字符。所有标准的 ASCII 字符、代码连字以及 Nerd Font 专用的图标私有区编码（Private Use Area）都会由它渲染。
2. 当遇到汉字时，FiraCode 中没有对应的字形，Foot 会自动向后回退到 `Noto Sans Mono CJK SC` 提取中文字形。
3. 当遇到 Emoji 表情符号时，中文字体中同样没有，Foot 会继续回退到 `Noto Color Emoji`，输出带有原生色彩的彩色表情。

通过这条链条，既保证了英文字符和终端特殊图标的等宽对齐，又兼顾了中文和彩色表情的正常显示。
