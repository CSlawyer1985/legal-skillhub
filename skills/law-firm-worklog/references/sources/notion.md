# 数据源适配器：Notion

主 SKILL.md 在涉及数据源的步骤里加载本文件。本文件分为四节：MCP 工具集、首次配置脚本（流程 A 第二组）、B2 数据拉取、B3 字段归一化。

## MCP 工具集

本适配器依赖官方 Notion MCP（`makenotion/notion-mcp-server`）。

关心的工具能力：

| 能力 | 工具 |
|------|------|
| 搜索 database | `mcp__notion__search` |
| 查询 database + filter | `mcp__notion__query_database` |

### 工具不可见时的提示文案

> 这个 skill 需要先装好 Notion MCP server 才能跑。可以参考 https://github.com/makenotion/notion-mcp-server 配置，配好后回来跟我说一声。

### 鉴权失败（401/403）

> Notion MCP 授权可能已过期，请在浏览器重新授权后重试。

不要继续拉数据。

---

## 首次配置脚本（流程 A 第二组：Notion 分支）

Notion 的 database schema 是用户自定义的，**必须显式问清**，不能靠列名猜。

### 步骤 1：列出可用的 database

调用 `mcp__notion__search`，让用户确认哪个 database 包含工作任务。

### 步骤 2：问清 schema

> 我需要知道你的 Notion database 有哪些字段。请告诉我：
>
> 1. **状态字段**叫什么名字？（完成的任务在这个字段里是什么值，比如"Done"/"已完成"）
> 2. **完成时间字段**叫什么名字？（记录任务完成的时间）
>
> 如果有其他相关字段也可以一起告诉我。

写入 `profile.md`：

```markdown
## 工作单元白名单（Notion）
| database_id | 状态字段 | 完成值 | 完成时间字段 |
|------------|---------|--------|-------------|
| `<id>`     | Status  | Done   | Completed   |
```

---

## B2 数据拉取

调用 `mcp__notion__query_database`，按状态 + 完成时间过滤：

```json
{
  "database_id": "<白名单中的 database_id>",
  "filter": {
    "property": "<状态字段名>",
    "status": { "equals": "<完成值>" }
  },
  "filter": {
    "property": "<完成时间字段名>",
    "date": { "on_or_after": "<起始日>", "on_or_before": "<截止日>" }
  }
}
```

**注意**：Notion API 的 filter 组合用 `and` 逻辑。

**分页**：返回结果如有 `has_more: true`，用 `start_cursor` 补拉至全部。

---

## B3 字段归一化

归一化输出：

```json
{
  "date":        "YYYY-MM-DD",   // 北京时间日期
  "title":       "<page.title>",
  "project_key": "<database_id>",
  "is_all_day":  false
}
```

Notion 没有原生"全天事件"概念，一律 `false`。

时区：`<完成时间字段>` 是 UTC 或本地时间取决于 workspace 设置，这里默认取日期部分即可。

---

## 流程 C：增删 database（Notion 分支）

用户说"新增/删除一个工作 database" → 修改 `profile.md` 的"工作单元白名单"表格对应行。