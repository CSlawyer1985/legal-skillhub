---
name: directory-index
description: Generate local directory indexes as Markdown or interactive HTML. Use when the user asks to create a folder index, file list, searchable/collapsible directory page, clickable local file opener, Finder/Explorer reveal page, data room index, due diligence file index, or structured inventory of a local directory. Supports Markdown output, HTML with local server, natural numeric sorting, skip rules, tags, and cross-platform open/reveal actions.
metadata:
  name_zh: 目录索引器
  version: '1.0'
---

# directory-index

对任意本地目录生成文件索引。支持两种输出模式，兼容 macOS / Windows / Linux：

- **Markdown 纯展示版**：静态 `.md` 文件，按目录层级递进标题（`##`→`###`→`####`），适合嵌入笔记/文档/Wiki
- **HTML 可跳转版**：交互式 `.html` 页面 + 本地 HTTP 服务器，可折叠树形结构，点击文件名用系统默认应用打开，支持搜索过滤

## 触发条件

- 用户要求为某个目录生成索引 / 文件清单 / 文件列表
- 用户想要一个可以点击打开文件的目录页面
- 用户说"给这个目录做个 index"、"列一下这个文件夹的所有文件并可以打开"

## 启动流程

1. **确认目录**：获取用户要索引的本地文件夹路径（绝对路径）
2. **确认输出模式**：用 `ask_followup_question` 询问用户：
   - Markdown 纯展示版（静态 .md，无需服务器）
   - HTML 可跳转版（交互式 .html + 服务器，点击可打开文件）
3. **执行生成**：根据用户选择调用脚本

## 使用方式

### Markdown 纯展示版

```bash
python3 "$SKILL_DIR/scripts/generate_index.py" "/path/to/target/directory" --format md
```

输出：目标目录下生成 `INDEX_<目录名>.md`

### HTML 可跳转版

```bash
python3 "$SKILL_DIR/scripts/generate_index.py" "/path/to/target/directory" --format html
```

输出：目标目录下生成 `INDEX_<目录名>.html` + `INDEX_<目录名>_server.py`，自动启动服务器并打开浏览器

### 通用参数

- 第一个参数（必填）：目标目录的绝对路径
- `--format`（必填）：输出格式，`md` 或 `html`
- `--max-depth`（可选）：最大递归深度，默认不限制。深层目录推荐 `--max-depth 3`
- `--port`（可选，仅 html）：服务器端口，默认 8427
- `--no-open`（可选，仅 html）：不自动打开浏览器
- `--tags`（可选）：自定义标签规则 JSON，格式见下方

## 跳过提示

扫描时会自动跳过 `node_modules`、`.git`、`__pycache__`、`venv`、`dist`、`build`、`.cache` 等大型/无意义目录。所有跳过信息都会**明确提示**：

1. **终端输出**：跳过的目录逐条列出（含原因），深度限制未展开的子目录单独列出
2. **Markdown 输出**：页首显示"已跳过的目录"（逐条带原因）和"因深度限制未展开"
3. **HTML 输出**：统计卡片下方显示跳过提示区（每个目录含原因标签）

跳过原因分两类：
- **默认跳过**：`node_modules`、`.git` 等已知无意义目录
- **深度限制**：因 `--max-depth` 设置而未展开的子目录
- **权限不足**：无读取权限的目录

## 大型目录处理

面对多层嵌套 + 数百文件的复杂目录，做了以下优化：

1. **自动跳过** `node_modules`、`.git`、`__pycache__`、`venv`、`dist`、`build`、`.cache` 等常见大型/无意义目录
2. **`--max-depth`** 控制递归深度，避免过深的目录树
3. **HTML 可折叠树形结构**：目录默认折叠，点击折叠/展开，支持"全部展开/折叠"按钮
4. **自然排序**：按数字语义排序目录和文件名，避免 `10.0` 排在 `2.0` 前面
5. **搜索过滤**：HTML 模式内置搜索框，输入即过滤文件名
5. **Markdown 层级递进**：按目录深度用 `##`/`###`/`####` 区分层级，深层文件自动缩进

