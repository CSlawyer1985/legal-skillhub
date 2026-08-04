# Export Compliance & Trade Controls

Analyze products, destinations, and end-users against US export control regulations (EAR, ITAR, OFAC sanctions). Generate classification recommendations, license requirements, and compliance checklists.

## What It Does

When given a product description, destination country, and end-user details:

1. **ECCN Classification** — Map product characteristics to likely Export Control Classification Numbers (Commerce Control List)
2. **Sanctions Screening** — Check destination country and end-user against OFAC SDN list indicators, Entity List red flags, and denied parties patterns
3. **License Determination** — Identify whether a license exception applies (e.g., TMP, TSR, ENC) or if a formal BIS license is needed
4. **Red Flag Checklist** — Walk through the BIS "Know Your Customer" red flags for the transaction
5. **Documentation Pack** — Generate: Shipper's Letter of Instruction template, End-Use Certificate template, Internal compliance memo

## How to Use

Provide the agent with:
- **Product**: What you're exporting (software, hardware, technical data, services)
- **Destination**: Country and specific entity/address
- **End-user**: Company name, industry, known affiliations
- **Value**: Transaction value (for de minimis calculations)

Example prompt:
```
Run export compliance check:
Product: Cloud-based encryption software (AES-256, key management)
Destination: United Arab Emirates
End-user: Dubai National Bank
Value: $180,000/year
```

## Classification Framework

### EAR Categories (Commerce Control List)
| Category | Description | Common Items |
|----------|-------------|--------------|
| 0 | Nuclear & Misc | Nuclear equipment, materials |
| 1 | Materials | Chemicals, alloys, composites |
| 2 | Materials Processing | Machine tools, robots |
| 3 | Electronics | ICs, sensors, lasers |
| 4 | Computers | Hardware, software, crypto |
| 5 | Telecom & Infosec | Encryption, network gear |
| 6 | Sensors & Lasers | Cameras, radar, sonar |
| 7 | Navigation | GPS, INS, accelerometers |
| 8 | Marine | Vessels, submersibles |
| 9 | Aerospace | Aircraft, engines, UAVs |

### Control Reasons
- NS (National Security), MT (Missile Technology), NP (Nuclear Nonproliferation)
- CB (Chemical/Biological), CC (Crime Control), RS (Regional Stability)
- AT (Anti-Terrorism), SS (Short Supply), UN (UN Sanctions)

### License Exception Quick Reference
| Exception | Use Case |
|-----------|----------|
| ENC | Mass-market encryption products |
| TMP | Temporary exports/reexports |
| TSR | Technology/software under restriction |
| GOV | US government agencies abroad |
| BAG | Personal baggage |
| RPL | Replacement parts (one-for-one) |
| CIV | Civil end-users (Country Group B) |

## OFAC Sanctions Programs (Active)
- **Comprehensive**: Cuba, Iran, North Korea, Syria, Crimea/DNR/LNR
- **Targeted**: Russia, Belarus, Myanmar, Venezuela, Nicaragua, China (military), Ethiopia, Mali, others
- **SDN List**: 12,000+ designated persons/entities — screen every transaction

## Red Flags (BIS "Know Your Customer" Guidance)
1. Customer reluctant to provide end-use/end-user info
2. Product inconsistent with buyer's line of business
3. Unusual shipping routes or intermediary countries
4. Customer willing to pay cash for expensive items
5. Delivery to freight forwarder rather than end-user
6. Evasive answers about whether item is for domestic use or export
7. Order for items incompatible with technical level of destination country
8. Customer has P.O. Box or residential address for commercial goods
9. Abnormal packaging or marking requests
10. Customer declines normal installation/training/maintenance

## De Minimis Rule
US-origin controlled content below these thresholds may not require a license:
- **25%** for most countries
- **10%** for Country Group E:1 (terrorism-supporting) and E:2
- Calculate: (value of US-origin controlled content / total value) × 100

## Output Format
```
═══ EXPORT COMPLIANCE ASSESSMENT ═══

PRODUCT CLASSIFICATION
  Likely ECCN: [number]
  Category: [description]
  Control Reasons: [NS/MT/etc.]

DESTINATION ANALYSIS
  Country: [name]
  Country Group: [A:1, B, D:1, etc.]
  Sanctions Programs: [if any]
  Embargo Status: [comprehensive/targeted/none]

END-USER SCREENING
  Entity List: [clear/match/possible match]
  SDN List: [clear/match/possible match]
  Red Flags Triggered: [list any]

LICENSE DETERMINATION
  License Required: [yes/no/likely]
  Applicable Exceptions: [if any]
  Recommended Action: [proceed/investigate/halt]

DOCUMENTATION NEEDED
  □ Shipper's Letter of Instruction
  □ End-Use Certificate
  □ Compliance Memo
  □ [additional as needed]
═══════════════════════════════════
```

## Industries That Need This
- Software companies selling internationally (especially encryption, AI/ML, cybersecurity)
- Hardware manufacturers with dual-use components
- Defense contractors and subcontractors
- Universities with international research collaborations
- Logistics and freight forwarding companies
- Any company doing business with sanctioned countries

## Regulatory References
- Export Administration Regulations (EAR): 15 CFR Parts 730-774
- International Traffic in Arms Regulations (ITAR): 22 CFR Parts 120-130
- OFAC Sanctions: 31 CFR Part 500
- Commerce Control List: Supplement No. 1 to Part 774
- Country Chart: Supplement No. 1 to Part 738
- Entity List: Supplement No. 4 to Part 744

---

*Built by [AfrexAI](https://afrexai-cto.github.io/context-packs/) — AI context packs for business operations.*
