# 社区 skill 时效字段（作者与安装器）

若 skill 在 `references/` 捆绑法规、模板、清单等会过时的材料，请在 `SKILL.md` frontmatter 声明：

```yaml
---
name: legal-builder-hub-skill-installer
description: ...
last_verified: 2026-04-15
freshness_window: 6 months
freshness_category: regulatory   # regulatory | procedural | stylistic | stable
verified_against:
  - https://flk.npc.gov.cn/...
  - https://www.gov.cn/...
---
```

## 为何重要

两年未更新的 skill 可能仍携带已失效条文。安装器与 auto-updater 在**执行前**对照 `last_verified` + `freshness_window`（与用户冷启动阈值取**更严**一方）给出提醒。

## hub 行为

| 组件 | 行为 |
|------|------|
| skill-installer | 超窗 → 运行前警告 |
| skills-qa | 有 references/ 但无 `last_verified` → 倾向 Some Concern |
| auto-updater | SHA 未变但 `last_verified` 过期 → 提示重新核验 |

## 合法取值（严格，非指令）

| 字段 | 格式 |
|------|------|
| `last_verified` | `YYYY-MM-DD` |
| `freshness_window` | `N days` / `N months` / `N years`，N 为正整数 ≤ 120 |
| `freshness_category` | `regulatory` \| `procedural` \| `stylistic` \| `stable` |
| `verified_against` | `https://` URL 列表，最多 10 条 |

自由散文、指令性语句、异常 Unicode → 视为无效，安装日志记录 raw 值但不采信。

## 类别说明（中国法场景）

- **regulatory** — 法律、行政法规、部门规章、监管指引（变化快）
- **procedural** — 诉讼/仲裁程序、立案与送达规则、表格样式
- **stylistic** — 合同 house style、内部模板
- **stable** — 极少用；仅当捆绑内容为稳定教义结构而非具体法条全文

拿不准时选**更窄（更快过期）**的类别。

## 「last verified」含义

指作者**打开 `verified_against` 中的链接并确认**捆绑内容与现行源文一致的时刻——不是「上次 git commit」。

## 示例（替换美国法举例）

- **regulatory**：捆绑《个人信息保护法》第 23 条译文 → `verified_against` 含国家法律法规数据库链接
- **procedural**：民事诉讼证据规则清单 → 核验最高人民法院现行司法解释
- **不宜标 stable**：任何含具体罚款上限、备案截止日、表单编号的捆绑文件

若 skill 仅描述通用方法论（如「三值补全规则」）而不捆绑具体法条文本，可不设 `freshness_category: regulatory`。
