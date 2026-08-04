# Self-Improve 技能

一个自我改进的技能系统，分析您的工作会话并为其他技能提出改进建议。

## 命令

| 命令 | 描述 |
|---------|-------------|
| `self-improve` | 分析当前会话并提出技能改进建议 |
| `self-improve [skill-name]` | 针对特定技能 |
| `self-improve on` | 启用自动模式 |
| `self-improve off` | 禁用自动模式 |
| `self-improve status` | 检查自动模式状态 |
| `self-improve [skill-name] history` | 查看修改历史 |

## 手动用法

使用技能后，运行 `self-improve` 以捕获改进：

```
> self-improve my-skill

--- Self-Improve: my-skill ---

Proposed additions:

1. "Always check for X before proceeding"
   Source: User correction at 14:32

2. "Use table format for Y"
   Source: User accepted format at 14:45

---

Apply these changes? [Y/n]
```

## 手动与自动模式

### 手动模式（默认）

每当您想从会话中捕获改进时运行 `self-improve`。没有任何内容会自动发生。

### 自动模式

启用后，技能会在会话结束时自动分析，并提出改进建议供您批准。

**启用方法：**

1. 运行 `self-improve on`

2. 将钩子添加到您的本地 Claude Code 设置（`.claude/settings.local.json`）：

```json
{
  "hooks": {
    "stop": [
      {
        "type": "command",
        "command": "./skills/skill-optimizer-en-malik-taiar/scripts/self-improve-hook.sh"
      }
    ]
  }
}
```

3. 在每个会话结束时，您会看到拟议的改进并被要求批准

**禁用方法：** 运行 `self-improve off`

## 工作原理

### 信号检测

技能扫描对话以寻找：
- **更正**：“No”（不）、“That's wrong”（那是错的）、“Always do X”（总是做 X）
- **成功**：“Perfect”（完美）、“Exactly”（正是如此）、被接受的输出
- **边缘情况**：需要的变通方案、未处理的场景

### 质量标准

每条更正都对照 4 项标准评估，以确保高质量的技能改进：

1. **完整**：包含应用指令所需的全部信息
2. **精确**：无模糊或主观术语
3. **原子性**：每条指令一个检查（不捆绑）
4. **稳定**：无无具体日期的时效依赖引用

### 分级

| 满足的标准 | 行动 |
|--------------|--------|
| 全部 4 项标准 | 直接添加到技能 |
| 少于 4 项 | 请求澄清，但若用户坚持仍添加 |

### 质量标准为何重要

没有严格的标准，技能会积累诸如“更彻底一些”或“使用标准格式”之类的模糊指令，这些指令无法被一致遵循。

质量标准确保添加到技能的每条指令都是：
- 无需猜测即可执行的
- 任何阅读技能的人都能理解
- 跨会话一致适用的

## 历史

所有修改都记录在每个技能文件夹内的 `CHANGELOG.md` 中。使用 `self-improve [skill-name] history` 查看。

历史以自然语言撰写（无需 git 知识）。您可以通过历史命令回退到任何先前版本。
