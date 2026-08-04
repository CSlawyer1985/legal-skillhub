# pre-motion

针对英格兰和威尔士民事诉讼的对抗式事前验尸（premortem）。构建案件的最强版本，然后从四个角度攻击它——程序、实体、证据、策略——在对方律师之前找出它会在哪里输。

适用于：提起诉讼前进行压力测试的事务律师、签署前的内部法律顾问、评估和解价值的调解人，以及为案件定价的诉讼资助方。

## 安装

属于 [claude-for-uk-legal](https://github.com/b1rdmania/claude-for-uk-legal) 插件套件的一部分：

```bash
/plugin marketplace add https://github.com/b1rdmania/claude-for-uk-legal
/plugin install uk-litigation-legal@claude-for-uk-legal
```

或直接安装单个技能：

```bash
cp -r pre-motion ~/.claude/skills/pre-motion
```

## 用法

```
/pre-motion
/pre-motion --depth=fast
/pre-motion --depth=thorough
```

对包含事实、证据引用、索赔项以及您所看到的最强案件版本的案件运行它。它返回一份排序的压力测试简报。

## 它做什么

- 构建乐观基线——证据支持的最强版本。
- 检查证据：文件缺口、跨文件矛盾、时间线漏洞，每一项都标记严重程度。
- 运行四次对抗式遍历（在支持的情况下使用并行子代理，否则顺序运行），每次告知案件已败诉并要求回溯原因——每个失败类别一次。
- 综合成简报：排序的失败场景（附严重程度、可能性和缓解措施）；证据不一致；盲点；和解姿态影响；以及一句结论。
- 内联标记每个不确定点——`[CITE NEEDED]`、`[SME VERIFY]`、`[EVIDENCE FLAG]`——使任何内容都不会读起来像已定论。

## 它不做什么

- 预测结果——它呈现失败模式，而非结果。
- 决定是否承接、和解或撤诉——那些是律师的决定。
- 替代正式的律师意见。它是该对话的结构化提示词，而非替代品。
- 涵盖非英国程序（美国联邦、苏格兰、北爱尔兰）。
- 对照实时来源核验判例法——在依赖其引用的任何权威依据之前自行核查。

## 要求

- Claude Code 或 Claude Cowork。无需 MCP 连接器。
- 一个可运行的材料（事实和证据引用）。在宿主工作区中，CPR 31.22 / 特权关卡在上游强制执行；仅对您被允许使用的材料独立运行。

## 许可证

Apache-2.0。
