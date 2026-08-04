---
name: yd-enterprise-info
description: |
  元典企业信息查询技能（开放平台版 https://open.chineselaw.com）。
  封装元典开放平台全部22个企业信息接口，支持自动翻页，彻底消除列表数量限制。
  覆盖：企业基本信息、变更记录、商标、专利、软著、作品著作权、网站备案、
  对外投资/担保、股权出质/冻结、经营异常、严重违法、欠税、行政处罚、
  被执行/失信、涉诉文书/统计、法院公告、开庭公告。
  适合：legal-due-diligence 尽调 10 章的工商数据获取、公司尽职调查背景核查。
  不负责底稿/报告撰写；数据获取后应配合 legal-due-diligence skill 完成书面分析。
metadata:
  author: Chengzhe Mo
  version: "26.4.29.1545"
compatibility: Designed for Claude Code. Requires Python 3.10+ for scripts.
---

# yd-enterprise-info（元典企业信息查询）v26.4.29.1545

> **定位**：独立的工商数据获取层 skill。
> 被 `legal-due-diligence` 调用，也可单独使用于公司背景核查。
> 不替代律师对原始工商档案的核验；所有数据仅作辅助参考。

---

## 触发词

`查工商`、`企业信息`、`查公司`、`enterprise info`、`工商查询`、`查股东`、
`查商标`、`查专利`、`查诉讼`、`查被执行`、`查失信`、`查行政处罚`、
`查对外投资`、`企业背景核查`、`yd-enterprise-info`

---

## 子命令速查

| 子命令 | 说明 | 是否分页 | DD 章节 |
|---|---|---|---|
| `search-company` | 按名称检索候选企业 | 否 | init |
| `base-info` | 基本信息+股东+核心成员+分支机构 | 否 | 1, 2, 3 |
| `change` | 变更记录 | ✅ 自动翻页 | 1 |
| `brand` | 商标信息 | ✅ 自动翻页 | 4 |
| `soft-right` | 软件著作权 | ✅ 自动翻页 | 4 |
| `patent` | 专利信息 | ✅ 自动翻页 | 4 |
| `copyright-work` | 作品著作权 | ✅ 自动翻页 | 4 |
| `website` | 网站备案 | ✅ 自动翻页 | 4 |
| `outbound-invest` | 对外投资 | ✅ 自动翻页 | 10 |
| `outbound-guarantee` | 对外担保 | ✅ 自动翻页 | 8 |
| `equity-pledge` | 股权出质 | ✅ 自动翻页 | 2, 8 |
| `equity-frozen` | 股权冻结 | ✅ 自动翻页 | 2, 9 |
| `abnormal` | 经营异常记录 | ✅ 自动翻页 | 1 |
| `serious-violation` | 严重违法记录 | ✅ 自动翻页 | 9 |
| `tax-arrears` | 欠税公告 | ✅ 自动翻页 | 6 |
| `admin-penalty` | 行政处罚 | ✅ 自动翻页 | 9 |
| `executed` | 被执行人信息 | ✅ 自动翻页 | 9 |
| `dishonest` | 失信被执行人 | ✅ 自动翻页 | 9 |
| `litigation-doc` | 涉诉文书列表 | ✅ 自动翻页 | 9 |
| `litigation-stat` | 涉诉多维度统计 | 否（聚合） | 9 |
| `court-announcement` | 法院公告 | ✅ 自动翻页 | 9 |
| `court-hearing` | 开庭公告 | ✅ 自动翻页 | 9 |

---

## 凭证设置

```bash
export CHINESELAW_API_KEY=你的KEY
# 或通过 --api-key 参数传入（不会写入任何文件）
```

---

## 使用示例

### 场景 A：已知名称，先检索确认 USCC

```bash
python3 scripts/yd_enterprise_info.py search-company \
  --name "北京华宇元典信息服务有限公司" --top-k 5
```

输出候选列表（含 id、企业名称、统一社会信用代码），律师人工确认后取得 USCC。

### 场景 B：已知 USCC，拉取基本信息

```bash
python3 scripts/yd_enterprise_info.py base-info \
  --tyshxydm 91110108MA0074PN30 \
  --output /path/to/project/raw/chineselaw/ --yes
```

