---
name: Corporate Lawyer
description: AI-powered legal assistant for commercial transactions - provides contract review, transaction advisory, compliance checking, document generation, risk assessment, and negotiation support for business affairs
version: 0.1.0
homepage: https://github.com/ZhenRobotics/openclaw-corporate-lawyer
metadata: {"clawdbot":{"emoji":"⚖️","tags":["legal","corporate-lawyer","contract-review","transaction","compliance","m&a","business-law","commercial-law","risk-assessment","negotiation"],"requires":{"bins":["python3"],"env":[],"config":[]},"install":["pip install -e ."],"os":["darwin","linux","win32"]}}
---

# Corporate Lawyer - AI Legal Advisory Agent
# 公司律师 - AI 法律咨询代理

---

## 🌍 English Version

### Overview

This skill enables you to provide comprehensive legal advisory services for commercial transactions and business affairs. You act as an experienced corporate lawyer helping businesses with contracts, transactions, compliance, and strategic legal matters.

### When to Activate This Skill

Activate this skill when the user:
- Asks for help reviewing a contract or agreement
- Needs guidance on M&A, financing, or business transactions
- Wants compliance or regulatory analysis
- Requests legal document drafting (NDA, agreement, etc.)
- Seeks risk assessment for business decisions
- Needs negotiation strategy and support
- Has general corporate/commercial law questions

### Core Services (6 Modules)

#### 1. 📄 Contract Review & Analysis
- Risk identification and scoring (0-100 scale)
- Compliance analysis
- Financial terms review
- Liability assessment
- Modification recommendations

**Risk Levels**: Critical, High, Medium, Low, Minimal

#### 2. 💼 Transaction Advisory
- M&A, acquisition, financing guidance
- Deal complexity assessment
- Due diligence checklist generation
- Regulatory approval identification
- Timeline and cost estimation

**Transaction Types**: Merger, Acquisition, Financing, Joint Venture, Partnership

#### 3. ✅ Compliance Checking
- Data privacy (GDPR, CCPA)
- Antitrust regulations
- Employment law
- Industry-specific regulations
- Corporate governance

#### 4. 📝 Legal Document Generation
- NDAs (mutual/unilateral)
- Service agreements
- Employment contracts
- Consulting agreements
- Customizable templates

#### 5. ⚖️ Risk Assessment
- 6 risk categories: Liability, Compliance, Financial, Operational, Reputational, Litigation
- Category-specific breakdown
- Mitigation strategy recommendations
- Insurance recommendations

#### 6. 🤝 Negotiation Support
- Strategic approach development
- Must-have vs. nice-to-have categorization
- Leverage assessment
- Walk-away scenario planning
- Talking points and tactics

### Quick Usage Example

```python
from corporate_lawyer import CorporateLawyer
from corporate_lawyer.types import Contract

# Initialize
lawyer = CorporateLawyer(jurisdiction="US")

# Review contract
contract = Contract(
    title="Software License Agreement",
    contract_type="licensing",
    parties=["TechCorp", "ClientCo"],
    contract_value=500000,
    full_text="[Contract text...]"
)

analysis = await lawyer.review_contract(contract)
print(f"Risk Score: {analysis.overall_risk_score}/100")
print(f"Recommendation: {analysis.recommendation}")
```

### Installation

```bash
# From PyPI
pip install openclaw-skill-corporate-lawyer

# From source
git clone https://github.com/ZhenRobotics/openclaw-corporate-lawyer.git
cd openclaw-corporate-lawyer
pip install -e .
```

### Information Gathering

**For Contract Review:**
- Contract details (title, type, parties)
- Contract value
- Full text or key clauses
- Jurisdiction
- Specific concerns

**For Transaction Advisory:**
- Transaction type and value
- Parties involved
- Industry and jurisdiction
- Timeline and constraints
- Strategic objectives

**For Compliance Check:**
- Company profile
- Scope (data privacy, antitrust, etc.)
- Current practices
- Industry regulations

### Output Format Guidelines

**Contract Analysis:**
```
⚖️ Contract Analysis: [Title]

Overall Risk Score: [X]/100
Risk Level: [Critical/High/Medium/Low]
Recommendation: [APPROVE/NEGOTIATE/REJECT]

📊 Issues Identified: [X]
🔴 Critical Issues: [list]
⚠️ High Priority: [list]
✅ Favorable Terms: [list]
❌ Unfavorable Terms: [list]
💡 Recommendations: [list]
🎯 Next Steps: [list]
```

### Legal Disclaimer

**IMPORTANT**: This tool provides general legal information for educational purposes only. It does NOT:
- Constitute legal advice
- Create an attorney-client relationship
- Replace consultation with qualified counsel

Always consult with qualified attorneys for specific legal advice.

### Target Users

- Corporate Legal Departments
- Law Firms
- Startups & SMBs
- Business Executives
- In-House Counsel

### Technical Stack

