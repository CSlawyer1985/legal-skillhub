---
name: smart-calendar
description: 基于 macOS / iOS 苹果生态的智能日程与待办事项管理 skill。将非结构化输入（口语描述、聊天截图、邮件截图）自动解析为结构化任务，经用户确认后写入 Apple 日历 / 提醒事项，支持标签管理（工作 / 生活 / 自定义）、时间冲突检测、后续更新删除，以及按项目制自动生成工作周报（项目 - 进展 - 待办三级结构）。语言风格定位为专业正式书面语，也适用于其他需要专业书面表达的知识工作场景。单机版：每台 Mac 独立运行，数据本地存储，不做多端同步。
metadata:
  description_zh: 智能日程待办管理（单机版）
  description_en: Smart Calendar & Todo Manager (single-machine edition)
  version: 1.0-dist
  disable: false
---

# smart-calendar（分发版 / 单机）

## 定位

**单机版**。每台 Mac 独立维护一份本地任务数据库（`~/.smart-calendar/tasks.json`）。日历事件和提醒事项本身会通过你已有的 iCloud 账号自动同步到其他 Apple 设备，但本 skill 的元数据（formal_title / 标签 / 项目 / 任务类型等）**不跨机同步**。如需跨设备保留完整上下文，请在同一台 Mac 上集中管理任务，或参考多机协同改造方案另行设计。

## When to use

用户在以下场景触发：
1. 输入待办事项的口语描述（如"明天之前把 A 项目方案改完发给协作方"）
2. 上传聊天截图、邮件截图等非结构化信息
3. 要求更新或删除之前创建的日程 / 任务
4. 要求生成工作周报
5. 要求管理标签（添加 / 删除 / 修改任务标签）
6. 任何涉及"把 XX 加到日历 / 提醒里"、"帮我排个日程"、"生成周报"的请求

## Prerequisites

- macOS 系统（操作 Calendar 和 Reminders app）
- Calendar 和 Reminders app 需被允许脚本控制 — 首次运行时会弹出 *系统设置 → 隐私与安全性 → 自动化* 的权限请求，必须授权
- Python 3 已安装（macOS 系统自带）
- **Apple Reminders 已建好「工作」和「生活」两个列表**
- **Apple Calendar 已建好「工作」和「生活」两个 iCloud 日历**

## 运作模型（v4.0 — Apple 当真源）

> **Apple Calendar / Reminders 是真源**，本 skill 的 `tasks.json` 是本地缓存。

```
                     [写入]
用户 / agent ─────────────────────────► Apple Reminders / Calendar
                                              │
                                              │ 列表名 = 主标签的物理载体
                                              │ description / body 末尾 = metadata block
                                              │（project, task_type, aux_tags, formal_title）
                                              │
                          iCloud 跨设备同步 ◄──┘
                                              │
                     [读取 / sync]            ▼
tasks.json ◄───────────────────────  Mac / iPhone
（本地缓存，可重建）
```

**核心规则**：
- 创建任务时，agent 决定主标签 `--tag-major work|life` → 自动写入对应列表 / 日历
- 元数据（project / task_type / aux_tags / formal_title）走 metadata block 跟着事件本体同步
- 跨机一致 + iPhone 友好（手动加到「工作」列表的任务也会被 skill 识别为「工作」）
- `sync` 命令随时从 Apple 真源重建 `tasks.json`

## Loop 层（可选自动心跳）

> harness 让 agent 能干活，**loop 让"同步 + 周报"被持续调度、验证、记录**。默认不启用。

两个心跳命令（手动可跑，也可挂 launchd 自动跑 — 见 README「启用自动 loop」节）：

```bash
python3 .../task_manager.py loop-tick --mode daily    # 每日 sync
python3 .../task_manager.py loop-tick --mode weekly   # sync + 出周报
python3 .../task_manager.py loop-status               # 查看 loop 健康
```

**A+B minimum viable loop**：automation（launchd）+ skill（本 skill）+ state file（`loop-state.json`，含 30 条 history 滚动）+ gate（结构性断言：`SYNC_DONE` + tasks.json 可解析 + 报告 size>800 + 含必需段落；失败弹 Basso 通知 + 写 `last_error` + exit 1）。

**设计原则**：确定性机械操作用结构性断言 gate，不引 maker/checker；cron 单跑天然 hard-stop；失败必显式上报。判断类工作（哪些算重点、对外投递）不进 loop。

