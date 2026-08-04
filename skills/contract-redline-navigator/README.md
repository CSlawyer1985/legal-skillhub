# Contract Redline Navigator

Slug: `contract-redline-navigator`

## 功能定位

Compare draft agreements, highlight risky clause changes, and generate a negotiation checklist with plain-language explanations.

## 适用场景

- 当用户需要：合同对比
- 当用户手头已有原始材料，需要快速整理成可执行输出
- 当用户希望先预览方案、再决定是否落盘或批量处理

## 安装要求

- OpenClaw / AgentSkills 兼容目录结构
- `python3` 可执行文件在 PATH 中可用
- 无远程安装脚本、无隐藏联网依赖、无未声明凭据要求

## 目录结构

- `SKILL.md`：触发描述、工作流、输出契约
- `scripts/clause_diff.py`：本地辅助脚本
- `resources/risk_clauses.md`：被 SKILL/README 引用的资源文件
- `examples/example-prompt.md`：触发与输入示例
- `tests/smoke-test.md`：最小冒烟测试
- `SELF_CHECK.md`：规范与安全自检
- `CHANGELOG.md`：变更记录

## 触发示例

- `合同对比`
- `redline this contract`
- `比较两个协议版本`
- `找风险条款`
- `做谈判清单`

## 建议输入

- old draft and new draft
- contract type
- risk tolerance
- counterparty type
- must-have fallback positions

## 预期输出

- risk-change summary
- negotiation checklist
- clause-by-clause diff
- plain-language brief

## 辅助脚本

脚本：`scripts/clause_diff.py`

建议先运行帮助信息确认参数：

```bash
python3 scripts/clause_diff.py --help
```

该脚本设计原则：

- 本地执行，便于审计与回滚
- 输入输出路径显式传入
- 不使用 `curl|bash`、远程直灌、base64 混淆执行
- 仅处理用户明确提供的文件或目录

## 输入输出示例

输入示例见：`examples/example-prompt.md`

输出示例建议至少包含：

- 结构化主结果
- 未决问题 / 风险项
- 可交付给他人的摘要或清单

## 常见问题

### 1. 这个 skill 会直接改我的文件吗？

默认不应直接进行破坏性批量操作；应优先生成预览、清单或草案，只有在用户明确要求时才建议执行进一步动作。

### 2. 这个 skill 需要联网吗？

当前目录内未声明联网依赖，也没有内置远程下载步骤。是否联网应由具体会话任务决定，而不是由 skill 包本身强制触发。

### 3. 资源文件的作用是什么？

`resources/risk_clauses.md` 为脚本或说明提供模板、规则、清单或模式参考，便于输出格式统一、可复用、可审计。

## 风险提示

- 对用户提供的数据、文本、截图或本地文件进行整理时，应先确认范围与目标。
- 涉及重命名、移动、合并、覆盖、生成正式对外内容时，应先给预览版本。
- 对不确定字段使用“待确认”标记，不应编造事实。

## 安全审计结论

- 依赖边界：仅声明 `python3`
- 凭据边界：未声明环境变量依赖
- 执行边界：本地脚本、本地资源、显式输入
- 高风险模式检查：未引入 `curl|bash`、远程管道执行、混淆载荷或私有 API 绑定
