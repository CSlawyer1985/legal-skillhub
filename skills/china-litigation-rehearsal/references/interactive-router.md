# Interactive Router

Use this reference as the default entry point for the skill. Start here for every new invocation unless the user explicitly says to skip guidance and already provides a mode, basic case facts, procedural stage, claims or defense goal, and key evidence.

## Design Goal

Guide a lawyer step by step without requiring them to know the skill's internal modules. Ask a few useful questions, recommend a path, and then continue into the right workflow.

Do not overwhelm the user with a full intake form at the start. Ask at most three questions per turn unless the user explicitly asks for the full template.

## Bypass Rule

Skip the guided menu only if all are true:

1. The user explicitly requests direct execution or says to skip guidance.
2. The user names a mode or single module.
3. The user provides enough case facts to proceed.

If any one is missing, stay in guided mode.

## First-Run Opening

For every new invocation that does not meet the bypass rule, respond with:

```text
我可以带你一步一步跑。先提醒：请使用甲公司、乙公司、A先生等代号，删除真实姓名、商业秘密、未公开客户材料和敏感个人信息。

先选一个目标：
1. 快速体检：10分钟内找程序炸点、争议焦点、证据缺口。
2. 标准预演：红队攻击、法官追问、败诉风险排查、庭前手册。
3. 深度打磨：加入关键人物发问、30秒/60秒/3分钟回答、二轮反驳。
4. 单点训练：只练红队、法官追问、关键人物、败诉风险排查或庭前手册。
5. 我不确定：你给我案情摘要，我来推荐模式。

请回复编号，并告诉我你现在有什么材料。
```

## Material Menu

If the user says they have materials but does not specify the type, ask:

```text
你目前手上有什么材料？可以多选：
A. 只有口头案情摘要
B. 有证据目录
C. 有合同/协议关键条款
D. 有起诉状、答辩状或代理意见初稿
E. 有法院通知、举证期限、争议焦点或庭审日期
F. 有证人/经办人/法定代表人需要出庭或接受询问
G. 有前面跑过的 AI 输出，需要整理成手册
```

Then route:

| User materials | Recommended route |
| --- | --- |
| A only | `快速体检` + minimum intake |
| A+B/C | `快速体检` or `标准预演` |
| A+B+C+D/E | `标准预演` |
| F | add `key-person-exam.md` after issue/procedure triage |
| G | `实战手册整理` using `hearing-playbook.md` |

## Urgency Menu

If the hearing or deadline timing is unclear, ask:

```text
时间上属于哪种？
1. 今天/明天就要开庭或提交材料
2. 3-7天内
3. 1-3周内
4. 只是前期评估
```

Route:

- `1`: ask only minimum intake, produce P0 actions first.
- `2`: standard mode, but prioritize evidence and oral answers.
- `3`: standard or deep mode.
- `4`: quick scan first, then recommend next module.

## Minimum Intake Card

If the user provides little case information, ask for this compact card:

```text
请先按这个 60 秒版本给我：
1. 案由、我方身份、程序阶段：
2. 我方诉求或目标：
3. 三个关键事实：
4. 现有关键证据：
5. 对方主要抗辩：
6. 最近期限或庭审日期：
7. 你最担心的问题：
```

If the user cannot answer all seven, continue with what is available and label gaps.

## Mode Recommendations

Recommend a mode instead of forcing the user to choose when the facts point clearly one way:

| Situation | Recommend |
| --- | --- |
| User has only summary and asks whether case is risky | 快速体检 |
| Hearing within days and evidence list exists | 标准预演 |
| User already has pleadings and wants to practice court answers | 深度打磨 |
| User wants opponent attack only | 单角色训练: 对方律师红队 |
| User wants judge questions only | 单角色训练: 法官追问 |
| User wants witness or handler practice | 单角色训练: 关键人物陈述 |
| User has prior outputs and wants a checklist | 实战手册整理 |

When recommending, state:

```text
我建议先用【模式名】，因为【一句理由】。如果你同意，我会先做【第一步产出】。
```

## Capability Map For New Users

When the user asks what the skill can do, show a concise map:

```text
这个 skill 可以做六件事：
1. 案件体检：程序闸门、争议焦点、证据缺口。
2. 红队攻击：模拟对方律师怎么拆你的案子。
3. 法官追问：按中国民事庭审语境生成高优先级问题。
4. 关键人物训练：经办人、法定代表人、证人等发问/质询演练。
5. 败诉风险排查：排查可能导致败诉或不利裁判的逻辑链、证据缺口和阻断方案。
6. 庭前手册：整理成开庭前一晚可复习的行动清单和口头版本。
```

Then ask which one they want to try first.

## After-Output Next Step Menu

After every major output, offer the next sensible options:

```text
下一步你可以选：
1. 继续跑对方律师红队
2. 进入法官追问
3. 训练关键人物发问
4. 做败诉风险排查
5. 生成庭前实战手册
6. 回到 intake 补充事实或证据
```

Only show options that fit the current stage. If the user is near a deadline, put the most urgent option first.

## Guardrails During Interaction

- Remind the user to anonymize before receiving detailed facts.
- If the user supplies real names or sensitive data, ask them to replace with codes before continuing.
- Do not ask for privileged or confidential details if a high-level description is enough.
- If legal authority is needed, route to `legal-authority-verification.md`.
- If the case is outside mainland civil/commercial first-instance preparation, state the limitation and ask whether to continue with a narrower scope.
