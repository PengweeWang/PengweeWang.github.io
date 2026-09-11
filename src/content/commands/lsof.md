---
title: lsof
desc: 查看端口占用及进程打开的文件句柄
tags: [network, port, process]
---

```bash
lsof -i :8080
```

- `-i :端口`：指定端口过滤（排查本地/远程端口被谁占用最快的方式）
- `-p <PID>`：列出指定进程打开的所有文件与连接
- `-u <用户>`：列出指定用户打开的文件
- `-i TCP:LISTEN`：仅查看当前正在监听中的所有 TCP 端口
