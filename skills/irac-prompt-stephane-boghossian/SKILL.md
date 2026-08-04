---
name: "irac-prompt-stephane-boghossian"
version: 0.1.0
description: |
  将任何粗糙的构建、研究或法律起草请求重构为 IRAC 形状的提示——Issue（争点）、Rule（规则）、Analysis（分析）、Conclusion（结论）——为前沿模型优化。它是律师资格考试框架，被重新用作提示工程。该技能以争点开头、以结论结尾（模型最重视注意力的位置），迫使您说出约束和非目标，并在生成单个 token 之前明确"好"的样子。在任何非平凡的构建之前使用它，或每当模糊的请求值得精确的简报时使用。
triggers:
  - irac this
  - structure this prompt
  - make a proper prompt for X
  - brief the model
  - turn this into a memo prompt
  - prompt like a lawyer
metadata:
  author: "Stephane Boghossian"
  license: "agpl-3.0"
  version: "2026-06-05"
---

# IRAC 提示

律师不会把"去查查那件住房的事"扔给助理。他们写备忘录：这是**争点**，这是管辖它的**规则**，这是它们如何适用的**分析**，这是我要的**结论**。同样的结构是影响前沿模型输出质量的单一最大杠杆。本技能将模糊的请求转化为那份简报。

## 何时使用
- 用户有模糊的构建/研究/起草任务，想要一个好的提示，而非猜测。
- 在启动非平凡的 vibecode 任务之前（自然地在 `/grill-me` 和 `/yalla` 之前配合使用）。
- 重新打包任务交给子代理或 HAQQ 的 Justinian。

## 方法

取用户的原始请求并将其重写为四个带标签的块。**以争点开头，以结论结尾**——模型最重视提示的顶部和底部。

### I——争点（顶部）
一两句话：我们到底要做什么、为谁做。单一问题陈述。如果用户给了三个问题，选择重要者或拆分为三个提示。*没有问题，就没有解决方案，没有价值。*

### R——规则（约束）
模型必须尊重的管辖事实：
- 硬约束（技术栈、语言、库、文件路径、输出格式）。
- 领域规则（法律方面：法规/条款/法域；代码方面：API 契约、要匹配的现有模式）。
- 非目标——不要做什么。律师会说明他们不想要什么；同样做。
- 完成定义 / "好"的样子，理想情况下可衡量。

### A——分析（模型应做的推理）
- 这为何重要以及真正的用户是谁。
- 已知的难点 / 先前尝试或较弱模型失败之处。
- 要采用的方法或第一性原理（或明确说："找出方法，这里是输入"）。
- 要处理的边缘情况：空状态、认证失败、网络错误、畸形输入。

### C——结论（请求）
具体交付物，清晰地重述。什么制品、什么形态、如何验证。

## 输出契约
在被围栏的代码块内发出重写后的提示，供用户逐字复制，带四个标题（**Issue / Rule / Analysis / Conclusion**）。然后，在围栏下方，附 2-3 行说明，说明您推断或假定的内容，以及任何值得 `/grill-me` 检查的缺口。不要注水——如果某个块确实为空（罕见），如实说明，而不是编造约束。

## 修饰符（用户可以要求任何这些）

**`--adversarial`** —— 附加一个三代理拆分，使没有代理为自己的作业打分（Mike 的核心技巧：*"你不会问助理他们是否复查过；你会把它交给别人"*）：
> 以三个角色运行。**规划者**：根据争点/规则产出步骤计划，不写代码。
> **执行者**：对照规则约束实施计划。**测试者**：对抗性地
> 对照完成定义和边缘情况核实执行者的输出；报告失败，
> 不修复。循环执行者↔测试者直到测试者通过。（映射到 `/grill-me` + `/lecun-world-model`。）

**`--budget`** —— 前置一条上下文预算指令（Mike：随着上下文填满，性能"断崖式下降"）：
> 将上下文窗口视为预算，而非垃圾场。保持此提示精简。使用带
> 窄任务和新上下文的并行子代理，而非一个臃肿的代理。在阶段之间压缩或开始
> 新对话。仅加载每个步骤需要的 Skills/文件。

**`--voice`** —— 用户口述的；容忍不流利、推断结构、不挑剔措辞。

**`--legal`** —— Issue/Rule/Analysis/Conclusion 字面映射到 IRAC。规则 = 法规/条款 + 法域；分析 = 适用于事实；标记任何依赖判断的事项（JUDGMENT-BOUND，交给 `/law-as-code-audit`）。绝不断言源文本不支持的法定结论。

## 演练示例

**原始请求：** "make something that checks if building permits are gonna get rejected"

**输出：**
```
ISSUE
Build a tool that, given a set of ADU building-permit blueprints, flags the corrections a California city plan-reviewer will require — before submission — for the builder filing the permit.

RULE
- Inputs: multi-page blueprint PDFs, table-sized, with dense margin annotations.
- Constraint: OCR alone strips annotations from the wall/element they reference —
  preserve visual context (which wall a "thickness" note belongs to).
- Stack: Anthropic SDK, parallel sub-agents, Skills for the ruleset. No paralegal in the loop.
- Done = ≥70% agreement with the city's real correction letters on a held-out set.
- Non-goal: do not auto-submit or give legal advice; output is an action plan a human files.

ANALYSIS
Prior generation models can't do this — that's the point. The hard part is grounding each rule check in the right region of the blueprint. Chunk the blueprint, pass each chunk + the relevant rules, ask "what's wrong here," then aggregate. Handle: missing pages, illegible scans, blueprints with no annotations.

CONCLUSION
A pipeline that ingests blueprints and returns a precise, per-item correction action plan in <20 min, benchmarked hourly against the correction-letter set.
```
*推断：从"permits"推断出 ADU + 加利福尼亚州 + 建造方一侧。留给 /grill-me 的开放问题：仅建造方一侧，还是也包括城市审查员一侧？（CrossBeam 最终两者都做了。）*

## 说明
- 本技能撰写*提示*，不执行任务。
- 灵感来自 Michael T. Brown 的 CrossBeam——这位人身伤害律师从未写过一行代码，通过像向助理简报一样提示模型，击败 13,000 名建造者赢得 Anthropic 2026 年全球黑客马拉松。三个修饰符：--adversarial（规划→执行→测试的代理拆分，使没有代理为自己的作业打分）、--budget（将上下文窗口视为预算，而非垃圾场）和 --legal（字面 IRAC，标记依赖判断的条款）。
