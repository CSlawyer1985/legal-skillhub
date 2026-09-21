# Output Contract

Use this reference before producing any substantive analysis. It keeps every module distinguishable, auditable, and useful for lawyers.

## Required Labels

Every substantive output must include:

```text
当前模式：
适用范围：
已确认事实：
关键缺失信息：
确定结论：
基于假设的推断：
待人工核验事项：
高风险点：
建议下一步动作：
```

If the user asks for a very short answer, compress the labels but do not remove the distinction between confirmed facts, assumptions, and verification items.

## Module-Specific Additions

For red-team outputs, add:

- 攻击成立前提。
- 攻击自身弱点。
- 我方阻断方向。

For judge-question outputs, add:

- 问题类型。
- 期望回答。
- 回答不好会导致的后果。
- 30秒口头版, 60秒展开版, and 3分钟完整论证版 when preparing answers.

For key-person outputs, add:

- 身份和认知边界。
- 是否亲历。
- 既有陈述一致性。
- 不得引导虚假或超范围陈述的红线。

For losing-risk-check outputs, add:

- 致命逻辑链。
- 需要补强的证据。
- 需要提前解释的事实空白。
- 该模拟依赖的假设前提。

For playbook outputs, add:

- P0/P1/P2 priority.
- 庭前必须补、庭审必须解释、备选准备.
- 30秒、60秒、3分钟 oral scripts if advocacy is involved.

## Tone And Verification

- Do not sound certain where the record is thin.
- Do not cite any legal authority unless supplied by the user or independently verified in the current task.
- Use `需检索核验` for statutes, judicial interpretations, guiding cases, meeting minutes, local rules, limitation rules, proof-burden rules, and appeal standards that are not verified.
- Make the final `人工核验清单` specific enough that a lawyer can assign work.
