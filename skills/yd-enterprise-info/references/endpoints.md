# 接口字段速查表

> 来源：元典开放平台 https://open.chineselaw.com/docs
> 版本：v26.4.29.1545
> 鉴权：所有接口均通过 HTTP header `X-API-Key: <key>` 鉴权
> 通用响应：`{ status: "success", code: 200, message: "...", data: {...} }`

---

## 1. search-company — 企业检索

**Endpoint**：`GET /open/rh_enterpriseSearch`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `name` | string | ✅ | 企业名称关键词 |
| `top_k` | int | 否 | 返回条数（1-50，默认10） |

**响应 data**：数组，每项包含 `id`、`企业名称`、`统一社会信用代码`

---

## 2. base-info — 企业基本信息

**Endpoint**：`GET /open/rh_enterpriseBaseInfo`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | ○ | 企业 ID（与 tyshxydm 二选一） |
| `tyshxydm` | string | ○ | 统一社会信用代码 |

**响应 data 主要字段**：
`id`、`企业名称`、`法定代表人`、`注册资本`、`工商注册号`、`组织机构码`、
`统一社会信用代码`、`企业类型`、`行业`、`成立日期`、`营业期限`、`核准日期`、
`登记机关`、`注册地址`、`经营状态`、`经营范围`、
`股东信息[]`（股东名称/类型/出资比例/认缴出资额/实缴出资额/参股日期）、
`核心成员[]`（姓名/职务）、
`分支机构[]`（分支机构名称/经营状态/负责人/成立日期）

---

## 3. change — 变更记录

**Endpoint**：`GET /open/rh_enterpriseChangeInfo`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` / `tyshxydm` | string | ○ | 企业标识 |
| `pageNo` | int | 否 | 页码（默认1，每页30条） |

**响应 data**：`total`、`pageNo`、`pageSize`、`hasMore`、`list[]`（变更时间/变更项目/变更前内容/变更后内容）

---

## 4. brand — 商标信息

**Endpoint**：`GET /open/rh_enterpriseBrand`

**分页参数**：同上

**list[] 字段**：`商标名称`、`商标logo`、`注册号`、`类别`、`流程状态`、`专用权期限开始日期`、`专用权期限结束日期`

---

## 5. soft-right — 软件著作权

**Endpoint**：`GET /open/rh_enterpriseSoftRight`

**分页参数**：同上

**list[] 字段**：软件著作权相关字段（软件名称、登记号、版本号、登记日期等）

---

## 6. patent — 专利信息

**Endpoint**：`GET /open/rh_enterprisePatent`

**分页参数**：同上

**list[] 字段**：专利名称、专利号、类型、申请日期、公开日期、状态等

---

## 7. copyright-work — 作品著作权

**Endpoint**：`GET /open/rh_enterpriseWorksRight`

**分页参数**：同上

**list[] 字段**：作品名称、登记号、作品类别、登记日期等

---

## 8. website — 网站备案

**Endpoint**：`GET /open/rh_enterpriseIcp`

**分页参数**：同上

**list[] 字段**：网站名称、网站备案/许可证号、网站域名、审核时间、服务类型等

---

## 9. outbound-invest — 对外投资

**Endpoint**：`GET /open/rh_enterpriseOutInvest`

**分页参数**：同上

**list[] 字段**：被投资企业名称、统一社会信用代码、出资比例、出资金额、经营状态等

---

## 10. outbound-guarantee — 对外担保

**Endpoint**：`GET /open/rh_enterpriseGuaranty`

**分页参数**：同上

**list[] 字段**：担保详情相关字段

---

## 11. equity-pledge — 股权出质

**Endpoint**：`GET /open/rh_enterprisePledge`

**分页参数**：同上

**list[] 字段**：出质人、质权人、出质股权数额、登记日期、登记编号、状态等

---

## 12. equity-frozen — 股权冻结

**Endpoint**：`GET /open/rh_enterpriseFrozenEquity`

**分页参数**：同上

**list[] 字段**：被执行人、冻结股权数额、执行法院、执行文号、冻结日期、到期日期等

---

## 13. abnormal — 经营异常

**Endpoint**：`GET /open/rh_enterpriseAbnormalOperation`

**分页参数**：同上

**list[] 字段**：列入日期、列入原因、列入机关、移出日期、移出原因等

---

## 14. serious-violation — 严重违法

**Endpoint**：`GET /open/rh_enterpriseSeriousIllegal`

**分页参数**：同上

**list[] 字段**：列入日期、列入原因、列入机关、移出日期等

---

## 15. tax-arrears — 欠税公告

**Endpoint**：`GET /open/rh_enterpriseCorporateTax`

**分页参数**：同上

**list[] 字段**：欠税税种、欠税余额、欠税所属期、公告日期等

---

## 16. admin-penalty — 行政处罚

**Endpoint**：`GET /open/rh_enterprisePunishment`

**分页参数**：同上

**list[] 字段**：决定书文号、违法行为类型、处罚内容、决定机关、决定日期等

---

## 17. executed — 被执行人

**Endpoint**：`GET /open/rh_enterpriseExecutedPerson`

**分页参数**：同上

**list[] 字段**：案号、立案日期、执行法院、执行标的金额、案件状态等

---

## 18. dishonest — 失信被执行人

**Endpoint**：`GET /open/rh_enterpriseExecutions`

**分页参数**：同上

**list[] 字段**：案号、立案日期、失信行为、执行法院、做出决定时间等

---

## 19. litigation-doc — 涉诉文书

**Endpoint**：`GET /open/rh_enterpriseWritList`

**分页参数**：同上

**list[] 字段**：案号、案件名称、文书类型、审判程序、审理法院、裁判日期、诉讼身份等

---

## 20. litigation-stat — 涉诉统计

**Endpoint**：`GET /open/rh_enterpriseWritAgg`

| 参数 | 类型 | 必填 |
|---|---|---|
| `id` / `tyshxydm` | string | ○ |

**响应 data**：`total`、`案件类别[]`、`一级案由[]`、`二级案由[]`、`文书种类[]`、
`审判程序[]`、`法院层级[]`、`结案方式[]`、`结案年份[]`、`地域[]`、`诉讼身份[]`、`对方当事人身份[]`
（每项均为 `{key, count}` 结构）

---

## 21. court-announcement — 法院公告

**Endpoint**：`GET /open/rh_enterpriseCourtNotice`

**分页参数**：同上

**list[] 字段**：公告类型、公告内容、公告日期、发布法院等

---

## 22. court-hearing — 开庭公告

**Endpoint**：`GET /open/rh_enterpriseCourtSessionNotice`

**分页参数**：同上

**list[] 字段**：案号、案件名称、审判长/员、开庭时间、开庭地点、当事人等

---

## 通用分页响应结构

```json
{
  "code": 200,
  "status": "success",
  "data": {
    "id": "...",
    "name": "企业名称",
    "total": 100,
    "pageNo": 1,
    "pageSize": 30,
    "hasMore": true,
    "list": [ ... ]
  }
}
```

合并后（yd_enterprise_info.py 自动翻页）输出：

```json
{
  "id": "...",
  "name": "企业名称",
  "total": 100,
  "list": [ /* 全部 100 条 */ ],
  "_meta": {
    "fetched_pages": 4,
    "fetched_items": 100,
    "total": 100,
    "max_pages_limit": 20,
    "fetched_at": "2026-04-29T16:00:00"
  }
}
```
