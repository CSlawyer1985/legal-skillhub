---
name: invoice-contract-extract
description: >
  发票与合同数据提取技能。读取 PDF/图片格式的发票、收据、合同文件，
  自动提取关键字段（金额、日期、供应商、条款、签字方），
  输出结构化 JSON 数据和可读报告。
  适用于财务团队、法务团队、运营自动化场景。
version: 1.0.0
author: AgentSkills Factory
tags:
  - data-extraction
  - invoice
  - contract
  - ocr
  - finance
  - automation
platforms:
  - claude-code
  - cursor
  - codex-cli
  - openclaw
license: commercial
price: 49
---

# 发票与合同数据提取

## 这个技能做什么

读取发票、收据、合同文件，自动提取结构化数据：

1. **发票/收据提取**：供应商、金额、税额、日期、明细行项目
2. **合同提取**：合同方、生效日期、到期日、金额、关键条款、签字信息
3. **数据校验**：金额计算核对、日期合理性检查
4. **结构化输出**：JSON 格式 + 人类可读报告
5. **批量处理**：支持一次处理多个文件

## 触发条件

- 提到"发票""invoice""收据""receipt""合同""contract""提取""extract"
- 使用 `/extract-invoice` 或 `/extract-contract` 命令
- 提供PDF/图片文件并要求提取数据

**示例**：
- "提取这个发票的信息：invoice.pdf"
- "/extract-invoice ./receipts/"
- "从这个合同里提取关键条款"

## 工作流

### 步骤 1：确认输入

必需信息：
- 文件路径（PDF/图片）或文件目录（批量）

可选信息：
- 文件类型（发票/收据/合同，默认自动检测）
- 输出格式（JSON/报告/两者，默认两者）
- 特定字段需求（如"只提取金额和日期"）

### 步骤 2：文件读取与检测

读取文件内容：
- PDF 文件：使用 Read 工具读取（支持PDF）
- 图片文件：使用 Read 工具读取（支持图片OCR）
- 判断文件类型：发票/收据/合同

### 步骤 3：数据提取

#### 3.1 发票/收据提取

**提取字段**：

| 字段 | 说明 | 必填 |
|------|------|:----:|
| 发票编号 | Invoice Number | ✅ |
| 开票日期 | Issue Date | ✅ |
| 到期日期 | Due Date | ⬜ |
| 供应商名称 | Vendor/Supplier Name | ✅ |
| 供应商地址 | Vendor Address | ⬜ |
| 供应商税号 | Vendor Tax ID | ⬜ |
| 客户名称 | Bill To | ✅ |
| 客户地址 | Customer Address | ⬜ |
| 明细行项目 | Line Items（描述+数量+单价+金额） | ✅ |
| 小计 | Subtotal | ✅ |
| 税率 | Tax Rate | ⬜ |
| 税额 | Tax Amount | ✅ |
| 总计 | Total | ✅ |
| 货币 | Currency | ✅ |
| 支付条款 | Payment Terms | ⬜ |
| 备注 | Notes | ⬜ |

#### 3.2 合同提取

**提取字段**：

| 字段 | 说明 | 必填 |
|------|------|:----:|
| 合同标题 | Contract Title | ✅ |
| 合同编号 | Contract Number | ⬜ |
| 合同类型 | Type（NDA/服务/采购/雇佣等） | ✅ |
| 生效日期 | Effective Date | ✅ |
| 到期日期 | Expiration Date | ✅ |
| 甲方 | Party A（名称+地址） | ✅ |
| 乙方 | Party B（名称+地址） | ✅ |
| 合同金额 | Contract Value | ⬜ |
| 付款条款 | Payment Terms | ⬜ |
| 关键义务 | Key Obligations（双方） | ✅ |
| 终止条款 | Termination Clause | ✅ |
| 保密条款 | Confidentiality | ⬜ |
| 争议解决 | Dispute Resolution | ⬜ |
| 签字方 | Signatories（姓名+职位+日期） | ✅ |
| 签字日期 | Signature Date | ✅ |

### 步骤 4：数据校验

提取后执行以下校验：

