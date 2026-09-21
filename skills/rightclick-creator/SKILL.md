---
name: rightclick-creator
description: 【macOS Only】右键神器。 当用户提到以下任一意图时，必须立即使用此 Skill： 「安装右键工具」「批量安装右键」「右键工具集」「macOS右键菜单」 「帮我装右键」「装右键工具」「添加右键菜单」「Finder右键」 「右键整理Word」「右键转PDF」「右键生成信息图」「右键转Markdown」 「右键功能」「右键快捷操作」「右键批量处理」 本 Skill 帮助 macOS 用户批量安装 Finder 右键快捷工具， 一次安装多个功能，安装后在任意文件上右键即可一键处理。 负向触发：非 macOS 系统、Windows 右键、Linux 右键菜单，不使用此 Skill。
metadata:
  display_name: 右键神器
  version: '1.0'
---

# 右键神器（macOS Only）

## 快速决策清单

CRITICAL：遇到以下任一情况，**立即**按对应动作执行，不要询问用户额外信息：

1. 用户要求「安装右键工具」「批量安装」→ **展示工具列表，等待用户选择**
2. 用户指定了具体工具名称 → **检查 API Key 配置 → 运行 `scripts/install.py --tools <工具名>`**
3. 用户说「全部安装」→ **检查 API Key 配置 → 运行 `scripts/install.py --all`**
4. 用户说「卸载」「删除右键工具」→ **运行 `scripts/install.py --uninstall <工具名>`**
5. 用户说「有哪些工具」「列出工具」→ **运行 `scripts/install.py --list`**

IMPORTANT：本 Skill 仅支持 **macOS**。Windows/Linux 用户不使用此 Skill。

IMPORTANT：需要 API Key 的工具（生成信息图、MD整理），**安装前必须先配置**。若已配置则跳过询问，若未配置则通过对话引导用户输入。不得跳过配置直接安装。

---

## 这个 Skill 做什么

把你常用的文件处理功能，一键批量装到 macOS Finder 的右键菜单里。

安装后，在 Finder 中选中文件 → 右键 → 快速操作 → 选择功能，文件立即被处理，无需打开任何应用。

**当前可用工具（9个）：**

| # | 分类 | 工具名 | 支持文件 | 功能简述 |
|---|------|--------|---------|---------|
| 1 | 格式整理 | word整理 | .docx/.doc | 清洗修订痕迹、字体混乱、Markdown符号 |
| 2 | 文档转换 | Word表格横排 | .docx | 表格页面改为横向 |
| 3 | 格式整理 | Excel格式整理 | .xlsx/.xls | 统一格式、列宽、字体 |
| 4 | 文档转换 | docx2pdf | .docx/.doc | Word 转 PDF（LibreOffice） |
| 5 | 文档转换 | MD转Word | .md/.txt | Markdown 转 Word |
| 6 | 信息生成 | 生成信息图 | .docx/.md | 生成信息图（HTML+PDF） |
| 7 | 文档转换 | PDF转MD | .pdf | PDF 智能转 Markdown |
| 8 | 格式整理 | MD整理 | .md | Markdown 格式整理 |
| 9 | 信息查询 | 查询天眼查 | 文本（选中文字） | 选中文字跳转天眼查搜索 |

---

## API Key 配置（安装时对话引导）

以下工具需要 API Key 才能使用：

| 工具名 | 需要 API Key | 支持的供应商 |
|--------|-------------|-------------|
| 生成信息图 | DeepSeek 或 通义千问 | DeepSeek (platform.deepseek.com)、通义千问 (dashscope.aliyun.com) |
| MD整理 | DeepSeek 或 通义千问 | DeepSeek (platform.deepseek.com)、通义千问 (dashscope.aliyun.com) |

### 配置方式（对话式）

**不在运行时弹窗。** 所有 API Key 配置都在安装阶段通过 AI 与用户的对话完成：

1. AI 展示工具列表时，标注哪些需要 API Key
2. 用户选择包含 AI 工具后，AI 询问：「这些工具需要配置 API Key，你使用哪个供应商？（DeepSeek / 通义千问 / 两个都要）」
3. 用户回答后，AI 继续问：「请提供你的 API Key」
4. AI 调用 `configure.py` 写入配置，确认保存成功
5. 继续执行安装

