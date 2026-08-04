# 常见问题解答（FAQ）

> 本文件汇总 baozheng-skills 技能使用中的高频问题，供用户和开发者快速排查。

## 一、技能功能

### Q1: 这个技能能做什么？

baozheng-skills 是一站式法律服务平台，提供四类核心能力：

| 模块 | 能力 | 输出 |
|:---|:---|:---|
| 模块A | 法律咨询（4步深度分析） | 法律分析报告 |
| 模块B | 要素式/通用起诉状起草 | 起诉状 .docx |
| 模块C | 法条分析 + 法规检索 | 6维度分析 / 6份交付物 |
| 模块D | 刑事专项材料辅助 | 5类刑事文书草稿 |

不处理：非中国法律、执行具体诉讼代理。

### Q2: 支持哪些法律领域？

覆盖 **22 类法律领域**（详见 `references/shared-category-coverage.md`）：

婚姻家庭、刑事案件、劳动纠纷、合同纠纷、公司企业、债权债务、房产纠纷、交通事故、继承、征地拆迁、建筑工程、医疗纠纷、损害赔偿、行政纠纷、环境保护、知识产权、保险纠纷、证券投资、互联网纠纷、人格尊严、涉外纠纷、消费权益。

### Q3: 这个技能能帮我打官司吗？

不能。本技能提供的是**法律咨询意见**和**起诉状起草工具**，不代理案件。AI 不能代替律师出庭。具体案件代理需要委托执业律师。

### Q4: 这个技能的法律依据有多新？

严格依据**中华人民共和国现行有效法律**，法律修订后持续同步更新。本技能内置 `scripts/flk_npc_client.py`（封装全国人大官方 flk.npc.gov.cn 的 `/law-search/` API），在回答法律问题时优先调用官方 API 获取实时法条数据；API 不可用时降级到 AI 训练知识库，确保法条引用的准确性和时效性。具体适用请以官方最新文本及司法实践为准。

## 二、起诉状相关

### Q5: 生成的起诉状可以直接提交法院吗？

要素式起诉状填好后**可以作为草稿提交**有管辖权的法院立案。**提交前建议由执业律师审核一遍**，确保诉讼请求、事实理由、证据清单完整无遗漏。通用起诉状需手动完善事实和理由内容。

### Q6: 34 个专属模板指的是什么？

本技能针对 34 类高频案由分别提供了要素式专属模板（case-01 至 case-34，其中 3 类为行政起诉状：case-13/20/32，其余为民事起诉状），涵盖民间借贷、离婚、买卖、金融借款、物业服务、信用卡、交通事故、劳动争议、融资租赁、保证保险、证券虚假陈述、继承、行政诉讼、医疗纠纷、商品房买卖、股权转让、建设工程、知识产权、网络侵权、征地拆迁、环境保护、保险理赔、基金投资、私募基金、信托、房屋租赁、人身损害、专利、商业秘密、公司解散、政府信息、涉外服务、消费权益等。非上述 34 类的案由使用通用模板（template-00）。

### Q7: 要素式起诉状和普通起诉状有什么区别？

| 对比维度 | 要素式起诉状 | 通用民事起诉状 |
|:---|:---|:---|
| 格式 | 表格化，逐项勾选填写 | 段落式，自由行文 |
| 结构 | 固定模块（说明/当事人/请求/事实/证据） | 传统结构（当事人→请求→事实→证据→法院） |
| 适合场景 | 标准案由，批量处理 | 任意民事案由，灵活行文 |
| 模板文件 | 对应案由模板文件 | `assets/template-00-general-civil.md` |

### Q8: 为什么生成的起诉状有些字段是空的？

追问时用户未提供相关信息，或该信息在特定案由中为可选项。建议尽量补充完整，信息越全越有利于立案。

### Q9: 起诉状里的事实和理由怎么写？

遵循"一事一理"原则：

- **事实**按时间线叙述：什么时间、什么人、做了什么事、产生了什么后果
- **理由**引用法律依据：结合事实指出对方违反了哪条法律、应承担什么责任
- 语言简洁、条理清晰、重点突出

### Q10: 没有证据也能起诉吗？

可以起诉，但胜诉可能性较低。**"谁主张谁举证"**是基本原则。建议在起诉前尽量收集相关证据。如果证据被对方掌握，可申请法院责令对方提交。

### Q11: 起诉有时间限制吗？

有。**诉讼时效**一般为**3年**（民法典第188条），自知道或应当知道权利受损害之日起计算。劳动争议仲裁时效为**1年**。超过时效可能丧失胜诉权。具体请以法律规定为准。完整时效速查参见 `references/shared-limitation-periods.md`。

### Q12: 起诉需要准备什么材料？

一般需要：起诉状 + 证据材料 + 原告身份证明 + 被告信息。具体以受诉法院要求为准。

### Q13: 起诉要花多少钱？

案件受理费根据诉讼标的额计算（财产案件按比例缴纳），具体标准可查询《诉讼费用交纳办法》。符合条件可申请缓交、减交或免交。

## 三、法条查询相关

### Q14: 法条查询的数据来源是什么？

**双通道策略**：优先调用**国家法律法规数据库**（flk.npc.gov.cn）官方 API 获取实时法条；API 不可用时降级到 AI 训练知识库，并标注 `[数据来源：AI知识库]`。不使用任何第三方非官方数据源。详见 `references/shared-statute-engine.md`。

