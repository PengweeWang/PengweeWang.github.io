---
title: grep
desc: 递归检索文本关键字并打印上下文
tags: [text, search, log]
related: [pipe, head, tail]
---

```bash
grep -rnI "ERROR" ./logs/ -C 3
```

- `-r`：递归子目录检索
- `-n`：打印匹配行的行号
- `-I`：自动忽略二进制文件
- `-i`：忽略大小写
- `-C 3`：显示匹配行前后各 3 行上下文（排查报错利器）
