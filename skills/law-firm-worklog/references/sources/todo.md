# 数据源适配器：Microsoft To Do

主 SKILL.md 在涉及数据源的步骤里加载本文件。本文件分为四节：MCP 工具集、首次配置脚本（流程 A 第二组）、B2 数据拉取、B3 字段归一化。

## MCP 工具集

本适配器依赖社区 MCP（`jordanburke/microsoft-todo-mcp-server`）。

关心的工具能力：

| 能力 | 工具 |
|------|------|
| 列出 task lists | `mcp__microsoft_todo__get_task_lists` |
| 查询 tasks + filter | `mcp__microsoft_todo__get_tasks` |

### 工具不可见时的提示文案

> 这个 skill 需要先装好 Microsoft To Do MCP server 才能跑。需要 Azure App Registration（企业账号），参考 https://github.com/jordanburke/microsoft-todo-mcp-server 配置，配好后回来跟我说一声。

> 注意：个人 Microsoft 账户（outlook.com/hotmail.com/live.com）可能遇到 `MailboxNotEnabledForRESTAPI` 错误，需使用企业账号。

### 鉴权失败（401/403）

> Microsoft To Do MCP 授权可能已过期，请在浏览器重新授权后重试。

不要继续拉数据。

---

## 首次配置脚本（流程 A 第二组：MS To Do 分支）

### 步骤 1：列出可用的 task lists

调用 `mcp__microsoft_todo__get_task_lists`，让用户勾选哪些是"工作"list。

### 步骤 2：确认状态映射

> 在你的 To Do 里，"已完成"的任务状态是什么？通常是 "completed"。

写入 `profile.md`：

```markdown
## 工作单元白名单（MS To Do）
| list_id | name | status_done_value |
|---------|------|------------------|
| `<id>`  | 工作 | completed        |
```

---

## B2 数据拉取

调用 `mcp__microsoft_todo__get_tasks`，用 OData filter：

```
$filter=taskListId eq '<list_id>' and status eq 'completed' and completedDateTime/dateTime ge '<起始日>' and completedDateTime/dateTime le '<截止日>'
```

**注意**：日期格式用 ISO 8601（如 `2026-05-01`）。

**分页**：返回 `@odata.nextLink` 标记时补拉至全部。

---

## B3 字段归一化

归一化输出：

```json
{
  "date":        "YYYY-MM-DD",   // 北京时间日期
  "title":       "<task.title>",
  "project_key": "<taskListId>",
  "is_all_day":  false
}
```

MS To Do 没有全天事件概念，一律 `false`。

时区：`completedDateTime` 是 UTC，按 +8 小时取北京时间日期。

---

## 流程 C：增删 task list（MS To Do 分支）

用户说"新增/删除一个工作 list" → 修改 `profile.md` 的"工作单元白名单"表格对应行。