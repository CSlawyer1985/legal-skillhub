# CementOps MSHA Compliance Agent

**Part of the [CementOps Compliance Suite](https://cementops.ai) — Free on ClawHub**

MSHA regulatory compliance for cement plant operations — hazard classification, stop-work gating, citation defense, and walk-through preparation.

Built from 12 years of hands-on cement plant operations experience. Speaks plant-floor language, not legal jargon.

## What It Does

| Capability | Description |
|-----------|-------------|
| **Hazard Classification** | Report a hazard (text or photo) and get: category, risk score (1-5), applicable 30 CFR citations, and recommended controls — immediate and permanent |
| **Deterministic Stop-Work** | 25 imminent danger rules evaluated by code, not the model. If the rule engine says stop, the agent says stop. Fail-safe defaults to stop-work if rules can't load. |
| **Citation Lookup** | Top 20 most-cited MSHA standards for cement (SIC 3241) with penalty ranges, S&S likelihood, inspector focus areas, and defense strategies |
| **Citation Defense** | Draft defense strategy outlines with evidence checklists, argument frameworks, and rebuttal letter templates. Covers machine guarding, housekeeping, LOTO, fall protection, and S&S contestation. |
| **Walk-Through Prep** | Inspection readiness checklists by plant area, top citation targets, documentation prep, and "gotcha" items inspectors specifically look for in cement plants |
| **Training Support** | Part 46 training requirements, plain-language CFR explanations, cement-specific examples |

## Why This Exists

Cement plants get cited. A lot. The average US cement plant receives 15-25 MSHA citations per year. The top citations — machine guarding, housekeeping, equipment defects, fall protection, LOTO — are the same ones every plant fights.

This skill puts 30 CFR Part 56 knowledge into an agent that:
- Talks like a plant safety professional, not a lawyer
- Makes stop-work decisions with code, not model inference
- Knows where inspectors look first (conveyor galleries, then the MCC room)
- Knows the defense playbook for the citations you'll actually receive

## Safety Architecture

**The stop-work system is deterministic.** The LLM classifies hazards. A Python script (`check_stopwork.py`) makes the stop/continue decision. The model cannot override, soften, or delay a stop-work directive.

```
Worker reports hazard
        |
        v
  LLM extracts description
        |
        v
  check_stopwork.py evaluates
  against 25 imminent danger rules
        |
    +---+---+
    |       |
 STOP    CONTINUE
 WORK       |
    |       v
    |   LLM classifies hazard,
    |   cites CFR, recommends
    |   controls
    v
 Agent delivers
 stop-work directive
 EXACTLY as written
 in rules. No hedging.
```

**Fail-safe:** If `stop-work-rules.json` or `check_stopwork.py` can't be loaded, the agent defaults to STOP WORK. The system fails safe, not open.

## What's Included

```
msha-compliance/
  SKILL.md                  — Agent instructions (ClawHub manifest)
  README.md                 — This file
  check_stopwork.py         — Deterministic stop-work engine (25 rules, 47 self-tests)
  stop-work-rules.json      — Imminent danger conditions with keywords and CFR references
  citation-rules.json       — Top 20 cement plant citations with penalties and defenses
  hazard-taxonomy.json      — 13-category hazard classification system
  test-queries.json         — 50-query evaluation suite with scoring criteria
  defense-templates/
    machine-guarding-defense.md   — 56.14107(a) rebuttal framework
    housekeeping-defense.md       — 56.20003 rebuttal framework
    lockout-tagout-defense.md     — 56.12016 rebuttal framework
    fall-protection-defense.md    — 56.15005 rebuttal framework
    general-ss-contest.md         — S&S (Mathies test) contestation framework
```

## Quick Start

Install from ClawHub:

```bash
npx clawhub@latest install cementops-msha-compliance
```

Or clone manually and point your agent to the skill directory:

```bash
openclaw agent --agent main --local \
  --skill-path /path/to/msha-compliance \
  -m "What are the MSHA requirements for conveyor belt guarding?" \
  --session-id test
```

### Verify the stop-work engine:

```bash
# Should return STOP_WORK
python3 check_stopwork.py "rotating shaft with no guard"

# Should return CONTINUE
python3 check_stopwork.py "dust accumulation on walkway"

# Run the full self-test suite (47 cases)
python3 check_stopwork.py --test
```

## Who This Is For

- **Plant safety managers** — walk-through prep, citation defense, hazard classification
- **Plant supervisors** — real-time hazard assessment from the floor (via Telegram or chat)
- **Safety consultants** — citation analysis and defense strategy for cement clients
- **Plant IT teams** — the deterministic stop-work architecture means safety decisions are auditable and not model-dependent

## Limitations

- **This is regulatory analysis, not legal advice.** The agent always recommends engaging qualified legal counsel for formal citation proceedings.
- **The stop-work engine uses keyword matching.** It catches the vast majority of imminent danger reports but can miss unusual phrasing. The fail-safe ensures it errs toward stopping.
- **Citation data is based on published 30 CFR Part 56 standards.** Penalty amounts are typical ranges — actual penalties depend on MSHA's assessment of negligence, gravity, good faith, history, and operator size.
- **This skill is designed for cement manufacturing (SIC 3241).** It applies to operations regulated under 30 CFR Part 56 (Surface Metal and Nonmetal Mines). It does not cover underground mining (Part 57) or coal mining (Parts 70-90).

## NemoClaw Deployment

For enterprise deployment inside a NemoClaw sandbox, use the included security policy to restrict the agent to approved endpoints only:

```yaml
# Approved network egress (see full policy in runbook)
- www.msha.gov:443         # MSHA databases (read-only)
- arlweb.msha.gov:443      # MSHA data retrieval
- www.ecfr.gov:443         # Electronic Code of Federal Regulations
- integrate.api.nvidia.com:443  # Nemotron inference
- api.anthropic.com:443    # Claude fallback
```

Everything else is blocked. This is the security story for plant IT teams.

---

## CementOps AI Skill Catalog

This skill is part of the **CementOps Compliance Suite** — 3 free skills covering MSHA, safety training, and environmental compliance. CementOps AI builds 18 specialized AI skills covering every area of cement plant operations.

| # | Skill | Domain | Availability |
|---|---|---|---|
| 1 | **MSHA Compliance** | Regulatory/citation defense | Free on ClawHub |
| 2 | **Safety Training** | Part 46 training programs | Free on ClawHub |
| 3 | **Environmental Compliance** | EPA/NESHAP/CEMS/Title V | Free on ClawHub |
| 4 | Pyroprocessing | Kiln/preheater/cooler optimization | CementOps AI Platform |
| 5 | Raw Grinding | Raw mill operation and optimization | CementOps AI Platform |
| 6 | Finish Grinding | Cement mill operation and optimization | CementOps AI Platform |
| 7 | Quality Control | Chemistry, testing, and specifications | CementOps AI Platform |
| 8 | Coal Mill | Fuel preparation and explosion safety | CementOps AI Platform |
| 9 | Raw Materials Handling | Stockpile and feed systems | CementOps AI Platform |
| 10 | Quarry Operations | Drilling, blasting, crushing | CementOps AI Platform |
| 11 | Cement Storage & Shipping | Silos, packing, bulk loading | CementOps AI Platform |
| 12 | Maintenance Planning | PM/CM scheduling and execution | CementOps AI Platform |
| 13 | Spare Parts | Inventory and procurement | CementOps AI Platform |
| 14 | Plant Utilities | Compressed air, water, power | CementOps AI Platform |
| 15 | Reliability Engineering | RCA, FMEA, asset health | CementOps AI Platform |
| 16 | Process Optimization | Heat balance, throughput | CementOps AI Platform |
| 17 | Energy Optimization | SEC, energy audits, CCUS | CementOps AI Platform |
| 18 | Refractory | Lining design, installation, inspection | CementOps AI Platform |

Premium skills include deterministic parameter checking engines, equipment databases, failure mode libraries, and troubleshooting decision trees built from 18+ months of cement plant domain engineering.

---

## About CementOps AI

CementOps AI builds AI agents for cement plant operations. We deploy tailored AI in 3-week sprints — covering your entire plant from quarry to shipping — for plants that need to run safer and smarter without adding headcount.

**Want the full platform?** [Book a demo](https://cementops.ai) | **Contact:** jlarkin@cementops.ai

## License

MIT — use it, modify it, deploy it. The domain knowledge in the JSON files is the result of real plant experience. If it keeps one person safer, it was worth publishing.
