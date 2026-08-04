---
name: yc-saas-drafter
description: |
  以 Y Combinator 标准格式 SaaS 模板为起点起草定制客户协议。通过覆盖费用结构、数据处理、
  机器学习权、实施服务等主题的结构化信息收集来定制协议。应用 18 项始终开启的默认处理，
  将原始 YC 模板转变为专业的起点（重命名为"Customer Agreement"、新增数据隐私章节、
  重构保证、合并 SLA/支持附件等）。产出干净的 .docx 和一份面向律师的备忘录，
  解释相对 YC 标准的每项变更。当用户说"draft a SaaS agreement"、"YC SaaS"、
  "startup SaaS contract"、"customer agreement"、"SaaS subscription agreement"或
  "I need a SaaS agreement starting from the YC form"时使用。当用户是讨论 SaaS
  缔约的初创企业创始人时也触发，即使他们未明确提及 YC。
metadata:
  author: "Victor Wang"
  license: "mit"
  version: "2026-05-12"
---

## 输出要求

最终 .docx 必须读起来像律师起草的。输出必须包含：

- **零**条 YC 起草注释（`*[Note:...]*`、`*[OPTIONAL:...]*`）
- **零**个占位脚手架（`[OPTIONAL]` 标记、选项指南）
- **零**个未填充的模板括号——除非是用户无法提供的值的刻意 `[TBD — description]` 标记，并在备忘录中记录

协议标题为"Customer Agreement"——**不是**"SaaS Services Agreement"。

如果输出中出现任何注释、说明或非 TBD 括号，草稿即未就绪。交付前修复它。

---

## 工作流

### 第 1 步：加载参考

在询问任何问题之前，阅读全部三个参考文件：

- `references/intake-questions.md` —— 15 个问题组，含分支和默认值
- `references/decision-matrix.md` —— 将答案映射到 YC 模板动作（18 项始终适用默认处理、12 项条件决策、变量替换、提请律师标记）
- `references/supplementary-language.md` —— 按 ID 锚定的预先写好的条款文本（始终适用块和条件块）

决策矩阵告诉您要**改变什么**。补充语言提供要插入的**确切文本**。不要即兴创作合同语言——如果矩阵说要插入 `#DATA-PRIVACY`，使用 supplementary-language.md 中的逐字文本。唯一例外是订单表服务费，由 LLM 根据费用模式示例撰写。

### 第 2 步：运行信息收集

按 `references/intake-questions.md` 中的问题顺序进行。应用分支逻辑（例如，无实施则跳过实施费，无试点则跳过试点详情，统一价格则跳过服务容量）。

关键原则：
- 提供默认值但允许用户覆盖
- 对用户尚无法提供的任何值使用 `[TBD — description]`
- 在继续前以摘要确认所有决定（模板在 intake-questions.md 末尾）
- 未经用户确认**不**进入文档组装

### 第 3 步：产出协议

从 `assets/YC_Form_SaaS_Agreement.docx` 阅读 YC 模板。

按以下顺序应用修改：

**首先——始终适用的默认处理**（decision-matrix.md A 部分，项目 A1-A18）：
1. 将订单表标题重命名为 → "Order Form Number One"
2. 全程将"SaaS Services Agreement"重命名为 → "Customer Agreement"
3. 更新前言日期年份
4. 第 1.1 条 SLA 引用——移除 [OPTIONAL]，始终开启
5. 第 1.2 条——将"Exhibit C"改为"Exhibit B"
6. 第 2.2 条——剥离出口管制说明（保留语言）
7. 第 2.3 条——完全删除客户赔偿条款 + 说明
8. 第 2.5 条——插入 `#DATA-PRIVACY`（新章节）
9. 第 3.3 条——移除可选框架（保留分析语言）
10. 第 6 条——重构为 6.1/6.2/6.3：插入 `#WARRANTY-REMEDY`、`#CUSTOMER-WARRANTY`、`#BETA-DISCLAIMER`
11. 第 7 条——移除可选说明，从专利范围中移除"United States"
12. 第 8 条——剥离谈判说明
13. 第 9 条——将 YC 新闻稿语言替换为 `#MARKETING-DEFAULT`
14. 附件——将 B + C 替换为 `#EXHIBIT-B-CONSOLIDATED`，删除附件 C
15. 剥离所有剩余的注释和说明

**其次——条件决策**（decision-matrix.md B 部分，项目 B1-B12）：
逐一走过每项条件决策。对每项，查找信息收集答案并应用指定动作。当矩阵引用补充语言（例如 `#NO-AUTO-RENEWAL`）时，使用逐字文本。

**第三——变量替换**（decision-matrix.md C 部分）：
将所有 YC 占位符替换为信息收集值。任何未收集的字段 → `[TBD — description]`。

**第四——清理：**
- 移除任何残留的注释、括号或起草指引
- 移除被删除章节留下的空段落
- 核实章节编号连续（特别是在 §2.5 新增和 §6 重构为 6.1/6.2/6.3 之后）
- 核实不存在非 TBD 括号

