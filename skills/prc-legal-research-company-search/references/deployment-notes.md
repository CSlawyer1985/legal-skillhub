# 元力平台部署说明

## 发布信息

- Skill slug：`prc-legal-research-company-search`
- 版本：`1.2.0`
- 作者：华宇元典
- MCP Server：`yuandian-company`
- MCP URL：`https://open.chineselaw.com/mcp/company/stream`

平台连接器应使用 Stateless Streamable HTTP `POST`，发送 `Authorization: Bearer <secret>`、`Accept: application/json, text/event-stream` 和 `Content-Type: application/json`。GET 探测会得到 405，不得据此判为宕机。

## 发布门禁

1. `tools/list` 能发现与 26 个 route key 对应的企业能力。
2. 运行时工具模式是参数契约的 source of truth，适配器兼容 MCP 工具前缀。
3. 重点验证 `tyshxydm`、`pageNo`、年报 `year` 以及聚合摘要方法。
4. 使用平台密钥存储注入凭据，下载包和数据库元数据不得包含明文 Key。
5. 验证 200/201 与 `data`/`extra` 响应兼容，再灰度发布并保留回滚备份。
