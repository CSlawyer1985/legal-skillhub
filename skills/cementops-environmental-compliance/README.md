# CementOps Environmental Compliance Skill

**Part of the [CementOps Compliance Suite](https://cementops.ai) — Free on ClawHub**

Environmental regulatory compliance for cement plant operations — EPA NESHAP emission limits, CEMS monitoring and QA/QC, Title V permitting, alternative fuels emissions impact, and NOV response procedures.

Built from real cement plant environmental compliance programs.

## What It Does

| Capability | Description |
|-----------|-------------|
| **NESHAP Emissions** | Subpart LLL emission limits for PM, D/F, THC, HCl, mercury — with specific numeric values and averaging periods |
| **CEMS Management** | QA/QC procedures, calibration drift response, RATA requirements, data availability troubleshooting |
| **Title V Permitting** | Permit modification triggers, deviation reporting timelines, compliance monitoring |
| **Alternative Fuels** | Emissions impacts of TDF, RDF/SRF, waste oils — trial burn requirements, monitoring, permit considerations |
| **NOV Response** | Step-by-step enforcement response guide with timelines, documentation, corrective actions |
| **Emission Exceedance Response** | Immediate response procedures for PM, SO2, CO, and other emission exceedances |

## What's Included

```
cementops-environmental-compliance/
  SKILL.md                                    — Agent instructions (ClawHub manifest)
  README.md                                   — This file
  test-queries.json                           — 15-query evaluation suite
  knowledge-bases/
    cement-kiln-emissions.json                — NESHAP Subpart LLL emission limits and standards
    cems-requirements.json                    — CEMS QA/QC procedures and requirements
    title-v-permits.json                      — Title V permitting and deviation reporting
    alternative-fuels-emissions.json          — AF emissions impacts and monitoring
  guidance-templates/
    nov-response-guide.md                     — NOV response procedures and timelines
  troubleshooting/
    emission-exceedance.json                  — Exceedance response procedures
    cems-issues.json                          — CEMS troubleshooting guide
  safety/
    environmental-safety.json                 — Calibration gas, stack testing, and chemical hazards
```

## Quick Start

Install from ClawHub:

```bash
npx clawhub@latest install cementops-environmental-compliance
```

## Who This Is For

- **Environmental managers** — emission limits reference, CEMS QA/QC, permit compliance
- **Compliance officers** — deviation reporting, NOV response, inspection preparation
- **Plant managers** — understand environmental obligations and enforcement risk
- **CEMS technicians** — calibration procedures, data availability troubleshooting

## Limitations

- **This is regulatory guidance, not legal advice.** Always consult qualified legal counsel and your state environmental agency for formal enforcement proceedings.
- **Emission limits are based on federal NESHAP Subpart LLL.** State implementation plans may impose stricter limits — always verify against your specific Title V permit.
- **CEMS procedures reference 40 CFR Part 60/63/75.** Your plant's QA/QC plan may have additional site-specific requirements.
- **Designed for cement manufacturing (SIC 3241).** Covers Portland cement kiln operations. Does not cover ready-mix, concrete products, or non-kiln sources.

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

MIT
