---
name: 销售合同审核
description: 本Skill用于对销售合同进行专业审核，根据输入的合同文本，按照"合同基本信息->潜在风险点->修改建议->参考条款->审核结论"的格式输出HTML格式的销售合同审核报告。适用于企业法务人员、业务人员审核销售合同场景。审核视角为乙方（卖方）视角，从乙方利益出发识别风险。
---

# 销售合同审核Skill

## 一致性保证（重要！）

为确保同一份合同每次审核结果一致，本Skill采用以下固化机制：

### 1. 固化文本提取脚本

使用 `references/extract_contract.py` 脚本标准化提取合同文本：

- **忽略修订痕迹**：自动过滤Track Changes的插入/删除内容
- **标准化处理**：统一空白字符、去除零宽字符、标准化引号
- **段落顺序固定**：按文档顺序提取，不做排序或重组
- **内容哈希验证**：输出包含SHA256哈希值，可验证文本一致性

### 2. 输入规范要求

提交审核的合同必须满足以下条件：

| 要求 | 说明 |
|------|------|
| 格式 | 支持 .docx, .pdf, .txt, .md |
| 编码 | UTF-8 |
| 修订痕迹 | **禁止**有Track Changes痕迹的文档 |
| 加密 | 不支持加密的文档 |
| 扫描件 | PDF必须是可搜索文本，OCR扫描件不支持 |

### 3. 文本提取命令

```bash
# 使用固化脚本提取文本
python references/extract_contract.py <合同文件路径>

# 输出示例：
{
  "file_name": "销售合同.docx",
  "content_hash": "a1b2c3d4...",  # 可用于验证一致性
  "paragraph_count": 45,
  "text": "合同正文..."
}
```

### 4. 一致性验证

每次提取后，检查 `content_hash` 值：
- **相同hash = 相同文本 = 一致审核结果**
- 如果hash变化，说明文本被修改或提取方式不同

---

## 技能概述

本Skill用于对销售合同进行专业审核。**审核视角为乙方（卖方）视角**，从乙方利益出发检查合同中的潜在风险。

当用户提交合同文本进行审核时，输出**HTML格式**的结构化审核报告，包括：

1. **合同基本信息** - 提取合同的核心要素（表格形式）
2. **潜在风险点** - 识别合同中对乙方不利的风险点
3. **修改建议** - 针对风险点提供具体的修改建议
4. **参考条款** - 提供可参考的标准条款示例
5. **审核结论** - 从乙方视角整体评价合同

## 审查总体目标（优先级顺序）

审查销售合同时，应依次判断以下四个层面（从乙方视角）：

1. **合法性**：条款是否违反《民法典》强制性规定？（最高优先级）
2. **可执行性**：条款在司法实践中是否可能被认定无效或不被支持？
3. **风险可控性**：乙方与甲方的权利义务是否实质对等？是否存在对乙方不利的单方陷阱？
4. **商业目标匹配**：条款是否妨碍乙方正常履约和回款？


## 审核要点参考

审核合同时，详细参考 `references/audit_points.md` 中的审核要点。

## 使用方法

### 步骤一：提取合同文本（必须）

**必须使用固化脚本提取文本**，确保一致性：

```bash
# 在skill目录下执行
python references/extract_contract.py <合同文件路径>
```

提取后的JSON输出中，`text`字段即为标准化后的合同文本。

### 步骤二：审核合同

1. 使用提取的标准化文本作为输入
2. 加载 `references/audit_points.md` 作为审核依据
3. 从**乙方（卖方）视角**按照四个层面优先级进行审查：
   - 首先检查合法性（民法典强制性规定）
   - 然后检查可执行性
   - 再检查风险可控性（权利义务对等性，特别关注对乙方不利的条款）
   - 最后检查商业目标匹配度
4. 生成HTML格式的审核报告

### 一致性验证

- 比对 `content_hash` 值确认文本未被修改
- 相同hash值必然产生相同审核结果

## HTML输出格式要求（已固化，与参考报告完全一致）

> **核心原则**：生成的HTML报告必须完全匹配 `references/report_template.html` 的结构和样式。CSS必须**内联**在 `<style>` 标签中，确保报告文件自包含、可独立打开。

### 1. 必须使用的固化CSS（完整内联）

以下CSS已固化，每次生成报告时必须**原样复制**到 `<style>` 标签中，**不得修改任何值**：

