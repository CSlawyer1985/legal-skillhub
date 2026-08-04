<div align="center">

# 法外功夫 AnythingButLaw.skill

> *法学院教你法律，但客户的问题从来不只是法律。*

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-skill-blueviolet.svg)](https://docs.anthropic.com/en/docs/claude-code)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-standard-orange.svg)](https://github.com/anthropics/claude-code)

<br>

客户问你和解方案的净现值是多少。<br>
对方律师在歧视案中扔出一份回归分析。<br>
尽调中 CFO 的数字对不上，但你说不出哪里不对。<br>
合同条款看着没问题，但激励机制全是坑。<br>

**这些不是法律问题。这些才是律师真正面对的问题。**

**法外功夫** 将九大商业分析框架蒸馏成一个 AI 技能，赋予律师法学院从未教过的非法律超能力。

[知识域](#九大知识域) · [安装](#安装) · [使用](#使用方法) · [示例](#示例) · [为什么做这个](#为什么做这个)

[English](README_EN.md)

</div>

---

## 它能做什么

法外功夫为 Claude 装备了 **9 大深度分析框架**，覆盖现代法律实务的核心非法律需求。每个框架都包含 **LaTeX 公式推导、worked examples、对抗清单、经典判例、常见陷阱速查表**：

- **构建决策树** 用于和解谈判，包含期望值、贝叶斯更新、VOI、效用函数、敏感性分析
- **运用博弈论** 识别道德风险、逆向选择、可信 vs 空洞威胁、Rubinstein 讨价还价、重复博弈
- **设计合同** 分析 6 种合同类型、委托代理模型、hold-up、关系专用投资、关系型合同
- **解读财务报表** 在尽调中发现红旗信号：DuPont 分解、Altman Z-Score、Beneish M-Score
- **计算现值、DCF、WACC、CAPM、Black-Scholes** 用于损害赔偿量化和企业估值
- **运行事件研究法** 量化证券欺诈的 per-share damages
- **分析市场** 运用 HHI、SSNIP、弹性、消费者剩余、掠夺性定价框架支持反垄断工作
- **运用法经济学** 评估 Hand 公式、Calabresi-Melamed、Becker 犯罪模型、效率违约
- **评估统计证据** 包括假设检验、贝叶斯推理、检察官谬误、Daubert 标准、多重比较校正
- **挑战回归分析** 识别遗漏变量、多重共线性、双向因果，使用 IV、DiD、RD 等现代因果推断工具

## 九大知识域

| # | 域 | 参考文件 | 律师核心场景 |
|---|---|---------|------------|
| 1 | 决策分析 | `decision-analysis.md` | 诉讼策略、和解、贝叶斯、VOI、效用函数 |
| 2 | 博弈论与信息 | `game-theory.md` | 讨价还价、道德风险、逆向选择、承诺机制 |
| 3 | 合同设计 | `contracting.md` | 委托代理、hold-up、关系型合同、违约救济 |
| 4 | 会计 | `accounting.md` | 三大报表、DuPont、Altman Z、Beneish M |
| 5 | 金融 | `finance.md` | DCF、WACC、CAPM、Black-Scholes、事件研究 |
| 6 | 微观经济学 | `microeconomics.md` | HHI、SSNIP、弹性、外部性、Coase 定理 |
| 7 | 法经济学 | `economic-analysis.md` | Hand 公式、Calabresi-Melamed、Becker 模型 |
| 8 | 统计分析 | `statistics.md` | 假设检验、贝叶斯、Daubert、多重比较 |
| 9 | 多元统计 | `multivariate-statistics.md` | OLS、IV、DiD、遗漏变量、歧视回归 |

## Worked Examples（10 个完整案例）

每个 example 都是真实情境下的完整数值分析，含公式、计算、敏感性分析和建议：

- `settlement-decision-analysis.md` — 和解 vs 审判的期望值陷阱
- `contract-negotiation-game-theory.md` — 球员合同中的道德风险 + 逆向选择
- `discrimination-regression-analysis.md` — 薪酬歧视的回归分析
- `accounting-due-diligence.md` — SaaS 公司的收入确认红旗
- `damages-valuation-dcf.md` — 特许经营违约的 DCF 损害赔偿计算
- `antitrust-market-definition.md` — 合并审查的 SSNIP + HHI 分析
- `efficient-breach-and-hold-up.md` — 制药合同中的效率违约与 hold-up
- `statistical-evidence-daubert.md` — 环境癌症诉讼的 Daubert 挑战
- `hand-formula-negligence.md` — 电动滑板车产品责任与 Hand 公式
- `auction-bidding-strategy.md` — 破产拍卖的投标策略

## 安装

### Claude Code（推荐）

```bash
git clone https://github.com/TracyWang95/AnythingButLaw.git ~/.claude/skills/AnythingButLaw
```

详见 [INSTALL.md](INSTALL.md)。

## 使用方法

安装后，当你向 Claude 提出涉及以下场景的问题时，技能会自动触发：

- 和解谈判与诉讼策略
- 合同起草与激励设计
- 财务报表分析与尽调
- 企业估值与损害赔偿计算
- 市场分析与反垄断
- 统计证据评估
- 歧视案件中的回归分析

### 示例提问

```
"客户收到110万和解要求。原告责任认定概率50%，可能赔偿100万，
但有10%概率判2500万惩罚性赔偿。该不该接受和解？"

"我们在谈一个服务合同——固定费用还是成本加成。各自的激励问题是什么？"

"对方提交了一份回归分析，控制学历和工龄后声称性别系数不显著。怎么挑战这个分析？"
```

## 示例

详见 [`examples/`](examples/) 目录中的完整分析案例。

## 为什么做这个

### 一套价值 200 万的功夫

中国法学院四年，教你法条、判例、法理、论文。毕业之后你发现：客户的问题从来不只是法律。和解该不该接？对方财报有没有水分？合同条款的激励机制对不对？回归分析结论能不能信？——这些问题，法学院一个字都没教过。

**这不是你的错。中国法学教育体系里，就没有这门课。**

美国法学院有一门课，专门教律师九种非法律技能：决策分析、博弈论、合同设计、会计、金融、微观经济学、法经济学、统计分析、多元回归。不是通识教育、不是选修水课——是真刀真枪的分析框架，每一个都直指法律实务中最核心的非法律痛点。

这门课的学费、生活费、加上三年 JD 的机会成本，折合人民币大概 **200 万**。

我去 Notre Dame 读法学院的时候，有点像杨过误入古墓派——本以为是去学更高深的法律，结果发现最值钱的功夫全在法律之外。全中国几十万律师，绝大多数一辈子都接触不到。

**所以我把它开源了。**

**法外功夫** 把这 200 万的课程浓缩成一个 AI 技能。你不需要去美国读 JD，不需要花三年时间，甚至不需要会英文。装上这个技能，Claude 就是你的古墓派师父——随时调用九大分析框架，帮你在决策、谈判、尽调、诉讼中看到别人看不到的东西。

武林中最怕的不是功夫差，是不知道有这门功夫。

现在你知道了。

## 评测结果

| 指标 | 有技能 | 基线 | 差异 |
|------|--------|------|------|
| **通过率** | **100%** | 73.3% | +26.7% |
| Tokens | 23,968 | 14,451 | +66% |
| 时间 | 117s | 79.8s | +47% |

## 致谢

- **灵感来源**：[colleague.skill](https://github.com/titanwings/colleague-skill) by @titanwings
- **驱动力**：Claude Code + AgentSkills standard

## 许可证

[MIT](LICENSE)
