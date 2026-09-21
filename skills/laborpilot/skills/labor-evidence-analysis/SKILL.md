---
name: labor-evidence-analysis
description: 劳动争议证据要件分析和证据清单生成。基于争点分析结果,逐项审查证据缺口,标注举证责任分配,生成本案证据清单。
license: AGPL-3.0
metadata:
  homepage: https://jinlishan.com/
  author: 金莉珊律师（微信jinlishan_）
  version: 1.4.4
---

# 劳动争议证据分析

1. 读取案件状态及已复核争点，按每个 `element_id` 生成待复核骨架：

   ```bash
   python3 scripts/build_evidence_chain.py \
     --state <case-root>/.casework/case_state.json \
     --scaffold
   ```

2. 骨架只提示要件、事实和候选材料关系，不得因材料被引用就推定证据三性、证明力或证明标准已满足。
3. 围绕每个待证命题核对证据项、材料来源与证明目的，并记录初始举证主体、证据控制方、责任转移条件和举证不能后果。考勤、工资台账、规章制度等由单位掌握时，须同时写明劳动者的初步举证和责任转移条件，依具体规则评估不利后果，不机械表述为必然“推定成立”。
4. 对 `partially_sufficient`、`insufficient`、`disputed` 或 `to_verify` 的证据链，必须同时列明缺口和可执行的补证行动。完全缺证时仍建立 `gap_only` 或对方／第三方掌握的证据链，不得使用豁免跳过。
5. 将经 Agent／律师复核的完整证据链写入状态：

   ```bash
   python3 scripts/build_evidence_chain.py \
     --state <case-root>/.casework/case_state.json \
     --input <经复核的证据链.json>
   ```

6. 执行器会反向回写构成要件及对方路径的 `evidence_ids`，并要求每个构成要件都有证据链或缺口链。证据评估为 `sufficient` 时，至少存在一项已关联材料且真实性状态已明确的 `available` 证据。旧 `evidence[]` 仅为占位结构时，提供完整证据链并显式使用 `--replace-existing-evidence`，替换前状态保留在 `.casework/history/`。
