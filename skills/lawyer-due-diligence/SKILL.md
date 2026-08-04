---
name: lawyer-due-diligence
description: |
  Professional Chinese legal due diligence report writer. Covers 11 standard DD modules:
  entity qualification, equity structure, business licenses, assets, major contracts,
  debts & guarantees, tax compliance, labor & HR, litigation & penalties, EHS,
  related-party transactions & non-competition.
  
  Trigger when the user asks to:
  - "write a legal due diligence report" / "律师尽职调查报告"
  - "conduct legal DD" / "法律尽调"
  - "analyze target company legal risks" / "目标公司法律风险分析"
  - "prepare DD for M&A / investment / IPO" / "并购/投资/IPO尽调"
  - "check compliance of a company" / "目标公司合规审查"
  - "due diligence checklist" / "尽调清单"
  - "legal risk assessment" / "法律风险评估报告"
  
  Output: structured Chinese legal due diligence report in DOCX/MD format with
  risk grading (🔴🟡🟢) and actionable recommendations.
---

# 律师尽职调查（Legal Due Diligence Report）

## 调查基准日

确认用户指定的调查基准日（基准日）。如用户未指定，默认为当前日期前一个工作日。

## 尽职调查流程

```
需求确认 → 资料收集 → 逐模块核查 → 法律分析 → 风险评级 → 报告撰写 → 结论建议
```

## 报告生成步骤

### 1. 确认尽调范围

向用户确认以下信息（如用户已提供则跳过）：
- **委托方**：谁委托的
- **目标公司**：公司全称
- **尽调目的**：并购/投资/IPO/专项
- **尽调范围**：全模块/特定模块
- **行业类型**：影响资质合规分析重点

### 2. 加载参考文件

- 阅读 `references/dd-modules.md` → 了解各模块调查要点、常见风险和标准表述
- 阅读 `references/report-structure.md` → 确定报告结构框架
- 阅读 `references/checklist.md` → 交叉检查有无遗漏

如用户有特殊要求（例如特定行业的专章），在标准模块基础上增减。

### 3. 逐模块分析与撰写

针对每个模块，按照以下逻辑展开：

```
调查内容（核查了什么资料）
    ↓
调查结果（事实陈述，客观中立）
    ↓
法律分析（结合法律法规进行评价）
    ↓
风险提示（标注 🔴🟡🟢）
```

### 4. 风险评级

| 等级 | 含义 | 行动建议 |
|------|------|---------|
| 🔴 高风险 | 重大法律瑕疵，可能致交易目的无法实现 | 审慎评估，必要时中止交易 |
| 🟡 中风险 | 存在风险但可补救 | 交易前完成整改 |
| 🟢 低风险 | 轻微瑕疵，不构成实质障碍 | 正常推进，完善即可 |

### 5. 报告格式

- **默认输出**：Markdown（便于预览和后续转换）
- **可转换格式**：提供 `.docx` 版本（Word格式，适合正式提交）
- **排版要求**：
  - 标题层级清晰（一级/二级/三级）
  - 正文宋体/仿宋，字号适当
  - 表格对齐，数据准确
  - 法律条文引用格式：《XXXX法》第X条

## 法律条文引用规则

- 使用标准全称：《中华人民共和国民法典》而非《民法典》
- 首次出现时用全称，后续可用简称
- 引用司法解释须标明文号：法释〔2023〕X号
- 引用部门规章须标明：XX部令第X号

## 参考文件说明

| 文件 | 用途 | 何时加载 |
|------|------|---------|
| `references/dd-modules.md` | 各模块调查要点、常见风险、标准表述 | 每次报告撰写时都要参考 |
| `references/report-structure.md` | 报告完整结构框架和风险等级标准 | 报告结构规划时参考 |
| `references/checklist.md` | 尽调清单，交叉检查未遗漏事项 | 报告完成前做最终核查 |

## 输出文件

- 报告文件命名格式：`律师尽职调查报告_[目标公司简称]_[日期].md`
- 如用户需要 `.docx`，使用 Word skill 转换

## 注意事项

1. **客观中立**：尽调报告应当客观陈述事实，不做无依据的推测
2. **区分法律问题与非法律问题**：不评估财务、估值等非法律事项
3. **注明信息来源**：区分"来源于目标公司提供"和"公开渠道查询"
4. **保留判断空间**：不确定的事项标注"需进一步核查"
5. **注意保密声明**：报告首页须注明"仅供内部决策参考"
