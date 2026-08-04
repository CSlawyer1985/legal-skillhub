# Installation Guide | 安装指南

## Claude Code (Recommended)

```bash
# Clone the repo into your Claude Code skills directory
git clone https://github.com/TracyWang95/AnythingButLaw.git ~/.claude/skills/AnythingButLaw
```

That's it. The skill will be available next time you start a Claude Code session.

## Verify Installation

Ask Claude:

```
"A plaintiff has a 60% chance of winning $500K. Trial costs $80K. 
Is a $250K settlement offer reasonable?"
```

If the skill is working, Claude will:
1. Build a decision tree
2. Calculate the expected value ($300K + $80K = $380K vs $250K settlement)
3. Discuss risk aversion
4. Recommend the settlement

## Manual Install

If you prefer not to use git:

1. Download the repository as a ZIP file from GitHub
2. Extract it
3. Copy the `AnythingButLaw` folder to `~/.claude/skills/`

## Requirements

- Claude Code CLI or Claude Code Desktop
- No Python dependencies required (pure markdown skill)

## Project Structure

```
AnythingButLaw/
├── SKILL.md                    # Main entry point — Claude reads this first
├── references/                 # Domain knowledge — loaded on demand
│   ├── decision-analysis.md    # Decision trees, expected value, risk aversion
│   ├── game-theory.md          # Nash equilibrium, moral hazard, adverse selection
│   ├── contracting.md          # 6 contract types, incentives, risk allocation
│   ├── accounting.md           # Financial statements, GAAP, ratios, fraud
│   ├── finance.md              # PV/FV, DCF, CAPM, valuation, EMH
│   ├── microeconomics.md       # Supply/demand, elasticity, monopoly, externalities
│   ├── economic-analysis.md    # Breach remedies, settlement theory, criminal law
│   ├── statistics.md           # Hypothesis testing, z-tests, Daubert
│   └── multivariate-statistics.md  # Regression, dummy variables, omitted bias
├── examples/                   # Worked analysis examples
├── README.md                   # English documentation
├── README_ZH.md                # 中文文档
├── INSTALL.md                  # This file
└── LICENSE                     # MIT
```

## How It Works

1. **SKILL.md** is always loaded into Claude's context (~500 lines). It contains the routing logic and cross-cutting principles.
2. When you ask a question, Claude reads SKILL.md and determines which **reference files** are relevant.
3. Claude reads only the needed reference files, keeping context usage efficient.
4. Complex problems may trigger multiple reference files (e.g., a merger question might need `finance.md` + `contracting.md` + `game-theory.md`).
