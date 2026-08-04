# 企业信息接口速查（legal-due-diligence 视角）

> 完整接口文档及 CLI 用法见：[yd-enterprise-info skill](https://github.com/malnlda/yd-enterprise-info)
> 本文件仅作为 draft 阶段快速参考，供 LLM 知晓 raw/ 下各 JSON 文件的内容。

---

## 各子命令与 JSON 文件对应关系

| JSON 文件前缀 | 子命令 | 含义 | DD 章节 |
|---|---|---|---|
| `search-company_*` | search-company | 企业检索候选列表 | init |
| `base-info_*` | base-info | 基本信息+股东+核心成员+分支机构 | 1, 2, 3 |
| `change_*` | change | 变更记录（含历次法人/注册资本/经营范围变更） | 1 |
| `brand_*` | brand | 商标列表（名称/注册号/类别/有效期） | 4 |
| `patent_*` | patent | 专利列表 | 4 |
| `soft-right_*` | soft-right | 软件著作权列表 | 4 |
| `copyright-work_*` | copyright-work | 作品著作权列表 | 4 |
| `website_*` | website | 网站备案列表 | 4 |
| `tax-arrears_*` | tax-arrears | 欠税公告 | 6 |
| `outbound-guarantee_*` | outbound-guarantee | 对外担保 | 8 |
| `equity-pledge_*` | equity-pledge | 股权出质 | 2, 8 |
| `equity-frozen_*` | equity-frozen | 股权冻结 | 2, 9 |
| `outbound-invest_*` | outbound-invest | 对外投资 | 10 |
| `abnormal_*` | abnormal | 经营异常记录 | 1 |
| `serious-violation_*` | serious-violation | 严重违法记录 | 1, 9 |
| `admin-penalty_*` | admin-penalty | 行政处罚 | 9 |
| `executed_*` | executed | 被执行人 | 9 |
| `dishonest_*` | dishonest | 失信被执行人 | 9 |
| `litigation-stat_*` | litigation-stat | 涉诉统计（总量/案件类别/案由分布） | 9 |
| `litigation-doc_*` | litigation-doc | 涉诉文书列表 | 9 |
| `court-announcement_*` | court-announcement | 法院公告 | 9 |
| `court-hearing_*` | court-hearing | 开庭公告（反映未决诉讼）| 9 |

---

## 分页接口文件结构

所有分页接口文件均包含 `_meta` 字段，用于核验数据完整性：

```json
{
  "list": [ ... ],
  "_meta": {
    "fetched_pages": N,
    "fetched_items": M,
    "total": M,
    "fetched_at": "YYYY-MM-DDTHH:MM:SS"
  }
}
```

**核验要点**：`fetched_items == total` 表示数据完整；否则说明受 `--max-pages` 限制，数据不完整，应在底稿备注。
