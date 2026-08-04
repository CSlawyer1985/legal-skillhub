# Belgian GAAP Compliance Suite

Complete Belgian accounting compliance toolkit for AI assistants. 8 interconnected skills covering the full Belgian GAAP lifecycle from chart of accounts to annual filing.

## What's Included

| Skill | Domain |
|-------|--------|
| belgian-gaap-pcmn | Standardized chart of accounts (PCMN) |
| belgian-gaap-vat | VAT settlement cycles and accounting entries |
| belgian-gaap-deductibility | Professional use vs fiscal deductibility |
| belgian-gaap-dna | Non-deductible expenses (DNA) |
| belgian-gaap-fines | Administrative fines and tax surcharges |
| belgian-gaap-closing | Year-end closing procedures |
| belgian-gaap-intervat | Intervat VAT return filing |
| belgian-gaap-annual-accounts | Annual accounts from ledger entries |

## Why This Bundle

- **Extremely niche**: zero competition on ClawHub for Belgian-specific accounting
- **Practice-tested**: built from real Belgian accounting workflows, not textbook summaries
- **Interconnected**: skills reference each other (e.g., a restaurant dinner touches deductibility + DNA + VAT)
- **Trilingual**: supports Dutch (nl), French (fr), and English (en) terminology

## Example Scenarios

### Record a business dinner
```
Record a business dinner at a restaurant for EUR 242 (incl. 21% VAT) with 3 clients.
```
Tests: deductibility (69%), DNA (31%), VAT recovery on deductible portion.

### Prepare quarterly VAT return
```
Prepare the Q4 2025 VAT return. Sales: EUR 150,000 (21%). Purchases: EUR 80,000 (21%).
```
Tests: Box 03/54/59 computation, Box 71/72 balance, Intervat XML structure.

### Year-end closing
```
Run year-end closing for FY 2025. Doubtful receivables: EUR 12,000.
```
Tests: provision entries, P&L transfer, balance sheet reconciliation.

## Installation

```bash
clawhub install belgian-gaap-compliance-suite
```

## License

Commercial — see bundle.yaml for pricing.
