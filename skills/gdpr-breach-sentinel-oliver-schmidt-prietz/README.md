# Breach Sentinel——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/GDPR-Breach-Sentinel/)**

版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 概述

GDPR Breach Response Sentinel（GDPR 违规响应哨兵）——为 Claude 设计的高级事件响应技能，提供：

- **违规定性分诊**——工作流前先设门禁：“这到底是不是个人数据泄露？”（Art. 4(12)）
- **ENISA 严重性评估**，含临界分值分析，并与第 33/34 条法定法律测试衔接
- **与 EDPB 模板对齐的违规证据文件**，镜像 EDPB 违规通知模板 [2026]（草案，公开咨询中）
- **EDPB 案例匹配**，对照 18 个已记录的违规场景（作为类推，并说明其局限）
- **专门的第 34 条决策模块**——高风险测试、第 34(3) 条全部三项例外、沟通策略
- **战略案件咨询**——资深律师级分析与建议
- **动态网络研究**，用于执法先例和监管机构（SA）特定指引，并遵循来源纪律
- **灵活的缓解行动手册**，针对具体事件定制
- **监管机构联系目录**，含按法域区分的门户查询
- **AI 法案第 73 条交叉适用**，用于涉及高风险 AI 系统的违规
- **行业平行制度筛查**（NIS2、DORA、eIDAS、ePrivacy、保险、劳资委员会）
- **审计就绪的 .docx 文档生成**（证据文件、第 33 条、第 34 条、合规日志、后续跟进/撤回等）
- **通知后案件跟踪**
- **正确处理处理者路径**——毫不迟延地通知控制者（第 33(2) 条）、合同约定的 DPA 窗口、交接包；不存在虚构的处理者 72 小时截止期限

## 文件结构

```
breach-sentinel/
├── SKILL.md                              # Main skill instructions (deploy this)
├── evals/
│   └── evals.json                        # 13 test cases, 132 assertions
└── references/
    ├── enisa-methodology.md              # ENISA scoring tables, legal bridge, worked examples
    ├── edpb-template-evidence-file.md    # EDPB Template [2026] field map + evidence file builder
    ├── art34-communication.md            # Art. 34 decision framework incl. all 34(3) exceptions
    ├── parallel-regimes.md               # AI Act Art. 73 depth + NIS2/DORA/eIDAS/etc. screen
    ├── edpb-cases.md                     # 18 EDPB breach case scenarios + analogy rules
    ├── templates.md                      # 17 document templates (Art. 33/34, handoff, follow-up …)
    ├── strategic-advisory.md             # Advisory framework, principles, tone examples
    ├── mitigation-playbook.md            # Design principles, output format, action categories
    ├── post-notification-tracking.md     # Tracking dashboard template
    └── web-research.md                   # Search query templates, source discipline, DE routing
```

## 部署

### Claude.ai（用户技能）

1. 进入 **Settings → Profile → Custom Skills**（或等效位置）
2. 上传整个 `breach-sentinel/` 文件夹结构
3. 当你提及数据泄露、第 33/34 条、“Datenpanne”或相关话题时，该技能将自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `breach-sentinel/` 文件夹复制到你的技能目录：
   ```bash
   cp -r breach-sentinel/ /path/to/your/skills/user/breach-sentinel/
   ```
2. 确保技能已在你的配置中注册

## 使用

### 快速开始

只需向 Claude 描述违规事件：

> “我们刚刚发现一名外部攻击者窃取了我们客户数据库的数据。
> 约 2,000 条记录，包含姓名、电子邮件和支付数据。我们在慕尼黑。
> 这件事发生在昨天下午 3 点。”

技能将激活并引导你完成评估。

### 触发短语

- “我们发生了数据泄露”/“Datenpanne”/“Datenschutzverletzung”
- “我们需要通知监管机构吗？”/“72 小时”/“Art. 33”
- “帮我评估这次违规”/“ENISA 评估”
- “生成违规通知文件”

### 模式

| 模式 | 何时使用 |
|------|-------------|
| **引导式** | 你对细节不确定；技能逐一提问 |
| **快速路径** | 你掌握全部事实；直接提供并即时获得评估 |
| **紧急** | 通知时限剩余不足 12 小时 |

## 能力摘要

| 功能 | 描述 |
|---------|-------------|
| 违规定性分诊 | 工作流前的门禁：安全事件对比个人数据泄露（第 4(12) 条） |
| ENISA 严重性计算 | 完整 SE = (DPC × EI) + CB 并作情境调整——作为决策支持 |
| 第 33/34 条法律衔接 | 每份评估均书面衔接：分值 → 事实 → 保障措施 → 法定结论 |
| EDPB 证据文件 | 镜像 EDPB 模板 [2026]（草案）的完整案卷——全部 7 个部分，可直接提交门户 |
| 第 34 条决策模块 | 高风险测试、第 34(3)(a)/(b)/(c) 条例外、沟通策略、决策备忘录 |
| 证据姿态 | 每份评估中均坚持事实/假设/未知项的纪律并标注置信度 |
| 临界分值分析 | 对接近 2.0/3.0/4.0 阈值的分值进行额外审查 |
| EDPB 案例匹配 | 对照《指南 01/2021》记录的 18 个场景——作为类推并说明其局限 |
| 战略咨询 | 资深律师级分析：隐藏风险、监管机构策略、杠杆点 |
| 动态网络研究 | 最新执法先例与监管机构指引，并遵循来源纪律规则 |
| 监管机构联系查询 | 查找通知门户 URL 和各法域特定要求 |
| 德国监管机构路由 | 根据实体类型正确路由至 BfDI 或 LfDI/LDA |
| 缓解行动手册 | 针对个案、灵活结构的行动计划，含责任人和截止期限 |
| AI 法案集成 | 针对 AI 违规的第 73 条严重事件筛查（定义、时限、适用性） |
| 平行制度筛查 | NIS2、DORA、eIDAS、ePrivacy、刑事、保险、合同、劳资委员会 |
| 处理者路径 | 第 33(2) 条毫不迟延义务、合同约定的 DPA 窗口、交接包 |
| 文档生成 | 审计就绪的 .docx 文件——17 个模板，含跟进、撤回、延迟通知 |
| 通知后跟踪 | 持续案件管理面板，含跟进和撤回里程碑 |

## 监管依据

| 文件 | 引用 |
|----------|-----------|
| GDPR 第 33 条和第 34 条 | 违规通知义务 |
| EDPB《指南 9/2022》v2.0 | 个人数据泄露通知 |
| EDPB《指南 01/2021》v2.0 | 关于违规通知的示例 |
| EDPB 模板 [2026] v1.0 | 个人数据泄露通知模板——草案，公开咨询截至 2026 年 8 月 5 日 |
| ENISA 严重性方法论 | 风险评估公式和评分 |
| 欧盟 AI 法案（条例 2024/1689） | 第 73 条严重事件报告（自 2026 年 8 月 2 日起适用） |

## 许可与免责声明

本技能基于公开可获取的 GDPR 监管材料提供指引。不构成法律意见。所有通知决定均应咨询具备资格的法律顾问和组织的数据保护官（DPO）。

---

*由 Oliver Schmidt-Prietz 创建——OneZero Legal
