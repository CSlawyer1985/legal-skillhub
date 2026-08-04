# Contract Review & Revise Skill

**Contract Review & Revise Skill** - Professional legal document review and modification system with Legal Document Review Agent

## 🎯 Overview

A **professional-grade** contract review and revision system integrated with Legal Document Review Agent:
1. **Smart Review** - AI quickly identifies risky clauses
2. **Professional Review** - Legal Document Review Agent provides in-depth legal analysis (lawyer-level)
3. **Comprehensive Report** - Combines both review results for complete recommendations
4. **Client Confirmation** - Supports selective acceptance of modifications
5. **Auto-Modification** - Uses `python-docx` to modify Word files
6. **Comparison List** - Generates detailed modification comparison documents

## 📁 Skill Structure

```
skills/contract-review-revise/
├── SKILL.md                 # Skill documentation
└── agents/
    └── legal-document-review.md  # Legal Document Review Agent
```

## 📋 Usage Workflow

### Step 1: Upload Contract File
- **Supported Format**: `.docx` (Word documents)
- Specify file path
- Specify review perspective (Party A/Party B/Neutral)
- Specify review mode:
  - **Quick Review** - AI-only review (suitable for simple contracts)
  - **Professional Review** - AI + Legal Document Review Agent (recommended for important contracts)

### Step 2: Initiate Review

#### Mode A: Quick Review (AI Review)
AI automatically:
- Reads the full contract
- Identifies key clauses (compensation, exemption, pricing, breach of contract, etc.)
- Analyzes legal risks
- Classifies by risk level

#### Mode B: Professional Review (AI + Legal Document Review Agent) ⭐ Recommended
1. **AI Preliminary Review** - Quickly identifies obvious issues
2. **Launch Legal Document Review Agent**
   - Review perspective: Party A/Party B/Neutral
   - Focus areas: Compensation clauses, deductible rates, price adjustments, late fees, goods disposal rights, dispute jurisdiction, etc.
   - Output format: Risk level + Clause location + Issue description + Modification suggestion + Legal basis
3. **Combine Reports** - Synthesize AI and Legal Agent recommendations

### Step 3: Generate Review Report

Output format:
```
=== Contract Review Report ===

🔴 HIGH RISK CLAUSES (Must Modify)
| Clause | Issue | Risk Level | AI Suggestion | Legal Agent Suggestion | Combined Recommendation |
|---|---|---|---|---|---|
| 5.1.1 | Compensation cap $100 | 🔴 High | Remove cap | Remove cap | ✅ Remove cap, compensate based on actual loss |

🟡 MEDIUM RISK CLAUSES (Recommended to Modify)
| Clause | Issue | Risk Level | AI Suggestion | Legal Agent Suggestion | Combined Recommendation |
|---|---|---|---|---|---|
| 13.4 | Jurisdiction: Defendant's location | 🟡 Medium | Plaintiff's location | Arbitration | ✅ Plaintiff's location or arbitration |

🟢 MISSING PROTECTIVE CLAUSES (Strongly Recommended to Add)
| Clause | Suggested Content | Reason | Source |
|---|---|---|---|
| New Clause 14 | Party B's Qualification and Compliance Responsibility | Prevent losses due to Party B's qualification issues | Legal Agent |
```

### Step 4: Client Confirmation
Client can:
- **Accept All** - Modify all clauses directly
- **Accept Partially** - Selectively accept certain modifications
- **Reject Some** - Keep original clauses
- **Request New Changes** - Add additional modification requirements
- **View Detailed Reasons** - Understand legal basis for each modification

### Step 5: Auto-Modify Contract
AI will modify the contract based on client confirmation:
- Use `python-docx` library to modify Word files
- Maintain original formatting and layout
- Save as new version (e.g., `_revised.docx`)
- Generate modification comparison list

## 🔧 Technical Implementation

### Dependencies
```python
from docx import Document
import os
```

### Legal Document Review Agent Integration
- **Agent File**: `agents/legal-document-review.md`
- **Launch Method**: Use `sessions_spawn` to launch sub-Agent
- **Review Focus**:
  - Reasonableness of compensation clauses
  - Excessive deductible rates
  - Fairness of price adjustment rights
  - Late fees and punitive clauses
  - Reasonableness of goods disposal rights
  - Favorability of dispute jurisdiction to client
  - Missing protective clauses
- **Output Format**:
  - Risk level (High/Medium/Low)
  - Clause location
  - Issue description
  - Modification suggestions
  - Legal basis (if applicable)

### Core Functions
1. **Contract Reading** - Use `python-docx` to read Word files
2. **Clause Identification** - Identify key clauses via keyword matching
3. **AI Risk Analysis** - Assess risk levels based on legal knowledge and experience
4. **Legal Agent Invocation** - Launch `legal-document-review` Agent for professional review
5. **Report Fusion** - Synthesize AI and Legal Agent recommendations
6. **Modification Suggestions** - Provide specific modification text
7. **File Modification** - Use `python-docx` to modify and save files
8. **Comparison Generation** - Generate Markdown-format modification comparison lists

