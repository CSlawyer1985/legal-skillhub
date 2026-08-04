---
name: patent-landscape
description: 当分析生物技术专利格局、识别药物知识产权中的空白领域、追踪竞争对手专利或评估药物开发的自由操作空间时使用。为生命科学创新提供全面的专利分析和战略洞察。
license: MIT
skill-author: AIPOCH
displayName: "生物医药专利格局分析"
version: "1.0.3"
slug: patent-landscape
---
# 生物技术专利格局分析器

分析生物技术和制药专利格局，以识别机会、评估竞争态势并指导研发战略。

## 使用场景

- 当任务需要分析生物技术专利格局、识别药物知识产权中的空白领域、追踪竞争对手专利或评估药物开发的自由操作空间时，使用此技能。为生命科学创新提供全面的专利分析和战略洞察。
- 将此技能用于需要明确假设、有界范围和可复现输出格式的证据洞察任务。
- 当您需要针对缺失输入、执行错误或部分证据有记录的回退路径时，使用此技能。

## 主要功能

- 以下功能的范围聚焦工作流程：当分析生物技术专利格局、识别药物知识产权中的空白领域、追踪竞争对手专利或评估药物开发的自由操作空间时使用。为生命科学创新提供全面的专利分析和战略洞察。
- 可执行路径：`scripts/main.py`。
- `references/` 目录中提供特定任务指导的参考材料。
- 结构化执行路径，旨在保持输出的一致性和可审查性。

## 依赖项

- `Python`：`3.10+`。当前打包技能的仓库基准版本。
- `第三方包`：`此技能包中未明确固定版本`。如果此技能需要更严格的环境控制，请添加固定版本。

## 使用示例

```bash
cd "20260318/scientific-skills/Evidence Insight/patent-landscape"
python -m py_compile scripts/main.py
python scripts/main.py --help
```

示例运行计划：
1. 确认用户输入、输出路径以及所需的配置值。
2. 如果脚本使用固定设置，请编辑文件内的 `CONFIG` 块或已记录的参数。
3. 使用已验证的输入运行 `python scripts/main.py`。
4. 检查生成的输出，并返回最终成果物，同时列出所有假设说明。

## 实施详情

参见上方 `## 工作流程` 部分的相关说明。

- 执行模型：验证请求，选择打包的工作流程，并生成有界的可交付成果。
- 输入控制：在运行任何脚本之前，确认源文件、范围限制、输出格式和验收标准。
- 主要实现入口：`scripts/main.py`。
- 参考指导：`references/` 包含支撑规则、提示或检查清单。
- 优先澄清的参数：输入路径、输出路径、范围过滤器、阈值以及任何领域特定约束。
- 输出规范：保持结果可复现，明确识别假设，避免未记录的副作用。

## 快速检查

使用此命令在深入执行前验证打包脚本入口点是否可解析。

```bash
python -m py_compile scripts/main.py
```

## 审计命令

使用以下具体命令进行验证。这些命令具有自包含性，避免使用占位符路径。

```bash
python -m py_compile scripts/main.py
python scripts/main.py --help
```

## 工作流程

1. 在进行详细工作之前，确认用户目标、所需输入和不可妥协的约束条件。
2. 验证请求是否符合已记录的范围，如果任务需要不支持的假设，则尽早停止。
3. 仅使用实际可用的输入，通过打包脚本路径或已记录的推理路径。
4. 返回结构化结果，将假设、可交付成果、风险和未解决项目分开呈现。
5. 如果执行失败或输入不完整，切换到回退路径并明确说明阻止完整执行的原因。

## 快速开始

```python
from scripts.patent_landscape import PatentLandscapeAnalyzer

analyzer = PatentLandscapeAnalyzer()

# Analyze therapeutic area
landscape = analyzer.analyze(
    therapeutic_area="CAR-T cell therapy",
    date_range="2020-2024",
    assignees=["Novartis", "Kite Pharma", "Juno Therapeutics"]
)
```

## 核心功能

### 1. 专利搜索与分析

