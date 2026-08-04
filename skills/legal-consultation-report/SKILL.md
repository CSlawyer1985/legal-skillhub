---
name: legal-consultation-report
description: 资深律师视角生成高转化率精美咨询报告；当用户需要输出法律咨询报告、风险评估报告、服务方案或促成签单的HTML文档时使用
dependency:
  python:
    - jinja2==3.1.2
---

# 法律咨询报告生成技能

## 任务目标

本技能用于：根据客户真实咨询需求，由资深律师视角生成**高转化率、排版精美**的法律咨询报告HTML文档，核心目标是**促成签单**。

## 核心能力

- 资深律师专业视角：语气真诚、逻辑严谨、信任感强
- 五大核心模块：客户需求、核心事实梳理、法律关系分析、潜在风险提示、解决方案建议
- 高转化率设计：风险前置凸显价值、解决方案展示专业、报价策略灵活、CTA引导签单
- 精美HTML输出：专业法律文书风格，排版精良，可直接下载

## 输入数据结构

脚本接收JSON格式的案情数据，通过命令行参数 `--case_data` 传入完整JSON字符串，或通过 `--case_file` 传入JSON文件路径。

### 核心字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `client_name` | string | 是 | 客户名称（公司名或个人姓名） |
| `client_contacts` | string | 是 | 联系人信息 |
| `lawyer_name` | string | 是 | 咨询律师姓名 |
| `lawyer_team` | string | 否 | 律师团队名称 |
| `core_advantages` | string | 否 | 律师核心优势描述 |
| `report_title` | string | 是 | 报告标题 |
| `report_subtitle` | string | 否 | 报告副标题 |
| `business_desc` | string | 是 | 企业/个人业务描述 |
| `consultation_background` | string | 是 | 咨询背景与诉求 |
| `core_requirements` | array | 是 | 核心法律需求列表 |
| `key_facts` | array | 是 | 核心事实要点 |
| `legal_relations` | array | 是 | 法律关系分析 |
| `risk_items` | array | 是 | 潜在风险提示 |
| `solutions` | array | 是 | 解决方案建议 |
| `service_packages` | array | 否 | 服务方案与报价 |
| `closing_message` | string | 否 | 结语信息 |
| `validity_period` | string | 否 | 报价有效期 |

## 操作流程

### 标准流程

1. **收集案情信息**：从对话中提取或用户提供完整的案情数据
2. **结构化数据整理**：按上述字段整理成JSON格式
3. **调用报告生成脚本**：
   ```bash
   python scripts/generate_report.py --case_data '{"client_name":"...","report_title":"...","core_requirements":[...],"key_facts":[...],"legal_relations":[...],"risk_items":[...],"solutions":[...]}'
   ```
4. **校验输出**：确认HTML报告完整生成
5. **交付客户**：提供下载链接或直接展示HTML内容

### 数据填充策略

- **客户需求**：基于用户表达的诉求，提炼为2-4条核心需求
- **核心事实**：从案情中提取与法律问题相关的关键事实
- **法律关系**：分析涉及的民事主体之间的法律关系性质
- **风险提示**：按优先级（高/中/低）标注风险点
- **解决方案**：针对每个风险点给出专业建议
- **服务报价**：可选，参照市场标准设计阶梯报价

## 报告结构模板

```html
[报告标题] + [副标题]
致：[客户名称] + [联系人]

[开场白：专业背景 + 服务承诺]

一、客户需求
   [需求列表]

二、核心事实梳理
   [事实要点表格或列表]

三、法律关系分析
   [法律关系图或列表]

四、潜在风险提示
   [风险分级表格：高/中/低]

五、解决方案建议
   [分条建议方案]

六、服务方案与报价（可选）
   [报价表格]

七、结语
   [专业总结 + CTA引导]

[脚注：律师信息 + 联系方式]
```

## 输出规范

- 格式：精美HTML，支持浏览器直接打开
- 样式：专业法律文书风格，主色调深蓝#1a4996
- 功能：包含一键下载按钮
- 文件名：`{客户名称}法律风险咨询报告.html`

## 注意事项

- 语气始终从资深律师视角出发，真诚专业
- 风险描述要客观但突出价值，避免过度恐吓
- 解决方案展示专业能力，不轻易承诺结果
- 报价策略灵活，体现性价比
- 结尾CTA明确，引导下一步沟通

## 资源索引

- 脚本：见 [scripts/generate_report.py](scripts/generate_report.py)（报告生成核心逻辑）
- 参考格式：见 [references/report_format.md](references/report_format.md)（JSON数据格式规范与示例）
