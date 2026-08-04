# 外部数据源使用指南

> **v26.4.29.1545 更新**：企业信息查询已迁移至独立 skill `yd-enterprise-info`，
> 本文件说明如何在 draft 阶段配合使用。

---

## 架构概述

```
legal-due-diligence (本 skill)
    │
    └─ 数据获取层：yd-enterprise-info skill
         ├─ 22 个元典企业信息接口（含自动翻页）
         └─ 数据落盘到 <项目>/raw/chineselaw/
```

`yd-enterprise-info` 负责拉取数据，`legal-due-diligence` 负责读取数据并撰写底稿。
两者职责分离，互不混淆。

---

## 使用流程

### 步骤 1：获取凭证

```bash
export CHINESELAW_API_KEY=你的KEY
```

### 步骤 2：检索目标公司（仅知名称时）

```bash
python3 ~/.claude/skills/yd-enterprise-info/scripts/yd_enterprise_info.py \
  search-company --name "目标公司名称"
```

输出候选列表，律师确认 USCC 后进入步骤 3。

### 步骤 3：按章节需要拉取数据

根据当前要写的底稿章节，参照下表选择子命令：

| DD 章节 | 必调子命令 | 建议子命令 |
|---|---|---|
| 第 1 章（主体资格）| `base-info`、`change` | `abnormal`、`serious-violation` |
| 第 2 章（股权结构）| `base-info`、`equity-pledge`、`equity-frozen` | — |
| 第 3 章（公司治理）| `base-info` | — |
| 第 4 章（核心资产）| `brand`、`patent`、`soft-right` | `copyright-work`、`website` |
| 第 6 章（财税）| — | `tax-arrears` |
| 第 8 章（债权债务）| `outbound-guarantee`、`equity-pledge` | — |
| 第 9 章（诉讼）| `litigation-stat`、`litigation-doc`、`executed`、`dishonest`、`admin-penalty` | `court-announcement`、`court-hearing`、`equity-frozen`、`serious-violation` |
| 第 10 章（其他）| `outbound-invest` | — |

> 完整映射见：[references/chineselaw/enterprise-endpoints-summary.md](chineselaw/enterprise-endpoints-summary.md)

拉取示例（第 4 章知识产权）：

```bash
USCC="目标公司USCC"
OUTDIR="/path/to/project/raw/chineselaw/"
for cmd in brand patent soft-right copyright-work; do
  python3 ~/.claude/skills/yd-enterprise-info/scripts/yd_enterprise_info.py \
    $cmd --tyshxydm $USCC --output $OUTDIR --yes
done
```

### 步骤 4：在 draft 模式中使用数据

draft 模式会自动检查 `<项目>/raw/chineselaw/` 目录：

- **有 JSON 文件** → 直接读取，整合到底稿
- **无 JSON 文件** → 提示"建议先运行 yd-enterprise-info XXX 命令获取工商数据"

---

## 引用规范（写入底稿时必须遵守）

1. **不入材料清单**：API 数据**不得**列入 §X.2 已获取材料清单
2. **明确来源**：在 §X.4 调查发现段首注明：
   > 经查阅元典开放平台「XXX接口」（调用时间 YYYY-MM-DD HH:MM，原始数据见 `raw/chineselaw/<文件名>`）
3. **核验完整性**：检查 `_meta.fetched_items == _meta.total`；不一致时在 §X.6 律师备忘注明"数据因翻页限制可能不完整，建议重跑 --max-pages 0"
4. **冲突即风险**：API 数据与目标公司提供材料不一致，§X.5 风险提示标注 🟡 中或 🔴 高风险
5. **失败留痕**：API 调用失败时在 §X.6 律师备忘中记录时间与原因

---

## 旧版本（v26.4.25.2039）兼容说明

旧版本文件格式（`company_detail_*.json`、`company_info_*.json`）与新版本不兼容。建议重新使用 `yd-enterprise-info` 拉取全量数据。

---

## yd-enterprise-info 详细文档

- GitHub：https://github.com/malnlda/yd-enterprise-info
- 本地安装：`~/.claude/skills/yd-enterprise-info/`
- 接口速查：`~/.claude/skills/yd-enterprise-info/references/endpoints.md`
