---
name: labor-dispute-casework
description: 劳动争议办案总控与案件编排器。当律师需要启动、继续或跨阶段管理中国劳动争议案件，需要判断下一步专业任务、维护 case_state、执行审批门禁或回写阶段成果时使用。支持劳动者方和用人单位方，默认浙江口径。
license: AGPL-3.0
metadata:
  homepage: https://jinlishan.com/
  author: 金莉珊律师（微信jinlishan_）
  version: 1.4.4
---

# 劳动争议办案总控

只负责案件状态、节点路由、门禁与回写；把实体任务交给对应专业 Skill。

## 不可变边界

1. 先记录用户已明确的 `task_context`、`representation`、`stage`、`jurisdiction` 和 `analysis_date`。只对尚不明确且会影响处理路径的字段提问；无法唯一判断时保持 `undetermined`，不得读取或处理案件文件。
2. 第二轮起先读已有 `case_state.json`，不得将后续阶段当成新案件。
3. 依“原始材料或当前确认＞已确认案件状态＞AI 生成内容”使用信息。
4. 高风险结论、文书起草和对外交付必须经明示审批节点。
5. 默认只生成“律师复核初稿”，不得自动进入提交状态。最终提交版必须直接派生自当前文件哈希已获律师批准的初稿，并作为新产物重新验证、重新审批。

## 启动

1. 读取 [节点契约](../../references/node-contracts.md)、[交付物规范](../../references/output-layout.md) 和 `../../workflow/graph.json`。
2. 无案件状态时，运行 `python3 scripts/case_state.py init --output <case-root>/.casework/case_state.json`；新状态从 `task_intake` 节点启动。
3. 运行 `python3 scripts/workflow_graph.py route --state <case-root>/.casework/case_state.json` 获取可进入节点和当前节点的机器完成条件。
4. 当前节点为 `task_intake` 时，完整读取 `../labor-task-intake/SKILL.md`。代理立场不得仅凭文件来源推测；但用户已明说“用人单位方”、“分析并写仲裁答辩状”时，应直接记录已明确的立场、任务和仲裁阶段，不重复追问。
5. 使用 `python3 scripts/case_state.py set-task --input <case-root>/.casework/case_state.json --representation <employee|employer> --stage <程序阶段> --user-request <本轮任务>` 就地更新单一状态，再由 `python3 scripts/workflow_graph.py transition --state <case-root>/.casework/case_state.json --event pass --actor <执行者>` 进入 `material_ingestion`。两个命令默认不传 `--output`。
6. 根据后续节点只调用一个主 Skill；法源、证据或计算可作必要的并行分支，但结果合并到同一份《案件研判报告》，节点运行文件放入 `.casework/`。用户侧正式成果默认交付 `.docx`，Markdown 仅作为内部工作稿；用户明确要求 Markdown 时例外。
7. 节点完成后按 `workflow/graph.json` 登记真实业务状态和产物，再按 `pass`、`return`、`pause` 或 `escalate` 更新状态；不得用空数组或空备注绕过门禁。
8. 任务确实没有文件或证据时，只有在用户明确确认具体原因后，才可运行 `python3 scripts/workflow_graph.py record-waiver --state <case-root>/.casework/case_state.json --requirement <条件编号> --reason <具体原因> --confirmed-by <确认人>`。该命令只对当前节点中标记可豁免的条件生效；`draft_artifact` 和 `report_backed_validations` 不允许豁免。

## 技能路由

- 任务、代理立场与阶段确认：`labor-task-intake`。
- 原始文件保全、文字层与本地 OCR 路由：`labor-material-ingestion`。
- 接案、材料、时间轴：`labor-case-intake`。
- 争点、请求、抗辩：`labor-issue-analysis`。
- 证据与举证责任：`labor-evidence-analysis`。
- 国家法及浙江口径：`labor-authority-research`。
- 金额、时效、程序期限：`labor-claims-procedure`。
- 法律文书初稿：`labor-document-drafting`。
- 交付前对抗性复核：`labor-case-validator`。

## 阶段回写

记录新增材料、事实状态、证据缺口、法源验证、期限、产物、审批结果和下一步。只有用户明确确认的内容才写入 `decisions`。用户已明确要求特定文书的，该指令可作为生成“律师复核初稿”的授权记录；只有互斥策略未确定时才再次暂停。
