# deli-cli 通用前置

适用于 `litigation-intake-assessment@1.0.0`。命中本 skill 后，凡需要调用法规检索、案例检索、类案匹配、裁判倾向核验、周期/成本辅助数据或后端能力时，先执行本文档步骤。

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
- 如果鉴权未完成，不得继续执行法规、案例或后端命令；先提示用户完成 CLI 初始化。

## 2. 发现当前 skill 命令

完成前置检查后，用当前 skill scope 发现命令：

```bash
npx @delilegal/deli-cli@latest cmds litigation-intake-assessment@1.0.0
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

- 每次检索或后端调用都要围绕一个明确争议焦点、请求权基础、抗辩事由、证据规则或裁判倾向。
- 无结果、结果明显失焦或命令不可用时，先说明情况并给出建议检索式或需要补充的案件事实，不自动连续换词重试。
- 法条、案例、案号、法院、裁判日期、裁判观点、收费标准和周期依据必须来自 CLI 返回结果、用户材料或可核验材料，不得编造。
- 检索受限时可以继续做条件性评估，但必须降低确信度，并在报告中标注“检索受限”或“结论待核”。
