# 多法域法律研究（Multi-jurisdictional Research）

使用 Legal Data Hunter MCP（40+ 国家，1300 万+ 文件）进行多法域法律研究和风险评估。当用户询问涉及多个国家的法律、比较法、跨境监管分析，或任何欧洲及其他覆盖法域的判例/立法时使用。触发词包括法域比较、跨境风险、多国合规、GDPR 在成员国间的执法，或 Legal Data Hunter 引用。也处理单一非法国法域的研究。

## 安装 Legal Data Hunter

安装 Legal Data Hunter MCP 服务器并验证连接。Legal Data Hunter 通过混合语义 + 关键词搜索，提供对 110+ 国家 1800 万+ 法律文件的访问——包括判例、立法和学说。

### 第一步：检测环境并安装

检查是否在 Claude Code 内运行：

```bash  
which claude 2\>/dev/null  
```

**如果 Claude Code 可用**，运行：

```bash  
claude mcp add legal-data-hunter --transport http https://legaldatahunter.com/mcp  
```

**如果不是 Claude Code**（Cursor、VS Code、Windsurf、JetBrains、Copilot、Lawvable），运行：

```bash  
npx legal-data-hunter --yes  
```

这会自动检测客户端，并将 MCP 配置写入正确位置。支持：Cursor、VS Code、Lawvable、Windsurf、Copilot CLI 和 JetBrains（Junie）。

### 第二步：验证安装

安装后，确认 MCP 服务器已连接。在 Claude Code 中，重新连接 MCP 服务器并检查 `Legal Data Hunter` 是否连同其工具一起出现。该服务器暴露 7 个工具：

| 工具 | 用途 |  
|------|---------|  
| `discover\_countries()` | 列出全部 110+ 个已索引国家及文件数量 |  
| `discover\_sources(country)` | 列出某国家的可用来源（如 `"FR"`、`"DE"`、`"EU"`） |  
| `search(query, ...)` | 跨法域混合语义 + 关键词搜索 |  
| `resolve\_reference(citation)` | 查找特定引用——ECLI、CELEX、条款编号、案号 |  
| `get\_document(id)` | 按 ID 检索文件的全文 |  
| `get\_filters()` | 列出可用筛选选项（法院、文件类型、日期范围） |  
| `report\_source\_issue(...)` | 报告数据源问题或请求新增来源 |

### 第三步：开始使用

连接后，以下是一些值得尝试的实用初始查询：

**探索覆盖范围：**  
- 调用 `discover_countries()` 查看所有已索引法域及其文件数量  
- 调用 `discover_sources("FR")` 查看法国法院数据库、立法来源和学说

**跨法域搜索：**  
- `search("unfair dismissal", country="DE", doc_type="case_law")` —— 德国关于不公平解雇的判例  
- `search("artificial intelligence regulation", country="EU")` —— 欧盟关于 AI 的立法  
- `search("data protection breach notification", country="UK")` —— 英国 GDPR 执法

**解析特定引用：**  
- `resolve_reference("ECLI:EU:C:2014:317")` —— 按 ECLI 查找 CJEU 判决  
- `resolve_reference("32016R0679")` —— 按 CELEX 编号查找 GDPR  
- `resolve_reference("Article 49 TFEU")` —— 查找条约条款

**检索完整文件：**  
- 使用 `get_document(id)`，传入 search 或 resolve_reference 返回的 ID，获取完整文本

## 提示

- **自然语言有效**：搜索引擎理解法律概念，而不仅仅是关键词。"Can an employer fire someone for social media posts?"（雇主能否因社交媒体发帖解雇员工？）与"dismissal social media misconduct"（解雇 社交媒体 不当行为）同样有效。  
- **交叉参照**：先在一个法域搜索，再用同一查询在另一法域搜索，以比较跨国法律做法。  
- **引用链**：先用 `resolve_reference()` 找到一部法律，再用该法律名称 `search()`，找出所有援引它的法院判决。  
- **筛选缩小结果**：先调用 `get_filters()` 查看可用筛选选项，再将其传给 `search()`。  
- **缺少来源？** 使用 `report_source_issue()` 请求新增法律来源或报告问题。新来源可在 48 小时内完成索引。

## 链接

- 仪表板：https://legaldatahunter.com  
- API 文档：https://legaldatahunter.com/docs  
- GitHub：https://github.com/worldwidelaw/legal-sources  
- MCP 端点：https://legaldatahunter.com/mcp  
