---
name: "checking-cn-patent-format"
description: |
  使用多Agent并行架构审查中国专利申请文件(.docx/.doc)，生成带修订追踪和批注的docx副本。当用户要求检查、审查、审阅或校对中国专利申请文件(.docx/.doc)时使用，尤其是用户明确要求使用多Agent模式或并行审查时使用。不要用于用户只想查看专利文档而不审查、输入文件不是.docx/.doc格式、或用户要求翻译专利文档的情况。
---

# 中国专利申请文件多Agent并行审查器

使用**多Agent分批并行架构**对中文专利申请文档（.docx / .doc）进行AI辅助审查。14条审查规则分配到13个审查Agent + N个图片审查子Agent分7批并行执行（每个Agent仅加载1条审查规则），文档提取、审查合并、图片context修复、批注添加和合规检查均委托给子Agent执行。主Agent仅负责编排、调度和关键决策。

> ⚠️ **.doc 格式支持**：本 skill 支持输入 `.doc` 格式文件。处理时会自动使用 pywin32（COM 自动化）调用 Microsoft Word 将 `.doc` 转换为 `.docx`。**要求**：Windows 系统 + 已安装 WPS 或 Microsoft Word  + 已安装 pywin32 库。

## 一、WHEN TO USE

- 用户要求检查、审查、审阅或校对中国专利申请 .docx 或 .doc 文件
- 用户提供中国专利申请 .docx 或 .doc 文件要求进行质量检查
- 用户希望发现中国专利申请文件中的撰写问题
- 用户明确要求使用多Agent模式或并行审查

## 二、DO NOT USE

- 用户只想查看或阅读专利文档，无需审查
- 输入文件不是 .docx 或 .doc 格式（如 .pdf、.txt）
- 用户咨询专利策略、可专利性分析或法律建议（本 skill 仅检查撰写质量）
- 用户要求翻译专利文档

## 三、INPUT / OUTPUT

### 3.1 本skill开始前的input

| 输入 | 类型 | 说明 |
|------|------|------|
| `input_doc` | 字符串 | 待审查的 .docx 或 .doc 文件的绝对路径 |

### 3.2 本skill完成工作后的output

| 输出 | 类型 | 说明 |
|------|------|------|
| `reviewed_docx` | 字符串 | 带修订追踪和批注的审查后 .docx 文件绝对路径 |
| `work_dir` | 字符串 | 包含所有中间文件的工作目录绝对路径 |

## 四、路径变量

| 变量 | 说明 | 示例 |
|:---|:---|:---|
| `<skill_name>` | Skill 名称，同时用作批注作者 | `checking-cn-patent-format` |
| `<skill_root>` | Skill 根目录 | `D:/path/to/.trae/skills/checking-cn-patent-format` |
| `<input_doc>` | 输入文件绝对路径 | `D:/docs/专利申请文件.docx` |
| `<input_dir>` | 输入文件所在目录 | `D:/docs` |
| `<input_stem>` | 输入文件名（不含扩展名） | `专利申请文件` |
| `<timestamp>` | 第5.2步获取的真实时间戳 | `20260511_143025` |
| `<work_dir>` | 工作目录 | `D:/docs/checking-cn-patent-format_20260511_143025` |

> 所有路径必须使用绝对路径，使用 `/` 作为路径分隔符以确保跨平台兼容性。

## 五、工作步骤

### 5.1 验证文件类型

检查输入文件扩展名是否为 `.docx` 或 `.doc`（不区分大小写）。如果不是，告知用户仅支持 .docx 和 .doc 格式后**终止**。

### 5.2 获取时间戳并创建工作目录（委托给子Agent）

执行命令获取真实本地时间戳：
```bash
python -c "from datetime import datetime; print(datetime.now().astimezone().strftime('%Y%m%d_%H%M%S'))"
```

将输出记录为 `<timestamp>`，定义 `<work_dir>` = `<input_dir>/<skill_name>_<timestamp>`，创建工作目录：`mkdir "<work_dir>"`。

### 5.3 提取文档文本并拆分章节（委托给子Agent）

> ⛔ 此步骤必须委托子Agent执行。主Agent禁止直接使用 RunCommand 调用 patent_extractor.py。

委托 `references/agent-extract.md` 中定义的文档提取Agent执行（`subagent_type: "subagent0"`，`response_language: "zh-CN"`）。

