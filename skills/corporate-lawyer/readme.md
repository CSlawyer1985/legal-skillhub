# Corporate Lawyer - AI-Powered Business Affairs Legal Assistant
# 公司律师 - AI 驱动的商业事务法律助手

> Your AI legal advisor for commercial transactions, contract review, and business compliance
>
> 您的商业交易、合同审查和业务合规的 AI 法律顾问

**Version / 版本:** 0.1.0 | **Status / 状态:** Production Ready / 生产就绪 | **License / 许可证:** MIT

---

## 🌍 English Version

### What is Corporate Lawyer?

Corporate Lawyer is an AI-powered legal advisory system designed to help **businesses, legal departments, and law firms** navigate complex commercial transactions. It provides comprehensive legal analysis, risk assessment, and document generation for business affairs.

### ✨ Core Capabilities

- **📄 Contract Review** - Analyze commercial contracts for risks, compliance, and favorable terms
- **💼 Transaction Advisory** - Guide M&A, financing, and partnership transactions
- **✅ Compliance Checking** - Verify regulatory compliance across jurisdictions
- **📝 Legal Document Generation** - Create NDAs, service agreements, and corporate documents
- **⚖️ Risk Assessment** - Evaluate legal, financial, and operational risks
- **🤝 Negotiation Support** - Develop strategies and tactics for business negotiations

---

### 🚀 Quick Start

#### Installation

```bash
# From PyPI (when published)
pip install openclaw-skill-corporate-lawyer

# From source
git clone https://github.com/ZhenRobotics/openclaw-corporate-lawyer.git
cd openclaw-corporate-lawyer
pip install -e .
```

#### Basic Usage

```python
import asyncio
from corporate_lawyer import CorporateLawyer
from corporate_lawyer.types import Contract

async def main():
    # Initialize lawyer
    lawyer = CorporateLawyer(jurisdiction="US")

    # Review a contract
    contract = Contract(
        title="Software License Agreement",
        contract_type="licensing",
        parties=["TechCorp Inc.", "ClientCo LLC"],
        contract_value=500000,
        full_text="[Contract text here...]",
        jurisdiction="Delaware",
    )

    # Get comprehensive contract analysis
    analysis = await lawyer.review_contract(contract)

    print(f"Overall Risk Score: {analysis.overall_risk_score}/100")
    print(f"Risk Level: {analysis.overall_risk_level}")
    print(f"Recommendation: {analysis.recommendation}")

    print(f"\nCritical Issues: {len(analysis.critical_issues)}")
    for issue in analysis.critical_issues:
        print(f"  - {issue.title}: {issue.description}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 📊 Features in Detail

#### 1. Contract Review & Analysis

**Comprehensive contract review including:**
- Risk identification and scoring (0-100 scale)
- Compliance analysis
- Financial terms review
- Liability assessment
- Actionable recommendations

**Risk Levels:** Critical, High, Medium, Low, Minimal

```python
analysis = await lawyer.review_contract(contract, detailed=True)

# Access findings
print(f"Risk Score: {analysis.overall_risk_score}")
print(f"Issues Found: {len(analysis.issues)}")
print(f"Favorable Terms: {analysis.favorable_terms}")
print(f"Unfavorable Terms: {analysis.unfavorable_terms}")
print(f"Missing Provisions: {analysis.missing_provisions}")
print(f"Suggested Modifications: {analysis.suggested_modifications}")
```

#### 2. Transaction Advisory

**Expert guidance for business transactions:**

**Supported Transaction Types:**
- Mergers & Acquisitions
- Asset/Stock Purchases
- Equity/Debt Financing
- Joint Ventures
- Strategic Partnerships
- Licensing Deals

**Advisory Components:**
- Deal structure recommendations
- Due diligence checklists (20+ items)
- Regulatory approval requirements
- Risk analysis and mitigation
- Timeline and cost estimates

```python
from corporate_lawyer.types import Transaction

