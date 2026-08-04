---
name: AnythingButLaw
description: "法外功夫 — Non-legal business skills for lawyers. Decision analysis, game theory, contract design, accounting, finance, microeconomics, law & economics, statistics, and regression analysis distilled into deep, actionable frameworks for legal practice. Each domain includes formulas with LaTeX notation, worked examples, adversarial checklists, and book-aligned structure. | 律师必备的非法律商业技能深度参考：决策分析、博弈论、合同设计、会计、金融、微观经济学、法经济学、统计分析、多元回归。每章都包含完整公式推导、worked examples、对抗清单与经典判例。当用户涉及和解谈判、合同激励、财务尽调、企业估值、损害赔偿计算、反垄断分析、统计证据评估、歧视诉讼回归分析、hold-up、效率违约、Daubert 动议等场景时触发。"
version: "2.0.0"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---

# 法外功夫 · AnythingButLaw

> 法学院教你法律，但客户的问题从来不只是法律。

本技能将律师必备的九大非法律商业知识蒸馏为可直接调用的深度思维框架。目标不是把你变成会计师或经济学家，而是让你能够：
- **识别假设**：当对方扔出一个数字，你知道该追问什么
- **提出关键问题**：用正确的框架拆解商业问题
- **判断答案是否合理**：知道什么时候一个"合理"的数字其实不合理
- **用对抗清单系统挑战对方专家**：无论是统计、财务还是经济证据

## 九大知识域

每个参考文件都包含：**核心框架 + 公式推导 (LaTeX) → Worked Example → 律师对抗清单 → 经典判例 → 常见陷阱速查表**。

| # | 域 | 参考文件 | 律师核心场景 |
|---|---|---|---|
| 1 | 决策分析 | `references/decision-analysis.md` | 诉讼策略、和解 vs 开庭、风险规避、贝叶斯更新、VOI |
| 2 | 博弈论与信息 | `references/game-theory.md` | 谈判、道德风险、逆向选择、承诺机制、Rubinstein 讨价还价 |
| 3 | 合同设计 | `references/contracting.md` | 激励对齐、风险分配、hold-up、关系型合同、委托代理模型 |
| 4 | 会计 | `references/accounting.md` | 三大报表、DuPont、Altman Z、Beneish M、尽调红旗 |
| 5 | 金融 | `references/finance.md` | 现值、DCF、WACC、CAPM、Black-Scholes、事件研究、MM 命题 |
| 6 | 微观经济学 | `references/microeconomics.md` | 反垄断、HHI、SSNIP、弹性、外部性、Coase 定理 |
| 7 | 法经济学 | `references/economic-analysis.md` | Hand 公式、Calabresi-Melamed、Becker 犯罪模型、效率违约 |
| 8 | 统计分析 | `references/statistics.md` | 假设检验、贝叶斯、Daubert、检察官谬误、多重比较 |
| 9 | 多元统计 | `references/multivariate-statistics.md` | OLS、遗漏变量、IV、DiD、logistic、歧视回归 |

## Worked Examples 目录

完整的 worked example 文件，每个覆盖一个或多个知识域：

| 文件 | 情境 | 涉及知识域 |
|---|---|---|
| `examples/settlement-decision-analysis.md` | IMP 案 110 万和解要约 vs 审判 | 决策分析、敏感性 |
| `examples/contract-negotiation-game-theory.md` | Washington Unicorns 球员合同 | 博弈论、合同设计 |
| `examples/discrimination-regression-analysis.md` | ISA 薪酬性别歧视 | 多元统计、回归 |
| `examples/accounting-due-diligence.md` | CloudLedger SaaS 尽调红旗 | 会计、金融 |
| `examples/damages-valuation-dcf.md` | FreshBite 特许经营违约损害 | 金融、决策分析 |
| `examples/antitrust-market-definition.md` | ZipBite + FlashFood 合并审查 | 微观经济学、SSNIP、HHI |
| `examples/efficient-breach-and-hold-up.md` | NovaCure 制药分销合同 | 法经济学、合同、博弈论 |
| `examples/statistical-evidence-daubert.md` | Lakeside 环境癌症诉讼 | 统计、Daubert、多元统计 |
| `examples/hand-formula-negligence.md` | 电动滑板车产品责任 | 法经济学、过失 |
| `examples/auction-bidding-strategy.md` | GeneScope IP 破产拍卖 | 博弈论、决策分析 |

