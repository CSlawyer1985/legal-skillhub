# AppleScript API 参考

## Calendar (日历)

### 创建事件
```applescript
tell application "Calendar"
    set targetCal to first calendar whose name is "Work"
    set newEvent to make new event at end of events of targetCal with properties {
        summary:"事件标题",
        start date:date "2026-05-22 14:00:00",
        end date:date "2026-05-22 15:30:00",
        description:"事件备注",
        location:"会议地点"
    }
    return uid of newEvent
end tell
```

### 更新事件
```applescript
tell application "Calendar"
    set ev to first event whose uid is "EVENT-UID-HERE"
    set properties of ev to {summary:"新标题", description:"新备注"}
end tell
```

### 删除事件
```applescript
tell application "Calendar"
    set ev to first event whose uid is "EVENT-UID-HERE"
    delete ev
end tell
```

### 列出事件（按日期范围）
```applescript
tell application "Calendar"
    set startD to date "2026-05-20 00:00:00"
    set endD to date "2026-05-20 23:59:59"
    repeat with c in calendars
        repeat with ev in (every event of c whose start date ≥ startD and start date ≤ endD)
            -- process event
        end repeat
    end repeat
end tell
```

### 事件属性
- `summary` - 标题
- `start date` - 开始时间
- `end date` - 结束时间
- `description` - 描述/备注
- `location` - 地点
- `uid` - 唯一标识符
- `allday event` - 是否全天事件 (boolean)

## Reminders (提醒事项)

### 创建提醒
```applescript
tell application "Reminders"
    set targetList to first list whose name is "Work"
    set newReminder to make new reminder at end of reminders of targetList with properties {
        name:"提醒标题",
        due date:date "2026-05-22 17:00:00",
        body:"提醒备注",
        priority:1  -- 1=高, 2=中, 3=低, 0=无
    }
    return id of newReminder
end tell
```

### 更新提醒
```applescript
tell application "Reminders"
    set rem to first reminder whose id is "REMINDER-ID-HERE"
    set properties of rem to {name:"新标题", body:"新备注"}
end tell
```

### 删除提醒
```applescript
tell application "Reminders"
    set rem to first reminder whose id is "REMINDER-ID-HERE"
    delete rem
end tell
```

### 列出提醒（按日期范围）
```applescript
tell application "Reminders"
    set startD to date "2026-05-20 00:00:00"
    set endD to date "2026-05-20 23:59:59"
    repeat with rlist in lists
        repeat with rem in (every reminder of rlist whose due date ≥ startD and due date ≤ endD)
            -- process reminder
        end repeat
    end repeat
end tell
```

### 提醒事项属性
- `name` - 标题
- `body` - 备注
- `due date` - 截止日期/时间
- `completion date` - 完成时间
- `completed` - 是否完成 (boolean)
- `priority` - 优先级 (0/1/2/3)
- `id` - 唯一标识符

## 注意事项

1. **权限**：首次运行会弹窗请求"控制 Calendar / Reminders"权限，必须在系统设置中授权
2. **应用未运行**：Calendar 未运行时可能返回 -600 错误。task_manager.py 会先 `open -a Calendar` + sleep 1.5s 兜底
3. **日期格式**：`date "YYYY-MM-DD HH:MM:SS"` 是最可靠的构造方式
4. **中文转义**：字符串中的双引号 `"` 必须转义为 `\"`；反斜杠必须**先**转义；换行用 `" & linefeed & "` 拼接
5. **时区**：AppleScript date 使用系统时区，无需额外处理
6. **delimiter 关键字**：Python 三引号字符串构造 AppleScript 时，**不要用 `"\n"`**（会被 Python 提前展开成真换行，导致 .scpt 字符串跨行编译失败）；统一用 AppleScript 关键字常量 `linefeed`
7. **`as string` 格式 locale 化**：`start date of ev as string` 在中文系统返回 `2026年5月20日 星期三 14:00:00`，Python strptime 无法直接解析。task_manager.py 改用 `(year of dD) & "-" & (month of dD as integer) & "-" & ...` 数值分量拼接
8. **大数据集性能**：用 `(every reminder of rlist whose completed is false)` 让 Reminders.app 端谓词过滤；远比 Python 端循环过滤快（实测：几百条 reminder 库：不过滤 4.5 分钟，谓词过滤 51 秒）
9. **字符串累加 vs list-as-string**：批量构造大输出时，AppleScript 直接 `set out to out & ...` 比 `set end of list to ... ` + `as string` 快得多

---

## 方向 B：metadata block 协议

智能日程 skill 在每条 reminder/event 的 description / body 末尾追加 metadata block，承载次标签和元数据。**格式约定**：

```
[用户可见的备注内容]

────────────────────
smart-calendar metadata (do not edit)
{"v":1,"project":"A 项目","task_type":"文件审阅","aux_tags":["紧急"],"formal_title":"..."}
```

**字段约定**（v1）：
- `v`: 版本号（int）
- `project`: 项目名（string，可选）
- `task_type`: 任务类型枚举（string，可选）
- `aux_tags`: 次标签数组（list of string，可选）
- `formal_title`: 正式标题（string，可选）

**解析逻辑**：
- 从末尾反向找 `────────────────────` fence 行
- fence 下一行必须包含 `smart-calendar metadata (do not edit)`
- 再下一行（或几行）是 JSON
- 解析失败、找不到 fence 都安全 fallback：把整段当 user_notes，metadata 为空 dict

**主标签不在 metadata 里**：主标签（工作 / 生活）由 reminder 所在列表 / event 所在日历名物理推断，不写 JSON 里。这样 iPhone 用户在 Apple 端拖动任务跨列表时，主标签会自动跟着变。
