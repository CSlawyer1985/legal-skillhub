# 故障处理详细参考

> 本文件包含SKILL.md第八节5种常见故障之外的详细故障处理方式。当skill在执行过程中遇到未在正文中列出的故障时，加载本文件寻求解决方案。

---

## 目录

- [终端故障恢复](#终端故障恢复)
- [脚本执行故障](#脚本执行故障)
- [JSON输出故障](#json输出故障)
- [批注添加故障](#批注添加故障)
- [验证故障](#验证故障)
- [子Agent故障](#子agent故障)
- [文件系统故障](#文件系统故障)

---

## 终端故障恢复

### 故障判定条件

满足以下任一条件即判定为终端故障：
- RunCommand 返回退出码 `-1073741510`（`STATUS_DLL_INIT_FAILED`）
- 连续 3 次命令均无输出（空日志 + 非零退出码）
- 连续 3 次命令返回相同的 DLL 初始化错误

### 故障恢复流程

1. 立即停止重试：确认终端故障后，禁止在同一终端上继续重试（最多重试3次以确认故障）
2. 记录当前状态：记录已完成的步骤、已生成的中间文件、当前需要执行的步骤
3. 向用户报告：
   ```
   ⚠️ 终端环境故障（STATUS_DLL_INIT_FAILED）
   已完成步骤：第X步（共9步：5.1~5.9）
   当前步骤：第Y步（脚本执行失败）
   工作目录：<work_dir>
   请在新的终端中执行以下命令完成剩余步骤：
   [具体命令]
   中间文件已保存在工作目录中，可用于断点续传。
   ```
4. 提供手动恢复命令

### 各步骤的手动恢复命令

**第5.3步（文档提取）失败时**：
```bash
python "<skill_root>/scripts/patent_extractor.py" "<input_doc>" --extract-output "<work_dir>/extracted_text_<timestamp>.txt"
python "<skill_root>/scripts/patent_extractor.py" "<input_doc>" --split-sections "<work_dir>"
```

**第5.5步（合并去重）失败时**：
```bash
python "<skill_root>/scripts/merge_reviews.py" --work-dir "<work_dir>" --timestamp "<timestamp>" --output "<work_dir>/reviews_<timestamp>.json"
```

**第5.6步（批注添加）失败时**：
```bash
python "<skill_root>/scripts/review_adder.py" "<input_doc>" "<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx" --reviews-file "<work_dir>/reviews_<timestamp>.json" --author "checking-cn-patent-format"
```

**第5.7步（验证）失败时**：
```bash
python "<skill_root>/scripts/verify.py" "<input_doc>" "<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx" "<work_dir>"
```

**第5.8步（跳过批注重定位）失败时**：
```bash
python "<skill_root>/scripts/skip_relocator.py" --input-doc "<input_doc>" --reviewed-docx "<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx" --work-dir "<work_dir>" --timestamp "<timestamp>" --author "checking-cn-patent-format"
```

**第5.8a步（格式化审查输出JSON）失败时**：
```bash
python "<skill_root>/scripts/format_json.py" --work-dir "<work_dir>"
```

**第5.9步（BUG审查与归档）**：
> 此步骤委托编排Agent（`references/agent-bug-review-orchestrator.md`）执行。编排Agent根据文件数量自动选择模式：
> - **并行模式**：调度多个Worker Agent（`references/agent-bug-review-worker.md`）分2~4组并行审查
> - **单Agent模式**：直接委托 `references/agent-bug-review.md` 执行
>
> 如编排Agent执行失败，可重新启动 `references/agent-bug-review-orchestrator.md` 子Agent完成任务。
> 如某个Worker Agent执行失败，编排Agent会自动重试该Worker（最多2次），不影响其他Worker。

### 断点续传规则

- 如果 `<work_dir>` 中已存在某步骤的输出文件，可以从下一步继续
- 已完成的审查Agent的JSON文件可直接复用
- 合并去重后的 `reviews_<timestamp>.json` 可直接复用

---

## 脚本执行故障

### patent_extractor.py 执行失败

**常见原因**：
- 输入docx文件损坏或格式不支持
- .doc文件但未安装WPS/Microsoft Word
- pywin32未安装

**处理方式**：
1. 检查错误输出中的具体错误信息
2. 如果输入文件是 .doc 且 pywin32 不可用，提示用户安装 pywin32 或手动转换为 .docx
3. 如果是文档损坏，提示用户检查文件完整性

### merge_reviews.py 执行失败

**常见原因**：
- 某些Agent的JSON输出格式错误导致解析失败
- 输出目录权限不足

**处理方式**：
1. 逐个排查各Agent的JSON输出文件，找到格式错误的文件
2. 修复JSON语法错误：检查中文引号、未转义双引号、括号不匹配等
3. 重新运行 merge_reviews.py

### review_adder.py 执行失败

**常见原因**：
- 输出目录权限不足
- 输入docx文件正在被其他程序占用（如Word打开中）
- reviews JSON中包含非法XML字符

**处理方式**：
1. 确保输入docx文件未被其他程序打开
2. 检查reviews JSON中的issue/suggestion字段是否包含非法控制字符

---

## JSON输出故障

### Agent输出JSON格式错误

**常见原因**（按频率排序）：
1. 使用中文引号""替代英文双引号"作为JSON字符串边界
2. 字符串值中包含未转义的双引号
3. 数组末尾多余逗号
4. 括号不匹配
5. issue/suggestion中包含控制字符或emoji

**修复方法**：
1. 中文引号→替换为英文双引号
2. 未转义双引号→替换为单引号''
3. 清理多余逗号
4. 修正括号匹配

### Context field常见问题

| 问题 | 表现 | 修复方法 |
|------|------|----------|
| Context包含\n | 跨段落文本 | 拆分为多条审查意见 |
| Context超过200字符 | 匹配困难 | 截取关键最小片段 |
| Context不是verbatim copy | 标点/字符差异 | 从extracted_text逐字复制 |
| Context是概括性描述 | 非文档原文 | 替换为实际文本 |
| old_text不是context子串 | 匹配失败 | 确保old_text从context中精确截取 |
| old_text/new_text逻辑矛盾 | 方向不一致 | 逐条检查四个字段逻辑一致性 |

---

## 批注添加故障

### 大量条目被跳过（成功率<80%）

**常见原因及修复优先级**：

1. **修订冲突**（最常见）→ 将冲突条目转为 comment 类型
2. **图片/附图类context不存在** → 调用 agent-image-fix 修复
3. **Context不是verbatim copy** → 从extracted_text搜索并复制原文
4. **Context包含\n换行符** → 拆分为多条（需返回审查Agent）
5. **occurrence参数失效** → 改为comment类型
6. **new_text包含\n** → 改用comment类型
7. **context超长** → 截取关键片段

### 跳过条目修复流程

1. 读取 `<work_dir>/reviews_<timestamp>.json`，找到被跳过的条目
2. 按优先级修复：修订冲突→图片/附图类→occurrence失效→context质量问题→其他
3. 重新运行 review_adder.py（最多重试2次）
4. 仍无法修复的条目跳过，在最终报告中注明

---

## 验证故障

### verify.py 段落数量验证失败

**处理方式**：
1. 检查review_adder.py的执行日志，确认是否有大量replace操作失败
2. 检查是否有跨run的复杂文本替换失败
3. 修复对应审查意见后重新执行第5.6步和第5.7步
4. 最多重试5次

### verify.py 模拟接受修订失败

这是已知的verify.py模拟逻辑误报：
- verify.py通过跳过`<w:del>`内的`<w:t>`模拟接受修订
- 当`<w:del>`包含段落中全部文本时，空段落被过滤导致计数差异
- 如果段落数量验证（项目1）通过，此误报可忽略

---

## 子Agent故障

### Agent执行超时

- 原因：Agent审查文本过长、小参数LLM上下文耗尽
- 处理：重新启动该Agent，在query中建议分段审查

### Agent输出空数组但实际存在问题

- 原因：Agent 10常见（快速浏览后输出空数组）
- 处理：重新启动Agent，在query中强调"必须逐项检查5种公开不充分情形"
- Agent 10必须逐一写出5种情形的检查过程后方可输出空数组

### Agent越权审查

- 原因：Agent 9/10/11/12越权报告非分配章节的问题
- 处理：
  - 已在第4批去除越权检查（Agent 9/10仅加载说明书JSON，物理隔离）
  - Agent 11/12越权：在合并去重阶段由merge_reviews.py自动过滤

### BUG审查Worker Agent故障

- **Worker执行超时**：Worker读取的文件组过大导致上下文耗尽
  - 处理：编排Agent重新启动该Worker，将文件组进一步拆分为更小的子组
- **Worker返回格式错误**：Worker返回的JSON不符合预期结构
  - 处理：编排Agent解析Worker返回的文本，提取有效BUG信息；如无法解析，重新启动该Worker
- **Worker执行失败**：Worker因异常终止
  - 处理：编排Agent重试该Worker（最多2次），如仍失败，标记该文件组为"审查不完整"
- **编排Agent故障**：编排Agent自身执行失败
  - 处理：主Agent重新启动 `references/agent-bug-review-orchestrator.md` 子Agent
  - 如编排Agent反复失败，回退到单Agent模式：直接委托 `references/agent-bug-review.md`

---

## 文件系统故障

### 工作目录创建失败

- 原因：输入目录无写入权限、磁盘空间不足
- 处理：提示用户检查磁盘空间和目录权限；尝试在其他位置创建工作目录

### 文件冲突

- 策略：直接覆盖，不询问
- 禁止因文件冲突停止工作流程
- 如果Write工具自动覆盖失败，检查文件是否被其他进程占用

### 图片文件无法读取

- 原因：EMF/WMF矢量格式
- 处理：Agent输出comment类型意见说明无法查看该图片，不中断流程