```css
:root{--primary:#2563eb;--primary-light:#3b82f6;--text-primary:#1f2937;--text-secondary:#6b7280;--bg-light:#f9fafb;--border:#e5e7eb;--risk-high:#dc2626;--risk-high-bg:#fef2f2;--risk-medium:#f59e0b;--risk-medium-bg:#fffbeb;--risk-low:#10b981;--risk-low-bg:#ecfdf5;--adv-bg:#eff6ff;--adv-border:#3b82f6;--white:#fff;--shadow:0 1px 3px rgba(0,0,0,0.1)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;font-size:14px;line-height:1.7;color:var(--text-primary);background:#f3f4f6;padding:20px}
.report-container{max-width:900px;margin:0 auto;background:var(--white);border-radius:8px;box-shadow:var(--shadow);overflow:hidden}
.report-header{background:linear-gradient(135deg,var(--primary),var(--primary-light));color:white;padding:30px 40px;text-align:center}
.report-header h1{font-size:28px;font-weight:600;margin-bottom:15px;letter-spacing:2px}
.report-meta{display:flex;justify-content:center;gap:30px;font-size:13px;opacity:0.9;flex-wrap:wrap}
.report-content{padding:30px 40px}
section{margin-bottom:32px}
section h2{font-size:18px;font-weight:600;color:var(--text-primary);padding-bottom:10px;border-bottom:2px solid var(--primary);margin-bottom:20px}
.summary-table{width:100%;border-collapse:collapse;font-size:13px}
.summary-table th,.summary-table td{padding:10px 14px;text-align:left;border:1px solid var(--border)}
.summary-table th{background:var(--primary);color:white;font-weight:600;text-align:center;font-size:12px}
.summary-table tbody tr:nth-child(odd){background:var(--bg-light)}
.summary-table tbody tr:hover{background:#f0f7ff}
.summary-table td{color:var(--text-secondary)}
.summary-table td:first-child{width:13%}
.summary-table td:nth-child(2){width:14%}
.risk-item{padding:14px 20px;margin-bottom:14px;border-radius:6px;border-left:4px solid var(--risk-high);background:var(--risk-high-bg)}
.risk-item.medium{background:var(--risk-medium-bg);border-color:var(--risk-medium)}
.risk-item.low{background:var(--risk-low-bg);border-color:var(--risk-low)}
.risk-header{display:flex;align-items:center;gap:10px;margin-bottom:6px;flex-wrap:wrap}
.risk-level{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;text-transform:uppercase;background:var(--risk-high);color:white}
.risk-level.medium{background:var(--risk-medium);color:white}
.risk-level.low{background:var(--risk-low);color:white}
.risk-title{font-weight:600;color:var(--text-primary);font-size:14px}
.risk-clause{font-size:11px;color:#8b5cf6;margin-left:6px;white-space:nowrap}
.risk-dimension{font-size:11px;color:var(--text-secondary);margin-left:auto}
.risk-description{color:var(--text-secondary);font-size:13px;margin-top:4px}
.suggestion-item{padding:14px 20px;margin-bottom:14px;background:var(--bg-light);border-radius:6px;border-left:3px solid var(--primary)}
.suggestion-header{font-weight:600;color:var(--text-primary);margin-bottom:6px;font-size:14px}
.suggestion-content{color:var(--text-secondary);font-size:13px}
.suggestion-content ul{margin-left:18px;margin-top:4px}
.suggestion-content li{margin-bottom:3px}
.advantage-item{padding:9px 14px;margin-bottom:6px;background:var(--adv-bg);border-radius:4px;border-left:3px solid var(--adv-border);font-size:13px;color:var(--text-secondary)}
.advantage-item strong{color:var(--primary)}
.note-item{padding:9px 14px;margin-bottom:6px;background:#fefce8;border-radius:4px;border-left:3px solid #eab308;font-size:13px;color:var(--text-secondary)}
.clause-item{margin-bottom:18px;border:1px solid var(--border);border-radius:6px;overflow:hidden}
.clause-header{background:var(--bg-light);padding:11px 18px;font-weight:600;font-size:13px;border-bottom:1px solid var(--border)}
.clause-content{padding:16px 18px;background:white;font-size:13px;line-height:1.8}
.clause-content pre{white-space:pre-wrap;word-wrap:break-word;background:#f8f9fa;padding:14px;border-radius:4px;overflow-x:auto;font-size:12px}
.conclusion-box{background:var(--bg-light);border-radius:8px;padding:20px;border:1px solid var(--border)}
.conclusion-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid var(--border)}
.conclusion-label{font-size:16px;font-weight:600;color:var(--text-primary)}
.conclusion-rating{padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600}
.conclusion-rating.low{background:var(--risk-low-bg);color:var(--risk-low)}
.conclusion-rating.medium{background:var(--risk-medium-bg);color:var(--risk-medium)}
.conclusion-rating.high{background:var(--risk-high-bg);color:var(--risk-high)}
.conclusion-content{color:var(--text-secondary);font-size:14px;line-height:1.8;margin-bottom:18px}
.conclusion-content p{margin-bottom:10px}
.conclusion-content ul{margin-left:18px}
.conclusion-content li{margin-bottom:4px}
.conclusion-signature{display:flex;gap:30px;padding-top:14px;border-top:1px dashed var(--border)}
.signature-item{display:flex;align-items:center;gap:8px}
.signature-label{font-size:12px;color:var(--text-secondary)}
.signature-value{font-weight:600;color:var(--text-primary);font-size:13px}
.report-footer{background:var(--bg-light);padding:18px 40px;text-align:center;color:var(--text-secondary);font-size:11px;border-top:1px solid var(--border)}
@media print{body{background:white;padding:0}.report-container{box-shadow:none}.report-header{-webkit-print-color-adjust:exact;print-color-adjust:exact}.risk-item,.risk-level{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
@media(max-width:768px){.report-header{padding:20px}.report-meta{flex-direction:column;gap:8px}.report-content{padding:20px}.summary-table{font-size:11px}.summary-table th,.summary-table td{padding:7px 8px}.conclusion-signature{flex-direction:column;gap:8px}}
```