transaction = Transaction(
    transaction_name="Acquisition of TargetCo",
    transaction_type="acquisition",
    buyer="BuyerCorp",
    seller="SellerCorp",
    transaction_value=50000000,
    industry="technology",
)

advice = await lawyer.advise_on_transaction(transaction)

print(f"Deal Complexity: {advice.deal_complexity}")
print(f"Estimated Timeline: {advice.estimated_timeline_days} days")
print(f"Key Risks: {advice.major_risks}")
```

#### 3. Compliance Checking

**Multi-jurisdictional compliance review:**

**Coverage Areas:**
- Data Privacy (GDPR, CCPA, etc.)
- Antitrust Regulations
- Employment Law
- Industry-Specific Regulations
- Corporate Governance

```python
from corporate_lawyer.types import CompanyProfile

company = CompanyProfile(
    company_name="TechCorp",
    industry="technology",
    company_size="medium",
)

compliance = await lawyer.check_compliance(
    subject="Business Operations",
    company_profile=company,
    scope=["data_privacy", "antitrust", "employment"],
)

print(f"Compliance Status: {compliance.overall_compliance_status}")
print(f"Compliance Score: {compliance.compliance_score}/100")
```

#### 4. Legal Document Generation

**Generate professional legal documents:**

**Document Types:**
- Non-Disclosure Agreements (NDA) - Mutual/Unilateral
- Service Agreements
- Consulting Agreements
- Employment Contracts
- Shareholder Agreements
- Letters of Intent

```python
document = await lawyer.generate_document(
    document_type="nda",
    parties=["Company A", "Company B"],
    terms={"term_years": 2, "survival_years": 3},
    jurisdiction="Delaware",
)

print(document.content)  # Full document text
print(f"Customization Notes: {document.customization_notes}")
```

#### 5. Risk Assessment

**Comprehensive legal risk evaluation:**

**Risk Categories:**
- Liability Risk
- Compliance Risk
- Financial Risk
- Operational Risk
- Reputational Risk
- Litigation Risk

```python
risk_assessment = await lawyer.assess_contract_risk(contract)

print(f"Overall Risk: {risk_assessment.overall_risk_level}")
print(f"Risk Score: {risk_assessment.overall_risk_score}/100")
print(f"Liability Risk: {risk_assessment.liability_risk_score}")
print(f"Compliance Risk: {risk_assessment.compliance_risk_score}")
print(f"Mitigation Strategies: {risk_assessment.recommended_risk_controls}")
```

#### 6. Negotiation Support

**Strategic negotiation guidance:**

**Strategy Components:**
- Overall approach and tactics
- Priority issues and positions
- Concession strategy
- Walk-away scenarios
- Leverage assessment

```python
strategy = await lawyer.generate_negotiation_strategy(
    context="Software License Agreement Negotiation",
    objectives=["Cap liability", "Favorable payment terms"],
    constraints={"contract_value": 500000, "alternatives": 2},
)

print(f"Approach: {strategy.overall_approach}")
print(f"Must-Haves: {strategy.must_haves}")
print(f"Walk-Away Scenarios: {strategy.walk_away_scenarios}")
```

---

### 🎓 Target Users

- **Corporate Legal Departments** - Contract management, compliance
- **Law Firms** - Client advisory, transaction support
- **Startups & SMBs** - Quick legal review, document generation
- **Business Executives** - Risk assessment, negotiation support
- **In-House Counsel** - Daily legal operations

---

### ⚠️ Legal Disclaimer

**IMPORTANT:** This tool provides general legal information for educational purposes only. It does NOT:
- Constitute legal advice
- Create an attorney-client relationship
- Replace consultation with qualified legal counsel

Always consult with qualified attorneys for specific legal advice.

---

### 🔧 Technical Stack

- **Language:** Python 3.10+
- **Type Safety:** Pydantic 2.5+ (20+ models)
- **Async:** asyncio, aiofiles
- **Code:** 23 Python files, 3,340 lines
- **Tests:** 6/6 modules passing (100% coverage)

---

### 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🇨🇳 中文版本

### 什么是 Corporate Lawyer？

Corporate Lawyer 是一个 AI 驱动的法律咨询系统，旨在帮助**企业、法务部门和律师事务所**应对复杂的商业交易。它为业务事务提供全面的法律分析、风险评估和文件生成。

### ✨ 核心功能

- **📄 合同审查** - 分析商业合同的风险、合规性和有利条款
- **💼 交易咨询** - 指导并购、融资和合作伙伴交易
- **✅ 合规检查** - 验证跨司法管辖区的监管合规性
- **📝 法律文件生成** - 创建保密协议、服务协议和公司文件
- **⚖️ 风险评估** - 评估法律、财务和运营风险
- **🤝 谈判支持** - 为商业谈判制定策略和战术

---

### 🚀 快速开始

#### 安装

```bash
# 从 PyPI 安装（发布后）
pip install openclaw-skill-corporate-lawyer

