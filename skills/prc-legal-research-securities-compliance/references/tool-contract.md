# 证券合规工具契约

运行前先对 `yuandian-securities` 执行能力发现。下表是 1.2.0 的五项公开证券能力；调用参数、枚举和必填项以运行时工具模式为准，即 source of truth。

| MCP 工具 | 用途 | 路由原则 |
|---|---|---|
| `yuandian_law_vector_zq_search` | 证券法规语义检索 | 自然语言问题或跨法规发现 |
| `yuandian_rh_ft_zq_search` | 证券法条关键词检索 | 已知法规、条款主题或精确术语 |
| `yuandian_rh_fg_zq_search` | 证券法规关键词检索 | 法规名称、监管主题或效力筛选 |
| `yuandian_rh_ssgsgg_search` | 上市公司公告检索 | 公司、市场、公告类型和日期筛选 |
| `yuandian_rh_zqcfws_search` | 证券处罚及监管文书检索 | 主体、监管机构、措施类型和日期筛选 |

## 调用纪律

- 当前公开证券 Server 仅以上五项专用能力。不得调用或声称存在通用 `yuandian_rh_ft_detail`、`yuandian_rh_fg_detail`。
- 精确法条需求使用 `yuandian_rh_ft_zq_search` 的返回原文和身份字段；如返回不足以核验完整上下文，明确标记“待法规原文复核”。
- 公司行政处罚不是证券监管处罚；不得用企业库行政处罚替代 `yuandian_rh_zqcfws_search`。
- 公告内容、监管文书和法规条文必须分组呈现，并标注来源类型和日期。
- MCP 使用 Stateless Streamable HTTP `POST`；`GET` 返回 `405` 属于预期协议行为。

## 响应与错误

兼容 JSON 和 SSE 帧中的 JSON-RPC 结果。开放平台 API 的成功码可能是 200 或 201，数据可能位于 `data` 或 `extra`；若元力适配层回退到 API，不得只接受单一成功码或单一数据字段。401/403、429、超时和缺失工具按接入门禁映射为稳定状态。