**DocX 格式说明：**
- 附件 B 积分表**必须**是适当的 Word 表格，而非内联文本
- 附件 B 沟通渠道**必须**是适当的 Word 表格
- 第 6 条子节（6.1、6.2、6.3）需要适当的标题格式
- 第 6.3 条（Beta 产品）必须全大写

将输出产出为 .docx 文件：
`[CompanyName]_[CustomerName]_Customer_Agreement_DRAFT.docx`

使用可用的文档创建工具（原生 DocX 技能、python-docx 或等效工具）生成格式专业的 Word 文档。

### 第 4 步：产出律师备忘录

在协议旁边创建一份 Markdown 备忘录：
`[CompanyName]_[CustomerName]_Customer_Agreement_Memo.md`

备忘录必须包含：

**1. 交易摘要** —— 一段：谁、什么、费用结构、期限。

**2. 模板基础** —— "本协议基于 Y Combinator 标准格式 SaaS 协议并作如下修改。"

**3. 始终应用的默认处理** —— 每项始终适用变更（A1-A18）的分项列表，附简要理由。示例：
- "重命名为'Customer Agreement'（专业标准）"
- "从知识产权赔偿专利范围中移除'United States'（标准修改）"
- "新增第 2.5 条数据隐私和安全条款（现代 SaaS 所必需）"
- "新增第 6.2 条客户保证和第 6.3 条 Beta 产品免责声明"

**4. 信息收集驱动的决策** —— 每项条件决策及所选内容。示例：
- "第 3.2 条：客户拥有衍生数据（保留括号语言）"
- "第 5.1 条：自动续约，60 天通知"

**5. 需要律师审查的事项** —— 这是关键的。对每个提请律师标记（decision-matrix.md D 部分），逐字包含标记文本。它们是：
- DPA 建议（几乎总是需要）
- 实施服务知识产权归属（如适用）
- 衍生数据所有权（如公司保留）
- 客户内容上的机器学习训练（如适用）
- 数据保留时间线确认

**6. TBD 事项** —— 文档中的每个 `[TBD — description]`，列出以便创始人知道发送前要填写什么。

### 第 5 步：交付

向用户提供：
1. 干净的 .docx 客户协议
2. 律师备忘录
3. 简要摘要：关键决策、TBD 数量、律师审查事项

---

## 决策点快速参考

| # | 位置 | 决定内容 |
|---|----------|---------------|
| B1 | 订单表 | 服务描述（来自产品信息收集） |
| B2 | 订单表 | 费用结构 + 服务容量（8 种费用类型） |
| B3 | 订单表 + 附件 A | 实施服务：包含或移除 |
| B4 | 订单表 | 试点期：包含或移除 |
| B5 | §2.1 | 分发软件许可：包含或移除 |
| B6 | §3.2 | 衍生数据：客户拥有或公司保留 |
| B7 | §5.1 | 自动续约：是（30/60/90 天通知）或否 |
| B8 | §5.2 | 终止时的数据保留期 |
| B9 | §9 | 管辖法律：州选择 |
| B10 | §9 | 营销表述：默认、更多或更少 |
| B11 | 附件 B | SLA 可用性：99.9% / 99.95% / 99.99% |
| B12 | 附件 B | 支持详情：电子邮件、电话、时间、工具 |

---

## 补充语言参考

| 锚点 | 条款 | 类型 |
|--------|--------|------|
| #DATA-PRIVACY | §2.5 数据隐私与安全 | 始终 |
| #WARRANTY-REMEDY | §6.1 排他性保证救济 | 始终 |
| #CUSTOMER-WARRANTY | §6.2 客户保证 | 始终 |
| #BETA-DISCLAIMER | §6.3 Beta 产品（全大写） | 始终 |
| #MARKETING-DEFAULT | §9 营销语言 | 始终 |
| #EXHIBIT-B-CONSOLIDATED | 附件 B：SLA + 支持 | 始终 |
| #NO-AUTO-RENEWAL | §5.1 手动续约替换 | 条件 |
| #FEE-EXAMPLES | 订单表费用模式（8 种类型） | 条件 |
| #EXPANDED-DATA-RESTRICTIONS | 敏感数据保护 | 条件 |
| #ML-TRAINING | 机器学习模型训练权 | 条件 |
| #ML-FEDERATED | 联邦学习例外 | 条件 |

---

## 本技能**不**做什么

- **不起草 DPA。** 在备忘录中标记 DPA 需求；另行使用 dpa-drafter。
- **不处理专业服务协议。** 如果交易有超出实施的重要服务，使用 msa-drafter。
- **不审查或修改收到的合同。** 本技能从模板起草。审查请使用审查技能。
- **不发明条款语言。** 每项修改都是删除、变量替换或从 supplementary-language.md 逐字插入。例外：订单表服务费，根据费用模式示例撰写。
- **不解决律师审查事项。** 在备忘录中标记它们供法律顾问处理。
