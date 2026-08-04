# Agent 3 审查任务 — 权利要求书格式检查1

## 配置信息

| 项目 | 值 |
|------|-----|
| section | 权利要求书 |
| claim_number | 权利要求序号（整数）或 null |
| 审查规则文件 | `<skill_root>/Checking Rules/31-权利要求书-简单审查1-格式检查1.md` |
| 所需章节文件 | `<work_dir>/section_claims_<timestamp>.json` |
| 禁止读取 | 其他任何章节拆分文件 |
| 禁止审查章节 | 摘要、说明书 |
| 输出文件 | `<work_dir>/reviews_agent3_<timestamp>.json` |

## 执行前检查清单

- [ ] 读取 `<skill_root>/references/common-specs.md` 完整内容
- [ ] 确认审查规则文件 `<skill_root>/Checking Rules/31-权利要求书-简单审查1-格式检查1.md` 存在且可读
- [ ] 确认章节拆分文件 `<work_dir>/section_claims_<timestamp>.json` 存在且 `paragraphs` 字段非空

## 执行步骤

1. 读取审查规则文件 `<skill_root>/Checking Rules/31-权利要求书-简单审查1-格式检查1.md` 的完整内容
2. 读取待审查文本：读取 `<work_dir>/section_claims_<timestamp>.json`，提取 `paragraphs` 字段的值作为待审查文本
3. 执行审查：按照审查规则逐条检查文本是否存在问题，收集所有发现的问题
4. 输出审查意见JSON：将审查意见整理为common-specs中规定的JSON格式，保存为 `<work_dir>/reviews_agent3_<timestamp>.json`
   - section 填写 "权利要求书"
   - claim_number 填写对应权利要求序号或 null
5. 立即执行自检 → 完成自检后不总结不暂停，直接结束

## 执行后自检清单

- [ ] JSON文件已写入且格式有效（`indent=2`）
- [ ] 重新读取 `<work_dir>/section_claims_<timestamp>.json` 验证 context verbatim
- [ ] 逐条检查 context 无 `\n` 换行符
- [ ] 逐条检查 new_text 无 `\n` 换行符
- [ ] 逐条检查 issue/suggestion/old_text/new_text 逻辑一致性
- [ ] 逐条确认 section 为 "权利要求书"
- [ ] 确认 JSON 无语法错误
- [ ] 修正后重新保存

## 专属约束

- 本Agent只审查权利要求书，不得对摘要或说明书提出审查意见
- 差异化审查说明：无