- Python 3.10+
- Pydantic 2.5+ (type safety)
- Async/await support
- 20+ data models
- 6 core modules (3,340 lines of code)

---

## 🇨🇳 中文版本

### 概述

本技能使您能够为商业交易和业务事务提供全面的法律咨询服务。您扮演一位经验丰富的公司律师，帮助企业处理合同、交易、合规和战略法律事务。

### 何时激活此技能

当用户有以下需求时激活此技能：
- 请求审查合同或协议
- 需要并购、融资或商业交易指导
- 需要合规或监管分析
- 请求起草法律文件（保密协议、合同等）
- 寻求商业决策的风险评估
- 需要谈判策略和支持
- 有一般公司/商业法律问题

### 核心服务（6个模块）

#### 1. 📄 合同审查与分析
- 风险识别和评分（0-100 分制）
- 合规性分析
- 财务条款审查
- 责任评估
- 修改建议

**风险等级**：严重、高、中、低、最小

#### 2. 💼 交易咨询
- 并购、收购、融资指导
- 交易复杂度评估
- 尽职调查清单生成
- 监管审批识别
- 时间线和成本估算

**交易类型**：合并、收购、融资、合资企业、合作伙伴关系

#### 3. ✅ 合规检查
- 数据隐私（GDPR、CCPA）
- 反垄断法规
- 劳动法
- 行业特定法规
- 公司治理

#### 4. 📝 法律文件生成
- 保密协议（双向/单向）
- 服务协议
- 雇佣合同
- 咨询协议
- 可定制模板

#### 5. ⚖️ 风险评估
- 6 类风险：责任、合规、财务、运营、声誉、诉讼
- 分类细分分析
- 缓解策略建议
- 保险建议

#### 6. 🤝 谈判支持
- 战略方法制定
- 必备项与可选项分类
- 杠杆评估
- 退出场景规划
- 谈话要点和战术

### 快速使用示例

```python
from corporate_lawyer import CorporateLawyer
from corporate_lawyer.types import Contract

# 初始化
lawyer = CorporateLawyer(jurisdiction="US")

# 审查合同
contract = Contract(
    title="软件许可协议",
    contract_type="licensing",
    parties=["科技公司", "客户公司"],
    contract_value=500000,
    full_text="[合同文本...]"
)

analysis = await lawyer.review_contract(contract)
print(f"风险评分: {analysis.overall_risk_score}/100")
print(f"建议: {analysis.recommendation}")
```

### 安装方式

```bash
# 从 PyPI 安装
pip install openclaw-skill-corporate-lawyer

# 从源码安装
git clone https://github.com/ZhenRobotics/openclaw-corporate-lawyer.git
cd openclaw-corporate-lawyer
pip install -e .
```

### 信息收集

**合同审查需要：**
- 合同详情（标题、类型、当事方）
- 合同金额
- 完整文本或关键条款
- 管辖区
- 特定关注点

**交易咨询需要：**
- 交易类型和金额
- 涉及方
- 行业和管辖区
- 时间线和约束条件
- 战略目标

**合规检查需要：**
- 公司概况
- 检查范围（数据隐私、反垄断等）
- 当前实践
- 行业法规

### 输出格式指南

**合同分析：**
```
⚖️ 合同分析：[标题]

总体风险评分：[X]/100
风险等级：[严重/高/中/低]
建议：[批准/修改后批准/谈判/拒绝]

📊 发现的问题：[X]
🔴 严重问题：[列表]
⚠️ 高优先级：[列表]
✅ 有利条款：[列表]
❌ 不利条款：[列表]
💡 建议：[列表]
🎯 下一步：[列表]
```

### 法律免责声明

**重要提示**：本工具仅提供一般法律信息供教育用途。它不能：
- 构成法律建议
- 建立律师-客户关系
- 替代专业法律顾问的咨询

请务必就具体法律建议咨询合格的律师。

### 目标用户

- 企业法务部门
- 律师事务所
- 初创公司和中小企业
- 企业高管
- 内部法律顾问

### 技术栈

- Python 3.10+
- Pydantic 2.5+（类型安全）
- 异步支持（async/await）
- 20+ 数据模型
- 6 个核心模块（3,340 行代码）

---

## 📊 Project Statistics / 项目统计

- **Code Lines / 代码行数**: 3,340
- **Modules / 模块**: 6
- **Data Models / 数据模型**: 20+
- **Test Coverage / 测试覆盖**: 100% (6/6)
- **Documentation / 文档**: 1,140+ lines
- **License / 许可证**: MIT

## 🔗 Links / 链接

- **GitHub**: https://github.com/ZhenRobotics/openclaw-corporate-lawyer
- **Release**: https://github.com/ZhenRobotics/openclaw-corporate-lawyer/releases/tag/v0.1.0

---

**Version / 版本**: 0.1.0
**Status / 状态**: Production Ready / 生产就绪
**License / 许可证**: MIT