**运行时未配置** → 静默跳过，不弹窗、不报错。用户后续可通过再次触发 Skill 补充配置。

---

## 使用场景

| 用户说 | 你该做什么 |
|---|---|
| 「帮我安装右键工具」「批量安装」 | 展示上方表格，让用户选择 |
| 「安装 word整理 和 docx2pdf」 | `python3 scripts/install.py --tools word整理 docx2pdf` |
| 「全部安装」「都装上」 | `python3 scripts/install.py --all` |
| 「卸载 word整理」 | `python3 scripts/install.py --uninstall word整理` |
| 「有哪些右键工具」 | `python3 scripts/install.py --list` |
| 「右键菜单没出现」「安装失败」 | 执行故障排查步骤 |

---

## 一、安装右键工具（对话式交互）

### 交互流程

**Step 1：展示工具列表并询问选择**

用户触发 Skill 时，展示工具表格，**同时标注哪些需要 API Key**：

```
📋 可用右键工具（9个）

┌───┬──────────┬──────────────┬─────────────────┬──────────┐
│ # │  分类    │    工具名    │    功能简述     │ 需要Key? │
├───┼──────────┼──────────────┼─────────────────┼──────────┤
│ 1 │ 格式整理 │ word整理     │ 清洗修订痕迹等  │    -     │
│ 2 │ 文档转换 │ Word表格横排 │ 表格页面横向    │    -     │
│ 3 │ 格式整理 │ Excel格式整理│ 统一格式列宽    │    -     │
│ 4 │ 文档转换 │ docx2pdf     │ Word转PDF       │    -     │
│ 5 │ 文档转换 │ MD转Word     │ Markdown转Word  │    -     │
│ 6 │ 信息生成 │ 生成信息图   │ 文本转信息图    │   ✅     │
│ 7 │ 文档转换 │ PDF转MD      │ PDF转Markdown   │    -     │
│ 8 │ 格式整理 │ MD整理       │ Markdown格式整理│   ✅     │
│ 9 │ 信息查询 │ 查询天眼查   │ 选中文字跳转搜索│    -     │
└───┴──────────┴──────────────┴─────────────────┴──────────┘

💡 需要 API Key 的工具（#6、#8）会在安装时引导你配置

你想安装哪些？可以按编号、名称、分类或说「全部安装」。
```

**Step 2：用户选择工具**

支持多种选择方式：
- 数字：`1、3、5` / `全部安装`
- 名称：`word整理、docx2pdf`
- 分类：`文档转换类的`
- 排除：`除了生成信息图都装`

**Step 3：API Key 配置对话（仅未配置时执行）**

如果用户选择了需要 API Key 的工具，**先检查是否已配置**。未配置才询问，已配置则跳过：

```bash
# 检查配置状态
python3 <skill_dir>/scripts/configure.py --status
```

**未配置时**，通过对话引导：

```
你选择了「生成信息图」和「MD整理」，这两个工具需要 API Key。

生成信息图支持：DeepSeek、通义千问（可配一个或两个）
MD整理支持：DeepSeek、通义千问（可配一个或两个）

请问：
1. 你使用哪个供应商？（DeepSeek / 通义千问 / 两个都要）
2. 对应的 API Key 是什么？
```

用户回答后，调用 configure.py 写入并验证：

```bash
# 配置生成信息图 - DeepSeek
python3 <skill_dir>/scripts/configure.py infographic --set-key deepseek_api_key=sk-xxx

# 配置生成信息图 - 通义千问
python3 <skill_dir>/scripts/configure.py infographic --set-key qwen_api_key=sk-yyy

# 配置 MD整理
python3 <skill_dir>/scripts/configure.py md-clean --set-key api_key=sk-yyy
# 或配置 DeepSeek
python3 <skill_dir>/scripts/configure.py md-clean --set-key deepseek_api_key=sk-xxx

# 验证配置已生效
python3 <skill_dir>/scripts/configure.py --status
```

**Step 4：执行安装**

```bash
python3 <skill_dir>/scripts/install.py --tools 工具1 工具2 ...
```

install.py 自动完成：
- 预检依赖（Python包、系统工具）
- 复制 Python 脚本到 `~/.rightclick-creator/tools/`
- `cp -R` 复制种子 workflow → `~/Library/Services/`
- `plistlib` 修改 COMMAND_STRING 和 Info.plist
- 同步时间戳保留元数据
- 刷新 pbs 缓存 + 重启 Finder
- 验证安装结果

