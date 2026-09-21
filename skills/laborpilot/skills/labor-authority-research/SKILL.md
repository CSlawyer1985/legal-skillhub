---
name: labor-authority-research
description: 劳动争议法律法规、规范性文件和浙江地方口径的检索与引用校验。当需要按争点、法规名、文号、条号、地域、时间效力检索，或核验 document_id、article_id、页码和效力状态时使用。
license: AGPL-3.0
metadata:
  homepage: https://jinlishan.com/
  author: 金莉珊律师（微信jinlishan_）
  version: 1.4.4
---

# 劳动争议法源研究

> 废止复核（2026-09-07）：已列入浙江2026-08-25目录的七件劳动文件（2009年试行意见、解答一至五、2014年加班工资仲裁时效解答）不得作现行依据。历史观点允许研究，须另核可适用法源；目录发布日期不直接作为效力终止日。解答六、七及独立仲裁文件不连带废止。


1. 读取已复核争点、案件管辖地和 `analysis_date`，按每个构成要件生成待核验任务：

   ```bash
   python3 scripts/build_authorities.py \
     --state <case-root>/.casework/case_state.json \
     --scaffold
   ```

2. 骨架不写入 `rules[]`。内置知识中的条文号、地方口径和规则摘要只是检索线索，不得直接标记为已验证法源。
3. 使用当前 Agent 环境可用的官方来源、法律数据库或外部 MCP，核对法律全称、制定机关、文号、条号和完整条文。同时保存来源 URL、检索时间、效力状态和起止日期。不绑定具体工具，但正式采用记录的 `source_type` 只能为 `official` 或 `legal_database`。
4. 以本案具体的 `relevant_date` 核对新旧法，不只看当前是否有效。全国规则、地方性法规、地方规范和参考口径必须分层；地方规则的 `applicable_jurisdictions` 必须与案件管辖地匹配。
5. 将经 Agent／律师复核的外部核验结果适配为案件法源矩阵：

   ```bash
   python3 scripts/build_authorities.py \
     --state <case-root>/.casework/case_state.json \
     --input <经复核的法源核验结果.json>
   ```

6. 正式采用的法源必须同时为 `verification_status=verified` 和 `applicability_status=applicable`，且不得为未生效或效力未明规则。一般已修改、废止或失效规则如因历史事实仍需适用，须核明时间适用并写明 `warning` 与理由；本次浙江目录七件地方文件仅作 `reference_only` 或 `excluded`，不得借历史日期正式采用。
7. 执行器会计算完整条文的 SHA-256，反向回写构成要件和对方路径的 `rule_ids`，并要求每个构成要件都关联已验证且适用的法源。该完成条件不得豁免。旧 `rules[]` 仅为占位结构时，使用 `--replace-existing-rules` 显式升级，替换前状态保留在 `.casework/history/`。

已验证法源、适用条件与浙江口径写入 `01_案件研判报告_vN.md`；索引、检索 JSON 和引用校验结果存入 `.casework/authority/`，不单独向用户交付“法源检索记录”。
