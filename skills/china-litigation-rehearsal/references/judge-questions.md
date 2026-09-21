# Judge Questions

Use this reference to simulate the judge's likely questions and train concise oral answers.

## Role Setup

Adopt a neutral PRC civil/commercial trial judge perspective. Focus on what the court must clarify to write a judgment: claims, facts, evidence, proof burden, legal application, amount, and procedural issues.

Do not act as either party's coach while listing questions. After the neutral question list, provide user-facing preparation points if requested.

## Question Categories

Generate questions across the categories that fit the case:

- 程序性: jurisdiction, standing, limitation, claim amendment, counterclaim, third party, appraisal.
- 请求权基础: what legal relationship and remedy the party relies on.
- 事实查明: timeline, performance, notice, breach, loss, causation, commercial background.
- 证据采信: original status, authenticity, source, contradictory records, missing links.
- 证明责任: who must prove which disputed fact and what remains unproved.
- 金额计算: components, period, formula, duplicative claims, mitigation.
- 法律适用: element-by-element fit, defense, remedy consequence.
- 裁判可写性: whether the court can write a coherent `本院认为` from the current record.
- 调解/实际效果: if commercially relevant, identify settlement or performance levers.

## Output Format

| 优先级 | 法官问题 | 类型 | 为什么重要 | 期望听到的回答 | 现有材料是否充分 | 回答不好后果 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 |  | 程序/事实/证据/法律/金额 |  |  | 充分/不足/不确定 |  |

Then add:

- `最容易被追问的三处`: short list.
- `最需要一页纸准备的三处`: short list.
- `需人工核验`: legal authorities or evidentiary rules that cannot be assumed.

## One-Question Drill

If the user wants rehearsal, ask one question at a time.

After each user answer:

1. Evaluate whether the answer directly answered the question.
2. Identify unclear, risky, evasive, or overlong portions.
3. Provide a stronger answer structure.
4. Ask the next question.

Use this feedback format:

```text
【评价】
是否正面回答：
最大问题：
可保留内容：

【更稳表达】
30秒版：
60秒版：

【下一问】
...
```

## Answer Compression

When compressing oral answers:

- Start with the conclusion.
- Use no more than three sentences for the 30-second version.
- Tie each key factual assertion to an evidence number if available.
- Avoid abstract doctrine unless the judge asked for it.
- Do not overstate facts that the evidence does not prove.

## Collegial Panel Variant

For complex cases, simulate three judicial lenses:

| 视角 | 关注点 | 可能问题 | 对我方影响 | 准备重点 |
| --- | --- | --- | --- | --- |
| 法条文义 | elements and formal rule fit |  |  |  |
| 商业合理性 | transaction reality and fairness |  |  |  |
| 程序证据 | burden, admissibility, record clarity |  |  |  |

Then state the likely tension among the three views without pretending to know the actual panel.

## Constraints

- Do not invent a real judge's style unless the user supplies reliable information.
- Keep questions case-specific. Avoid generic law school issue lists.
- If a question depends on an unverified legal rule, mark `需检索核验`.
