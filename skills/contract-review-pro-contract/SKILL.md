---
name: "contract-review-pro"
description: "Chinese contract risk intelligence — scan, annotate, and explain clauses in labor, rental, service, NDA, and 15+ other contract types under PRC law."
---

# Contract Review Pro

Intelligent Chinese contract risk review. Upload any contract (PDF, DOCX, scanned image, or paste text) and get a structured risk assessment within minutes. Contract Review Pro recognizes **15+ contract types**, applies **20+ rule sets based on PRC law**, and provides clear explanations with actionable modification suggestions.

## Why Contract Review Pro?

- **Know before you sign**: Spot unfair clauses, hidden risks, and legal violations before they cost you.
- **Chinese law expertise**: Built-in knowledge of PRC labor law, civil code, property law, consumer protection law, and more.
- **Negotiation-ready**: Each risk comes with a suggested counter-term and "must-fight vs nice-to-fix" priority.
- **No legal degree needed**: Every technical clause is explained in plain Chinese and English.

## Workflow (8 Steps)

```
Input: Contract file (PDF/DOCX/image) or pasted text
↓
[1] Extract text (OCR supported for scanned documents)
[2] Identify contract type: 劳动合同 / 租房合同 / 购销合同 / 服务协议 / NDA / 借款合同 / 担保合同 / 合伙协议 / 投资协议 / 采购合同 / 工程合同 / 运输合同 / 仓储合同 / 物业合同 / 保险合同 / 赠与合同 / 技术合同
[3] Load relevant rule set(s) for that contract type (apply 20+ PRC legal rule sets)
[4] Scan clauses line-by-line with risk detection patterns:
    → 🔴 High: Unenforceable, illegal, or severely one-sided terms
    → 🟡 Medium: Ambiguous, unbalanced, or risky terms
    → 🟢 Low: Standard terms with minor clarification needs
    → ⚪ Info: Explanatory or non-risky clauses
[5] For each risk: original text excerpt → plain language explanation → standard clause comparison → modification suggestion → negotiation priority
[6] Generate contract summary: parties, amount, term, key dates, special conditions
[7] Optional: side-by-side comparison with standard template for this contract type
[8] Output structured review report (Markdown or PDF)
↓
Output: Annotated contract + risk report (risk inventory + suggestions + negotiation talking points)
```

## Built-in Rule Sets (20+)

### Labor & Employment
| # | Rule Set | Laws Applied | Red Flags |
|---|----------|-------------|-----------|
| 1 | 劳动合同 (Labor Contract) | 劳动合同法 | Non-compete without compensation, probation >6mo, "at-will termination" |
| 2 | 竞业限制 (Non-Compete) | 劳动合同法 §23-24 | No compensation clause, >2yr period, unlimited scope |
| 3 | 保密协议 (NDA) | 反不正当竞争法 | Perpetual confidentiality, no exception for public info, unlimited liability |

### Real Estate & Property
| # | Rule Set | Laws Applied | Red Flags |
|---|----------|-------------|-----------|
| 4 | 房屋租赁合同 (Residential Lease) | 民法典 §703-734 | Landlord unilateral termination, deposit forfeiture conditions, repair liability |
| 5 | 商业租赁合同 (Commercial Lease) | 民法典, 城市房地产管理法 | Rent escalation >5%/yr, business license restrictions |
| 6 | 买卖合同 (Property Sale) | 民法典 §595-647 | Delivery delay penalties, quality defects disclaimer |

### Business & Commerce
| # | Rule Set | Laws Applied | Red Flags |
|---|----------|-------------|-----------|
| 7 | 购销合同 (Sales/Purchase) | 民法典 §595-647 | Inspection period too short, force majeure defined too narrowly |
| 8 | 服务协议 (Service Agreement) | 民法典 §919-940 | Service standard vague, termination notice unreasonable |
| 9 | 采购合同 (Procurement) | 民法典, 招标投标法 | Unilateral price adjustment, delivery acceptance conditions |
| 10 | 运输合同 (Transport) | 民法典 §809-842 | Carrier liability caps below mandatory minimum |
| 11 | 仓储合同 (Storage/Warehouse) | 民法典 §904-918 | Storage period ambiguity, damage liability exclusion |

### Finance & Investment
| # | Rule Set | Laws Applied | Red Flags |
|---|----------|-------------|-----------|
| 12 | 借款合同 (Loan Agreement) | 民法典 §667-680, 民间借贷司法解释 | Interest >4× LPR, hidden fees, prepayment penalty |
| 13 | 担保合同 (Guarantee) | 民法典 §681-702, 担保法 | Unlimited guarantee period, no expiry |
| 14 | 投资协议 (Investment) | 公司法, 证券法 | Repurchase obligation without cap, drag-along without tag-along |

