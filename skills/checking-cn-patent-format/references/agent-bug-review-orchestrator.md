# BUG审查编排 Agent（Orchestrator）

> 本Agent在skill所有预设任务执行完成后作为收尾步骤的编排器执行，负责扫描工作目录、智能分割文件组、并行调度Worker Agent、收集整合审查结果并生成最终结构化BUG日志。

## 配置信息

| 项目 | 值 |
|------|-----|
| 角色 | 编排器（Orchestrator），不直接审查文件，仅负责调度和整合 |
| 审查范围 | 通过Worker Agent间接覆盖本次skill完整执行过程中的所有BUG |
| 信息来源 | `<work_dir>` 下所有中间文件（通过Worker分组读取） |
| Worker配置 | `<skill_root>/references/agent-bug-review-worker.md` |
| 单Agent回退配置 | `<skill_root>/references/agent-bug-review.md` |
| 输出路径 | `<work_dir>` |
| 输出文件 | `<skill_name>_BUG_<timestamp>.json` |

## 执行前检查清单

- [ ] 确认 `<work_dir>` 存在且包含本次执行的完整中间文件
- [ ] 确认 `<work_dir>` 存在（输出目录即工作目录，已由前置步骤创建）
- [ ] 确认 `<skill_name>` 为 `checking-cn-patent-format`
- [ ] 确认 `<timestamp>` 为本次执行的时间戳
- [ ] 确认 Worker 配置文件 `<skill_root>/references/agent-bug-review-worker.md` 存在
- [ ] 确认单Agent回退配置 `<skill_root>/references/agent-bug-review.md` 存在

## 执行步骤

### 1. 扫描工作目录并枚举文件

遍历 `<work_dir>` 下的所有文件，构建文件清单。对每个文件记录：
- 文件名
- 文件大小（字节）
- 文件类型分类（见下方分类表）

**文件功能分类表**：

| 分类标签 | 文件模式 | 说明 |
|----------|----------|------|
| `compliance` | `compliance_check_<timestamp>.json`, `compliance_fix_<timestamp>.json` | 合规检查与修复 |
| `agent_output` | `reviews_agent1~13_<timestamp>.json`, `reviews_fig_*.json` | 审查Agent输出 |
| `merge_annotation` | `reviews_<timestamp>.json`, `skipped_reviews_<timestamp>.json` | 合并去重与批注 |
| `extraction` | `extracted_text_<timestamp>.txt`, `section_*_<timestamp>.json`, `header_sections_<timestamp>.json` | 文档提取与章节拆分 |
| `image` | `image_analysis_<timestamp>.json`, 图片文件 | 图片分析 |
| `verification` | 验证脚本输出日志（如有） | 内容完整性验证 |
| `conversion` | doc转换相关文件（如有） | .doc格式转换 |

### 2. 判断执行模式

根据文件数量和总大小决定执行模式：

**判定规则**：

```
if 文件总数 <= 8 AND 总大小 <= 2MB:
    执行模式 = "single"（单Agent模式）
else:
    执行模式 = "parallel"（并行模式）
```

- **单Agent模式**：直接委托 `<skill_root>/references/agent-bug-review.md` 执行完整审查，本编排器不做分组调度
- **并行模式**：继续执行步骤3~7

### 3. 文件分组（并行模式）

将文件按功能类别分为2~4个Worker组。分组策略遵循以下原则：

**3.1 固定分组模板**：

| 组别 | 包含的分类标签 | Worker职责 |
|------|---------------|-----------|
| **Group A** | `compliance` | 合规检查与修复BUG审查 |
| **Group B** | `agent_output` | 审查Agent输出BUG审查 |
| **Group C** | `merge_annotation`, `verification` | 合并批注与验证BUG审查 |
| **Group D** | `extraction`, `image`, `conversion` | 提取与图片BUG审查 |

**3.2 自适应调整规则**：

- 如果某个Group包含的文件总大小 > 3MB，将该Group按文件进一步拆分为2个子组
- 如果某个Group无对应文件（如无conversion文件），跳过该Group
- 最终Worker数量 = 实际有文件的Group数量（2~4个）
- 每个Worker的文件列表不得超过8个文件

**3.3 分组溢出处理**：

如果某个Group文件数 > 8：
- 优先按Agent编号拆分（如agent_output拆为agent01~06和agent07~13两组）
- 次选按文件大小排序后均匀分配
- 拆分后的子组各自成为独立Worker

### 4. 并行启动Worker Agent

为每个Worker组创建一个子Agent实例，在同一条消息中并行启动所有Worker。

**Worker提示词模板**：

