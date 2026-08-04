---
name: patent-continuous-learning
description: Automatically extract reusable patterns from patent drafting sessions, including keyword strategies, writing techniques, and search methods, to build an accumulative patent knowledge base.
origin: professional-patent-agents
version: 1.0.0
---

# Patent Continuous Learning Skill

Automatically extract reusable patterns from patent drafting sessions to form a patent knowledge base.

## Trigger Conditions

- After patent drafting is complete (patent-auditor review passed)
- When search strategy is particularly effective
- When user corrects writing style
- When new writing techniques or patterns are discovered
- When user provides access to patent database APIs
- When new patent search skills are found on ClawHub

## Core Concept: Patent Instinct

A Patent Instinct is an atomic learning unit that records a specific patent-related experience:

```yaml
---
id: prefer-quantified-effect
trigger: "When writing technical effects"
confidence: 0.8
domain: "patent-writing"
source: "session-observation"
scope: global
---

# Prefer Quantified Technical Effects

## Trigger Condition
When writing the "Advantages Over Prior Art" section of a patent

## Action
Use quantified data to describe technical effects, such as:
- Efficiency improved by XX%
- Latency reduced by XXms
- Success rate improved by XX%

## Evidence
- 2026-03-19: User corrected "high efficiency" to "efficiency improved by 30%"
- 2026-03-18: Audit recommendation to add quantified data
```

## Patent Instinct Types

| Type | Description | Scope |
|------|-------------|-------|
| `keyword-strategy` | Effective search keyword combinations | project |
| `writing-pattern` | Writing techniques and sentence patterns | global |
| `tech-description` | Technical description patterns | project |
| `claim-structure` | Claim structure patterns | global |
| `search-tactic` | Search platform usage tips | global |
| `error-avoidance` | Common error avoidance | global |
| `api-recommendation` | Patent database API recommendations | global |
| `skill-discovery` | ClawHub skill discovery patterns | global |

## Confidence Evolution

| Score | Meaning | Behavior |
|-------|---------|----------|
| 0.3 | Tentative | Suggest but don't enforce |
| 0.5 | Medium | Apply when relevant |
| 0.7 | Strong | Auto-apply |
| 0.9 | Certain | Core behavior |

**Confidence Increase**:
- Pattern observed repeatedly
- User confirms effectiveness
- Audit passed

**Confidence Decrease**:
- User explicitly corrects
- Causes problems

## Learning Flow

```
Patent drafting session
      |
      | Observe key events
      v
+------------------------------------------+
|  observations/                           |
|   - Successful search strategies          |
|   - User correction records               |
|   - Audit feedback                        |
|   - Newly discovered patterns             |
+------------------------------------------+
      |
      | Extract instincts
      v
+------------------------------------------+
|  instincts/                              |
|   - keyword-strategy/  (project scope)    |
|   - writing-pattern/   (global scope)     |
|   - tech-description/  (project scope)    |
+------------------------------------------+
      |
      | /evolve clustering
      v
+------------------------------------------+
|  evolved/                                |
|   - skills/patent drafting enhanced skill |
|   - templates/reusable templates          |
+------------------------------------------+
```

## Commands

| Command | Description |
|---------|-------------|
| `/patent-learn` | Extract patent instincts from current session |
| `/patent-instincts` | Display learned patent instincts |
| `/patent-evolve` | Cluster related instincts into skills |

## Directory Structure

```
patent/
├── learning/
│   ├── observations.jsonl     # Observation records
│   ├── instincts/
│   │   ├── global/            # Global instincts
│   │   │   ├── prefer-quantified-effect.yaml
│   │   │   └── avoid-complete-code.yaml
│   │   └── projects/
│   │       └── project-name/  # Project scope
│   │           ├── keyword-strategy.yaml
│   │           └── tech-description.yaml
│   └── evolved/
│       ├── skills/
│       └── templates/
```

## Example: Auto-learned Instincts

### Patent Database API Recommendation

```yaml
---
id: recommend-patent-database-api
trigger: "When starting patent prior art search"
confidence: 0.9
domain: "api-recommendation"
scope: global
---

# Recommend Patent Database APIs for Professional Search

## Trigger Condition
When user requests patent prior art search and default channels may not be sufficient.

## Action
1. Ask user about available patent database APIs
2. Recommend appropriate APIs based on search needs:
   - Global search: Google Patents, Lens.org
   - US patents: USPTO, PatentsView
   - European patents: EPO Espacenet
   - Chinese patents: CNIPA
   - International: WIPO
3. Check ClawHub for patent search skills: `clawhub search patent`
4. Use installed skills if available

## Evidence
- 2026-03-19: User feedback that default channels are not accurate enough for patent search
- Patent prior art search requires professional patent database access
- ClawHub may have specialized patent search skills
```

### Search Keyword Strategy

```yaml
---
id: keyword-device-pairing
trigger: "When searching device pairing patents"
confidence: 0.85
domain: "keyword-strategy"
scope: project
project: example-project
---

# Device Pairing Search Keywords

## Keyword Combinations
- Primary keywords: device, terminal, pairing, connection
- Combination methods: `device pairing`, `terminal quick connection`
- Platform preference: Google Patents (English), AMiner (Academic)

## Evidence
- 2026-03-18: Found 5 highly relevant references using this combination
- Confidence increased from 0.5 to 0.85
```

### Writing Technique

```yaml
---
id: avoid-complete-code
trigger: "When writing patent embodiments"
confidence: 0.95
domain: "writing-pattern"
scope: global
---

# Avoid Complete Code

## Rule
Patent documents should not contain complete executable code. Use instead:
- Algorithm pseudocode
- Flowcharts
- Functional module descriptions

## Evidence
- 2026-03-17: Audit found complete code, recommended removal
- 2026-03-18: User confirmed this rule
- Verified across multiple patents
```

## Integration into Patent Workflow

Auto-trigger learning in all three scenarios:

### Scenario 1: User Idea → Drafting

```
After patent-auditor review passes
      |
      | Check for new patterns learned
      v
patent-continuous-learning extracts instincts
```

### Scenario 2: User Draft → Optimization

```
User correction or audit recommendation
      |
      | Record effective improvements
      v
patent-continuous-learning updates instincts
```

### Scenario 3: Agency Feedback

```
Targeted optimization successful
      |
      | Record effective differentiation descriptions
      v
patent-continuous-learning updates instincts
```
