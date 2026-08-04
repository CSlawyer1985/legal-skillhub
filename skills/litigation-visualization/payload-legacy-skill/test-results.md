# V3 测试结果

## 独立盲测

- 日期：2026-07-21。
- 隔离方式：独立测试席只读取 `SKILL.md`、`references/`、`assets/`、两个验证脚本和无预期答案的盲测输入；未读取 `test-prompts.json`、本文件、manifest、候选提取、治理记录或旧盲测报告。
- 用例：14 条；5 条正向触发、3 条不触发、6 条边界/安全场景。
- 路由：11 条触发（其中 6 条触发后必须限制、HOLD、降级或拒绝原要求），3 条不触发。
- 行为符合预期：14/14，100/100。
- 六类硬门：隐私、旧法、OCR、视觉误导、行为—背景—意图推断、现图完整性审查，6/6 PASS。

盲测证明路由与说明层在本测试集上工作，不证明真实案件图、授权、法源、OCR、裁判效力或交付内容在实体上正确。

## 结构、规格与输出回归

- Skill Creator frontmatter 校验：PASS。
- 包体预检：PASS；20 个受控文本文件，无 PDF、来源书原图、整书 OCR、软链接、禁止二进制或缓存文件。
- 六个原创模板均保留 `TODO_DO_NOT_DELIVER` 防误交付标记；该标记在模板中是必需门控，任何成品 artifact 残留该标记都会被拒绝。
- `scripts/validate_spec.py` 正例：PASS。
- 四个 invalid spec fixture：全部按预期失败，覆盖普通规格错误、法律门、隐私门和外部处理/交付门。
- `scripts/validate_output.py` 正例：PASS；invalid output fixture 正确检出哈希、字段、路径、占位符、ID 记账及 locator 目标错误。
- V3 定向红队：18/18 PASS；覆盖 11 字段来源账本、来源类型、中文法律触发、逐条法源覆盖、人工放行字段、HOLD 恢复控制、空间 sidecar 与真实采集日期、裁判处理交叉约束、虚假 locator、发布字段白名单、omitted ID 残留及压缩 Office 内容扫描。
- 意图或因果假说使用 `record_type=inference`，不使用废弃字段名 `type=inference`。

## 独立复审

- 首轮复审发现的 4 个 P1 与裁判处理缺口已逐项修复并由定向回归关闭。
- 冻结 V3 复审随后发现 `spatial_review.collected_at=null` 可通过，以及元素最小字段未完全显式强制；两项均已修复并加入回归。
- 聚焦独立复核：`PASS_FOR_LOCAL_CANDIDATE_PACKAGING`，P0/P1/P2 未关闭项均为 0，旧 HOLD 已关闭；该结论仍不批准正式安装、生产晋升、真实案件交付或外部发布。

本测试只支持本地候选构建的结构与行为证据。它不表示正式安装、默认替换、真实案件使用、法院/客户交付、生产晋升或外部发布获准。