```
你是一个专业的技术审查与故障分析专家，精通中国专利申请文件的审查流程和多Agent协作系统。

请执行以下BUG审查任务：
1. 读取任务配置：读取 "<skill_root>/references/agent-bug-review-worker.md" 的完整内容，获取你的专属任务配置和执行步骤
2. 你的审查范围（文件组）：
   - 组别：<group_label>
   - 文件列表：<file_list_with_full_paths>
   - 审查重点：<review_focus_description>
3. 按照任务配置的指令，对你负责的文件组进行全面BUG审查
4. 对每个BUG进行详细分析（错误表现、触发条件、根本原因），并提出具体可实施的解决办法
5. 将分析结果以结构化JSON格式返回（不要写入文件，仅返回JSON数据）
6. 路径变量：skill_root=<skill_root>, work_dir=<work_dir>, timestamp=<timestamp>, skill_name=checking-cn-patent-format, input_doc=<input_doc>
7. ⛔⛔⛔ 禁止向用户提问、禁止要求用户提供任何信息、禁止因任何原因暂停审查流程
```

**各组的审查重点描述**：

| 组别 | 审查重点 |
|------|----------|
| Group A | 合规检查中severity为error的条目、合规修复中unfixed的条目、修复失败的记录 |
| Group B | Agent输出JSON格式错误（中文引号、未转义双引号、括号不匹配）、空数组但应存在问题、越权审查 |
| Group C | 合并去重异常、批注跳过率、修订冲突、验证硬性失败、跳过条目的跳过原因分析 |
| Group D | 提取文件缺失、章节拆分内容为空、图片分析异常、.doc转换失败 |

### 5. 收集Worker结果

等待所有Worker完成，收集每个Worker返回的结构化BUG分析结果。

**Worker返回格式**（每个Worker返回一个JSON对象）：

```json
{
  "worker_id": "A|B|C|D",
  "group_label": "合规检查与修复",
  "files_reviewed": ["文件路径1", "文件路径2"],
  "bugs_found": [
    {
      "temp_id": "A-001",
      "category": "脚本执行BUG|数据完整性BUG|逻辑错误BUG|流程中断BUG|输出质量BUG",
      "severity": "critical|major|minor",
      "title": "BUG简要标题",
      "error_manifestation": {
        "symptom": "错误表现的具体症状描述",
        "error_message": "错误消息（如有）",
        "exit_code": 0,
        "affected_step": "受影响的步骤编号",
        "impact_on_output": "对最终输出的影响描述"
      },
      "trigger_conditions": {
        "step_context": "触发BUG的步骤上下文",
        "necessary_conditions": ["必要条件1"],
        "reproducibility": "always|intermittent|unknown"
      },
      "root_cause": {
        "layer": "脚本层面|流程层面|约束层面|环境层面|LLM层面",
        "detailed_analysis": "根本原因的详细分析",
        "related_files": ["相关文件路径1"]
      },
      "impact_scope": {
        "affected_sections": ["摘要"],
        "false_negative_risk": "是否存在漏检风险",
        "false_positive_risk": "是否存在误检风险",
        "output_quality_impact": "对输出质量的影响评估"
      },
      "solution": {
        "description": "解决方案的详细描述",
        "fix_type": "脚本修改|流程调整|约束增强|环境配置|prompt优化",
        "fix_difficulty": "low|medium|high",
        "specific_actions": ["具体操作步骤1"],
        "preventive_measures": ["预防措施1"]
      }
    }
  ],
  "execution_summary_partial": {
    "files_checked": 0,
    "files_with_issues": 0,
    "bugs_count": 0
  }
}
```

### 6. 整合与去重

**6.1 BUG去重**：

多个Worker可能报告同一BUG的不同方面。去重规则：
- 如果两个BUG的 `affected_step` 相同且 `root_cause.layer` 相同且 `title` 语义相似，视为同一BUG
- 合并策略：保留信息更完整的记录，将另一条记录的补充信息合并进去
- 合并后的BUG按 `severity` 降序排列（critical → major → minor）

**6.2 BUG重新编号**：

去重后的BUG按全局顺序重新编号：`BUG-001`、`BUG-002`、...

**6.3 统计信息汇总**：

从所有Worker结果中汇总：
- `steps_completed`：根据 `<work_dir>` 中实际存在的文件推断
- `steps_failed`：根据缺失的预期文件推断
- `agents_total`：根据存在的 `reviews_agentN_*.json` 文件数量
- `agents_failed`：根据格式错误的Agent输出文件数量
- `annotation_success_rate`：从批注添加日志中提取
- `compliance_errors`：从合规检查日志中统计
- `compliance_warnings`：从合规检查日志中统计
- `skipped_reviews_count`：从跳过条目文件中统计

### 7. 生成最终BUG日志JSON

将整合后的结果写入 `<work_dir>/<skill_name>_BUG_<timestamp>.json`：

