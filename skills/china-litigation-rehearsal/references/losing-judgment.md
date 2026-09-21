# Losing Risk Check

Use this reference to check losing risks, simulate unfavorable reasoning, and reverse-engineer how to block adverse reasoning before the hearing.

## Purpose

The goal is not to predict the court's decision. The goal is to reveal the most dangerous chains of reasoning that could make an adverse decision legally writable from the current record.

## Inputs Needed

At minimum:

- claims or defense goal;
- key facts and timeline;
- evidence list with proof purpose;
- known opponent defenses;
- disputed issues;
- amount/remedy calculation if relevant.

If the record is thin, state assumptions before writing the simulated reasoning.

## Main Output

Default to a losing-risk check. Produce simulated judgment prose only when the user explicitly asks for a `本院认为` style passage.

### Part 1: 败诉风险排查表

| 编号 | 不利结论 | 法院可能如何写 | 依赖事实/证据 | 我方薄弱处 | 假设前提 | 阻断方案 |
| --- | --- | --- | --- | --- | --- | --- |
| R1 |  |  |  |  |  |  |

For each branch, state:

- whether the branch is based on confirmed facts or assumptions;
- what evidence would make the branch writable;
- what evidence or explanation can block it;
- whether the user's target should be lowered or reframed.

### Part 2: Optional Simulated Unfavorable Reasoning

Only if requested, write a concise `本院认为` style section. Keep it realistic:

- no exaggerated hostile language;
- no invented law or case citations;
- explain how the court could reject the user's main position;
- address the user's key evidence and why it may be insufficient;
- explain why the opponent's defense may be accepted or partly accepted;
- identify unresolved facts the court may treat as failure of proof.

If legal authority would be necessary, write:

`相关法律依据及裁判规则需检索核验，此处仅模拟裁判论证结构。`

### Part 3: 致命逻辑链排查

| 编号 | 致命裁判逻辑 | 内核 | 依赖事实/证据 | 当前薄弱处 | 庭前阻断方案 |
| --- | --- | --- | --- | --- | --- |
| L1 |  |  |  |  |  |

For every fatal chain, classify:

- `立即补证`: can be strengthened before hearing.
- `庭审解释`: must be explained orally because hard evidence is limited.
- `降低目标`: consider narrowing claim, amount, or argument.
- `调解杠杆`: use as settlement risk if appropriate.

## Optional Variants

### Three Outcomes

If requested, compare:

| 结果版本 | 成立条件 | 裁判理由骨架 | 我方应促成/避免的事实认定 |
| --- | --- | --- | --- |
| 完全支持我方 |  |  |  |
| 部分支持我方 |  |  |  |
| 不支持我方 |  |  |  |

### Appeal Risk

If the user asks about appeal:

- assess only at a rehearsal level unless judgment text and record are supplied;
- distinguish factual findings, legal application, procedure, and amount;
- mark all appellate standards and legal authorities as `需检索核验` unless verified.

### Similar Case Distinction

If the user supplies a similar case, compare facts and evidence directly. If no case is supplied, do not fabricate a specific case. Instead, write a hypothetical comparison framework.

## Constraints

- Do not cite fabricated statutes, judicial interpretations, guiding cases, meeting minutes, or local rules.
- Do not phrase the simulated adverse result as the likely or certain result.
- If a chain depends on missing facts, label it `基于假设`.
