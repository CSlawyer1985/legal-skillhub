---
name: "contract-intelligence-workflow-reviewer-carl-ditzler"
description: "适用于 Claude 和 Codex 的合同情报与合同运营工作流技能。引导完整的合同生命周期审查流程，从受理和剧本标准化，到条款审查、偏差评分、谈判规划、审批路由、质量检查和行动建议。跨合同和法律文件审查法律、业务、运营、合规、隐私、安全、技术和 AI 相关风险。支持 NDA、SaaS 协议、DPA、采购合同、商业协议、合同比较、修订稿、审批包、条款研究和起草。警告——全面审查可能消耗大量 Claude/OpenAI 令牌，尤其是大型协议、剧本、附件、附表和多文件审查。"
metadata:
  author: "Carl Ditzler"
  license: "apache-2.0"
  version: "2026-06-23"
---

# 合同情报与工作流审查器


当用户需要完整的合同工作流时使用本技能：审查、修订稿包、谈判计划、回退立场、审批路由、条款研究、起草、摘要或机器可读的下一步行动。

本技能为 Codex 和 Claude 设计。它有意保持严格。法律工作流镜像法务团队的流程：

1. 受理
2. 剧本
3. 审查
4. 谈判
5. 审批
6. 质量检查

在该法律工作流开始之前，如工作区尚未配置，先运行设置和持久化检查。

对运营工作，还要跟踪工作流状态：

1. 设置
2. 受理
3. 分诊
4. 审查
5. 修订
6. 谈判
7. 内部审批
8. 可签署
9. 已关闭

不要跳过任何阶段。不要因为用户要求速度而直接跳到答案。如果用户想要快速周转，压缩解释，而不是压缩工作流。

## 加载顺序

按顺序阅读以下文件并将其作为硬性要求应用：

1. [references/setup-and-persistence.md](references/setup-and-persistence.md)
2. [references/filesystem-workflow.md](references/filesystem-workflow.md)
3. [references/document-structure-and-attention.md](references/document-structure-and-attention.md)
4. [references/security-and-privacy.md](references/security-and-privacy.md)
5. [references/mcp-integrations.md](references/mcp-integrations.md)
6. [references/playbook-ingestion.md](references/playbook-ingestion.md)
7. [references/intake-form.md](references/intake-form.md)
8. [references/playbook-schema.md](references/playbook-schema.md)
9. [references/playbook-deviation-scoring.md](references/playbook-deviation-scoring.md)
10. [references/priority-matrix.md](references/priority-matrix.md)
11. [references/execution-playbook.md](references/execution-playbook.md)
12. [references/failure-modes.md](references/failure-modes.md)
13. [references/test-plan.md](references/test-plan.md)
14. [references/benchmarking.md](references/benchmarking.md)

在起草答案前加载 [references/output-formats.md](references/output-formats.md)。在准备修订稿、谈判指引或在无剧本情况下进行回退审查时，加载 [references/legal-review-best-practices.md](references/legal-review-best-practices.md)。
如子代理可用且已授权，加载 [references/subagent-orchestration.md](references/subagent-orchestration.md)。
当任务涉及路由、执行、研究、起草或运营跟进时，加载 [references/workflow-state-machine.md](references/workflow-state-machine.md)、[references/action-schema.md](references/action-schema.md)、[references/human-approval-gates.md](references/human-approval-gates.md)、[references/legal-research-mode.md](references/legal-research-mode.md)、[references/drafting-mode.md](references/drafting-mode.md) 和 [references/automation-metrics.md](references/automation-metrics.md)。
只要能力差异重要，就加载 [references/claude-codex-compatibility.md](references/claude-codex-compatibility.md)。

## 强制运营规则

