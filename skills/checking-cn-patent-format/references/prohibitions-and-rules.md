# 禁止事项与详细规则

本文件包含 Skill 执行过程中的详细禁止事项和规则说明。主 Agent 在执行工作流时按需加载。

> **核心约束（已提取至SKILL.md第七节）**：
> 1. 流程完整性 — 9个步骤必须不间断连续执行
> 2. 必须使用 review_adder.py 添加批注 — 禁止编写自定义脚本
> 3. 禁止跳过验证（第5.7步）— 未通过验证不得交付
> 4. 所有子Agent禁止向用户提问 — 必须自行判断并继续执行
> 5. 必须分批并行启动审查Agent — 禁止逐个串行启动

---

## 目录

- [关键禁止事项](#关键禁止事项)
- [审查意见 JSON 格式规范](#审查意见-json-格式规范)
- [文件命名规则](#文件命名规则)
- [工作文件夹管理规则](#工作文件夹管理规则)
- [脚本调用规则](#脚本调用规则)
- [验证步骤规则](#验证步骤规则)
- [修订追踪规范](#修订追踪规范)

---

## 关键禁止事项

1. **禁止自行编写修正脚本**：必须使用 `review_adder.py` 添加批注和修订操作。自行编写脚本会导致严重内容丢失。

2. **禁止在终端中直接执行多行 Python 代码**：必须直接调用提供的脚本（`patent_extractor.py`、`review_adder.py`、`merge_reviews.py`、`verify.py`）。

3. **禁止在 skill 目录内创建工作文件夹**：工作文件夹必须创建在输入 docx 文件所在目录下。所有路径必须使用绝对路径。

4. **禁止自行编造时间戳**：时间戳必须通过执行命令获取真实值。

5. **禁止在单个 Agent 对话中执行多条审查规则**：每个子Agent必须只执行其被分配的审查规则。

6. **禁止主 Agent 自行编写审查意见**：审查工作必须通过 Task 工具启动子 Agent 完成。

7. **禁止主 Agent 直接执行可委托的工作步骤**：文档提取、合并去重、批注添加必须通过 Task 工具委托执行。

8. **禁止在审查意见 JSON 的字符串值中使用未转义的双引号或中文引号**：必须使用 `\"` 转义或改用单引号 `''`。

9. **禁止逐个串行启动审查子 Agent**：必须分 7 批并行启动。

10. **禁止审查 Agent 越权审查非分配章节**：每个审查 Agent 必须只审查其被分配的章节。

11. **禁止合并去重 Agent 从外部目录复制文件**：修复 JSON 解析错误时必须在原文件基础上修复。

12. **禁止在 context、old_text、highlight_text 中使用 HTML/XML 标签**：这些字段必须是文档原文的逐字复制。

13. **禁止在 context、old_text 中包含换行符 `\n`**：跨段落的问题必须拆分为多条审查意见。

14. **禁止 suggestion 的修改方向与 issue 诊断矛盾**：suggestion 必须逻辑正确。

15. **禁止 Agent 11/12 报告单章节内部的问题**：仅报告跨章节的一致性问题。

16. **禁止文档提取使用 `>` 重定向输出到文件**：必须使用 `--extract-output` 参数。

17. **禁止要求用户管理/删除中间文件，禁止子Agent自行删除中间产物**：所有中间产物保留在 `<work_dir>` 中（"用完即保留"）。**在工作目录中创建的临时文件（如修复脚本、临时数据文件、`bug_log_temp_<timestamp>.json` 等）同样禁止删除，禁止因临时文件的存在而停下工作流或要求用户清理**。

18. **禁止在工作目录外创建脚本或中间文件**：所有中间产物必须放在 `<work_dir>` 中。

19. **审查 Agent 禁止读取非分配章节的文件**：只能读取其章节对应的拆分文件。

20. **禁止 context 中添加原文不存在的标点符号**：context 必须是文档原文的逐字复制。

21. **禁止 Agent 10 轻易输出空数组**：必须对每种"公开不充分"情形逐一给出明确判断。

22. **禁止 new_text 包含换行符 `\n`**：docx 中无法通过替换操作插入新段落。

23. **禁止审查Agent上下文浪费**：必须先写入JSON文件，再执行自验证。

24. **禁止 issue/suggestion/old_text/new_text 逻辑矛盾**：四个字段必须逻辑自洽。

25. **合并去重代理必须验证各 Agent 实际审查意见数量**：以实际统计数为准。

26. **主 Agent 禁止直接运行文档提取命令**：必须通过 Task 工具委托执行。

27. **Agent 9 和 Agent 10 禁止报告跨章节一致性问题**：仅检查说明书内部问题。

28. **replace 条目强制验证 old_text 和 new_text 非空**：空值会被降级为 comment。

29. **所有子Agent禁止向用户提问**：query 中必须包含此指令。

30. **主Agent禁止在步骤间停顿**：9个步骤必须在同一连续会话中不间断执行。

31. **禁止终端故障后反复重试同一终端**：最多重试3次，确认故障后执行恢复流程。

32. **禁止SubAgent修改skill脚本文件**：子Agent只能调用脚本，不得修改脚本源码。

33. **BUG审查Worker禁止读取未分配的文件**：每个Worker只能读取编排器分配的文件列表中的文件，禁止读取其他文件。

34. **BUG审查Worker禁止写入文件**：Worker的结果仅通过返回值传回给编排器，禁止Worker自行写入任何文件。

35. **BUG审查编排器必须并行启动Worker**：所有Worker必须在同一条消息中并行启动，禁止逐个串行启动。

---

## 审查意见 JSON 格式规范

- JSON 字符串值中禁止包含未转义的双引号，引用字词使用单引号 `''`
- 禁止使用中文引号 `""` 作为 JSON 字符串边界
- `context` 必须是文档中实际存在的文本片段的逐字复制
- `context` 禁止是概括性描述
- 同一文本多次出现时，使用 `occurrence` 字段（从1开始的整数）
- `old_text` 应尽量短小精悍，只包含需要替换/删除的最小文本片段
- `old_text`、`context`、`new_text` 禁止包含换行符 `\n`
- `context`、`old_text`、`highlight_text` 禁止包含 HTML/XML 标签
- `highlight_text` 用于 comment 类型时指定精准覆盖范围
- `paragraph_index` 表示段落索引（从0开始），无法确定填 null
- 合并后必须执行去重
- 每条审查意见必须有明确的 context
- 审查 Agent 必须执行自验证

---

## 文件命名规则

获取真实本地时间戳：
```bash
python -c "from datetime import datetime; print(datetime.now().astimezone().strftime('%Y%m%d_%H%M%S'))"
```

| 文件类型 | 命名格式 | 位置 |
|:-------|:-------|:-------|
| 工作文件夹 | `<input_dir>/<skill_name>_<timestamp>` | 输入文件同目录 |
| 提取文本 | `extracted_text_<timestamp>.txt` | `<work_dir>` |
| 摘要拆分 | `section_abstract_text_<timestamp>.json` | `<work_dir>` |
| 权利要求书拆分 | `section_claims_<timestamp>.json` | `<work_dir>` |
| 说明书拆分 | `section_description_<timestamp>.json` | `<work_dir>` |
| 说明书附图拆分 | `section_description_fig_<timestamp>.json` | `<work_dir>` |
| 摘要附图拆分 | `section_abstract_fig_<timestamp>.json` | `<work_dir>` |
| 章节摘要 | `header_sections_<timestamp>.json` | `<work_dir>` |
| 图片分析 | `image_analysis_<timestamp>.json` | `<work_dir>` |
| 审查意见 | `reviews_agent1~13_<timestamp>.json` | `<work_dir>` |
| 合并审查意见 | `reviews_<timestamp>.json` | `<work_dir>` |
| 审查版 docx | `<input_stem>_ReviewOut_<timestamp>.docx` | 输入文件同目录 |
| 跳过条目 | `skipped_reviews_<timestamp>.json` | `<work_dir>` |
| 合规检查日志 | `compliance_check_<timestamp>.json` | `<work_dir>` |
| 合规修复记录 | `compliance_fix_<timestamp>.json` | `<work_dir>` |
| BUG审查日志 | `<skill_name>_BUG_<timestamp>.json` | `<work_dir>` |

---

## 工作文件夹管理规则

- 所有中间产物必须放在 `<work_dir>` 下
- 最终审查版 docx 放在输入文件同目录下
- 工作文件夹必须创建在输入 docx 文件所在目录下
- 所有路径必须使用绝对路径
- 所有中间文件使用完毕后保留（"用完即保留"）
- 禁止子Agent自行删除/清理任何中间产物
- 禁止在 `<work_dir>` 以外的位置创建任何中间文件

---

## 脚本调用规则

- 禁止使用 `python -c` 执行多行 Python 代码
- 禁止将多行代码保存为独立脚本放在项目目录中（临时脚本必须放在 `<work_dir>` 中，修复完成后保留不删除）
- 禁止使用 bash 语法设置环境变量
- 必须使用 `python "<skill_root>/scripts/脚本名.py"` 直接调用
- 路径分隔符使用 `/`（跨平台兼容）
- `patent_extractor.py` 的 `--split-sections` 参数必须使用

---

## 验证步骤规则

验证为强制性，使用 `verify.py` 脚本执行三项验证：

```bash
python "<skill_root>/scripts/verify.py" "<input_doc>" "<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx" "<work_dir>"
```

**结果判定**：

| 验证项 | 性质 | 未通过处理 |
|:-----|:-----|:----------|
| 段落数量验证 | 硬性 | 必须排查修正 |
| 文件结构验证 | 硬性 | 必须排查修正 |
| 模拟接受修订 | 参考性 | 段落数不一致为已知误报 |

---

## 修订追踪规范

- 替换文本：`<w:del>` + `<w:delText>` + `<w:ins>` + `<w:t>`
- 删除文本：`<w:del>` + `<w:delText>`
- 必须保留原 run 的 rPr（格式属性）
- 最小化修改：只标记实际更改的文本