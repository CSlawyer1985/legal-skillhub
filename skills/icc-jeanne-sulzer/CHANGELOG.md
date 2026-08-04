# 变更日志——ICC 技能

`icc/` 技能的所有重要变更均记录于此。版本遵循顶层 `README.md` 中指示的套件级版本控制。

## v1.1.2 — 2026-06-02

专家验证后的实质性更正。

- **更正了全技能中的第 28 条编号。** 《罗马规约》第 28 条使用字母子款——`28(a)`（军事指挥官）和 `28(b)`（其他上级），各含罗马数字子要素——且没有编号款项。早期版本错误地将 `Article 28(1)/(2)` 呈现为规约的编号，将 `28(a)/(b)` 呈现为实务简写；这是颠倒的。已更新 `references/citation-format.md`、`SKILL.md`、`references/verification-workflow.md` 和两个示例，改用 `28(a)`（*Bemba* 军事制度）和 `28(b)`（文职/其他上级制度）。顶层 `CLAUDE.md` 约束已同步更正。

## v1.1.1 — 2026-05-30

编辑一致性清理（套件级审阅）；无实质性变更。

- 更正了 v1.0 和 v1.1 说明中的内容文件计数（六个文件，而非七个）。
- 将 `verification-workflow.md` 和示例中的对勾和叉号标记替换为纯文本标记，以匹配套件的无符号风格。

## v1.1 — 2026-05-27

重组为标准技能布局。

- 将六个既有 ICC 内容文件从仓库根目录移至 `icc/references/` 和 `icc/examples/`。
- 新增 `icc/SKILL.md` 作为技能入口点，汇集核心纪律、使用时机指引、工作流摘要、对参考和示例材料的指引，以及五项硬性规则。
- 新增本变更日志。

本修订中参考或示例文件的内容无实质性变更。

## v1.0 — 初始

ICC 技能的初始内容，以六个 Markdown 文件撰写：

- `authoritative-sources.md` — 来源层级和 icc-cpi.int 回退阶梯。
- `citation-format.md` — 基础文书和 ICC 文件的引注格式；第 28 条简写讨论。
- `verification-workflow.md` — 操作流程和三级验证梯度。
- `foundational-texts.md` — 四项 ICC 基础文本以及什么不是基础文本。
- `example-verification.md` — 完整验证示例（Bemba、Ntaganda）。
- `example-audit.md` — 工作草稿审计和法院记录审计模式。
