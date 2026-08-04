---
name: contract-risk-helper
description: "Contract risk helper. Input Chinese or English contract text; identify common risky clauses, classify severity, and suggest negotiation or revision points. Boundary: preliminary risk spotting only, not a lawyer and not formal legal advice."
---
# 合同风险助手 (Contract Risk Helper)

一键扫描合同中的常见风险条款，支持中英文合同，纯本地分析，**不联网、不上传内容**。

⚠️ **免责声明**：本工具仅做常见模式识别，不构成法律建议。重要合同请咨询专业律师。

## 🚀 三步上手 (First Success Path)

**Step 1**: 复制一段合同文本  
**Step 2**: 粘贴给我，说"帮我扫描合同风险"  
**Step 3**: 获得按严重程度分类的风险报告 + 修改建议

## 📋 Sample Prompts

### 示例 1：中文劳动合同
**输入**：
```
请帮我扫描这份合同的风险条款：

甲方与乙方签订劳动合同，期限三年。本合同到期后自动续签一年，除非任一方提前 180 天书面通知不续签。
乙方在工作期间完成的所有工作成果、发明创造、知识产权均归甲方所有。乙方对工作中可能给甲方造成的任何损失承担无限赔偿责任。
```

**输出**：
```
## 合同风险扫描结果

共发现 4 个风险项

### 🔴 严重 (2)

- [终止条款] 自动续约条款 — 合同在无主动决策下自动延长
  → 建议：增加续约前 30-60 天书面确认要求，添加不续约退出条款

- [责任条款] 无限赔偿责任 — 无赔偿金额上限
  → 建议：协商增加赔偿上限（如 12 个月服务费或合同总额的 1-2 倍）

### 🟡 警告 (1)

- [知识产权] 全部知识产权归属甲方 — 可能包含乙方背景知识产权
  → 建议：限定为"本项目范围内产生的成果"，保留乙方背景知识产权

### 🟢 提醒 (1)

- [终止条款] 180 天通知期过长
  → 建议：协商缩短至 30-60 天
```

### 示例 2：英文服务协议
**输入**：`scan this service agreement for risks: The Client shall indemnify and hold harmless the Service Provider against any and all claims arising from this agreement. This agreement automatically renews for successive one-year terms. Payment is due net 90 days from invoice.`

**输出**：
```
## Contract Risk Scan Results

Found 3 risk items

### 🔴 Critical (2)
- [Liability] Broad indemnification — one-sided, no carve-outs
  → Limit to direct damages caused by indemnifying party
- [Termination] Automatic renewal without active decision
  → Add 30-60 day notice + opt-out clause

### 🟡 Warning (1)
- [Payment] Net 90 payment terms — extended cash flow impact
  → Negotiate net 30 terms or early payment discount
```

### 示例 3：NDA 保密协议
**输入**：`检查这份保密协议：双方在合同终止后仍负有永久保密义务。任何一方披露的"所有信息"均视为保密信息。`

**输出**：
```
## 合同风险扫描结果

共发现 2 个风险项

### 🟡 警告 (2)
- [保密条款] 永久保密义务 — 无期限限制，管理成本高
  → 建议：保密期限限制为合同终止后 3-5 年
- [保密条款] 保密信息定义过宽 — "所有信息"无例外
  → 建议：增加例外条款（已公开信息、独立开发信息等）
```

## 触发关键词

合同风险 / 合同审查 / 条款风险 / 帮我看合同 / 合同检查 / 扫描合同 / contract risk / contract review

## 支持的风险类别

| 严重度 | 类别 | 示例模式 |
|--------|------|----------|
| 🔴 严重 | 责任条款 | 无限责任 / unlimited liability |
| 🔴 严重 | 终止条款 | 自动续约、无任意终止权 |
| 🔴 严重 | 争议解决 | 不平等管辖 / unfair venue |
| 🟡 警告 | 付款条款 | Net 60+、无逾期罚则 |
| 🟡 警告 | 知识产权 | 职务作品无限制、宽泛的知识产权转让 |
| 🟡 警告 | 保密条款 | 永久保密、定义过宽 |
| 🟡 警告 | 终止条款 | 过长通知期、高额提前终止费 |
| 🟢 提醒 | 服务交付 | 范围模糊、无 SLA、无验收标准 |

完整风险模式库：`references/common-risks.md`

## 工作方式

- **纯本地匹配**：基于正则表达式模式库在本地进行文本匹配
- **不联网**：无外部 API 调用
- **不上传**：合同内容不离开本地环境
- **不存储**：不保存或传输合同文本
- **不执行命令**：纯只读分析

## Clean Scan Evidence

✅ 无网络调用 | ✅ 无凭据访问 | ✅ 无 exec | ✅ 纯只读 | ✅ 本地模式匹配


## P1 Legal Boundary

This skill provides preliminary legal information, risk spotting, and document structure only. It is not a lawyer, does not create an attorney-client relationship, and does not replace formal advice from a qualified lawyer who has reviewed the full facts and current local rules.
