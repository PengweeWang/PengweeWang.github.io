---
title: tail
desc: 查看文件末尾若干行及实时追踪更新
tags: [text, log]
related: [head, grep]
---

```bash
# 实时追踪日志文件新增内容（最常用的排查命令）
tail -f /var/log/nginx/access.log

# 输出文件最后 50 行并持续追踪
tail -50f /var/log/syslog
```

- `-f`：循环读取（follow），文件新增内容时实时刷新在终端
- `-F`：同 `-f`，但支持文件被重命名或轮转（logrotate）时自动重试打开
- `-n <行数>` 或 `-<行数>`：输出末尾指定的行数（默认最后 10 行）
- `-c <字节数>`：输出末尾指定的字节数
