# EU AI Act Compliance Skill

A comprehensive skill for assessing AI systems in HR and recruitment contexts against EU AI Act requirements, with specific focus on Irish regulatory requirements.

## What This Skill Does

This skill helps HR professionals, compliance officers, and organisations:

- **Classify AI systems** according to EU AI Act risk categories
- **Assess compliance gaps** against regulatory requirements
- **Generate remediation plans** with prioritised actions
- **Document human oversight** requirements (Article 14)
- **Understand GDPR intersection** with AI in HR contexts
- **Navigate Irish-specific** regulatory requirements

## Features

### Risk Classification

Classifies AI systems as:
- **High-risk**: Recruitment AI, performance management, workforce planning (Annex III)
- **Medium-risk**: Advisory systems with human oversight
- **Minimal-risk**: Administrative systems with no decision impact

### Compliance Gap Analysis

Assesses requirements including:
- Risk management (Article 9)
- Data governance (Article 10)
- Technical documentation (Article 11)
- Record-keeping (Article 12)
- Transparency (Article 13)
- Human oversight (Article 14)
- Accuracy and robustness (Article 15)

### Reference Materials

Includes detailed reference files:
- **Article 14 Checklist**: Human oversight requirements
- **GDPR-AI Intersection**: Where data protection meets AI
- **Recruitment Risk Assessment**: Specific guidance for recruitment AI
- **Irish Employment Context**: Irish legislation and regulatory guidance

## Installation

### Via ClawHub

```bash
openclaw skill install eu-ai-act-compliance
```

### Manual Installation

1. Clone or download this skill to your OpenClaw workspace:
   ```bash
   cd ~/.openclaw/workspace/skills
   git clone https://github.com/enda-rochford/eu-ai-act-compliance.git
   ```

2. Restart OpenClaw or reload skills:
   ```bash
   openclaw reload
   ```

## Usage Examples

### Basic Risk Assessment

```
User: I'm implementing a CV screening tool. Is it high-risk under the EU AI Act?
```

The skill will:
1. Ask clarifying questions about the tool's functionality
2. Classify according to Annex III criteria
3. Explain the reasoning with article references
4. Identify compliance requirements

### Full Compliance Assessment

```
User: Assess my candidate ranking system for EU AI Act compliance
```

The skill will:
1. Gather information about the system
2. Determine risk classification
3. Generate a compliance gap report
4. Recommend prioritised remediation steps

### Documentation Support

```
User: Help me create human oversight documentation for my AI recruitment tool
```

The skill will:
1. Reference Article 14 requirements
2. Provide checklist items to complete
3. Guide documentation creation
4. Suggest evidence to retain

### GDPR Intersection

```
User: How does GDPR Article 22 apply to my AI performance assessment tool?
```

The skill will:
1. Explain Article 22 requirements
2. Assess if the tool makes automated decisions
3. Identify data subject rights
4. Recommend compliance measures

## Skill Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Main skill logic and classification process |
| `references/article-14-checklist.md` | Human oversight requirements checklist |
| `references/gdpr-ai-intersection.md` | GDPR and AI intersection guidance |
| `references/recruitment-risk-assessment.md` | Recruitment-specific risk assessment |
| `references/irish-employment-context.md` | Irish regulatory context |
| `skill.json` | Skill metadata |
| `README.md` | This file |

## Supported AI Use Cases

- **CV screening and parsing**
- **Candidate ranking and scoring**
- **Interview scheduling**
- **Video interview analysis**
- **Assessment and psychometric testing**
- **Reference checking automation**
- **Performance management systems**
- **Workforce planning tools**

## Regulatory Framework

This skill references:

- **EU AI Act**: Regulation (EU) 2024/1689
- **GDPR**: Regulation (EU) 2016/679
- **Irish Employment Equality Acts**: 1998-2021
- **SI 284/2016**: Public procurement regulations
- **Irish Data Protection Act**: 2018

## Important Dates

| Date | Milestone |
|------|-----------|
| 1 August 2025 | Prohibited practices enforcement begins |
| 2 February 2026 | High-risk system compliance deadline |
| 2 August 2027 | Full EU AI Act application |

## Disclaimer

This skill provides informational guidance only. It does not constitute legal advice. Organisations should consult with qualified legal professionals for compliance decisions specific to their circumstances.

## Author

**Enda Rochford**
- Email: randtrandbusiness@gmail.com
- LinkedIn: [Enda Rochford](https://www.linkedin.com/in/endarochford/)
- Website: [RandTrad Consulting](https://www.randtradconsulting.com/)

Enda is the founder of RandTrad Consulting, providing AI training and compliance services to organisations across Ireland. He specialises in:
- EU AI Act compliance for HR professionals
- GDPR and data protection
- HR systems implementation
- Training design and delivery

Enda has delivered AI training programmes for CMG Events and works with organisations across the SME, public, and recruitment sectors.

## License

**Free Version (Limited)**

The free version provides:
- Basic risk classification (high/medium/minimal)
- Limited compliance guidance

For full compliance gap analysis, remediation plans, and Irish regulatory context, purchase the Pro version on ClawHub.

**Pro Version (Commercial License)**

Purchased skills on ClawHub include:
- Full compliance gap analysis
- Remediation recommendations
- Irish regulatory context (SI 284/2016, DPC guidance)
- Reference documentation
- Priority support

**Pricing**

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | Basic classification |
| Pro | $25 | Full gap analysis + recommendations |
| Enterprise | $75 | Custom documentation + support |

## Get More

**This free skill provides basic EU AI Act classification.**

For full compliance tools and support:

| Offering | What You Get | Link |
|----------|--------------|------|
| **API Access** | Full compliance analysis via API | [RapidAPI](https://rapidapi.com/randtrad-randtrad-default/api/eu-ai-act-hr-compliance-api) |
| **Training** | EU AI Act courses for HR professionals | [RandTrad Consulting](https://www.randtradconsulting.com/) |
| **Consulting** | Custom compliance implementation | Email: randtrandbusiness@gmail.com |

---

## Support This Work

Find this skill useful? You can:

☕ [Buy me a coffee](https://buymeacoffee.com/endarochfov)

⭐ Star the skill on ClawHub

---

*This skill is part of the ClawHub skill repository for OpenClaw.*