## 首次配置

首次使用时 skill 会自动创建默认配置（`~/.smart-calendar/config.json`）。建议确认 / 修改以下字段：

1. **周报标题与团队名**（默认标题为"个人工作周报"，team_name 为空）：
   ```bash
   # 个人使用：默认即"个人工作周报"，无需配置；如需改名再 set-config
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
     --key weekly_report.report_title --value "重点项目周报"
   # 团队 / 小组场景：设置 team_name，标题变成 "{team_name}{report_title}"
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
     --key weekly_report.team_name --value "项目组"
   ```
   最终周报标题 = `{team_name}{report_title}`；team_name 为空时只用 report_title。

2. **周报输出目录**（必须设置，否则周报只能输出到控制台）：
   ```bash
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
     --key weekly_report.output_dir \
     --value "/path/to/your/weekly/report/folder"
   ```

3. **查看当前配置**：
   ```bash
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py get-config
   ```

4. **可选：自定义数据目录**（指向 iCloud Drive 或其他位置，用于测试隔离）：
   ```bash
   export SMART_CALENDAR_DATA_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/smart-calendar"
   ```
   ⚠️ 注意：iCloud Drive 跨机同步**不是事务性的**，两端同时写会产生 `.conflicted` 文件。单机版不建议把 DATA_DIR 放 iCloud Drive，仅作测试用途。

## Steps

### 阶段一：解析输入

1. 接收用户输入（文字或图片）。如果是图片，使用多模态能力提取文字内容。
2. 从输入中提取以下结构化字段：
   - **任务标题**（核心描述）
   - **任务类型**：文件审阅 / 反馈 / 调研 / 文书撰写 / 会议 / 其他
   - **所属项目**（用户根据自己业务确定，例如"A 项目"、"X 收购"、"客户 Y"等）
   - **截止时间**（日期 + 可选时间）
   - **开始时间**（如有明确起止时段则提取）
   - **结束时间**（如有明确起止时段则提取）
   - **优先级**：高 / 中 / 低
   - **相关人员**（协作方 / 相关方 / 管理层等）
   - **备注**（额外上下文）
3. 信息不完整时（缺少截止时间、任务类型模糊、所属项目不明确），向用户确认。每个待确认字段提供"留白 / 不回答"选项。用户选择留白时基于已有信息和上下文推断默认值。

### 阶段二：主标签判定 + 次标签收集（v4.0 关键设计）

4. **主标签**：基于任务内容判断「工作」or「生活」。判断规则：
   - 涉及业务项目名、专业术语（方案、审阅、调研、评审会等）、工作相关人员（协作方、外部顾问、管理层）→ **工作**
   - 涉及家庭、购物、健身、休闲、个人事务 → **生活**
   - 无法明确判断时，**主动询问用户**："这个任务属于工作还是生活？"
5. **主标签的物理载体是 Apple 列表 / 日历**（不是 tasks.json 字段）：
   - 工作任务 → 写入「工作」列表 + 「工作」日历
   - 生活任务 → 写入「生活」列表 + 「生活」日历
   - 这是真源 — 即使在 iPhone 上把一条 reminder 从「工作」拖到「生活」，sync 后 skill 也会立即识别为「生活」
6. **次标签**（紧急、自定义）走 metadata block，与主标签分层：
   - 不为每个次标签建 Apple 列表（避免列表爆炸）
   - 次标签通过 `--meta-aux-tags` 写入 reminder body / event description 末尾的 metadata block
   - 用户可随时添加自定义次标签：
     ```bash
     python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py add-tag "紧急"
     ```

**标签别名说明**：内部规范用中文标签（`工作` / `生活`）。agent 用英文写入 `work` / `Work` / `WORK` / `life` / `Life` / `LIFE` 会自动归一化为对应中文。`--tag-major` 同样接受这些别名。

### 阶段三：确认与正式用语生成

7. 将提取的结构化信息展示给用户：

   ```
   📋 识别到的任务信息
   ──────────────────────────────
   任务标题：[提取的标题]
   任务类型：[类型]
   所属项目：[项目名]
   截止时间：[日期 时间]
   优先级：[高/中/低]
   标签：[工作/生活/自定义]
   相关人员：[人员列表]
   备注：[备注]
   ──────────────────────────────
   🎯 将创建：提醒事项 / 日历事件 / 两者
   ```

