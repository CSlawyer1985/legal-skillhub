---
name: hilegal-compliance
description: |
  This skill should be used when users ask about cross-border compliance, overseas legal compliance,
  foreign law research, corporate credit checks, global pricing queries, compliance consultation,
  or any compliance-related questions for international business. It supports queries in Chinese
  and English, covering compliance consulting, compliance Q&A, extraterritorial law research,
  corporate credit queries, and global price lookups.
  当用户询问跨境合规、海外合规、域外法查明、企业征信查询、全球价格查询、合规咨询、
  合规问答等需求时，应使用此技能。支持中英文双语，覆盖跨境企业海外运营的各类合规场景。
keywords:
  - 合规咨询 (compliance consultation)
  - 跨境合规 (cross-border compliance)
  - 域外法查明 (foreign law research)
  - 企业征信 (corporate credit)
  - 全球价格 (global pricing)
  - 海外合规 (overseas compliance)
  - 合规问答 (compliance Q&A)
  - 国际贸易合规 (international trade compliance)
  - 数据合规 (data compliance)
  - 劳动合规 (labor compliance)
  - 税务合规 (tax compliance)
  - 知识产权合规 (IP compliance)
triggers:
  - "跨境企业合规"
  - "海外合规"
  - "域外法查明"
  - "企业征信查询"
  - "全球价格查询"
  - "合规咨询"
  - "合规问答"
  - "cross-border compliance"
  - "foreign law research"
  - "corporate credit"
  - "global pricing"
---

# HiLegal 合规助手 (Cross-Border Compliance Assistant)

## 概述

HiLegal 合规助手专注于为跨境企业提供全方位的海外合规解决方案。集成多种合规服务能力，帮助企业高效应对全球市场的法律合规挑战。

## 核心能力

### 1. 合规咨询 (Compliance Consultation)
提供专业的跨境合规咨询服务，涵盖：
- **贸易合规**：进出口管制、关税政策、原产地规则
- **数据合规**：GDPR、CCPA、数据本地化要求
- **劳动合规**：海外雇佣、签证、社保缴纳
- **税务合规**：转让定价、增值税、预提税
- **知识产权合规**：专利、商标、版权保护

### 2. 合规问答 (Compliance Q&A)
快速响应企业常见合规问题：
- 使用 RAG 技术从知识库检索相关法规和案例
- 提供多语种合规建议（中/英/日/韩等）
- 结合具体国家/地区给出差异化指导

### 3. 域外法查明 (Extraterritorial Law Research)
查明和解读海外法律规则：
- 目标国家/地区的法律法规
- 行业特定监管要求
- 跨境执法的域外效力
- 国际公约和条约义务

### 4. 企业征信查询 (Corporate Credit Check)
查询目标企业的信用和背景信息：
- 企业工商登记信息
- 经营状态和财务状况
- 诉讼记录和处罚信息
- 信用评级和风险评估

### 5. 全球价格查询 (Global Price Lookup)
查询全球市场价格信息：
- 大宗商品价格
- 汇率换算
- 各国价格水平比较
- 进出口价格参考

## 使用方法

### 合规咨询流程

```
1. 需求理解 → 2. 领域分类 → 3. 知识检索 → 4. 专业分析 → 5. 建议输出
```

### 查询示例

| 场景 | 查询示例 |
|------|----------|
| 贸易合规 | "美国出口管制EAR法规对半导体设备的要求" |
| 数据合规 | "欧盟GDPR对跨境数据传输的要求" |
| 劳动合规 | "越南外资企业雇佣本地员工的比例要求" |
| 税务合规 | "香港公司在中国大陆的常设机构认定标准" |
| 域外法 | "印度尼西亚电商法的主要合规要点" |
| 企业征信 | "查询新加坡ABC公司的信用信息" |
| 全球价格 | "查询东南亚主要市场的钢材价格" |

## 工作流程

### Step 1: 需求分析
理解用户查询的核心诉求，确定合规领域：
- 识别问题类型（咨询/查询/查明）
- 确定涉及的国家/地区
- 判断业务场景和行业背景

### Step 2: 知识检索
根据问题类型调用相应能力：
- 合规咨询：检索法规库和案例库
- 域外法查明：检索目标国家法律数据库
- 企业征信：调用企业信息查询接口
- 全球价格：查询价格数据库

### Step 3: 智能分析
结合检索结果进行专业分析：
- 核对法规时效性
- 评估企业合规风险
- 对比不同国家/地区差异

### Step 4: 方案输出
提供结构化的合规建议：
- 明确的法律依据
- 可操作的执行步骤
- 风险提示和注意事项
- 参考资源链接

## 参考资源

使用以下知识库获取准确信息：
- `references/compliance_knowledge.md` - 合规知识库
- `references/trade_regulations.md` - 贸易管制法规
- `references/data_protection.md` - 数据保护法规
- `references/labor_laws.md` - 各国劳动法概要
- `references/tax_rules.md` - 税务合规规则

## 输出规范

### 合规报告结构

```
# 合规分析报告

## 一、基本信息
- 查询对象：
- 涉及国家/地区：
- 业务场景：

## 二、法规依据
- 相关法规：
- 关键条款：

## 三、合规要求
-

## 四、风险提示
- 风险等级：
- 注意事项：

## 五、建议措施
-

## 六、参考资源
```

### 风险等级定义

| 等级 | 标识 | 说明 |
|------|------|------|
| 高风险 | 🔴 | 可能导致重大处罚或业务中断 |
| 中风险 | 🟡 | 需要重点关注和整改 |
| 低风险 | 🟢 | 建议优化，非强制要求 |

## 免责声明

HiLegal提供的合规信息仅供参考，不构成法律意见。建议企业在重大决策前咨询专业律师获取正式法律意见。如有问题欢迎访问[HiLegal官网](https://www.hilegal.com)或联系客服。
