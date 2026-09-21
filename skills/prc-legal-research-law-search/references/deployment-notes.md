# 元力平台部署说明

## 发布信息

- Skill slug：`prc-legal-research-law-search`
- 版本：`1.2.0`
- 作者：华宇元典
- MCP Server：`yuandian-law`
- MCP URL：`https://open.chineselaw.com/mcp/law/stream`

平台连接器应使用 Stateless Streamable HTTP `POST`，发送 `Authorization: Bearer <secret>`、`Accept: application/json, text/event-stream` 和 `Content-Type: application/json`。GET 探测会得到 405，不得据此判为宕机。

## 发布门禁

1. `tools/list` 能发现五项法律工具。
2. 运行时工具模式是参数契约的 source of truth。
3. 使用平台密钥存储注入凭据，下载包和数据库元数据不得包含明文 Key。
4. 验证 JSON 与 SSE 响应解析、401/403、429 和超时状态。
5. 灰度通过后再替换旧版；保留旧目录和数据库记录备份以便回滚。
