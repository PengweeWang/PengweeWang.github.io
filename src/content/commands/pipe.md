---
title: "| (管道符)"
desc: 将前一个命令的标准输出作为后一个命令的标准输入
tags: [stream, pipeline, shell]
related: [redirect, grep, head, tail]
---

```bash
# 过滤进程列表并统计符合条件的数量
ps aux | grep "nginx" | wc -l

# 查看大文件时配合分页器滚动浏览
cat long-log.txt | less
```

- **核心概念**：`command1 | command2`。管道左侧命令的标准输出（stdout）直接对接右侧命令的标准输入（stdin）。
- **注意**：管道默认**只传递标准输出（stdout）**，不传递标准错误（stderr）。
- **传递错误输出**：若需要把标准错误也一并传入管道，可使用 `|&`（Bash 4.0+）或 `2>&1 |`。