**Step 5：告知验证方法**

```
安装完成！请验证：
1. 等待 Finder 重启（约 3-5 秒）
2. 选中对应类型文件 → 右键 → 快速操作
3. 检查菜单中是否出现已安装的工具
```

### 安装成功的标志

- `~/.rightclick-creator/tools/` 目录下有对应子目录和脚本
- `~/Library/Services/` 下有 `.workflow` 文件
- Finder 右键 → 快速操作 → 出现对应工具名

---

## 二、故障排查

### 右键菜单没出现

```bash
# 方法1：手动刷新
/System/Library/CoreServices/pbs -flush
killall Finder

# 方法2：重新安装
python3 <skill_dir>/scripts/install.py --tools <工具名>
```

### 处理失败 / 无输出

```bash
# 查看日志
cat ~/.rightclick-creator/logs/*.log
```

常见原因：
- `pandoc 未找到`：brew install pandoc
- `python-docx 未安装`：pip3 install python-docx lxml
- `LibreOffice 未找到`：brew install --cask libreoffice（docx2pdf 需要）

### 输出文件在 Word 中只读

```bash
xattr -d com.apple.quarantine /path/to/文件.docx
```

---

## 三、卸载

```bash
# 卸载单个工具
python3 <skill_dir>/scripts/install.py --uninstall 工具名

# 手动删除
rm -rf ~/Library/Services/工具名.workflow
/System/Library/CoreServices/pbs -flush
killall Finder
```

---

## 四、端到端示例

### 示例 1：不含 AI 工具（简单路径）

**用户输入：**「帮我安装 word整理 和 docx2pdf」

**你的执行流程：**

1. 确认 Skill 目录路径
2. 运行安装：
   ```bash
   python3 ~/.workbuddy/skills/右键神器/scripts/install.py \
     --tools word整理 docx2pdf
   ```
3. 等待安装完成，检查输出
4. 告知用户验证方法

### 示例 2：含 AI 工具（完整路径）

**用户输入：**「帮我安装 word整理 和 MD整理」

**你的执行流程：**

1. 确认 Skill 目录路径
2. **检查 MD整理 的 API Key 配置**：
   ```bash
   python3 ~/.workbuddy/skills/右键神器/scripts/configure.py --status
   ```
3. **未配置 → 对话询问**：
   > 「MD整理 需要 API Key，你使用哪个供应商？（DeepSeek / 通义千问）」
4. **写入配置**：
   ```bash
   python3 ~/.workbuddy/skills/右键神器/scripts/configure.py md-clean \
     --set-key api_key=sk-xxx
   ```
5. **验证配置**：
   ```bash
   python3 ~/.workbuddy/skills/右键神器/scripts/configure.py --status
   ```
6. **执行安装**：
   ```bash
   python3 ~/.workbuddy/skills/右键神器/scripts/install.py \
     --tools word整理 MD整理
   ```
7. 等待安装完成，告知验证方法

**禁止做的：**不要从零创建 workflow；不要用 sed 修改 plist；不要跳过 pbs 刷新；不要跳过 API Key 配置直接安装 AI 工具。

---

## 五、目录结构

```
右键神器/
├── SKILL.md                    ← 本文件
├── README.md                   ← 项目说明
├── scripts/
│   ├── install.py              ← 多工具安装器（核心）
│   ├── extract_catalog.py      ← 一次性：从现有 workflow 提取 catalog
│   └── tools/                  ← 工具专属 Python 脚本
│       ├── docx_format_cleaner/
│       ├── word_table_landscape/
│       ├── excel_format/
│       ├── md2docx_plain/
│       ├── infographic/
│       ├── pdf2md/
│       ├── md_cleaner/
│       └── tianyancha/
└── references/
    └── tools_catalog.json      ← 工具配置目录
```

---

## 六、扩展新工具

如需添加新的右键工具：

1. 在 `~/Library/Services/` 创建并验证 workflow（通过 Automator GUI）
2. 运行 `python3 scripts/extract_catalog.py` 提取脚本
3. 手动补充 `tools_catalog.json` 中的 id、category、description、dependencies、path_mappings
4. 将 Python 脚本复制到 `scripts/tools/{新工具}/`
5. 重新安装即可
