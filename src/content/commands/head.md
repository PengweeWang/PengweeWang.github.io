---
title: head
desc: 查看文件开头若干行
tags: [text, preview]
related: [tail, grep]
---

```bash
# 查看文件前 20 行内容
head -n 20 /var/log/syslog

# 查看多个文件的前 10 行并输出文件名头信息
head file1.txt file2.txt
```

- `-n <行数>`：输出指定行数（默认前 10 行）
- `-c <字节数>`：输出指定字节数
- `-q`：静默模式，查看多个文件时不打印文件名标题
