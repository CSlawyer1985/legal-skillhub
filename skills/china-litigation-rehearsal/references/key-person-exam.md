# Key-Person Examination

Use this reference for preparation involving witnesses, legal representatives, handlers, employees, HR, finance, sales, project managers, or other key people who may answer questions in a PRC civil/commercial hearing.

## Ethical Red Line

Key-person preparation is not teaching anyone to lie. It is limited to:

- understanding procedure;
- accurately recalling facts;
- staying within personal knowledge;
- distinguishing personal knowledge from documents, hearsay, and legal evaluation;
- expressing clearly under pressure;
- recognizing confusing, leading, or improper questions.

Never suggest fabricated facts, coordinated false testimony, concealment of material facts, or answers beyond the person's knowledge boundary.

## Person Setup

Before a drill, collect:

```text
人员代号：
身份：证人 / 法定代表人 / 经办人 / 员工 / HR / 财务 / 销售 / 项目经理 / 其他
与案件关系：
是否亲历关键事实：
可回答的事实边界：
不可回答或不应评价的事项：
既有陈述、笔录、邮件、聊天记录或会议纪要：
利益关系或偏向：
紧张、回避或记忆风险：
关联证据：
我方发问目的：
对方可能攻击点：
```

## Mode A: AI As Key Person

Use when the user wants to practice asking questions.

Behavior:

- Answer as the key person, not as a lawyer.
- Stay within the person's knowledge boundary.
- For unfavorable or uncertain areas, respond naturally: limited memory, need to see the document, not personally involved, or not a legal expert.
- After each answer, critique the user's question.

Feedback format:

| 问题 | 回答风险 | 发问问题 | 更好问法 |
| --- | --- | --- | --- |

Critique dimensions:

- 是否过度开放。
- 是否暗含诱导或错误前提。
- 是否重复、无关、过度评价。
- 是否让回答人越过亲历事实。
- 是否能证明预设待证事实。

## Mode B: AI As Opposing Questioner

Use when the user wants stress testing.

Ask one question at a time. Prefer controlled questions:

- closed yes/no questions;
- questions with a contested premise;
- timeline confusion;
- document detail challenges;
- prior-statement inconsistency;
- interest/bias questions;
- questions that invite speculation, then flag why the person should avoid speculation.

After the user answers:

```text
【本轮攻击强度】高/中/低
【回答风险】
【与既有证据/陈述的冲突】
【更稳妥回答方向】
【下一问】
```

## Mode C: AI As Judge Intervening

Use when the user wants judicial interruption during questioning.

Intervene when:

- the question goes to a decisive fact;
- the answer conflicts with evidence;
- counsel repeats or confuses the record;
- the person appears to speculate;
- new information may affect adjudication.

Provide short, realistic judicial prompts rather than long lectures.

## Stress Level Variant

If asked, set stress from 1 to 10:

- `1-3`: calm and responsive.
- `4-6`: normal hesitation and imperfect memory.
- `7-8`: anxious, defensive, easily led.
- `9-10`: highly confused or evasive, suitable only for risk discovery.

## Multi-Person Comparison

When comparing people, use:

| 待证事实 | 人员A表现 | 人员B表现 | 稳定性 | 冲突点 | 建议出庭/发问顺序 |
| --- | --- | --- | --- | --- | --- |

## Constraints

- Do not let a non-lawyer make legal evaluations; use `我不是法律专业人士` where appropriate.
- Do not let anyone answer beyond personal knowledge.
- For legal representatives and handlers, distinguish company-position answers from personal recollection.
- For sensitive facts, remind the user to keep the description anonymized and non-confidential where possible.
