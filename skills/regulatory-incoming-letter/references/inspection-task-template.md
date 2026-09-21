# `inspection-task` 模板（`gap_type` 扩展项）

**对应技能**：`regulatory-incoming-letter`（监管来函处置，创建）+ `regulatory-gap-surfacer`（内规差异呈现，管理）
**结构定义版本**：v2（阶段 3 落地）

`inspection-task` 是 `gap-tracker.yaml` 中 `gap_type` 的新枚举值，专门用于监管下发函拆解出的整改任务。与原有的 `partial` / `full` / `new-policy` 等政策类内规差异区分对待。

---

## 完整字段 YAML 模板

```yaml
gaps:
  - id: INS-001                            # 函件相关任务用 INS- 前缀（区别于 GAP- 前缀的政策内规差异）
    requirement: "具体要求事项（来自函件正文逐条拆解）"
    regulation: "监管来文 + 文号"
    policy_affected: "可能受影响的内部政策（如有）"
    gap_type: "inspection-task"            # ✱ 新枚举值

    # ───── 监管来函处置特有字段 ─────
    inspection_letter_id: "2026-05-25-金管沪-XX"   # 关联到 letter.yaml
    inspection_category: "第 5 类 专项自查"          # 6 分法归类
    inspection_subcategory: ""                      # 如适用（如 2a / 2b）

    # ───── 负责人模型（继承自内规差异呈现 v2）─────
    policy_owner:
      name: "王琳"
      department: "法务部"
      dm_id: "feishu_xxx"
    task_owner:
      name: "张总"
      department: "业务一部"
      dm_id: "feishu_yyy"
    section_owner:                          # 可选 —— 跨章节复杂任务时使用
      name: ""
      department: ""
      dm_id: ""

    # ───── 时效（监管硬截止日）─────
    opened: 2026-05-25                     # 任务创建日期
    due: 2026-06-19                        # 内部截止日（监管截止日 - 5 个工作日缓冲）
    regulatory_deadline: 2026-06-24        # ✱ 监管要求的**硬截止日**
    status: "open"                         # open | in-progress | closed | risk-accepted
    status_verified: true                  # 函件已核实（监管直接下发）

    # ───── 派单状态 ─────
    notified_task_owner: false
    notified_policy_owner: false
    reminders_sent: []                     # 三档预警发送历史

    # ───── 上报追踪（监管来函处置特有）─────
    submission_required: true              # 是否需要纳入对外上报材料
    submission_received: false             # 是否已收到业务部门反馈
    submission_received_date: ""
    submission_content: ""                 # 业务部门提交内容摘要（用于上报汇总）
    submission_supporting_docs: []         # 支持材料路径列表
    submission_status: ""                  # 已完成 / 进行中 / 风险接受

    # ───── 引用追溯 ─────
    source_tags:
      - "[监管下发函]"
      - "[金管总局公开栏目]"               # 如适用，附监管动态监测移交时的标签

    # ───── 解决 / 风险接受 ─────
    resolution: ""                         # 关闭时填
    risk_accepted_rationale: ""            # 风险接受时填
    risk_accepted_by: ""                   # 风险接受人（按 `escalation_path`）
    risk_accepted_date: ""
```

---

## 关键字段说明

### `id` 前缀约定

| 前缀 | 含义 | 来源 |
|---|---|---|
| `GAP-` | 政策更新类内规差异 | `regulatory-policy-diff`（政策比对）产出 |
| `INS-` | 监管下发函整改任务 | `regulatory-incoming-letter`（监管来函处置）产出 |
| `CMT-` | 评议决策（在 `comment-tracker.yaml`） | `regulatory-reg-feed-watcher`（监管动态监测）/ `regulatory-comments`（评议管理）产出 |

### `inspection_letter_id`

格式 `YYYY-MM-DD-<监管缩写>-<文号尾号>`，例如：

- `2026-05-25-金管沪-XX` —— 金管总局上海监管局
- `2026-04-10-网信办-YY` —— 国家网信办
- `2026-03-15-证监深-ZZ` —— 深圳证监局
- `2026-02-20-人行总-WW` —— 中国人民银行总行

关联到 `$LEGAL_AGENT_PROFILE_HOME/regulatory-legal/incoming-letters/<letter-id>/letter.yaml`。

### `inspection_category`

按 6 分法填写：

- "第 1 类 行政处罚"
- "第 2 类 行政监管措施"（**优先**填子类）
- "第 2 类 行政监管措施—2a 责令整改"
- "第 2 类 行政监管措施—2b 现场检查反馈"
- "第 3 类 监管谈话"
- "第 4 类 程序性通知"
- "第 5 类 专项自查 / 工作函"
- "第 6 类 监管问询"