# 从源码安装
git clone https://github.com/ZhenRobotics/openclaw-corporate-lawyer.git
cd openclaw-corporate-lawyer
pip install -e .
```

#### 基本使用

```python
import asyncio
from corporate_lawyer import CorporateLawyer
from corporate_lawyer.types import Contract

async def main():
    # 初始化律师
    lawyer = CorporateLawyer(jurisdiction="US")

    # 审查合同
    contract = Contract(
        title="软件许可协议",
        contract_type="licensing",
        parties=["科技公司", "客户公司"],
        contract_value=500000,
        full_text="[合同文本...]",
        jurisdiction="特拉华州",
    )

    # 获取全面的合同分析
    analysis = await lawyer.review_contract(contract)

    print(f"总体风险评分: {analysis.overall_risk_score}/100")
    print(f"风险等级: {analysis.overall_risk_level}")
    print(f"建议: {analysis.recommendation}")

    print(f"\n严重问题: {len(analysis.critical_issues)}")
    for issue in analysis.critical_issues:
        print(f"  - {issue.title}: {issue.description}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 📊 功能详解

#### 1. 合同审查与分析

**全面的合同审查，包括：**
- 风险识别和评分（0-100 分制）
- 合规性分析
- 财务条款审查
- 责任评估
- 可操作的建议

**风险等级：** 严重、高、中、低、最小

```python
analysis = await lawyer.review_contract(contract, detailed=True)

# 访问调查结果
print(f"风险评分: {analysis.overall_risk_score}")
print(f"发现的问题: {len(analysis.issues)}")
print(f"有利条款: {analysis.favorable_terms}")
print(f"不利条款: {analysis.unfavorable_terms}")
print(f"缺失条款: {analysis.missing_provisions}")
print(f"建议修改: {analysis.suggested_modifications}")
```

#### 2. 交易咨询

**商业交易的专家指导：**

**支持的交易类型：**
- 合并与收购
- 资产/股权购买
- 股权/债务融资
- 合资企业
- 战略合作伙伴关系
- 许可交易

**咨询组成部分：**
- 交易结构建议
- 尽职调查清单（20+ 项）
- 监管审批要求
- 风险分析和缓解
- 时间线和成本估算

```python
from corporate_lawyer.types import Transaction

transaction = Transaction(
    transaction_name="收购目标公司",
    transaction_type="acquisition",
    buyer="买方公司",
    seller="卖方公司",
    transaction_value=50000000,
    industry="technology",
)

advice = await lawyer.advise_on_transaction(transaction)

print(f"交易复杂度: {advice.deal_complexity}")
print(f"预计时间线: {advice.estimated_timeline_days} 天")
print(f"主要风险: {advice.major_risks}")
```

#### 3. 合规检查

**多司法管辖区合规审查：**

**覆盖领域：**
- 数据隐私（GDPR、CCPA 等）
- 反垄断法规
- 劳动法
- 行业特定法规
- 公司治理

```python
from corporate_lawyer.types import CompanyProfile

company = CompanyProfile(
    company_name="科技公司",
    industry="technology",
    company_size="medium",
)

compliance = await lawyer.check_compliance(
    subject="业务运营",
    company_profile=company,
    scope=["data_privacy", "antitrust", "employment"],
)

print(f"合规状态: {compliance.overall_compliance_status}")
print(f"合规评分: {compliance.compliance_score}/100")
```

#### 4. 法律文件生成

**生成专业法律文件：**

**文件类型：**
- 保密协议（NDA）- 双向/单向
- 服务协议
- 咨询协议
- 雇佣合同
- 股东协议
- 意向书

```python
document = await lawyer.generate_document(
    document_type="nda",
    parties=["公司 A", "公司 B"],
    terms={"term_years": 2, "survival_years": 3},
    jurisdiction="特拉华州",
)

print(document.content)  # 完整文件文本
print(f"定制说明: {document.customization_notes}")
```

#### 5. 风险评估

**全面的法律风险评估：**

**风险类别：**
- 责任风险
- 合规风险
- 财务风险
- 运营风险
- 声誉风险
- 诉讼风险

```python
risk_assessment = await lawyer.assess_contract_risk(contract)

print(f"总体风险: {risk_assessment.overall_risk_level}")
print(f"风险评分: {risk_assessment.overall_risk_score}/100")
print(f"责任风险: {risk_assessment.liability_risk_score}")
print(f"合规风险: {risk_assessment.compliance_risk_score}")
print(f"缓解策略: {risk_assessment.recommended_risk_controls}")
```

#### 6. 谈判支持

**战略谈判指导：**

**策略组成部分：**
- 总体方法和战术
- 优先事项和立场
- 让步策略
- 退出场景
- 杠杆评估

```python
strategy = await lawyer.generate_negotiation_strategy(
    context="软件许可协议谈判",
    objectives=["限制责任", "有利的付款条件"],
    constraints={"contract_value": 500000, "alternatives": 2},
)

print(f"方法: {strategy.overall_approach}")
print(f"必备项: {strategy.must_haves}")
print(f"退出场景: {strategy.walk_away_scenarios}")
```

---

### 🎓 目标用户

- **企业法务部门** - 合同管理、合规
- **律师事务所** - 客户咨询、交易支持
- **初创公司和中小企业** - 快速法律审查、文件生成
- **企业高管** - 风险评估、谈判支持
- **内部法律顾问** - 日常法律运营

---

### ⚠️ 法律免责声明

**重要提示：** 本工具仅提供一般法律信息供教育用途。它不能：
- 构成法律建议
- 建立律师-客户关系
- 替代专业法律顾问的咨询

请务必就具体法律建议咨询合格的律师。

---

### 🔧 技术栈

- **语言：** Python 3.10+
- **类型安全：** Pydantic 2.5+（20+ 模型）
- **异步：** asyncio, aiofiles
- **代码：** 23 个 Python 文件，3,340 行
- **测试：** 6/6 模块通过（100% 覆盖）

---

### 📄 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)

---

## 📊 Project Statistics / 项目统计

| Metric / 指标 | Value / 数值 |
|---------------|-------------|
| **Version / 版本** | 0.1.0 |
| **Code Lines / 代码行数** | 3,340 |
| **Python Files / Python 文件** | 23 |
| **Core Modules / 核心模块** | 6 |
| **Data Models / 数据模型** | 20+ |
| **Test Coverage / 测试覆盖** | 100% (6/6) |
| **Documentation / 文档** | 1,140+ lines |
| **License / 许可证** | MIT |

## 🔗 Links / 链接

- **GitHub Repository / 仓库**: https://github.com/ZhenRobotics/openclaw-corporate-lawyer
- **GitHub Release / 发布**: https://github.com/ZhenRobotics/openclaw-corporate-lawyer/releases/tag/v0.1.0
- **PyPI Package / 包** (when published / 发布后): https://pypi.org/project/openclaw-skill-corporate-lawyer/

---

**Built for businesses and legal professionals / 为企业和法律专业人士打造**

*Empowering smart legal decisions / 赋能智慧法律决策*
