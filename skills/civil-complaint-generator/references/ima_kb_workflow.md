# ima 知识库 MCP 工具使用指南

本文件详细说明如何使用 ima-mcp MCP 工具完成起诉状模板的检索与获取。

## 工具链概览

| 步骤 | 工具名 | 用途 |
|------|--------|------|
| 1 | `mcp__ima-mcp__get_knowledge_base_list` | 获取所有知识库列表 |
| 2 | `mcp__ima-mcp__search_knowledge` | 在指定知识库内语义检索 |
| 2b | `mcp__ima-mcp__get_knowledge_list` | 列出知识库全部内容（备用方案） |
| 3 | `mcp__ima-mcp__fetch_media_content` | 获取具体文件的完整内容 |

以上四个工具均为 deferred tools，需通过 `ToolSearch` 加载 schema 后用 `DeferExecuteTool` 调用。

## 详细流程

### 步骤 1：获取知识库列表

调用 `mcp__ima-mcp__get_knowledge_base_list`，参数示例：

```json
{
  "limit": 50,
  "type": "KBT_MINE_KB"
}
```

参数说明：
- `limit`：获取数量上限，建议设为 50
- `type`：知识库类型，`KBT_MINE_KB` 为个人知识库，`KBT_SHARED_KB` 为共享知识库

若首次未找到目标知识库，可尝试 `KBT_SHARED_KB` 或不传 type 参数。

从返回结果中查找名称含以下关键词的知识库：
- "案由起诉状规则库"
- "起诉状模板"
- "诉讼文书模板"
- "法律文书"

记录目标知识库的 `knowledge_base_id`。

### 步骤 2：语义检索模板

调用 `mcp__ima-mcp__search_knowledge`，参数示例：

```json
{
  "knowledge_base_id": "<从步骤1获取的ID>",
  "query": "民间借贷纠纷起诉状",
  "filters": [
    {
      "filter_type": "MEDIA_TYPE_FILTER_TYPE",
      "media_type_filter": {
        "media_type": ["MARKDOWN", "TXT", "NOTE"]
      }
    }
  ]
}
```

参数说明：
- `knowledge_base_id`：步骤 1 获取的目标知识库 ID
- `query`：案由名称 + "起诉状"，如"买卖合同纠纷起诉状"
- `filters`：过滤文件类型，优先检索 MARKDOWN 类型（模板通常为 .md 文件）

检索策略：
- 首次检索使用"案由 + 起诉状"作为 query
- 若结果不理想，可尝试仅用案由名称检索
- 若仍无结果，转步骤 2b

### 步骤 2b：列出全部知识（备用方案）

当语义检索无结果时，调用 `mcp__ima-mcp__get_knowledge_list`：

```json
{
  "knowledge_base_id": "<目标知识库ID>",
  "limit": 100,
  "filters": [
    {
      "filter_type": "MEDIA_TYPE_FILTER_TYPE",
      "media_type_filter": {
        "media_type": ["MARKDOWN", "TXT", "NOTE"]
      }
    }
  ],
  "sort_type": "TITLE_SORT_TYPE"
}
```

从返回的文件列表中按标题/文件名匹配案由关键词。

### 步骤 3：获取模板内容

从步骤 2 或 2b 的检索/列表结果中选取最匹配的条目，记录其 `media_id`。

调用 `mcp__ima-mcp__fetch_media_content`：

```json
{
  "media_id": "<从步骤2获取的文件media_id>"
}
```

返回的内容即为模板 .md 文件的完整文本。

## 模板文件结构速查

检索到的 .md 模板文件通常包含以下区块：

```markdown
# [案由名称]起诉状模板

## 【案情输入区】
- 原告信息：姓名、性别、出生年月、住址、联系方式...
- 被告信息：...
- 法律关系要素：合同签订时间、金额、期限...
- 履约情况：...
- 违约事实：...

## 【补充信息输入区】
- 被告身份信息补充：...
- 金额明细确认：...

## 【民事起诉状】
民事起诉状
原告：...
被告：...
诉讼请求：...
事实与理由：...
证据清单：...
此致
[管辖法院]人民法院
起诉人：...
[日期]

## 【法律依据】
- 《民法典》第X条：...
```

解析模板时，重点提取：
1. 【案情输入区】中的字段列表 -- 用于阶段一引导用户
2. 【补充信息输入区】中的字段列表 -- 用于阶段二前置检查
3. 【民事起诉状】中的结构定义 -- 用于阶段二生成起诉状
4. 【法律依据】中的法条 -- 用于法律意见书分析

## 异常处理

| 异常情况 | 处理方式 |
|---------|---------|
| 知识库未连接 | ima-mcp 连接器状态为 disconnected 时，告知用户"知识库未连接，无法检索模板，是否使用通用起诉状模板继续生成？" |
| 未找到匹配模板 | 语义检索和列表检索均无结果时，告知用户"未能在此知识库中找到 [案由] 的专用模板"，询问是否使用通用起诉状结构生成 |
| 多个匹配结果 | 选取相关度最高的一个作为主模板，同时告知用户存在其他备选模板可供查看 |
| 模板内容不完整 | 若模板缺少关键区块（如【民事起诉状】），使用本技能内置通用结构补充缺失部分，并在法律意见书中标注 |
