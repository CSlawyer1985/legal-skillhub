# deli-cli 通用前置

适用于 `private-lending-interest-calculator@1.0.0`。

## 1. 检查 CLI 状态

命中本 skill 后，先执行：

```bash
npx @delilegal/deli-cli@latest check
```

如提示未配置 API Key，引导用户前往以下地址创建：

```text
https://open.delilegal.com/personal/keys
```

初始化命令：

```bash
npx @delilegal/deli-cli@latest init --apikey "<你的 API Key>"
```


CLI 配置保存位置：

```text
~/.deli/cli/config.json
```

不得读取、创建或提示用户配置 skill 目录下的旧 `config.json`。

## 2. 发现当前命令

使用当前 skill scope 发现命令：

```bash
npx @delilegal/deli-cli@latest cmds private-lending-interest-calculator@1.0.0
```

必须解析返回内容中的：

- `RUN id`
- `usage`
- `commands`
- `params`
- `description`

后续调用必须使用当次返回的 `run_...` 入口、命令名和参数形态。不要假设固定命令、固定参数或固定输出格式一定存在。

## 无可用命令时的执行边界

如 `cmds` 返回为空、未提供可执行命令、未暴露当前任务需要的工具，或当前 skill scope 没有后端 MCP/工具服务，不视为 skill 失败。此时不再尝试通过 CLI 调用 MCP；Agent 应直接依据本 `SKILL.md`、本地 `references/`、`assets/` 和用户材料完成本 skill 的主体工作。

在无可用命令时，外部法规/案例/地方口径/动态数据/后端计算等无法由 CLI 核验的内容必须标注“检索受限”“命令不可用”或“需人工复核”；不得编造 CLI 未返回的依据、案例、数值或结论。

## 3. 计算类限制

- 只调用民间借贷利息计算、参数校验、LPR 参数获取、结果生成等计算相关命令。
- 不调用法规检索命令。
- 不调用案例检索命令。
- 稳定规则、LPR 参数口径和法条索引以本 skill 的 references 为准。