**发票校验**：
- [ ] 小计 + 税额 = 总计？（误差<0.01）
- [ ] 明细行项目金额之和 = 小计？
- [ ] 日期格式合理？（开票日期 ≤ 到期日期）
- [ ] 金额为正数？
- [ ] 货币符号与金额匹配？

**合同校验**：
- [ ] 生效日期 ≤ 到期日期？
- [ ] 甲乙方信息完整？
- [ ] 关键条款是否有明显缺失？
- [ ] 签字信息完整？

校验不通过的字段，标注 ⚠️ 并说明问题。

### 步骤 5：输出

#### 输出 1：JSON 结构化数据

```json
{
  "file": "invoice_001.pdf",
  "type": "invoice",
  "extractedAt": "2026-07-22",
  "fields": {
    "invoiceNumber": "INV-2026-0042",
    "issueDate": "2026-07-15",
    "dueDate": "2026-08-15",
    "vendor": {
      "name": "Acme Corp",
      "address": "123 Main St, San Francisco, CA",
      "taxId": "US123456789"
    },
    "customer": {
      "name": "TechStart Inc"
    },
    "lineItems": [
      {
        "description": "Consulting service - July",
        "quantity": 40,
        "unitPrice": 150.00,
        "amount": 6000.00
      }
    ],
    "subtotal": 6000.00,
    "taxRate": 0.0875,
    "taxAmount": 525.00,
    "total": 6525.00,
    "currency": "USD"
  },
  "validation": {
    "passed": true,
    "warnings": []
  }
}
```

#### 输出 2：可读报告

---

## 📄 数据提取报告

**文件**：{文件名}
**类型**：{发票/收据/合同}
**提取日期**：{日期}

### 提取结果

| 字段 | 值 | 状态 |
|------|-----|:----:|
| 发票编号 | {值} | ✅/⚠️ |
| 开票日期 | {值} | ✅ |
| 供应商 | {值} | ✅ |
| 客户 | {值} | ✅ |
| 总计 | {值} | ✅ |

### 明细行项目
| # | 描述 | 数量 | 单价 | 金额 |
|---|------|------|------|------|
| 1 | {描述} | {数量} | {单价} | {金额} |

### 校验结果
- [✅] 小计 + 税额 = 总计
- [✅] 明细金额之和 = 小计
- [⚠️] 到期日期为空（可能需要人工确认）

### 原文对照
{关键区域的原文截图或引用，方便人工核对}

---

### 步骤 6：批量处理模式

如果输入是目录，对每个文件：
1. 逐个提取
2. 汇总到一张表格
3. 输出合并的 JSON 数组
4. 标注提取失败或校验不通过的文件

**批量汇总表**：

| 文件名 | 类型 | 供应商/甲方 | 金额 | 日期 | 校验 |
|--------|------|-----------|------|------|:----:|
| {文件1} | 发票 | {名称} | {金额} | {日期} | ✅ |
| {文件2} | 合同 | {名称} | {金额} | {日期} | ⚠️ |

### 步骤 7：质量自检

- [ ] 所有必填字段已提取或标注"未找到"
- [ ] 金额校验已执行
- [ ] 日期校验已执行
- [ ] JSON 格式有效
- [ ] 可读报告包含原文对照
- [ ] 批量模式下汇总表完整

## 使用示例

**示例 1：单发票**
> 提取 invoice_2026_07.pdf 的数据

**示例 2：批量**
> /extract-invoice ./receipts/ --format=json

**示例 3：合同**
> 从这份合同里提取关键条款和签字信息：contract.pdf

## 注意事项

1. **准确性**：金额和日期是关键字段，如有不确定标注"需人工确认"
2. **多语言**：支持中英文发票和合同
3. **多格式**：PDF、PNG、JPG 均可
4. **隐私**：提取的数据不发送到外部，本地处理
5. **不替代专业判断**：合同条款解读仅供参考，重要合同需法务审核

## 技能边界

不做：
- 不做财务记账（只提取数据，不入账）
- 不做法律建议
- 不验证发票真伪
- 不处理加密/密码保护的文件（提示用户提供解密版本）

---

*AgentSkills Factory 出品 | 版本 1.0.0 | 适用于 Claude Code / Cursor / Codex CLI / OpenClaw*
