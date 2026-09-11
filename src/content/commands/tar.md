---
title: tar
desc: 打包归档与解压缩文件
tags: [compress, archive, disk]
---

```bash
# 解压 .tar.gz 到指定目录
tar -zxvf archive.tar.gz -C /target/dir/

# 将目录打包为 .tar.gz 压缩包
tar -zcvf archive.tar.gz /path/to/folder/
```

- `-c`：创建新的归档文件 (create)
- `-x`：解压释放归档文件 (extract)
- `-z`：使用 gzip 压缩/解压
- `-v`：显示处理文件的详细过程
- `-f`：指定操作的归档文件名（必须放在选项最后）
- `-C`：解压到指定的解压目录