**验证输出**：确认 `<work_dir>` 中存在以下文件且内容非空：
- `extracted_text_<timestamp>.txt`
- `section_abstract_text_<timestamp>.json`（paragraphs 非空）
- `section_claims_<timestamp>.json`（paragraphs 非空）
- `section_description_<timestamp>.json`（paragraphs 非空）
- `section_description_fig_<timestamp>.json`
- `section_abstract_fig_<timestamp>.json`
- `header_sections_<timestamp>.json`
- `image_analysis_<timestamp>.json`

验证通过后立即进入第5.4步，不总结不暂停。

### 5.4 多子Agent并行审查（核心步骤）

13个审查Agent + N个图片审查子Agent分**7批**并行启动。每个Agent仅加载1条审查规则，仅读取分配的章节拆分文件（物理隔断）。

**子Agent提示词模板**（标准化简短模板，Agent自行从对应文件读取配置）：

```
你是一个专业且严格的中国专利审查员，熟知《专利法》、《专利法实施细则》和《专利审查指南》。
⛔⛔⛔ 禁止向用户提问、禁止要求用户提供任何信息、禁止因任何原因暂停审查流程。

请执行以下审查任务：
1. 读取通用规范：读取 "<skill_root>/references/common-specs.md" 的完整内容，严格遵守其中所有规范
2. 读取审查任务配置：读取 "<skill_root>/references/agent-NN.md" 的完整内容，获取你的专属任务配置和执行步骤
3. 按照通用规范和任务配置的指令执行审查
4. 路径变量：skill_root=<skill_root>, work_dir=<work_dir>, timestamp=<timestamp>
```

将 `NN` 替换为Agent编号（01-13）。

#### 审查任务分组与批次

| 批次 | Agent | 任务 | 规则文件 | 章节文件 |
|------|-------|------|----------|----------|
| **第1批** | Agent 1-2 | 摘要审查 | 11/12 | section_abstract_text |
| **第2批** | Agent 3-6 | 权利要求书简单审查 | 31系列×4 | section_claims |
| **第3批** | Agent 7-8 | 权利要求书复杂审查 | 32系列×2 | section_claims |
| **第4批** | Agent 9-10 | 说明书审查 | 41/42 | section_description |
| **第5批** | Agent 11-12 | 全文跨章节审查 | 61/62 | header_sections |
| **第6批** | Agent 13 | 附图元数据级审查 | 51 | section_description + section_description_fig + section_abstract_fig + image_analysis |
| **第7批** | 图片子Agent×N | 图片级审查 | 52 | 图片文件（主Agent动态创建） |

#### 分批启动规则

- 每批必须在同一条消息中并行启动该批次所有Agent（禁止逐个启动）
- 每批验证通过后**立即**在同一回复中启动下一批（不总结不暂停）
- 验证方式：确认输出JSON为有效数组，context字段非空
- 如果某Agent验证失败，重新启动该Agent

#### Agent输出质量验证

每批完成后立即验证（推荐）：
```bash
python "<skill_root>/scripts/output_validator.py" --work-dir "<work_dir>" --timestamp "<timestamp>" --agents <N,M,...> --extracted-text "<work_dir>/extracted_text_<timestamp>.txt"
```

全量验证（所有审查Agent完成后）：
```bash
python "<skill_root>/scripts/output_validator.py" --work-dir "<work_dir>" --timestamp "<timestamp>" --extracted-text "<work_dir>/extracted_text_<timestamp>.txt"
```

### 5.5 合并去重与修订冲突解决（委托给子Agent）

委托 `references/agent-merge.md` 中定义的合并去重Agent执行一体化合并去重。

验证输出确认 `<work_dir>/reviews_<timestamp>.json` 存在且为有效JSON数组后：

1. **图片类context修复**（委托 `references/agent-image-fix.md` 子Agent）：修复说明书附图类审查意见中非verbatim copy的context锚点
2. **批注添加**（顺序启动 `references/agent-annotate.md` 子Agent）：执行 `review_adder.py` 添加批注和修订追踪。注意：摘要附图section的批注不再寻找锚定文字，而是自动在摘要附图章节结尾插入"摘要附图批注"文字作为批注的锚定文字
3. **跳过条目保存**：被跳过的条目由 `references/agent-skip-save.md` 子Agent另存为 `<work_dir>/skipped_reviews_<timestamp>.json` 以备用户检查