### 场景 C：拉取知识产权数据（第 4 章）

```bash
USCC="91110108MA0074PN30"
OUTDIR="/path/to/project/raw/chineselaw/"
for cmd in brand patent soft-right copyright-work website; do
  python3 scripts/yd_enterprise_info.py $cmd \
    --tyshxydm $USCC --output $OUTDIR --yes
done
```

### 场景 D：拉取诉讼数据（第 9 章）

```bash
USCC="91110108MA0074PN30"
OUTDIR="/path/to/project/raw/chineselaw/"
for cmd in litigation-stat litigation-doc court-announcement court-hearing \
           executed dishonest admin-penalty serious-violation equity-frozen; do
  python3 scripts/yd_enterprise_info.py $cmd \
    --tyshxydm $USCC --output $OUTDIR --yes
done
```

### 场景 E：限制翻页（省积分）

```bash
python3 scripts/yd_enterprise_info.py litigation-doc \
  --tyshxydm 91110108MA0074PN30 \
  --max-pages 5 --output ./raw/ --yes
```

### 场景 F：只看第 2 页

```bash
python3 scripts/yd_enterprise_info.py brand \
  --tyshxydm 91110108MA0074PN30 --page 2
```

---

## 关键参数说明

| 参数 | 说明 | 默认 |
|---|---|---|
| `--tyshxydm USCC` | 统一社会信用代码（与 --id 二选一） | — |
| `--id ID` | 元典内部企业 ID（与 --tyshxydm 二选一） | — |
| `--output DIR` | JSON 落盘目录；省略则直接打印 | — |
| `--max-pages N` | 自动翻页上限，`0` = 不限制 | 20 |
| `--page N` | 只拉第 N 页（与 --max-pages 互斥） | — |
| `--yes / -y` | 跳过积分确认 | 否 |
| `--print-data` | 落盘同时打印完整 JSON | 否 |
| `--api-key KEY` | API Key（高于环境变量） | — |

---

## 落盘文件格式

```
raw/chineselaw/
├── brand_91110108MA0074PN30_202604291600.json
├── patent_91110108MA0074PN30_202604291601.json
└── litigation-stat_91110108MA0074PN30_202604291602.json
```

文件名格式：`<子命令>_<USCC或ID>_<YYYYMMDDHHMM>.json`

分页接口文件根节点包含 `_meta`：

```json
{
  "id": "...",
  "name": "...",
  "total": 1273,
  "list": [ ... ],
  "_meta": {
    "fetched_pages": 26,
    "fetched_items": 1273,
    "total": 1273,
    "max_pages_limit": 20,
    "fetched_at": "2026-04-29T16:00:00"
  }
}
```

---

## 与 legal-due-diligence 的关系

```
legal-due-diligence (draft 模式)
    └─ 检查 raw/chineselaw/ 是否有对应 JSON
         ├─ 有 → 直接读取整合到底稿
         └─ 无 → 提示用户运行 yd-enterprise-info 相应子命令
                 → 用户运行后回来 draft
```

**legal-due-diligence 各章推荐调用的子命令**，详见：
- [references/chapter-mapping.md](references/chapter-mapping.md)

**各接口字段速查**，详见：
- [references/endpoints.md](references/endpoints.md)

---

## 引用规范（在底稿中使用本工具数据时）

1. **不入材料清单**：API 数据**不得**列入底稿 §X.2 已获取材料清单
2. **明确来源**：§X.4 调查发现段首注明：
   > 经查阅元典开放平台「XXX」接口（调用时间 YYYY-MM-DD HH:MM，原始数据见 `raw/chineselaw/<文件名>`）
3. **冲突即风险**：API 数据与目标公司提供材料不一致，§X.5 风险提示标注 🟡 中或 🔴 高风险
4. **失败留痕**：调用失败在 §X.6 律师备忘中记录时间与原因

---

## 积分提示

- 每次 API 调用消耗约 10 积分（元典计费规则）
- 分页接口每页单独计费（第 1、2、3 页各 10 积分）
- 建议按需选择子命令，不必每次都运行全部 22 个
- `--max-pages 20`（默认）意味着单次分页接口最多消耗 200 积分
