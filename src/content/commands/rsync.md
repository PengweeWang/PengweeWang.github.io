---
title: rsync
desc: 增量文件同步与断点续传备份
tags: [sync, backup, network]
---

```bash
rsync -avzP --exclude=".git" /local/dir/ user@remote:/path/
```

- `-a`：归档模式（递归、保留文件属性与符号链接）
- `-v`：显示详细进度
- `-z`：传输时开启压缩
- `-P`：断点续传并打印实时传输速率
- **避坑**：源目录结尾带 `/` 仅同步目录内文件；不带 `/` 则连同目录本身一起同步。
