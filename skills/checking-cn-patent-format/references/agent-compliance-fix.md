# 合规修复 Agent

> **新创建**：本Agent在合规检查Agent完成后执行，加载检查日志，对可修复的问题当场整改并记录，不可修复的标记。

## 配置信息

| 项目 | 值 |
|------|-----|
| 输入 | `<work_dir>/compliance_check_<timestamp>.json`（检查日志） |
| 输出 | `<work_dir>/compliance_fix_<timestamp>.json`（修复/整改记录） |

## 执行前检查清单

- [ ] 确认 `<work_dir>/compliance_check_<timestamp>.json` 存在且为有效JSON
- [ ] 确认 `<work_dir>` 存在

## 执行步骤

1. 读取检查日志 `<work_dir>/compliance_check_<timestamp>.json`
2. 筛选 `fixable: true` 的条目，逐条执行修复：

   **常见可修复问题及修复方式**：

   | 问题类型 | 修复方式 |
   |----------|----------|
   | 临时文件未放置于 `<work_dir>` | 将文件移动到 `<work_dir>` |
   | 输出JSON未使用 `indent=2` 格式化 | 重新格式化并保存（仅格式修复，不改内容） |
   | context包含 `\n` 换行符 | 标记为不可修复（需返回对应Agent重做） |
   | 子Agent查询缺少"禁止向用户提问" | 标记为不可修复（需主Agent修正query） |
   | 中间文件被意外删除 | 标记为不可修复（文件已丢失） |
   | 步骤遗漏导致输出缺失 | 标记为不可修复（需重新执行步骤） |
   | verify.py 未执行 | 标记为不可修复（需主Agent执行） |

3. 对可修复问题执行整改：
   - 对每个修复动作，在日志中追加 `action_taken` 字段
   - 修复前后记录对比（如文件位置变动记录）

4. 生成修复记录 `<work_dir>/compliance_fix_<timestamp>.json`：
   ```json
   [
     {
       "check_id": "CC-001",
       "status": "fixed|unfixed",
       "action_taken": "具体整改措施描述",
       "result": "success|failure",
       "note": "附加说明"
     }
   ]
   ```

5. 输出修复摘要：total_checked、fixed_count、unfixed_count、unfixed_details（不可修复项列表及原因）

## 执行后自检清单

- [ ] 所有标记为 fixable 的条目已逐一检查并尝试修复
- [ ] 修复记录JSON已生成且格式有效
- [ ] 不可修复项已详细记录原因
- [ ] 修复过程中未引入新的违规

## 专属约束

- 不得修改 `<skill_root>/scripts/` 下的脚本文件
- 不得修改审查意见JSON的内容（仅可修改格式）
- 文件移动/重命名操作需谨慎，确保不破坏引用关系
- 本Agent执行完成后立即结束，不总结修复结果