### Q15: 官方 API 不可用时怎么办？

自动降级到 **AI 训练知识库** 提供法条引用，在法律引用末尾标注 `[数据来源：AI知识库]`，并建议用户手动访问 https://flk.npc.gov.cn/ 核验。不降级到任何第三方非官方数据源。详见 `references/shared-statute-engine.md`。

### Q16: 模块C的"四步深度分析"和"六步法规检索"有什么区别？

| 流水线 | 触发场景 | 交付物 |
|:---|:---|:---|
| C1 四步深度分析 | 已知具体法条，需结构化拆解 | 法条结构化分析 + 体系定位 + 概念深挖 + 类案验证 |
| C2 六步法规检索 | 从检索主题出发，端到端检索 | 法规清单 + 法条原文 + 案例 + 分析（共6份） |

## 四、刑事案件相关

### Q17: 刑事案件能辅助什么？

模块D 支持 **5 类刑事专项材料**：

| 子流程 | 材料 | 模板 |
|:---|:---|:---|
| D4 | 刑事控告材料草稿 | `assets/criminal-accusation-template.md` |
| D5 | 取保候审申请草稿 | `assets/bail-application-template.md` |
| D6 | 辩护意见要点整理 | `assets/criminal-defense-opinion-template.md` |
| D7 | 刑事附带民事材料草稿 | `assets/criminal-incidental-civil-template.md` |
| D8 | 羁押阶段家属沟通提纲 | `assets/detention-family-communication-template.md` |

### Q18: 刑事案件正式会见、阅卷、出庭能做吗？

不能。模块D 仅提供基础分析、流程指引、材料清单和文书草稿辅助。正式会见、阅卷、出庭由律师承接，详见 `references/module-d-criminal.md` D2 禁止边界。

## 五、意图收敛与任务拆解

### Q19: 描述案情时需要注意什么？

- **尽量详细** — 时间、地点、人物、金额、经过越清楚越好
- **分清当事人** — 谁是原告、谁是被告
- **提供证据类型** — 合同/借条/聊天记录/转账记录/照片等
- **明确诉求** — 想要什么结果（还钱/赔偿/离婚/解除合同等）

### Q20: 意图不清晰时怎么处理？

启动渐进式意图收敛协议（`references/shared-intent-convergence.md`），最多 3 轮：

```
S_R1（领域确认）→ S_R2（意图确认）→ S_R3（细节确认）→ S_DISPATCHED（派发）
```

3 轮未收敛则走兜底路由（module-a A2 通用咨询流程）。

### Q21: 混合意图怎么处理？

检测到多个意图时，**自动拆解**为有序任务队列（`references/shared-task-decomposition.md`），按依赖排序 → 同领域合并 → 跨领域拆分 → 顺序执行 → 最终汇总。仅在依赖矛盾或用户需求冲突时才询问用户。

### Q22: 直跳规则是什么？

用户输入同时包含**领域专有词**（如"离婚""工资拖欠""取保候审"）和**行为词**（如"写起诉状""查法条""控告"）时，零轮次直跳目标模块，不启动收敛协议。

## 六、技术使用

### Q23: 怎么生成起诉状 DOCX？

```bash
# 列出全部可用案由
python scripts/generate_complaint_docx.py --list

# 预览模板（不生成文件）
python scripts/generate_complaint_docx.py --case 01 --dry-run

# 用示例数据填充并预览
python scripts/generate_complaint_docx.py --case 01 --data examples/private-lending-data.json --dry-run

# 生成空模板 DOCX
python scripts/generate_complaint_docx.py --case 01 --output private-lending.docx

# 用示例数据填充并生成 DOCX
python scripts/generate_complaint_docx.py --case 01 --data examples/private-lending-data.json --output private-lending-filled.docx
```

> 脚本优先使用 `python-docx`；环境未安装该包时，自动使用 Python 标准库生成基础 `.docx` 文件。

### Q24: 怎么跑验证脚本？

```bash
# 样例质量门禁（40 个 examples）
python scripts/validate_examples.py

# 类别覆盖矩阵门禁（22 类 + routes + version_marker）
python scripts/validate_category_coverage.py
```

### Q25: 怎么跑单元测试？

```bash
# 全部测试（10 个用例）
python -m unittest tests.test_generate_complaint_docx -v

# 或用 discover
python -m unittest discover -s tests -v
```

测试自动覆盖全部 40 个 case↔template↔example 三元组，无需手工维护映射（`setUpClass` 自动推导）。

### Q26: 新增案由需要改哪些文件？

按命名约定添加以下 3 个文件，测试自动覆盖，无需修改测试代码：

1. `assets/template-NN-{slug}.md` — 模板
2. `references/case-NN-{slug}.md` — 模块速览
3. `examples/{slug}-data.json` — 填充样例

同时需同步更新以下引用点：

- `references/module-b-complaint.md` B1 表
- `references/shared-category-coverage.md` 覆盖矩阵
- `references/shared-intent-convergence.md` R1/R2/R3 映射
- `references/shared-activation-rules.md` 关键词触发分类
- `SKILL.md` 案由速览 + 触发条件

### Q27: 失败回退机制是什么？

`references/shared-error-handling.md` 定义 10 类异常场景的标准化处理，遵循**不中断、不瞎编、给出路**原则。连续失败 2 次触发熔断，提示用户介入。
