# 验收用例

| 编号 | 场景 | 预期结果 |
|---|---|---|
| COMPANY-01 | 输入企业简称且命中多个主体 | 展示候选并等待确认，不擅自选择 |
| COMPANY-02 | 输入统一社会信用代码 | 使用 `tyshxydm` 定位后查询目标分项 |
| COMPANY-03 | 查询 2025 年年报 | 调用年报能力并传 `year=2025` |
| COMPANY-04 | 查询涉诉明细第二页 | 使用 `pageNo`，标注分页范围 |
| COMPANY-05 | 区分失信与被执行 | `rh_enterpriseExecutions` 对应失信，`rh_enterpriseExecutedPerson` 对应被执行 |
| COMPANY-06 | 能力发现少于 26 项 | 返回 `CAPABILITY_MISSING` 并列出缺失 route key |
| COMPANY-07 | API 成功码 201 且数据在 `extra` | 正常解析，不误报失败 |
| COMPANY-08 | MCP 返回 401 | 状态为 `AUTH_FAILED`，不回显凭据、不调用外部企业网站替代 |
