---
name: labor-claims-procedure
description: 劳动争议金额计算、时效和程序路径。基于争点分析结果,逐项计算请求金额(N/2N/加班费/工伤待遇),确定时效和程序策略。
license: AGPL-3.0
metadata:
  homepage: https://jinlishan.com/
  author: 金莉珊律师（微信jinlishan_）
  version: 1.4.4
---

# 劳动争议金额与程序

1. 读取案件状态和上游已复核的争点、证据与法源。先判断请求权基础和公式类型，再调用计算器；不得由金额高低反推法律适用，也不得在 N、N＋1、2N 之间自动择高。
2. 使用 `python3 scripts/calculate_claims.py --state <case_state.json> --scaffold` 生成待复核骨架。骨架只提示可能公式，不写入 `claims[]` 或 `calculations[]`，也不解锁金额节点。
3. 对每个数值输入记录案件来源 ID；逐项确认计算口径、相关日期、适用法源和风险。N、N＋1、2N 必须以 `cap_applies=0/1` 明确确认三倍社平工资封顶是否适用；适用时必须提供对应日期和地域的 `monthly_wage_cap` 参数。
4. 使用 `python3 scripts/calculate_claims.py --state <case_state.json> --input <经复核输入.json>` 执行计算。需要动态数值时，以 `--parameter-package <参数包.json>` 追加符合 `references/parameter-package.schema.json` 的版本化参数包，不在公式中硬编码年度社平工资、最低工资或地域待遇数值。
5. 支持的专业公式包括：经济补偿 N、N＋1、违法解除赔偿金 2N；工作日 150%、休息日 200%、法定节假日 300% 加班工资；一次性伤残补助金、伤残津贴、地域工伤待遇、三笔一次性待遇合计；竞业限制补偿和金额合计。金额使用 `ROUND_HALF_UP` 精确到分。
6. 正例：输入、来源、法源及参数完整且适用时，生成金额、算式、中间步骤和 `.casework/calculations/ledger.json`／`ledger.md`。反例：存在 `pending_inputs` 时不得生成貌似精确的金额；缺少、拼错或多传公式字段，参数日期／地域不适用，或者台账金额、算式、步骤和内容摘要被篡改时，必须拒绝通过。
7. 完成节点前，每个金额请求都以唯一 `claim_id` 写入 `claims[]`，并与 `calculations[]` 中唯一 `calculation_id` 双向关联。只有状态为 `calculated`、可独立重算且没有待确认输入时才能进入下游；金额门禁不得豁免。旧占位请求只有在明确使用 `--replace-existing-calculations` 时才可升级，替换前状态须保留在历史快照。
8. 使用 `python3 scripts/analyze_procedure.py --state <case_state.json> --scaffold` 为每个已复核争点生成待复核程序骨架。骨架只用于提示逐项审查时效、管辖、一裁终局、临时救济和后续救济路径，不写入 `procedural_assessments[]`，也不解锁程序门禁。
9. 律师／Agent 应结合已核验的实体、时间与地域规则完成程序判断，再使用 `python3 scripts/analyze_procedure.py --state <case_state.json> --input <经复核的程序分析.json>` 写入台账。每个争点必须记录当前案件地域与分析日，并使用本争点已核验、已采用且适用的法源支持结论。明确判定时效内／外时，起算日、截止日与分析日必须逻辑一致。
10. 金额结果和程序结果是 `claims_procedure` 的两组独立完成条件：已复核争点必须全部具有 `analysis_status=reviewed` 的程序分析，且 `pending_items` 为空。只完成金额计算、只完成程序分析，或任一程序项仍待确认，都不得进入策略审批；`reviewed_procedure_path` 门禁不得豁免。脚本不自动替律师选择程序策略。
