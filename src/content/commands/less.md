---
title: less
desc: 终端输出与长文本分页浏览神器（全键盘滚动与快速搜索）
tags: [text, pager, view, scroll]
related: [pipe, tail, head, scroll, grep]
---

```bash
# 查看长文本文件
less /var/log/syslog

# 配合管道分页查看命令的长输出（避免刷屏丢失上下文）
dmesg | less
systemctl list-units | less

# 常用参数组合：-N 显示行号，-R 保持 ANSI 彩色代码
less -NR /var/log/nginx/access.log
```

- **上下滚动**：`j` 或 `↓` 向下滚一行，`k` 或 `↑` 向上滚一行
- **全屏翻页**：`空格` 或 `Ctrl + f` 向下翻一页，`b` 或 `Ctrl + b` 向上翻一页
- **半屏翻页**：`d` 向下翻半屏，`u` 向上翻半屏
- **快速搜索**：输入 `/关键词` 向下搜索，输入 `?关键词` 向上搜索；按 `n` 跳到下一个匹配项，`N` 跳到上一个
- **首尾跳转**：`g` 快速跳到文件开头，`G` 快速跳到文件末尾
- **实时追踪**：按 `Shift + f` 进入类似 `tail -f` 的实时监听模式，按 `Ctrl + c` 退出监听并保留当前浏览位置
- **退出**：按 `q` 退出
