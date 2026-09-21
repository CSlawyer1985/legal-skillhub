---
name: labor-case-intake
description: 劳动争议案件接入、材料盘点和初步分流。当需要建立材料清单、案件时间轴、当事人询问提纲、识别劳动关系类型或判断程序阶段时使用。不用于直接撰写诉讼文书。
license: AGPL-3.0
metadata:
  homepage: https://jinlishan.com/
  author: 金莉珊律师（微信jinlishan_）
  version: 1.4.4
---

# 劳动争议案件接入

1. 先读 `.casework/case_state.json`；不改动原始材料。如 `task_context` 未完整、`representation=undetermined` 或 `stage=undetermined`，立即返回 `task_intake`，不得建立案件底盘或继续分析。
2. 为每份材料记录来源、形成时间、真实性、关联性、合法性、证明目的及待核问项。
3. 将经人工或 Agent 标注的事实候选整理为 JSON，使用 `statement`、`status`、`sources`、`occurred_on` 和可选 `source_locators`。相互矛盾的事实还应分别填写 `conflicts_with_fact_ids`、`conflict_status`、`conflict_explanation` 和 `conflict_next_action`，再运行：

   ```bash
   python3 scripts/build_timeline.py \
     --state <case-root>/.casework/case_state.json \
     --input <事实候选.json> \
     --extract-from-materials
   ```

   `--extract-from-materials` 可省略；启用时只从已登记派生文本提取含日期的候选句，并一律标记为 `to_verify`。执行器会生成 `.casework/intake/timeline.json` 和 `timeline.md`，脱敏身份证号与手机号，严格区分有证据支撑、当事人陈述、对方主张、双方争议和待查明。冲突关系必须双向一致；未解决冲突须写明具体核实行动，且不得把任一冲突事实标记为 `supported`。
4. 识别主体、关系性质、用工时间、工作地、合同、工资、社保、解除终止及程序现状。
5. 将材料清单、时间轴和初步分流写入同一份 `01_案件研判报告_vN.md`；待询问项和缺失材料写入 `03_待补材料与行动清单_vN.md`。不单独生成“接入底稿”。
6. 不做最终责任判断；将可能争点交给 `labor-issue-analysis`。
7. 完成节点前确认每条事实具有唯一 `fact_id`、非空事实陈述、合法状态和可核验来源关系；`supported` 必须关联已登记材料。冲突事实不得自引用、引用不存在事实或只保存单向关系，双方冲突状态必须一致。不得只更新人读报告而让案件状态保持为空。

完成条件见 [节点契约](../../references/node-contracts.md)，案件状态规则见 [case-state](../../references/case-state.md)。
