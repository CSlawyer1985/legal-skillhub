[English](README.md) · **中文**

# smart-calendar（智能日程 · 单机版）

> macOS / iOS 苹果生态下的智能日程与待办事项管理 skill。面向需要专业书面表达的知识工作者，把口语化任务描述转换为正式书面语并写入 Apple 日历 / 提醒事项，自动按项目生成工作周报。

## 这是单机版

每台 Mac 独立维护本地任务数据库（`~/.smart-calendar/tasks.json`）。日历事件和提醒事项本身会通过 iCloud 自动同步到你的其他 Apple 设备，但本 skill 的元数据（formal_title / 标签 / 项目 / 任务类型等）**不跨机同步**。

如需多端协同，需要额外定制改造 — 不在本分发版范围内。

## 安装

将整个 `smart-calendar/` 目录放到 `~/.claude/skills/`：

```bash
cp -r /path/to/smart-calendar ~/.claude/skills/
```

或软链：

```bash
ln -s /path/to/smart-calendar ~/.claude/skills/smart-calendar
```

数据目录 `~/.smart-calendar/` 会在首次运行时自动创建。

## 首次使用前必做

1. **授予 Automation 权限**
   首次运行操作 Calendar / Reminders 的命令时，macOS 会弹出权限请求。必须授权，否则后续写入全部失败。
   后续如需重新检查，到：*系统设置 → 隐私与安全性 → 自动化* 找到对应应用（Terminal / iTerm / Claude Code / 你的 agent 进程）→ 确保 Calendar 与 Reminders 都打勾。

2. **配置周报标题**（可选）
   ```bash
   # 默认标题就是 "个人工作周报"，个人用不需要改
   # 如要团队前缀（标题变成 "{team_name}{report_title}"）：
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
     --key weekly_report.team_name --value "项目组"
   # 如要改主标题：
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
     --key weekly_report.report_title --value "重点项目周报"
   ```
   不配的话默认标题就是 "个人工作周报"，无团队前缀。

3. **配置周报输出目录**（必做，否则只能输出到控制台）
   ```bash
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
     --key weekly_report.output_dir \
     --value "/path/to/your/weekly/report/folder"
   ```

4. **建好 Apple 列表 / 日历 + 检查命名**
   ```bash
   # 先在 Reminders.app 建「工作」+「生活」列表
   # 在 Calendar.app 建「工作」+「生活」iCloud 日历
   # 然后验证：
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py list-reminder-lists
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py list-calendars
   ```
   skill 默认 `--tag-major work` 写入「工作」列表 / 日历；`life` 写入「生活」。如果你想用别的列表 / 日历名，通过 `set-config --key work_lists --value '["XX"]'`（同理 `life_lists` / `work_calendars` / `life_calendars`）。

## 验证安装

```bash
python3 ~/.claude/skills/smart-calendar/scripts/smoke_test.py
```

冒烟测试会创建一条测试提醒和一个测试日历事件、做查询和更新、生成示例周报，最后清理测试数据。全部通过即视为安装成功。

## 触发用例

让 agent 处理类似输入：

- "明天之前把 A 项目方案改完发给协作方"
- "下周三下午 2-4 点和团队开评审会，议题是 B 项目"
- "把上次那个清单的截止时间改到周五"
- "生成本周周报"
- 直接拖入聊天截图 / 邮件截图，让 agent OCR + 解析

agent 会：解析输入 → 提取结构化字段 → 与你确认 → 生成正式书面语 → 检测时间冲突 → 写入 Apple 日历 / 提醒事项 → 保存元数据。

## 可选：启用自动 loop（每日 sync + 周五周报）

> 默认**不启用**。skill 平时靠 agent 实时调用即可。如果你想让"每日同步 + 周五自动出周报"无人值守地跑，按下面启用 launchd 心跳。
>
> 这是 [Loop Engineering](https://addyosmani.com/blog/loop-engineering/) 的最小落地：一个 automation（launchd）+ 一个 skill（本 skill）+ 一个 state file（`loop-state.json`）+ 一个 gate（结构性断言）。

**两个心跳命令**（也可手动随时跑）：
```bash
# 每日 sync：从 Apple 重建 tasks.json
python3 .../scripts/task_manager.py loop-tick --mode daily

# 周五周报：sync + 生成周报 .md（需先配 weekly_report.output_dir）
python3 .../scripts/task_manager.py loop-tick --mode weekly

# 查看 loop 健康状态（最近运行 / 错误 / history）
python3 .../scripts/task_manager.py loop-status
```

**挂 launchd 自动触发**（每日 18:00 + 周五 17:00）：
```bash
# 1. 查出你的 python3 绝对路径
which python3                       # 如 /opt/homebrew/bin/python3

# 2. 编辑两个模板，替换 {{PYTHON3}} 和 {{SKILL_PATH}} 占位符
#    {{SKILL_PATH}} = task_manager.py 绝对路径
vi templates/com.smartcalendar.daily.plist.template
vi templates/com.smartcalendar.weekly.plist.template

# 3. 拷到 LaunchAgents 并加载
cp templates/com.smartcalendar.daily.plist.template  ~/Library/LaunchAgents/com.smartcalendar.daily.plist
cp templates/com.smartcalendar.weekly.plist.template ~/Library/LaunchAgents/com.smartcalendar.weekly.plist
launchctl load -w ~/Library/LaunchAgents/com.smartcalendar.daily.plist
launchctl load -w ~/Library/LaunchAgents/com.smartcalendar.weekly.plist

# 停用：
launchctl unload -w ~/Library/LaunchAgents/com.smartcalendar.daily.plist
launchctl unload -w ~/Library/LaunchAgents/com.smartcalendar.weekly.plist
```

**loop 失败如何感知**：每次 tick 失败会弹 macOS 通知（Basso 声）+ 写 `loop-state.json` 的 `last_error`。建议每隔几天 `loop-status` 扫一眼 `history`，确认 loop 健康——这是对抗"loop 静默失败"的最小习惯。

⚠️ **不要把它当甩手掌柜**：loop 帮你同步和出草稿，但周报内容、任务归类仍需你定期 review。loop 降低的是机械操作成本，不是判断成本。

## 文件清单

| 路径 | 用途 |
|---|---|
| `SKILL.md` | skill 主入口，定义 agent 执行流程 |
| `README.md` / `README.zh-CN.md` | 英文 / 中文说明 |
| `scripts/task_manager.py` | Python 核心控制器（CLI，含 sync / loop-tick） |
| `scripts/smoke_test.py` | 冒烟测试（92 项） |
| `references/applescript_api.md` | AppleScript API 参考 |
| `templates/weekly_report.md` | 周报模板（参考用，当前由代码直接拼装） |
| `templates/com.smartcalendar.daily.plist.template` | 每日 sync loop 的 launchd 模板 |
| `templates/com.smartcalendar.weekly.plist.template` | 每周周报 loop 的 launchd 模板 |

## 环境变量

| 变量 | 默认值 | 用途 |
|---|---|---|
| `SMART_CALENDAR_DATA_DIR` | `~/.smart-calendar` | 数据目录路径，可指向 iCloud Drive 或其他自定义位置（不建议用于多端同步） |

## 版本

v1.1 · 单机版 · Apple 真源架构（sync）+ 可选 launchd loop。不含跨机协同。

## 许可

MIT
