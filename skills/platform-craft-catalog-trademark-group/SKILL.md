---
name: "platform-craft-catalog-trademark-group"
description: "调用海外运营平台接口 GET /craft/craft-trademark-group/selectGroupList，用于查询商标组。这是一个最小颗粒度 API skill；当用户需要执行该单一接口动作，或上层 agent 需要编排商城浏览、搜索、下单链路中的这一步时触发。"
version: "1.0.3"
tags:
  - "海外运营平台"
  - "商城Agent"
  - "原子Skill"
  - "API接口"
  - "platform-craft-catalog"
metadata:
  slug: "platform-craft-catalog-trademark-group"
  display_name: "kutesmart-海外运营平台工艺目录-查询商标组"
  environment: "production"
  service: "craft"
  api_method: "GET"
  endpoint: "/craft/craft-trademark-group/selectGroupList"
  base_url: "https://www.kutetailor.com/api/craft"
  auth_type: "bearer"
  permission_level: "read"
  category: "商城Agent原子接口"
  publisher: "platform"
  visibility: "public_all"
---

# kutesmart-海外运营平台工艺目录-查询商标组

正式环境固定调用地址：`GET https://www.kutetailor.com/api/craft/craft/craft-trademark-group/selectGroupList`

这个 skill 是最小颗粒度接口 skill，只负责一个平台接口动作：`trademark_group`。需要组合成完整业务链路时，由上层 agent 按聚合 skill 或计划文档编排多个原子 skill。

## 触发场景

当用户需要查询商标组时使用。若用户需求需要多个接口步骤，本 skill 只完成本接口调用，并把关键返回字段交给后续 skill。

## 调用参数要求

tool arguments 统一使用嵌套 `params` 对象：

```json
{
  "params": {
    "accessToken": "Bearer token or raw token",
    "query": {},
    "path": {},
    "body": {},
    "headers": {}
  }
}
```

重要约束：

- 最外层只放 `params`，不要使用 `params.xxx` 这类点号顶层 key。
- 正式环境地址固定在 frontmatter 的 `base_url`，调用时不要从用户输入覆盖。
- 登录态接口使用 `params.accessToken` 生成 `Authorization: Bearer <token>`；如果传入值已含 `Bearer `，不要重复拼接。
- Path 参数写入 `params.path`，Query 参数写入 `params.query`，JSON Body 写入 `params.body`，额外 Header 写入 `params.headers`。
- POST/PUT 默认发送 JSON body；如果上层接口网关另有约定，以网关契约为准。
- 这是查询或计算类接口；仍需遵守当前登录态、租户和用户权限。

## 接口

| action | 请求 | URL | 参数 | 返回 | 用途 |
|---|---|---|---|---|---|
| `trademark_group` | `GET` | `/craft/craft-trademark-group/selectGroupList` | Query：`categoryId`、`memberId` | `RS<List<AppCraftTrademarkGroupVO>>` | 查询商标组。 |

## 执行要点

- 执行器必须使用 frontmatter 中的固定正式环境地址，不接受用户输入覆盖 `base_url`。
- 按上表选择 HTTP method 和 URL；URL 中 `{变量}` 从 `params.path` 替换。
- GET/DELETE 查询参数放在 URL query；POST/PUT 请求体按参数列要求提交。
- 返回结果必须以接口响应为事实来源，不要补造库存、价格、订单号、优惠金额或物流状态。
- 如果接口返回认证、权限、参数或业务错误，把原始错误码和错误信息传给上层 agent。

## 来源

| 字段 | 值 |
|---|---|
| 聚合 skill | `platform-craft-catalog` |
| 聚合 skill 文档 | `doc/skill/platform-craft-catalog/SKILL.md` |
| 原始 action | `trademark_group` |
