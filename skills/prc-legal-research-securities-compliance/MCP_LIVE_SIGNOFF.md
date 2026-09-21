# 元典证券 MCP 生产验收

## 目标

- Server：`yuandian-securities`
- URL：`https://open.chineselaw.com/mcp/securities/stream`
- 协议：Stateless Streamable HTTP `POST`
- 认证：元力平台密钥存储注入 Bearer Token

## 验收步骤

1. 在实际 Agent Host 上确认平台已绑定 `yuandian-securities`，不得把真实 API Key 放入聊天、命令历史或普通配置文件。
2. 执行 `tools/list`，确认以下五项工具全部出现：
   - `yuandian_law_vector_zq_search`
   - `yuandian_rh_ft_zq_search`
   - `yuandian_rh_fg_zq_search`
   - `yuandian_rh_ssgsgg_search`
   - `yuandian_rh_zqcfws_search`
3. 读取每项运行时 schema，核对必填项、类型和枚举。
4. 分别执行一项最小法规检索、公告检索和监管文书检索。
5. 验证 401/403 映射为 `AUTH_FAILED`，429 映射为 `RATE_LIMITED`，缺少工具映射为 `CAPABILITY_MISSING`。
6. 确认日志、报告和错误响应均未包含 Token。

可选离线探针：

```bash
python scripts/yuandian_mcp_probe.py \
  --server securities \
  --require-tool yuandian_rh_fg_zq_search \
  --require-tool yuandian_rh_zqcfws_search \
  --require-tool yuandian_rh_ssgsgg_search
```

探针 `READY` 只证明连接、鉴权和能力目录可用；法律检索质量仍应通过 `tests/acceptance-cases.md` 的业务场景验收。
