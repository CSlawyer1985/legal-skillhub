---
name: mac-clipboard-to-md-main
description: 仅限macOS使用。剪贴板快速保存到 Markdown 笔记。 本 Skill为一次性安装skill，使用 AskUserQuestion 工具以弹窗形式交互， 逐步引导用户完成 Automator Service（菜单栏服务/快捷键）的安装和配置。本skill触发词包括但不限于：剪贴板工具、剪贴板快捷键、快速记录工具、Clipboard to Markdown、保存剪贴板、brain dump、work record、AppleScript 快捷键、设置剪贴板快捷键、安装快捷记录等。
metadata:
  display_name: 剪贴板转笔记
---

# 剪贴板转笔记（仅限macOS）— 交互式安装向导

## 核心原则

- **逐步引导**：每次只问一个问题，等用户回答后再进入下一步
- **用 AskUserQuestion 工具代替纯文本提问**：所有需要用户选择的步骤，都用 AskUserQuestion 弹窗呈现选项
- **路径参考 `<skill_dir>`**：所有文件引用都以 SKILL.md 所在目录为根
- **纯文本用于介绍和说明**：仅信息展示环节用纯文本，需要用户决策时切换为 AskUserQuestion

---

## 交互流程

### Phase 1：macOS 检测（AskUserQuestion）

一上来先确认系统。**不要默认假设用户在 macOS 上。**

```json
{
  "question": "你用的是 macOS 吗？",
  "header": "系统检测",
  "options": [
    {
      "label": "是，macOS",
      "description": "继续安装流程"
    },
    {
      "label": "否，Windows/Linux",
      "description": "该工具仅支持 macOS"
    }
  ]
}
```

**选「否」→ 回复：** 这个工具只支持 macOS，Automator 是系统组件没办法在其他系统上用。需要其他帮助可以找我。

**选「是」→ 进入 Phase 2。**

---

### Phase 2：介绍（纯文本）

```
这个工具可以把剪贴板内容一键保存到 Markdown 笔记。

有两个脚本可选：
- work-record — 静默模式，复制 → 快捷键 → 自动追加到 Work record.md
- brain-dump — 交互模式，复制 → 快捷键 → 弹窗让你输入文件名/标签/描述
```

然后直接进入 Phase 3。

- 用户已装过或了解 → 跳过介绍，直接进入 Phase 3（选择工具）

---

### Phase 3：选择工具（AskUserQuestion 单选框）

**工具：** `AskUserQuestion`
- **multiSelect：** `true`（可以选一个，也可以两个都选）
- **header：** `"选择工具"`

```json
{
  "question": "你想安装哪个工具？",
  "header": "选择工具",
  "multiSelect": true,
  "options": [
    {
      "label": "work-record",
      "description": "静默追加到 Work record.md，适合随手记"
    },
    {
      "label": "brain-dump",
      "description": "带对话框，可自定义文件名/标签，适合分类归档"
    }
  ]
}
```

**结果处理：**
- 选 `work-record` → 记录 `tools = ["work-record"]`
- 选 `brain-dump` → 记录 `tools = ["brain-dump"]`
- 两个都选 → 记录 `tools = ["work-record", "brain-dump"]`

---

### Phase 4：询问保存路径（AskUserQuestion + 默认选项）

**如果是 work-record：**

```json
{
  "question": "work-record 会把剪贴板内容追加到这个文件。你想用什么路径？",
  "header": "保存路径",
  "options": [
    {
      "label": "~/Documents/Work record.md",
      "description": "默认路径，直接放文档目录"
    },
    {
      "label": "设在 Obsidian 库里",
      "description": "放入你的 Obsidian 学习库"
    }
  ]
}
```

- 选 `默认路径` → `path = expanduser("~/Documents/Work record.md")`
- 选 `Obsidian 库` → 用当前工作目录作为 vault 根路径，构造推荐路径

```json
{
  "question": "请输入 work-record 要追加到的完整文件路径：",
  "header": "自定义路径",
  "options": [
    {
      "label": "Vault 根目录",
      "description": "放在 Obsidian vault 根目录"
    }
  ]
}
```

**注意：** 选「Vault 根目录」→ `path = {当前 vault 根路径}/Work record.md`。`{当前 vault 根路径}` 是动态占位符，AI 执行时应从当前工作目录自动推导，不要硬编码特定用户的路径。如果用户想放在子目录，可以让其选择「Other」自行输入。

**如果没装 work-record，跳过此步。**

---

**如果是 brain-dump：**

```json
{
  "question": "brain-dump 会在这个文件夹里创建笔记文件。你想用什么路径？",
  "header": "保存文件夹",
  "options": [
    {
      "label": "~/Documents/brain dump/",
      "description": "默认路径，直接放文档目录"
    },
    {
      "label": "设在 Obsidian 库里",
      "description": "放入你的 Obsidian 学习库"
    }
  ]
}
```

- 选 `默认路径` → `path = expanduser("~/Documents/brain dump/")`
- 选 `Obsidian 库` → 用当前工作目录作为 vault 根路径，构造推荐路径（选项同上，只是文件路径改为文件夹路径）

**如果没装 brain-dump，跳过此步。**

---

### Phase 5：选择安装方式（纯文本 + AskUserQuestion）

