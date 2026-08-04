# Agent 9 审查任务 — 说明书简单审查

## 配置信息

| 项目 | 值 |
|------|-----|
| section | 说明书 |
| claim_number | null |
| 审查规则文件 | `<skill_root>/Checking Rules/41-说明书-简单审查1.md` |
| 所需章节文件 | `<work_dir>/section_description_<timestamp>.json` |
| 禁止读取 | 其他任何章节拆分文件 |
| 禁止审查章节 | 摘要、权利要求书 |
| 输出文件 | `<work_dir>/reviews_agent9_<timestamp>.json` |

## 执行前检查清单

- [ ] 读取 `<skill_root>/references/common-specs.md` 完整内容
- [ ] 确认审查规则文件存在且可读
- [ ] 确认章节拆分文件存在且 `paragraphs` 字段非空

## 执行步骤

1. 读取审查规则文件 `<skill_root>/Checking Rules/41-说明书-简单审查1.md` 的完整内容
2. 读取待审查文本：读取 `<work_dir>/section_description_<timestamp>.json`，提取 `paragraphs` 字段的值作为待审查文本
3. 执行审查：按照审查规则逐条检查，关注撰写规范问题（错别字、用语不当、标点错误、格式缺失等）
4. 输出审查意见JSON：保存为 `<work_dir>/reviews_agent9_<timestamp>.json`，section 填写 "说明书"，claim_number 填写 null
5. 立即执行自检 → 完成自检后不总结不暂停，直接结束

## 执行后自检清单

- [ ] JSON文件已写入且格式有效（`indent=2`）
- [ ] 重新读取 `<work_dir>/section_description_<timestamp>.json` 验证 context verbatim
- [ ] 逐条检查 context 无 `\n` 换行符
- [ ] 逐条检查 new_text 无 `\n` 换行符
- [ ] 逐条检查 issue/suggestion/old_text/new_text 逻辑一致性
- [ ] 逐条确认 section 为 "说明书"
- [ ] 确认 JSON 无语法错误
- [ ] 修正后重新保存

## 专属约束

### 跨章节边界约束

- 本Agent只检查说明书内部的撰写规范问题
- **极其重要：禁止报告任何形式的"发明名称/说明书标题与正文内容不一致"问题**（这是Agent 11/12的专属职责）
- 禁止报告"发明名称与摘要主题不一致"类问题（由Agent 11/12负责）
- 禁止报告"说明书与权利要求书主题不一致"类问题（由Agent 11/12负责）

**仅允许报告的问题类型**（全部可在section_description内部独立验证）：
- 说明书内部的错别字、病句、标点错误
- "本发明"用语不规范（仅在说明书范围内统计）
- 缺少标准段落结尾语句
- 附图说明中的文字错误（不涉及附图本身是否缺失/重复）
- 术语在同一章节内的前后使用不一致
- 格式问题（序号、缩进等）

**判断金标准**：审查意见的context是否全部且仅来自section_description文件的paragraphs数组？如果是→可以报告；如果需要引用或隐含其他章节文件的内容→绝对禁止。

### 与Agent 10的职责边界

- Agent 9负责说明书撰写规范问题（错别字、用语不当、标点错误等），从"撰写质量"角度审查
- Agent 10负责说明书公开充分性问题，从"可实施性"角度审查
- 当错别字/术语不清问题同时构成"撰写规范"和"公开不充分"时，Agent 9应优先报告，Agent 10仅在该问题的修正方案与Agent 9不同时才单独报告
- 禁止在issue中提及"公开不充分"——这是Agent 10的职责表述，Agent 9应使用"错别字"、"用语不当"、"术语不清"等表述

### 审查粒度控制

- 同一类型的批量错误，禁止为每个实例单独生成一条审查意见
- 应采用"代表性示例+批量说明"模式：选择2-3个典型实例详细报告，其余使用1条comment概括说明
- 建议输出量范围：5-20条

### "本发明"批量替换策略

- 策略A（推荐）：全部使用comment类型，合并为1-3条comment，在suggestion中明确说明"请使用Word查找替换功能统一替换"
- 策略B（高级）：精选少量高置信度replace（context<50字符），其余使用comment
- 禁止对超过5处的"本发明"问题全部使用replace类型

### 说明书特有风险

- 发明名称与技术领域分属不同段落：必须拆分为两条审查意见
- new_text禁止包含\n