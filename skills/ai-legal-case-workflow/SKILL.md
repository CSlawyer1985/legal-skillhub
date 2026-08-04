---
name: ai-legal-case-workflow
slug: ai-legal-case-workflow
displayName: 民事诉讼AI辅助全流程
description: 由程建都律师基于一线诉讼办案流程开发的中国民事诉讼 AI 协作技能，面向执业律师和诉讼团队，覆盖民事一审 1–7 七阶段与民事二审 A0–A6 专门路径（判决上诉与三类受控裁定上诉）。适用于读取卷宗、建立事实时间线和证据矩阵，分析诉讼时效、管辖、保全、费用及上诉期限，形成起诉状、答辩状、上诉状、证据目录、质证意见、庭审提纲、客户报告和交付归档底稿；支持原告、被告、上诉人、被上诉人及多方上诉场景，并可按阶段局部执行。它不是单一文书生成提示词，而是一套将材料读取、证据分析、策略形成、文书组建和质量检查组织为可复用、可追溯闭环的 AI 辅助办案工作流。刑事、行政、再审、执行、无具体材料的纯咨询、利益冲突及结果承诺不适用；涉外、港澳台、知识产权、海事海商和破产衍生诉讼仅做识别、风险提示与专项核验闸门。所有输出均为律师工作底稿，不能替代原件核对、现行法核验和执业律师最终判断。
license: CC BY-NC 4.0 - 完整文本见 https://github.com/jackcheng459/ai-legal-case-workflow/blob/main/LICENSE
---

# 民事诉讼AI辅助全流程

## 关于作者与合作

本技能由 **程建都律师** 开发维护。程建都律师系北京海润天睿（郑州）律师事务所高级合伙人、管委会成员，长期从事复杂商事争议解决、股东股权纠纷和企业应收账款处理，并持续探索 AI 在诉讼办案、律师团队协作和法律产品中的真实应用。

