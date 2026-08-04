# BUG审查与归档 Agent（单Agent模式 / Fallback）

> **收尾步骤**：本Agent在skill所有预设任务执行完成后作为最后一个步骤执行，全面审查本次完整执行过程中出现的所有BUG，生成结构化分析日志并归档。

> **模式说明**：本文件为**单Agent模式**配置，由编排器（`agent-bug-review-orchestrator.md`）在文件数量较少（≤8个文件且总大小≤2MB）时作为fallback委托执行。当文件数量较多时，编排器将使用并行模式（`agent-bug-review-worker.md`）分Worker执行审查。主Agent直接委托本文件时，始终使用单Agent模式。

## 配置信息

| 项目 | 值 |
|------|-----|
| 审查模式 | 单Agent模式（Fallback） |
| 编排器 | `<skill_root>/references/agent-bug-review-orchestrator.md` |
| 并行Worker | `<skill_root>/references/agent-bug-review-worker.md` |
| 审查范围 | 本次skill完整执行过程中出现的所有BUG、异常、故障、错误 |
| 信息来源 | `<work_dir>` 下所有中间文件、合规检查日志、跳过条目、验证结果、各Agent输出 |
| 输出路径 | `<work_dir>` |
| 输出文件 | `<skill_name>_BUG_<timestamp>.json` |

## 执行前检查清单

- [ ] 确认 `<work_dir>` 存在且包含本次执行的完整中间文件
- [ ] 确认 `<work_dir>` 存在（输出目录即工作目录，已由前置步骤创建）
- [ ] 确认 `<skill_name>` 为 `checking-cn-patent-format`
- [ ] 确认 `<timestamp>` 为本次执行的时间戳

## 执行步骤

### 1. 收集BUG信息来源

遍历 `<work_dir>` 下的所有文件，重点关注以下BUG信息源：

**1.1 合规检查日志**：
- 读取 `<work_dir>/compliance_check_<timestamp>.json`，提取所有 `severity: "error"` 的条目
- 提取所有 `severity: "warning"` 的条目中与BUG相关的记录

**1.2 合规修复记录**：
- 读取 `<work_dir>/compliance_fix_<timestamp>.json`，提取所有 `status: "unfixed"` 的条目
- 提取 `result: "failure"` 的修复尝试

**1.3 跳过条目**：
- 读取 `<work_dir>/skipped_reviews_<timestamp>.json`（如存在），分析每条被跳过审查意见的跳过原因
- 分类统计跳过原因：修订冲突、context不存在、verbatim不匹配、occurrence失效、跨段落等

**1.4 验证结果**：
- 检查 verify.py 的执行输出，提取段落数量验证、文件结构验证、模拟接受修订的失败信息
- 如果验证日志存在于 `<work_dir>` 中，解析其中的错误详情

**1.5 审查Agent输出**：
- 检查13个审查Agent的输出JSON文件（`reviews_agent1~13_<timestamp>.json`），验证JSON格式有效性
- 标记存在格式错误（中文引号、未转义双引号、括号不匹配等）的Agent输出

**1.6 图片审查子Agent输出**：
- 检查图片子Agent的输出文件，标记任何异常

**1.7 批注添加日志**：
- 检查 review_adder.py 的执行输出，提取批注添加成功率、跳过数量、替换失败数量

**1.8 文档转换问题**（如适用）：
- 如果输入为 .doc 文件，检查 doc_converter.py 的执行是否有异常

### 2. BUG识别与分类

对收集到的所有问题进行去重和归类，识别真正的BUG。BUG识别标准：

| BUG类别 | 识别标准 |
|---------|----------|
| **脚本执行BUG** | 脚本返回非零退出码、抛出未捕获异常、输出结果与预期不符 |
| **数据完整性BUG** | 中间文件缺失、JSON解析失败、内容截断或损坏 |
| **逻辑错误BUG** | 审查意见矛盾、suggestion方向错误、context锚定失败 |
| **流程中断BUG** | 步骤执行中断、Agent超时、终端故障导致的流程断裂 |
| **输出质量BUG** | 批注跳过率过高（>20%）、验证硬性失败、合规检查error |

### 3. 逐BUG详细分析

对每个识别出的BUG执行以下详细分析，记录到结构化数据中：

**3.1 错误表现**：
- 描述BUG在skill执行过程中表现出的具体症状
- 记录相关的错误消息、退出码、异常堆栈（如有）
- 说明BUG对最终输出的影响程度

