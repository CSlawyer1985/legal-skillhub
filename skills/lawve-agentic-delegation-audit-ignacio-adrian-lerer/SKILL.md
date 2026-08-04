---
name: "lawve-agentic-delegation-audit-ignacio-adrian-lerer"
description: "当律师、法律团队或客户需要评估能够代表某人行动的 AI 代理时使用：发送消息、搜索、起草、提交、支付、删除、连接账户、使用工具或依赖外部数据。为法律运营产出一份实用的委托、监督、问责和控制审计。"
metadata:
  author: "Ignacio Adrián Lerer"
  license: "agpl-3.0"
  version: "2026-06-05"
---

# Lawve 代理式委托审计

使用本技能帮助律师评估 AI 代理工作流是否足够安全、可在法律或业务运营中使用。

核心观点：

```text
当 AI 仅回答时，用户评估输出。
当 AI 行动时，用户委托权力。
被委托的权力需要控制、日志、撤销和问责。
```

## 何时使用

- 客户想要将 AI 代理用于法律、合规、业务或行政工作。
- 产品、律师事务所或法律运营团队正在将代理连接到电子邮件、文件、CRM、法院门户、支付、消息、日历、数据库、浏览器工具或代码执行。
- 律师需要用实用的治理术语解释代理式 AI 的风险。
- 工作流可能发送、提交、删除、批准、购买、发布、签署、部署或变更访问权限。
- 系统自称“自主”、“代理式”、“带工具的助理”、“AI 员工”、“法律副驾驶”或“工作流代理”。

## 不用于

- 无代理式行动的纯教义法律研究。
- 未经法域特定法律审查的最终法律意见。
- 代理运行时的技术实现。
- 在没有证据、日志和控制的情况下批准代理的生产使用。

## 受理

只收集必要内容：

- 代理执行什么任务？
- 谁是人工委托人？
- 谁部署或运营代理？
- 它可以访问哪些系统、账户、文件、渠道或工具？
- 无需逐步批准即可采取哪些行动？
- 哪些行动是不可逆的、外部的、财务的、法律的、机密的或声誉敏感的？
- 存在哪些日志，谁能读取它们？
- 用户如何暂停、撤销、申诉或纠正代理？
- 哪些数据可以影响代理，包括电子邮件、网页、聊天、文件、工单和提示？

## 审计步骤

1. **对自主级别分类**
   - `answer_only`：仅产生信息。
   - `draft_only`：起草但不发送或更改记录。
   - `approval_gated_actor`：仅经显式批准后行动。
   - `policy_bounded_actor`：在预定限制内行动。
   - `long_running_actor`：跨时间、会话或触发持续运行。

2. **映射被委托的权力**
   - 点名委托人。
   - 点名部署者/运营者。
   - 列出代理拥有的权力。
   - 分离读取、起草、内部写入、外部写入、财务、法律敏感和特权行动。

3. **检查可观察性**
   - 用户能看到代理做了什么吗？
   - 工具调用和外部行动被记录吗？
   - 日志对非开发者可理解吗？
   - 源数据和模型推理分离吗？

4. **检查控制和撤销**
   - 用户能暂停代理吗？
   - 权限可以收窄吗？
   - 访问权能快速撤销吗？
   - 不可逆行动在执行前有预览吗？

5. **检查问责**
   - 发生损害时谁负责？
   - 责任在供应商、部署者、用户、专业人员和客户之间分配吗？
   - 在法律依赖或外部行动之前有人工审查点吗？

6. **检查攻击面**
   - 不可信内容能影响代理吗？
   - 代理将电子邮件、网页、聊天、文档、工单或社交帖子当作指令处理吗？
   - 外部内容和系统指令分离吗？
   - 考虑提示注入、数据外泄和工具滥用吗？

7. **应用法律不确定性门禁**
   - 对下游法律/业务依赖使用 `PASS`、`ESCALATE` 或 `BLOCK`。
   - 不要将重大不确定性藏在免责声明文本中。

## 输出

使用此紧凑格式：

```markdown
## Agentic Delegation Audit

### Verdict
PASS | NEEDS CONTROLS | BLOCK

### Why
[2-5 sentences]

### Delegated Authority
- Principal:
- Deployer/operator:
- Autonomy level:
- Systems/tools:
- Highest-risk action:

### Control Checklist
- Permission scope: adequate | weak | missing
- Human approval before external/legal/financial action: yes | partial | no
- User-readable logs: yes | partial | no
- Revocation/pause: yes | partial | no
- Prompt-injection/data-boundary controls: yes | partial | no
- Accountability owner: clear | partial | unclear

### Required Controls
- [control 1]
- [control 2]
- [control 3]

### Legal Reliance Gate
PASS | ESCALATE | BLOCK

### Next Step
[smallest practical next step]
```

## 决策规则

- `PASS`：代理仅为起草或严格审批门控，日志清晰，权限已界定范围，且无重大法律/客户风险未受管理。
- `NEEDS CONTROLS`：代理可能有用，但缺失的控制阻止安全运营依赖。
- `BLOCK`：代理可以在没有充分批准、日志、撤销或问责的情况下执行外部、法律、财务、机密、破坏性或特权行动。
