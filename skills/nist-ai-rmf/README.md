# NIST AI 风险管理框架——Claude 技能

将 **NIST AI 风险管理框架**（NIST AI 100-1 + NIST AI 600-1 生成式 AI 配置文件）应用于特定 AI 系统、治理问题或影响评估——从已发布的 NIST 文本逐字引用子类别（`GOVERN 1.1`）和配置文件行动 ID（`GV-1.2-001`）。

这是独立技能分发版。将压缩文件夹上传到 Claude Cowork（桌面应用）或任何其他接受独立技能 ZIP 的主机。技能在提示提及 AI RMF、四项功能（治理 Govern / 映射 Map / 测量 Measure / 管理 Manage）、可信 AI 特征或 12 项 GAI 配置文件风险时自动激活。

## 三种模式

技能根据用户的问题自动选择模式：

- **咨询（Consult）**——快速查找。*"依 AI RMF，我应该为这个 AI 系统做什么？"* 返回适用风险（对生成式 AI）及相关建议行动/子类别，逐字引用。
- **治理计划（Governance plan）**——围绕治理（GOVERN）功能的结构化计划。*"依 AI RMF，我们的治理计划应包含什么？"*
- **评估（Assessment）**——完整、RMF 对齐的影响评估，端到端走完治理、映射、测量、管理。*"为我们的 HR 简历筛选工具运行一次 NIST AI RMF 影响评估。"*

## 示例提示

```
NIST AI RMF 对基于 GPT-4 构建的客服聊天机器人怎么说？
为我们的 HR 简历筛选工具运行一次 NIST AI RMF 评估。
依 NIST AI RMF，我们的治理计划应包含什么？
```

## 溯源

输出中的每个子类别 ID 和行动 ID 与源 NIST 出版物**逐字节一致**。适用性判断、操作性注释、角色归属建议和最终建议以行内方式标注为 `[model judgment — verify against system specifics]`（模型判断——请对照系统具体情况核验）。如果某引用无法对应到 `references/` 中的真实行，那是缺陷——而非特性。

## 来源

- **NIST AI 100-1** —— AI 风险管理框架 1.0（2023 年 1 月）。美国政府公有领域作品。权威来源：<https://www.nist.gov/itl/ai-risk-management-framework>。
- **NIST AI 600-1** —— AI RMF：生成式 AI 配置文件（2024 年 7 月）。美国政府公有领域作品。权威来源：<https://www.nist.gov/itl/ai-risk-management-framework>。

`references/core/` 和 `references/gai-profile/` 中的逐字摘录是运行时真相来源。如需重新核验任何引用，请下载原文比较。

## 局限

- 该框架是**非约束性**的自愿 NIST 指引，而非法规。强制性制度（欧盟 AI 法案、纽约市地方法 144、科罗拉多州 AI 法案、行业规则）施加的实际义务可能追随 NIST——也可能不追随。技能会标记分歧；它不替代分析。
- 来源冻结于上述发布日期。NIST 发布修订版时，参考文件需要重新提取。
- GAI 配置文件以生成式 AI 为前提。将其行动应用于非生成式系统会产生噪音——技能明确避免这一点。
- 这不能替代法律顾问。

## 许可

技能代码为 [MIT](LICENSE)。NIST 出版物本身是美国政府的作品，依 17 U.S.C. § 105 不受版权保护——无论本技能的许可如何，它们均为公有领域。