**3.2 触发条件**：
- 分析BUG出现的具体步骤和上下文
- 识别触发BUG的必要条件（如特定输入文件特征、特定审查规则组合、特定Agent的执行顺序）
- 判断BUG是否为间歇性（偶发）还是可稳定复现

**3.3 根本原因**：
- 追溯BUG产生的根本原因，区分以下层面：
  - **脚本层面**：Python脚本逻辑缺陷、边界条件未处理
  - **流程层面**：步骤编排不合理、Agent间数据传递问题
  - **约束层面**：约束规则矛盾或不足
  - **环境层面**：系统环境依赖问题、第三方库缺陷
  - **LLM层面**：Agent输出不可控、prompt歧义导致的偏差

**3.4 影响范围**：
- 评估BUG影响的审查结果类别（摘要/权利要求书/说明书/附图/全文）
- 评估是否导致漏检或误检
- 评估对最终docx输出的影响

### 4. 提出解决方案

对每个BUG提出具体、可实施的解决办法：

**4.1 解决方案描述**：
- 给出明确的修复操作步骤
- 如涉及脚本修改，说明修改的具体位置和逻辑
- 如涉及流程调整，说明调整后的步骤编排

**4.2 修复难度评估**：
- `low`：可通过调整约束规则或参数快速修复
- `medium`：需修改脚本逻辑或调整Agent配置
- `high`：涉及架构性调整或外部依赖变更

**4.3 预防措施**：
- 提出防止同类BUG再次发生的机制建议
- 如需要新增验证步骤或约束规则，明确说明

### 5. 生成结构化BUG日志JSON

将分析结果写入 `<work_dir>/<skill_name>_BUG_<timestamp>.json`：

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
    "review_mode": "single"
  },
  "execution_summary": {
    "steps_completed": ["5.1", "5.2", "..."],
    "steps_failed": [],
    "agents_total": 0,
    "agents_failed": 0,
    "annotation_success_rate": 0,
    "compliance_errors": 0,
    "compliance_warnings": 0,
    "skipped_reviews_count": 0
  },
  "bugs": [
    {
      "bug_id": "BUG-001",
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
        "necessary_conditions": ["必要条件1", "必要条件2"],
        "reproducibility": "always|intermittent|unknown"
      },
      "root_cause": {
        "layer": "脚本层面|流程层面|约束层面|环境层面|LLM层面",
        "detailed_analysis": "根本原因的详细分析",
        "related_files": ["相关文件路径1"]
      },
      "impact_scope": {
        "affected_sections": ["摘要", "权利要求书"],
        "false_negative_risk": "是否存在漏检风险",
        "false_positive_risk": "是否存在误检风险",
        "output_quality_impact": "对输出质量的影响评估"
      },
      "solution": {
        "description": "解决方案的详细描述",
        "fix_type": "脚本修改|流程调整|约束增强|环境配置|prompt优化",
        "fix_difficulty": "low|medium|high",
        "specific_actions": ["具体操作步骤1", "具体操作步骤2"],
        "preventive_measures": ["预防措施1", "预防措施2"]
      }
    }
  ],
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
  }
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

### 6. 输出BUG审查摘要

生成BUG日志后，向主Agent返回以下摘要信息：

```
🐛 BUG审查与归档完成

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

BUG日志已归档至：<work_dir>/<skill_name>_BUG_<timestamp>.json
```

## 执行后自检清单

- [ ] BUG日志JSON已生成且格式有效
- [ ] 所有BUG信息来源已检查
- [ ] 每条BUG记录包含完整的分析字段
- [ ] 每个BUG都有对应的解决方案
- [ ] 统计信息与BUG列表一致
- [ ] 输出目录路径正确

## 专属约束

- 本Agent在所有其他步骤（包括合规检查和合规修复）完成后执行
- 仅分析已发生的BUG，不修改任何中间文件或脚本源码
- 如果执行过程中未发现任何BUG，仍生成完整的日志JSON（bugs数组为空，meta和execution_summary正常填写）
- 不得向用户提问，不得要求用户提供额外信息
- 所有分析基于 `<work_dir>` 中实际存在的文件，不得臆测
- ⛔⛔⛔ **临时文件保留规则**：`bug_log_temp_<timestamp>.json` 在 `save_bug_log.py` 执行完成后必须保留在 `<work_dir>` 中。禁止删除该临时文件，禁止询问用户是否删除，禁止因临时文件的存在而暂停流程或要求用户清理。所有中间产物遵循"用完即保留"原则
- 本Agent执行完成后立即结束，返回摘要信息给主Agent