### Technology & IP
| # | Rule Set | Laws Applied | Red Flags |
|---|----------|-------------|-----------|
| 15 | 技术合同 (Technology Contract) | 民法典 §843-887 | IP ownership ambiguity, non-compete linked to unrelated tech |
| 16 | 软件开发合同 (Software Dev) | 民法典, 计算机软件保护条例 | Acceptance criteria subjective, source code escrow missing |
| 17 | 数据协议 (Data Processing) | 个人信息保护法, 数据安全法 | Data use beyond consent, cross-border transfer without assessment |

### Construction & Engineering
| # | Rule Set | Laws Applied | Red Flags |
|---|----------|-------------|-----------|
| 18 | 建设工程合同 (Construction) | 民法典 §788-808, 建筑法 | Payment milestones unclear, change order process missing |
| 19 | 监理合同 (Supervision) | 建设工程质量管理条例 | Supervision scope too broad, indemnification without fault |

### Other
| # | Rule Set | Laws Applied | Red Flags |
|---|----------|-------------|-----------|
| 20 | 保险合同 (Insurance) | 保险法 | Exclusion clauses not in bold, waiting period >30d |
| 21 | 合伙协议 (Partnership) | 合伙企业法 | Profit-sharing ambiguous, withdrawal conditions unclear |
| 22 | 赠与合同 (Gift/Donation) | 民法典 §657-666 | Revocation conditions omitted |
| 23 | 物业合同 (Property Management) | 民法典 §937-950, 物业管理条例 | Service fee escalation formula missing |

## Sample Prompts

### Sample 1: Rental contract review
> "I'm about to sign a Beijing apartment lease. Please review and flag any unfair clauses — especially about deposit return, early termination, and repair responsibilities."

### Sample 2: Employment contract check
> "My new company gave me an employment contract with a non-compete clause. Check if it's valid under Chinese labor law."

### Sample 3: NDA review
> "Review this NDA. I'm the receiving party. Flag any clauses that are too broad on confidentiality or liability."

### Sample 4: Service agreement
> "I'm a freelancer signing a service agreement with a tech company. The termination clause says they can cancel any time with 7 days notice. Is that fair?"

### Sample 5: Loan agreement
> "Check this personal loan agreement between friends. The interest rate seems high. What's the legal max under PRC law?"

## First-Success Path

```
1. Paste a contract or describe it (if text not available yet)
2. The skill identifies the contract type (e.g., "房屋租赁合同")
3. It loads the matching rule set (民法典 §703-734 + related)
4. Each clause is scanned against 20+ rule sets
5. Output shows risk level (🔴/🟡/🟢/⚪) with plain-language explanation
6. Review the "must-fix" items before signing
```

## Output Example

```markdown
# Contract Review Report

**Type**: 房屋租赁合同 (Residential Lease)
**Reviewed**: 2026-06-14

## 🔴 High Risk (3 items)

### 🔴 1. 第12条：损坏赔偿 (Damage Compensation)
**原文**: "房屋内物品损坏，租客需按原价3倍赔偿"
**风险说明**: 3倍赔偿远超《民法典》规定的实际损失赔偿原则，属于惩罚性条款，可能被认定为无效。
**标准条款**: "租客因过失造成物品损坏的，应按实际损失或合理维修费用赔偿"
**修改建议**: 删除"3倍"赔偿，改为"按实际损失或维修费用赔偿"
**谈判优先级**: 🔴 必须修改 — 这是显失公平条款

### 🔴 2. 第8条：单方解约 (Unilateral Termination)
**原文**: "出租方可提前30天通知解约，无需说明理由"
**风险说明**: 根据《民法典》第726条，承租人享有优先承租权。出租人无正当理由随意解约不符合法律精神。
**标准条款**: "出租方需在合理期限内通知，并说明正当理由"
**修改建议**: 修改为"双方协商一致可解约，或出租方在提前60天通知并支付X个月租金作为违约金"
**谈判优先级**: 🔴 必须修改

## 🟡 Medium Risk (2 items)

### 🟡 3. 第5条：水电费分摊 (Utility Allocation)
**原文**: "水电费按人头分摊"
**风险说明**: 表述模糊，按"人头"含义不明确（常住人口？所有登记人？访客？）
**建议**: 改为"水电费按实际使用度数计算，由租客承担"或明确分摊规则
```

## Tags

`contract-review-pro`, `contract-review`, `chinese-law`, `legal`, `risk-assessment`, `labor-law`, `rental`, `nda`, `compliance`, `prc-law`, `due-diligence`