### 5.6 添加批注修订（委托给子Agent）

委托 `references/agent-annotate.md` 中定义的批注添加Agent执行（如5.5中已顺序启动，此步骤作为验证/重试环节）。

验证批注输出确认 `<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx` 存在。如跳过数量>0，修复后重试（最多2次）。

> ⛔ 必须使用 `review_adder.py`。禁止编写自定义批注脚本——会导致严重内容丢失。

### 5.7 内容完整性验证（强制）

运行验证脚本：
```bash
python "<skill_root>/scripts/verify.py" "<input_doc>" "<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx" "<work_dir>"
```

验证脚本会自动将验证日志保存为 `<work_dir>/verify_log.json`，供后续合规检查和BUG审查使用。

**结果判定**：
- 段落数量验证 — **硬性**：必须通过，失败则排查修复后重新执行5.6和5.7
- 文件结构验证 — **硬性**：必须通过，失败则排查修复
- 模拟接受修订 — **参考性**：已知误报，段落数量通过则不算失败

> ⛔ 未通过硬性验证的文档禁止交付给用户。

### 5.8 跳过批注重定位（委托给子Agent）

> 本步骤在5.7内容完整性验证通过后执行，将批注添加过程中被跳过的条目重新定位到对应section章节结尾处。

委托 `references/agent-skip-relocate.md` 中定义的跳过批注重定位Agent执行（`subagent_type: "subagent0"`，`response_language: "zh-CN"`）。

**核心逻辑**：
1. 识别所有在前期处理中被标记为"跳过"状态的批注（从 `skipped_reviews_<timestamp>.json` 读取）
2. 针对每个被跳过的批注，定位其原始所属的section章节
3. 在相应section章节的结尾处，创建标准文本"额外批注"作为锚定文本
4. 以"额外批注"文本为定位点，添加原被跳过的批注内容
5. 确保新增批注与原文档内容格式保持一致，不影响文档整体结构
6. 记录所有重定位操作，在日志文件中注明原批注ID、原位置及新位置信息

**运行重定位脚本**：
```bash
python "<skill_root>/scripts/skip_relocator.py" --input-doc "<input_doc>" --reviewed-docx "<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx" --work-dir "<work_dir>" --timestamp "<timestamp>" --author "checking-cn-patent-format"
```

**验证输出**：
- 确认 `<work_dir>/relocation_log_<timestamp>.json` 存在且为有效JSON
- 确认 `<work_dir>/deduplicated_comments_<timestamp>.json` 存在且为有效JSON
- 确认审查后docx文件中包含"额外批注"锚定文本及关联批注

**输出文件说明**：
- `relocation_log_<timestamp>.json`：重定位操作日志，记录每条跳过批注的原位置、新位置、重定位时间戳
- `deduplicated_comments_<timestamp>.json`：去重后批注数据文件，完整保留所有经过去重处理后的有效批注内容，包含原始位置信息、内容、创建时间戳等关键元数据

> 注意：如果 `skipped_reviews_<timestamp>.json` 不存在或为空，脚本将直接生成空的重定位日志和去重批注数据文件，不视为错误。

### 5.8a 格式化审查输出JSON

运行格式化脚本确保所有审查Agent输出的JSON文件为标准缩进格式（indent=2）：

```bash
python "<skill_root>/scripts/format_json.py" --work-dir "<work_dir>"
```

验证：确认所有 `reviews_agent*_*.json` 文件已格式化为多行缩进格式（非单行）。

### 5.9 BUG审查与日志归档（收尾步骤，委托给子Agent）

> 本步骤在skill所有预设任务（含合规检查和合规修复）执行完成后，作为收尾步骤执行。

委托 `references/agent-bug-review-orchestrator.md` 中定义的BUG审查编排Agent执行（`subagent_type: "subagent0"`，`response_language: "zh-CN"`）。

编排Agent将根据 `<work_dir>` 中的文件数量和大小自动选择执行模式：
- **并行模式**（文件数>8或总大小>2MB）：将文件按功能类别分为2~4组，并行启动Worker Agent审查，最后整合去重生成最终日志
- **单Agent模式**（文件数≤8且总大小≤2MB）：直接委托 `references/agent-bug-review.md` 执行完整审查