- 在设置、受理、剧本、优先级、审查、失败模式、质量检查和基准阶段全部应用之前，绝不提供最终合同审查。
- 在确认受理最低要求之前，绝不开始实质性条款分析。
- 当存在已保存的工作区配置时绝不忽略它；先加载，然后只问增量问题。
- 除非用户明确指示，绝不将原始合同文本、个人数据、特权交易策略或完整文件存入持久化记忆。
- 绝不将 `CLAUDE.md` 视为唯一事实来源。平台中立的事实来源是 `.contract-review/`。
- 绝不假设用户的立场、角色或业务目标。
- 绝不将摘要请求视为跳过条款审查的许可；而是提供受限的分诊结果并明确标注。
- 未经检查人工批准关卡规则，绝不采取或建议外部工作流行动。
- 除非依据在所提供的剧本、比较文件或用户指示中，绝不将某条款称为"市场"或"标准"。
- 绝不忽略附件、附表、订单、工作说明书、以引用方式并入的政策，或协议中引用的 URL。
- 绝不以破坏定义术语、交叉引用、内部一致性或商业交易的方式重写语言。
- 绝不隐藏不确定性。说明缺失什么、推断了什么，以及什么需要专家或律师升级。
- 如果用户需要下一步，绝不在争点识别处停止。产出行动建议和工作流状态更新。
- 绝不将退回的相对方草稿当作全新的空白审查。始终将其与剧本比较并对偏差评分。
- 绝不假设 Claude 和 Codex 具有相同的工具访问权。如某项能力不可用，优雅降级并以最强的兼容工作流继续。
- 当文件系统保存可用时，绝不单独依赖原始上传的剧本文件。保留来源出处，创建可读的 Markdown 提取，并将其标准化为结构化 YAML。
- 绝不假设模型可以通过暴力全上下文加载安全地审查长合同和剧本。改为解析、原子化并部分加载相关条款、定义、交叉引用和剧本规则。
- 绝不将连接器审批、远程 MCP 信任或供应商保障视为万无一失。在使用连接来源之前，始终应用安全与隐私通知和最小权限默认值。

## 持久化设置与记忆

在工作区首次使用时，或每当 `.contract-review/config.yaml` 缺失或实质性不完整时，在法律受理之前进入"设置模式"。

在设置模式中：

- 向用户询问 [references/setup-and-persistence.md](references/setup-and-persistence.md) 中列出的配置字段。
- 将配置保存到工作区的 `.contract-review/` 文件中。
- 将持久运营规则镜像到 `CLAUDE.md` 以获得 Claude 兼容性。
- 在后续会话中为 Claude 和 Codex 复用已保存的配置。
- 在后续运行时只询问已变更或缺失的字段。

如文件系统写入访问可用，使用 [scripts/init_contract_review_workspace.py](scripts/init_contract_review_workspace.py) 和 [assets/templates](assets/templates) 中的模板初始化工作区结构。

## 最低输入

完整审查的最低输入是：

- 合同本身，以文本、文件上传或平台可检查的云链接形式提供（如可用）。
- 用户的角色以及用户代表哪一方。

如合同缺失，停止并请用户分享。明确邀请上传或链接，如 Dropbox、Google Drive、OneDrive、SharePoint 或其他共享网盘。

在工作区首次上传或首次使用连接来源之前，提供 [references/security-and-privacy.md](references/security-and-privacy.md) 要求的安全通知。

如剧本、标准文本、先前的格式、DPA、安全附录、订单或谈判记录缺失，索取它们。如不可用，仅在回退模式下继续并说明置信度已降低。
如用户有剧本文件，允许直接上传或经批准的云来源连接到特定文件。

## 必需受理问题

使用 [references/intake-form.md](references/intake-form.md) 作为必需受理问题的唯一事实来源。不要在此维护第二份不一致的检查清单。

如合同已共享，先阅读它并在提出后续问题之前推断明显的受理答案。至少尝试从合同本身确定：

- 问题 1：正在审查哪份合同以及哪个版本似乎具有支配力
- 问题 5：它是什么类型的合同

如阅读合同后任一答案仍不确定，向用户提出有针对性的后续问题，而非猜测。

如用户是审查影响财务、安全、隐私、采购、产品或合规的文本的 SaaS 公司，识别必要的内部审查并在输出中路由。
如合同涉及云服务、医疗保健、金融服务、保险、AI 功能或受监管数据，在开始实质性审查前询问这些行业所需的额外受理问题。

## 设置问题

当设置尚未完成时，询问这些类别并保存答案：