### 2. 必须使用的固化DOM结构

以下HTML DOM结构已固化，每次生成报告时必须**严格遵循**，**不得添加或删除任何class属性**。变量 `{{...}}` 替换为实际内容。

```html
<body>
    <div class="report-container">

        <header class="report-header">
            <h1>销售合同审核报告</h1>
            <div class="report-meta">
                <span>审核日期：{{audit_date}}</span>
                <span>合同名称：{{contract_name}}</span>
                <span>审核视角：乙方（卖方）</span>
            </div>
        </header>

        <div class="report-content">

            <!-- 注意：section 标签无 class 属性 -->
            
            <!-- 一、合同要点总结 -->
            <section>
                <h2>一、合同要点总结</h2>
                <table class="summary-table">...</table>
            </section>

            <!-- 二、潜在风险点 -->
            <section>
                <h2>二、潜在风险点（仅列出对乙方不利的条款）</h2>
                <!-- 风险项 -->
            </section>

            <!-- 三、修改建议 -->
            <section>
                <h2>三、修改建议</h2>
                <!-- 修改建议项 -->
            </section>

            <!-- 四、参考条款 -->
            <section>
                <h2>四、参考条款</h2>
                <!-- 参考条款项 -->
            </section>

            <!-- 五、审核结论 -->
            <section>
                <h2>五、审核结论</h2>
                <div class="conclusion-box">...</div>
            </section>

        </div>

        <footer class="report-footer">
            <p>本报告仅供参考，不构成法律意见。具体合同条款的效力及风险需结合实际情况判断，建议咨询专业律师。</p>
        </footer>

    </div>
</body>
```

### 3. 各模块内容要求（乙方视角）

**3.1 合同要点总结表格**（4列）：

