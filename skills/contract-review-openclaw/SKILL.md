---
name: contract-review
description: 公开发布的合同审核 Skill，通过统一工具入口触发 OpenClaw Contract Review Plugin。
compatibility: Requires openclaw-contract-review-plugin >= 0.1.0
metadata: {"openclaw":{"homepage":"https://your-domain.example/docs/openclaw-contract-review-plugin-skill-design","dispatch":{"mode":"tool","tool":"contract_review","argMode":"raw"},"invocation":{"userInvokable":true},"requires":{"config":["plugins.entries.openclaw-contract-review-plugin.enabled"]}}}
---
# Contract Review

使用这个 Skill 时，所有合同审核动作收敛到统一工具 `contract_review`，不绕过插件手工分析。

## 何时使用

支持通过 slash 命令（如 `/contract-review login`、`/contract-review logout`）或自然语言触发。

- 用户上传合同并要求审核、继续审阅或补充要求时
- 用户要求登录、重新登录或处理会话失效时
- 用户要求查询进度、获取结果或取消审核时
- 用户要求退出会话时
- 用户使用自然语言表达意图（如"帮我看看合同"、"继续上次的审核"）时

## 支撑说明

- [意图路由规则](references/intent-routing.md)
- [登录与鉴权门控](./references/auth-gate.md)
- [执行约束](references/execution-rules.md)
- [交互示例](references/examples.md)

---

## 工作方式

这是一个“主 Skill + 支撑文件”的公开 Skill：

- `SKILL.md` 只保留高层编排、门控顺序、公开边界与关键禁止事项
- 详细规则拆到同目录下的参考文件，按需读取
- 无论读取哪个参考文件，所有真实动作仍然只能通过 `contract_review` 执行

## 核心流程（四阶段门控）

每次用户交互必须按以下顺序依次通过四个阶段。**前一阶段未完成时，禁止进入下一阶段。**

### 阶段 1 — 意图确认（Intent Gate）

**在明确用户意图之前，不得调用任何工具。**

- 必须先确认用户是否要进行合同审核，或只是登录、登出、查状态、查结果、取消、继续等其他操作
- 若用户要进行合同审核，必须先确认其审核立场、审核模式（标准审核模式 / 深度审核模式），以及是否已经给出针对性的审核要求
- 在完成上述确认后，再把用户输入（slash 或自然语言）映射成唯一 `commandName`
- 有效值仅限：`submit` | `status` | `followup` | `resume` | `cancel` | `result` | `rounds` | `login` | `logout` | `login_help`
- 若意图不明，只输出追问文本并终止当前轮
- **若识别为 `submit`，在进入阶段 2 之前必须完成信息完整性预检（见下方 "submit 信息预检"）；预检未通过 → 立即终止，不进入阶段 2，不调用任何工具**
- 详细意图映射与追问规则，见 [intent-routing.md](references/intent-routing.md)

#### submit 信息预检（阶段 1 末尾，进入阶段 2 之前）

以下四项必须**全部**在当前轮用户输入中确认：

| 必要项 | 已满足的条件 |
| --- | --- |
| 合同文件 | 当前轮已上传附件，或用户明确指定了目标文件 |
| 审核立场 | 用户已明确说明（偏甲方 / 偏乙方 / 中性） |
| 审核模式 | 用户已选择（标准审核模式 / 深度审核模式） |
| 审核要求 | 用户已给出针对性关注点或重点条款 |

**任一缺失 → 当前轮只输出追问文本（一次性列出所有缺失项），立即终止。不进入阶段 2，不调用任何工具，不输出登录链接。** 待用户下一轮补全后，从阶段 1 末尾重新执行预检。

> ⚠️ **严禁**：追问文本与任何工具调用出现在同一响应轮中。只要有任一信息缺失，结论只有一个：**输出追问 → 终止**，没有例外。

### 阶段 2 — 权限验证（Auth Gate）

**登录流程未完成前，不得调用任何审核业务操作。**

- `login` / `logout` / `login_help` 走非业务路径
- `submit` / `status` / `followup` / `resume` / `cancel` / `result` / `rounds` 走业务路径
- 对于主路径“上传合同 + 审核要求”，插件会在缺少登录态时自动发起登录流程
- 若需登录，当前轮只返回登录引导、浏览器确认提示，以及“完成登录后将自动继续刚才的合同审核提交”的说明
- 不展示 `user_code`
- 详细认证、会话状态与登录文案规则，见 [auth-gate.md](references/auth-gate.md)

### 阶段 3 — 执行操作（Execute Gate）

- `submit` 前必须确认四项齐备：合同文件、审核立场、审核模式（标准审核模式 / 深度审核模式）、针对性的审核要求
- 四项不齐 → 只追问并终止当前轮
- 纯查询优先复用最近任务上下文，不得漂移成新提交
- 若查不到最近任务上下文，只提示用户提供任务 ID 或重新提交
- 详细执行与查询控制规则，见 [execution-rules.md](references/execution-rules.md)

### 阶段 4 — 提交后跟踪（Post-Submit Subscription）

仅在 `submit` 成功返回任务 ID 后进入：

1. 先输出提交确认文字
2. 再调用 `contract_review` 的 `watch`

顺序不可颠倒，否则进度推送会先于确认消息到达。详细要求见 [execution-rules.md](references/execution-rules.md)。

---

## 全局约束

以下规则在所有阶段始终生效：

1. 所有合同审核动作只调用 `contract_review`
2. 不得使用通用工具读取合同文件或手工生成审核结论
3. 需要追问时，当前轮只输出追问文本，立即终止
4. 对“处理中 / 审核中 / 稍后再查”仅做安静等待回复，不自动轮询
5. 提交成功后只围绕该任务做后续操作
6. 不得编造任务状态，不得编造 artifact 链接，不得编造进度百分比
7. 登录链接若已通过飞书直推发送，不重复展示

详细约束与反例见 [execution-rules.md](references/execution-rules.md)。
8. **submit 预检在阶段 1 末尾执行**，四项不齐时当前轮立即终止，绝不进入阶段 2（见阶段 1 "submit 信息预检"）

---

## 快速执行摘要

- 用户通过 slash 或自然语言表达意图时，先确认是否要进行合同审核，还是执行其他操作
- 若进入 `submit`，**先在阶段 1 末尾执行信息预检**：合同文件、审核立场、审核模式、审核要求四项若有任一缺失，仅输出追问文本，终止当前轮；四项全齐后才进入阶段 2
- 未登录时，插件会自动发起登录流程，提示用户在浏览器确认
- 浏览器确认完成后，插件会自动继续刚才的合同审核提交
- 查询 `status` / `result` / `rounds` 时，优先复用最近任务上下文
- 禁止编造任务状态
- 禁止编造 artifact 链接

---

## Additional resources

- 意图识别、`commandName` 映射、追问边界：见 [intent-routing.md](references/intent-routing.md)
- 登录、会话状态、`/contract-review login`、`/contract-review logout`：见 [auth-gate.md](references/auth-gate.md)
- 提交、查询、followup、resume、cancel、watch、全局约束：见 [execution-rules.md](references/execution-rules.md)
- 正反示例与推荐回复方式：见 [examples.md](references/examples.md)

这些参考文件用于让主 Skill 更清晰、子模块更专业；但它们只是支撑说明，不改变本 Skill 的唯一入口约束。