**子Agent提示词模板**：

```
你是一个专业的技术审查与故障分析编排器，精通中国专利申请文件的审查流程和多Agent协作系统。

请执行以下BUG审查与归档任务：
1. 读取编排配置：读取 "<skill_root>/references/agent-bug-review-orchestrator.md" 的完整内容，获取你的专属任务配置和执行步骤
2. 按照编排配置的指令，扫描工作目录、判断执行模式、调度Worker Agent（并行模式）或直接审查（单Agent模式）
3. 收集并整合所有审查结果，对BUG去重合并，生成最终结构化BUG日志JSON文件并归档
4. 路径变量：skill_root=<skill_root>, work_dir=<work_dir>, timestamp=<timestamp>, skill_name=checking-cn-patent-format, input_doc=<input_doc>
5. ⛔⛔⛔ 禁止向用户提问、禁止要求用户提供任何信息、禁止因任何原因暂停审查流程
```

**验证输出**：确认 `<work_dir>/<skill_name>_BUG_<timestamp>.json` 存在且为有效JSON，且 `meta.review_mode` 字段为 `"parallel"` 或 `"single"`。

> 注意：即使本次执行未发现任何BUG，仍需生成完整的日志JSON文件（bugs数组为空），以建立执行记录档案。

> ⛔ **临时文件保留**：BUG审查过程中生成的临时文件 `bug_log_temp_<timestamp>.json` 在 `save_bug_log.py` 执行完成后必须保留在 `<work_dir>` 中，禁止删除，禁止询问用户是否删除，禁止因临时文件的存在而暂停流程。

## 六、最终输出

> `<model_name>` 替换为当前会话所使用的大模型名称。

```
📋 专利申请文件审查完成（多Agent分批并行协作模式）

审查文件：xxx.docx
发现问题：N 处
审查模式：13 个审查 Agent + N 个图片子Agent 分 7 批并行审查 + 7 个辅助 Agent
使用模型：<model_name>

【审查摘要】
- 摘要-简单审查：X1 处（Agent 1）
- 摘要-复杂审查：X2 处（Agent 2）
- 权利要求书-格式检查1：Y1 处（Agent 3）
- 权利要求书-格式检查2：Y2 处（Agent 4）
- 权利要求书-所述的引用基础：Y3 处（Agent 5）
- 权利要求书-引用与主题：Y4 处（Agent 6）
- 权利要求书-复杂审查1：Y5 处（Agent 7）
- 权利要求书-单一性审查：Y6 处（Agent 8）
- 说明书-简单审查：W1 处（Agent 9）
- 说明书-公开充分审查：W2 处（Agent 10）
- 全文-简单审查：V1 处（Agent 11）
- 全文-复杂审查：V2 处（Agent 12）
- 附图审查：Z 处（Agent 13 + N_fig 个图片子Agent）

已生成审查版文档：xxx_ReviewOut_<timestamp>.docx
审查意见汇总JSON：<work_dir>/reviews_<timestamp>.json
跳过条目（如有）：<work_dir>/skipped_reviews_<timestamp>.json
重定位日志（如有跳过）：<work_dir>/relocation_log_<timestamp>.json
去重批注数据：<work_dir>/deduplicated_comments_<timestamp>.json
中间文件保存在：<work_dir>

【审查质量指标】
- 批注添加成功率：Z%
- 跳过批注重定位：成功 X 条 / 失败 Y 条（详见 <work_dir>/relocation_log_<timestamp>.json）
- 合规检查结果：通过X项/警告Y项/错误Z项（详见 <work_dir>/compliance_check_<timestamp>.json）

【BUG审查结果】
- 审查模式：<parallel|single>（<N>个Worker并行 / 单Agent模式）
- 本次执行共发现 BUG：N 处（critical: X / major: Y / minor: Z）
- BUG日志已归档至：<work_dir>/checking-cn-patent-format_BUG_<timestamp>.json
```

> **合规检查**：最终输出前，启动 `references/agent-compliance-check.md` 子Agent检查整个执行过程的约束遵守情况，生成 `<work_dir>/compliance_check_<timestamp>.json`。然后启动 `references/agent-compliance-fix.md` 子Agent加载检查日志，对可修复问题当场整改并记录。
>
> **BUG审查与归档**：合规检查及修复完成后，启动 `references/agent-bug-review-orchestrator.md` 编排Agent。编排Agent根据文件数量自动选择模式：文件较多时并行调度 `references/agent-bug-review-worker.md` Worker Agent分2~4组审查，文件较少时回退到 `references/agent-bug-review.md` 单Agent模式。最终生成结构化分析日志并归档至 `<work_dir>/`。