### Supported Contract Types
- Service contracts ( warehousing, logistics, technology, consulting, etc.)
- Procurement contracts
- Sales contracts
- Lease agreements
- Cooperation agreements
- Employment contracts
- Other commercial contracts

## 📝 Usage Examples

### Example 1: Review Warehousing Contract (Professional Review Mode)
```
Please professionally review D:\Contracts\Warehousing_Agreement.docx from Party A's perspective
```

**AI will automatically:**
1. Read the contract file
2. Launch Legal Document Review Agent for in-depth review
3. Generate comprehensive review report
4. Wait for client confirmation

### Example 2: Review Technology Cooperation Agreement (Quick Review Mode)
```
Please quickly review E:\Projects\Technology_Cooperation.docx from Party B's perspective
```

### Example 3: Review Important Contract (Professional Review + Deep Analysis)
```
Please professionally review E:\Projects\Important_Agreement.docx from Party A's perspective, focusing on compensation clauses and breach of contract responsibilities
```

## ⚠️ Important Notes

1. **Legal Disclaimer**
   - Review suggestions provided by this skill are for reference only
   - Does not constitute formal legal advice
   - Important contracts should be reviewed by a qualified attorney
   - Legal Document Review Agent suggestions do not replace professional legal counsel

2. **File Safety**
   - Original file will be backed up before modification
   - New version will be generated without overwriting the original
   - Client should confirm modifications independently

3. **Format Preservation**
   - Original formatting and layout will be maintained as much as possible
   - Some complex formatting may be affected
   - Manual review recommended after modification

4. **Language Support**
   - Primary support: Chinese contracts
   - Also supports: English contracts
   - Other languages: Can be reviewed but recommendations may be less specific

5. **Legal Agent Limitations**
   - Legal Document Review Agent can only analyze text, cannot directly modify Word files
   - AI assistant must perform file modifications based on Agent's suggestions
   - Agent review takes some time (typically 1-2 minutes)

## 🚀 Future Extensions

Future enhancements may include:
- Support for PDF contracts (requires OCR or parsing)
- Multi-language contract review
- Integration with legal databases (citing specific legal provisions)
- Batch review of multiple contracts
- Generation of negotiation scripts and supplementary agreements
- History tracking and version comparison
- Multi-model Legal Agent comparison (multiple legal Agents reviewing simultaneously)

## 📚 Legal Basis

Review references major laws and regulations:
- Civil Code of the People's Republic of China
- Contract Law of the People's Republic of China
- Consumer Rights Protection Law of the People's Republic of China
- Company Law of the People's Republic of China
- Industry-specific regulations

## 💡 Best Practices

### 1. Before Review
- Clearly specify review perspective (Party A/Party B/Neutral)
- Provide contract background and business objectives
- Specify special focus areas
- Choose "Professional Review" mode for important contracts

### 2. During Review
- Focus on core clauses: compensation, exemption, pricing, breach of contract responsibilities
- Identify unreasonable content in standard clauses
- Check for missing protective clauses
- Review Legal Agent's detailed analysis

### 3. After Review
- Communic modification recommendations thoroughly with client
- Explain modification reasons and legal basis
- Generate clear modification comparison lists
- Compare AI and Legal Agent recommendation differences

### 4. After Modification
- Manually check modification content
- Confirm formatting and layout correctness
- Save multiple versions for easy comparison
- Retain review report as reference

## 🎯 Review Checklist

### Compensation Clauses
- [ ] Is compensation cap reasonable?
- [ ] Is deductible rate too high?
- [ ] Is compensation calculation method clear?
- [ ] Is payment method clear (cash/system credit)?

### Pricing Clauses
- [ ] Is price adjustment right fair?
- [ ] Is price adjustment notice period reasonable?
- [ ] Is there a price protection mechanism?

### Breach of Contract Responsibilities
- [ ] Is penalty too high?
- [ ] Is late fee rate reasonable?
- [ ] Are punitive clauses reasonable?
- [ ] Are breach termination conditions clear?

### Goods/Service Disposal
- [ ] Is prior notice required for disposal?
- [ ] Is notice period reasonable?
- [ ] Is disposal proceeds ownership clear?

### Dispute Resolution
- [ ] Is jurisdiction/arbitration institution fair?
- [ ] Is governing law clear?
- [ ] Is dispute resolution cost reasonable?

### Protective Clauses
- [ ] Qualification and compliance responsibility
- [ ] Subcontracting restrictions
- [ ] Inspection rights and inventory management
- [ ] Post-termination handling
- [ ] Service Level Agreement (SLA)

---

**Version**: 1.0.0  
**Author**: 虾米 🦐  
**Last Updated**: 2026-04-28  
**Integrated**: Legal Document Review Agent (Professional Legal Review)