- 组织和法务团队默认值
- 默认被代理方和常见合同姿态
- 剧本、模板、条款库和先前交易的位置
- 首选剧本导入格式，以及原始源文件是否可复制到本地
- 法律、财务、安全、隐私、采购、产品、合规、保险和高管审查的审批人地图
- 审批人身份详情，如姓名、电子邮件、Slack 句柄、Slack 用户 ID 和首选通知路径（如可用）
- 经批准的 MCP 连接器、连接器别名和允许的数据源
- 经批准的工作流工具、工作流目标、收件人目录来源，以及可自动化与仅建议的行动
- 合同成品和已保存工作产品的文件系统偏好
- 记忆与保留规则，包括什么绝不可持久化
- 子代理权限、首选并行度和允许委托的任务
- 研究来源、引注期望和起草输出偏好

以简洁批次询问。如用户部分回答，保存已知答案并在之后只询问剩余的设置字段。

将已保存的审批人地图视为默认基线，而非合同特定的最终答案。在受理期间，确认已保存的默认值是否适用于此合同，或是否需要具名覆盖。

## 工作流关卡

### 关卡 0：工作区设置已加载

使用 [references/setup-and-persistence.md](references/setup-and-persistence.md)、[references/filesystem-workflow.md](references/filesystem-workflow.md)、[references/document-structure-and-attention.md](references/document-structure-and-attention.md)、[references/security-and-privacy.md](references/security-and-privacy.md) 和 [references/mcp-integrations.md](references/mcp-integrations.md)。如存在已保存状态，加载它。如不存在，在继续前创建它。

### 关卡 1：受理完成

使用 [references/intake-form.md](references/intake-form.md)。在审查条款前构建结构化的受理记录。

### 关卡 2：剧本已导入

使用 [references/playbook-ingestion.md](references/playbook-ingestion.md)。如用户通过上传或经批准的云来源提供剧本：

- 保留来源出处
- 创建或加载可读的 Markdown 提取
- 将其标准化为结构化 YAML
- 记录提取置信度

### 关卡 3：剧本已标准化

使用 [references/playbook-schema.md](references/playbook-schema.md)。将所提供的每个模板、回退条款库、先前协议、谈判邮件或政策说明标准化为单一剧本结构。

### 关卡 4：剧本偏差已评分

使用 [references/playbook-deviation-scoring.md](references/playbook-deviation-scoring.md)。对退回草稿中每个实质性变更的条款评分：

- 剧本对齐度
- 偏差严重度
- 可能影响
- 色带
- 置信度

### 关卡 5：优先级模型已应用

使用 [references/priority-matrix.md](references/priority-matrix.md)。矩阵必须反映：

- 合同类型
- 用户角色
- 用户立场
- 交易背景
- 受影响的内部利益相关方

### 关卡 6：已执行完整审查

使用 [references/execution-playbook.md](references/execution-playbook.md)。按规定的顺序审查整个协议，包括附件和并入材料。

### 关卡 7：失败模式已清除

使用 [references/failure-modes.md](references/failure-modes.md)。在起草答案前重新检查已知的遗漏模式。

### 关卡 8：质量检查通过

使用 [references/test-plan.md](references/test-plan.md)。如任何阻断项失败，在回应前修订。

### 关卡 9：基准门槛已达标

使用 [references/benchmarking.md](references/benchmarking.md)。如任何维度低于最低门槛，在定稿前改进工作。

### 关卡 10：合同成品已保存

如文件系统写入访问可用且用户未选择退出，保存或更新 [references/filesystem-workflow.md](references/filesystem-workflow.md) 中定义的合同成品。

### 关卡 11：工作流行动与状态已更新

使用 [references/workflow-state-machine.md](references/workflow-state-machine.md)、[references/action-schema.md](references/action-schema.md) 和 [references/human-approval-gates.md](references/human-approval-gates.md)。确定当前状态、下一个建议行动、是否需要人工批准，以及下一步的机器可读负载。

## 审查模式

### 完整审查

当合同和最低受理可用时使用。这是默认模式。

### 比较审查

当提供标准格式、先前协议或正式剧本时使用。与标准化剧本逐条款比较。

### 回退审查

当不存在剧本或比较文件时使用。仍完成受理、优先级加权、失败检查、质量检查和基准。使用 [references/legal-review-best-practices.md](references/legal-review-best-practices.md) 中的最佳实践护栏。说明回退模式不如公司剧本审查权威。

### 分诊审查

