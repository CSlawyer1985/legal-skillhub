# 元力平台 MCP 接入门禁

## 连接目标

- Server：`yuandian-case`
- URL：`https://open.chineselaw.com/mcp/case/stream`
- 传输：Stateless Streamable HTTP，仅使用 `POST`
- 请求头：`Authorization: Bearer <YUANDIAN_API_KEY>`、`Accept: application/json, text/event-stream`、`Content-Type: application/json`
- 该端点不支持 GET/SSE 常驻连接；`GET` 返回 `405` 不是服务离线。

## 平台执行顺序

1. 优先使用元力平台已经绑定的 `yuandian-case`，普通 Skill 会话不得修改全局 MCP 配置或重启网关。
2. 调用 `tools/list`（能力发现），确认所需工具存在。
3. 读取运行时工具模式（runtime tool schema）；工具名、参数类型、枚举和必填项以运行时工具模式为准，即 source of truth。
4. 使用无副作用、最小返回量的检索请求探测鉴权和响应解析。
5. 只有探测成功才进入案例检索。

## 状态映射

| 状态 | 判定 | 行为 |
|---|---|---|
| `READY` | 能力发现和最小探测成功 | 执行检索 |
| `NOT_CONFIGURED` | 平台没有绑定 Server 或凭据 | 提示管理员完成绑定 |
| `AUTH_FAILED` | HTTP 401/403 或鉴权错误 | 检查 Key、套餐和权限 |
| `NETWORK_FAILED` | DNS、TLS、超时或连接失败 | 停止并报告网络错误 |
| `CAPABILITY_MISSING` | 所需工具未出现在 `tools/list` | 停止并报告缺失工具 |
| `RATE_LIMITED` | HTTP 429 或限流错误 | 遵循重试时间，不循环重试 |
| `UNKNOWN_FAILURE` | 无法归类的协议或服务错误 | 保留 request id 后停止 |

API Key 只允许保存在元力平台密钥存储中。不得回显、记录或写入 API Key、密钥或凭据到 Skill 包、日志、缓存、报告和对话。
