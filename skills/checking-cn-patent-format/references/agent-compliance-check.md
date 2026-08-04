# 合规检查 Agent

> **新创建**：本Agent在最终输出前执行，检查整个skill执行过程中是否有违反约束的情况，生成检查日志JSON。

## 配置信息

| 项目 | 值 |
|------|-----|
| 检查依据 | `<skill_root>/SKILL.md` 第七节（5条核心约束）、`<skill_root>/references/prohibitions-and-rules.md` |
| 输出 | `<work_dir>/compliance_check_<timestamp>.json`（检查日志） |

## 执行前检查清单

- [ ] 确认 `<skill_root>/SKILL.md` 存在（读取第七节关键约束）
- [ ] 确认 `<skill_root>/references/prohibitions-and-rules.md` 存在
- [ ] 确认 `<work_dir>` 存在且包含所有中间文件

## 执行步骤

1. 读取约束规则：读取 `<skill_root>/references/prohibitions-and-rules.md` 完整内容，了解所有约束条款
2. 遍历检查以下维度：

   **2.1 文件位置合规**：
   - 检查 `<work_dir>` 外是否有该skill创建的中间文件（.py、.ps1、.json、.txt等）
   - 检查 `<skill_root>/scripts/` 下的脚本是否被修改

   **2.2 执行流程完整性**：
   - 检查各步骤预期输出文件是否存在
   - 验证步骤5.3：extracted_text、sections、3个拆分文件、header_sections、image_analysis
   - 验证步骤5.4：所有13个Agent的输出JSON文件
   - 验证步骤5.5：reviews合并文件、图片修复后的reviews文件
   - 验证步骤5.6：ReviewOut docx文件
   - 验证步骤5.7：verify_log.json（verify.py自动保存的验证日志）
   - 验证步骤5.8：relocation_log、deduplicated_comments（如有跳过条目）
   - 验证步骤5.8a：reviews_agent*_*.json已格式化为多行缩进格式
   - 验证步骤5.9：BUG日志JSON文件

   **2.3 JSON格式合规**：
   - 抽样检查审查意见JSON中的关键字段
   - 检查context是否包含\n换行符
   - 检查是否有emoji或非法控制字符
   - 检查context长度是否超过200字符

   **2.4 中间文件管理合规**：
   - 确认中间产物未被删除
   - 确认未询问用户是否删除文件

   **2.5 子Agent行为合规**：
   - 检查子Agent查询中是否包含"禁止向用户提问"指令
   - 检查Agent是否读取了禁止读取的文件（通过日志推断）

3. 生成检查日志JSON `<work_dir>/compliance_check_<timestamp>.json`：
   ```json
   [
     {
       "check_id": "CC-001",
       "category": "文件位置合规|执行流程完整性|JSON格式合规|中间文件管理|子Agent行为",
       "severity": "error|warning|info",
       "description": "具体违规描述",
       "file_path": "涉及的中间文件路径（如适用）",
       "relevant_rule": "约束条款引用",
       "fixable": true/false,
       "suggested_fix": "修复建议（如可修复）"
     }
   ]
   ```

4. 输出检查摘要：total_checks、errors、warnings、fixable_count、unfixable_count

## 执行后自检清单

- [ ] 检查日志JSON已生成且格式有效
- [ ] 所有检查维度已覆盖
- [ ] 每条违规记录包含完整的元数据（category、severity、description、fixable等）

## 专属约束

- 仅检查和记录，不执行任何修复操作
- 不得修改任何中间文件
- 本Agent执行完成后立即结束，不总结检查结果