示例：
```bash
# 深层项目目录，限制 3 层
python3 "$SKILL_DIR/scripts/generate_index.py" "/path/to/project" --format html --max-depth 3
```

## 跨平台支持

脚本兼容 macOS / Windows / Linux：

| 功能 | macOS | Windows | Linux |
|------|-------|---------|-------|
| 打开文件 | `open` | `os.startfile` | `xdg-open` |
| 定位文件 | `open -R` | `explorer /select,` | `xdg-open` (打开所在目录) |
| 打开浏览器 | `open` | `start` | `xdg-open` |
| 杀端口进程 | `lsof` + `kill` | `netstat` + `taskkill` | `lsof` + `kill` |

HTML 模式生成的服务器脚本（`INDEX_xxx_server.py`）同样跨平台，可在任意系统上独立运行。

## 自定义标签

通过 `--tags` 参数为特定文件或目录添加标签：

```bash
python3 "$SKILL_DIR/scripts/generate_index.py" "/path/to/dir" \
  --format html \
  --tags '{"readonly": ["report_*.xlsx", "*/archive/*"], "main": ["main_*.xlsx"], "backup": ["*backup*"]}'
```

支持的标签类型：
- `readonly` — 只读
- `main` — 主文件
- `backup` — 备份
- `pending` — 待确认
- 自定义标签名 — 显示为标签名

## 工作原理

### Markdown 模式
1. 扫描目标目录，递归获取所有文件和子目录
2. 检测文件类型，分配图标标签
3. 生成 `INDEX_<目录名>.md` 到目标目录
4. 无需服务器，纯静态文件

### HTML 模式
1. 扫描目标目录，递归获取所有文件和子目录
2. 检测文件类型（xlsx/docx/eml/md/pdf/其他），分配图标和颜色
3. 生成 `INDEX_<目录名>.html` 到目标目录
4. 启动 Python 本地 HTTP 服务器（默认 8427 端口）
5. 服务器提供三个接口：`/health`（状态检查）、`/open?path=xxx`（打开文件）和 `/reveal?path=xxx`（资源管理器/Finder 定位）
6. 自动在系统浏览器中打开 `http://localhost:<port>/`
7. 如果用户误用 `file://` 直接打开 HTML，页面会在服务器已运行时自动跳转到本地服务器；服务器未运行时显示明确提示

## 技术依赖

- Python 3（使用标准库 `http.server`，无需 pip install）
- 系统浏览器（Safari/Chrome/Edge/Firefox，仅 HTML 模式需要）
- 无其他外部依赖

## 真实场景优化经验

面向大型资料室、尽调文件夹、项目交割材料等目录时，优先使用 HTML 模式。脚本已针对实际使用中常见问题做了防护：默认折叠大型目录树、自然排序编号目录、点击文件名不使用 `<a>` 默认导航、检测 `file://` 误打开并自动跳转服务器地址、服务器返回 no-cache 头避免旧页面缓存。

## 注意事项

- HTML 模式必须通过 `http://localhost:<port>/` 使用，不能直接依赖 `file://` 本地打开；脚本会自动打开服务器地址
- 如果双击 HTML 文件打开，页面会尝试检测本地服务器并自动跳转；服务器未运行时会显示启动提示
- HTML 模式服务器会以后台进程启动；如需重新启动，可运行目标目录下的 `INDEX_<目录名>_server.py`
- 已存在的同端口服务器会自动替换，并启用端口复用降低重启失败概率
- HTML 文件和服务器脚本生成在目标目录下，不污染其他位置
- Markdown 模式零依赖，生成后即可在任何 Markdown 编辑器中查看
- Windows 下杀端口使用 `netstat -ano | findstr :端口号` → `taskkill /F /PID <pid>`

## 输出文件

### Markdown 模式
- `INDEX_<目录名>.md` — 索引页面

### HTML 模式
- `INDEX_<目录名>.html` — 索引页面
- `INDEX_<目录名>_server.py` — 服务器脚本（可独立启动：`python3 INDEX_xxx_server.py`）