8. 用户确认后生成正式用语（专业书面语）：
   - 标题正式化：口语化描述转专业书面语
   - 备注正式化：补充完整上下文，使用专业术语
   - 示例："明天把 A 项目方案改完" → "A 项目方案修订及定稿 —— 根据内部审阅意见完成方案文本修订并发送协作方确认"

### 阶段四：冲突检测

9. 写入前检查时间冲突：
   ```bash
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py check-conflict \
     --date "YYYY-MM-DD" [--time "HH:MM"] [--duration 60]
   ```
   - 给定 `--time` 时按 `[time, time + duration)` 区间做真正的重叠判断
   - 不给 `--time` 时返回当天全部事件
10. 有冲突时展示详情并询问用户是否继续：
    ```
    ⚠️ 时间冲突提示
    该时段已有以下日程：
    - 14:00-15:30  A 项目内部讨论会
    是否继续创建？
    ```

### 阶段五：智能路由与写入

11. 根据任务特征智能路由：
    - **仅提醒事项**：只有截止时间、无明确起止时段的任务型工作（如"周五前提交审阅意见"）
    - **仅日历事件**：有明确起止时间的会议 / 约会（如"周三下午 2-4 点评审会"）
    - **两者同时创建**：有截止时间的复杂任务，提醒事项记录任务本身、日历事件预留工作时段
    - 默认偏好：任务型居多时路由到提醒事项；有明确时段时路由到日历

12. 执行写入（**v4.0：用 `--tag-major` + `--meta-*` 参数**）：
    ```bash
    # 创建提醒事项（不指定 --list 时自动按 --tag-major 选「工作」/「生活」列表）
    python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py create-reminder \
      --title "正式标题" \
      --tag-major work \
      --due "YYYY-MM-DD HH:MM" \
      --notes "正式备注" \
      --priority [1|2|3] \
      --meta-project "项目名" \
      --meta-task-type "文件审阅" \
      --meta-aux-tags "紧急,待审" \
      --meta-formal-title "正式标题"

    # 创建日历事件（同理，不指定 --calendar 时自动按 --tag-major 选）
    python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py create-event \
      --title "正式标题" \
      --tag-major work \
      --start "YYYY-MM-DD HH:MM" \
      --end "YYYY-MM-DD HH:MM" \
      --notes "正式备注" \
      --meta-project "项目名" \
      --meta-task-type "会议"
    ```

    `--tag-major` 接受 `work` / `life` / `工作` / `生活`，自动归一化。
    metadata block 会被追加到 reminder body / event description 末尾，跨机同步、跨端可读。

### 阶段六：本地索引（可选）+ sync

13. **v4.0 下 Apple 是真源，tasks.json 是本地缓存**。如果只是创建任务，无需手动 save-task — 跑 `sync` 命令可随时从 Apple 重建 tasks.json。但如果想立即更新本地索引（避免下次跑 search 时漏掉刚创建的任务），可显式保存：
    ```bash
    python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py save-task \
      --task-id "auto-generated-uuid" \
      --user-input "原始输入" \
      --parsed-json '{...}' \
      --formal-title "..." \
      --formal-notes "..." \
      --calendar-event-id "..." \
      --reminder-id "..." \
      --project "项目名" \
      --task-type "类型" \
      --major-tag work \
      --aux-tags "紧急"
    ```
14. **`sync` 命令 — 从 Apple 真源重建 tasks.json**（推荐定期跑，尤其在 iPhone 手动加任务后）：
    ```bash
    python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py sync
    # 可选参数：
    #   --months-back 6 / --months-forward 3   日历事件扫描范围
    #   --dry-run                              只 print 不写盘
    ```
    sync 行为：
    - 扫白名单内的 Reminders 列表（`work_lists` + `life_lists`）的**未完成** reminders
    - 扫白名单内的 Calendar 日历（`work_calendars` + `life_calendars`）的指定时间范围内事件
    - 解析每条 description / body 末尾的 metadata block 还原 project / task_type / aux_tags / formal_title
    - 主标签由所在列表 / 日历名物理推断（不读 metadata 里的 tags 字段）
    - 写盘前自动备份 `tasks.json.bak`
15. 数据库路径：`~/.smart-calendar/tasks.json`（可通过 `SMART_CALENDAR_DATA_DIR` 环境变量覆盖）