问题反馈与合作交流：[GitHub 仓库](https://github.com/jackcheng459/ai-legal-case-workflow/) · 微信号 `wx1811985798`。

## 这项技能解决什么问题

本技能来自一线律师诉讼工作流程的拆解与沉淀，目标不是让人工智能替代律师，而是协助律师建立可复用、可追溯的“材料读取、证据分析、形成策略、组建文书和质量检查”AI 协作办案全流程。

它不是单一的文书生成提示词，而是两条相互隔离、共享事实与证据底座的程序路径：民事一审七阶段与民事二审 A0–A6。根据代理立场和案件进度选择局部流程，不要求每次从头执行，也不要一次加载全部参考文件。

### 适合谁

- 希望系统使用 AI 辅助办理民事一审或二审案件的执业律师。
- 需要统一材料、分析、文书和复核标准的律师团队。
- 正在建设法律 AI 课程、产品或办案 SOP 的实践者。

### 两条程序路径

| 程序 | 路径 | 典型任务 |
|---|---|---|
| 民事一审 | 1–7 | 诉前分析、主体核查与保全、起诉或答辩、庭审、交付 |
| 民事二审 | A0–A6 | 上诉可行性与期限、原审裁判拆解、上诉理由与应对、二审文书、庭审或询问、裁判交付 |

一审原告通常走 `1 → 2 → 3 → 等待应诉材料 → 4 → 5 → 6 → 7`，一审被告通常走 `1 → 2 → 4 → 5 → 6 → 7`。二审按照 `A0 → A1 → A2 → A3 → A4 → A5 → A6` 推进，但可用 `start_phase` 和 `end_phase` 处理局部任务。

### 贯穿全流程的核心能力

- 全量读取卷宗并建立可回溯的事实时间线。
- 将事实主张与证据、页码、段落或音视频时间点关联。
- 前置识别期限、管辖、保全、费用和程序风险。
- 按请求权基础、构成要件和裁判错误类型组织策略。
- 让多份文书共享同一事实底座，通过律师裁决点和质量清单闭环。

> 本技能只生成分析候选和工作底稿。事实认定、诉讼策略、法律适用、文书定稿、对外发送和法院提交均由执业律师决定。

## 不可绕过的执行闸门

1. **适用范围**：专门流程只处理具体中国民事一审和二审案件。刑事、行政、再审、执行、纯咨询、单纯合同起草和同时代理利益冲突双方不适用。
2. **程序隔离**：先确认 `procedure`。一审只使用 `start_stage/end_stage`，二审只使用 `start_phase/end_phase`；不得把一审阶段、期限或模板套入二审。
3. **人类终局裁决**：不得把 AI 输出表述为律师已确认结论，不预测或承诺判决结果。
4. **数据边界**：按绿色、黄色、红色、红线审查材料、必要性、授权和链路。红色数据仅在任务必要、授权清楚、链路可信且有人工终审时处理；红线数据不得进入普通 AI 链路、外部代理或公开仓库。
5. **事实可追溯**：区分原始材料、当事人陈述、辅助识别、分析推论和法律评价。金额、日期、身份、证据编号及送达事实回原件复核。
6. **法源可核验**：不得凭记忆确认法条或案例。通过当前可用的权威来源实时核实效力和现行文本；通过时标注 `【已核实：<来源名称>，YYYY-MM-DD】`，无法核实时标注 `【未经工具核实，仅供参考】`。
7. **工具真实状态**：只使用平台实际可用且已获授权的工具，不虚构查询、重试、协作、转换、发送或提交成功。
8. **质量门与修订痕迹**：每阶段或阶段组完成后检查质量。未通过时停在当前步骤；不覆盖原始材料和既有定稿，新增版本并记录变化。
9. **专门领域闸门**：识别涉外、港澳台、知识产权、海事海商或破产衍生诉讼时，只形成要素、风险和待核验问题，标记 `specialist_review_required=true`。专项法源和专业人员复核前，不输出确定性程序结论。
10. **二审入口闸门**：没有原审裁判文书或可核验的送达记录时，可以拆解争点，但不得认定上诉期限尚未届满或计算确定截止日；小额诉讼等一审终审案件不得生成普通上诉方案。

## 快速启动

一审示例：

```yaml
case_type: 设备买卖合同纠纷
procedure: first_instance
role: defendant
materials_path: /path/to/case-materials
start_stage: 1
end_stage: 5
output_formats: [md]
```

二审示例：

```yaml
case_type: 股权转让纠纷
procedure: second_instance
original_role: plaintiff
appeal_role: appellant
decision_type: judgment
materials_path: /path/to/appeal-materials
start_phase: A0
end_phase: A4
output_formats: [md]
```

也可自然语言启动：“一审判决刚收到，我代理原告，先核对上诉期限并拆解败诉理由”“对方已经上诉，我方准备二审答辩”。更多示例和反模式见 `references/usage-and-faq.md`。

## 开始前检查

| 检查项 | 要求 | 缺失时处理 |
|---|---|---|
| 案件性质 | 具体民事诉讼案件 | 不适用时停止专门流程 |
| 程序 | 明确一审或二审 | 无法确认时先询问，不猜测 |
| 材料路径 | 存在、有权读取且非空 | 要求有效路径 |
| 代理立场 | 一审为原告或被告；二审区分原审地位和本方上诉地位 | 不明确时先确认 |
| 二审入口 | 原审裁判、送达记录、各方上诉材料和缴费状态 | 列出缺口；期限结论所需材料缺失时保持 `blocked` 或 `partial` |
| 专门领域 | 识别专项要素 | 进入专项核验闸门 |
| 数据与工具 | 完成四级数据审查，确认法源、文档和查询能力 | 如实降级，不推断“无风险” |

读材料前先读取 `references/tooling-and-fallbacks.md` 的异常处理与回退规则。

## 输入输出契约

### 共同必需输入

| 参数 | 类型 | 说明 |
|---|---|---|
| `case_type` | string | 案件类型，可从材料提取后请用户确认 |
| `procedure` | enum | `first_instance` 或 `second_instance` |
| `materials_path` | string | 卷宗材料目录绝对路径 |

### 一审条件输入

| 参数 | 类型 | 说明 |
|---|---|---|
| `role` | enum | `plaintiff` 或 `defendant` |
| `start_stage` | int | 默认 1，范围 1–7 |
| `end_stage` | int | 默认 7，范围 1–7 |
| `case_stage` | enum | `pre_litigation`、`subject_check`、`filing`、`defense`、`counterclaim`、`trial`、`post_trial`、`delivery`；仅在未给 `start_stage` 时推定 |

`case_stage` 映射：`pre_litigation`→1，`subject_check`→2，`filing` 结合 `role` 映射为原告阶段3或被告阶段4，`defense/counterclaim`→4，`trial`→6，`post_trial`→`start_stage=6` 并从 `references/stages-6-7-delivery.md` 的 6C 庭后子步骤切入，`delivery`→7。

### 二审条件输入

| 参数 | 类型 | 说明 |
|---|---|---|
| `original_role` | enum | `plaintiff`、`defendant` 或 `third_party` |
| `appeal_role` | enum | `appellant`、`appellee` 或 `dual_track` |
| `decision_type` | enum | `judgment` 或 `ruling` |
| `start_phase` | enum | 默认 `A0`，范围 `A0`–`A6` |
| `end_phase` | enum | 默认 `A6`，范围 `A0`–`A6` |

二审建议输入：

| 参数 | 类型 | 说明 |
|---|---|---|
| `decision_path` | string | 原审裁判文书路径；未单列时从材料目录识别 |
| `service_records` | list | 各当事人的送达证、电子回执或其他原始记录 |
| `client_filed_appeal` | bool | 本方是否已提交上诉，以提交凭证核验 |
| `other_party_filed_appeal` | bool | 对方是否已上诉，以法院送达或卷宗材料核验 |
| `appeal_tracks` | list | 已存在的多方上诉轨道；没有时由 A0 建立 |
| `appeal_fee_status` | enum | `unknown`、`notified`、`paid`、`overdue_risk` 或 `not_applicable` |
| `second_instance_stage` | enum | `pre_filing`、`filed`、`responding`、`hearing`、`post_hearing`、`decided`、`delivery`；仅在未给 `start_phase` 时推定 |

`second_instance_stage` 映射：`pre_filing/filed/responding`→A0，`hearing/post_hearing`→A5，`decided/delivery`→A6。后两类从中途切入时仍须快速执行 A0 入口核验和 A1 底座完整性检查，不能跳过期限与裁判身份确认。

裁定上诉仅覆盖不予受理、管辖权异议和驳回起诉三类通常可上诉裁定；其他裁定或特别救济进入专项核验闸门。

### 共同可选输入

`plaintiff`、`defendant`、`target_amount`、`output_formats`（默认 `[md]`）、`parallel_enabled`（默认 `true`，只表示具备资格）、`enable_mcp_tools`（授权白名单）。

### 输入校验

- 路径不存在或目录为空时停止当前阶段并说明。
- 一审阶段或二审阶段组越界、起点晚于终点时要求修正，不静默交换。
- 一审参数与二审参数混用时暂停，先确认程序并移除不适用参数。
- 代理立场、当事人或裁判类型不明确时保留“待确认”，不得自行补全。
- 二审存在多个上诉时，为每份上诉建立独立 `appeal_track`，不得把不同请求、理由和期限合并。
- 跳过前序流程时核对已有时间线、证据编号、裁判拆解和期限核验；逐项披露缺失后才继续。

### 输出与副作用

- 产出写入用户指定目录；未指定时按阶段或阶段组建立子目录，不改写卷宗。
- 每份产出标明事实来源、未核实事项、版本、`run_status` 和人工复核状态。
- `run_status` 只使用 `in_progress`、`completed`、`partial`、`blocked`、`waiting_external`。异常时列出已完成产出、失败步骤、实际尝试次数、未核事项、降级动作、能否重试、恢复位置和用户动作。
- `completed` 只表示约定步骤和质量门已经执行，不代表律师审核、格式转换、发送或法院提交成功。
- 相同材料重复执行时复用已通过最低检查的产出；材料变化时新建版本，不重复有费用或外部副作用的调用。
- 触发专项闸门时输出 `specialist_review_required`、`specialist_domains`、`trigger_facts`、`pending_questions`、`blocked_conclusions` 和 `specialist_review_status`。

## 一审七阶段路由

| 阶段 | 核心目标 | 主要产出 | 执行前必读 |
|---|---|---|---|
| 1 诉前案情分析 | 事实、时间线、争点和证据锚点 | 案件概要、时间线、证据清单、策略候选 | `references/stages-1-2-analysis.md` |
| 2 主体核查与保全 | 主体风险、财产线索和保全可行性 | 主体核查、资产线索、保全方案 | `references/stages-1-2-analysis.md` |
| 3 起诉材料制作 | 请求、事实、证据和法源闭环 | 起诉状、证据目录、立案材料 | `references/stages-3-5-litigation.md` |
| 4 反诉与答辩分析 | 拆解对方请求和举证缺口 | 构成要件表、应对策略 | `references/stages-3-5-litigation.md` |
| 5 应诉材料包 | 形成一致的成套材料 | 答辩、质证、法源、发问和调解材料 | `references/stages-3-5-litigation.md` |
| 6 庭审工作 | 庭前、庭中和庭后补强 | 庭审提纲、庭审分析、庭后意见 | `references/stages-6-7-delivery.md` |
| 7 格式与交付 | 转换、命名、验证和归档 | 已验证文件、客户摘要、归档清单 | `references/stages-6-7-delivery.md` |

一审完整执行协议和裁剪规则见上述阶段文件。原告完成阶段3但尚未收到对方材料时，状态为 `waiting_external`，不得假想对方主张进入阶段4。

## 二审 A0–A6 路由

| 阶段组 | 核心目标 | 主要产出 | 质量门 |
|---|---|---|---|
| A0 入口与期限 | 可上诉性、送达、期限、费用和各方上诉状态 | 入口核验表、期限计算表、费用待办 | D0 |
| A1 原审底座 | 重建原审请求、争点、证据、认定和裁判理由 | 原审裁判拆解表、事实证据底座 | D1 |
| A2 上诉审计 | 把上诉请求与事实、证据、法律、程序错误及结果影响连接 | 上诉轨道、裁判错误矩阵、策略选项 | D2 |
| A3 增量与程序 | 审查新证据、新请求、程序问题和调查需求 | 增量证据表、缺口关闭计划、程序申请清单 | D3 |
| A4 文书材料包 | 形成上诉状、答辩状或裁定上诉材料 | 二审文书、证据目录、法源核验报告 | D4 |
| A5 庭审或询问 | 准备审理范围、发问、质证、调解和庭后补强 | 庭审或询问提纲、质证意见、庭后意见 | D5 |
| A6 裁判与交付 | 对比原审与二审裁判、告知后续边界并归档 | 裁判对比、客户报告、归档与交接清单 | D6 |

详细步骤、裁定上诉边界和多上诉轨道见 `references/appeal-workflow.md`；固定结构见 `references/appeal-templates.md`；D0–D6 见 `references/appeal-quality-checklist.md`。

## 通用执行协议

1. 根据 `procedure` 和条件参数确定范围，生成输入缺口表。
2. 只读取当前阶段对应参考文件，不预载全部细节。
3. 全量读取该阶段所需材料，记录不可读、缺失和冲突文件。
4. 需要固定结构时，只读取对应模板章节。
5. 生成工作底稿，将关键事实和裁判判断回链到原始材料。
6. 运行通用质量检查及一审或二审专项质量门。
7. 报告已完成、未完成、未经核实和需要律师裁决的事项。
8. 质量门通过后才进入下一阶段；用户要求暂停时立即停止。

## 协作与回退

- 简单案件由一个 Agent 串行完成。复杂案件只在存在两个以上独立任务、平台支持且授权允许时并行。
- 一审优先在阶段3和5并行；二审可在 A1–A4 对“事实证据、程序、法源、文书”分工，但 A0 期限结论和 A2 策略选择由主代理统一复核。
- 子任务引用同一事实锚点、证据编号和裁判拆解；主代理检查跨文书一致性。
- 工具不可用时保留已完成分析并披露覆盖不足，不伪造结果。安全且平台支持时，同一调用最多 3 次（含首次）。
- 降级不等于完成。无法继续时返回结构化失败回执并停在可恢复位置，不自动安装依赖。仓库 `scripts/` 仅供维护验证，不参与案件处理。

## 最低质量控制

- 材料是否完整读取，不可读文件是否记录。
- 事实、原审认定和主张是否回链到原始载体。
- 主体、金额、日期、送达、证据编号和上诉轨道是否一致。
- 法源是否核实效力、原文和来源。
- 期限是否写明文件类型、送达事实、起算依据、届满日、办理动作和复核人。
- 策略建议是否列出成立条件、预期作用、风险、证据缺口和律师裁决点，而非只给单一答案。
- AI 草稿、律师待复核和律师已定稿是否区分。
- `run_status` 与实际范围是否一致，格式和外部动作是否单独验证。

## 参考文件加载表

| 文件 | 何时读取 |
|---|---|
| `references/tooling-and-fallbacks.md` | 读材料和调用外部能力前；发生异常或恢复执行时 |
| `references/stages-1-2-analysis.md` | 一审阶段1–2 |
| `references/stages-3-5-litigation.md` | 一审阶段3–5 |
| `references/stages-6-7-delivery.md` | 一审阶段6–7 |
| `references/templates.md` | 生成一审固定结构文书时，只读对应章节 |
| `references/quality-checklist.md` | 一审每阶段和跨阶段复核 |
| `references/appeal-workflow.md` | 任何二审任务；只读当前 A 阶段组章节及通用边界 |
| `references/appeal-templates.md` | 生成二审固定结构文书时，只读对应章节 |
| `references/appeal-quality-checklist.md` | 二审每阶段组和跨文书复核 |
| `references/appeal-case-examples.md` | 需要理解二审输入、输出和场景验收时，可选读取 |
| `references/usage-and-faq.md` | 首次使用、判断适用性、跳阶段或回答 FAQ 时 |
| `references/complete-output-example.md` | 查看一审虚构完整输出与失败恢复时，可选读取 |
| `references/case-study.md` | 查看一审脱敏执行复盘和效果边界时，可选读取 |

不要一次加载全部 references。长文件只读与当前程序、阶段、文书和问题相关的章节；无条件生效的闸门不得裁剪。

## 维护与许可

问题反馈和合作交流可通过 [GitHub 仓库](https://github.com/jackcheng459/ai-legal-case-workflow/) 或微信号 `wx1811985798` 联系。

非商业使用遵循 CC BY-NC 4.0。完整许可文本与版权说明见 GitHub 仓库中的 `LICENSE` 和 `NOTICE.md`；SkillHub 平台专用包因平台文件要求不随包附带许可证文档。
