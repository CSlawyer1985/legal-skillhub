<div align="center">

# AnythingButLaw.skill

> *"Law school taught you the law. Nobody taught you everything else."*

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-skill-blueviolet.svg)](https://docs.anthropic.com/en/docs/claude-code)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-standard-orange.svg)](https://github.com/anthropics/claude-code)

<br>

Your client asks about the NPV of a settlement.<br>
Opposing counsel throws a regression analysis at you in a discrimination case.<br>
The CFO's numbers in a due diligence don't add up, but you can't say why.<br>
A contract looks fine on paper, but the incentives are all wrong.<br>

**These are not legal problems. They are the problems lawyers actually face.**

**AnythingButLaw** is an AI skill that gives lawyers the non-legal superpowers law school never taught — 9 analytical frameworks covering decision analysis, game theory, contract design, accounting, finance, economics, statistics, and more.

[Knowledge Domains](#knowledge-domains) · [Install](#install) · [Usage](#usage) · [Examples](#examples) · [Why This Exists](#why-this-exists)

[中文](README.md)

</div>

---

> **法外功夫** — 法律之外的真功夫。九大商业分析框架，一个 AI 技能搞定。

## What It Does

AnythingButLaw equips Claude with **9 analytical frameworks** essential for modern legal practice:

- **Build decision trees** for settlement negotiations with expected value, sensitivity analysis, and crossover points
- **Apply game theory** to identify moral hazard, adverse selection, and credible vs. empty threats in negotiations
- **Design contracts** by analyzing incentive alignment, risk allocation, and verifiability across 6 contract types
- **Read financial statements** and spot red flags in due diligence (revenue recognition tricks, cash flow vs. profit gaps)
- **Calculate present value, DCF, and CAPM** for damages quantification and business valuation
- **Analyze markets** using supply/demand, elasticity, surplus, and monopoly frameworks for antitrust work
- **Apply law & economics** to evaluate breach remedies, settlement vs. trial decisions, and optimal sanctions
- **Evaluate statistical evidence** including hypothesis testing, confidence intervals, and the Daubert standard
- **Challenge regression analyses** in discrimination cases by identifying omitted variables, multicollinearity, and two-way causation

## Knowledge Domains

| # | Domain | Reference File | Lawyer Use Cases |
|---|--------|---------------|-----------------|
| 1 | Decision Analysis | `decision-analysis.md` | Settlement strategy, risk aversion, sensitivity analysis |
| 2 | Game Theory & Information | `game-theory.md` | Negotiation, moral hazard, adverse selection, credible threats |
| 3 | Contract Design | `contracting.md` | Contract structure, incentives, risk allocation, breach remedies |
| 4 | Accounting | `accounting.md` | Financial statements, due diligence, fraud detection |
| 5 | Finance | `finance.md` | Present value, DCF, CAPM, damages quantification, valuation |
| 6 | Microeconomics | `microeconomics.md` | Antitrust, market failure, externalities, Coase theorem |
| 7 | Law & Economics | `economic-analysis.md` | Breach remedies, settlement analysis, criminal sanctions |
| 8 | Statistics | `statistics.md` | Hypothesis testing, Daubert standard, confidence intervals |
| 9 | Multivariate Statistics | `multivariate-statistics.md` | Regression in discrimination cases, omitted variable bias |

## Install

### Claude Code (Recommended)

```bash
git clone https://github.com/TracyWang95/AnythingButLaw.git ~/.claude/skills/AnythingButLaw
```

### Manual Install

```bash
git clone https://github.com/TracyWang95/AnythingButLaw.git
# Copy the folder to your Claude Code skills directory
```

See [INSTALL.md](INSTALL.md) for detailed instructions.

## Usage

Once installed, the skill activates automatically when you ask Claude questions involving:

- Settlement negotiations and litigation strategy
- Contract drafting and incentive design
- Financial statement analysis or due diligence
- Business valuation and damages calculation
- Market analysis and antitrust issues
- Statistical evidence evaluation
- Regression analysis in discrimination cases

### Example Prompts

```
"My client received a $1.1M settlement demand. Plaintiff has 50% chance on 
liability, likely damages $1M, but 10% chance of $25M punitive. Should we settle?"

"We're negotiating a service contract — flat fee vs. cost-plus. What are the 
incentive implications of each structure?"

"Opposing counsel submitted a regression showing no gender effect on salary 
after controlling for education and tenure. How do I challenge this?"
```

## Examples

See the [`examples/`](examples/) directory for detailed worked analyses:

- **Settlement Decision Analysis** — Decision tree, expected value, sensitivity analysis, risk aversion
- **Contract Negotiation with Information Asymmetry** — Moral hazard, adverse selection, incentive alignment
- **Discrimination Regression Analysis** — t-statistics, omitted variables, hypothesis testing on proportions

## Why This Exists

### A ¥2,000,000 Skill Set — Now Open Source

Chinese law schools spend four years teaching statutes, cases, jurisprudence, and thesis writing. Then you graduate and discover: your client's problems are never just about the law. Should we settle? Are the CFO's numbers real? Does this contract create a moral hazard? Can we trust that regression analysis? — Law school never mentioned any of this.

**This isn't your fault. Chinese legal education simply doesn't have this course.**

American law schools teach a course that covers 9 non-legal skills essential for lawyers: decision analysis, game theory, contract design, accounting, finance, microeconomics, law & economics, statistics, and multivariate regression. Not a liberal arts elective — real analytical frameworks, each targeting the most critical non-legal pain points in legal practice.

The tuition, living costs, and opportunity cost of a 3-year JD add up to roughly **¥2,000,000 (≈$280K)**.

When I went to Notre Dame Law School, it felt like stumbling into a hidden martial arts sect — I thought I was going to learn more advanced law, but the most valuable skills turned out to be everything *outside* the law. That's why the Chinese name is **法外功夫** ("kung fu beyond the law"): decision trees, game theory, regression analysis — none of it is law, but every bit of it keeps you alive on the legal battlefield.

The problem: this "secret knowledge" has only been passed down to a handful of students. Hundreds of thousands of Chinese lawyers will never encounter it in their careers.

**So I open-sourced it.**

**AnythingButLaw** condenses a ¥2M education into one AI skill. No JD required. No three-year commitment. No English fluency needed. Install this skill, and Claude becomes your personal analyst — ready to deploy 9 analytical frameworks for negotiation, due diligence, litigation, and beyond.

The most dangerous gap isn't lacking the skill — it's not knowing the skill exists.

Now you know.

## Project Structure

```
AnythingButLaw/
├── SKILL.md                    # Main skill entry point (AgentSkills standard)
├── references/                 # Deep domain knowledge (loaded on demand)
│   ├── decision-analysis.md
│   ├── game-theory.md
│   ├── contracting.md
│   ├── accounting.md
│   ├── finance.md
│   ├── microeconomics.md
│   ├── economic-analysis.md
│   ├── statistics.md
│   └── multivariate-statistics.md
├── examples/                   # Worked examples
├── README.md
├── README_ZH.md
├── INSTALL.md
└── LICENSE
```

## Evaluation Results

Tested against 3 legal practice problems (settlement analysis, contract negotiation, discrimination regression):

| Metric | With Skill | Baseline | Delta |
|--------|-----------|----------|-------|
| **Pass Rate** | **100%** | 73.3% | +26.7% |
| Tokens | 23,968 | 14,451 | +66% |
| Time | 117s | 79.8s | +47% |

**Key finding**: The skill's biggest impact is on problems requiring multi-step incentive reasoning (game theory + contract design). In the contract negotiation test, the baseline completely missed a moral hazard problem, recommending the wrong contract. The skill correctly identified it.

## Credits

- **Inspired by**: [colleague.skill](https://github.com/titanwings/colleague-skill) by @titanwings
- **Powered by**: Claude Code + AgentSkills standard

## License

[MIT](LICENSE)
