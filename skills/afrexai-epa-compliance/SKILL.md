# Environmental Compliance Manager

Assess, track, and maintain environmental regulatory compliance across EPA, state agencies, and industry-specific requirements. Built for manufacturing, construction, energy, logistics, and any business with environmental obligations.

## What It Does

When given facility details, operations type, or specific environmental concerns, this skill:

1. **Regulatory Mapping** — Identifies which EPA programs apply (Clean Air Act, Clean Water Act, RCRA, CERCLA, EPCRA, TSCA) plus state-level requirements
2. **Permit Tracking** — Catalogs required permits (air emissions, stormwater NPDES, hazardous waste generator, SPCC plans) with renewal dates and compliance deadlines
3. **Inspection Readiness** — Generates pre-inspection checklists based on facility type, common citation areas, and recent enforcement trends
4. **Reporting Calendar** — Maps all mandatory reporting deadlines: TRI Form R, Tier II, DMRs, biennial hazardous waste reports, GHG reporting, air emissions inventories
5. **Violation Risk Assessment** — Scores current compliance posture against common violation categories with estimated penalty exposure
6. **Corrective Action Plans** — Generates remediation steps for identified gaps with priority ranking by penalty risk

## Regulatory Coverage

### Federal Programs
| Program | Statute | Key Requirements | Penalty Range |
|---------|---------|-----------------|---------------|
| Clean Air Act (CAA) | 42 USC §7401 | Title V permits, NESHAP, NSPS, PSD/NSR | $25,000-$75,000/day |
| Clean Water Act (CWA) | 33 USC §1251 | NPDES permits, stormwater, pretreatment | $25,000-$64,618/day |
| RCRA | 42 USC §6901 | Hazardous waste ID, storage, disposal, manifests | $37,500-$70,117/day |
| CERCLA (Superfund) | 42 USC §9601 | Reporting, cleanup liability, cost recovery | Strict liability, no cap |
| EPCRA | 42 USC §11001 | TRI reporting, Tier II, emergency planning | $25,000-$75,000/violation |
| TSCA | 15 USC §2601 | Chemical inventory, new chemical review, PFAS | $25,000-$50,000/day |

### State Programs
- Delegated authority states (most EPA programs)
- State-specific: California (CEQA, Prop 65, CARB), Texas (TCEQ), New York (DEC), Florida (DEP)
- Multi-state operations: identify overlapping requirements

## Facility Classification Matrix

### By Generator Status (RCRA)
| Category | Quantity | Requirements |
|----------|----------|-------------|
| Very Small (VSQG) | <220 lbs/month | Basic labeling, no time limit, no manifest |
| Small (SQG) | 220-2,200 lbs/month | 270-day storage, manifests, contingency plan |
| Large (LQG) | >2,200 lbs/month | 90-day storage, full contingency, biennial report |

### By Emissions Source (CAA)
| Category | Threshold | Requirements |
|----------|-----------|-------------|
| Minor Source | Below major thresholds | State permit, basic recordkeeping |
| Synthetic Minor | Accepted limits below major | Federally enforceable limits, monitoring |
| Major Source | >100 tpy any HAP, >10/25 HAP | Title V permit, MACT/NESHAP, annual compliance cert |

## Inspection Readiness Checklist

### Universal (All Facilities)
- [ ] Environmental policy posted and current
- [ ] Permits displayed/accessible (air, water, waste)
- [ ] Training records for environmental staff (within 12 months)
- [ ] Spill prevention plan current and reviewed annually
- [ ] Emergency contact list posted at all chemical storage areas
- [ ] Container labeling correct (contents, hazard, accumulation start date)
- [ ] Secondary containment intact, no cracks or standing liquid
- [ ] Storm drains labeled "No Dumping — Drains to [water body]"
- [ ] Waste manifests filed and accessible (3-year minimum, 5-year recommended)
- [ ] Air monitoring/emissions records current

### Hazardous Waste Specific
- [ ] EPA ID number current and posted
- [ ] Satellite accumulation areas compliant (<55 gal/1 quart acutely hazardous)
- [ ] Weekly inspections of storage areas documented
- [ ] Contingency plan updated within last year
- [ ] Land disposal restriction notifications on file
- [ ] Used oil storage clearly labeled, no mixing with hazardous waste

### Stormwater Specific
- [ ] SWPPP current and on-site
- [ ] Quarterly visual inspections documented
- [ ] Benchmark monitoring results within limits
- [ ] BMPs maintained (silt fences, drain covers, berms)
- [ ] No Exposure Certification current (if applicable)

## Reporting Calendar Template

| Report | Frequency | Deadline | Agency | Applies If |
|--------|-----------|----------|--------|-----------|
| TRI Form R | Annual | July 1 | EPA | >10 employees + threshold chemicals |
| Tier II | Annual | March 1 | SERC/LEPC | Any OSHA threshold chemical on-site |
| Biennial Hazardous Waste | Every 2 years | March 1 (even years) | EPA/State | LQG status |
| Title V Compliance Cert | Annual | Per permit | State | Major source |
| DMR (Discharge Monitoring) | Monthly/Quarterly | Per permit | EPA/State | NPDES permit holder |
| GHG Reporting | Annual | March 31 | EPA | >25,000 MT CO2e/year |
| Air Emissions Inventory | Annual/Biennial | Per state | State | Air permit holders |
| SPCC Plan Review | Every 5 years | Rolling | EPA | >1,320 gal aboveground or >42,000 gal underground oil |

## Violation Risk Scoring

Rate each area 1-5 (1=fully compliant, 5=critical gap):

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Permit currency | 20% | _ | _ |
| Waste management | 20% | _ | _ |
| Reporting timeliness | 15% | _ | _ |
| Recordkeeping | 15% | _ | _ |
| Training | 10% | _ | _ |
| Spill prevention | 10% | _ | _ |
| Air emissions | 10% | _ | _ |
| **Total** | **100%** | | **_/5.0** |

**Risk Tiers:**
- 1.0-2.0: Low risk — maintain current program
- 2.1-3.0: Moderate — address gaps within 90 days
- 3.1-4.0: High — immediate corrective action, consider voluntary disclosure
- 4.1-5.0: Critical — retain environmental counsel, self-audit before next inspection

## Penalty Mitigation Factors

EPA considers these when calculating fines:
1. **Good faith efforts** to comply (documented environmental management system)
2. **Voluntary disclosure** before inspection (can reduce penalty 75-100%)
3. **History of compliance** (no prior violations in 5 years)
4. **Ability to pay** (financial hardship documentation)
5. **Environmental justice** impact (proximity to disadvantaged communities increases scrutiny)
6. **Cooperation** during investigation
7. **Supplemental Environmental Projects** (SEPs) — can offset 50-80% of penalty

## Usage

Provide:
- Facility type and location (state matters for delegated programs)
- Operations description (manufacturing processes, chemicals used, waste generated)
- Current permits and their expiration dates
- Last inspection date and any outstanding violations
- Number of employees and annual revenue (for penalty context)

The skill maps your regulatory universe, scores your compliance posture, and generates a prioritized action plan with deadlines.

---

*Built by [AfrexAI](https://afrexai-cto.github.io/context-packs/) — AI agents that run your operations. Browse our full context pack library for industry-specific agent configurations starting at $47.*
