# 元典 MCP 工具使用指南

## 一、法律法规检索

### 语义检索 — `yuandian_law_vector_search`

| 参数 | 说明 |
|------|------|
| `query` | **必填**。自然语言查询 |
| `return_num` | 返回数量，默认 45，建议 10-15 |
| `rewrite_flag` | 是否改写查询，默认 true |
| `fatiao_filter` | 过滤条件：时效性、效力级别等 |

### 法条关键词检索 — `yuandian_rh_ft_search`

| 参数 | 说明 |
|------|------|
| `keyword` | **必填**。法条内容关键词 |
| `search_mode` | AND（默认）或 OR |
| `sxx` | 时效性：现行有效、失效 等 |
| `top_k` | 返回条数，默认 10 |

### 法规检索 — `yuandian_rh_fg_search`

检索法规列表，支持多种过滤。获法规 ID 后可用 `yuandian_rh_fg_detail` 查看全文。

---

## 二、案例检索（穷尽三个来源）

### 步骤 1：普通案例库 — `yuandian_rh_ptal_search`

| 常用参数 | 说明 |
|---------|------|
| `ah` | 案号 |
| `ay` | 案由数组（或关系） |
| `ssqy` | 涉诉企业名称 |
| `qw` | 全文关键词 |
| `ajlb` | 案件类别，民商事用 `"民事案件"` |
| `ja_start/end` | 结案日期范围 |
| `top_k` | 返回条数，默认 10 |

### 步骤 2：权威案例库 — `yuandian_rh_qwal_search`

支持筛选 `source: ["指导性案例", "典型案例", "参考案例", "公报案例"]`

### 步骤 3：语义检索兜底 — `yuandian_case_vector_search`

用自然语言描述案件事实做语义搜索。注意：此接口覆盖普通和权威两个库。

### 案例详情 — `yuandian_rh_case_details`

**必须同时传 `type`（ptal 或 qwal）和 `ah`（案号）。**

---

## 三、企业信息检索（被告为企业时使用）

1. `yuandian_rh_enterpriseSearch`：按企业名称搜索，获取 ID 和统一社会信用代码
2. `yuandian_rh_enterpriseBaseInfo`：企业基本信息（法定代表人、注册资本等）
3. `yuandian_rh_enterpriseWritAgg`：企业涉诉统计
4. `yuandian_rh_enterpriseExecutedPerson`：失信被执行人查询

---

## 四、使用原则

- 法条引用前确认"现行有效"
- 类案优先参考指导性案例和典型案例
- 被告为企业时用企业工具核实信息
