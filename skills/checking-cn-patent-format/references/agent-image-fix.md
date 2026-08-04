# 图片类Context修复 Agent

> **新创建**：本Agent在合并去重完成后执行，专门修复说明书附图类审查意见中的context锚定问题。

## 配置信息

| 项目 | 值 |
|------|-----|
| 输入 | `<work_dir>/reviews_<timestamp>.json` + `<work_dir>/extracted_text_<timestamp>.txt` |
| 输出 | 修复后的 `<work_dir>/reviews_<timestamp>.json`（原地更新） |

## 执行前检查清单

- [ ] 确认 `<work_dir>/reviews_<timestamp>.json` 存在且为有效JSON数组
- [ ] 确认 `<work_dir>/extracted_text_<timestamp>.txt` 存在

## 执行步骤

1. 读取 `<work_dir>/reviews_<timestamp>.json`
2. 读取 `<work_dir>/extracted_text_<timestamp>.txt`（用于查找文档中的实际文本）
3. 筛选需要修复的条目（section 为 "说明书附图" 的条目）
4. 逐条检查筛选条目的 context 是否为文档 verbatim copy：
   - 如果 context 包含"（源文件："、"图1/图2/图3"、"说明书附图图"等Agent构造文本标记 → 需要修复
   - 如果 context 是描述性文本而非文档实际文本 → 需要修复
5. 按优先级修复：
   - **说明书附图元数据级问题**：定位说明书附图章节的实际文本，替换 context 和 highlight_text；如果说明书附图章节没有实际存在的可锚定文本（规则12场景），则 context 和 highlight_text 均设为"说明书附图"（文档页眉中的章节标题文本）
   - **图片子Agent输出的问题**（context格式为"<图片逻辑名称>：<位置描述>"）：替换为说明书附图章节的实际文本
   - 如果无法从extracted_text中找到合适的锚定文本：保持 context 不变，确保 action_type 为 comment，在 issue 追加"[注：图片类问题，无法自动定位到文档文本]"
6. 将修复后的JSON重新保存到 `<work_dir>/reviews_<timestamp>.json`

## 执行后自检清单

- [ ] 所有说明书附图类条目的 context 已检查
- [ ] 可修复的条目已更新为文档实际文本
- [ ] 不可修复的条目已确保 action_type 为 comment 并添加备注
- [ ] 修复后的JSON文件已保存且格式有效

## 专属约束

- 仅修复 context 和 highlight_text 字段，不得修改 issue、suggestion、action_type 等字段（除非需要将非法 action_type 改为 comment）
- context 替换后必须能在 extracted_text.txt 中找到完全匹配
- 本Agent执行完成后立即结束，不总结不暂停