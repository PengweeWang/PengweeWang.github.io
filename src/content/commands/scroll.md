---
title: 终端翻页与滚屏技巧
desc: 纯键盘与无鼠标环境下的终端历史回滚、分屏与TUI交互翻页技巧
tags: [terminal, scroll, shortcut, shell]
related: [less, pipe, tail]
---

```bash
# 避免终端刷屏最通用的做法：利用管道传给分页器
dmesg | less
journalctl -xe | less
```

### 1. 终端模拟器原生回滚（查看已输出的历史信息）

当命令输出已打印在终端中，滚动终端自身的回滚缓冲区（Scrollback Buffer）：

- **整页翻滚**：`Shift + PageUp`（向上翻页） / `Shift + PageDown`（向下翻页）
  - _笔记本键盘或 60%/87% 紧凑键盘若无独立 PgUp/PgDn，通常是组合键：`Shift + Fn + ↑` / `Shift + Fn + ↓`_
- **回滚搜索**：现代终端（如 Foot）普遍支持 `Ctrl + Shift + r`，直接输入关键字即可高亮并跳到历史输出位置
- **自定义平滑滚动**：在终端配置（如 `~/.config/foot/foot.ini`）中可将逐行滚动映射为 `Ctrl + Shift + ↑/↓`，半页滚动映射为 `Ctrl + Shift + k/j`

### 2. TUI 全屏交互程序内翻页（如 OpenCode、Vim、htop）

启动这类程序后，终端切入了备用屏幕（Alternate Screen），终端级的 `Shift + ...` 快捷键不会传递给程序内部，必须使用**程序自身的按键**（**不要加 Shift**）：

- 单按 **`PageUp` / `PageDown`**（或 `Fn + ↑/↓`）：消息历史与长文本上下翻页
- 消息列表中使用 **`↑` / `↓`** 逐行移动浏览
- 支持 Vim 键位的工具可使用 **`Ctrl + u`**（上翻半屏）与 **`Ctrl + d`**（下翻半屏）
- 若焦点停留在底部输入框内，通常按 **`Esc`** 或 **`Tab`** 将焦点切换至消息列表区，再按翻页键滚动

### 3. 终端复用器 tmux 滚动模式

纯键盘运维多窗口环境时的最佳实践：

- 按前缀组合键 **`Ctrl + b`** 然后按 **`[`** 进入拷贝/浏览模式
- 此时可以使用 **方向键** 或 Vim 移动键（`h/j/k/l`、`Ctrl+u/d`、`g/G`）自由滚屏
- 浏览完毕按 **`q`** 或 `Enter` 退出
