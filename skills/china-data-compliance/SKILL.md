---
name: china-data-compliance
description: "Ensure applications comply with Chinese data protection laws (PIPL, Cybersecurity Law, Data Security Law). Teach AI agents how to implement privacy policies, consent management, data localization, cross-border transfer assessment, and security impact assessment. Covers: PIPL compliance checklist, personal information consent flow, data localization implementation, cross-border data transfer assessment, and security impact assessment (网络安全审查). Triggers on: 中国数据合规, china data compliance, 个人信息保护法, PIPL compliance, 网络安全法, cybersecurity law, 数据安全法, data security law, 数据本地化, data localization, 跨境数据传输, cross-border data transfer, 隐私政策, privacy policy china, 个人信息同意, consent management china, 网络安全审查, security assessment china, 数据出境, data export china"
version: "2.3.0"
license: MIT-0
compatibility: "Claude Code, Cursor, Windsurf, Codex CLI, Gemini CLI, OpenClaw, Kimi Code, Qwen Code, Aider, Amp"
homepage: "https://github.com/lm203688/china-compliance-skills-mirror"
when_to_use: "Use when building applications for Chinese users that collect personal information, store data, or transfer data across borders. Also for PIPL合规, 数据出境评估, 隐私政策, 数据本地化, 网络安全审查, GDPR+PIPL dual compliance, or any China data protection question."
argument-hint: "<app description or data flow> [compliance scope: pipl|cybersecurity|data-security|all]"
---

# China Data Compliance - 中国数据合规专家

You are an expert at ensuring applications comply with China's three-pillar data protection framework: PIPL (个人信息保护法), Cybersecurity Law (网络安全法), and Data Security Law (数据安全法).

## Core Philosophy

**In China, data compliance is not optional — it's a prerequisite for operating.** Non-compliance can result in service suspension, fines up to ¥50M or 5% of annual revenue, and criminal liability. You help agents build compliance into the architecture, not bolt it on after.

## The Three Laws

| Law | Focus | Key Requirement | Max Penalty |
|-----|-------|----------------|-------------|
| PIPL (2021) | Personal information | Consent + purpose limitation | ¥50M or 5% revenue |
| Cybersecurity Law (2017) | Network security | Security assessment + data localization for CII | ¥1M + suspension |
| Data Security Law (2021) | Data classification | Classification + cross-border assessment | ¥10M + suspension |

## Workflow 1: PIPL Compliance Checklist

### Step 1: Privacy Policy (隐私政策)
```markdown
Required sections in Chinese privacy policy:
1. 信息收集范围 (What data you collect)
2. 使用目的 (Why you collect it)
3. 共享与披露 (Who you share with)
4. 存储地点与期限 (Where and how long)
5. 用户权利 (User rights: access, delete, export)
6. 未成年人保护 (Under-14 protection)
7. 跨境传输 (Cross-border transfer, if applicable)
8. 更新机制 (How you notify changes)
```

### Step 2: Consent Management
```javascript
// PIPL consent flow implementation
class PIPLConsent {
  // Separate consent required for:
  // 1. Core service data collection
  // 2. Marketing communications
  // 3. Third-party sharing
  // 4. Cross-border transfer
  // 5. Sensitive personal information (biometrics, health, finance)
  // 6. Under-14 data (parental consent required)

  async collectConsent({ purpose, dataTypes, isSensitive, isCrossBorder }) {
    // Each purpose needs SEPARATE consent (not bundled)
    // Sensitive data needs EXPLICIT consent (not implied)
    // Cross-border needs SEPARATE consent + security assessment
    
    return {
      consentId: generateId(),
      purpose,
      dataTypes,
      timestamp: Date.now(),
      version: this.policyVersion,
      method: isSensitive ? 'explicit' : 'general',
      withdrawable: true  // Must always be withdrawable
    };
  }

  async withdrawConsent(consentId) {
    // Must stop processing within 15 days
    // Must delete data within 30 days
    // Cannot refuse core service if user withdraws non-essential consent
  }
}
```

### Step 3: User Rights Implementation
```javascript
// PIPL user rights API
const userRights = {
  // Right to access (查阅权)
  async exportData(userId) { /* Return all data about user */ },
  
  // Right to delete (删除权)
  async deleteData(userId) { /* Delete within 30 days */ },
  
  // Right to correct (更正权)
  async correctData(userId, field, value) { /* Update personal info */ },
  
  // Right to portability (可携带权)
  async portData(userId) { /* Export in standard format */ },
  
  // Right to refuse automated decision (拒绝自动化决策权)
  async optOutAutomation(userId) { /* Human review available */ },
  
  // Right to withdraw consent (撤回同意权)
  async withdrawConsent(userId) { /* Stop processing, keep minimum */ }
};
```

## Workflow 2: Data Localization (数据本地化)

### When Required
- **Critical Information Infrastructure (CII)** operators: MUST store in China
- **Personal information handlers**: If processing >1M users or cumulative export >100K users
- **Important data**: As classified by sector regulators

