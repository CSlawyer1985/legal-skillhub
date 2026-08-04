---
name: 采购合同审核
description: 本Skill用于对采购合同进行专业审核，根据输入的合同文本，按照"合同基本信息->潜在风险点->修改建议->参考条款->审核结论"的格式输出HTML格式的采购合同审核报告。适用于企业法务人员、采购人员审核采购合同场景。审核视角为甲方（采购方/买方）视角，从甲方利益出发识别风险。
---

# 采购合同审核Skill

## 一致性保证（重要！）

为确保同一份合同每次审核结果一致，本Skill采用以下固化机制：

### 1. 固化文本提取脚本（v2 纯标准库）

使用 `references/extract_contract.py` 脚本标准化提取合同文本：

- **零外部依赖**：仅使用 Python 标准库（`zipfile` + `xml.etree.ElementTree`），无需 `pip install`
- **忽略修订痕迹**：自动过滤Track Changes的插入/删除内容
- **表格提取**：支持提取合同中的表格内容
- **标准化处理**：统一空白字符、去除零宽字符、标准化引号
- **段落顺序固定**：按文档顺序提取，不做排序或重组
- **内容哈希验证**：输出包含SHA256哈希值，可验证文本一致性
- **环境要求**：仅需 Python 3.7+

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
# 使用固化脚本提取文本（零依赖，直接运行）
python references/extract_contract.py <合同文件路径>

