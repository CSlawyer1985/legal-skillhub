# 数据源适配器：飞书 / Lark 任务模块

主 SKILL.md 在涉及数据源的步骤里加载本文件。本文件分为四节：MCP 工具集、首次配置脚本（流程 A 第二组）、B2 数据拉取、B3 字段归一化。

本适配器基于**飞书原生任务模块**（非多维表格）。

## MCP 工具集

依赖飞书官方 `lark-openapi-mcp` 的 Task Management Preset。

关心的工具能力：

| 能力 | 工具 |
|------|------|
| 列出任务 | `lark_task_list` |
| 获取任务详情 | `lark_task_get` |

### 工具不可见时的提示文案

> 这个 skill 需要先在 Claude Code 里装好飞书 MCP（lark-openapi-mcp）的 Task Management Preset 才能跑。
>
> 配置方法：
> 1. 安装 lark-openapi-mcp：`npm install -g @larksuiteoapi/lark-mcp`
> 2. 在 MCP 配置中启用任务 preset：`-t preset.task.default`
> 3. 在飞书开放平台建企业自建应用，给它"任务"权限
> 4. 把 app_id/app_secret 配给 MCP server
>
> 配好后回来跟我说一声。

### 鉴权失败（401/403）

> 飞书 MCP 的 tenant_access_token 可能已过期，或应用没拿到任务模块的访问权限。请确认应用有"任务"读取权限后重试。

不要继续拉数据。

---

## 首次配置脚本（流程 A 第二组：飞书任务分支）

飞书任务模块不需要用户自建表。用户确认在用飞书任务功能后，问：

> 飞书任务的"完成"状态在你那边叫什么？通常是"已完成"/"Done"。告诉我在飞书任务里选任务时，"已完成"对应的值是什么。

写入 `profile.md`：

```markdown
## 工作单元白名单（飞书任务）
| status_done_value |
|-------------------|
| 已完成             |
```

飞书任务模块没有"任务列表"概念，所有任务统一处理。

---

## B2 数据拉取

调用飞书任务 list 工具，按状态 + 完成时间筛选：

```json
{
  "query": {
    "status": "<status_done_value>",
    "completed_time_start": "<起始日 UTC 毫秒时间戳>",
    "completed_time_end": "<截止日次日 UTC 毫秒时间戳>"
  },
  "page_size": 100
}
```

注意：

- 飞书任务的 `completed_time` 是**毫秒级 UNIX 时间戳**。北京日期 `2026-05-01 00:00:00 +08:00` → UTC 是 `2026-04-30 16:00:00` → 准确换算。
- 起止区间做成 `[起始日 00:00, 截止日次日 00:00)` 半开，避免边界条目丢失。

**分页**：返回 `has_more` / `page_token` 标记，补拉至全部。

---

## B3 字段归一化

每条任务的关键字段：

- `title`：任务标题（字符串）
- `completed_time`：完成时间（毫秒时间戳，UTC）

时区处理：

- `completed_time` 是 UTC 毫秒时间戳。除以 1000 得 epoch 秒，加 8 小时（`+ 28800` 秒）得北京时间，取日期部分。

归一化输出：

```json
{
  "date":        "YYYY-MM-DD",   // 北京时间日期
  "title":       "<task.title>",
  "project_key": "*",            // 飞书任务无列表概念，用 * 兜底
  "is_all_day":  false
}
```

飞书任务没有全天事件概念，一律 `false`。

---

## 流程 C：增删工作单元（飞书分支）

飞书任务模块没有"任务列表"概念。如果用户说"新增/删除一个工作相关的东西"，告知飞书任务模块是全局的，所有任务都参与，无需维护白名单。