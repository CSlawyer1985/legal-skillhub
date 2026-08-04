# Agent 1 审查任务 — 摘要简单审查

## 配置信息

| 项目 | 值 |
|------|-----|
| section | 摘要 |
| claim_number | null |
| 审查规则文件 | `<skill_root>/Checking Rules/11-摘要-简单检查1.md` |
| 所需章节文件 | `<work_dir>/section_abstract_text_<timestamp>.json` |
| 禁止读取 | 其他任何章节拆分文件 |
| 禁止审查章节 | 权利要求书、说明书 |
| 输出文件 | `<work_dir>/reviews_agent1_<timestamp>.json` |

## 执行前检查清单

- [ ] 读取 `<skill_root>/references/common-specs.md` 完整内容
- [ ] 确认审查规则文件 `<skill_root>/Checking Rules/11-摘要-简单检查1.md` 存在且可读
- [ ] 确认章节拆分文件 `<work_dir>/section_abstract_text_<timestamp>.json` 存在且 `paragraphs` 字段非空

## 执行步骤

1. 读取审查规则文件 `<skill_root>/Checking Rules/11-摘要-简单检查1.md` 的完整内容
2. 读取待审查文本：读取 `<work_dir>/section_abstract_text_<timestamp>.json`，提取 `paragraphs` 字段的值作为待审查文本
3. 执行审查：按照审查规则逐条检查文本是否存在问题，收集所有发现的问题
4. 输出审查意见JSON：将审查意见整理为common-specs中规定的JSON格式，保存为 `<work_dir>/reviews_agent1_<timestamp>.json`
   - section 填写 "摘要"
   - claim_number 填写 null
5. 立即执行自检（见下方检查清单）→ 完成自检后不总结不暂停，直接结束

## 执行后自检清单

- [ ] JSON文件已写入且格式有效（`indent=2`）
- [ ] 重新读取 `<work_dir>/section_abstract_text_<timestamp>.json` 的 `paragraphs` 数组
- [ ] 逐条确认 context 字段值在 paragraphs 中确实存在且逐字匹配
- [ ] 逐条检查 context 无 `\n` 换行符
- [ ] 逐条检查 new_text 无 `\n` 换行符
- [ ] 逐条检查 issue/suggestion/old_text/new_text 逻辑一致性
- [ ] 逐条确认 section 为 "摘要"
- [ ] 确认 JSON 无语法错误
- [ ] 修正后重新保存

## 专属约束

- 本Agent只审查摘要，不得对权利要求书或说明书提出审查意见
- **职责边界（防止与Agent 2重复）**：本Agent仅负责摘要的格式/标点/结构类问题，包括：字数限制、段落格式、错别字/病句/重复语句、标点符号错误、附图标记格式。**禁止审查**以下内容（由Agent 2负责）：商业性宣传用语、贬低或诽谤用语、现有技术描述、摘要表述完整性、摘要内容一致性