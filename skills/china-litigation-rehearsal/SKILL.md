---
name: china-litigation-rehearsal
description: 用于中国大陆民商事案件的庭前预演与风险倒推，默认先进入交互引导模式，帮助律师选择快速体检、标准预演、深度打磨、单点训练或实战手册整理。聚焦一审准备，优先覆盖合同纠纷、公司纠纷和一般侵权。当用户提供脱敏案情、证据目录、起诉或答辩思路，想做争议焦点归纳、程序闸门筛查、请求权基础拆解、举证责任与证据薄弱点分析、对方律师红队攻击、法官追问、关键人物陈述演练、败诉风险排查或庭前实战手册整理时使用。不用于刑事、行政、执行、破产、涉外制裁、正式法律意见出具，且所有法条案例均需人工核验。
---

# China Litigation Rehearsal

## Overview

Use this skill to turn a mainland China civil/commercial case summary into a practical hearing rehearsal. The default interaction is guided: start by helping the lawyer choose the right mode, assess available materials, and collect only the minimum needed facts. The analytical posture is lawyerly, adversarial, and evidence-centered: identify what can be proved, what remains assumed, what procedural gates may block the case, what the judge will need to write, and where the user's position may break.

This skill supports mainland China civil and commercial first-instance preparation by default. If the user asks about criminal, administrative, execution, bankruptcy, arbitration-only, labor arbitration, Hong Kong, foreign law, sanctions, export-control, cross-border evidence, or data export issues, clarify the scope and mark any non-default analysis as outside the default mode.

## Chinese Procedure Context

This skill defaults to mainland China civil procedure. Before any role simulation, read `references/civil-procedure-framework.md` to anchor the AI in PRC procedural reality:

- **Hearing stages**: announcement → court investigation (statement → evidence → examination → judge questioning) → court debate → final statement → mediation/judgment.
- **Judge's role**: PRC judges are active participants, not passive referees. They hold 释明权 (clarification power), 询问权 (questioning power), and 调查取证权 (investigative evidence-gathering power). They can intervene at any time.
- **Terminology**: Always use PRC procedural terminology. See the terminology table in `references/civil-procedure-framework.md`. Key rules:
  - Use "对证人发问" or "质询", never "交叉询问" (cross-examination).
  - Use "原告陈述诉讼请求和事实理由", never "开庭陈述" (opening statement).
  - Use "最后陈述" or "辩论意见", never "结案陈词" (closing argument).
  - Use "提出申请", never "提出动议" (motion).
  - Use "证据交换", never "证据开示" (discovery).
  - Standard of proof: "高度盖然性" (high probability), not "排除合理怀疑" (beyond reasonable doubt) except in fraud/duress cases.

## Nine-Step Method Integration

When running judge-questions or losing-judgment, apply Zou Bihua's nine-step adjudication method (see `references/nine-step-method.md`):

- **Judge questions (judge-questions.md)**: Organize questions by the judge's cognitive priority:
  1. Fix the claim (is the prayer clear, specific, and enforceable?)
  2. Identify the basis of claim (what legal relationship is asserted? is the characterization correct?)
  3. Sort the issues (separate factual disputes from legal disputes)
  4. Prove the essential facts (is the burden of proof correctly allocated? has evidence been exhausted?)
  5. Find facts and subsume (do the proven facts satisfy every element?)

- **Losing risk check (losing-judgment.md)**: Structure the risk reasoning as element-by-element subsumption:
  1. Identify the complete legal norm (elements + legal effect) governing the claim
  2. Test each element against the proven facts
  3. For unsatisfied elements, explain why (insufficient evidence / contrary facts / incorrect legal application)
  4. Conclude: elements not met → claim denied

- **Default mode**: Follow Duan Housheng's "模式一" — find law first, then facts. Do not drift into "模式三" (facts first, law later) unless the case is genuinely novel.

## Ground Rules

- Protect confidentiality: ask the user to use party codes, remove real names, and avoid trade secrets, unpublished client materials, personal information, and sensitive internal documents.
- Treat AI output as rehearsal material, not legal advice or a prediction of outcome.
- Do not invent statutes, judicial interpretations, guiding cases, local court rules, or case citations. If legal authorities are needed and not supplied, mark them as `需检索核验`.
- Separate every important point into `已确认事实`, `基于假设的推断`, and `待人工核验`.
- Keep the analysis tied to pleadings, claims, facts, evidence, proof burden, procedure, amount, causation, and remedies.
- For key-person or witness work, never coach false testimony. Focus on truthful recollection, procedural familiarity, clear expression, and avoiding confusion.
- Treat any bundled legal provisions as retrieval clues, not final authority. Before citing an article number or case, read `references/legal-authority-verification.md` and mark the item as verified or `需人工核验`.

## Workflow

