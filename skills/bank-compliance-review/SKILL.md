---
name: Bank Compliance Review Assistant
slug: bank-compliance
description: AI-powered bank compliance and regulatory review assistant - screen marketing materials, KYC documents, AML alerts, and NFRA/CBIRC compliance checks. Updated for 2025-2026 regulations including 商业银行资本管理办法 (Basel III China 2024), 消费者权益保护规定升级, FATF mutual evaluation 2025, and 反洗钱法修订. Keywords: bank compliance, KYC, AML, regulatory review, NFRA, Basel III, China banking, 合规审查, 合规审核, 监管合规, 反洗钱, KYC尽调, 客户身份识别, 受益人识别, 制裁筛查, 交易监控.
version: "4.1.1"
triggers:
  - 合规审查
  - 合规审核
  - 监管合规
  - KYC筛查
  - 反洗钱
  - 合规检查
  - 监管报告
  - 材料合规
  - 宣传合规
  - 合规风险
---

# Bank Compliance Review Assistant
# 银行合规审查助手


### 银行监管最新动态 [2026-06-15更新]

| 动态类型 | 内容摘要 | 发布时间 | 影响范围 |
|---------|---------|---------|---------|
| 监管发布 | NFRA 2026年第2号令：《银行保险机构许可证管理办法》6月1日施行 | 2026-06 | 合规审查需纳入许可证管理新规 |
| 监管动态 | Basel III资本管理办法持续实施，三重风险计量规则逐步落地 | 2026-H1 | 合规审查需关注资本计量合规性 |
| 监管动态 | 2026年Q1银行监管处罚分析：消费者权益保护处罚占比提升 | 2026-Q1 | 消费者权益保护处罚案例增加，合规审查需加强 |
| 政策更新 | 交易账簿资本要求风险敏感性提高，12家上市银行资本占用变化 | 2025-11 | 交易账簿业务合规审查需关注资本占用 |

> **数据截止**: 2026-06-15 | 来源：国家金融监督管理总局、银行业协会、安永分析
> **声明**: 以上动态供参考，具体以官方最新发布为准


### 银行监管最新动态 [2026-06-28更新]

| 动态类型 | 内容摘要 | 发布时间 | 影响范围 |
|---------|---------|---------|---------|
| 监管发布 | 金融监管总局发布《关于银行业保险业人工智能安全开发应用的指导意见》，明确资金交易、资产评估、信贷审批等为AI高风险应用场景 | 2026-06-18 | 银行AI应用合规与信贷风控 |
| 监管计划 | NFRA《2026年规章制定工作计划》新制定《银行业保险业网络安全管理办法》，银行网络安全与数据安全从指导意见升级为刚性规章 | 2026-06-23 | 银行网络安全与数据合规 |
| 监管施行 | NFRA 2026年第2号令《银行保险机构许可证管理办法》6月1日起施行，银行许可证管理纳入内控自评估 | 2026-06-01 | 银行合规审查与许可证管理 |

> **数据截止**: 2026-06-28 | 来源：国家金融监督管理总局、行业公开信息
> **声明**: 以上动态供参考，具体以官方最新发布为准

## Skill Overview

### 0. 2024-2026 银行合规最新监管动态

| 时间 | 法规/事项 | 合规影响 |
|------|---------|---------|
| **2024年1月1日** | 《商业银行资本管理办法》正式实施（中国版巴三） | 三档差异化资本监管，信用/市场/操作风险全面升级 |
| **2024年** | 《商业银行消费者权益保护管理办法》修订 | 适当性管理、信息披露、投诉处理更严格 |
| **2025年** | FATF对中国反洗钱互评估完成 | AML体系建设压力加大，KYC/CDD标准提升 |
| **2025年11月** | 《个人信息保护法》实施细则 | 银行客户数据处理合规要求更细化 |
| **2025年** | 《反洗钱法》修订草案审议 | 可疑交易报告、客户尽职调查标准拟提升 |
| **2026年** | 《金融消费者投诉处理管理办法》修订征求意见 | 投诉处理时效、赔偿标准更新 |

