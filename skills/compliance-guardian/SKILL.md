# Compliance Guardian — FinCEN Real Estate Reporting

Tool for real estate professionals to determine FinCEN reporting requirements and prepare Real Estate Reports.

## Description

The FinCEN Residential Real Estate Reporting Rule (effective March 1, 2026) requires reporting of non-financed residential property transfers to LLCs, trusts, and other entities. Compliance Guardian helps transaction coordinators and agents:

1. **Screen transactions** — Quickly determine if reporting is required
2. **Collect data** — User-friendly form for all required FinCEN fields
3. **Track deadlines** — Never miss a filing deadline

## Background

### Who Must Report?

The "reporting person" is typically the closing agent (title company, attorney, escrow officer). However, brokers and agents need to understand the requirements to:
- Advise clients properly
- Ensure compliance in their transactions
- Avoid E&O exposure

### What's Reportable?

A transaction requires a FinCEN Real Estate Report when ALL three conditions are met:
1. **Residential property** (1-4 units, or vacant land for residential development)
2. **Entity/Trust buyer** (LLC, corporation, partnership, or trust)
3. **Non-financed** (no regulated bank mortgage — includes cash, hard money, seller financing)

### Filing Deadline

The later of:
- 30 calendar days after closing, OR
- Last day of the month following the month of closing

## Features

### 1. Transaction Screener

Three-question wizard:
- Property type?
- Buyer type?
- Financing type?

Result: Clear YES/NO with explanation.

### 2. Form Pre-Filler

Collects all required FinCEN fields:
- **Reporting person** — Name, title, business, contact
- **Property** — Address, APN, closing date, consideration
- **Seller** — Name, address
- **Buyer entity** — Legal name, EIN, formation state
- **Beneficial owners** — Name, DOB, address, citizenship, TIN

### 3. Deadline Tracker

- Input closing date → calculates filing deadline
- Color-coded countdown (green > 14 days, yellow > 7 days, red ≤ 7 days)
- Persistent tracking of all pending filings

## Usage

### As Standalone Tool

1. Download `compliance-guardian.html`
2. Open in any web browser
3. No installation required

### Integrated with Mission Control

Add navigation button to your Mission Control dashboard:
```html
<button onclick="window.open('/compliance-guardian.html')">🛡️ FinCEN</button>
```

## Technical Details

- Single HTML file (~20KB)
- No external dependencies
- Mobile-responsive
- Print-friendly
- Data stored in localStorage (browser only)

## Files

```
compliance-guardian/
├── SKILL.md                  # This file
└── compliance-guardian.html  # Main tool
```

## References

- [FinCEN BSA E-File Portal](https://bsaefiling.fincen.treas.gov/)
- [First American FinCEN Resources](https://www.firstam.com/fincen/)
- Rule effective date: March 1, 2026

## Credits

Built by KW Sacramento Metro AI Team.
First compliance tool for the FinCEN Real Estate Reporting Rule.

## License

MIT