## 七、关键约束

> ⛔ 以下为最关键约束。更多详细规则见 `references/prohibitions-and-rules.md`。

1. **流程完整性**：9个步骤必须不间断连续执行。禁止步骤间总结后停顿、禁止批次间等待、禁止文件冲突询问、禁止子Agent向用户提问。完成当前步骤后立即在同一回复中执行下一步。

2. **必须使用 review_adder.py 添加批注**：禁止编写自定义脚本处理批注或修订操作，会导致严重内容丢失。

3. **禁止跳过验证**（第5.7步）：段落数量和文件结构验证为硬性验证，未通过的文档禁止交付给用户。

4. **所有子Agent禁止向用户提问**：每个子Agent的query中必须包含此指令。遇到不确定情况时依据规则自行判断并继续执行。

5. **必须分批并行启动审查Agent**：禁止逐个串行启动。同一批次内必须在同一条消息中用多个并行Task调用同时启动。

## 八、故障的处理

| 故障 | 处理方式 |
|------|----------|
| 终端DLL初始化失败（退出码 -1073741510） | 立即停止重试（最多3次），记录当前状态，向用户报告并提供手动恢复命令 |
| 脚本执行超时/无响应 | 检查输入文件完整性，尝试在新终端重新执行该步骤 |
| JSON解析失败（Agent输出格式错误） | 读取被跳过的JSON文件，修复语法错误（中文引号、未转义双引号、括号匹配等），重新运行 |
| 批注添加大量跳过（成功率<80%） | 分析跳过原因（context verbatim/修订冲突/occurrence失效），按优先级修复后重试（最多2次） |
| 验证失败 | 排查原因（检查replace操作日志），修复对应审查意见后重新执行5.6和5.7（最多重试5次） |
| 跳过批注重定位失败 | 检查skipped_reviews文件格式和章节识别结果，重试5.8步骤（最多2次）；若仍失败，保留原跳过条目供用户手动检查 |

> 更多故障处理详情见 `references/fault-handling.md`。

## 九、参考文件

| 文件 | 用途 | 加载时机 |
|------|------|----------|
| `references/common-specs.md` | 所有审查Agent共用的通用规范（JSON格式、context约束、自检清单等） | 审查Agent启动时 |
| `references/agent-01.md` ~ `agent-13.md` | 13个审查Agent的独立任务配置（物理隔断） | 对应Agent启动时 |
| `references/agent-fig-review.md` | 图片审查子Agent任务配置 | 第7批图片子Agent启动时 |
| `references/agent-extract.md` | 文档提取Agent任务配置 | 第5.3步 |
| `references/agent-merge.md` | 合并去重Agent任务配置 | 第5.5步 |
| `references/agent-image-fix.md` | 图片类context修复Agent任务配置 | 第5.5步（合并后） |
| `references/agent-annotate.md` | 批注添加Agent任务配置 | 第5.5步（图片修复后）/第5.6步 |
| `references/agent-skip-save.md` | 跳过条目保存Agent任务配置 | 第5.5步（批注完成后） |
| `references/agent-skip-relocate.md` | 跳过批注重定位Agent任务配置 | 第5.8步 |
| `references/agent-compliance-check.md` | 合规检查Agent任务配置 | 最终输出前 |
| `references/agent-compliance-fix.md` | 合规修复Agent任务配置 | 合规检查后 |
| `references/agent-bug-review.md` | BUG审查与归档Agent任务配置（单Agent模式/Fallback） | 第5.9步（收尾，文件少时） |
| `references/agent-bug-review-orchestrator.md` | BUG审查编排Agent任务配置（并行模式调度器） | 第5.9步（收尾，文件多时） |
| `references/agent-bug-review-worker.md` | BUG审查工作Agent任务配置（并行Worker） | 第5.9步（由编排器调度） |
| `references/prohibitions-and-rules.md` | 详细禁止事项和规则 | 执行过程中按需加载 |
| `references/fault-handling.md` | 详细故障处理方式 | 遇到未预期的故障时加载 |
| `references/context_anchoring_guide.md` | Context锚定最佳实践指南 | 审查Agent遇到锚定困难时参考 |
| `references/output_template_v2.json` | 标准化输出格式模板 | 审查Agent输出前参考 |
| `references/deduplicated_comments.json` | 去重后批注数据存储模板 | 第5.8步生成去重批注数据时参考 |
| `references/technical.md` | OOXML批注注入技术参考 | 开发调试时参考 |