### Implementation
```bash
# Tencent Cloud (China regions)
# Store data in ap-shanghai or ap-guangzhou
tccli cos create-bucket --Bucket my-data-cn --Region ap-shanghai

# Alibaba Cloud (China regions)
aliyun oss mb oss://my-data-cn --region cn-shanghai

# Database must be in China region
# MySQL: ap-shanghai (Tencent) / cn-shanghai (Alibaba)
# Redis: ap-shanghai (Tencent) / cn-shanghai (Alibaba)
```

### Architecture Pattern
```
[China Users] → [China CDN] → [China Servers (Shanghai)]
                                    ↓ (replicated, not primary)
                            [Global Servers (if needed)]
```

## Workflow 3: Cross-Border Data Transfer Assessment (数据出境安全评估)

### Step 1: Determine if Assessment is Required
```javascript
function needsAssessment({ userCount, dataTypes, isCII, hasImportantData }) {
  // Mandatory assessment if ANY of these:
  if (isCII) return true;  // CII operator
  if (hasImportantData) return true;  // Important data
  if (userCount > 1000000) return true;  // >1M users' PI
  if (dataTypes.includes('sensitive') && userCount > 10000) return true;  // >10K users' sensitive PI
  if (cumulativeExportUsers > 100000) return true;  // Cumulative >100K users
  
  // Otherwise: standard contract or certification may suffice
  return false;
}
```

### Step 2: Assessment Report Template
```markdown
# 数据出境安全评估报告

## 1. 出境数据情况
- 数据类型和数量
- 接收方信息
- 传输方式和技术措施

## 2. 合法性基础
- 同意情况
- 合同必要性
- 法定义务

## 3. 风险评估
- 数据泄露风险
- 数据滥用风险
- 接收方法律环境风险

## 4. 保护措施
- 加密传输
- 访问控制
- 审计日志

## 5. 应急预案
- 数据泄露响应
- 用户通知机制
```

## Workflow 4: Security Impact Assessment (网络安全审查)

### When Required
- Platform operators with >1M users before IPO
- CII operators purchasing network products/services
- Data processors affecting national security

### Assessment Process
```
1. Self-assessment → 2. Submit to CAC → 3. Initial review (30 days) → 4. Deep review (90 days) → 5. Decision
```

## Workflow 5: App Privacy Compliance (App隐私合规)

### Pre-Launch Checklist
- [ ] Privacy policy accessible before registration
- [ ] Separate consent for each data collection purpose
- [ ] No forced consent (can use app without non-essential consent)
- [ ] No background collection without explicit consent
- [ ] SDK list disclosure (all third-party SDKs)
- [ ] Under-14 special protection mode
- [ ] Account deletion function (within 15 days)
- [ ] Data export function
- [ ] No unauthorized sharing with third parties
- [ ] No tracking after uninstall

### Common Rejection Reasons (App Store / Ministry review)
1. Privacy policy not visible before first use
2. Collecting data not mentioned in privacy policy
3. Bundled consent (forcing all-or-nothing)
4. No account deletion function
5. Background location/collection without consent
6. SDK not disclosed in privacy policy

## Safety Rules

1. **Never skip consent** — PIPL requires separate, explicit, informed consent
2. **Data minimization** — only collect what you need, delete when purpose is fulfilled
3. **China storage first** — default to China regions for Chinese user data
4. **Document everything** — keep consent records, assessment reports, audit logs
5. **Regular review** — laws update frequently; review compliance quarterly
6. **Legal counsel** — this skill provides technical guidance, not legal advice; always consult a China data lawyer for production systems

## 🌐 Web App — 合规通

**不想写代码？直接用Web版：**

👉 **https://1341839497-jv04655vcs.ap-shanghai.tencentscf.com/**

- 免费检测5次/月
- Pro版 ¥99/月：无限次检测 + 批量检测 + API接入
- 支持小红书/抖音/百度/淘宝/京东5大平台
- 150+违禁词库 + SEO合规检查 + 安全替换建议

## Quick Reference

| Requirement | Threshold | Action |
|-------------|-----------|--------|
| Data localization | CII operator | Store all data in China |
| Cross-border assessment | >1M users PI | Submit to CAC |
| Security assessment | Pre-IPO >1M users | Submit to CAC |
| Privacy policy | All apps | Required before first use |
| Consent management | All PI processing | Separate per purpose |
| Account deletion | All apps | Must provide within 15 days |
| Under-14 protection | All apps with minor users | Parental consent + special mode |

## Next Best Skill

- **Primary**: [cn-seo-optimizer](https://github.com/lm203688/china-compliance-skills-mirror/tree/main/skills/cn-seo-optimizer) — after data compliance is in place, check content for advertising law violations
- **Related**: [cn-geo-monitor](https://github.com/lm203688/china-compliance-skills-mirror/tree/main/skills/cn-geo-monitor) — optimize brand visibility in Chinese AI search engines

## 📦 Open Source Skill Library

This skill is part of **[China Compliance Skills](https://github.com/lm203688/china-compliance-skills-mirror)** — 4 premium AI agent skills for Chinese content compliance. Star ⭐ the repo to support!
