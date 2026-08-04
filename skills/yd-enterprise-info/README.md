# yd-enterprise-info

**元典开放平台企业信息查询工具** — v26.4.29.1545

封装[元典开放平台](https://open.chineselaw.com)全部 22 个企业信息接口，支持自动翻页，彻底消除列表数量限制（旧接口最多返回 10 条，新分页接口可拉取全量）。

作为 [legal-due-diligence](https://github.com/malnlda/legal-due-diligence) 的数据获取层独立运行，也可单独用于企业背景核查。

---

## 覆盖接口（22 个）

| 子命令 | 用途 |
|---|---|
| `search-company` | 按名称检索候选企业 |
| `base-info` | 基本信息+股东+核心成员+分支机构 |
| `change` | 变更记录（分页） |
| `brand` | 商标信息（分页） |
| `soft-right` | 软件著作权（分页） |
| `patent` | 专利信息（分页） |
| `copyright-work` | 作品著作权（分页） |
| `website` | 网站备案（分页） |
| `outbound-invest` | 对外投资（分页） |
| `outbound-guarantee` | 对外担保（分页） |
| `equity-pledge` | 股权出质（分页） |
| `equity-frozen` | 股权冻结（分页） |
| `abnormal` | 经营异常（分页） |
| `serious-violation` | 严重违法（分页） |
| `tax-arrears` | 欠税公告（分页） |
| `admin-penalty` | 行政处罚（分页） |
| `executed` | 被执行人信息（分页） |
| `dishonest` | 失信被执行人（分页） |
| `litigation-doc` | 涉诉文书列表（分页） |
| `litigation-stat` | 涉诉多维度统计 |
| `court-announcement` | 法院公告（分页） |
| `court-hearing` | 开庭公告（分页） |

---

## 快速开始

```bash
# 1. 设置 API Key
export CHINESELAW_API_KEY=你的KEY

# 2. 检索目标公司，确认 USCC
python3 scripts/yd_enterprise_info.py search-company --name "目标公司名称"

# 3. 拉取基本信息
python3 scripts/yd_enterprise_info.py base-info \
  --tyshxydm <USCC> --output ./raw/ --yes

# 4. 批量拉取知识产权数据
for cmd in brand patent soft-right copyright-work; do
  python3 scripts/yd_enterprise_info.py $cmd \
    --tyshxydm <USCC> --output ./raw/ --yes
done
```

---

## 关键特性

- **自动翻页**：分页接口默认自动翻取所有页，合并为单个 JSON 文件，`_meta` 字段记录 total/fetched_pages
- **零依赖**：仅使用 Python 标准库（`urllib`、`json`、`argparse`、`pathlib`）
- **积分保护**：`--max-pages 20`（默认）防止过度消耗；`--yes` 跳过逐次确认
- **统一鉴权**：HTTP header `X-API-Key`，Key 不落盘

---

## 安装（作为 Claude Code skill）

```bash
cp -r yd-enterprise-info ~/.claude/skills/
```

---

## 与 legal-due-diligence 的配合

```
legal-due-diligence draft 模式
  └─ 检查 raw/chineselaw/ → 有 JSON → 直接整合
                          → 无 JSON → 提示运行 yd-enterprise-info
```

各章节推荐调用的子命令见 [references/chapter-mapping.md](references/chapter-mapping.md)。

---

## 许可

MIT
