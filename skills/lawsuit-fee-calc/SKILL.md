---
name: lawsuit-fee-calc
description: Calculate lawsuit filing fees and litigation costs for civil cases in China. Use when the user asks about 诉讼费、诉讼费计算、起诉要多少钱、打官司费用、案件受理费、财产案件诉讼费、非财产案件诉讼费, or wants to estimate court fees and litigation costs before filing a lawsuit. This skill provides fee calculation assistance only and does not constitute legal advice.
---

# Lawsuit Fee Calculator

## Overview

This skill helps users calculate lawsuit filing fees and estimate litigation costs for civil cases in China. It covers both property disputes (财产案件) and non-property disputes (非财产案件), providing accurate calculations based on current Chinese court fee standards.

**⚠️ Important Disclaimer**: This tool provides fee calculation assistance only. Actual fees may vary by court and jurisdiction. Always verify current fee schedules with the specific court where you plan to file. This does not constitute legal advice.

## When to Use This Skill

- Estimating costs before filing a lawsuit
- Calculating case acceptance fees (案件受理费)
- Understanding fee structures for different case types
- Budgeting for litigation expenses
- Comparing costs of different claim amounts

## Limitations

- Based on general PRC court fee standards; specific courts may vary
- Does not include attorney fees or other legal service costs
- Does not cover all special case types
- Fee standards may change; verify with the specific court
- Not a substitute for professional legal consultation

## Fee Calculation Standards

### Property Disputes (财产案件)

Calculated based on claim amount using progressive rates:

| Claim Amount Range | Rate | Quick Calculation |
|-------------------|------|-------------------|
| ≤ ¥10,000 | 50元 fixed | ¥50 |
| ¥10,001 - ¥100,000 | 2.5% | Amount × 2.5% - ¥200 |
| ¥100,001 - ¥200,000 | 2% | Amount × 2% + ¥300 |
| ¥200,001 - ¥500,000 | 1.5% | Amount × 1.5% + ¥1,300 |
| ¥500,001 - ¥1,000,000 | 1% | Amount × 1% + ¥3,800 |
| ¥1,000,001 - ¥2,000,000 | 0.9% | Amount × 0.9% + ¥4,800 |
| ¥2,000,001 - ¥5,000,000 | 0.8% | Amount × 0.8% + ¥6,800 |
| ¥5,000,001 - ¥10,000,000 | 0.7% | Amount × 0.7% + ¥11,800 |
| ¥10,000,001 - ¥20,000,000 | 0.6% | Amount × 0.6% + ¥21,800 |
| > ¥20,000,000 | 0.5% | Amount × 0.5% + ¥41,800 |

### Non-Property Disputes (非财产案件)

| Case Type | Fee Standard |
|-----------|-------------|
| Divorce (离婚案件) | ¥50-¥300; if property > ¥200,000, excess at 0.5% |
| Personality rights (人格权) | ¥100-¥500; if damages > ¥50,000, excess at 1% |
| Other non-property | ¥50-¥100 |
| Intellectual property (no amount) | ¥500-¥1,000 |
| Labor disputes | ¥10 per case |
| Administrative cases | ¥50-¥100 |

### Other Common Fees

| Fee Type | Standard |
|----------|----------|
| Application fee (申请执行) | No fee for enforcement |
| Property preservation | ≤ ¥1,000: ¥30; > ¥1,000: 1% max ¥5,000 |
| Payment order (支付令) | 1/3 of case acceptance fee |
| Bankruptcy case | Based on estate value |

## Workflow

1. **Identify case type** — Property dispute or non-property dispute
2. **Gather claim information** — Claim amount, case specifics
3. **Calculate base fee** — Apply appropriate rate formula
4. **Add other fees** — Include preservation, application fees if applicable
5. **Present breakdown** — Show detailed fee calculation

## Usage

### Basic Calculation
```
"诉讼费计算"
"起诉10万块钱要多少诉讼费"
"离婚案件诉讼费多少"
```

### With Specific Amount
```
"50万标的诉讼费"
"财产保全费用计算"
"劳动仲裁诉讼费"
```

### Compare Scenarios
```
"100万和200万诉讼费差多少"
"不同金额诉讼费对比"
```

## Calculation Examples

### Example 1: Property Dispute ¥500,000
- Base: ¥500,000 × 1.5% + ¥1,300 = ¥8,800
- **Total: ¥8,800**

### Example 2: Property Dispute ¥1,000,000
- Base: ¥1,000,000 × 1% + ¥3,800 = ¥13,800
- **Total: ¥13,800**

### Example 3: Divorce Case (no property dispute)
- **Fee: ¥50-¥300** (varies by court)

### Example 4: Divorce with ¥1,000,000 property
- Base: ¥300
- Property excess: (¥1,000,000 - ¥200,000) × 0.5% = ¥4,000
- **Total: ¥4,300**

## Output Format

For each calculation:
- **Case type** identified
- **Claim amount** (if applicable)
- **Fee breakdown** showing calculation steps
- **Total estimated fee**
- **Notes** on potential variations

## Additional Cost Considerations

Beyond court fees, litigation may involve:
- Attorney fees (律师费) - varies widely
- Evidence collection costs
- Expert witness fees
- Travel expenses
- Notarization/certification fees
- Translation fees (if applicable)

## References

For detailed fee schedules and legal basis:
- [references/fee-standards.md](references/fee-standards.md) — Complete fee calculation tables
- [references/legal-basis.md](references/legal-basis.md) — Legal basis for fee standards

## Important Reminders

- **Fee Waivers**: Low-income litigants may apply for fee reduction or waiver
- **Refund Policy**: If case settles before judgment, portion of fees may be refunded
- **Payment Timing**: Fees typically due when filing; preservation fees when applying
- **Jurisdiction Variations**: Local courts may have slight variations

## Privacy Note

Case information is processed for fee calculation only. No data is stored or transmitted to third parties.
