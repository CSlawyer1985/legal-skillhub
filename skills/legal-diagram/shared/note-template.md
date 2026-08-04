# Markdown 图表模板

由生成核心和教程编写的 Markdown 输出。用户未提供输出路径时，默认文件夹为 `./diagrams/`。

## 页眉

```markdown
# <标题>

- 事项类型：<matter_type>
- 图表类型：<diagram_type>
- 来源：<来源标签或基本名称>
- 状态：草稿
```

## 正文

```markdown
# <标题>

## 图表摘要

<图表展示内容的一段通俗语言描述>

```mermaid
<Mermaid 块>
```
```

围栏 Mermaid 块在任何支持 Mermaid 的 Markdown 查看器中渲染。HTML 导出（`workflows/html-export.md`）是独立且可选的。