| Attribute | Value |
|-----------|-------|
| **Skill Type** | Pure Conversation / Compliance Workflow |
| **Target Users** | Bank compliance officers, legal counsel, KYC/AML analysts, product managers |
| **Core Capability** | Marketing material screening → Basel III capital check → KYC/AML review → FATF compliance → Risk escalation |
| **Industry** | Commercial banking, regulatory compliance, anti-money laundering |

---

## How to Use

Simply describe your compliance review task. No scripts needed.

**Example prompts:**
- "帮我审查这条贷款产品的朋友圈宣传文案"
- "KYC筛查这个企业客户"
- "检查这份理财产品说明书是否合规"
- "帮我做一次反洗钱名单筛查"
- "审查这份银保合作协议的合规风险"

---

## Phase 1: Marketing Material Compliance Review

### Screening Dimensions:

**P0 - Absolute Violations (Must Fix):**
| Violation Type | Examples | Risk Level |
|----------------|----------|------------|
| False/Misleading Claims | 承诺固定收益、保本、100%赔付 | HIGH |
| Absolute Language | 最优、第一、唯一、绝对安全 | HIGH |
| Regulatory Prohibited Terms | 银行存款、储蓄性质等误导性表述（理财/保险产品） | HIGH |
| Unlicensed Recommendations | 暗示银行信用背书未经授权产品 | HIGH |
| Personal Data Exposure | 泄露客户隐私信息 | CRITICAL |

**P1 - Significant Issues (Should Fix):**
| Issue Type | Examples | Risk Level |
|------------|----------|------------|
| Missing Risk Disclosures | 未披露产品风险、净值波动 | MEDIUM |
| Incomplete Fee Disclosures | 手续费、管理费披露不完整 | MEDIUM |
| Regulatory Sensitive Terms | CBIRC/CBDRC regulated terms without approval | MEDIUM |
| Competitive Disparagement | 贬低其他银行/金融机构产品 | MEDIUM |
| Missing Legal Disclaimer | 缺少法定免责声明 | HIGH |

**P2 - Best Practice (Consider Improving):**
- Font size too small for key disclosures
- Complex language not accessible to retail customers
- Call-to-action (CTA) unclear or too aggressive

### Review Output Format:

```
✅ 合规通过 / ⚠️ 存在N处风险（必须修改）/ ❌ 存在P0级违规（立即整改）

🔴 P0级违规（3处）：
1. "预期年化收益8%" —— 未标注"业绩比较基准"及"非保证收益"
2. "保本理财" —— 资管新规后不允许使用"保本"表述
3. "比银行存款更划算" —— 贬低银行存款产品

🟡 P1级建议（2处）：
1. 管理费率0.5%未在首页显著披露
2. 缺少"理财有风险，投资需谨慎"标准声明

✅ 合格项（4处）：
- 风险等级标识清晰（R3中等风险）
- 封闭期说明完整
- 起投金额披露准确
- 产品编码已公示

💡 修改建议：
[逐条提供修改后文案]
```

---

## Phase 2: KYC/AML Screening

### KYC Due Diligence Framework:

**1. Basic Information Verification:**
- Company registration documents (营业执照)
- Ultimate Beneficial Owner (UBO) identification
- Authorized signatories and board resolution
- Anti-money laundering policy documentation

**2. Risk Scoring Matrix:**

| Risk Factor | Low Risk | Medium Risk | High Risk |
|-------------|----------|-------------|-----------|
| Customer Type | Listed company, SOE | Private enterprise | Individual, offshore entity |
| Business Nature | Traditional, regulated | Mixed, domestic | Crypto, trading, cash-heavy |
| Geography | Domestic, G7 | Emerging markets | High-risk countries (FATF list) |
| Transaction Pattern | Regular, predictable | Variable | Large, irregular, round-tripping |
| PEP Status | No PEP connection | Indirect connection | Direct PEP involvement |

**Overall Risk Rating:** Low / Medium / High / Restricted

### AML Alert Review:

