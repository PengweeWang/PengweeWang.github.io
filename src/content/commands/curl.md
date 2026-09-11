---
title: curl
desc: 网络请求测试与接口调试工具
tags: [http, api, network]
---

```bash
# 查看请求耗时、状态码与响应头
curl -Iv https://example.com

# 发送 POST JSON 请求
curl -X POST https://api.example.com/data \
  -H "Content-Type: application/json" \
  -d '{"key":"value"}'
```

- `-I`：仅获取 HTTP 响应头 (HEAD 请求)
- `-v`：详细输出握手与请求全过程 (verbose)
- `-s`：静默模式，不输出进度统计
- `-L`：自动跟随 301/302 重定向
- `-o <file>`：将响应内容保存为文件
