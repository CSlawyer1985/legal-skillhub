---
name: labor-task-intake
description: 劳动争议办案的前置任务确认。当用户启动新案件、给出案件文件但未明确要求，或代理立场、程序阶段尚未确认时使用。在读取或处理案件材料前必须先完成。
license: AGPL-3.0
metadata:
  homepage: https://jinlishan.com/
  author: 金莉珊律师（微信jinlishan_）
  version: 1.4.4
---

# 劳动争议任务确认

1. 在打开、提取、OCR、统计或分析案件文件前，先从用户当前表述中提取本轮具体任务、代理立场和程序阶段。
2. 用户已明说“劳动者方”或“用人单位方”时直接确认；不得仅从申请书、答辩书、文件名或材料来源推测代理立场。
3. 用户明确要求“仲裁申请书／仲裁答辩状”、“一审起诉状／答辩状”或“上诉状／二审答辩”时，可据此唯一确定对应阶段，并在 `task_context` 记录推断依据。文书种类仍可对应多个阶段时才询问。
4. 一次最多问三个短问题；用户已明确或根据明确任务可唯一确定的项目不重复询问。
5. 未获得用户回答时，保持 `representation=undetermined`、`stage=undetermined`和 `current_node=task_intake`；不调用材料处理或实体分析 Skill。
6. 获得确认后，运行 `python3 scripts/case_state.py set-task --input <case-root>/.casework/case_state.json --representation <employee|employer> --stage <程序阶段> --user-request <本轮任务>`，按需追加 `--jurisdiction`、`--requested-output` 和 `--confirmed-by`，就地回写 `task_context`、`representation`、`stage` 和 `jurisdiction`，不生成根目录节点快照。
7. 运行 `python3 scripts/workflow_graph.py transition --state <case-root>/.casework/case_state.json --event pass --actor <执行者>`；只有门禁通过后才进入 `material_ingestion`。

建议提问：

- “这次希望我使用该 Skill 完成什么具体任务？”
- “本案代理劳动者方还是用人单位方？”
- “案件当前处于哪个程序阶段？”