**Red Flag Indicators (红旗指标):**
- [ ] Structuring (拆单交易，规避报告阈值)
- [ ] Rapid movement of funds (快进快出)
- [ ] Round-tripping (资金循环)
- [ ] High-risk jurisdiction transactions (高风险地区往来)
- [ ] Shell company transactions (空壳公司往来)
- [ ] Unusual cash patterns (异常现金模式)
- [ ] Mismatched business activity (交易与业务不符)

### Review Output:

```
【KYC筛查报告】

企业名称：[X]
筛查日期：[日期]
综合风险评级：[高/中/低]

一、基础信息核实
✅ 营业执照核实通过
✅ 法人代表身份核实通过
⚠️ UBO穿透核查：最终受益人为[张三]，持股[70%]，需进一步核实资金来源

二、名单筛查
✅ 中国人民银行制裁名单：无命中
✅ FATF高风险国家名单：无命中
⚠️ 海关/税务黑名单：疑似命中[X公司]，需人工复核

三、交易监控评估
- 月均交易量：[1,200万元]
- 交易对手集中度：[前5名占比85%] ⚠️ 警告
- 跨境交易占比：[12%] ⚠️ 建议关注

四、综合结论
[高风险/建议加强尽调/可以建立业务关系/拒绝开户]

五、后续行动建议
1. [立即上报合规负责人]
2. [要求客户提供进一步证明材料]
3. [设置交易限额并定期复核]
```

---

## Phase 3: CBIRC Regulatory Compliance Check

### Key CBIRC/NFRA Regulations Checklist (2024-2026 Updated):

| Regulation | Requirement | Check |
|-----------|-------------|-------|
| 资管新规 (2018) | 打破刚兑，禁止资金池，禁止期限错配 | [ ] |
| 理财销售管理办法 | 风险评级匹配，"双录"要求 | [ ] |
| **商业银行资本管理办法（2024新规）** | 三档差异化资本监管，风险权重重新校准 | [ ] |
| **消费者权益保护管理办法（2024版）** | 适当性销售，信息披露标准升级，7天冷静期 | [ ] |
| 数据安全法/个人信息保护法 | 客户信息保密，不得违规泄露 | [ ] |
| 反洗钱规定（2025修订中） | 大额/可疑交易报告，KYC/CDD加强 | [ ] |
| **FATF合规标准（2025互评估后）** | 受益权人识别，政治敏感人物（PEP）管理 | [ ] |
| 关联交易管理办法 | 关联方授信须经审批并披露 | [ ] |

---

## Phase 4: Regulatory Reporting Support

### Common Regulatory Reports:

| Report Type | Frequency | Key Content |
|------------|----------|-------------|
| 监管统计数据报送 (1104) | 定期 | 资本充足率、资产质量、流动性指标 |
| 反洗钱大额交易报告 | 实时 | 单笔50万/累计200万以上现金交易 |
| 可疑交易报告 | 实时 | 可疑行为识别与上报 |
| 重大事项报告 | 事件驱动 | 重大风险事件、高管变动 |
| 消保投诉统计 | 季度 | 投诉数量、类型、处理结果 |

---

## Quick Command Templates

**Marketing Material Review:**
```
审查以下银行产品宣传材料是否合规：
[粘贴文案/材料内容]
产品类型：[理财/贷款/保险/基金]
目标客群：[个人/企业/高净值]
```

**KYC Screening:**
```
对[企业名称]进行KYC筛查：
- 营业执照：[描述]
- 主要业务：[描述]
- 预期年交易量：[X万元]
- 是否有跨境业务：[是/否]
- 是否有涉外股东：[是/否]
```

**AML Alert Investigation:**
```
调查以下可疑交易预警：
- 客户：[名称]
- 预警类型：[描述]
- 涉及金额：[X万元]
- 交易特征：[描述]
```

**Agreement Compliance Review:**
```
审查以下合作协议的合规风险：
[粘贴协议摘要或关键条款]
合作类型：[银保合作/银证合作/银信合作/其他]
```

---

## Disclaimer

This skill provides compliance screening support for bank officers. AI-generated compliance opinions do not replace formal legal advice or regulatory guidance. All compliance decisions must be reviewed by qualified compliance officers and approved by appropriate authority levels per internal policies. Report generation is for workflow assistance only.