```python
results = analyzer.search_patents(
    keywords=["CRISPR", "gene editing", "therapeutic"],
    classification="C12N15/113",  # IPC class
    jurisdictions=["US", "EP", "WO"]
)
```

**搜索策略：**
- **基于关键词**：技术术语 + 同义词
- **基于分类**：IPC/CPC 编码
- **基于引用**：正向/反向引用
- **基于受让人**：公司专利组合

### 2. 空白领域分析

```python
opportunities = analyzer.identify_white_spaces(
    technology="Antibody-drug conjugates",
    target_diseases=["breast cancer", "lung cancer"],
    existing_claims=landscape
)
```

**空白领域机会：**
- 服务不足的疾病适应症
- 新型联合疗法
- 替代给药机制
- 地域空白（新兴市场）

### 3. 竞争对手情报

```python
competitors = analyzer.analyze_competitors(
    companies=["Pfizer", "Moderna", "BioNTech"],
    focus_area="mRNA vaccines"
)
```

**竞争对手指标：**
| 指标 | 描述 |
|--------|-------------|
| 组合规模 | 有效专利总数 |
| 申请速度 | 近期申请趋势 |
| 地理覆盖 | 司法管辖区策略 |
| 技术重点 | 核心与外围领域 |
| 合作模式 | 协作趋势 |

### 4. 自由操作（FTO）评估

```python
fto = analyzer.assess_fto(
    product_concept="Bispecific antibody targeting PD-1 and CTLA-4",
    jurisdictions=["US", "EU", "Japan"]
)
```

**FTO 分析步骤：**
1. 识别相关专利权利要求
2. 将权利要求映射到产品特征
3. 评估阻碍专利的有效性
4. 绕过设计选项
5. 许可建议

## 命令行使用

```text

# Generate patent landscape report
python scripts/patent_landscape.py \
  --query "immuno-oncology checkpoint inhibitors" \
  --output landscape_report.pdf \
  --format comprehensive

# Quick FTO check
python scripts/patent_landscape.py \
  --fto "product_description.txt" \
  --jurisdictions US EP JP
```

## 数据来源

- USPTO（美国）
- EPO（欧洲）
- WIPO（全球）
- JPO（日本）
- CNIPA（中国）

## 参考资料

- `references/ipc-classifications.md` - 生物技术的 IPC/CPC 编码
- `references/patent-search-strategies.md` - 高级搜索技术
- `examples/landscape-reports/` - 示例报告

---

**技能 ID**：204 | **版本**：1.0 | **许可证**：MIT

## 输出要求

每个最终响应应在相关时明确以下内容：

- 目标或请求的可交付成果
- 使用的输入和引入的假设
- 工作流程或决策路径
- 核心结果、建议或成果物
- 约束、风险、注意事项或验证需求
- 未解决项目和下一步检查

## 错误处理

- 如果所需输入缺失，请明确说明缺少哪些字段，并仅请求最少的额外信息。
- 如果任务超出已记录的范围，请停止而不是猜测或悄悄扩大任务范围。
- 如果 `scripts/main.py` 失败，请报告失败点，总结仍可安全完成的内容，并提供手动回退方案。
- 不得虚构文件、引用、数据、搜索结果或执行结果。

## 输入验证

此技能接受与 `patent-landscape` 已记录用途相匹配且包含足够上下文以安全完成工作流程的请求。

当请求超出范围、缺少关键输入或需要不支持的假设时，不得继续执行工作流程。请回应：

> `patent-landscape` 仅处理其已记录的工作流程。请提供缺少的必要输入，或切换到更合适的技能。

## 参考资料

- [references/audit-reference.md](references/audit-reference.md) - 支持的范围、审计命令和回退边界

## 响应模板

对于非简单请求，使用以下固定结构：

1. 目标
2. 收到的输入
3. 假设
4. 工作流程
5. 可交付成果
6. 风险与限制
7. 后续检查

如果请求简单，可以压缩结构，但在假设和限制影响正确性时仍需明确说明。
