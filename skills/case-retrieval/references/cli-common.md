# deli-cli 通用前置

适用于 `case-retrieval@1.0.0`。命中本 skill 后，凡需要执行案例检索、类案匹配、分页查看更多结果、按时间排序或调用后端能力时，先执行本文档步骤。

## 1. 检查 CLI 与鉴权

先运行：

```bash
npx @delilegal/deli-cli@latest check
```

如提示未配置 API Key，引导用户前往以下地址创建：

```text
https://open.delilegal.com/personal/keys
```

然后写入本机 CLI 配置：

```bash
npx @delilegal/deli-cli@latest init --apikey "你的 API Key"
```

CLI 配置保存位置：

```text
~/.deli/cli/config.json
```

注意：

- 不读取、不创建、不提示用户配置 skill 目录下的旧 `config.json`。
- 如果鉴权未完成，不得继续执行案例检索；先提示用户完成 CLI 初始化。

## 2. 发现当前 skill 命令

完成前置检查后，用当前 skill scope 发现命令：

```bash
npx @delilegal/deli-cli@latest cmds case-retrieval@1.0.0
```

必须解析本次 `cmds` 输出中的以下字段：

- `RUN id`
- `usage`
- `commands`
- `params`
- `description`

后续调用必须使用当次返回的 `run_...` 入口、命令名和参数形态，不得假设固定命令或固定参数一定存在。

## 无可用命令时的执行边界

如 `cmds` 返回为空、未提供可执行命令、未暴露当前任务需要的工具，或当前 skill scope 没有后端 MCP/工具服务，不视为 skill 失败。此时不再尝试通过 CLI 调用 MCP；Agent 应直接依据本 `SKILL.md`、本地 `references/`、`assets/` 和用户材料完成本 skill 的主体工作。

在无可用命令时，外部法规/案例/地方口径/动态数据/后端计算等无法由 CLI 核验的内容必须标注“检索受限”“命令不可用”或“需人工复核”；不得编造 CLI 未返回的依据、案例、数值或结论。

## 3. 调用约束

- 单个用户问题默认只形成一个高质量检索式并调用一次。
- 用户输入包含事实经过、诉请抗辩、争议焦点或材料摘要时，若当前命令支持长文本/相似案例参数，首次调用必须使用该类参数，不得先拆成关键词检索。
- 长文本/相似案例检索返回有效结果后即停止检索，不追加关键词拆分或同义词改写。
- 只有命令不支持长文本/相似案例参数，或用户只给出短检索标签时，才使用关键词检索。
- 无结果、结果明显失焦或命令不可用时，先说明情况并给出建议检索式，不自动连续换词重试。
- 涉及案号、法院、裁判日期、裁判结果、案例层级或裁判观点时，只能使用 CLI 返回内容或用户提供材料，不得编造。
- 用户明确要求“下一页”“更多结果”时，先说明会产生新的 CLI 调用，再按 `cmds` 当前返回的分页参数形态执行。
