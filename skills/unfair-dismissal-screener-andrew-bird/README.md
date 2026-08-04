# unfair-dismissal-screener

对照英格兰与威尔士的不公平解雇框架对解雇（拟议的或已实施的）进行筛查，并显示其在何处存在风险敞口。

大多数解雇在劳动法庭上败诉是由于程序问题，而非实体问题。本技能界定合格服务期问题、检查无需合格期即可成立的自动不公平类别，并构建 Burchell / Polkey / 合理回应区间（band of reasonable responses）分析，然后浮出具体的程序缺陷——作为供律师核实的草稿，而非公平性的认定。适用于雇主在解雇前决定是否推进，以及任何一方在解雇后评估潜在索赔的强度。

## 安装

```bash
git clone https://github.com/b1rdmania/unfair-dismissal-screener ~/.claude/skills/unfair-dismissal-screener
```

或在 [Legalise](https://github.com/b1rdmania/legalise) 工作区中：从技能库添加——审查清单、授予能力、在事务上启用、从对话运行。每次运行都会留下带签名的、可审计的记录。

## 使用

```
/unfair-dismissal-screener
/unfair-dismissal-screener --mode=pre-dismissal
/unfair-dismissal-screener --mode=post-dismissal
```

用开始日期、解雇生效日期、雇主主张的理由以及所遵循的程序对事务运行。它返回结构化筛查结果：资格、理由、实体和程序公平性、指示性风险分数，以及说明性赔偿范围。

## 它做什么

- 界定合格服务期门槛（ERA 第 108 条），并检查无需合格期即可成立的自动不公平事由。
- 识别所主张的潜在公平理由（第 98(2) 条）及其是否真实。
- 为行为案件构建 Burchell 分析——真实信念、合理依据、合理调查——对照合理回应区间。
- 构建 Polkey 问题和 ACAS 准则加价（uplift），并将其带入说明性赔偿范围。
- 产出带可见推理的指示性风险分数，并在此处行内标记每个不确定点——`[CITE NEEDED]`（需引用）、`[SME VERIFY]`（需专家核实）——使任何内容都不显得已定论。

## 它不做什么

- 确定公平性——那是法庭基于提示词从未见过的证据和证人的裁决。
- 预测结果——风险分数是指示性的，不是校准过的概率。
- 提供法律意见——它是供律师审查的草稿筛查，结论由律师负责。
- 精确量化养老金损失，或详细覆盖裁员选拔标准挑战。
- 涵盖苏格兰或北爱尔兰。
- 对照实时来源验证法规或判例——依赖前请核对每项引用并重新计算每个数字。

## 要求

- Claude Code 或 Claude Cowork。无需 MCP 连接器。
- 一个要运行的事务（解雇事实、所主张的理由、所遵循的程序）。

## 许可

Apache-2.0。
