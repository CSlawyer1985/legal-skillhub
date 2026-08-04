---
name: contract-review
description: AI合同智能审查助手。上传或粘贴合同文本，自动进行9维雷达评分、风险热力图可视化、条款对比修改建议、法律依据引用、谈判策略生成，输出交互式HTML审查报告。覆盖买卖合同/劳动用工/租赁合同/服务合同/保密协议/投资协议/建设工程/技术开发8类合同类型。触发词：合同审查, 审合同, 合同风险, 合同分析, 审查合同, contract review, 帮我看看合同, 合同审核, 法律风险分析。
version: "1.0.0"
agent_created: true
location: user
allowed-tools: [Read, Write, Edit, Bash, WebSearch, WebFetch, Grep, Glob]
metadata:
  openclaw:
    requires:
      bins:
        - python.exe
    emoji: "📋"
    homepage: https://github.com/bettermen/contract-review
---

# 合同审查 (Contract Review)

AI驱动的合同智能审查技能，输出交互式可视化HTML审查报告。

## 核心特色

与市面上SaaS合同审查工具不同，本技能提供：
1. **9维雷达评分** — 主体资格/条款完整性/违约责任/争议解决/法律合规/权利义务对等/履约可行性/知识产权/格式规范
2. **风险热力图** — 按合同章节可视化风险密度
3. **条款对比修改** — 原文 vs 修改建议并列对比，可直接复制使用
4. **法律依据引用** — 每个风险点引用《民法典》等具体法条
5. **谈判策略生成** — 不止发现问题，提供谈判话术和博弈角度
6. **完全本地免费** — 无需订阅，离线可用

## 触发条件

当用户提到以下关键词时触发：
- 合同审查、审合同、合同风险、合同分析、审查合同、contract review
- 帮我看看合同、合同审核、法律风险分析
- 用户上传或粘贴合同文本

## 工作流程

### 阶段1：接收合同

1. 确定合同获取方式：文本粘贴 / 文件上传(.txt/.docx/.pdf) / URL
2. 如果是 .docx 或 .pdf 文件，先用对应工具提取文本内容
3. 如果用户未指定合同类型，根据合同内容自动识别

### 阶段2：合同类型识别与审查清单加载

识别合同类型，加载对应的审查清单：
- 买卖合同 (sales) → 参考 `references/checklist_sales.md`
- 劳动用工合同 (labor) → 参考 `references/checklist_labor.md`
- 租赁合同 (lease) → 参考 `references/checklist_lease.md`
- 服务合同 (service) → 参考 `references/checklist_service.md`
- 保密协议 (nda) → 参考 `references/checklist_nda.md`
- 投资协议 (investment) → 参考 `references/checklist_investment.md`
- 建设工程合同 (construction) → 参考 `references/checklist_construction.md`
- 技术开发合同 (tech_dev) → 参考 `references/checklist_tech_dev.md`

通用审查维度始终生效，参考 `references/checklist_general.md`

### 阶段3：逐维审查

按9个维度逐一审查合同：

**维度1：主体资格 (Party Qualification)**
- 签约主体合法性（营业执照/授权委托）
- 履约能力评估
- 印章与签字效力

**维度2：条款完整性 (Clause Completeness)**
- 必备条款是否齐全（标的/数量/质量/价款/履行期限/地点/方式/违约责任/争议解决）
- 关键定义是否清晰

**维度3：违约责任 (Breach Liability)**
- 违约金设定是否合理（不超过损失30%，依据民法典585条）
- 违约情形是否覆盖全面
- 免责条款是否合法

**维度4：争议解决 (Dispute Resolution)**
- 管辖法院/仲裁机构是否明确
- 是否违反专属管辖
- 仲裁条款有效性

**维度5：法律合规 (Legal Compliance)**
- 是否违反强制性法律规定
- 格式条款是否公平
- 知识产权归属是否明确

**维度6：权利义务对等性 (Reciprocity)**
- 双方权利义务是否失衡
- 是否存在霸王条款
- 单方解除权是否合理

**维度7：履约可行性 (Performance Feasibility)**
- 交付标准/验收条件是否可执行
- 付款节点是否合理
- 质量标准的可操作性

**维度8：知识产权保护 (IP Protection)**
- 知识产权归属约定
- 保密条款完整性
- 竞业限制合理性

**维度9：格式规范性 (Format Standardization)**
- 结构层次逻辑性
- 语言表述精确度
- 附件与正文协同性

### 阶段4：风险分级

对发现的风险进行三级分类：
- 🔴 **致命风险** — 可能导致合同无效、重大损失（如主体无资质、违法条款）
- 🟡 **重大风险** — 可能导致严重不利后果（如违约金过高、管辖不利）
- 🟢 **一般风险** — 可协商改进的瑕疵（如表述模糊、格式不规范）

### 阶段5：生成条款修改建议

对每个风险点：
1. 引用原文条款
2. 提供修改后条款（可直接复制使用）
3. 说明修改理由
4. 引用法律依据（民法典具体条款）

### 阶段6：谈判策略生成

对乙方/弱势方合同：
- 识别谈判优先级（哪些必须改、哪些可让步）
- 提供谈判话术建议
- 分析对方可能反应及应对策略

### 阶段7：生成HTML报告

基于 `assets/report_template.html` 模板，将审查结果填入并生成交互式可视化报告。

报告包含模块：
1. 合同概览卡片（类型/签约方/审查时间/综合评分）
2. 9维雷达图（Chart.js）
3. 风险热力图（按章节分布）
4. 风险清单表（分级/描述/原文/建议/法律依据）
5. 条款对比区（原文 vs 修改建议）
6. 谈判策略建议
7. 综合评分卡（A+ ~ F）

### 阶段8：交付报告

1. 将生成的HTML保存到工作目录
2. 使用 present_files 展示报告
3. 提供简要口头总结

## 使用模板的方法

报告模板位于 `assets/report_template.html`：
- 读取模板全文
- 将以下占位符替换为实际审查结果JSON：
  - `{{CONTRACT_INFO}}` — 合同基本信息JSON
  - `{{RADAR_DATA}}` — 9维评分数据JSON（每个维度0-100分）
  - `{{RISK_ITEMS}}` — 风险条目数组JSON
  - `{{COMPARISON_ITEMS}}` — 条款对比数组JSON
  - `{{NEGOTIATION_STRATEGY}}` — 谈判策略JSON
  - `{{SCORE_CARD}}` — 综合评分数据JSON
  - `{{LAW_REFERENCES}}` — 法律依据引用数组JSON
  - `{{HEATMAP_DATA}}` — 热力图数据JSON
- 将替换后的完整HTML写入工作目录 `contract-review-report.html`

## 参考文件

- `references/checklist_general.md` — 通用审查清单（所有合同类型适用）
- `references/checklist_sales.md` — 买卖合同审查清单
- `references/checklist_labor.md` — 劳动用工合同审查清单
- `references/checklist_lease.md` — 租赁合同审查清单
- `references/checklist_service.md` — 服务合同审查清单
- `references/checklist_nda.md` — 保密协议审查清单
- `references/checklist_investment.md` — 投资协议审查清单
- `references/checklist_construction.md` — 建设工程合同审查清单
- `references/checklist_tech_dev.md` — 技术开发合同审查清单
- `references/law_reference.md` — 法律条款引用库

## 注意事项

1. 本技能输出的是AI辅助审查建议，不构成法律意见
2. 重大合同建议由专业律师最终审核
3. 审查结果仅供参考，使用者需自行判断
4. 对法律条文的引用可能不完整，重要决策请核实最新法律