## 十、技术架构

```
checking-cn-patent-format/
├── SKILL.md                                  # 主控制文件（本文档）
├── requirements.txt                          # Python依赖
├── references/
│   ├── common-specs.md                       # 通用规范（所有审查Agent共用）
│   ├── agent-01.md ~ agent-13.md             # 13个审查Agent独立配置（物理隔断）
│   ├── agent-fig-review.md                   # 图片审查子Agent配置
│   ├── agent-extract.md                      # 文档提取Agent配置
│   ├── agent-merge.md                        # 合并去重Agent配置
│   ├── agent-image-fix.md                    # 图片context修复Agent配置（新增）
│   ├── agent-annotate.md                     # 批注添加Agent配置
│   ├── agent-skip-save.md                    # 跳过条目保存Agent配置（新增）
│   ├── agent-skip-relocate.md                # 跳过批注重定位Agent配置（新增）
│   ├── agent-compliance-check.md             # 合规检查Agent配置（新增）
│   ├── agent-compliance-fix.md               # 合规修复Agent配置（新增）
│   ├── agent-bug-review.md                   # BUG审查与归档Agent配置（单Agent模式/Fallback）
│   ├── agent-bug-review-orchestrator.md      # BUG审查编排Agent配置（并行模式调度器）
│   ├── agent-bug-review-worker.md            # BUG审查工作Agent配置（并行Worker）
│   ├── prohibitions-and-rules.md             # 详细禁止事项与规则
│   ├── fault-handling.md                     # 详细故障处理参考
│   ├── context_anchoring_guide.md           # Context锚定最佳实践指南
│   ├── output_template_v2.json               # 标准化输出格式模板
│   ├── deduplicated_comments.json            # 去重后批注数据存储模板（新增）
│   └── technical.md                          # OOXML批注注入技术参考（新增）
├── scripts/
│   ├── patent_extractor.py                   # 文档提取与章节拆分
│   ├── review_adder.py                       # 批注与修订追踪添加
│   ├── merge_reviews.py                      # 合并去重与冲突解决
│   ├── verify.py                             # 内容完整性验证
│   ├── skip_relocator.py                     # 跳过批注重定位（新增）
│   ├── format_json.py                        # JSON文件格式化（indent=2）
│   ├── save_bug_log.py                       # BUG日志JSON格式化写入
│   ├── output_validator.py                   # Agent输出JSON验证器
│   ├── doc_converter.py                      # .doc转.docx（COM自动化）
│   ├── document.py                           # docx文档操作底层
│   ├── utilities.py                          # 工具函数
│   ├── error_handling.py                     # 自定义异常类 + 批注日志记录器（新增）
│   ├── workflow.py                           # 工作流编排类（新增）
│   ├── patent_analyzer.py                    # 专利文档智能分析器（新增）
│   ├── report_renderer.py                    # 审查报告/摘要DOCX生成（新增）
│   └── templates/                            # OOXML模板
├── ooxml/
│   └── scripts/
│       ├── unpack.py / pack.py               # OOXML打包/解包
│       └── validation/                       # 文档验证
└── Checking Rules/
    ├── 11-摘要-简单检查1.md
    ├── 12-摘要-复杂检查1.md
    ├── 31-权利要求书简单审查1~4/
    ├── 32-权利要求书复杂审查1~2/
    ├── 41-说明书-简单审查1.md
    ├── 42-说明书-复杂审查1-说明书公开是否充分.md
    ├── 51-附图-简单检查1.md
    ├── 52-附图-图片检查1.md
    ├── 61-全文-简单审查1.md
    └── 62-全文-复杂审查1.md
```

## 十一、依赖项

- Python 3.10+
- defusedxml — XML安全解析
- lxml — OOXML操作
- python-docx — docx文档读写
- Pillow>=10.0.0 — 图片质量分析（Agent 13图片子Agent使用）
- numpy — 图片清晰度/对比度计算
- pywin32 — .doc转.docx（仅Windows + Microsoft Word环境需要）