### 阶段七：更新 / 删除

15. 用户要求更新 / 删除时：
    - 搜索本地数据库匹配关键词：
      ```bash
      python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py search "关键词"
      ```
    - 展示匹配结果，让用户选择要操作的记录
    - 执行更新或删除：
      ```bash
      python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py update \
        --task-id "xxx" --field "title" --value "新标题"

      python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py delete \
        --task-id "xxx"
      ```

### 阶段八：周报生成

16. 用户主动触发周报（**本版本不实现自动定时**；如需周五自动提示请用 launchd / cron 自行配置）：
    ```bash
    # 输出到控制台
    python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py weekly-report

    # 写入文件（使用配置的输出目录）
    python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py weekly-report \
      --output-dir "/path/to/output"
    ```
17. 周报规则：
    - **时间范围**：上周五 18:00 至 本周五 17:00（在 Mon-Thu 触发时返回上一个已结束的周期）
    - **过滤条件**：只提取带"工作"标签的日程和待办
    - **结构**：项目 - 进展 - 待办 三级结构
    - **进展**：本周时间范围内有活动的任务（创建 / 更新 / 截止）
    - **待办**：截止时间在本周期结束后、或没有截止时间但状态仍为 active 的任务
    - **期号计算**：基于固定锚点（2026-01-02）按周递推，跨机一致
    - **输出格式**：Markdown 文件
    - **文件名**：`{team_name}{report_title}（YYYY-MM-DD）.md`（默认 `个人工作周报（YYYY-MM-DD）.md`）

## Pitfalls

1. **Calendar / Reminders 权限**：首次运行 AppleScript 会弹权限请求。用户拒绝后所有写入都会失败，且不会再次弹窗 — 需手动到 *系统设置 → 隐私与安全性 → 自动化* 重新授权。
2. **AppleScript 字符转义**：标题 / 备注中的双引号、反斜杠、换行符都会被自动转义，但极少数情况可能仍需手动检查。
3. **时间格式**：AppleScript 的 date 构造对格式敏感，必须使用 `YYYY-MM-DD HH:MM:SS` 格式。
4. **时区**：Calendar 和 Reminders 使用系统时区。`created_at` / `updated_at` 落盘时带本地时区，周报范围判断已做 timezone-aware 处理。
5. **并发写入**：JSON 数据库采用原子重命名写入。**单进程使用安全**，但**多进程并发写入**仍有竞态风险（读 - 改 - 写之间不持锁）。单机交互式使用一般不会触发。
6. **模糊时间解析**：用户说"明天""下周一"等相对时间，需要 agent 根据当前日期正确计算绝对日期。
7. **日历 / 列表名约定（v4.0 关键）**：skill 假设 Apple 已有「工作」和「生活」两个 Reminders 列表 + 两个 Calendar 日历（首次配置时必须建好）。**默认 `--tag-major work` 写入「工作」列表 / 「工作」日历**，不要手写 `--list "提醒事项"` 或 `--calendar "Work"`（v3 旧法，会落到错误列表）。如需 override 列表名，确认目标真实存在，并通过 `work_lists` / `life_lists` / `work_calendars` / `life_calendars` 配置白名单（允许多名共存）。第一次写入前可用 `list-calendars` / `list-reminder-lists` 验证。
8. **截图解析失败**：图片 OCR 可能识别错误，关键字段（尤其是时间和人名）必须向用户二次确认。
9. **多端同步限制**：本 skill 不做多端协同。Mac A 创建的任务在 Mac B 上跑搜索 / 更新 / 周报命令会**完全看不到** — 因为元数据数据库 `tasks.json` 是本地文件。Apple 日历 / 提醒本身会跨设备同步，但脱离本 skill 的元数据上下文。如需多机协同，请按用户需求定制改造。

## Verification

1. 创建任务后，打开 Calendar / Reminders app 验证事件 / 提醒是否成功创建
2. 检查 iPhone / iPad 上是否同步出现
3. 运行 `list-recent --limit 5` 查看最近创建的记录
4. 运行 `list-tags` 查看标签列表
5. 周报生成后，核对任务数量与数据库记录是否一致，确认"生活"标签任务未被包含

## 数据持久化格式

### 任务记录

每个任务以 JSON 对象存储在 `~/.smart-calendar/tasks.json`：