确认路径后，问用户想自动还是手动：

```json
{
  "question": "安装方式选哪个？",
  "header": "安装方式",
  "options": [
    {
      "label": "自动安装（推荐）",
      "description": "AI 用 install.py 自动创建 workflow，无需手动操作"
    },
    {
      "label": "手动安装",
      "description": "告诉你改哪一行，自己开 Automator 粘贴"
    }
  ]
}
```

**选「自动安装」→ 直接进入 Phase 6a（自动流程）**
**选「手动安装」→ 进入 Phase 6b（手动流程）**

---

### Phase 6a：自动安装（运行 install.py）

```bash
# 构造路径参数
# 如果是 work-record，路径示例：
WORK_PATH="~/Documents/Work record.md"
# 如果是 brain-dump，路径示例：
BRAIN_PATH="~/Documents/brain dump/"

# 运行安装（单个工具）
python3 <skill_dir>/scripts/install.py --tool work-record --path "$WORK_PATH"

# 或两个工具都装
python3 <skill_dir>/scripts/install.py --tool all --work-record-path "$WORK_PATH" --brain-dump-path "$BRAIN_PATH"
```

install.py 会：
1. 读取 Applescript 模板 → 替换占位路径为用户路径
2. 用 `plistlib` 构造 `.workflow` 包（Info.plist + document.wflow）
3. 复制到 `~/Library/Services/`
4. 刷新 pbs 缓存 + 重启 Finder（右键菜单立即生效）

**安装完成后，说明快捷键是必需的：**

```
✅ workflow 已装好，但无输入的 Service 不会出现在右键菜单里。
你必须设置快捷键才能使用：

1. 「系统设置」→「键盘」→「键盘快捷键」
2. 左边选「服务」，右边「通用」里找到「保存到 Work Record」
3. 点击右侧空白区域按下快捷键

推荐：Ctrl+Cmd+Shift+V

设好之后按快捷键就能用，不需要打开任何应用。
```

然后进入 Phase 7（验证）。

---

### Phase 6b：手动安装（纯文本引导）

用户需要亲自在 macOS GUI 中操作。**不要写中间文件到任何位置。**

读取模板，展示需要修改的那一行：

```bash
# 读模板，定位具体行号（work-record 第 26 行）
sed -n '24,28p' "<skill_dir>/work-record.applescript"
```

然后直接告诉用户改哪里：

```
work-record 需要改第 26 行：

  原来：set filePath to "/Users/你的用户名/Documents/Work record.md"
  改成：set filePath to "你选的路径"

然后打开这个文件（项目中 <skill_dir>/work-record.applescript），
改好之后全选复制。

接下来创建 macOS 快速操作：
1. 打开「自动操作」（Spotlight 搜 Automator）
2. 文件 → 新建 → 选择「快速操作」
3. 顶部设置：工作流程收到 → 「没有输入」，位于 → 「任何应用程序」
4. 左侧找到「运行 AppleScript」→ 拖到右侧
5. 删掉默认代码，粘贴你刚才复制的内容
6. 按 Cmd+S 保存

work-record → 保存为「保存到 Work Record」
brain-dump → 保存为「Brain Dump」

搞定了告诉我。
```

用户回复「好了」后进入 Phase 6c。

---

### Phase 6c：设置快捷键（手动安装流程 - 纯文本引导）

同样需要用户在系统设置中操作：

```
最后一步，绑定快捷键：

1. 打开「系统设置」→「键盘」→「键盘快捷键」
2. 左边选「服务」，右边找到「通用」
3. 找到你刚保存的快速操作名称
4. 点击右侧空白区域，按下快捷键

推荐：work-record → Ctrl+Cmd+Shift+V
       brain-dump → Ctrl+Opt+Cmd+V
```

设置好了告诉我，进入验证。

---

### Phase 7：验证（自动/手动共用）

```
验证一下：
1. 复制一段文字
2. 按快捷键
3. 打开笔记文件检查内容是否写入

试试看。
```

---

## 交互对照表

| 阶段 | 交互方式 | 原因 |
|------|---------|------|
| Phase 1 macOS检测 | AskUserQuestion | 前置过滤，非macOS直接结束 |
| Phase 2 介绍 | 纯文本 | 信息展示，无需决策 |
| Phase 3 选工具 | AskUserQuestion + 多选 | 用户需选择，选项有限 |
| Phase 4 问路径 | AskUserQuestion + 预设选项 | 提供常用选项 + Other 输入 |
| Phase 5 选安装方式 | AskUserQuestion | 自动 vs 手动 |
| Phase 6a 自动安装 | Bash 运行 install.py | AI 执行，自动创建 workflow |
| Phase 6b 手动安装 | 纯文本 + Bash | GUI 操作，AI 无法代劳 |
| Phase 6c 设快捷键（手动） | 纯文本 | GUI 操作，AI 无法代劳 |
| Phase 7 验证 | 纯文本 | 用户自行测试 |

---

## 目录结构

```
<skill_dir>/
├── SKILL.md                   ← 本文件
├── scripts/
│   └── install.py             ← 自动安装器（plistlib 构造 workflow）
├── README.md / README.zh.md
├── work-record.applescript    ← work-record 模板
└── brain-dump.applescript     ← brain-dump 模板
```