| 类别 | 项目 | 内容 | 乙方视角评价 |
|------|------|------|-------------|
| 合同主体 | 甲方（买方） | [名称] | 留空 |
| 合同主体 | 乙方（卖方） | [名称] | 留空 |
| 合同标的 | 标的名称 | [产品/服务内容] | 留空 |
| 合同金额 | 合同总价 | [金额]，是否含税 | 留空 |
| 付款条件 | 付款方式 | 预付款[X]%+验收款[X]%+质保金[X]% | 有风险时标注，如`style="color:#f59e0b;"` |
| 付款条件 | 付款节点 | [具体时间节点] | 有风险时标注，无风险留空 |
| 付款条件 | 发票要求 | [每个阶段需提供的发票类型和金额] | 付款与发票金额不一致时标注中风险 |
| 合同变更 | 变更原则 | [合同变更程序和审批要求，原文引用] | 有风险时标注 |
| 合同变更 | 变更计价 | [变更时的计价方式和标准，原文引用] | 有风险时标注 |
| 交付安排 | 交付时间 | [期限] | 留空 |
| 交付安排 | 验收期 | [期限及起始条件] | 留空 |
| 质保安排 | 质保期 | [期限及起始条件] | 留空(质保起算日已合并至此行) |
| 合同期限 | 生效条件 | [生效条件] | 留空 |
| 合同期限 | 终止条件 | [终止条件] | 留空 |
| 争议解决 | 管辖约定 | [仲裁/诉讼 + 管辖地] | 非乙方所在地时标注风险 |
| 违约责任 | 甲方违约责任 | [原文引用，包括所有相关条款] | 留空（甲方违约责任重对乙方有利） |
| 违约责任 | 乙方违约责任 | [原文引用，包括所有相关条款] | 有风险时标注 |
| 违约责任 | 发票违约责任 | [原文引用，如：乙方未按期提供发票应承担的责任] | 有风险时标注 |
| 违约责任 | 单边违约风险 | [是否存在单边违约风险的判断结果] | 有风险时标注 |

**3.2 潜在风险点**（每个风险项的HTML结构）：

```html
<div class="risk-item [medium|low]">
    <div class="risk-header">
        <span class="risk-level [medium|low]">[高风险|中风险|低风险]</span>
        <span class="risk-title">[风险标题]</span>
        <span class="risk-clause">[第X条]</span>
        <span class="risk-dimension">[审查维度]</span>
    </div>
    <div class="risk-description">
        [风险详细描述]
    </div>
</div>
```

> **风险等级说明**：
> - **高风险**：使用 `class="risk-item"`（默认红色，不加high类名）
> - **中风险**：使用 `class="risk-item medium"`
> - **低风险**：使用 `class="risk-item low"`
> - 每个风险项必须标注条款位置（`risk-clause`）和审查维度（`risk-dimension`）

**3.3 修改建议**（每个建议项的HTML结构）：

```html
<div class="suggestion-item">
    <div class="suggestion-header">建议N：[简述]（[风险等级] → 对应修改）</div>
    <div class="suggestion-content">
        <ul>
            <li><strong>修改内容：</strong>[具体修改方案]</li>
            <li><strong>备选方案：</strong>[如有]</li>
            <li><strong>法律依据：</strong>[相关法律条款]</li>
        </ul>
    </div>
</div>
```

**3.4 参考条款**（每个条款的HTML结构）：

```html
<div class="clause-item">
    <div class="clause-header">参考条款N：[标题]</div>
    <div class="clause-content">
        <pre>[标准条款文本]</pre>
    </div>
</div>
```

**3.5 审核结论**（完整结构，必须包含以下6个部分）：

```html
<div class="conclusion-box">
    <div class="conclusion-header">
        <span class="conclusion-label">综合风险评级</span>
        <span class="conclusion-rating [low|medium|high]">[低风险|中风险|高风险]</span>
    </div>
    <div class="conclusion-content">
        <p><strong>整体评价：</strong>[从乙方视角的整体评价]</p>

        <p><strong>乙方优势条款（建议保留）：</strong></p>
        <div class="advantage-item"><strong>✓ [优势标题]：</strong>[说明]</div>
        <!-- 可多个 advantage-item -->

        <p><strong>可优化项（N项，均非签约前提）：</strong></p>
        <ul>
            <li><strong>[风险等级]（N项）：</strong>[可优化项说明]</li>
        </ul>

        <p><strong>履约注意事项：</strong></p>
        <div class="note-item"><strong>[注意事项标题]：</strong>[详细说明]</div>
        <!-- 可多个 note-item -->

        <p><strong>签约建议：</strong>[最终建议]</p>
    </div>
    <div class="conclusion-signature">
        <div class="signature-item">
            <span class="signature-label">审核人：</span>
            <span class="signature-value">AI合同审核系统</span>
        </div>
        <div class="signature-item">
            <span class="signature-label">审核日期：</span>
            <span class="signature-value">{{audit_date}}</span>
        </div>
    </div>
</div>
```

### 4. 样式色值速查表

