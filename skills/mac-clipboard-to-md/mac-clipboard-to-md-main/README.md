---
categories: "[[Projects]]"
---
# Mac Clipboard to Markdown

Quickly save macOS clipboard content to Markdown notes via keyboard shortcut.
一键将 Mac 剪贴板内容保存到 Markdown 笔记。

---

## 简介

两款 macOS Automator 工具，使用 AppleScript 和快捷键将剪贴板内容保存至 Markdown 笔记。

### work-record.applescript

静默模式。复制文本 → 按快捷键 → 自动追加到 `Work record.md`，带时间戳倒序排列。

- 动态定位 YAML frontmatter，不受行数变化影响
- 文件不存在时自动创建模板
- 无 frontmatter 的文件也兼容

**适用场景**：随手记录零散信息、临时笔记。

### brain-dump.applescript

交互模式。按快捷键后依次弹窗输入文件名、标签、描述，保存到 `brain dump/` 文件夹。

- 自动生成 YAML frontmatter
- 支持多标签
- 可选描述字段

**适用场景**：需要分类归档的内容。

---

## Overview

Two macOS Automator tools that save clipboard content to Markdown notes via keyboard shortcuts.

### work-record.applescript

Silent mode. Copy text → press shortcut → content appended to `Work record.md` with timestamp, newest on top.

- Dynamic YAML frontmatter detection
- Auto-creates file with template if missing
- Graceful fallback for files without frontmatter

**Use case**: Quick capture of snippets and temporary notes.

### brain-dump.applescript

Interactive mode. Prompts for filename, tags, and description before saving to `brain dump/` folder.

- Auto-generated YAML frontmatter
- Multiple tags support
- Optional description

**Use case**: Categorized notes with metadata.

---

## 安装方法

### 方式一：自动安装（推荐）

终端直接运行（问答引导）：
```bash
python3 scripts/install.py
```

或带参数指定工具和路径（静默安装）：
```bash
# 单个工具
python3 scripts/install.py --tool work-record --path "~/Documents/Work record.md"
# 两个一起装
python3 scripts/install.py --tool all --work-record-path "~/Documents/Work record.md" --brain-dump-path "~/Documents/brain dump/"
```

### 方式二：手动安装

1. 修改脚本中的占位路径为你的实际路径
2. 打开「自动操作」→ 新建「快速操作」（无输入，任何应用）
3. 拖入「运行 AppleScript」，粘贴对应脚本内容
4. 保存后去「系统设置 → 键盘 → 键盘快捷键 → 服务」绑定快捷键

### 方式三：AI 辅助

使用 Claude Code 触发 skill `/mac-clipboard-to-md`，按问答引导安装。

---

## Installation

### Method 1: Automated (Recommended)

Run interactively:
```bash
python3 scripts/install.py
```

Or silent mode with arguments:
```bash
# Single tool
python3 scripts/install.py --tool work-record --path "~/Documents/Work record.md"
# Both tools
python3 scripts/install.py --tool all --work-record-path "~/Documents/Work record.md" --brain-dump-path "~/Documents/brain dump/"
```

### Method 2: Manual Setup

1. Edit placeholder paths in the `.applescript` files
2. Open Automator → New → Quick Action (no input, any application)
3. Drag "Run AppleScript", paste script content, save
4. Bind shortcut in System Settings → Keyboard → Keyboard Shortcuts → Services

### Method 3: AI-Assisted

Run with Claude Code: `/mac-clipboard-to-md`

---

## 目录结构 | Structure

```
mac-clipboard-to-md/
├── SKILL.md                   ← AI 安装向导（Claude Code）
├── scripts/
│   └── install.py             ← 自动安装器（参数/交互双模式）
├── work-record.applescript    ← 静默模式脚本
├── brain-dump.applescript     ← 交互模式脚本
├── CHANGELOG.md               ← 版本历史
├── README.md                  ← 本文件
└── LICENSE
```

---

## License

MIT License
