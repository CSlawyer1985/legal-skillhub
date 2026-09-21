# 企业信息工具契约

运行前先对 `yuandian-company` 执行能力发现。元力平台应以运行时工具模式为准，即 source of truth。MCP 工具通常带 `yuandian_` 前缀；下表同时列出当前 26 个开放平台 route key，便于平台适配器和审计统一核对。

| route key | 用途 | 关键约束 |
|---|---|---|
| `rh_company_info` | 按名称或股票简称获取候选详情 | 候选消歧后再查风险 |
| `rh_company_detail` | 按企业 ID 或统一社会信用代码获取聚合详情 | 统一社会信用代码字段为 `tyshxydm` |
| `rh_enterpriseSearch` | 企业候选检索 | 企业名称不唯一时必须让用户确认 |
| `rh_enterpriseBaseInfo` | 企业基本信息 | 展示主体名称和统一社会信用代码 |
| `rh_enterpriseAggregationSummary` | 聚合统计和 Top 20 摘要 | 当前开放平台为 GET；若 MCP schema 不同，以运行时工具模式为准 |
| `rh_enterpriseAnnualReport` | 指定年份企业年报详情 | 必须传 `year` |
| `rh_enterpriseOutInvest` | 对外投资 | 列表结果说明分页范围 |
| `rh_enterpriseBrand` | 商标 | 列表结果说明分页范围 |
| `rh_enterprisePatent` | 专利 | 列表结果说明分页范围 |
| `rh_enterpriseSoftRight` | 软件著作权 | 列表结果说明分页范围 |
| `rh_enterpriseWorksRight` | 作品著作权 | 列表结果说明分页范围 |
| `rh_enterpriseIcp` | 网站备案 | 列表结果说明分页范围 |
| `rh_enterpriseChangeInfo` | 工商变更 | 保留变更日期、变更前和变更后 |
| `rh_enterpriseWritAgg` | 涉诉统计 | 统计不是文书明细 |
| `rh_enterpriseWritList` | 涉诉文书列表 | 分页字段使用 `pageNo` |
| `rh_enterpriseCourtSessionNotice` | 开庭公告 | 保留法院和开庭日期 |
| `rh_enterpriseCourtNotice` | 法院公告 | 不与开庭公告混淆 |
| `rh_enterpriseExecutions` | 失信被执行人 | 不得写成普通被执行人 |
| `rh_enterpriseExecutedPerson` | 被执行人 | 不得写成失信被执行人 |
| `rh_enterpriseFrozenEquity` | 股权冻结 | 保留状态和期限 |
| `rh_enterprisePunishment` | 行政处罚 | 不得自动等同证券监管处罚 |
| `rh_enterprisePledge` | 股权出质 | 保留登记编号和状态 |
| `rh_enterpriseGuaranty` | 对外担保 | 说明数据口径和时间 |
| `rh_enterpriseAbnormalOperation` | 经营异常 | 保留列入和移出信息 |
| `rh_enterpriseCorporateTax` | 欠税公告 | 保留税务机关和期间 |
| `rh_enterpriseSeriousIllegal` | 严重违法 | 保留列入和移出信息 |

## 调用纪律

- MCP 暴露名称可能为 `yuandian_rh_company_info`、`yuandian_rh_company_detail`、`yuandian_rh_enterpriseSearch` 等；只能从能力发现结果选择实际名称，禁止拼接猜测。
- 先消歧企业，再取得 ID 或 `tyshxydm`，最后调用分项接口。
- 汇总、统计和列表是三种不同口径；分页结果不得表述为企业全部记录。
- MCP 使用 Stateless Streamable HTTP `POST`；`GET` 返回 `405` 属于 MCP 端点的预期协议行为，不影响开放平台 route 的 GET 语义。

## 响应与错误

开放平台 API 的成功码可能是 200 或 201，数据可能位于 `data` 或 `extra`。元力适配层必须兼容二者，并把 401/403、429、超时、缺失工具映射为接入门禁中的稳定状态。