| 元素 | CSS变量/颜色 | 用途 |
|------|-------------|------|
| 主题色 | `--primary: #2563eb` | 标题栏背景、表头、h2底部边框 |
| 标题栏渐变 | `--primary-light: #3b82f6` | 报告头部渐变 |
| 高风险 | `--risk-high: #dc2626` | 红色，高风险标识 |
| 高风险背景 | `--risk-high-bg: #fef2f2` | 淡红背景 |
| 中风险 | `--risk-medium: #f59e0b` | 橙色，中风险标识 |
| 中风险背景 | `--risk-medium-bg: #fffbeb` | 淡黄背景 |
| 低风险 | `--risk-low: #10b981` | 绿色，低风险标识 |
| 低风险背景 | `--risk-low-bg: #ecfdf5` | 淡绿背景 |
| 条款定位 | `#8b5cf6` | 紫色，条款位置标注 |
| 优势项背景 | `--adv-bg: #eff6ff` | 淡蓝背景 |
| 优势项边框 | `--adv-border: #3b82f6` | 蓝色左边框 |
| 注意项背景 | `#fefce8` | 淡黄背景 |
| 注意项边框 | `#eab308` | 黄色左边框 |
| 正文字色 | `--text-primary: #1f2937` | 标题、正文主要颜色 |
| 次要文字 | `--text-secondary: #6b7280` | 描述文字颜色 |
| 字体 | `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto` | 系统字体栈 |

### 5. 固化检查清单

生成报告前必须逐项确认：

- [ ] CSS完全使用第1节中的固化代码，**一字不改**
- [ ] `<section>` 标签**没有任何class属性**
- [ ] 报告头部标题为 "销售合同审核报告"
- [ ] 报告头部包含3个meta项（审核日期、合同名称、审核视角）
- [ ] 五个section标题顺序正确，第二个为"二、潜在风险点（仅列出对乙方不利的条款）"
- [ ] 审核结论包含6个子部分（综合风险评级、整体评价、乙方优势条款、可优化项、履约注意事项、签约建议）
- [ ] 审核结论有签名区域（审核人 + 审核日期）
- [ ] footer使用完整文本："本报告仅供参考，不构成法律意见。具体合同条款的效力及风险需结合实际情况判断，建议咨询专业律师。"
- [ ] 所有颜色使用固化CSS变量，不自定义颜色值
- [ ] 风险等级class正确：高风险无额外类名，中风险=`medium`，低风险=`low`

## 违约责任审核要点（重要补充）

从乙方视角审核违约责任时，必须包含以下内容：

### 1. 违约责任必须从合同全文中总结

审核违约责任时，**必须从合同全文中搜索并引用所有相关条款**，包括但不限于：
- 合同正文中关于违约责任的专门章节（如第7条）
- 合同附件中的违约责任条款（如廉洁协议、安全管理协议中的违约责任）
- 任何涉及违约金、赔偿、解除合同等违约后果的条款

### 2. 发票违约责任必须明确列出

**必须审核并列出以下发票相关违约责任**（从合同原文引用）：

| 发票违约情形 | 违约责任（原文引用） |
|-------------|---------------------|
| 乙方未正常纳税 | 乙方应承担由此给甲方造成的一切损失，包括但不限于未抵扣税额、逾期滞纳金、税款罚金等 |
| 乙方未按期提供发票 | 同上 |
| 乙方提供发票不合规 | 同上 |

**注意**：发票违约责任是乙方责任，属于对乙方不利的风险点，应在违约责任审核中明确列出。

### 3. 合同变更原则（如有）需补充到合同要点总结

如果合同中包含变更原则条款（如合同变更程序、变更审批流程、变更计价方式等），**必须在合同要点总结中补充**：

| 类别 | 项目 | 内容 |
|------|------|------|
| 合同变更 | 变更原则 | [引用合同原文的变更条款，如：需按甲方《深圳市机场（集团）有限公司建设工程变更管理规定》相关程序办理] |
| 合同变更 | 变更计价方式 | [引用合同原文的变更计价方式] |

### 4. 付款与发票金额一致性审核（新增中风险）

**必须审核付款金额与增值税专用发票金额是否一致**：

- **审核要点**：每个付款阶段的付款金额与乙方需提供的增值税专用发票金额是否匹配
- **风险等级**：如果付款金额与发票金额不一致 → **中风险**
- **原因**：付款金额与发票金额不一致可能导致乙方提前垫付税款，或存在税务风险

**示例**：
- 阶段1：合同签订价的50%付款，乙方需提供合同签订价50%的增值税专用发票
- 阶段2：合同签订价的30%付款，乙方需提供合同签订价30%的增值税专用发票
- 阶段3：累计支付至合同结算金额的95%，乙方需提供累计至合同结算金额100%的增值税专用发票

