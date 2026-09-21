# Issue Map

Use this reference to convert case facts into a hearing agenda.

## Core Frame

Build the map from:

`诉讼请求/抗辩目标 -> 争议焦点 -> 待证事实 -> 证明责任 -> 关键证据 -> 法官需要写进本院认为的句子`

## Issue Map Format

| 争议焦点 | 与诉请/抗辩的关系 | 待证事实 | 证明压力 | 关键证据 | 对方攻击 | 法官追问 |
| --- | --- | --- | --- | --- | --- | --- |

Use `证明压力` rather than final proof-burden conclusions unless the legal rule is verified.

## Hearing Agenda

After the map, produce a hearing agenda:

1. `必须先讲清`: threshold facts or procedural prerequisites.
2. `必须用证据锚定`: facts the court should not hear as bare assertion.
3. `可放在后面`: background or lower-risk points.
4. `不要主动展开`: points that may create unnecessary attack surface.

## Judgment-Writability Test

For each core issue, ask:

- Can the court write a clear finding based on the current record?
- What sentence would the user want to see in `本院认为`?
- What sentence would be most dangerous if written against the user?
- Which evidence makes each sentence writable?

Output:

| 本院认为目标句 | 支撑证据 | 当前缺口 | 阻断对方版本 |
| --- | --- | --- | --- |

## Common Failure Modes

- The user has a strong story but no evidence anchor.
- The user has evidence but the proof purpose is too broad.
- The user argues legal consequences before fixing the factual finding.
- The user treats amount calculation as arithmetic when causation or mitigation is disputed.
- The user ignores a procedural gate that can prevent merits review.
