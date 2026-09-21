# 目录索引器（directory-index）v1.0

给任意本地文件夹一键生成可搜索、可点击的文件索引页。

---

## 它做什么

你有一个文件夹，里面层层叠叠放了几百个文件，想快速知道"到底有什么、在哪里"——目录索引器扫一遍这个文件夹，生成两种格式的索引：

- **Markdown 版**：纯文本目录清单，适合嵌入笔记或 Wiki
- **HTML 版**：交互式网页，带搜索框、可折叠目录树、点击直接打开文件

典型场景：尽调资料室、项目交割材料、合同文件夹、代码仓库文档目录。

---

## 快速开始

### 环境要求

- Python 3.6+（macOS / Windows / Linux 均可）
- 无需 pip install 任何东西，零外部依赖
- HTML 模式需要一个浏览器

### 基本用法

```bash
# Markdown 版（生成 .md 文件，无需服务器）
python3 scripts/generate_index.py "/path/to/your/folder" --format md

# HTML 版（生成 .html 页面 + 自动启动本地服务器）
python3 scripts/generate_index.py "/path/to/your/folder" --format html
```

生成完成后：
- Markdown 版：打开目标目录下的 `INDEX_<文件夹名>.md`
- HTML 版：浏览器会自动打开 `http://localhost:8427/`

### 常用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--format` | 输出格式，`md` 或 `html`（必填） | `--format html` |
| `--max-depth` | 最大递归深度，默认不限制 | `--max-depth 3` |
| `--port` | 服务器端口，默认 8427（仅 HTML） | `--port 9000` |
| `--no-open` | 不自动打开浏览器（仅 HTML） | `--no-open` |
| `--tags` | 自定义标签规则，JSON 格式 | 见下方"标签"章节 |

---

## 功能一览

### 搜索过滤

HTML 版内置搜索框，输入文件名关键词即时过滤，搜索时自动展开所有目录。

### 可折叠目录树

目录默认折叠，点击展开/折叠，另有"全部展开/折叠"按钮。对几百个文件的目录不会一眼看花。

### 自然排序

目录和文件名按数字语义排序：`1.0` → `2.0` → `10.0`，不会出现 `10.0` 排在 `2.0` 前面的问题。

### 点击打开文件

HTML 版点击文件名，直接用系统默认应用打开（比如 PDF 用预览、xlsx 用 Excel）。点击定位图标，在 Finder/资源管理器里显示文件位置。

### 自动跳过无意义目录

扫描时自动跳过 `node_modules`、`.git`、`__pycache__`、`venv`、`dist`、`build`、`.cache` 等 12 类目录，并在索引页和终端明确列出跳过了什么、为什么跳过。

### 自定义标签

给特定文件或目录打标签，在索引页上直观标识：

```bash
python3 scripts/generate_index.py "/path/to/dir" \
  --format html \
  --tags '{"readonly": ["report_*.xlsx", "*/archive/*"], "main": ["main_*.xlsx"], "backup": ["*backup*"]}'
```

内置标签类型：`readonly`（只读）、`main`（主文件）、`backup`（备份）、`pending`（待确认），也支持自定义标签名。

---

## HTML 模式访问方式

HTML 版通过本地服务器运行，地址是 `http://localhost:8427/`。

如果误操作双击了 HTML 文件（浏览器地址栏显示 `file://...`），页面会：
1. 自动检测本地服务器是否在运行
2. 服务器在运行 → 自动跳转到 `http://localhost:8427/`
3. 服务器没运行 → 显示提示，告诉你怎么启动

服务器重启方式：运行目标目录下的 `INDEX_<文件夹名>_server.py`。

---

## 输出文件

两种模式都会在目标目录下生成索引文件，不污染其他位置：

**Markdown 模式**
- `INDEX_<文件夹名>.md`

**HTML 模式**
- `INDEX_<文件夹名>.html` — 索引页面
- `INDEX_<文件夹名>_server.py` — 服务器脚本（可独立运行）

---

## 跨平台支持

| 功能 | macOS | Windows | Linux |
|------|-------|---------|-------|
| 打开文件 | `open` | `os.startfile` | `xdg-open` |
| 定位文件 | `open -R` | `explorer /select,` | `xdg-open` |
| 打开浏览器 | `open` | `start` | `xdg-open` |

注：Windows 路径兼容性已做代码级处理，但尚未在 Windows 机器上实际验证。

---

## 安装（WorkBuddy 场景）

1. 获取 `directory-index-v1.0.skill` 安装包
2. 在 WorkBuddy 的 Skills 管理页面上传
3. 安装完成后，对话中说"帮我给 XX 目录建索引"即可触发

---

## 实战验证

已在某大型文件夹（528 文件 / 172 目录）上完整测试通过，包括：点击打开文件、搜索过滤、目录折叠、自然排序、file:// 误打开自动跳转、非默认端口等场景。

---

## 许可

本技能零外部依赖，代码基于 Python 标准库，可自由使用和修改。
