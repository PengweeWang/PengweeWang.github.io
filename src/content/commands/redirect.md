---
title: '> / >> (重定向)'
desc: 标准输入输出重定向与错误输出分流
tags: [stream, io, redirect]
related: [pipe]
---

```bash
# 1. 覆盖写入文件
echo "Hello Linux" > output.txt

# 2. 追加写入文件
echo "Append line" >> output.txt

# 3. 将标准输出与错误输出合并重定向到文件
command > app.log 2>&1
# 或简写形式（Bash 4.0+）
command &> app.log

# 4. 丢弃所有输出（黑洞设备）
command > /dev/null 2>&1
```

- `>`：覆盖写入目标文件（若文件不存在则创建，存在则清空重写）
- `>>`：追加写入目标文件末尾
- `<`：标准输入重定向（从文件读取内容作为命令输入）
- `2>`：仅重定向标准错误输出 (stderr)
- `2>&1`：将文件描述符 2 (stderr) 重定向到文件描述符 1 (stdout)
