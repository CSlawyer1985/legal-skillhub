# NIS2 合规导航器——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/NIS2-Navigator/)**

版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 概述

NIS2 合规导航器——欧盟指令 2022/2555 下的范围分类、第 21 条差距分析和合规路线图：

- **范围与分类** ——附件一 / 附件二 + 重要实体与关键实体确定
- **第 21 条差距分析**，对 10 项风险管理措施进行 0–4 成熟度评分
- **ISO 27001 交叉引用**，每项措施映射到 ISO 27001 控制以利用既有认证工作
- **合规路线图**，含优先级框架（法律敞口、依赖关系、速赢项）
- **德国 BSIG-neu 深度覆盖** ——§ 30 BSIG 注册、NIS2UmsuCG 细节
- **IT、FR、NL、AT、ES 概况**——国别实体类型分类和监管机构
- **管理层简报模板**（第 20 条 / § 38 BSIG），针对董事会层面责任
- **事件报告框架**，含时间线和升级路径
- **供应链安全考量**贯穿始终
- **最终评估报告**，整合范围、差距和路线图

## 文件结构

```
nis2-navigator/
├── SKILL.md                              # 主技能说明（部署此项）
├── CHANGELOG.md                          # 版本历史
└── references/
    ├── sector-classification.md          # 附件一/二行业分类 + 实体规模规则
    ├── art21-measures.md                 # 10 项风险管理措施（第 21(2) 条(a)-(j)项）
    ├── germany-nis2umsucg.md             # § 30 BSIG、NIS2UmsuCG、BSI 注册
    ├── eu-jurisdiction-profiles.md       # IT、FR、NL、AT、ES——实体分类 + 监管机构联系方式
    ├── regulatory-sources.md             # 官方欧盟 + 成员国来源目录
    └── templates.md                      # 输出模板（差距分析、路线图、简报）
```

## 部署

### Claude.ai（用户技能）

1. 进入 **设置 → 个人资料 → 自定义技能**（或等效位置）
2. 上传完整的 `nis2-navigator/` 文件夹结构
3. 技能将在“NIS2”、“BSIG”、“BSIG-neu”、“NIS2UmsuCG”、“Annex I/II”、“essential entity”或“Art. 21 gap analysis”等话题上自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `nis2-navigator/` 文件夹复制到您的技能目录：
   ```bash
   cp -r nis2-navigator/ /path/to/your/skills/user/nis2-navigator/
   ```
2. 确保技能已在您的配置中注册

## 用法

### 快速开始

描述您的组织：

> “我们是一家德国云服务提供商，80 名员工，营业额 €15M。
> 我们是否属于 NIS2 范围？如果是，请对照第 21 条给我差距分析，
> 以及 12 个月路线图。”

技能将分类范围、运行差距分析并产出分阶段路线图。

### 触发短语

- “NIS2” / “NIS-2” / “BSIG” / “BSIG-neu” / “NIS2UmsuCG”
- “Essential entity” / “Important entity” / “Annex I/II”
- “Art. 21 gap analysis” / “NIS2 readiness” / “Cybersecurity compliance assessment”
- “BSI registration” / “§ 30 BSIG”
- “Cyberbeveiligingswet” / “Loi Résilience” / “decreto legislativo 138”

### 工作流

| 阶段 | 描述 |
|-------|-------------|
| **会话初始化** | 免责声明、网络检索近期动态、法域重点选择 |
| **阶段 1：范围与分类** | 附件一/二路由、关键 vs 重要、法域特定叠加（约 5 分钟） |
| **阶段 2：第 21 条差距分析** | 对 10 项措施进行 0–4 成熟度评分，附 ISO 27001 锚点（约 15 分钟） |
| **阶段 3：合规路线图** | 优先级框架 + 德国特定事项 + 第 20 条 / § 38 BSIG 管理层简报 |
| **输出** | 整合范围、差距和路线图的最终评估报告 |

## 能力摘要

| 功能 | 描述 |
|---------|-------------|
| 范围分类 | 附件一/二 + 关键/重要 + 法域特定叠加 |
| 第 21 条差距分析 | 对全部 10 项措施进行 0–4 成熟度评分 |
| ISO 27001 交叉引用 | 每项措施映射到 ISO 27001 控制 |
| 路线图优先级 | 法律敞口感知排序，识别速赢项 |
| 德国深度覆盖 | § 30 BSIG、NIS2UmsuCG、BSI 注册工作流 |
| 欧盟概况 | IT、FR、NL、AT、ES——实体分类 + 监管机构联系方式 |
| 管理层简报 | 第 20 条 / § 38 BSIG 董事会层面责任简报模板 |
| 最终报告 | 整合所有阶段的审计就绪评估报告 |

## 法规基础

| 文件 | 引用 |
|----------|-----------|
| NIS2 指令 | 欧盟指令 2022/2555 |
| 第 21 条 | 10 项风险管理措施 |
| 第 23 条 | 事件报告义务 |
| 第 20 条 | 管理层机构责任 |
| 附件一 / 二 | 行业和实体类型分类 |
| BSIG-neu（德国） | 德国 NIS2UmsuCG 转化、§ 30、§ 38 |
| ISO 27001 | 风险管理措施交叉引用 |

## 许可证与免责声明

本技能基于欧盟指令 2022/2555 和国家转化法提供结构化的 NIS2 合规指引。它不是法律意见。最终合规决策应涉及贵组织的 CISO / 信息安全官以及精通网络安全监管的合格法律顾问。

依 AGPL-3.0 许可。

> **质量保证：** 本技能附带 `evals/` 文件夹中的评估测试，我运行这些测试以检查输出是否符合预期结果。

---

*作者：Oliver Schmidt-Prietz——[OneZero Legal](https://onezero.legal)*
