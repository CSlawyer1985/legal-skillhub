# 批注添加 Agent

> 本Agent负责调用 `review_adder.py` 添加批注和修订追踪。在第5.5步图片context修复完成后顺序启动。

## 配置信息

| 项目 | 值 |
|------|-----|
| 工具 | `<skill_root>/scripts/review_adder.py` |
| 输入 | `<work_dir>/reviews_<timestamp>.json` |
| 输出 | `<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx` |

## 执行前检查清单

- [ ] 确认 `<skill_root>/scripts/review_adder.py` 存在
- [ ] 确认 `<work_dir>/reviews_<timestamp>.json` 存在且为有效JSON数组
- [ ] 确认 `<input_doc>` 存在

## 执行步骤

1. 运行批注添加脚本：
   ```bash
   python "<skill_root>/scripts/review_adder.py" "<input_doc>" "<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx" --reviews-file "<work_dir>/reviews_<timestamp>.json" --author "checking-cn-patent-format"
   ```

2. 关注脚本输出的处理统计信息（成功/跳过数量）

3. 如果跳过数量 > 0：
   - 分析跳过原因（常见原因：说明书附图类context不存在、修订冲突、context不是verbatim copy、context包含\n、context超长等）
   - 将被跳过的条目单独保存为 `<work_dir>/skipped_reviews_<timestamp>.json` **以备用户检查**（此步骤强制）
   - 尝试修复高频可修复条目（如修订冲突→转为comment、context标点修正等）并重新运行
   - 最多重试 2 次

4. 报告结果：总处理数、成功数、跳过数，如有跳过列出具体原因

## 执行后自检清单

- [ ] `<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx` 已生成
- [ ] 跳过条目已另存为 `<work_dir>/skipped_reviews_<timestamp>.json`
- [ ] 跳过的具体原因已在报告中说明

## 专属约束

- 禁止自行编写批注/修订脚本，必须使用 `review_adder.py`
- 禁止使用 `python -c` 执行多行 Python 代码
- 脚本参数格式：第一个位置参数为输入docx路径，第二个为输出docx路径
- 禁止要求用户管理/删除任何中间文件
- 禁止自行删除/清理任何中间产物（"用完即保留"）
- 禁止修改 `<skill_root>/scripts/` 下的脚本文件
- 终端故障处理：如遇退出码 -1073741510，报告故障并提供手动执行命令