# 数据源适配器：滴答清单 / TickTick (DiDa365)

主 SKILL.md 在涉及数据源的步骤里加载本文件。本文件分为四节：MCP 工具集、首次配置脚本（流程 A 第二组）、B2 数据拉取、B3 字段归一化。

## MCP 工具集

本适配器依赖以下工具：

| 工具 | 用途 |
|------|------|
| `mcp__dida364__list_projects` | 列出当前账户下所有项目，用于首次配置时确定工作项目白名单 |
| `mcp__dida364__list_completed_tasks_by_date` | 拉取指定日期范围内已完成任务（按 projectIds 过滤） |

### 工具不可见时的提示文案

> 这个 skill 需要先在 Claude Code 里装好滴答清单 MCP 才能跑（用来从滴答拉已完成任务）。可以参考 https://github.com/dida365/mcp-server 或滴答官方文档配置 MCP server，配好后回来跟我说一声。

### 鉴权失败（401/403）

> 滴答 MCP 授权可能已过期，请在浏览器重新登录滴答账号后重试。

不要继续拉数据。

---

## 首次配置脚本（流程 A 第二组：DiDa365 分支）

调用 `mcp__dida364__list_projects` 列出所有项目，然后问：

> 上面这些项目里，**哪几个是"工作"项目**？（这些里的已完成任务会被拉进工时；没被你标的项目自动不参与，不用单独列。）

收齐用户勾选的 projectId 后写入 `profile.md`：

```markdown
## 工作单元白名单（DiDa365 项目）
| projectId | 用途 |
|-----------|------|
| `<id>`    | 主工作项目 |
```

黑名单不参与任何逻辑——其余项目自动不进白名单即可，不用让用户标"个人/学习/家庭"。

---

## B2 数据拉取

调用：

```
mcp__dida364__list_completed_tasks_by_date
```

参数：

```json
{
  "search": {
    "startDate": "<起始日>T00:00:00+08:00",
    "endDate":   "<截止日>T23:59:59+08:00",
    "projectIds": [<读自 profile.md 的工作项目 ID 白名单>]
  }
}
```

**绝不**不带 projectIds 全量拉取——用户可能有上千条历史任务。

**分页**：返回结果如有 `hasMore` 标记，必须补拉至全部。

---

## B3 字段归一化

每条任务归一化成四元组：

```json
{
  "date":        "YYYY-MM-DD",   // 北京时间日期
  "title":       "<task.title>",
  "project_key": "<task.projectId>",
  "is_all_day":  <bool>
}
```

**全天任务时区处理（滴答特有坑）**：

滴答 API 对 `isAllDay: true` 的任务返回 `completedTime` 为 `YYYY-MM-DDT16:00:00+0000`（UTC 16:00）。加 8 小时后落到次日 00:00。

**修正规则**：当 `isAllDay == true` 时，归一化日期取 `completedTime` 的日期部分 +1 天。

归一化输出示例：

```json
{
  "date":        "2026-05-15",
  "title":       "审阅合同",
  "project_key": "abc123",
  "is_all_day":  true
}
```

---

## 流程 C：增删工作项目（DiDa365 分支）

用户说"新增/删除一个工作项目" → 修改 `profile.md` 的"工作单元白名单"表格对应行。