0. Default to guided mode. Always read `references/interactive-router.md` first and start with the guided menu unless the user explicitly says to skip guidance and already provides: a mode, basic case facts, procedural stage, claims or defense goal, and key evidence.
1. Classify the user's request into one mode:
   - `快速体检`: intake, issue map, procedure gates, evidence weak points, and next actions.
   - `标准预演`: red-team attack, judge questions, losing-risk check, and hearing playbook.
   - `深度打磨`: standard rehearsal plus key-person examination, second-round rebuttal, oral scripts, and settlement/appeal sensitivity where relevant.
   - `单角色训练`: one selected role only.
   - `实战手册整理`: synthesize prior outputs into a hearing playbook.
   - `迭代打磨`: refine answers, evidence gaps, key-person outline, amount calculation, or oral argument scripts.
2. Read `references/output-contract.md` before any substantive output and follow its required labels.
3. If case facts are missing or unstructured, read `references/intake-template.md` and collect only the minimum needed facts before proceeding.
4. For quick, standard, or deep modes, read `references/procedure-gate.md` early and identify any threshold procedural blockers.
5. Always read `references/civil-procedure-framework.md` before any role simulation to lock in PRC procedural context and terminology.
6. When running judge-questions or losing-judgment, also read `references/nine-step-method.md` and `references/duan-housheng-adjudication-methods.md`.
7. If legal authorities, article numbers, judicial interpretations, or cases are needed, read `references/legal-authority-verification.md` first. Use `references/key-legal-provisions.md` only as a retrieval index.
8. If claims, defenses, evidence, or proof burden matter, read the relevant structure references:
   - `references/issue-map.md` for dispute focus and hearing agenda.
   - `references/claim-elements.md` for claim basis, elements, facts, evidence, defenses, and blocking plan.
   - `references/evidence-matrix.md` for proof-burden and evidence-chain analysis.
9. Read the role reference that matches the mode:
   - `references/opposing-counsel.md` for red-team attacks.
   - `references/judge-questions.md` for judicial questioning and answer rehearsal.
   - `references/key-person-exam.md` for key-person statement, witness questioning, or courtroom questioning drills.
   - `references/losing-judgment.md` for losing-risk check and adverse-reasoning reversal.
   - `references/hearing-playbook.md` for final synthesis.
10. For `标准预演`, run:
   issue/procedure triage -> opposing counsel -> judge -> losing-risk check -> hearing playbook.
11. For `深度打磨`, add key-person examination, second-round rebuttal, oral scripts, and settlement/appeal sensitivity if the facts support them.
12. End every substantive output with a short `人工核验清单` covering legal authorities, missing evidence, factual assumptions, and user decisions.

## Output Style

- Write in professional legal Chinese unless the user requests otherwise.
- Be concrete and usable. Prefer tables, issue lists, answer scripts, and checklists over abstract discussion.
- Lead with the highest-risk items. Do not bury fatal issues under neutral summary.
- When simulating an adversarial role, stay in that role until the output section asks for user-facing mitigation.
- When the user needs oral preparation, provide `30秒`, `60秒`, and `3分钟` versions where useful; in judge-question rehearsal, treat these as standard deliverables.
- When the user gives prior AI outputs from the roles, treat them as raw rehearsal notes and consolidate rather than repeating them.

## Reference Map

- `references/interactive-router.md`: first-run onboarding, mode selection, intake depth routing, and next-step menus.
- `references/intake-template.md`: intake questions and structured case brief.
- `references/output-contract.md`: required labels and module-specific output fields.
- `references/procedure-gate.md`: jurisdiction, arbitration, limitation, preservation, appraisal, service, and hearing blockers.
- `references/issue-map.md`: dispute focus, hearing agenda, and fact/proof pressure map.
- `references/claim-elements.md`: claim basis, elements, facts, evidence, defenses, and blocking plan.
- `references/evidence-matrix.md`: evidence/proof-burden matrix and gap analysis.
- `references/opposing-counsel.md`: opponent lawyer red-team simulation.
- `references/judge-questions.md`: judge questions, one-question drill, and oral answer compression.
- `references/key-person-exam.md`: key-person, witness, legal representative, handler, or employee statement drills.
- `references/losing-judgment.md`: losing-risk check, simulated adverse reasoning, and fatal logic chains.
- `references/hearing-playbook.md`: final pre-hearing playbook format.
- `references/civil-procedure-framework.md`: PRC civil procedure stage map, judge powers, evidence rules, judgment structure, and cross-jurisdictional terminology table.
- `references/legal-authority-verification.md`: official-source hierarchy and verification protocol for statutes, judicial interpretations, and cases.
- `references/nine-step-method.md`: Zou Bihua's nine-step adjudication method — the judge's cognitive framework for analyzing claims, elements, facts, and legal conclusions.
- `references/duan-housheng-adjudication-methods.md`: Duan Housheng's three practical modes of adjudication — theoretical foundation for why "find law first, then facts" is the default mode.
- `references/key-legal-provisions.md`: core articles from PRC Civil Procedure Law, Civil Evidence Provisions, and SPC Judicial Interpretations.
- `references/litigation-pitfalls.md`: common procedural, evidentiary, substantive, and witness-related traps with an attack-dimension index for red-team analysis.
- `references/recommended-readings.md`: tiered reading list covering procedure, evidence, trial practice, judgment writing, litigation strategy, and case law research.
- `references/reference-bibliography.md`: comprehensive bibliography across eight categories — methodology, procedure, evidence, adjudication methods, litigation practice, legal writing, statutes, and academic papers.
