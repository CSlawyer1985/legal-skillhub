# 跳过条目保存 Agent

> **新创建**：本Agent在批注添加Agent完成后执行，将批注过程中被跳过的条目另存为独立的JSON文件，供用户检查。

## 配置信息

| 项目 | 值 |
|------|-----|
| 输入 | 批注添加Agent报告中跳过的条目信息（从跳过条目日志中获取） |
| 输出 | `<work_dir>/skipped_reviews_<timestamp>.json`（供用户检查的跳过条目汇总） |

## 执行前检查清单

- [ ] 确认批注添加Agent已完成（可检查 `<work_dir>/skipped_reviews_<timestamp>.json` 是否存在）
- [ ] 如果批注添加Agent已生成跳过文件，验证其内容完整性

## 执行步骤

1. 验证跳过条目文件：
   - 读取 `<work_dir>/skipped_reviews_<timestamp>.json`（如已生成）
   - 确认文件为有效JSON数组
   - 统计跳过条目总数和各跳过原因分类

2. 补充跳过条目元数据（如果缺失）：
   - 为每条跳过条目添加 `skip_reason` 字段
   - 按跳过原因分类汇总：
     - "context_not_found"（图片/附图类context不存在）
     - "revision_conflict"（修订冲突）
     - "context_not_verbatim"（context不是逐字复制）
     - "context_contains_newline"（context包含\n）
     - "context_too_long"（context超长）
     - "old_text_not_substring"（old_text不是context子串）
     - "occurrence_invalid"（occurrence参数失效）
     - "text_not_found"（未找到文本）
     - "other"

3. 报告跳过条目汇总：
   - 总跳过数量
   - 各原因分类数量
   - 最高频原因及建议修正方向

## 执行后自检清单

- [ ] 跳过条目JSON文件格式有效、内容完整
- [ ] 跳过原因分类统计已完成
- [ ] 报告中包含了供用户手动检查的建议

## 专属约束

- 仅读取和分析，不得修改跳过条目的原始内容
- 不得尝试重新执行批注添加
- 本Agent执行完成后立即结束