## 如何使用

**路由逻辑：**

- **"该不该做 X"类的决策** → `decision-analysis.md` → 相关领域
- **和解 vs 开庭 / 谈判策略** → `decision-analysis.md` + `game-theory.md`
- **合同条款激励 / 风险分配** → `contracting.md`（可能需要 `game-theory.md`）
- **财务报表、尽调红旗** → `accounting.md`（深层估值加 `finance.md`）
- **企业估值、损害赔偿金额** → `finance.md`
- **反垄断、市场界定、价格分析** → `microeconomics.md`
- **效率违约、Hand 公式、法律制度设计** → `economic-analysis.md`
- **数据证据、抽样、显著性、Daubert 挑战** → `statistics.md`
- **歧视回归、因果推断** → `multivariate-statistics.md`（可能需要 `statistics.md`）

**复杂问题**（如一个涉及估值 + 合同 + 博弈的并购交易）应同时读取多个相关文件。**大多数真实案件至少横跨 2–3 个知识域**——这正是本技能的价值所在。

## 六条贯穿法则

这些主题在所有九个域中反复出现，是律师"法外功夫"的内功心法：

### 1. 风险与不确定性管理
从决策树的期望值计算，到金融中的风险-回报权衡，再到合同中的风险分配。核心工具：期望值、确定性等价、敏感性分析、分散投资、VOI、贝叶斯更新。

### 2. 信息不对称
博弈论中的道德风险和逆向选择、合同设计中的可验证性问题、会计中的审计独立性、法经济学中的不完全合同。**几乎所有商业法律问题的根源都是信息不对称**。识别它是解决问题的第一步。

### 3. 激励设计
从合同中的绩效激励 vs 投入激励，到博弈论中的囚徒困境，再到法经济学中的威慑理论。**好的法律方案本质上是好的激励设计**。问自己：这个条款/规则/制度给各方创造了什么激励？

### 4. 估值与量化
会计的 DuPont / 财务比率、金融的 DCF / CAPM / WACC、统计的假设检验、多元统计的回归。律师不需要自己算，但需要知道对方的数字是怎么来的、哪些假设可以挑战、什么量级是合理的。

### 5. 社会福利与效率
微观经济学的剩余最大化、法经济学的 Kaldor-Hicks 效率、福利经济学的规范框架。理解效率概念帮助律师在政策倡导、监管合规和公益诉讼中找到经济学论据。

### 6. 因果推断
相关 ≠ 因果。遗漏变量、反向因果、选择偏差、混杂变量——这些才是现代证据法争议的核心。工具箱：OLS、IV、DiD、RD、倾向得分匹配、合成控制法。

## 输出风格

- **始终以律师的实际工作场景为出发点**，不是教科书式讲解
- **公式用 LaTeX 标记**（GitHub 原生支持 `$...$` 和 `$$...$$` 渲染）
- **中英双语术语**（如"确定性等价 (certainty equivalent)"），因为很多概念在中文法律文献中无统一译名
- **用 worked example 和对比表格** 解释抽象概念
- **数字 + 敏感性分析**：不给单点估计，给范围和关键阈值
- **对抗清单思维**：面对任何证据，先问"这里哪里可能出错？"
- 如果用户的问题跨越多个域，**先给一个整体框架**，再深入每个部分
- **承认局限**：当数据不够、假设不合理时明确说出来

## 版本

- **v1.0** (2025): 初版，PPT 提纲结构
- **v2.0** (2026): 深度扩写，LaTeX 公式化，worked examples 扩至 10 个，每章增加对抗清单和经典判例
