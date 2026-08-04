# 跳过批注重定位 Agent

> 本Agent由主Agent在第5.8步委托执行，负责将批注添加过程中被跳过的条目重新定位到对应section章节结尾处，以"额外批注"为锚定文本添加批注。

## 配置信息

| 项目 | 值 |
|------|-----|
| 工具 | `<skill_root>/scripts/skip_relocator.py` |
| 输入 | `<work_dir>/skipped_reviews_<timestamp>.json`、`<work_dir>/reviews_<timestamp>.json`、审查后docx文件 |
| 输出 | 更新后的审查docx文件、`<work_dir>/relocation_log_<timestamp>.json`、`<work_dir>/deduplicated_comments_<timestamp>.json` |

## 执行前检查清单

- [ ] 确认 `<skill_root>/scripts/skip_relocator.py` 存在
- [ ] 确认 `<work_dir>/skipped_reviews_<timestamp>.json` 存在
- [ ] 确认 `<work_dir>/reviews_<timestamp>.json` 存在
- [ ] 确认 `<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx` 存在
- [ ] 确认5.7内容完整性验证已通过

## 执行步骤

1. 运行跳过批注重定位脚本：
   ```bash
   python "<skill_root>/scripts/skip_relocator.py" --input-doc "<input_doc>" --reviewed-docx "<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx" --work-dir "<work_dir>" --timestamp "<timestamp>" --author "checking-cn-patent-format"
   ```

2. 关注脚本输出的处理统计信息：
   - 总跳过条目数
   - 成功重定位数
   - 失败数
   - 各章节处理情况

3. 验证输出文件：
   - 确认 `<work_dir>/relocation_log_<timestamp>.json` 存在且为有效JSON
   - 确认 `<work_dir>/deduplicated_comments_<timestamp>.json` 存在且为有效JSON
   - 确认审查后docx文件已更新（包含"额外批注"锚定文本和重定位批注）

4. 检查重定位日志内容：
   - 每条重定位记录应包含：原批注所属section、原位置信息、新位置信息、重定位时间戳
   - 失败记录应包含失败原因

5. 检查去重批注数据文件内容：
   - `metadata` 字段完整，包含源文件路径、处理时间戳等
   - `deduplication_summary` 字段包含完整的去重统计
   - `comments` 数组中每条批注的 `status` 字段正确标注（added/skipped/relocated）
   - 重定位的批注应包含 `relocation_info` 字段

6. 报告结果：
   - 总跳过条目数
   - 成功重定位数
   - 失败数及失败原因
   - 各章节重定位情况

## 重定位逻辑说明

脚本执行以下核心逻辑：

1. **读取跳过条目**：从 `skipped_reviews_<timestamp>.json` 读取所有被跳过的审查意见
2. **按章节分组**：将跳过条目按 `section` 字段分组
3. **插入锚定文本**：对每个有跳过条目的章节，在该章节最后一个段落之后插入一个新段落，内容为"额外批注"
4. **添加批注**：以"额外批注"文本为定位点，为该章节的所有跳过条目逐一添加批注
5. **生成日志**：记录所有重定位操作，包含原位置和新位置信息
6. **生成去重批注数据**：合并已添加和已重定位的批注信息，生成完整的去重批注数据文件

## 执行后自检清单

- [ ] 审查后docx文件中包含"额外批注"锚定文本
- [ ] 重定位批注正确显示在对应章节结尾
- [ ] 重定位日志文件格式有效、内容完整
- [ ] 去重批注数据文件格式有效、内容完整
- [ ] 原有批注和修订未受影响

## 专属约束

- 必须使用 `skip_relocator.py`，禁止编写自定义重定位脚本
- 重定位操作仅在5.7验证通过后执行
- 如果跳过条目文件不存在或为空，直接生成空的去重批注数据文件，不视为错误
- 重定位后的批注统一使用 `action_type: "comment"`，不再执行 replace/delete 操作
- 摘要附图section的条目在批注添加阶段已通过"摘要附图批注"锚定文字自动处理，通常不会出现在跳过条目中；如因摘要附图章节未识别导致跳过，则按常规重定位流程处理
- 禁止修改 `<skill_root>/scripts/` 下的脚本文件（本Agent专属脚本除外）
- 终端故障处理：如遇退出码 -1073741510，报告故障并提供手动执行命令