# 输出示例：
{
  "file_name": "采购合同.docx",
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

本Skill用于对采购合同进行专业审核。**审核视角为甲方（采购方/买方）视角**，从甲方利益出发检查合同中的潜在风险。

当用户提交合同文本进行审核时，输出**HTML格式**的结构化审核报告，包括：

1. **合同基本信息** - 提取合同的核心要素（表格形式）
2. **潜在风险点** - 识别合同中对甲方不利的风险点
3. **修改建议** - 针对风险点提供具体的修改建议
4. **参考条款** - 提供可参考的标准条款示例
5. **审核结论** - 从甲方视角整体评价合同

## 采购合同类型识别（审核第一步，必须执行！）

在正式审核合同前，**必须首先识别合同所属的采购类型**，不同类型适用不同的审核规则和法律依据。

### 采购类型判断标准

| 采购类型 | 判断关键词 | 典型特征 | 主要法律依据 |
|---------|-----------|---------|------------|
| **货物类** | 采购、购买、供货、设备、材料、产品、硬件、软件许可 | 标的为有形物品或标准化软件产品，关注交付、验收、所有权转移 | 《民法典》合同编买卖合同、《产品质量法》、《政府采购法》 |
| **工程类** | 施工、建设、安装、装修、改造、EPC、总承包、分包 | 涉及不动产建设或大型设备安装，关注工期、质量、安全、农民工工资、履约保函 | 《民法典》合同编建设工程合同、《招标投标法》、《建筑法》、《建设工程质量管理条例》、《保障农民工工资支付条例》 |
| **服务类** | 技术服务、咨询服务、开发、设计、运维、外包、培训 | 标的为无形劳务或智力成果，关注服务标准、验收方式、知识产权、人员资质 | 《民法典》合同编技术服务合同/委托合同、《政府采购法》 |

### 类型判断流程

1. **优先匹配工程类**：合同中出现"施工""建设""装修""EPC""总承包"等关键词 → 工程类
2. **其次匹配服务类**：合同中出现"技术服务""咨询""开发""设计""运维""外包"且无实物交付 → 服务类
3. **默认货物类**：以实物交付为主，含明确的设备清单/材料清单 → 货物类
4. **混合类型**：合同同时包含货物+安装服务 → 按主给付义务判断，通常货物附带安装仍为货物类；工程中包含材料采购仍为工程类

### 识别结果要求

审核报告中**必须在"合同要点总结"表格最前面增加"采购类型"行**，标注类型及判断依据。

---

## 审查总体目标（优先级顺序）

审查采购合同时，应依次判断以下四个层面（从甲方视角）：

1. **合法性**：条款是否违反《民法典》《招标投标法》《政府采购法》《建筑法》《产品质量法》等强制性规定？（最高优先级）
2. **可执行性**：条款在司法实践中是否可能被认定无效或不被支持？
3. **风险可控性**：甲方与乙方的权利义务是否实质对等？是否存在对甲方不利的单方陷阱？
4. **商业目标匹配**：条款是否保障甲方按时按质获得合格产品/服务？


## 审核要点参考

审核合同时，详细参考 `references/audit_points.md` 中的审核要点。

**新增审核要点（来源：业务采购合同审核要点-20260611.docx）**：

1. **合同主体**：统一社会信用代码核查、供应商成立1年以上、禁止引用已废止《合同法》
2. **签署地点**：精确至县级市/区级别
3. **运输风险划分**：风险转移时点为"送达验收合格后"
4. **验收规则**：两段时限（收货后验收期+质量异议期）、验收凭证效力说明、质保期从验收合格日起算
5. **报价及付款**：先货后款、分3-4期付款、保留质保金（5%-10%）
6. **发票开具细节**：完整开票主体信息、明确发票类型
7. **审减条款**：政府投资项目同比例核减约定
8. **违约责任**：分情形违约金、损失赔偿范围、单方解除权、瑕疵补救、第三方损失、违约金抵扣
9. **知识产权**：成果归属甲方、侵权责任兜底
10. **商业保密**：完整商业秘密范围定义、保密期限≥2年
11. **争议解决**：二选一约定、禁止仲裁+诉讼同时约定

## 使用方法

### 步骤一：提取合同文本（必须）

**必须使用固化脚本提取文本**，确保一致性。脚本基于纯标准库，无需安装任何依赖：

```bash
# 在skill目录下执行（Python 3.7+ 即可运行）
python references/extract_contract.py <合同文件路径>
```

提取后的JSON输出中，`text`字段即为标准化后的合同文本。

### 步骤二：审核合同

1. 使用提取的标准化文本作为输入
2. **第一步：识别采购类型**（必须最先执行！）：
   - 根据合同关键词判断属于货物类/工程类/服务类/混合类
   - 在审核报告中标注采购类型及判断依据
3. 加载 `references/audit_points.md` 作为审核依据
4. **根据采购类型加载对应的分类审核规则**（audit_points.md中的对应章节）：
   - 货物类：重点关注交付验收、所有权转移、产品质量、运输保险
   - 工程类：重点关注工期质量、履约保函、安全生产、农民工工资、竣工验收
   - 服务类：重点关注SLA标准、知识产权归属、人员资质、数据安全
5. 从**甲方（采购方/买方）视角**按照四个层面优先级进行审查：
   - 首先检查合法性（民法典、招标投标法、政府采购法、建筑法、产品质量法等强制性规定）
   - 然后检查可执行性
   - 再检查风险可控性（权利义务对等性，特别关注对甲方不利的条款）
   - 最后检查商业目标匹配度
6. 生成HTML格式的审核报告

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
            <h1>采购合同审核报告</h1>
            <div class="report-meta">
                <span>审核日期：{{audit_date}}</span>
                <span>合同名称：{{contract_name}}</span>
                <span>采购类型：{{contract_type}}</span>
                <span>审核视角：甲方（采购方）</span>
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
                <h2>二、潜在风险点（仅列出对甲方不利的条款）</h2>
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

### 3. 各模块内容要求（甲方视角）

**3.1 合同要点总结表格**（4列）：

> **重要**：
> 1. 表格最前面必须增加"采购类型"行，标注类型及判断依据。
> 2. **合同变更为可选行**：只有合同中包含明确的变更条款（变更程序、变更计价等）时，才展示"合同变更"行；合同无变更条款时，**不展示该行**。

| 类别 | 项目 | 内容 | 甲方视角评价 |
|------|------|------|-------------||
| **采购类型** | **合同类型** | [货物类/工程类/服务类/混合类] | 标注判断依据关键词 |
| 合同主体 | 甲方（买方） | [名称+统一社会信用代码] | 留空 |
| 合同主体 | 乙方（卖方/承包方/服务方） | [名称+统一社会信用代码] | 有风险时标注（如资质不足、成立不足1年、涉诉等） |
| 合同主体 | 签署地点 | [精确至县级市/区] | 模糊时标注风险 |
| 合同标的 | 标的名称 | [产品/服务/工程内容] | 规格是否唯一可量化，模糊则标注风险 |
| 合同金额 | 合同总价 | [金额]，是否含税、含运输费 | 留空 |
| 付款条件 | 付款方式 | 先货后款，分3-4期：预付款[X]%+到货款[X]%+验收款[X]%+质保金[X]% | 预付款比例过高时标注，如`style="color:#f59e0b;"` |
| 付款条件 | 付款节点 | [具体时间节点] | 付款与进度不匹配时标注风险 |
| 付款条件 | 发票要求 | [每个阶段需提供的发票类型、金额、开票主体信息] | 发票信息不完整或金额不一致时标注风险 |
| {{change_clause}} | {{change_clause}} | {{change_clause}} | {{change_clause}} |
| 交付安排 | 交付时间 | [期限] | 交付时间不明确时标注风险 |
| 交付安排 | 验收规则 | 两段时限：收货后[X]日内验收+质量异议期[X]日 | 未约定两段时限时标注高风险 |
| 交付安排 | 风险转移 | [风险转移时点：送达验收合格后/签收时/其他] | 未约定或约定不利时标注风险 |
| 质保安排 | 质保期 | [期限及起始条件] | 质保期过短或起算点不合理时标注风险 |
| **履约担保** | **履约保证金/保函** | [金额/比例及退还条件] | 工程类缺少履约担保时标注高风险；货物/服务类无此要求 |
| 合同期限 | 生效条件 | [生效条件] | 留空 |
| 合同期限 | 终止条件 | [终止条件] | 甲方解除权不足时标注风险 |
| 争议解决 | 管辖约定 | [仲裁/诉讼 + 管辖地] | **非甲方所在地时标注风险（高风险）**；同时约定仲裁+诉讼时标注高风险 |
| 违约责任 | 甲方违约责任 | [原文引用] | 甲方违约责任过重时标注 |
| 违约责任 | 乙方违约责任 | [原文引用] | 乙方违约责任过轻时标注风险（高风险） |
| 违约责任 | 发票违约责任 | [原文引用] | 乙方发票违约责任缺失时标注风险 |
| 违约责任 | 单边违约风险 | [是否存在单边违约风险的判断结果] | 对甲方不利时标注风险 |
| 违约责任 | 违约金抵扣 | [甲方可直接抵扣违约金的约定] | 未约定时标注中风险 |
| 违约责任 | 侵权责任兜底 | [乙方承担全部侵权赔偿的约定] | 未约定时标注高风险 |
| **分类专项** | **[类型专项字段]** | [根据采购类型动态添加] | 见下方分类专项字段说明 |
| 知识产权 | 成果归属 | [知识产权归属约定] | 未归甲方时标注风险 |
| 保密条款 | 保密期限 | [保密期限，应≥2年] | 期限不足时标注风险 |
| 保密条款 | 商业秘密范围 | [商业秘密定义是否完整] | 范围不完整时标注风险 |
| **审减条款** | **政府投资项目审计** | [同比例核减约定] | 政府投资项目未约定时标注中风险 |

> **{{change_clause}}占位符说明**：如果合同中存在明确的变更条款（变更程序、变更审批、变更计价等），则替换为两行合同变更内容（变更原则+变更计价）；如果合同中不存在变更条款，则替换为空字符串（即不展示该行）。

**分类专项字段说明**（根据采购类型动态添加）：

| 采购类型 | 专项字段 | 审核要点 |
|---------|---------|---------|
| **货物类** | 所有权转移时点 | 货物所有权何时转移（交付时/验收后/付款后），《民法典》第604条 |
| **货物类** | 运输与保险 | 运输方式、风险承担、保险责任 |
| **货物类** | 包装标准 | 是否符合国家/行业标准 |
| **货物类** | 知识产权保证 | 乙方保证产品不侵犯第三方知识产权 |
| **货物类** | 备品备件 | 是否包含备品备件清单 |
| **工程类** | 工期及节点 | 开工日期、竣工日期、中间节点是否明确 |
| **工程类** | 履约保函 | 是否约定履约保函/保证金，比例不低于合同价的5% |
| **工程类** | 质量标准 | 是否明确引用国家/行业施工质量标准 |
| **工程类** | 安全生产 | 安全生产责任划分，是否违反《建筑法》《安全生产法》 |
| **工程类** | 农民工工资保障 | 是否约定农民工工资专用账户、工资保证金，《保障农民工工资支付条例》 |
| **工程类** | 分包管理 | 分包是否需甲方同意，禁止转包 |
| **工程类** | 竣工验收 | 竣工验收程序、标准、期限 |
| **工程类** | 质量保修 | 保修范围和年限是否符合法定最低标准 |
| **服务类** | 服务标准/SLA | 服务水平协议是否量化（响应时间、解决时间等） |
| **服务类** | 人员资质要求 | 服务人员资质、经验要求 |
| **服务类** | 知识产权归属 | 服务过程中产生的成果知识产权归属（归甲方/双方共有） |
| **服务类** | 保密与数据安全 | 数据保护义务、个人信息保护合规 |
| **服务类** | 服务验收 | 交付成果量化标准、验收流程 |

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
            <li><strong>法律依据：</strong>[相关法律条款]（详见本报告"四、参考条款"第N条）</li>
        </ul>
    </div>
</div>
```

**3.4 参考条款**（关联风险与法律依据的展示逻辑）：

> **核心原则**：参考条款不再展示通用的标准条款文本，而是**针对每个已识别的风险点，列出该风险所违背的具体法律法规条款及出处**。展示逻辑如下：
> 1. 仅针对"潜在风险点"中已列出的风险项，展示其对应的法律依据
> 2. 每个参考条款必须包含：所违背的法律文件名称 + 具体条款号 + 条款原文
> 3. 参考条款与风险点一一对应（风险项N → 参考条款N）
> 4. 如果该风险未违反具体法律规定（如纯商业谈判类风险），则不需要展示参考条款

每个参考条款的HTML结构：

```html
<div class="clause-item">
    <div class="clause-header">
        <span>参考条款N：对应风险「[风险标题]」</span>
        <span class="risk-clause">[违背的法律文件名称]</span>
    </div>
    <div class="clause-content">
        <p><strong>[具体条款号]：</strong>[条款原文]</p>
        <div class="note-item">
            <strong>违背说明：</strong>合同第X条约定「...」，与上述法律强制性规定不符，可能导致该条款无效或甲方权益受损。
        </div>
    </div>
</div>
```

> **样式说明**：
> - 条款标题使用 `risk-clause` 类（紫色，11px），与风险点的条款位置标注保持一致
> - 条款内容使用 `<p>` 标签，继承 `.clause-content` 的默认样式（13px），与报告其他正文部分字体一致
> - 违背说明使用 `note-item` 类（黄色边框淡黄背景），与审核结论中的"履约注意事项"样式一致

**示例**：

风险项：合同约定管辖地为乙方所在地（违反《民事诉讼法》第35条）
→ 参考条款展示：
```
参考条款1：对应风险「异地管辖约定」
违背的法律文件：《中华人民共和国民事诉讼法》

第35条：合同或者其他财产权益纠纷的当事人可以书面协议选择被告住所地、合同履行地、合同签订地、原告住所地、标的物所在地等与争议有实际联系的地点的人民法院管辖，但不得违反本法对级别管辖和专属管辖的规定。

违背说明：合同第X条约定管辖地为乙方所在地法院，但根据《民事诉讼法》第35条，协议管辖应选择与争议有实际联系的地点。甲方所在地法院属于"原告住所地"，是法定的可选管辖地。约定乙方所在地将大幅增加甲方维权成本。
```

风险项：工程类合同未约定农民工工资专户（违反《保障农民工工资支付条例》第26条）
→ 参考条款展示：
```
参考条款2：对应风险「农民工工资保障缺失」
违背的法律文件：《保障农民工工资支付条例》

第26条：施工总承包单位应当按照有关规定开设农民工工资专用账户，专项用于支付该工程建设项目农民工工资。开设、使用农民工工资专用账户有关资料应当由施工总承包单位妥善保存备查。

违背说明：合同未约定开设农民工工资专用账户，违反《保障农民工工资支付条例》第26条强制性规定。如发生农民工工资拖欠，甲方（发包方）可能依据本条例第30条承担先行垫付责任。
```

**生成规则**：
- 参考条款的数量 = 涉及违反法律法规的风险项数量（纯商业风险不生成参考条款）
- 编号从1开始，按风险项顺序对应
- 必须从 `references/audit_points.md` 的第十章节"主要法律法规索引"和正文中各章节的法律依据中引用准确的法律条文
- 条款原文必须**精确引用**，不得自行概括或改写

**3.5 审核结论**（完整结构，必须包含以下6个部分）：

```html
<div class="conclusion-box">
    <div class="conclusion-header">
        <span class="conclusion-label">综合风险评级</span>
        <span class="conclusion-rating [low|medium|high]">[低风险|中风险|高风险]</span>
    </div>
    <div class="conclusion-content">
        <p><strong>整体评价：</strong>[从甲方视角的整体评价]</p>

        <p><strong>甲方优势条款（建议保留）：</strong></p>
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
- [ ] 报告头部标题为 "采购合同审核报告"
- [ ] 报告头部包含4个meta项（审核日期、合同名称、采购类型、审核视角）
- [ ] 审核视角meta为"甲方（采购方）"
- [ ] **合同要点总结表格第一行为"采购类型"行**，包含类型和判断依据
- [ ] **已根据采购类型加载对应的分类审核规则进行审核**
- [ ] 五个section标题顺序正确，第二个为"二、潜在风险点（仅列出对甲方不利的条款）"
- [ ] 审核结论包含6个子部分（综合风险评级、整体评价、甲方优势条款、可优化项、履约注意事项、签约建议）
- [ ] 审核结论有签名区域（审核人 + 审核日期）
- [ ] footer使用完整文本："本报告仅供参考，不构成法律意见。具体合同条款的效力及风险需结合实际情况判断，建议咨询专业律师。"
- [ ] 所有颜色使用固化CSS变量，不自定义颜色值
- [ ] 风险等级class正确：高风险无额外类名，中风险=`medium`，低风险=`low`
- [ ] **合同变更行有条件展示**：仅合同含变更条款时才展示变更行
- [ ] **参考条款与风险点一一对应**：参考条款N对应风险N的法律依据
- [ ] **参考条款展示被违背的法律条款原文**：包含法律文件名称、具体条款号、条款原文
- [ ] **纯商业类风险不生成参考条款**（未违反具体法律规定时）
- [ ] 修改建议中"法律依据"后标注"详见参考条款第N条"
- [ ] **合同主体审核**：已核查甲乙双方统一社会信用代码、供应商成立年限（1年以上）、法律依据引用《民法典》而非已废止《合同法》
- [ ] **签署地点审核**：已核查合同签署地点是否精确至县级市/区
- [ ] **运输风险划分审核**：已核查风险转移时点是否为"送达验收合格后"
- [ ] **验收规则审核**：已核查是否约定两段验收时限（收货后验收期+质量异议期），验收凭证约定，质保期起算点
- [ ] **付款条件审核**：已核查是否先货后款、分3-4期付款、保留质保金（5%-10%）
- [ ] **发票开具审核**：已核查开票主体信息是否完整、发票类型是否明确
- [ ] **审减条款审核**：已核查政府投资项目是否约定同比例核减条款
- [ ] **违约责任审核**：已核查违约金抵扣权、分情形违约金、损失赔偿范围、单方解除权、第三方损失、侵权责任兜底
- [ ] **知识产权审核**：已核查成果归属甲方、侵权责任兜底条款
- [ ] **保密条款审核**：已核查商业秘密范围是否完整、保密期限是否≥2年
- [ ] **争议解决审核**：已核查是否二选一约定、禁止同时约定仲裁+诉讼

## 违约责任审核要点（重要补充）

从甲方视角审核违约责任时，必须包含以下内容：

### 1. 违约责任必须从合同全文中总结

审核违约责任时，**必须从合同全文中搜索并引用所有相关条款**，包括但不限于：
- 合同正文中关于违约责任的专门章节
- 合同附件中的违约责任条款（如廉洁协议、安全管理协议中的违约责任）
- 任何涉及违约金、赔偿、解除合同等违约后果的条款

### 2. 乙方违约责任必须充分

**必须审核乙方违约责任是否充分保障甲方权益**：

| 违约情形 | 应有违约责任 |
|-------------|---------------------|
| 乙方逾期交付 | 应约定明确的违约金比例及上限 |
| 乙方交付产品/服务不合格 | 应约定维修、更换、退货、赔偿条款 |
| 乙方未按期提供发票 | 应约定乙方承担由此给甲方造成的损失 |
| 乙方提供发票不合规 | 应约定乙方更换发票并承担相关损失 |

**注意**：乙方违约责任过轻是甲方风险，应在违约责任审核中明确列出。

### 3. 单边违约风险判断（重要！）

**必须判断合同是否存在"单边违约风险"**（从甲方视角）：

| 风险类型 | 判断标准 | 风险等级 |
|---------|---------|---------|
| **乙方违约责任过轻** | 乙方违约无对应违约责任或责任极轻 | 高风险 |
| **甲方违约责任过重** | 甲方违约金比例高于乙方 | 中风险 |
| **单边解除权** | 乙方有权任意解除合同，但甲方无对等解除权 | 高风险 |
| **甲方违约责任无上限** | 甲方违约责任未设置上限 | 中风险 |

### 4. 付款与发票金额一致性审核

**必须审核付款金额与增值税专用发票金额是否一致**：
- 每次付款金额与乙方需提供的增值税专用发票金额应一致
- 不一致时发票金额大于付款金额，有助于甲方抵扣，对甲方有利；不一致时发票金额小于付款金额，对甲方不利（中风险）

## 数字准确性铁律（最高优先级！）

**报告中的所有数字必须从合同原文中直接引用，严禁推断、换算或自行计算。**

### 铁律规则
1. **数字引用原文，不做转换**：合同写"0.4‰"就写"0.4‰"，不要自行转换或简写。
2. **不推断修订痕迹**：合同有修订痕迹（Track Changes）时，删除/插入的内容不能混用。
3. **违约金比例不可自行比对**：引用双方违约金时分别引用原文。

### 禁止行为
- ❌ 看到"万分之四"自行写成"0.4‰"或"0.04%"
- ❌ 将"肆佰伍拾贰万元整"简化为"452万"
- ❌ 将中文数字自行换算为阿拉伯数字

### 合同要点总结表格填写规则（重要！）

**在填写"合同要点总结"表格时，必须严格遵循以下规则：**

1. **只填写合同中明确存在的内容**
   - 合同要点总结表格中的每一项内容，都必须从合同原文中找到对应条款
   - 如果合同中**未约定**某项内容，必须填写"未明确约定"，不得自行推断或假设

2. **违约责任字段的特别约束**
   - **甲方违约责任**：必须填写合同中明确约定的甲方违约责任条款原文，如果合同未约定则填写"未明确约定"
   - **乙方违约责任**：必须填写合同中明确约定的乙方违约责任条款原文，如果合同未约定则填写"未明确约定"
   - **禁止行为**：❌ 不得在合同未约定的情况下，自行添加如"甲方逾期付款应按每日万分之四向乙方支付违约金"等条款内容

3. **金额、比例等数字字段的约束**
   - 合同中写"千分之四"（4‰）就写"千分之四"，不要误认为是"万分之四"（0.4‰）
   - 保险费"千分之四" ≠ 违约金"万分之四"，必须区分清楚

4. **验证清单**
   填写完合同要点总结表格后，逐项检查：
   - [ ] 每一项内容都能在合同原文中找到对应条款
   - [ ] 违约责任相关字段没有自行添加合同未约定的内容
   - [ ] 金额、比例等数字与合同原文一致

## 甲方视角风险识别核心原则（关键！）

**"风险"的定义：仅指对甲方（采购方/买方）不利的条款。** 识别风险时必须严格遵循以下原则：

### 什么算甲方风险（必须报告）
| 类型 | 示例 | 理由 |
|------|------|------|
| 乙方义务过轻 | 乙方违约责任过低、质保期过短 | 损害甲方利益 |
| 甲方权利缺失 | 缺少验收权、无合同解除权 | 甲方缺少保护 |
| 乙方权利过大 | 乙方任意解除权、限制甲方验收权 | 甲方处于被动 |
| 交付无保障 | 交付时间模糊、无延期违约金 | 影响甲方项目进度 |
| 管辖不利 | 管辖地不在甲方所在地 | 增加维权成本 |
| 知识产权风险 | 开发成果知识产权归属不明确 | 甲方后续使用受限 |
| 保密不足 | 乙方保密义务不充分 | 甲方商业秘密泄露风险 |
| 工程类专项风险 | 无履约保函、无农民工工资保障、无安全生产条款、允许转包 | 甲方承担连带法律责任 |
| 服务类专项风险 | SLA未量化、知识产权归乙方且无永久许可、数据安全条款缺失 | 服务质量无保障、后续使用受限 |

### 什么不算甲方风险（不应报告）
| 类型 | 示例 | 理由 |
|------|------|------|
| 乙方义务过重 | **乙方违约金高、质保期长** | 对甲方有利，保障甲方权益 |
| 乙方权利受限 | 乙方不得转分包、须经甲方同意 | 有利于甲方管控 |
| 甲方权利充分 | 甲方有验收权、解除权、变更审批权 | 甲方优势条款 |
| 对甲方有利的不对等 | 付款比例对甲方有利（如30%预付款） | 商业谈判优势 |
| 标准商业惯例 | **合同签字盖章即生效（无需与预付款挂钩）** | 标准商业操作 |
| 工程类对甲方有利 | 乙方须购买工程保险、提供履约保函、设立农民工工资专户 | 保障甲方利益，非乙方风险 |
| 服务类对甲方有利 | 知识产权归甲方、乙方人员须经甲方认可、甲方有权审计 | 保障甲方利益，非乙方风险 |

### 特殊处理
- 乙方违约金比例极高（如日千分之八），虽对甲方有利，但属于可执行性层面的注意事项（法院可能调低），应放在**审核结论**中作为"履约注意事项"提醒，**不应列为风险点**
- 司法实践中违约金过高可能被调减的风险，不等于甲方的风险

## 注意事项

- **审核第一步必须识别采购类型**（货物类/工程类/服务类/混合类），并在报告中标明判断依据
- **审核视角为甲方（采购方/买方）**，所有风险分析从甲方利益出发，严格遵循上述核心原则
- 合法性审查为最高优先级，任何违反法律法规强制性规定的条款必须指出
- 工程类合同必须关注：履约担保、农民工工资保障、安全生产、分包转包限制、质量保修年限
- 服务类合同必须关注：知识产权归属（默认归受托方！）、SLA量化、数据安全、人员资质
- 货物类合同必须关注：所有权转移时点、运输保险、产品知识产权保证
- **乙方违约金高对甲方有利**，不可标记为甲方风险；需注意司法调低可能，但不应列入风险点
- 管辖约定优先选择甲方所在地法院
- **质保期从"验收合格之日"起算对甲方有利**（质保期从项目可用时开始），从"交付之日"起算对甲方不利
- **合同签字盖章生效为标准商业惯例**，无需与预付款到账挂钩
- 预付款比例建议不超过30%，避免资金占用风险
- 验收标准必须明确且可量化
- 审核时应结合具体业务场景，不能机械套用条款
- 对于重大风险应明确标注并建议咨询专业律师
- HTML报告需要启动本地服务器预览
