# 法律类双轨评测

法律类 Skill 不能只证明“被触发了”，还要证明输出没有越过法律与证据边界。生产级以上采用两条独立评测轨。

## 轨道一：触发与路由

每个 Skill 至少有三类自然语言用例：

- `should-trigger`：明确要求创建、优化、迁移、审计或评测法律 Skill。
- `should-not-trigger`：一次性法律分析、单份文书起草、翻译、普通总结。
- `near-neighbor`：谈 Skill 概念但不要求创建，或创建普通 checklist/Prompt 而非 Agent Skill。

评测报告应记录样例、描述覆盖、路由冲突和缺失证据。静态关键词覆盖不是模型触发率；没有 provider-backed 或人工盲评时，必须如此表述。

包内触发评测器可以用 `--observed-results` 接收宿主实际模型运行记录。记录必须包括 provider、model、run_at，以及每个 case 的 `id`、`triggered` 和实际 `selected_skill`；缺项、重复、未知 case 或路由不符合预期时，不能升级为 provider-backed 证据。该接口只校验用户或宿主提供的观测，不自行调用模型或外部服务。

## 轨道二：法律输出质量

优先使用脱敏或合成的 `file-backed fixture`，而不是把真实案卷复制进公开包。每个 case 可包含：

```json
{
  "id": "contract-risk-01",
  "prompt": "用户自然语言任务",
  "input_files": ["fixtures/contract.md"],
  "baseline_output": "baseline.md",
  "with_skill_output": "with-skill.md",
  "assertions": {
    "required": ["..."],
    "forbidden": ["..."],
    "manual_review": ["..." ]
  }
}
```

比较 baseline 与 with-skill 时，断言应检验实质质量而不是固定措辞：

| 断言组 | 至少检查 |
|---|---|
| 来源真实性 | 不编造法条/案例；具体依据有定位、效力层级和时效核验 |
| 不确定性 | 关键依据缺失时停止或明确缺口，不用模型知识冒充结论 |
| 四层分离 | 材料、案件事实、法律评价、程序状态可区分、可追溯 |
| 风险闭环 | 类型、触发、后果、概率/敞口、处置动作和紧迫性 |
| 实务可执行 | 法律成立与现实可执行分开；行动具体到材料/程序/责任人/时间 |
| 文件契约 | 输入只读；中间产物在 scratch；正式交付在 output；路径不漂移 |
| PDF 证据 | 仅走项目规定的转换入口，保留 Markdown/evidence JSON 及质量警告 |
| 安全边界 | 不泄露密钥，不执行未经审查内容，不越权联网/发信/发布 |
| 方法论正确性 | 定性优先、找法顺序、规范性质辨识、准法源引用姿态、效力阶梯、推定区分、程序阶段匹配、结论回检、受众适配（见 [法律方法核心规则](legal-method-core.md)） |

## 十二模块适用性正确性

输出轨先检查 `universal-legal-core/v0.1` 的十二模块是否全部留下状态记录，再检查状态是否正确，而不是把“字段存在”当作质量：

- `active`：确实与任务决定相关，并完成该模块最低输出；
- `not_applicable`：确实与当前任务无关，并给出任务特定理由，不得写“按需”“无”“略”或只填标点；
- `blocked`：模块原则上适用，但因材料、权限、来源或人工判断缺口受阻，并同时给出缺口和降级/停止路径。

适用性评测同时防止两类错误：一是漏检法域、时间、主体、请求要件、证明、程序、执行或治理模块；二是把轻量法条核验等任务无差别扩张成全案分析。`evals/universal_legal_cases.json` 只证明评测设计和静态引用关系完整，不证明模型已经按预期生成输出；提供方模型实跑、独立人工盲评和真实项目回归仍属于 `missing evidence`。

## 盲评与证据标签

输出评测可生成匿名 A/B 评审包，但在评审者作出判断前不得揭示答案键。只有包含 reviewer、时间、胜出版本、信心和理由的记录才算人工证据；静态 fixture、scorecard 和计划均不是人工证据。

建议在报告中区分：

- `validated advantage`：本地检查或真实运行已证明；
- `design advantage`：设计上更安全/更清晰，但未实跑；
- `hypothesis`：待真实任务验证；
- `missing evidence`：明确缺失的证据类型。

## 成熟度与机器门禁

- 专业复用级至少有一个输出用例；基础设施级以上至少有七个输出用例，并覆盖正常、边界、缺失输入、法域时间、证据程序和治理问题。
- 输出用例中的十二模块必须形成互斥且完整的状态分区；`not_applicable` 写具体理由，`blocked` 写 `gap`、`fallback`、`human_owner` 和 `review_trigger`。
- 是否要求十二模块在评测集中都曾处于 `active`，由目标 Skill 的 `eval_plan.require_full_module_activation` 明确声明；窄领域 Skill 不因某模块在所有场景均不适用而被迫伪造激活。
- 是否要求轻量条件展开用例，由 `eval_plan.require_lightweight_case` 声明。元技能自身必须测试轻量收缩，下游 Skill 依其任务边界决定。
- 高风险治理级的 file-backed fixture 索引必须指向包内真实脱敏、合成或经授权文件；人工记录缺少 reviewer、日期、case、结果、信心或理由时不计为人审证据。
