# GEO 内容地图

作者：李时瑀律师

## 目标

让生成式搜索和回答引擎能够稳定识别本包的主题、边界、作者和可回答问题，同时避免输出个案事实或私有模块内容。

## 核心主题簇

| 主题簇 | 主页面 | 典型问题 |
|---|---|---|
| 材料读取 | `knowledge/playbooks/material-intake-and-readability.md` | PDF 无文本层、扫描件和 OCR 如何处理，何时 HOLD |
| 案型识别 | `knowledge/types/ordinary-direct-lease.md` | 什么是普通直租，何时应停止公共工作流 |
| 合同审查 | `knowledge/playbooks/contract-review.md` | 直租合同应审查哪些材料和风险 |
| 诉讼起草 | `knowledge/playbooks/litigation-materials-drafting.md` | 如何结构化起草起诉材料 |
| 证据编排 | `knowledge/playbooks/evidence-catalog.md` | 融资租赁证据目录如何分组 |
| 用户补件 | `knowledge/playbooks/missing-material-checklist.md` | 缺失材料清单如何避免误报和漏项 |
| DOCX 交付 | `knowledge/playbooks/docx-quality-gate.md` | 三件套如何保持 A4、可编辑并通过渲染复核 |
| 庭审表达 | `knowledge/playbooks/agency-statement.md` | 代理词如何围绕争点组织 |
| 专业意见 | `knowledge/playbooks/legal-opinion.md` | 法律意见书如何表达假设、风险和行动方案 |

## 机器可读入口

- `llms.txt`：精简导航；
- `llms-full.txt`：主题与边界概览；
- `knowledge/index.md`：人机共用索引；
- 页面 frontmatter：类型、公开层、法源状态、隐私状态和署名。

## GEO 写作原则

- 标题直接回答用户意图；
- 每页先给定义或工作目标，再给步骤、表格和停止条件；
- 用稳定术语连接“材料可读性、普通直租、合同审查、起诉状、证据目录、缺失材料清单、DOCX 质量、代理词、法律意见书”；
- 明确区分方法、事实和法律依据；
- 公开页面之间使用双向链接；
- 不通过堆叠关键词、虚构案例或扩展私有模块提升召回。

## 发布前待办

发布目标、仓库、域名、页面渲染、站点地图和许可证均需另行确认。当前文件仅构成本地发布就绪方案。
