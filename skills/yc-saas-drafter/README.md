# YC SaaS 起草技能

一个以 Y Combinator 标准格式 SaaS 模板为起点起草定制**客户协议**的 Claude 技能。运行结构化信息收集，应用 18 项始终开启的默认处理，将原始 YC 模板转变为专业的起点，根据交易处理 12 项条件决策，并输出一份干净的 `.docx` 外加面向律师的备忘录，解释每项变更。

为初创企业创始人及其法律顾问构建，他们想要 YC 模板作为基线，但不想要起草注释、可选脚手架和粗糙边缘。

## 它做什么

- 全程将"SaaS Services Agreement"重命名为"Customer Agreement"
- 添加适当的数据隐私章节（§2.5）
- 将保证重构为排他性救济 / 客户保证 / beta 免责声明
- 将 SLA 和支持合并为单一附件 B
- 剥离所有 `[OPTIONAL]`、`*[Note: ...]*` 和起草注释
- 替换交易变量（公司、客户、费用、管辖法律等）
- 标记律师审查事项（DPA 需求、机器学习训练权、服务中的知识产权归属等）

产出：
1. `[Company]_[Customer]_Customer_Agreement_DRAFT.docx`
2. `[Company]_[Customer]_Customer_Agreement_Memo.md` —— 记录每项变更

## 如何使用

这是一个 Claude Agent 技能。使用方式：

1. 将此文件夹放入您的 Claude 技能目录（例如 Claude Code / Cowork 的 `~/.claude/skills/`，或您使用的任何 Claude 产品的技能文件夹）。
2. 用触发短语开始对话，例如：
   - "Draft a YC SaaS agreement"
   - "I need a Customer Agreement starting from the YC form"
   - "New SaaS deal with [customer]"
3. 回答信息收集问题。Claude 将确认您的选择、产出草稿并交付备忘录。

## 本仓库包含什么

```
yc-saas-drafting-skill/
├── SKILL.md                              # Entry point — workflow and rules
├── assets/
│   └── YC_Form_SaaS_Agreement.docx       # YC's published standard form
└── references/
    ├── intake-questions.md               # 15 question groups with branching
    ├── decision-matrix.md                # Maps answers to template actions
    └── supplementary-language.md         # Verbatim clause text by anchor ID
```

决策矩阵告诉 Claude 要**改变什么**。补充语言提供要插入的**确切文本**。技能不即兴创作合同语言。

## 归属

`assets/YC_Form_SaaS_Agreement.docx` 是 Y Combinator 的标准格式 SaaS 协议，由 YC 发布供初创企业使用。Y Combinator 与本技能无关联。

## 不能替代律师

本技能产出起草起点。每个输出都包含一份带标记事项的备忘录，这些事项需要律师审查——DPA 需求、机器学习训练权、实施服务中的知识产权归属、衍生数据所有权和数据保留。未经律师就这些要点审查，不要发送草稿。

## 许可证

[MIT](./LICENSE) —— Copyright (c) 2026 Victor @ stokebuilder
