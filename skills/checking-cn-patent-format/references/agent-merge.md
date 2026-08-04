# 合并去重 Agent

> 本Agent由主Agent在第5.5步委托执行，负责合并所有Agent的审查意见、多策略去重和修订冲突解决。

## 配置信息

| 项目 | 值 |
|------|-----|
| 工具 | `<skill_root>/scripts/merge_reviews.py` |
| 输入 | 所有 `reviews_agentN_<timestamp>.json` 文件 |
| 输出 | `<work_dir>/reviews_<timestamp>.json` |

## 执行前检查清单

- [ ] 确认 `<skill_root>/scripts/merge_reviews.py` 存在
- [ ] 确认所有审查Agent的JSON输出文件存在（agent1-13）
- [ ] 确认 `<work_dir>` 存在

## 执行步骤

1. 运行一体化合并脚本：
   ```bash
   python "<skill_root>/scripts/merge_reviews.py" --work-dir "<work_dir>" --timestamp "<timestamp>" --output "<work_dir>/reviews_<timestamp>.json" --enable-dedup-log
   ```
   
   脚本自动完成：合并 → 预分组去重 → 多策略去重（精确/语义/包含/issue语义/跨章节vs单章节/位置邻近） → 冗余replace去重 → 修订冲突检测与解决 → replace-comment冲突合并 → 排序（comment优先于replace/delete） → 输出

2. **语义去重后处理（LLM辅助）**：脚本去重基于字段匹配和n-gram相似度，可能遗漏语义相同但表述不同的审查意见。在脚本运行完成后，执行以下人工语义去重检查：
   
   a. 读取 `<work_dir>/reviews_<timestamp>.json`
   
   b. 按 `(section, paragraph_index)` 分组，对每组内的审查意见进行语义去重检查：
      - 如果两条意见的 issue 描述的是同一问题（即使表述不同），且 context 指向同一段落同一位置，则判定为语义重复
      - 语义重复的判定标准：两条意见的核心问题类型相同（如都是"错别字"、都是"缺少所述"、都是"附图标记不一致"等），且修改目标相同（old_text 相同或高度重叠）
      - 保留策略：保留 suggestion 最详细、信息量最大的一条；如果两条各有独特信息，将独特信息合并到保留条目的 issue/suggestion 中，然后删除另一条
   
   c. 特别关注以下高频重复场景：
      - Agent 11（全文简单审查）与 Agent 13（附图审查）对说明书中附图标记问题的重复报告
      - Agent 11 与 Agent 12（全文复杂审查）对跨章节一致性问题的重复报告
      - 单章节 Agent 与跨章节 Agent 对同一位置同一问题的重复报告
   
   d. 将语义去重后的结果保存回 `<work_dir>/reviews_<timestamp>.json`

3. 关注脚本输出的统计信息。如果有文件被跳过，读取并修复JSON语法错误后重新运行：
   - 检查中文引号""被误用为JSON边界
   - 检查未转义的双引号
   - 检查缺少逗号、多余逗号、括号不匹配等
   - 禁止从外部目录复制文件来替代修复

4. 验证输出：
   - 读取 `<work_dir>/reviews_<timestamp>.json`，确认：
     - 文件为有效 JSON 数组
     - 所有条目包含 section、issue、context、suggestion、action_type 字段
     - context 字段非空
     - 不存在语义高度重复的条目（同一段落同一问题出现两次以上）

5. 报告结果：
   - 合并前各Agent的审查意见数量（逐个读取各 `reviews_agentN_*.json` 文件统计实际数组长度，以实际统计数为准）
   - 合并总数、去重数量、去重后总数
   - 语义去重后处理：额外去除的语义重复数量
   - 修订冲突检测：发现的冲突数量、解决方法
   - 位置邻近重复检测：检查是否存在同一段落内多条相似审查意见，标注供用户参考
   - 修复建议一致性检查：检查是否存在相互矛盾的建议
   - 建议冲突检测与标注：标注修正方向矛盾或程度不同的建议

## 执行后自检清单

- [ ] 输出文件 `<work_dir>/reviews_<timestamp>.json` 存在且为有效JSON数组
- [ ] 报告中包含完整的去重统计信息
- [ ] 位置邻近重复已在报告中标注
- [ ] 建议冲突已在报告中标注

## 专属约束

- **修复JSON时允许创建临时脚本**：如果 merge_reviews.py 输出中发现 skipped > 0，需要修复被跳过的JSON文件时，允许在 `<work_dir>` 中创建临时修复脚本（如 `_fix_json_temp.py`）。修复完成后临时文件保留在 `<work_dir>` 中，**禁止删除临时文件，禁止因临时文件的存在而停下工作流或要求用户清理**
- 禁止在工作目录外创建任何文件
- 禁止修改 `<skill_root>/scripts/` 下的脚本文件
- 终端故障处理：如果命令返回退出码 -1073741510 或连续3次无输出，报告终端故障并提供手动执行命令