### 5. 单边违约风险判断（重要！）

**必须判断合同是否存在"单边违约风险"**：

| 风险类型 | 判断标准 | 风险等级 |
|---------|---------|---------|
| **甲方违约责任过轻** | 甲方违约（如逾期付款、任意解除合同）无对应违约责任或责任极轻 | 中风险 |
| **乙方违约责任过重** | 乙方违约金比例高于甲方，或乙方违约后果严重于甲方 | 中风险 |
| **单边解除权** | 甲方有权任意解除合同，但乙方无对等解除权 | 高风险 |
| **单边变更权** | 甲方有权单方变更合同内容，但乙方无对等权利 | 中风险 |

**从合同全文中识别单边违约风险的要点**：
1. 对比甲方违约责任条款和乙方违约责任条款的严重程度
2. 检查是否存在"甲方有权...但乙方无权..."的条款
3. 检查违约金的金额/比例是否对等
4. 检查解除合同的条件是否对等

### 6. 双方擅自终止协议的违约责任
   - 甲方擅自终止合同的责任
   - 乙方擅自终止合同的责任
   - 双方责任是否对等

### 7. 赔偿第三方追诉的损失
   - 甲方原因导致第三方追诉的责任承担
   - 乙方原因导致第三方追诉的责任承担

### 8. 商业秘密/BM信息泄露损失赔偿
   - 保密义务和违约责任
   - 信息泄露的赔偿范围

### 9. 知识产权侵权损失
   - 甲方使用乙方产品侵犯第三方知识产权的责任
   - 乙方提供产品侵犯第三方知识产权的责任

## 数字准确性铁律（最高优先级！）

**报告中的所有数字必须从合同原文中直接引用，严禁推断、换算或自行计算。**

### 铁律规则
1. **数字引用原文，不做转换**：合同写"0.4‰"就写"0.4‰"，不要自行转换或简写。
2. **不推断修订痕迹**：合同有修订痕迹（Track Changes）时，删除/插入的内容不能混用。必须确认最终版本的数字。如无法确认，引用能确定的原文表述并标注不确定性。
3. **违约金比例不可自行比对**：引用甲方违约金和乙方违约金时分别引用原文，分析时可指出倍数关系，但原文数字不可改动。

### 禁止行为
- ❌ 看到"万分之四"自行写成"0.4‰"或"0.04%"
- ❌ 从修订痕迹的"万分之一（删除）万分之四（插入）"中自行判断最终版本
- ❌ 将"肆佰伍拾贰万元整"简化为"452万"
- ❌ 将中文数字自行换算为阿拉伯数字


## 乙方主体与付款信息识别规则（重要！）

### 1. 乙方（卖方）识别规则

审核合同时，乙方信息可能以多种形式出现，必须正确识别以下所有格式：

#### 1.1 单一乙方格式
| 格式 | 示例 |
|------|------|
| 受托方（乙方） | 受托方（乙方）：中科星图股份有限公司 |
| 乙方（卖方） | 乙方（卖方）：xxx公司 |
| 供应商 | 供应商：xxx公司 |
| 承包方 | 承包方：xxx公司 |

#### 1.2 联合体乙方格式（重点！）
| 格式 | 示例 |
|------|------|
| 乙方1+乙方2联合体 | 乙方1（联合体牵头单位）：xxx公司、乙方2（联合体成员单位）：xxx公司 |
| 受托方（乙方1）+受托方（乙方2） | 受托方（乙方1）：xxx公司、受托方（乙方2）：xxx公司 |
| 乙方（联合体牵头单位）+乙方（联合体成员单位） | 乙方（联合体牵头单位）：xxx公司、乙方（联合体成员单位）：xxx公司 |

#### 1.3 识别要点
- **必须搜索所有可能的乙方字段名**：受托方、乙方、供应商、承包方、卖方等
- **联合体情况**：需要同时识别"乙方1"和"乙方2"，两者都是乙方主体
- **乙方名称**：必须填写具体的公司名称，不能留空或填写"（合同中未填写）"
- **如果合同中确实没有填写乙方名称**，才标注为"合同中未填写"

### 2. 付款信息提取规则

#### 2.1 付款信息位置
付款信息通常位于合同第3条或"合同价格及支付方式"章节，必须完整提取。

#### 2.2 付款信息整合呈现规则（重要！）

