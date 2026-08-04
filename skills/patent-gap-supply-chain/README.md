# patent-gap-supply-chain

通过"专利缺口"反推产业链关系的竞争情报工作流 skill，适用于 WorkBuddy / Codebuddy / Claude Code / Codex。

A competitive intelligence workflow skill that infers supply-chain relationships from patent gaps. Works with WorkBuddy / Codebuddy / Claude Code / Codex.

---

## 中文说明

### 这是什么

当研究科技股 / 硬件 / 制造 / 医药类公司时，发现标的 A 的产品使用了技术 T，但 A 没有 T 的相关专利——这套 skill 引导从专利缺口切入，激活专利归属 / 工商关联 / 人才流动 / 采购招标 / 产品拆解五条线索并行验证，并内置替代假设检查与反情报对抗检查，输出带置信度的产业链关系推断报告。

### 核心设计

- **专利降级为入口线索**：专利缺口只触发验证，不直接定论
- **多线索交叉印证**：≥2 条高置信线索相互印证方可定论
- **替代假设必查**：显式排除交叉授权 / NPE / 第三方模组等替代解释
- **反情报对抗必查**：警惕被研究方用壳公司 / 分散专利掩盖真实供应链
- **触发点前移**：不依赖 agent 自动深挖到专利缺口，触发词覆盖"科技股研究 / 行业分析"等更早的意图入口

### 安装

    git clone https://github.com/tianzhiceng297-boop/patent-gap-supply-chain.git ~/.workbuddy/skills/patent-gap-supply-chain

或手动复制 `SKILL.md` 和 `references/` 到 `~/.workbuddy/skills/patent-gap-supply-chain/`。

### 兼容性 / Compatibility

| Agent | 加载方式 |
|------|---------|
| WorkBuddy / Codebuddy | 放入 `~/.workbuddy/skills/`，自动加载 + 触发词触发（原生支持） |
| Claude Code | 将 `SKILL.md` 内容追加到项目 `CLAUDE.md`，或放入 `.claude/commands/` 作为自定义命令；`references/` 按需在命令中引用 |
| Codex (OpenAI) | 将 `SKILL.md` 内容追加到项目 `AGENTS.md`；`references/` 按需引用 |
| 其他 agent | 将 `SKILL.md` 作为 system prompt 或项目指令注入；`references/` 按需提供 |

> 本 skill 的指令内容是通用 markdown，任何能读取并执行 markdown 指令的 agent 均可使用。区别仅在于加载机制：WorkBuddy 原生支持自动触发，其他 agent 需手动注入或配置。

### 触发场景

- "研究 XX 科技股"
- "分析 XX 公司的供应链"
- "查一下 XX 技术的专利归属"
- "XX 公司用了某技术但好像没专利"
- "识别 XX 的供应商"

### 适用边界

| 标的类型 | 适用性 |
|---------|--------|
| 硬件 / 制造 / 医药 / 材料 | 强适用 |
| 软件 / 互联网 | 弱适用（降低置信度） |
| 商业模式创新 | 不适用 |

---

## English

### What it is

When researching tech / hardware / manufacturing / pharma companies, you find that target A's product uses technology T, but A holds no patents related to T. This skill starts from the patent gap, activates five parallel verification leads — patent ownership, corporate affiliation, talent flow, procurement, product teardown — with built-in alternative-hypothesis checks and counter-intelligence checks, outputting a confidence-scored supply-chain inference report.

### Core design

- **Patents demoted to an entry lead**: a patent gap triggers verification but does not directly conclude
- **Multi-lead corroboration**: ≥2 high-confidence leads corroborating required to conclude
- **Alternative hypotheses are mandatory**: explicitly exclude cross-licensing / NPE / third-party-module explanations
- **Counter-intelligence check is mandatory**: watch for shell companies / dispersed patents hiding the real supply chain
- **Trigger point moved upstream**: does not rely on the agent autonomously digging to the patent gap; trigger keywords cover earlier intent entries like "tech stock research / industry analysis"

### Installation

    git clone https://github.com/tianzhiceng297-boop/patent-gap-supply-chain.git ~/.workbuddy/skills/patent-gap-supply-chain

Or manually copy `SKILL.md` and `references/` to `~/.workbuddy/skills/patent-gap-supply-chain/`.

### Compatibility

| Agent | How to load |
|-------|-------------|
| WorkBuddy / Codebuddy | Drop into `~/.workbuddy/skills/`; auto-loaded + trigger-keyword activation (native) |
| Claude Code | Append `SKILL.md` content to the project `CLAUDE.md`, or place under `.claude/commands/` as a custom command; reference `references/` as needed |
| Codex (OpenAI) | Append `SKILL.md` content to the project `AGENTS.md`; reference `references/` as needed |
| Other agents | Inject `SKILL.md` as a system prompt or project instruction; provide `references/` on demand |

> The skill's instructions are plain markdown — any agent that can read and execute markdown instructions can use it. The only difference is the loading mechanism: WorkBuddy supports auto-triggering natively; other agents require manual injection or configuration.

### Trigger scenarios

- "Research [tech stock]"
- "Analyze [company]'s supply chain"
- "Look up patent ownership of [technology]"
- "[Company] uses a technology but seems to have no patents"
- "Identify [company]'s suppliers"

### Applicability

| Target type | Applicability |
|-------------|---------------|
| Hardware / manufacturing / pharma / materials | Strong |
| Software / internet | Weak (reduce confidence) |
| Business-model innovation | Not applicable |

---

## File structure

- `SKILL.md` — core: triggers, applicability pre-check, 7-step workflow overview, I/O contract, tool integration, key principles
- `references/workflow.md` — detailed 7-step operations (decision rules, tool invocation, output format)
- `references/checklists.md` — alternative-hypothesis checklist, counter-intelligence checklist, confidence scoring rules
- `examples/sample-output.md` — worked example showing the full report format
- `CHANGELOG.md` — version history

## License

MIT