```json
{
  "task_id": "uuid-v4",
  "user_input": "用户原始输入",
  "parsed": {
    "title": "提取标题",
    "task_type": "文件审阅|反馈|调研|文书撰写|会议|其他",
    "project": "项目名",
    "deadline_date": "2026-05-22",
    "deadline_time": "17:00",
    "start_datetime": null,
    "end_datetime": null,
    "priority": "高|中|低",
    "related_people": ["人员1", "人员2"],
    "notes": "额外上下文"
  },
  "formal_title": "正式用语标题",
  "formal_notes": "正式用语备注",
  "calendar_event_id": "Apple Event UID 或 null",
  "reminder_id": "Apple Reminder ID 或 null",
  "tags": ["工作"],
  "created_at": "2026-05-20T14:30:00+08:00",
  "updated_at": "2026-05-20T14:30:00+08:00",
  "status": "active|completed|cancelled"
}
```

### 配置文件

`~/.smart-calendar/config.json`：

```json
{
  "tags": ["工作", "生活"],
  "weekly_report": {
    "enabled": true,
    "output_dir": "",
    "generate_day": "friday",
    "generate_time": "17:00",
    "team_name": "",
    "report_title": "个人工作周报"
  },
  "first_run": true
}
```

## CLI 命令速查

```bash
# 日历 / 提醒操作（v4.0：用 --tag-major + --meta-*）
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py list-calendars
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py list-reminder-lists
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py create-event \
  --title "..." --tag-major work --start "YYYY-MM-DD HH:MM" --end "YYYY-MM-DD HH:MM" \
  --meta-project "..." --meta-task-type "..."
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py create-reminder \
  --title "..." --tag-major work --due "YYYY-MM-DD HH:MM" \
  --meta-project "..." --meta-aux-tags "紧急" --meta-formal-title "..."

# v4.0：从 Apple 真源重建 tasks.json
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py sync
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py sync --dry-run

# 任务管理
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py save-task \
  --task-id "..." --parsed-json '{...}' --tags "工作"
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py search "关键词"
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py update \
  --task-id "xxx" --field "status" --value "completed"
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py delete --task-id "xxx"
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py list-recent --limit 10

# 标签管理
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py list-tags
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py add-tag "紧急"
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py remove-tag "紧急"
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-task-tags \
  --task-id "xxx" --tags "工作,紧急"

# 冲突检测
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py check-conflict \
  --date "YYYY-MM-DD" --time "HH:MM" --duration 60

# 周报
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py weekly-report
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py weekly-report \
  --output-dir "/path/to/output"

# 配置
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py get-config
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
  --key weekly_report.team_name --value "项目组"
python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
  --key weekly_report.output_dir --value "/path"
```

## 文件结构

```
~/.claude/skills/smart-calendar/
├── SKILL.md                          # 本文件
├── README.md                         # 安装与定位说明
├── scripts/
│   ├── task_manager.py               # Python 核心控制器
│   └── smoke_test.py                 # 冒烟测试
├── references/
│   └── applescript_api.md            # AppleScript API 参考
└── templates/
    └── weekly_report.md              # 周报模板（参考用，当前由代码直接拼装）

~/.smart-calendar/          # 数据目录（运行时自动创建）
├── tasks.json                        # 任务数据库
├── config.json                       # 配置文件
└── tmp_*.scpt                        # 临时 AppleScript 文件（用完自动清理）
```

## 已知边界

v4.0 已实现方向 B（Apple 真源 + metadata block + sync），单机版上限大致到这里。剩余边界：

- **写入并发锁**：多进程同时写 tasks.json 仍有竞态风险（单进程交互使用不触发）
- **周五自动触发**：周报生成需用户或外部 scheduler（如 launchd / cron）触发，skill 不内嵌
- **Reminder 标记完成**：update task status 到 completed 不会反向标记 Reminders.app 里的提醒
- **sync 性能**：大型 Apple 库下首次 sync 可能 30~60 秒（实测：少量 active reminder + 几十 calendar event ≈ 51 秒）
- **多机协同（部分实现）**：Apple Calendar / Reminders 通过 iCloud 跨机同步是真源；tasks.json 仍是各机本地缓存。如需在 Mac B 同样体验完整 skill，需另行安装本 skill 并跑一次 `sync` 重建本地缓存