**付款金额、付款比例、付款条件、付款节点必须整合在一起作为"付款方式"呈现，不能分开列为多个项目。**

每个付款阶段应整合呈现为以下格式：
```
① 付款比例（付款金额）：付款条件 + 需提交的材料
```

示例格式：
```
① 30%（1,368,540.00元）：合同签订30日后，需提交"买方收到业主方相应款项证明材料"+发票+设备到货报告
② 40%（1,824,720.00元）：初验完成30日后，需提交"买方收到业主方相应款项证明材料"+初验合格说明
③ 30%（1,368,540.00元）：终验完成30日后，需提交终验合格说明+质保书
```

#### 2.3 数字准确性铁律（必须遵守！）

**所有金额、比例必须与合同原文完全一致，严禁换算或简写：**

| 正确做法 | 错误做法 |
|----------|----------|
| 合同签订价的50% | 50% |
| 人民币4,520,000.00元 | 452万 |
| 累计支付至合同结算金额的95% | 95% |
| 合同结算金额的100% | 100% |
| 增值税专用发票 | 专票 |

- **金额必须精确**：合同写"4,520,000.00元"就不能写成"452万"
- **比例必须完整**：合同写"合同签订价的50%"就不能只写"50%"
- **累计付款必须标注"累计"**：如"累计支付至合同结算金额的95%"
- **币种必须保留**：如"人民币"、"USD"等

#### 2.4 付款信息必须包含的要素
| 要素 | 说明 | 示例 |
|------|------|------|
| 付款阶段 | 付款的阶段序号 | 第1期、第2期、第3期 |
| 付款比例 | 该阶段付款占总价的比例（原文引用） | 合同签订价的50%、累计至合同结算金额的95% |
| 付款金额 | 该阶段实际付款金额（原文引用或计算） | 2,260,000.00元（合同签订价452万元×50%）|
| 付款条件 | 该阶段付款的前提条件 | 完成需求调研、系统深化设计、硬件到货等 |
| 付款节点 | 时间节点/触发条件 | 合同签订后、验收合格后、质保期满后 |
| 发票要求 | 该阶段需要提供的发票类型和金额 | 合同签订价50%的增值税专用发票 |

#### 2.5 付款信息提取示例

**合同原文示例**（第3.7条）：
```
3.7 支付方式及进度：
付款阶段 付款比例 付费方式
1 合同签订价的 50% 完成需求调研、系统深化设计、硬件到货及施工完成，系统完成核心功能上线及进入试运行一阶段。乙方提供付款书面申请和合同签订价 50% 的增值税专用发票并经甲方审核无误后 20 个工作日内支付。
2 合同签订价的 30% 完成系统完成主要的功能开发，试运行一阶段稳定，完成初验。乙方提供付款书面申请和合同签订价 30% 的增值税专用发票并经甲方审核无误后 20 个工作日内支付。
3 累计支付至合同结算金额的 95% 系统功能开发完成，运行二阶段稳定，且终验通过，完成项目结算和资产入固。乙方提供付款书面申请和累计至合同结算金额 100% 的增值税专用发票并经甲方审核无误后 20 个工作日内支付。
4 累计支付至合同结算金额的 100% 系统在质保期内运行正常，在质保期结束后，乙方按合同约定履行完毕全部质保期服务且无任何质量缺陷，没有发生本合同规定的抵扣、扣除质保金的任何情况，乙方提供付款书面申请和等额收据并经甲方审核无误后 20 个工作日内支付。
```

**正确提取结果（整合呈现）**：
```
付款方式：
① 合同签订价的50%（2,260,000.00元）：完成需求调研、系统深化设计、硬件到货及施工完成，系统完成核心功能上线及进入试运行一阶段。乙方提供付款书面申请和合同签订价50%的增值税专用发票并经甲方审核无误后20个工作日内支付。
② 合同签订价的30%（1,356,000.00元）：完成系统主要功能开发，试运行一阶段稳定，完成初验。乙方提供付款书面申请和合同签订价30%的增值税专用发票并经甲方审核无误后20个工作日内支付。
③ 累计支付至合同结算金额的95%：系统功能开发完成，运行二阶段稳定，且终验通过，完成项目结算和资产入固。乙方提供付款书面申请和累计至合同结算金额100%的增值税专用发票并经甲方审核无误后20个工作日内支付。
④ 累计支付至合同结算金额的100%：质保期结束后，乙方履行完毕全部质保期服务且无任何质量缺陷。乙方提供付款书面申请和等额收据并经甲方审核无误后20个工作日内支付。
```

