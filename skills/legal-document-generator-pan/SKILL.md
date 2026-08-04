---
name: legal-document-generator
description: "Generate professional Chinese legal documents including contracts, petitions, defense statements, and legal opinions. Use when creating: (1) Civil/commercial contracts and agreements, (2) Civil litigation documents (petitions, defenses), (3) Criminal defense documents, (4) Legal opinion letters, (5) Administrative documents, (6) Legal notice and warning letters"
---

# Legal Document Generator

This skill enables generation of professional Chinese legal documents with proper format, structure, and legal terminology.

## Core Capabilities

### 1. Contract Generation
Generate various types of contracts including:
- Sales contracts (销售合同)
- Service agreements (服务协议)
- Lease agreements (租赁合同)
- Loan agreements (借款合同)
- Employment contracts (劳动合同)
- Partnership agreements (合伙协议)
- Non-disclosure agreements (保密协议)

**Structure requirements:**
- Header: Document title, contract number, date
- Parties: Names, addresses, identification details
- Contract body: Articles 1, 2, 3... with clear terms
- Signature block: Both parties' signatures and seals
- Witness section (if applicable)

### 2. Civil Litigation Documents
Generate:
- Civil complaints (民事起诉状)
- Civil defenses (民事答辩状)
- Counterclaims (反诉状)
- Applications for preservation (财产保全申请书)
- Evidence lists (证据清单)

**Format standards:**
- Standard A4 paper format
- Proper font: Songti (宋体) for body, SimHei (黑体) for titles
- Font sizes: Title 22pt, first-level headings 18pt, body 12pt
- Line spacing: 1.5x
- Margins: Top 3cm, bottom 2.5cm, left 3cm, right 2.5cm

**Essential elements:**
- Plaintiff/Defendant information
- Court jurisdiction
- Claims and facts
- Legal basis with specific article citations
- Signature and date

### 3. Criminal Defense Documents
Generate:
- Defense opinions (辩护意见书)
- Criminal defense statements (刑事辩护词)
- Bail applications (取保候审申请书)
- Leniency applications (从轻处罚申请书)

**Key points:**
- Focus on factual innocence or mitigating circumstances
- Cite specific Criminal Law articles (刑法条款)
- Reference Procedural Law provisions (刑事诉讼法)
- Include personal circumstances and remorse indicators

### 4. Legal Opinions
Generate:
- Formal legal opinion letters (法律意见书)
- Due diligence reports (尽职调查报告)
- Compliance opinions (合规意见)
- Risk assessments (风险评估)

**Structure:**
- Executive summary
- Factual background
- Legal analysis
- Risk assessment
- Recommendations

### 5. Administrative Documents
Generate:
- Petitions for administrative reconsideration (行政复议申请书)
- Administrative litigation documents (行政诉讼文书)
- Government response letters (政府回复函)

### 6. Legal Notices
Generate:
- Lawyer's letters (律师函)
- Demand letters (催款函)
- Warning notices (警告函)
- Cease and desist letters (停止侵权函)

## Document Generation Workflow

1. **Understand requirements**
   - Identify document type
   - Gather all necessary facts and parties
   - Determine legal basis

2. **Structure the document**
   - Follow standard format for document type
   - Use proper section numbering
   - Include all required elements

3. **Draft content**
   - Use precise legal terminology
   - Reference specific laws and articles
   - Maintain professional, formal tone

4. **Review and validate**
   - Check completeness of required elements
   - Verify legal citations
   - Ensure proper formatting

## References

### Chinese Legal Code References
Use `references/legal_codes.md` for:
- Civil Code articles (民法典)
- Criminal Law provisions (刑法)
- Procedural Law references (诉讼法)
- Administrative Law rules (行政法)

### Document Templates
Use `references/templates/` for:
- Standard contract formats
- Litigation document samples
- Opinion letter templates

### Resources

### scripts/
Python scripts for:
- Document formatting validation
- Legal citation verification
- Template population from data

### references/
- `legal_codes.md`: Key legal provisions by category
- `templates/`: Document template samples
- `terminology.md`: Legal terminology glossary

### assets/
- `templates/`: Document template files (.docx)
- `examples/`: Sample completed documents