### `regulatory_deadline` vs `due`

- `regulatory_deadline`：监管要求的**硬截止日**，错过有处罚风险
- `due`：公司**内部截止日**，默认是 `regulatory_deadline - 5 个工作日`（缓冲）。可在冷启动访谈中调整缓冲天数

提醒按 `regulatory_deadline` 倒计时：

| 距离 `regulatory_deadline` | 提醒动作 |
|---|---|
| 30 天 | 一次预提醒（仅 `task_owner`） |
| 15 天 | 二次提醒（`task_owner` + 抄送 `policy_owner`） |
| 5 天 | 三次紧急（`task_owner` + `policy_owner` + `escalation_path.重大业务影响决策`） |
| 0 天（监管截止日当日） | 🔴 红色告警 + 强制升级 |
| 已超期 | 🔴🔴 持续告警直至关闭 / 风险接受 |

### `submission_required`

判断本任务的反馈内容**是否需要**进入对外上报材料：

- `true`（默认）：业务部门反馈 → 进入上报草稿 → 提交监管
- `false`：仅内部整改，不对外上报（如纯流程性改造，不写进监管回函）

### `submission_status` 枚举

- `已完成` —— 整改完成 + 证据齐全
- `进行中` —— 整改启动但未完成，需在上报材料中说明进度 + 后续时间表
- `风险接受` —— 经评估不整改，需附风险接受决策依据（按 `escalation_path` 会签）

---

## 与内规差异呈现（`regulatory-gap-surfacer`）的协作

1. **创建**：监管来函处置在第 4 步任务派发时把 `inspection-task` 写入 `gap-tracker.yaml`
2. **派单**：内规差异呈现按 v2 结构定义的 `task_owner` 字段发 DM（**逐条预审**）
3. **提醒**：内规差异呈现按三档预警节奏发提醒（30/15/5 天）
4. **状态报告**：在 `regulatory-gaps`（内规差异跟踪）输出中 `inspection-task` 单独成档（区别于普通内规差异），按 `inspection_letter_id` 分组显示

### `regulatory-gaps` 中的 `inspection-task` 分组示例

```markdown
## 未整改处理的内规差异 —— 2026-06-10

### 🔴 监管下发函任务（按函件分组）

#### 函件：金管总局自查工作函 (2026-05-25-金管沪-XX) —— 14 天后到期

| INS-ID | 要求事项 | 负责人 | 提交状态 |
|---|---|---|---|
| INS-001 | 消费金融贷款利率合规性自查 | 业务一部张总 | 已完成 ✓ |
| INS-002 | 贷款营销话术合规性自查 | 市场部李总 | 进行中 ⏳ |
| INS-003 | 投诉处理流程自查 | 客服部赵总 | 已完成 ✓ |
| ...（共 14 条） | | | |

汇总：已完成 9 条 / 进行中 4 条 / 未启动 1 条 ⚠️

→ 建议：5 个工作日内催 INS-002 / INS-004 / INS-007 / INS-014 的负责人

---

### 🟠 30 天内到期的政策内规差异

[正常内规差异视图]

### 🟡 开放的政策内规差异

[正常内规差异视图]
```

---

## 风险接受流程

如果某条 `inspection-task` **不打算整改**（如该事项对本公司不适用、或整改成本远超风险），走"风险接受"流程：

1. 业务部门提出风险接受申请（写明理由）
2. 法务初审：法律风险评估
3. 首席合规官复审：合规风险评估
4. `escalation_path.重大业务影响决策`：最终决策者（如总经理）签字
5. **写入对外上报材料**：明示"本公司经评估认为 [事项] 不属于本次自查范围 / 不适用 / 拟保留现状"+ 法律依据 / 业务理由

`status: risk-accepted` 必须在所有上述步骤完成后才能标记。

---

## 关闭流程

整个 `letter-id` 的所有 `inspection-task` **全部关闭或风险接受** + **监管回函通过验收** 后，才能：

1. `letter.yaml` 的 `status: closed`
2. 各 `inspection-task` 的 `status: closed`（如还是 `open`）
3. 归档：移到 `$LEGAL_AGENT_PROFILE_HOME/regulatory-legal/incoming-letters/_archived/<letter-id>/`
4. 跟踪日志中保留闭环时间、监管回函摘要

---

*本模板由阶段 3 监管来函处置技能落地时产出，2026-05-18。结构定义与内规差异呈现 v2 对齐。*