```json
{
  "meta": {
    "skill_name": "checking-cn-patent-format",
    "timestamp": "<timestamp>",
    "execution_time": "<本次执行开始到结束的时间范围>",
    "input_file": "<input_doc>",
    "work_dir": "<work_dir>",
    "model": "<当前使用的大模型名称>",
    "total_bugs_found": 0,
    "analysis_generated_at": "<生成此分析报告的时间戳>",
    "review_mode": "parallel",
    "worker_count": 0,
    "workers_completed": 0
  },
  "execution_summary": {
    "steps_completed": ["5.1", "5.2"],
    "steps_failed": [],
    "agents_total": 0,
    "agents_failed": 0,
    "annotation_success_rate": 0,
    "compliance_errors": 0,
    "compliance_warnings": 0,
    "skipped_reviews_count": 0
  },
  "bugs": [],
  "statistics": {
    "bugs_by_category": {
      "脚本执行BUG": 0,
      "数据完整性BUG": 0,
      "逻辑错误BUG": 0,
      "流程中断BUG": 0,
      "输出质量BUG": 0
    },
    "bugs_by_severity": {
      "critical": 0,
      "major": 0,
      "minor": 0
    },
    "bugs_by_root_cause_layer": {
      "脚本层面": 0,
      "流程层面": 0,
      "约束层面": 0,
      "环境层面": 0,
      "LLM层面": 0
    }
  },
  "worker_reports": [
    {
      "worker_id": "A",
      "group_label": "合规检查与修复",
      "files_reviewed": [],
      "bugs_contributed": 0
    }
  ]
}
```

**JSON文件写入要求**：
- ⛔⛔⛔ **必须使用 `save_bug_log.py` 脚本写入文件，禁止使用Write工具直接写入**（会导致JSON堆在一行）
- 写入方式：先将完整JSON数据写入临时文件 `<work_dir>/bug_log_temp_<timestamp>.json`，然后执行：
  ```bash
  python "<skill_root>/scripts/save_bug_log.py" --input "<work_dir>/bug_log_temp_<timestamp>.json" --output "<work_dir>/<skill_name>_BUG_<timestamp>.json"
  ```
- 禁止将整个JSON写成1行
- 禁止在字符串值中使用未转义的双引号
- ⛔⛔⛔ **临时文件 `bug_log_temp_<timestamp>.json` 在 `save_bug_log.py` 执行完成后必须保留在 `<work_dir>` 中，禁止删除，禁止询问用户是否删除，禁止因临时文件的存在而暂停流程或要求用户清理**

### 8. 输出BUG审查摘要

生成BUG日志后，向主Agent返回以下摘要信息：

```
🐛 BUG审查与归档完成（并行模式，N个Worker）

本次执行共发现 BUG：N 处
- critical: X 处 | major: Y 处 | minor: Z 处

BUG分类统计：
- 脚本执行BUG：X1 处
- 数据完整性BUG：X2 处
- 逻辑错误BUG：X3 处
- 流程中断BUG：X4 处
- 输出质量BUG：X5 处

根本原因分布：
- 脚本层面：Y1 处
- 流程层面：Y2 处
- 约束层面：Y3 处
- 环境层面：Y4 处
- LLM层面：Y5 处

Worker执行情况：
- Worker A（合规检查与修复）：审查 N 个文件，发现 X 处BUG
- Worker B（审查Agent输出）：审查 N 个文件，发现 X 处BUG
- Worker C（合并批注与验证）：审查 N 个文件，发现 X 处BUG
- Worker D（提取与图片）：审查 N 个文件，发现 X 处BUG

去重合并：N 处重复BUG已合并
BUG日志已归档至：<work_dir>/<skill_name>_BUG_<timestamp>.json
```

## 执行后自检清单

- [ ] BUG日志JSON已生成且格式有效
- [ ] 所有Worker的结果已收集
- [ ] BUG去重已完成，无重复条目
- [ ] BUG编号连续且从BUG-001开始
- [ ] 统计信息与BUG列表一致
- [ ] meta中review_mode为"parallel"或"single"
- [ ] worker_reports数组包含所有Worker的执行摘要
- [ ] 输出目录路径正确

## 专属约束

- 本Agent不直接审查文件内容，仅负责编排调度和结果整合
- 所有文件审查工作委托给Worker Agent执行
- 如果判定为单Agent模式，委托给 `<skill_root>/references/agent-bug-review.md` 执行
- Worker必须在同一条消息中并行启动，禁止逐个串行启动
- 如果某个Worker执行失败，重新启动该Worker（最多2次），不影响其他Worker
- 如果Worker重试仍失败，该Worker负责的文件组标记为"审查不完整"，在最终报告中注明
- 不得向用户提问，不得要求用户提供额外信息
- 即使本次执行未发现任何BUG，仍需生成完整的日志JSON（bugs数组为空）
- ⛔⛔⛔ **临时文件保留规则**：`bug_log_temp_<timestamp>.json` 在 `save_bug_log.py` 执行完成后必须保留在 `<work_dir>` 中。禁止删除该临时文件，禁止询问用户是否删除，禁止因临时文件的存在而暂停流程或要求用户清理。所有中间产物遵循"用完即保留"原则
- 本Agent执行完成后立即结束，返回摘要信息给主Agent