## 十二、容错机制与错误处理（v2.1增强版）

### 12.1 已知错误类型与防护措施

| 错误编号 | 错误类型 | 严重级别 | 影响范围 | 修复状态 |
|---------|---------|---------|---------|---------|
| BUG-001/002 | Agent输出空数组 | Critical | 审查维度缺失 | ✅ output_validator.py已升级为ERROR级 |
| BUG-006 | 零段落章节(摘要附图)检测失败 | Critical | 摘要附图批注100%失败 | ✅ review_adder.py+skip_relocator.py已修复 |
| BUG-003 | 图片子Agent空输出 | Major | 图片质量检查缺失 | ⚠️ 部分修复(Pillow预检) |
| BUG-007 | 去重不完整(context相同未去重) | Major | 冗余审查意见残留 | ✅ merge_reviews.py新增context精确匹配策略 |
| BUG-008 | Pillow依赖缺失无预警 | Minor | 图片元数据降级 | ✅ patent_extractor.py新增环境健康检查 |

### 12.2 环境健康检查流程（Step 5.3增强）

在执行 `patent_extractor.py` 时，脚本会自动运行 `check_environment_health()` 并输出：
```
📋 环境健康检查:
  ✅ pillow (v10.2.0) [必需]
  ✅ lxml (v5.1.0) [必需]
  ❌ defusedxml [必需]
  ⚠️ 缺少 1 个必需依赖: defusedxml
     修复: pip install 'defusedxml>=0.7.1'
```

**处理规则**：
- 若Pillow缺失 → 图片元数据降级为文件大小+格式，图片质量审查Agent结果可信度降低
- 若lxml/defusedxml缺失 → 文档提取完全失败，必须终止流程
- **建议在Step 5.2之后立即调用环境检查，发现严重依赖问题时提前终止**

### 12.3 Agent输出质量保障（Step 5.4增强）

每个Agent输出经过 `output_validator.py` 验证时：
- **空数组**：从WARNING升级为 **ERROR**，标记该Agent对应审查维度完全缺失
- **空数组处理策略**：
  1. 记录到验证日志，标注 `false_negative_risk: high`
  2. 在最终报告中明确列出"未覆盖的审查维度"
  3. 建议对空输出Agent进行单次重试（最多1次）

### 12.4 零段落章节处理（BUG-006修复说明）

**问题根因**：`_find_section_boundaries()` 通过扫描段落文本检测章节名称。
摘要附图章节的 `paragraph_count=0`（仅含图片），文本扫描无法匹配。

**修复方案**：
1. `_find_section_boundaries(paragraphs, known_sections=None)` 新增可选参数
2. 从 `header_sections_*.json` 加载已知章节元数据（含零段落信息）
3. 对零段落章节根据其在元数据中的序号推断位置

**涉及文件**：
- `scripts/review_adder.py` — 批注注入时自动加载header_sections.json
- `scripts/skip_relocator.py` — 跳过批注重定位时同样加载
- 两文件函数保持同步（版本标记: v2.1-BUG006-fix）

### 12.5 去重策略优先级（BUG-007修复说明）

修复后的去重策略执行顺序：

| 优先级 | 策略名称 | 匹配条件 | 说明 |
|-------|---------|---------|------|
| P0（最高） | context精确匹配 | context字段完全相同 | 【新增】同位置必去重 |
| P1 | 精确去重 | context + issue + old_text完全相同 | 原有最高优先级 |
| P2 | 语义去重 | old_text相同 + section相同 + context相似>0.8 | 原有 |
| P3-P7 | 包含关系/Issue语义/跨章vs单章/位置邻近/交叉引用 | （不变） | 原有 |

### 12.6 代码同步管理

以下函数在多文件中存在逻辑副本，修改时需同步更新：
| 函数名 | 所在文件 | 同步版本 |
|-------|---------|---------|
| `_find_section_boundaries()` | review_adder.py, skip_relocator.py | v2.1-BUG006-fix |
| `_detect_section()` | review_adder.py, skip_relocator.py | v2.1-BUG006-fix |
| `_get_para_text()` | review_adder.py, skip_relocator.py | v2.1-BUG006-fix |