#### 2.6 常见付款信息表述方式
- "预付款"、"进度款"、"验收款"、"尾款"、"质保金"
- "首付"、"第二笔款项"、"第三笔款项"、"最后一笔款项"
- "合同签订后X日内"、"验收合格后X日内"、"终验后X日内"

#### 2.7 禁止行为
- ❌ 不能将"未在合同正文中明确"作为付款方式的描述
- ❌ 不能将"付款节点不明确"作为付款条件的描述
- ❌ 付款金额、比例、条件不能分开列为多个项目
- ❌ 金额不能换算：合同写"4,520,000.00元"不能写成"452万"
- ❌ 比例不能简写：合同写"合同签订价的50%"不能只写"50%"
- ❌ 累计付款不能漏写"累计"：如"累计支付至..."
- ❌ 必须从合同原文中提取具体的付款阶段、比例、条件、金额
- ❌ 如果合同确实没有明确付款信息，才能标注为风险


## 乙方视角风险识别核心原则（关键！）

**"风险"的定义：仅指对乙方（卖方）不利的条款。** 识别风险时必须严格遵循以下原则：

### 什么算乙方风险（必须报告）
| 类型 | 示例 | 理由 |
|------|------|------|
| 乙方义务过重 | 乙方违约金过高、质保期过长 | 损害乙方利益 |
| 乙方权利缺失 | 缺少默示验收条款、无所有权保留 | 乙方缺少保护 |
| 甲方权利过大 | 甲方任意解除权、单方变更权 | 乙方处于被动 |
| 乙方收款障碍 | 背靠背付款、付款节点模糊 | 影响乙方回款 |
| 管辖不利 | 管辖地不在乙方所在地 | 增加维权成本 |

### 什么不算乙方风险（不应报告）
| 类型 | 示例 | 理由 |
|------|------|------|
| 甲方义务过重 | **甲方逾期付款违约金高（如0.8%/日）** | 对乙方有利，有助于保障乙方收款 |
| 甲方权利受限 | 甲方验收期短、甲方不得转授权 | 有利于乙方 |
| 乙方权利充分 | 乙方知识产权保留、乙方可中止服务 | 乙方优势条款 |
| 对乙方有利的不对等 | 付款比例对乙方有利（如70%预付款） | 商业谈判优势 |
| 标准商业惯例 | **合同签字盖章即生效（无需与预付款挂钩）** | 标准商业操作，签署即生效为通行做法 |
| 标准商业惯例 | **验收条款不强制区分初验/终验** | 默示验收条款已覆盖全部验收，无需单独定义终验 |

### 特殊处理：表面对甲方不利但可能影响乙方的情况
- 甲方违约金比例极高（如日千分之八），虽对乙方有利，但属于可执行性层面的注意事项（法院可能调低），应放在**审核结论**中作为"履约注意事项"提醒，**不应列为风险点**
- 司法实践中违约金过高可能被调减的风险，不等于乙方的风险
- **合同签字盖章生效是标准商业惯例**，无需额外挂钩预付款到账，预付款未付乙方也无需开始履约，此非风险

## 注意事项

- **审核视角为乙方（卖方）**，所有风险分析从乙方利益出发，严格遵循上述核心原则
- 合法性审查为最高优先级，任何违反《民法典》强制性规定的条款必须指出
- **甲方违约金高对乙方有利**，不可标记为乙方风险；需注意司法调低可能，但不应列入风险点
- 乙方承担的违约金应控制上限（不超过合同总价20%-30%），超过此限制的乙方违约金才为风险点
- 管辖约定优先选择乙方所在地法院
- **质保期从"交付之日"起算对乙方有利**（锁定质保期限），从"验收合格之日"起算对乙方不利（甲方可拖验收延长乙方义务）
- **合同签字盖章生效为标准商业惯例**，无需与预付款到账挂钩，预付款未付乙方也不必开始履约
- **验收默示条款已覆盖全部验收环节**，无需单独定义初验/终验流程，不应将"缺少终验条款"列为风险
- 首付比例建议30%-50%，避免低首付长周期
- 验收期限必须明确起始条件
- 审核时应结合具体业务场景，不能机械套用条款
- 对于重大风险应明确标注并建议咨询专业律师
- HTML报告需要启动本地服务器预览