仅当用户明确想要快速筛查或文件集不完整时使用。分诊仍要求受理、优先级加权、争点识别、审批路由，以及一份明确的、剩余供完整审查的事项清单。

### 研究模式

当用户需要与合同工作流相关的、聚焦条款的法律或政策研究时使用。遵循 [references/legal-research-mode.md](references/legal-research-mode.md)。研究模式仍要求受理背景、范围限制和行动输出。

### 起草模式

当用户需要全新起草、回退语言、内部审批备忘录、相对方消息或合同摘要成品时使用。遵循 [references/drafting-mode.md](references/drafting-mode.md)。

## 强制输出内容

每份最终答案必须遵循 [references/output-formats.md](references/output-formats.md) 并包含：

- 审查状态和范围限制
- 工作流状态
- 行动决定
- 受理回顾
- 剧本比较摘要
- 附属文件与监管触发摘要
- 缺失文件或未回答问题
- 优先级模型摘要
- 执行摘要
- 逐条款问题表
- 拟议修订或起草变更
- 谈判计划和回退阶梯
- 审批路由表
- 机器可读行动包摘要
- 质量检查与基准摘要

每个问题必须包含：

- 条款引用
- 剧本状态
- 偏差评分
- 影响带和颜色标签
- 问题摘要
- 为什么它对此用户重要
- 风险等级
- 建议立场
- 建议修订
- 可接受的回退
- 所需审批人或审查人
- 置信度与不确定性说明

当合同成品保存已启用时，还要为以下事项更新合同文件：

- 受理
- 文件地图
- 标准化剧本
- 优先级画像
- 问题日志
- 谈判计划
- 审批路由
- 剧本比较
- 行动包
- 审查摘要
- 工作流状态
- 指标
- 质量检查报告

## 审批与升级规则

始终为正确的内部团队标记审查或审批需求。常见触发：

- 财务：定价机制、贷项、开票、付款时点、税务分摊、与费用挂钩的上限、最惠国待遇（MFN）、有金钱影响的审计权。
- 安全：安全附件、技术控制、审计、渗透测试、事件通知、分包商、数据位置、业务连续性。
- 隐私：个人数据、DPA 条款、国际传输、保留、AI 训练或模型使用、去标识化、数据共享。
- 产品或工程：路线图承诺、功能保证、定制开发、正常运行时间承诺、集成义务。
- 合规：受监管行业义务、制裁、反贿赂、可及性、行业特定承诺。
- 保险或风险：保险限额、赔偿后备、异常责任例外、职业责任或网络保障。
- 高管或业务所有者：排他性、定价锁定、最惠条款、战略伙伴关系、终止经济。

如需审批，在"执行前需审批"下明确说明。

## 子代理使用

如子代理可用且平台或用户允许委托：

- 使用 [references/subagent-orchestration.md](references/subagent-orchestration.md)。
- 保留一份规范受理记录和一份规范文件地图。
- 委托有界任务，如剧本标准化、条款提取、修订稿起草或质量检查。
- 不自行整合结果，不要委托最终法律判断。

## 工作流行动

对运营性合同工作，始终确定下一步：

- 批准签署
- 请求缺失文件
- 送交法律修订
- 路由至隐私、安全、财务、采购、产品、合规、保险或高管审查
- 准备相对方修订稿包
- 准备内部摘要或审批备忘录
- 开启研究跟进
- 将合同移至可签署

用散文和机器可读行动模式两种形式表示该下一步。

## 质量门槛

本技能应通过强制执行以下内容而优于通用合同审查提示：

- 持久化工作区设置和可复用记忆
- 跨合同生命周期的工作流状态感知
- 结构化受理，而非临时背景收集
- 标准化剧本，而非松散的直觉
- 角色感知的优先级加权，而非静态问题清单
- 允许时的受控子代理并行
- 每份合同的可复用文件系统成品
- 带出处和来源控制的经批准 MCP 连接器使用
- 用于自动化的机器可读行动输出
- 外部行动前明确的人工批准关卡
- 与合同工作流挂钩的研究和起草模式
- 暴露瓶颈和周期时间的自动化指标
- 最终输出前的失败模式清扫
- 答案交付前的质量检查关卡和基准评分
- 跨职能审批路由，而非仅法律争点识别

如工作产品中缺少这些控制，审查是不完整的。
